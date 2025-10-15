from jinja2 import Template
import logging
from typing import Dict, Any, List
from .flows import IVRFlow, IVRMenu, is_business_hours

# Configure logging
logger = logging.getLogger(__name__)

# Enhanced dialplan template with support for multi-level menus, business hours, and fallback logic
DPTPL = """\
; ===== IVR Flow: {{ flow_id }} =====
; Generated: {{ generated_at }}
; Tenant: {{ tenant }}

[{{ entry_context }}]
; Main entry point
exten => s,1,NoOp(IVR {{ flow_id }} - Call from ${CALLERID(num)})
 same => n,Answer()
 same => n,Set(GV_DIR={{ sounds_dir }})
 same => n,Set(GV_FLOW_ID={{ flow_id }})
 same => n,Set(GV_TENANT={{ tenant }})
 same => n,Set(GV_CALLER_LANG={{ default_language }})
 same => n,Set(GV_MENU_LEVEL=0)
 same => n,Set(GV_RETRY_COUNT=0)
 same => n,Set(GV_MAX_RETRIES={{ max_retries }})
{% if business_hours %}
 same => n,GosubIf($["{{ business_hours_check }}"="1"]?business-hours,1,1)
{% endif %}
{% if call_recording.enabled %}
 same => n,ExecIf($["{{ call_recording.enabled }}"="true"]?MixMonitor(${UNIQUEID}.{{ call_recording.format }}))
{% endif %}
 same => n,Goto(menu-{{ root_menu_id }},s,1)

{% for menu_id, menu in menus.items() %}
; ===== Menu: {{ menu_id }} =====
[menu-{{ menu_id }}]
exten => s,1,NoOp(Menu {{ menu_id }} - Level ${GV_MENU_LEVEL})
 same => n,Set(GV_CURRENT_MENU={{ menu_id }})
 same => n,Set(GV_MENU_LEVEL=$[${GV_MENU_LEVEL}+1])
 same => n,Playback(${GV_DIR}/{{ menu.prompt }}_${GV_CALLER_LANG})
 same => n,WaitExten({{ menu.timeout_sec }})

{% for option_key, option in menu.options.items() %}
exten => {{ option_key }},1,NoOp(Option {{ option_key }}: {{ option.action }})
{% if option.action == 'menu' %}
 same => n,Set(GV_RETRY_COUNT=0)
 same => n,Goto(menu-{{ option.menu_ref }},s,1)
{% elif option.action == 'queue' %}
 same => n,Set(GV_RETRY_COUNT=0)
 same => n,ExecIf($["{{ recording_enabled }}"="true"]?MixMonitor(${UNIQUEID}.wav))
 same => n,Queue({{ option.queue_ref }},tTk)
 same => n,Hangup()
{% elif option.action == 'extension' %}
 same => n,Set(GV_RETRY_COUNT=0)
 same => n,ExecIf($["{{ recording_enabled }}"="true"]?MixMonitor(${UNIQUEID}.wav))
 same => n,Goto({{ option.context }},{{ option.extension }},1)
{% elif option.action == 'voicemail' %}
 same => n,Set(GV_RETRY_COUNT=0)
 same => n,ExecIf($["{{ recording_enabled }}"="true"]?MixMonitor(${UNIQUEID}.wav))
 same => n,Voicemail({{ option.voicemail_box }}@{{ option.context }},u)
 same => n,Hangup()
{% elif option.action == 'hangup' %}
 same => n,Playback(${GV_DIR}/{{ option.prompt }}_${GV_CALLER_LANG})
 same => n,Hangup()
{% elif option.action == 'transfer' %}
 same => n,Set(GV_RETRY_COUNT=0)
 same => n,ExecIf($["{{ recording_enabled }}"="true"]?MixMonitor(${UNIQUEID}.wav))
 same => n,Dial({{ option.destination }},{{ option.timeout|default(30) }})
 same => n,Hangup()
{% elif option.action == 'language' %}
 same => n,Set(GV_CALLER_LANG={{ option.language }})
 same => n,Playback(${GV_DIR}/{{ option.prompt }}_${GV_CALLER_LANG})
 same => n,Goto(menu-{{ menu_id }},s,1)
{% endif %}

{% endfor %}

; Timeout handling for {{ menu_id }}
exten => t,1,NoOp(Timeout in menu {{ menu_id }})
 same => n,Set(GV_RETRY_COUNT=$[${GV_RETRY_COUNT}+1])
 same => n,GotoIf($[${GV_RETRY_COUNT} < {{ menu.max_retries }}]?retry-{{ menu_id }})
 same => n,Goto(fallback-{{ menu_id }},1,1)

; Invalid input handling for {{ menu_id }}
exten => i,1,NoOp(Invalid input in menu {{ menu_id }})
 same => n,Set(GV_RETRY_COUNT=$[${GV_RETRY_COUNT}+1])
 same => n,GotoIf($[${GV_RETRY_COUNT} < {{ menu.max_retries }}]?retry-{{ menu_id }})
 same => n,Goto(fallback-{{ menu_id }},1,1)

; Retry logic for {{ menu_id }}
exten => retry-{{ menu_id }},1,NoOp(Retry {{ menu_id }} - Attempt ${GV_RETRY_COUNT})
 same => n,Playback(${GV_DIR}/invalid_${GV_CALLER_LANG})
 same => n,Goto(menu-{{ menu_id }},s,1)

; Fallback handling for {{ menu_id }}
exten => fallback-{{ menu_id }},1,NoOp(Fallback for {{ menu_id }})
{% if menu.fallback_action == 'voicemail' %}
 same => n,Playback(${GV_DIR}/voicemail_${GV_CALLER_LANG})
 same => n,Voicemail({{ voicemail_fallback|default('1000') }}@{{ tenant }},u)
{% elif menu.fallback_action == 'queue' %}
 same => n,Playback(${GV_DIR}/transfer_${GV_CALLER_LANG})
 same => n,Queue({{ fallback_queue|default('support') }},tTk)
{% elif menu.fallback_action == 'hangup' %}
 same => n,Playback(${GV_DIR}/goodbye_${GV_CALLER_LANG})
{% else %}
 same => n,Playback(${GV_DIR}/invalid_${GV_CALLER_LANG})
{% endif %}
 same => n,Hangup()

{% endfor %}

{% if business_hours %}
; ===== Business Hours Check =====
[business-hours]
exten => 1,1,NoOp(Business hours check)
 same => n,Set(GV_BUSINESS_HOURS={{ business_hours_check }})
 same => n,Return()

; ===== After Hours Handling =====
[after-hours]
exten => s,1,NoOp(After hours - {{ flow_id }})
 same => n,Answer()
 same => n,Set(GV_DIR={{ sounds_dir }})
 same => n,Playback(${GV_DIR}/after-hours_${GV_CALLER_LANG})
{% if voicemail_fallback %}
 same => n,Voicemail({{ voicemail_fallback }}@{{ tenant }},u)
{% else %}
 same => n,Hangup()
{% endif %}
{% endif %}

; ===== Language Selection =====
[language-selection]
exten => s,1,NoOp(Language selection)
 same => n,Answer()
 same => n,Set(GV_DIR={{ sounds_dir }})
 same => n,Playback(${GV_DIR}/language-prompt_${GV_CALLER_LANG})
 same => n,WaitExten(10)

{% for lang in languages %}
exten => {{ lang.code }},1,NoOp(Set language to {{ lang.code }})
 same => n,Set(GV_CALLER_LANG={{ lang.code }})
 same => n,Playback(${GV_DIR}/language-confirmed_${GV_CALLER_LANG})
 same => n,Goto(menu-{{ root_menu_id }},s,1)
{% endfor %}

exten => t,1,NoOp(Language selection timeout)
 same => n,Set(GV_CALLER_LANG={{ default_language }})
 same => n,Goto(menu-{{ root_menu_id }},s,1)

exten => i,1,NoOp(Invalid language selection)
 same => n,Playback(${GV_DIR}/invalid_${GV_CALLER_LANG})
 same => n,Goto(language-selection,s,1)
"""

