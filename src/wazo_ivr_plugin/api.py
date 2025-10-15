import os
import logging
from typing import Optional
from .flows import load_flow, save_flow, validate_flow, is_business_hours
from .tts import synthesize_text, get_tts_status, cleanup_cache
from .dialplan import render_dialplan, validate_dialplan, reload_dialplan
from .wazo import wazo_session, get_queues, get_wazo_status

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def build_flow(flow_path: str, wazo_host: str, token: str, validate: bool = True) -> bool:
    """
    Build and deploy an IVR flow
    
    Args:
        flow_path: Path to flow configuration file
        wazo_host: Wazo server hostname/IP
        token: Wazo authentication token
        validate: Whether to validate the flow before building
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Load flow
        flow = load_flow(flow_path)
        logger.info(f"Loaded flow: {flow.id}")
        
        # Validate flow if requested
        if validate:
            errors = validate_flow(flow)
            if errors:
                logger.error(f"Flow validation failed: {', '.join(errors)}")
                return False
        
        # Generate TTS audio files
        logger.info("Generating TTS audio files...")
        for prompt_id, prompt_config in flow.prompts.items():
            for lang, text in prompt_config.get("text", {}).items():
                voice = next(
                    (v['voice'] for v in flow.languages if v['code'] == lang),
                    flow.languages[0]['voice'] if flow.languages else "Joanna"
                )
                
                audio_dir = f"/var/lib/wazo/sounds/ivr/{flow.tenant}/{flow.id}"
                os.makedirs(audio_dir, exist_ok=True)
                audio_file = f"{audio_dir}/{prompt_id}_{lang}.wav"
                
                synthesize_text(
                    text=text,
                    voice=voice,
                    out_wav=audio_file,
                    tts_backend=flow.tts_backend,
                    language=lang
                )
                logger.info(f"Generated audio: {audio_file}")
        
        # Generate dialplan
        logger.info("Generating dialplan...")
        session = wazo_session(wazo_host, token)
        queue_map = get_queues(session)
        dialplan_path = f"/etc/asterisk/extensions_extra.d/50-ivr-{flow.id}.conf"
        
        render_dialplan(flow, queue_map, dialplan_path)
        
        # Validate dialplan
        dialplan_errors = validate_dialplan(dialplan_path)
        if dialplan_errors:
            logger.warning(f"Dialplan validation warnings: {dialplan_errors}")
        
        # Reload dialplan
        logger.info("Reloading Asterisk dialplan...")
        if reload_dialplan():
            logger.info(f"Successfully built and deployed flow: {flow.id}")
            return True
        else:
            logger.error("Failed to reload dialplan")
            return False
            
    except Exception as e:
        logger.error(f"Failed to build flow: {e}")
        return False

def deploy_flow(flow_id: str, wazo_host: str, token: str) -> bool:
    """
    Deploy an existing flow to Wazo system
    
    Args:
        flow_id: ID of the flow to deploy
        wazo_host: Wazo server hostname/IP
        token: Wazo authentication token
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if flow exists
        flow_path = f"/var/lib/wazo-ivr/flows/{flow_id}.yml"
        if not os.path.exists(flow_path):
            logger.error(f"Flow file not found: {flow_path}")
            return False
        
        # Build and deploy
        return build_flow(flow_path, wazo_host, token)
        
    except Exception as e:
        logger.error(f"Failed to deploy flow {flow_id}: {e}")
        return False

