"""
REST API for Wazo IVR System Plugin
Provides endpoints for IVR flow management, provisioning, and CRM integration
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
import uuid

from .flows import IVRFlow, load_flow, save_flow, validate_flow, is_business_hours
from .tts import synthesize_text, get_tts_status, cleanup_cache
from .wazo import wazo_session, get_queues, get_agents, get_extensions
from .dialplan import render_dialplan

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app configuration
app = Flask(__name__)
CORS(app)

# Configuration
FLOWS_DIR = "/var/lib/wazo-ivr/flows"
SOUNDS_DIR = "/var/lib/wazo/sounds/ivr"
DIALPLAN_DIR = "/etc/asterisk/extensions_extra.d"

# Ensure directories exist
os.makedirs(FLOWS_DIR, exist_ok=True)
os.makedirs(SOUNDS_DIR, exist_ok=True)
os.makedirs(DIALPLAN_DIR, exist_ok=True)

class IVRManager:
    """Manages IVR flows and their lifecycle"""
    
    def __init__(self):
        self.flows: Dict[str, IVRFlow] = {}
        self.load_existing_flows()
    
    def load_existing_flows(self):
        """Load existing flows from storage"""
        for filename in os.listdir(FLOWS_DIR):
            if filename.endswith(('.yml', '.yaml', '.json')):
                try:
                    flow_path = os.path.join(FLOWS_DIR, filename)
                    flow = load_flow(flow_path)
                    self.flows[flow.id] = flow
                    logger.info(f"Loaded flow: {flow.id}")
                except Exception as e:
                    logger.error(f"Failed to load flow {filename}: {e}")
    
    def create_flow(self, flow_data: Dict[str, Any]) -> IVRFlow:
        """Create a new IVR flow"""
        flow_id = flow_data.get('id') or str(uuid.uuid4())
        flow_data['id'] = flow_id
        
        if flow_id in self.flows:
            raise ValueError(f"Flow with ID '{flow_id}' already exists")
        
        flow = IVRFlow(**flow_data)
        
        # Validate flow
        errors = validate_flow(flow)
        if errors:
            raise ValueError(f"Flow validation failed: {', '.join(errors)}")
        
        self.flows[flow_id] = flow
        self.save_flow(flow)
        
        logger.info(f"Created flow: {flow_id}")
        return flow
    
    def update_flow(self, flow_id: str, flow_data: Dict[str, Any]) -> IVRFlow:
        """Update an existing IVR flow"""
        if flow_id not in self.flows:
            raise ValueError(f"Flow '{flow_id}' not found")
        
        # Update flow data
        current_flow = self.flows[flow_id]
        for key, value in flow_data.items():
            if hasattr(current_flow, key):
                setattr(current_flow, key, value)
        
        # Validate updated flow
        errors = validate_flow(current_flow)
        if errors:
            raise ValueError(f"Flow validation failed: {', '.join(errors)}")
        
        self.save_flow(current_flow)
        logger.info(f"Updated flow: {flow_id}")
        return current_flow
    
    def delete_flow(self, flow_id: str) -> bool:
        """Delete an IVR flow"""
        if flow_id not in self.flows:
            return False
        
        # Remove flow file
        flow_file = os.path.join(FLOWS_DIR, f"{flow_id}.yml")
        if os.path.exists(flow_file):
            os.unlink(flow_file)
        
        # Remove dialplan file
        dialplan_file = os.path.join(DIALPLAN_DIR, f"50-ivr-{flow_id}.conf")
        if os.path.exists(dialplan_file):
            os.unlink(dialplan_file)
        
        del self.flows[flow_id]
        logger.info(f"Deleted flow: {flow_id}")
        return True
    
    def get_flow(self, flow_id: str) -> Optional[IVRFlow]:
        """Get a specific IVR flow"""
        return self.flows.get(flow_id)
    
    def list_flows(self) -> List[Dict[str, Any]]:
        """List all IVR flows"""
        return [
            {
                "id": flow.id,
                "tenant": flow.tenant,
                "entry_context": flow.entry_context,
                "tts_backend": flow.tts_backend,
                "languages": flow.languages,
                "created_at": flow.created_at,
                "updated_at": flow.updated_at,
                "status": "active" if self.is_flow_active(flow.id) else "inactive"
            }
            for flow in self.flows.values()
        ]
    
    def save_flow(self, flow: IVRFlow):
        """Save flow to storage"""
        flow_path = os.path.join(FLOWS_DIR, f"{flow.id}.yml")
        save_flow(flow, flow_path)
    
    def is_flow_active(self, flow_id: str) -> bool:
        """Check if flow is currently active (dialplan exists)"""
        dialplan_file = os.path.join(DIALPLAN_DIR, f"50-ivr-{flow_id}.conf")
        return os.path.exists(dialplan_file)
    
    def deploy_flow(self, flow_id: str, wazo_host: str, token: str) -> bool:
        """Deploy flow to Wazo system"""
        if flow_id not in self.flows:
            return False
        
        try:
            flow = self.flows[flow_id]
            
            # Generate TTS audio files
            self.generate_audio_files(flow)
            
            # Generate dialplan
            session = wazo_session(wazo_host, token)
            queue_map = get_queues(session)
            dialplan_path = os.path.join(DIALPLAN_DIR, f"50-ivr-{flow_id}.conf")
            render_dialplan(flow, queue_map, dialplan_path)
            
            # Reload Asterisk dialplan
            os.system("asterisk -rx 'dialplan reload'")
            
            logger.info(f"Deployed flow: {flow_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deploy flow {flow_id}: {e}")
            return False
    
    def generate_audio_files(self, flow: IVRFlow):
        """Generate TTS audio files for flow"""
        for prompt_id, prompt_config in flow.prompts.items():
            for lang, text in prompt_config.get("text", {}).items():
                voice = next(
                    (v['voice'] for v in flow.languages if v['code'] == lang),
                    flow.languages[0]['voice'] if flow.languages else "Joanna"
                )
                
                audio_dir = os.path.join(SOUNDS_DIR, flow.tenant, flow.id)
                audio_file = os.path.join(audio_dir, f"{prompt_id}_{lang}.wav")
                
                synthesize_text(
                    text=text,
                    voice=voice,
                    out_wav=audio_file,
                    tts_backend=flow.tts_backend,
                    language=lang
                )

# Initialize IVR manager
ivr_manager = IVRManager()

# API Routes

@app.route('/api/ivr/flows', methods=['GET'])
def list_flows():
    """List all IVR flows"""
    try:
        flows = ivr_manager.list_flows()
        return jsonify({"flows": flows, "count": len(flows)})
    except Exception as e:
        logger.error(f"Failed to list flows: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ivr/flows', methods=['POST'])
def create_flow():
    """Create a new IVR flow"""
    try:
        flow_data = request.get_json()
        if not flow_data:
            return jsonify({"error": "No flow data provided"}), 400
        
        flow = ivr_manager.create_flow(flow_data)
        return jsonify({
            "message": "Flow created successfully",
            "flow": {
                "id": flow.id,
                "tenant": flow.tenant,
                "entry_context": flow.entry_context,
                "created_at": flow.created_at
            }
        }), 201
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Failed to create flow: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ivr/flows/<flow_id>', methods=['GET'])
def get_flow(flow_id: str):
    """Get a specific IVR flow"""
    try:
        flow = ivr_manager.get_flow(flow_id)
        if not flow:
            return jsonify({"error": "Flow not found"}), 404
        
        return jsonify({
            "id": flow.id,
            "tenant": flow.tenant,
            "entry_context": flow.entry_context,
            "tts_backend": flow.tts_backend,
            "languages": flow.languages,
            "prompts": flow.prompts,
            "menus": {menu_id: {
                "id": menu.id,
                "prompt": menu.prompt,
                "timeout_sec": menu.timeout_sec,
                "max_retries": menu.max_retries,
                "options": menu.options,
                "fallback_action": menu.fallback_action,
                "parent_menu": menu.parent_menu
            } for menu_id, menu in flow.menus.items()},
            "recording": flow.recording,
            "business_hours": {
                "name": flow.business_hours.name,
                "timeframes": flow.business_hours.timeframes,
                "timezone": flow.business_hours.timezone
            } if flow.business_hours else None,
            "voicemail_fallback": flow.voicemail_fallback,
            "call_recording": flow.call_recording,
            "max_call_duration": flow.max_call_duration,
            "created_at": flow.created_at,
            "updated_at": flow.updated_at
        })
        
    except Exception as e:
        logger.error(f"Failed to get flow {flow_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ivr/flows/<flow_id>', methods=['PUT'])
def update_flow(flow_id: str):
    """Update an existing IVR flow"""
    try:
        flow_data = request.get_json()
        if not flow_data:
            return jsonify({"error": "No flow data provided"}), 400
        
        flow = ivr_manager.update_flow(flow_id, flow_data)
        return jsonify({
            "message": "Flow updated successfully",
            "flow": {
                "id": flow.id,
                "updated_at": flow.updated_at
            }
        })
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Failed to update flow {flow_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ivr/flows/<flow_id>', methods=['DELETE'])
def delete_flow(flow_id: str):
    """Delete an IVR flow"""
    try:
        success = ivr_manager.delete_flow(flow_id)
        if not success:
            return jsonify({"error": "Flow not found"}), 404
        
        return jsonify({"message": "Flow deleted successfully"})
        
    except Exception as e:
        logger.error(f"Failed to delete flow {flow_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ivr/flows/<flow_id>/deploy', methods=['POST'])
def deploy_flow(flow_id: str):
    """Deploy an IVR flow to Wazo system"""
    try:
        wazo_host = request.json.get('wazo_host') if request.json else None
        token = request.json.get('token') if request.json else None
        
        if not wazo_host or not token:
            return jsonify({"error": "wazo_host and token are required"}), 400
        
        success = ivr_manager.deploy_flow(flow_id, wazo_host, token)
        if not success:
            return jsonify({"error": "Failed to deploy flow"}), 500
        
        return jsonify({"message": "Flow deployed successfully"})
        
    except Exception as e:
        logger.error(f"Failed to deploy flow {flow_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ivr/status', methods=['GET'])
def get_system_status():
    """Get system status including TTS backends"""
    try:
        tts_status = get_tts_status()
        flows_count = len(ivr_manager.flows)
        active_flows = sum(1 for flow_id in ivr_manager.flows.keys() if ivr_manager.is_flow_active(flow_id))
        
        return jsonify({
            "tts": tts_status,
            "flows": {
                "total": flows_count,
                "active": active_flows,
                "inactive": flows_count - active_flows
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ivr/tts/voices', methods=['GET'])
def get_available_voices():
    """Get available TTS voices for languages"""
    try:
        from .tts import get_available_voices, POLLY_VOICES
        
        language = request.args.get('language', 'en-US')
        voices = get_available_voices(language)
        
        return jsonify({
            "language": language,
            "voices": voices,
            "all_languages": list(POLLY_VOICES.keys())
        })
        
    except Exception as e:
        logger.error(f"Failed to get available voices: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ivr/tts/synthesize', methods=['POST'])
def synthesize_speech():
    """Synthesize speech for testing"""
    try:
        data = request.get_json()
        text = data.get('text')
        voice = data.get('voice', 'Joanna')
        language = data.get('language', 'en-US')
        tts_backend = data.get('tts_backend', 'polly')
        
        if not text:
            return jsonify({"error": "Text is required"}), 400
        
        # Generate temporary audio file
        temp_dir = "/tmp/wazo-ivr-test"
        os.makedirs(temp_dir, exist_ok=True)
        audio_file = os.path.join(temp_dir, f"test_{uuid.uuid4().hex}.wav")
        
        synthesize_text(
            text=text,
            voice=voice,
            out_wav=audio_file,
            tts_backend=tts_backend,
            language=language
        )
        
        return jsonify({
            "message": "Speech synthesized successfully",
            "audio_file": audio_file,
            "text": text,
            "voice": voice,
            "language": language
        })
        
    except Exception as e:
        logger.error(f"Failed to synthesize speech: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ivr/wazo/queues', methods=['GET'])
def get_wazo_queues():
    """Get Wazo queues for integration"""
    try:
        wazo_host = request.args.get('wazo_host')
        token = request.args.get('token')
        
        if not wazo_host or not token:
            return jsonify({"error": "wazo_host and token are required"}), 400
        
        session = wazo_session(wazo_host, token)
        queues = get_queues(session)
        
        return jsonify({"queues": queues})
        
    except Exception as e:
        logger.error(f"Failed to get Wazo queues: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ivr/wazo/agents', methods=['GET'])
def get_wazo_agents():
    """Get Wazo agents for integration"""
    try:
        wazo_host = request.args.get('wazo_host')
        token = request.args.get('token')
        
        if not wazo_host or not token:
            return jsonify({"error": "wazo_host and token are required"}), 400
        
        session = wazo_session(wazo_host, token)
        agents = get_agents(session)
        
        return jsonify({"agents": agents})
        
    except Exception as e:
        logger.error(f"Failed to get Wazo agents: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ivr/maintenance/cleanup', methods=['POST'])
def cleanup_system():
    """Clean up old cache files and temporary data"""
    try:
        max_age_days = request.json.get('max_age_days', 30) if request.json else 30
        cleanup_cache(max_age_days)
        
        return jsonify({"message": f"Cleanup completed for files older than {max_age_days} days"})
        
    except Exception as e:
        logger.error(f"Failed to cleanup system: {e}")
        return jsonify({"error": str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
