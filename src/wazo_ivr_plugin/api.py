import os
from .flows import load_flow
from .tts import synthesize_polly, synthesize_local, SOUNDS_BASE
from .dialplan import render
from .wazo import wazo_session, get_queues

def build(flow_path, wazo_host, token):
    flow = load_flow(flow_path)
    # synthesize prompts to WAVs
    for prompt, cfg in flow.prompts.items():
        for lang, text in cfg["text"].items():
            out = f"{SOUNDS_BASE}/{flow.tenant}/{flow.id}/{prompt}_{lang}.wav"
            voice = next((v['voice'] for v in flow.languages if v['code']==lang), "Joanna")
            if flow.tts_backend == "polly":
                synthesize_polly(text, voice, out)
            else:
                synthesize_local(text, out)
    # render dialplan and reload
    s = wazo_session(wazo_host, token)
    qmap = get_queues(s)
    out_dp = f"/etc/asterisk/extensions_extra.d/{flow.entry_context}.conf"
    render(flow, qmap, out_dp)
    os.system("asterisk -rx 'dialplan reload'")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--flow", required=True)
    ap.add_argument("--wazo-host", required=True)
    ap.add_argument("--token", required=True)
    args = ap.parse_args()
    build(args.flow, args.wazo_host, args.token)