def render_dialplan(flow: IVRFlow, queue_map: Dict[str, Any], out_path: str) -> None:
    """Render enhanced dialplan for IVR flow"""
    try:
        # Prepare template data
        sounds_dir = f"/var/lib/wazo/sounds/ivr/{flow.tenant}/{flow.id}"
        default_language = flow.languages[0]['code'] if flow.languages else 'en-US'
        max_retries = max((menu.max_retries for menu in flow.menus.values()), default=3)
        
        # Business hours check
        business_hours_check = "1" if is_business_hours(flow) else "0"
        
        # Find root menu (menu without parent)
        root_menu_id = None
        for menu_id, menu in flow.menus.items():
            if not menu.parent_menu:
                root_menu_id = menu_id
                break
        
        if not root_menu_id:
            raise ValueError("No root menu found in flow")
        
        # Prepare template context
        context = {
            'flow_id': flow.id,
            'tenant': flow.tenant,
            'entry_context': flow.entry_context,
            'sounds_dir': sounds_dir,
            'menus': flow.menus,
            'languages': flow.languages,
            'default_language': default_language,
            'max_retries': max_retries,
            'root_menu_id': root_menu_id,
            'recording_enabled': str(bool(flow.recording.get("enabled", False))).lower(),
            'call_recording': flow.call_recording,
            'business_hours': flow.business_hours,
            'business_hours_check': business_hours_check,
            'voicemail_fallback': flow.voicemail_fallback,
            'fallback_queue': 'support',  # Default fallback queue
            'generated_at': flow.updated_at
        }
        
        # Render dialplan
        template = Template(DPTPL)
        dialplan_content = template.render(**context)
        
        # Write dialplan file
        with open(out_path, 'w') as f:
            f.write(dialplan_content)
        
        logger.info(f"Generated dialplan for flow {flow.id}: {out_path}")
        
    except Exception as e:
        logger.error(f"Failed to render dialplan for flow {flow.id}: {e}")
        raise

