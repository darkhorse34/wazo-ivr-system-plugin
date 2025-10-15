import requests, urllib3
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

urllib3.disable_warnings()

# Configure logging
logger = logging.getLogger(__name__)

class WazoAPIError(Exception):
    """Custom exception for Wazo API errors"""
    pass

def wazo_session(host: str, token: str) -> requests.Session:
    """Create authenticated Wazo session"""
    session = requests.Session()
    session.headers.update({
        "X-Auth-Token": token,
        "Content-Type": "application/json"
    })
    session.verify = False
    session.base = f"https://{host}"
    return session

def _make_request(session: requests.Session, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
    """Make authenticated request to Wazo API"""
    url = f"{session.base}{endpoint}"
    
    try:
        response = session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json() if response.content else {}
    except requests.exceptions.RequestException as e:
        logger.error(f"Wazo API request failed: {e}")
        raise WazoAPIError(f"API request failed: {e}")

# Confd API functions
def get_queues(session: requests.Session) -> Dict[str, Dict[str, Any]]:
    """Get all queues from Wazo confd"""
    try:
        response = _make_request(session, "GET", "/api/confd/1.1/queues?recurse=false")
        queues = {}
        for queue in response.get("items", []):
            queues[queue["name"]] = {
                "id": queue.get("id"),
                "name": queue.get("name"),
                "context": queue.get("context", "ctx-queue"),
                "number": queue.get("number", ""),
                "strategy": queue.get("strategy", "leastrecent"),
                "timeout": queue.get("timeout", 20),
                "retry": queue.get("retry", 2),
                "music_on_hold": queue.get("music_on_hold", "default"),
                "service_level": queue.get("service_level", 20)
            }
        return queues
    except Exception as e:
        logger.error(f"Failed to get queues: {e}")
        return {}

def get_agents(session: requests.Session) -> Dict[str, Dict[str, Any]]:
    """Get all agents from Wazo confd"""
    try:
        response = _make_request(session, "GET", "/api/confd/1.1/agents?recurse=false")
        agents = {}
        for agent in response.get("items", []):
            agents[agent["number"]] = {
                "id": agent.get("id"),
                "number": agent.get("number"),
                "firstname": agent.get("firstname", ""),
                "lastname": agent.get("lastname", ""),
                "context": agent.get("context", "default"),
                "language": agent.get("language", "en_US"),
                "timezone": agent.get("timezone", "UTC"),
                "enabled": agent.get("enabled", True)
            }
        return agents
    except Exception as e:
        logger.error(f"Failed to get agents: {e}")
        return {}

def get_extensions(session: requests.Session) -> Dict[str, Dict[str, Any]]:
    """Get all extensions from Wazo confd"""
    try:
        response = _make_request(session, "GET", "/api/confd/1.1/extensions?recurse=false")
        extensions = {}
        for ext in response.get("items", []):
            extensions[ext["exten"]] = {
                "id": ext.get("id"),
                "exten": ext.get("exten"),
                "context": ext.get("context", "default"),
                "commented": ext.get("commented", False),
                "description": ext.get("description", "")
            }
        return extensions
    except Exception as e:
        logger.error(f"Failed to get extensions: {e}")
        return {}

def get_users(session: requests.Session) -> Dict[str, Dict[str, Any]]:
    """Get all users from Wazo confd"""
    try:
        response = _make_request(session, "GET", "/api/confd/1.1/users?recurse=false")
        users = {}
        for user in response.get("items", []):
            users[user["uuid"]] = {
                "id": user.get("id"),
                "uuid": user.get("uuid"),
                "firstname": user.get("firstname", ""),
                "lastname": user.get("lastname", ""),
                "email": user.get("email", ""),
                "username": user.get("username", ""),
                "enabled": user.get("enabled", True),
                "timezone": user.get("timezone", "UTC"),
                "language": user.get("language", "en_US")
            }
        return users
    except Exception as e:
        logger.error(f"Failed to get users: {e}")
        return {}

def get_schedules(session: requests.Session) -> Dict[str, Dict[str, Any]]:
    """Get all schedules from Wazo confd"""
    try:
        response = _make_request(session, "GET", "/api/confd/1.1/schedules?recurse=false")
        schedules = {}
        for schedule in response.get("items", []):
            schedules[schedule["name"]] = {
                "id": schedule.get("id"),
                "name": schedule.get("name"),
                "timezone": schedule.get("timezone", "UTC"),
                "enabled": schedule.get("enabled", True),
                "closed_destination": schedule.get("closed_destination", ""),
                "open_destination": schedule.get("open_destination", "")
            }
        return schedules
    except Exception as e:
        logger.error(f"Failed to get schedules: {e}")
        return {}

# Calld API functions
def get_calls(session: requests.Session) -> List[Dict[str, Any]]:
    """Get active calls from Wazo calld"""
    try:
        response = _make_request(session, "GET", "/api/calld/1.0/calls")
        return response.get("items", [])
    except Exception as e:
        logger.error(f"Failed to get calls: {e}")
        return []

def get_call(session: requests.Session, call_id: str) -> Optional[Dict[str, Any]]:
    """Get specific call from Wazo calld"""
    try:
        response = _make_request(session, "GET", f"/api/calld/1.0/calls/{call_id}")
        return response
    except Exception as e:
        logger.error(f"Failed to get call {call_id}: {e}")
        return None

def answer_call(session: requests.Session, call_id: str) -> bool:
    """Answer a call"""
    try:
        _make_request(session, "POST", f"/api/calld/1.0/calls/{call_id}/answer")
        return True
    except Exception as e:
        logger.error(f"Failed to answer call {call_id}: {e}")
        return False

def hangup_call(session: requests.Session, call_id: str) -> bool:
    """Hangup a call"""
    try:
        _make_request(session, "DELETE", f"/api/calld/1.0/calls/{call_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to hangup call {call_id}: {e}")
        return False

def transfer_call(session: requests.Session, call_id: str, destination: str) -> bool:
    """Transfer a call to destination"""
    try:
        data = {"destination": destination}
        _make_request(session, "POST", f"/api/calld/1.0/calls/{call_id}/transfer", json=data)
        return True
    except Exception as e:
        logger.error(f"Failed to transfer call {call_id} to {destination}: {e}")
        return False

def hold_call(session: requests.Session, call_id: str) -> bool:
    """Hold a call"""
    try:
        _make_request(session, "POST", f"/api/calld/1.0/calls/{call_id}/hold")
        return True
    except Exception as e:
        logger.error(f"Failed to hold call {call_id}: {e}")
        return False

def unhold_call(session: requests.Session, call_id: str) -> bool:
    """Unhold a call"""
    try:
        _make_request(session, "POST", f"/api/calld/1.0/calls/{call_id}/unhold")
        return True
    except Exception as e:
        logger.error(f"Failed to unhold call {call_id}: {e}")
        return False

def mute_call(session: requests.Session, call_id: str) -> bool:
    """Mute a call"""
    try:
        _make_request(session, "POST", f"/api/calld/1.0/calls/{call_id}/mute")
        return True
    except Exception as e:
        logger.error(f"Failed to mute call {call_id}: {e}")
        return False

def unmute_call(session: requests.Session, call_id: str) -> bool:
    """Unmute a call"""
    try:
        _make_request(session, "POST", f"/api/calld/1.0/calls/{call_id}/unmute")
        return True
    except Exception as e:
        logger.error(f"Failed to unmute call {call_id}: {e}")
        return False

def start_recording(session: requests.Session, call_id: str) -> bool:
    """Start recording a call"""
    try:
        _make_request(session, "POST", f"/api/calld/1.0/calls/{call_id}/record/start")
        return True
    except Exception as e:
        logger.error(f"Failed to start recording call {call_id}: {e}")
        return False

def stop_recording(session: requests.Session, call_id: str) -> bool:
    """Stop recording a call"""
    try:
        _make_request(session, "POST", f"/api/calld/1.0/calls/{call_id}/record/stop")
        return True
    except Exception as e:
        logger.error(f"Failed to stop recording call {call_id}: {e}")
        return False

# Dird API functions
def get_contacts(session: requests.Session, search: str = "") -> List[Dict[str, Any]]:
    """Search contacts in Wazo dird"""
    try:
        params = {"search": search} if search else {}
        response = _make_request(session, "GET", "/api/dird/1.0/contacts", params=params)
        return response.get("items", [])
    except Exception as e:
        logger.error(f"Failed to get contacts: {e}")
        return []

def get_contact(session: requests.Session, contact_id: str) -> Optional[Dict[str, Any]]:
    """Get specific contact from Wazo dird"""
    try:
        response = _make_request(session, "GET", f"/api/dird/1.0/contacts/{contact_id}")
        return response
    except Exception as e:
        logger.error(f"Failed to get contact {contact_id}: {e}")
        return None

def search_directory(session: requests.Session, query: str, profile: str = "default") -> List[Dict[str, Any]]:
    """Search directory using Wazo dird"""
    try:
        params = {"q": query, "profile": profile}
        response = _make_request(session, "GET", "/api/dird/1.0/directories/lookup", params=params)
        return response.get("results", [])
    except Exception as e:
        logger.error(f"Failed to search directory: {e}")
        return []

# Utility functions
def get_wazo_status(session: requests.Session) -> Dict[str, Any]:
    """Get overall Wazo system status"""
    try:
        status = {
            "confd": {"available": False, "error": None},
            "calld": {"available": False, "error": None},
            "dird": {"available": False, "error": None}
        }
        
        # Test confd
        try:
            _make_request(session, "GET", "/api/confd/1.1/status")
            status["confd"]["available"] = True
        except Exception as e:
            status["confd"]["error"] = str(e)
        
        # Test calld
        try:
            _make_request(session, "GET", "/api/calld/1.0/status")
            status["calld"]["available"] = True
        except Exception as e:
            status["calld"]["error"] = str(e)
        
        # Test dird
        try:
            _make_request(session, "GET", "/api/dird/1.0/status")
            status["dird"]["available"] = True
        except Exception as e:
            status["dird"]["error"] = str(e)
        
        return status
        
    except Exception as e:
        logger.error(f"Failed to get Wazo status: {e}")
        return {"error": str(e)}

def create_ivr_extension(session: requests.Session, flow_id: str, extension: str, context: str = "default") -> bool:
    """Create extension for IVR flow"""
    try:
        data = {
            "exten": extension,
            "context": context,
            "commented": False,
            "description": f"IVR Flow: {flow_id}"
        }
        _make_request(session, "POST", "/api/confd/1.1/extensions", json=data)
        return True
    except Exception as e:
        logger.error(f"Failed to create IVR extension {extension}: {e}")
        return False

def create_ivr_context(session: requests.Session, context_name: str, description: str = "") -> bool:
    """Create context for IVR flow"""
    try:
        data = {
            "name": context_name,
            "description": description or f"IVR Context: {context_name}",
            "type": "internal"
        }
        _make_request(session, "POST", "/api/confd/1.1/contexts", json=data)
        return True
    except Exception as e:
        logger.error(f"Failed to create IVR context {context_name}: {e}")
        return False
