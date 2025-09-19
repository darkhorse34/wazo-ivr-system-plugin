import json, yaml
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class IVRFlow:
    id: str
    tenant: str = "default"
    entry_context: str = ""
    tts_backend: str = "polly"   # or "local"
    languages: list = field(default_factory=lambda:[{"code":"en-US","voice":"Joanna"}])
    prompts: Dict[str, Dict[str, Dict[str,str]]] = field(default_factory=dict)
    menus: Dict[str, Any] = field(default_factory=dict)
    recording: Dict[str, Any] = field(default_factory=lambda:{"enabled":False})

def load_flow(path:str)->IVRFlow:
    with open(path) as f:
        data = yaml.safe_load(f) if path.endswith((".yml",".yaml")) else json.load(f)
    flow = IVRFlow(**data)
    if not flow.entry_context:
        flow.entry_context = f"dp-ivr-{flow.id}"
    return flow