def undeploy_flow(flow_id: str) -> bool:
    """
    Undeploy a flow from Wazo system
    
    Args:
        flow_id: ID of the flow to undeploy
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        dialplan_path = f"/etc/asterisk/extensions_extra.d/50-ivr-{flow_id}.conf"
        
        if os.path.exists(dialplan_path):
            os.unlink(dialplan_path)
            logger.info(f"Removed dialplan: {dialplan_path}")
        
        # Reload dialplan
        if reload_dialplan():
            logger.info(f"Successfully undeployed flow: {flow_id}")
            return True
        else:
            logger.error("Failed to reload dialplan after undeployment")
            return False
            
    except Exception as e:
        logger.error(f"Failed to undeploy flow {flow_id}: {e}")
        return False

def get_system_status(wazo_host: Optional[str] = None, token: Optional[str] = None) -> dict:
    """
    Get system status including TTS backends and Wazo connectivity
    
    Args:
        wazo_host: Wazo server hostname/IP (optional)
        token: Wazo authentication token (optional)
    
    Returns:
        dict: System status information
    """
    status = {
        "tts": get_tts_status(),
        "wazo": {"available": False, "error": None},
        "flows": {"deployed": [], "available": []}
    }
    
    # Check Wazo connectivity if credentials provided
    if wazo_host and token:
        try:
            session = wazo_session(wazo_host, token)
            wazo_status = get_wazo_status(session)
            status["wazo"] = wazo_status
        except Exception as e:
            status["wazo"]["error"] = str(e)
    
    # Check deployed flows
    dialplan_dir = "/etc/asterisk/extensions_extra.d"
    if os.path.exists(dialplan_dir):
        for filename in os.listdir(dialplan_dir):
            if filename.startswith("50-ivr-") and filename.endswith(".conf"):
                flow_id = filename[7:-5]  # Remove "50-ivr-" prefix and ".conf" suffix
                status["flows"]["deployed"].append(flow_id)
    
    # Check available flows
    flows_dir = "/var/lib/wazo-ivr/flows"
    if os.path.exists(flows_dir):
        for filename in os.listdir(flows_dir):
            if filename.endswith(('.yml', '.yaml', '.json')):
                flow_id = filename.rsplit('.', 1)[0]
                status["flows"]["available"].append(flow_id)
    
    return status

def cleanup_system(max_age_days: int = 30) -> bool:
    """
    Clean up old cache files and temporary data
    
    Args:
        max_age_days: Maximum age of files to keep
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        cleanup_cache(max_age_days)
        logger.info(f"System cleanup completed for files older than {max_age_days} days")
        return True
    except Exception as e:
        logger.error(f"System cleanup failed: {e}")
        return False

# Legacy function for backward compatibility
def build(flow_path, wazo_host, token):
    """Legacy build function - redirects to new function"""
    logger.warning("Using legacy build function - consider using build_flow")
    return build_flow(flow_path, wazo_host, token)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Wazo IVR System Plugin CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Build command
    build_parser = subparsers.add_parser('build', help='Build and deploy a flow')
    build_parser.add_argument("--flow", required=True, help="Path to flow configuration file")
    build_parser.add_argument("--wazo-host", required=True, help="Wazo server hostname/IP")
    build_parser.add_argument("--token", required=True, help="Wazo authentication token")
    build_parser.add_argument("--no-validate", action="store_true", help="Skip flow validation")
    
    # Deploy command
    deploy_parser = subparsers.add_parser('deploy', help='Deploy an existing flow')
    deploy_parser.add_argument("--flow-id", required=True, help="Flow ID to deploy")
    deploy_parser.add_argument("--wazo-host", required=True, help="Wazo server hostname/IP")
    deploy_parser.add_argument("--token", required=True, help="Wazo authentication token")
    
    # Undeploy command
    undeploy_parser = subparsers.add_parser('undeploy', help='Undeploy a flow')
    undeploy_parser.add_argument("--flow-id", required=True, help="Flow ID to undeploy")
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Get system status')
    status_parser.add_argument("--wazo-host", help="Wazo server hostname/IP")
    status_parser.add_argument("--token", help="Wazo authentication token")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up system')
    cleanup_parser.add_argument("--max-age-days", type=int, default=30, help="Maximum age of files to keep")
    
    args = parser.parse_args()
    
    if args.command == 'build':
        success = build_flow(args.flow, args.wazo_host, args.token, not args.no_validate)
        exit(0 if success else 1)
    elif args.command == 'deploy':
        success = deploy_flow(args.flow_id, args.wazo_host, args.token)
        exit(0 if success else 1)
    elif args.command == 'undeploy':
        success = undeploy_flow(args.flow_id)
        exit(0 if success else 1)
    elif args.command == 'status':
        status = get_system_status(args.wazo_host, args.token)
        print(f"System Status: {status}")
    elif args.command == 'cleanup':
        success = cleanup_system(args.max_age_days)
        exit(0 if success else 1)
    else:
        parser.print_help()
        exit(1)
