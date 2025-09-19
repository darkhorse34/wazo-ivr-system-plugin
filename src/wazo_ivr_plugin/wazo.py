import requests, urllib3
urllib3.disable_warnings()

def wazo_session(host, token):
    s = requests.Session(); s.headers.update({"X-Auth-Token": token}); s.verify=False
    s.base = f"https://{host}"
    return s

def get_queues(s):
    r = s.get(s.base + "/api/confd/1.1/queues?recurse=false"); r.raise_for_status()
    out={}
    for q in r.json().get("items",[]):
        out[q["name"]] = {"context": q.get("context","ctx-queue"), "number": q.get("number","")}
    return out