def create_ivr_context_dialplan(flow: IVRFlow, out_path: str) -> None:
    """Create context-specific dialplan for IVR flow"""
    context_template = """\
; ===== IVR Context: {{ flow_id }} =====
; This context handles incoming calls to the IVR flow

[{{ entry_context }}-incoming]
exten => _X.,1,NoOp(Incoming call to IVR {{ flow_id }})
 same => n,Goto({{ entry_context }},s,1)

; ===== Direct Queue Access =====
[{{ entry_context }}-queues]
{% for queue_name, queue_info in queues.items() %}
exten => {{ queue_info.number }},1,NoOp(Direct queue access: {{ queue_name }})
 same => n,Answer()
 same => n,Queue({{ queue_name }},tTk)
 same => n,Hangup()
{% endfor %}
"""
    
    try:
        from .wazo import get_queues
        
        # Get queue information (this would need a session in real usage)
        queue_map = {}  # Placeholder - would be populated with actual queue data
        
        template = Template(context_template)
        context_content = template.render(
            flow_id=flow.id,
            entry_context=flow.entry_context,
            queues=queue_map
        )
        
        with open(out_path, 'w') as f:
            f.write(context_content)
        
        logger.info(f"Generated context dialplan for flow {flow.id}: {out_path}")
        
    except Exception as e:
        logger.error(f"Failed to create context dialplan for flow {flow.id}: {e}")
        raise

def validate_dialplan(dialplan_path: str) -> List[str]:
    """Validate generated dialplan syntax"""
    errors = []
    
    try:
        import subprocess
        result = subprocess.run(
            ['asterisk', '-rx', f'dialplan show {dialplan_path}'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            errors.append(f"Dialplan validation failed: {result.stderr}")
        
    except subprocess.TimeoutExpired:
        errors.append("Dialplan validation timed out")
    except FileNotFoundError:
        errors.append("Asterisk not found for validation")
    except Exception as e:
        errors.append(f"Dialplan validation error: {e}")
    
    return errors

def reload_dialplan() -> bool:
    """Reload Asterisk dialplan"""
    try:
        import subprocess
        result = subprocess.run(
            ['asterisk', '-rx', 'dialplan reload'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info("Dialplan reloaded successfully")
            return True
        else:
            logger.error(f"Failed to reload dialplan: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to reload dialplan: {e}")
        return False

# Legacy function for backward compatibility
def render(flow, queue_map, out_path):
    """Legacy render function - redirects to new function"""
    logger.warning("Using legacy render function - consider using render_dialplan")
    return render_dialplan(flow, queue_map, out_path)
