import json, yaml
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime, time
import uuid

@dataclass
class IVRMenu:
    id: str
    prompt: str
    timeout_sec: int = 5
    max_retries: int = 3
    options: Dict[str, Any] = field(default_factory=dict)
    fallback_action: Optional[str] = None
    parent_menu: Optional[str] = None

@dataclass
class BusinessHours:
    name: str
    timeframes: Dict[str, List[str]] = field(default_factory=dict)  # day -> [time_ranges]
    timezone: str = "UTC"

@dataclass
class IVRFlow:
    id: str
    tenant: str = "default"
    entry_context: str = ""
    tts_backend: str = "polly"   # or "local"
    languages: List[Dict[str, str]] = field(default_factory=lambda:[{"code":"en-US","voice":"Joanna"}])
    prompts: Dict[str, Dict[str, Dict[str,str]]] = field(default_factory=dict)
    menus: Dict[str, IVRMenu] = field(default_factory=dict)
    recording: Dict[str, Any] = field(default_factory=lambda:{"enabled":False})
    business_hours: Optional[BusinessHours] = None
    voicemail_fallback: Optional[str] = None
    call_recording: Dict[str, Any] = field(default_factory=lambda:{"enabled":False, "format":"wav"})
    max_call_duration: int = 300  # 5 minutes default
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        if not self.entry_context:
            self.entry_context = f"dp-ivr-{self.id}"
        
        # Convert menu dicts to IVRMenu objects
        if isinstance(self.menus, dict):
            menu_objects = {}
            for menu_id, menu_data in self.menus.items():
                if isinstance(menu_data, dict):
                    menu_objects[menu_id] = IVRMenu(id=menu_id, **menu_data)
                else:
                    menu_objects[menu_id] = menu_data
            self.menus = menu_objects

def load_flow(path: str) -> IVRFlow:
    """Load IVR flow from YAML or JSON file"""
    with open(path) as f:
        data = yaml.safe_load(f) if path.endswith((".yml",".yaml")) else json.load(f)
    
    # Handle business hours
    if 'business_hours' in data and isinstance(data['business_hours'], dict):
        data['business_hours'] = BusinessHours(**data['business_hours'])
    
    flow = IVRFlow(**data)
    return flow

def save_flow(flow: IVRFlow, path: str) -> None:
    """Save IVR flow to YAML or JSON file"""
    flow.updated_at = datetime.now().isoformat()
    
    # Convert to dict for serialization
    data = {
        'id': flow.id,
        'tenant': flow.tenant,
        'entry_context': flow.entry_context,
        'tts_backend': flow.tts_backend,
        'languages': flow.languages,
        'prompts': flow.prompts,
        'menus': {menu_id: {
            'id': menu.id,
            'prompt': menu.prompt,
            'timeout_sec': menu.timeout_sec,
            'max_retries': menu.max_retries,
            'options': menu.options,
            'fallback_action': menu.fallback_action,
            'parent_menu': menu.parent_menu
        } for menu_id, menu in flow.menus.items()},
        'recording': flow.recording,
        'business_hours': {
            'name': flow.business_hours.name,
            'timeframes': flow.business_hours.timeframes,
            'timezone': flow.business_hours.timezone
        } if flow.business_hours else None,
        'voicemail_fallback': flow.voicemail_fallback,
        'call_recording': flow.call_recording,
        'max_call_duration': flow.max_call_duration,
        'created_at': flow.created_at,
        'updated_at': flow.updated_at
    }
    
    with open(path, 'w') as f:
        if path.endswith(('.yml', '.yaml')):
            yaml.dump(data, f, default_flow_style=False, indent=2)
        else:
            json.dump(data, f, indent=2)

def is_business_hours(flow: IVRFlow) -> bool:
    """Check if current time is within business hours"""
    if not flow.business_hours:
        return True
    
    now = datetime.now()
    current_day = now.strftime('%A').lower()
    current_time = now.time()
    
    if current_day not in flow.business_hours.timeframes:
        return False
    
    for time_range in flow.business_hours.timeframes[current_day]:
        start_str, end_str = time_range.split('-')
        start_time = datetime.strptime(start_str, '%H:%M').time()
        end_time = datetime.strptime(end_str, '%H:%M').time()
        
        if start_time <= current_time <= end_time:
            return True
    
    return False

def validate_flow(flow: IVRFlow) -> List[str]:
    """Validate IVR flow configuration and return list of errors"""
    errors = []
    
    # Check required fields
    if not flow.id:
        errors.append("Flow ID is required")
    
    if not flow.menus:
        errors.append("At least one menu is required")
    
    # Check menu references
    for menu_id, menu in flow.menus.items():
        if not menu.prompt:
            errors.append(f"Menu '{menu_id}' must have a prompt")
        
        # Check option references
        for option_key, option_data in menu.options.items():
            if isinstance(option_data, dict):
                action = option_data.get('action')
                if action == 'menu' and option_data.get('menu_ref') not in flow.menus:
                    errors.append(f"Menu '{menu_id}' option '{option_key}' references non-existent menu '{option_data.get('menu_ref')}'")
                elif action == 'queue' and not option_data.get('queue_ref'):
                    errors.append(f"Menu '{menu_id}' option '{option_key}' queue action missing queue_ref")
    
    # Check prompt references
    for menu_id, menu in flow.menus.items():
        if menu.prompt not in flow.prompts:
            errors.append(f"Menu '{menu_id}' references non-existent prompt '{menu.prompt}'")
    
    return errors
