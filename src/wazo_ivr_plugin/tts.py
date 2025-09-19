import os, subprocess, tempfile, boto3
SOUNDS_BASE = "/var/lib/wazo/sounds/ivr"

def _pcm_to_wav(pcm_path, wav_path, rate="8000"):
    subprocess.check_call(["sox", "-t", "raw", "-r", rate, "-e", "signed", "-b", "16", "-c", "1", pcm_path, wav_path])

def synthesize_polly(text:str, voice:str, out_wav:str, region=None):
    os.makedirs(os.path.dirname(out_wav), exist_ok=True)
    polly = boto3.client("polly", region_name=region or os.getenv("AWS_REGION","us-east-1"))
    r = polly.synthesize_speech(Text=text, OutputFormat="pcm", SampleRate="8000", VoiceId=voice)
    with tempfile.NamedTemporaryFile(delete=False) as t:
        t.write(r["AudioStream"].read()); tmp_pcm = t.name
    _pcm_to_wav(tmp_pcm, out_wav, "8000"); os.unlink(tmp_pcm)

def synthesize_local(text:str, out_wav:str):
    os.makedirs(os.path.dirname(out_wav), exist_ok=True)
    subprocess.check_call(["flite", "-voice", "slt", "-t", text, "-o", out_wav])
