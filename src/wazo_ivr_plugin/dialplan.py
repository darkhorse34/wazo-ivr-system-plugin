from jinja2 import Template

DPTPL = """\
[{{ entry_context }}]
exten => s,1,NoOp(IVR {{ flow_id }} root)
 same => n,Answer()
 same => n,Set(GV_DIR={{ sounds_dir }})
 same => n,Background(${GV_DIR}/{{ menus.root.prompt }}_en-US)
 same => n,WaitExten({{ menus.root.timeout_sec|default(5) }})

exten => 1,1,NoOp(Route to sales)
 same => n,ExecIf($["{{ recording_enabled }}"="true"]?MixMonitor(${UNIQUEID}.wav))
 same => n,Goto({{ sales_ctx }},{{ sales_exten }},1)

exten => 2,1,NoOp(Route to support)
 same => n,ExecIf($["{{ recording_enabled }}"="true"]?MixMonitor(${UNIQUEID}.wav))
 same => n,Goto({{ support_ctx }},{{ support_exten }},1)

exten => t,1,Playback(${GV_DIR}/invalid_en-US)
 same => n,Hangup()

exten => i,1,Playback(${GV_DIR}/invalid_en-US)
 same => n,Hangup()
"""

def render(flow, queue_map, out_path):
    sounds_dir = f"/var/lib/wazo/sounds/ivr/{flow.tenant}/{flow.id}"
    sales = queue_map["sales_q"]
    support = queue_map["support_q"]
    dialplan = Template(DPTPL).render(
        entry_context=flow.entry_context,
        flow_id=flow.id,
        sounds_dir=sounds_dir,
        menus=flow.menus,
        recording_enabled=str(bool(flow.recording.get("enabled",False))).lower(),
        sales_ctx=sales["context"], sales_exten=sales["number"],
        support_ctx=support["context"], support_exten=support["number"],
    )
    with open(out_path,"w") as f: f.write(dialplan)
