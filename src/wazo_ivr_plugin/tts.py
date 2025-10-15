import os, subprocess, tempfile, boto3, logging
from typing import Optional, Dict, Any
from pathlib import Path
import hashlib

SOUNDS_BASE = "/var/lib/wazo/sounds/ivr"
CACHE_DIR = "/var/cache/wazo-ivr/tts"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Polly voice mappings for different languages
POLLY_VOICES = {
    "en-US": ["Joanna", "Matthew", "Kimberly", "Amy", "Brian", "Emma"],
    "en-GB": ["Emma", "Brian", "Amy", "Joanna"],
    "es-ES": ["Conchita", "Enrique"],
    "es-US": ["Lupe", "Miguel", "Penelope"],
    "fr-FR": ["Celine", "Mathieu", "Lea"],
    "de-DE": ["Marlene", "Hans", "Vicki"],
    "it-IT": ["Carla", "Giorgio"],
    "pt-BR": ["Camila", "Vitoria", "Ricardo"],
    "ja-JP": ["Mizuki", "Takumi"],
    "ko-KR": ["Seoyeon"],
    "zh-CN": ["Zhiyu"],
    "ru-RU": ["Tatyana", "Maxim"]
}

def _pcm_to_wav(pcm_path: str, wav_path: str, rate: str = "8000", channels: int = 1) -> None:
    """Convert PCM audio to WAV format using sox"""
    try:
        subprocess.check_call([
            "sox", "-t", "raw", "-r", rate, "-e", "signed", "-b", "16", 
            "-c", str(channels), pcm_path, wav_path
        ])
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to convert PCM to WAV: {e}")
        raise

def _get_cache_key(text: str, voice: str, engine: str) -> str:
    """Generate cache key for TTS audio"""
    content = f"{text}|{voice}|{engine}"
    return hashlib.md5(content.encode()).hexdigest()

def _get_cached_audio(cache_key: str) -> Optional[str]:
    """Check if audio is already cached"""
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.wav")
    if os.path.exists(cache_file):
        return cache_file
    return None

def _cache_audio(cache_key: str, audio_path: str) -> str:
    """Cache generated audio file"""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.wav")
    if not os.path.exists(cache_file):
        subprocess.check_call(["cp", audio_path, cache_file])
    return cache_file

def synthesize_polly(
    text: str, 
    voice: str, 
    out_wav: str, 
    region: Optional[str] = None,
    engine: str = "neural",
    sample_rate: str = "8000",
    use_cache: bool = True
) -> None:
    """Synthesize speech using Amazon Polly"""
    os.makedirs(os.path.dirname(out_wav), exist_ok=True)
    
    # Check cache first
    if use_cache:
        cache_key = _get_cache_key(text, voice, engine)
        cached_file = _get_cached_audio(cache_key)
        if cached_file:
            subprocess.check_call(["cp", cached_file, out_wav])
            logger.info(f"Using cached audio for: {text[:50]}...")
            return
    
    try:
        # Configure Polly client
        polly_config = {
            "region_name": region or os.getenv("AWS_REGION", "us-east-1")
        }
        
        # Add credentials if available
        if os.getenv("AWS_ACCESS_KEY_ID"):
            polly_config["aws_access_key_id"] = os.getenv("AWS_ACCESS_KEY_ID")
        if os.getenv("AWS_SECRET_ACCESS_KEY"):
            polly_config["aws_secret_access_key"] = os.getenv("AWS_SECRET_ACCESS_KEY")
        
        polly = boto3.client("polly", **polly_config)
        
        # Synthesize speech
        response = polly.synthesize_speech(
            Text=text,
            OutputFormat="pcm",
            SampleRate=sample_rate,
            VoiceId=voice,
            Engine=engine
        )
        
        # Convert PCM to WAV
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pcm") as tmp_pcm:
            tmp_pcm.write(response["AudioStream"].read())
            tmp_pcm_path = tmp_pcm.name
        
        _pcm_to_wav(tmp_pcm_path, out_wav, sample_rate)
        os.unlink(tmp_pcm_path)
        
        # Cache the result
        if use_cache:
            _cache_audio(cache_key, out_wav)
        
        logger.info(f"Generated Polly audio: {out_wav}")
        
    except Exception as e:
        logger.error(f"Polly synthesis failed: {e}")
        # Fallback to local TTS
        logger.info("Falling back to local TTS")
        synthesize_local(text, out_wav)

def synthesize_local(
    text: str, 
    out_wav: str, 
    voice: str = "slt",
    engine: str = "flite"
) -> None:
    """Synthesize speech using local TTS engine"""
    os.makedirs(os.path.dirname(out_wav), exist_ok=True)
    
    try:
        if engine == "flite":
            subprocess.check_call([
                "flite", "-voice", voice, "-t", text, "-o", out_wav
            ])
        elif engine == "espeak":
            subprocess.check_call([
                "espeak", "-v", voice, "-s", "150", "-w", out_wav, text
            ])
        elif engine == "festival":
            # Create temporary script for festival
            script_content = f'(tts_text "{text}" "{out_wav}")'
            with tempfile.NamedTemporaryFile(mode='w', suffix='.scm', delete=False) as script_file:
                script_file.write(script_content)
                script_path = script_file.name
            
            subprocess.check_call([
                "festival", "--script", script_path
            ])
            os.unlink(script_path)
        else:
            raise ValueError(f"Unsupported local TTS engine: {engine}")
        
        logger.info(f"Generated local audio: {out_wav}")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Local TTS synthesis failed: {e}")
        # Create a silent audio file as fallback
        _create_silent_audio(out_wav, duration=2.0)

def _create_silent_audio(out_wav: str, duration: float = 2.0) -> None:
    """Create a silent audio file as fallback"""
    try:
        subprocess.check_call([
            "sox", "-n", "-r", "8000", "-c", "1", out_wav, 
            "trim", "0", str(duration)
        ])
        logger.warning(f"Created silent audio fallback: {out_wav}")
    except subprocess.CalledProcessError:
        logger.error("Failed to create silent audio fallback")

def get_available_voices(language: str = "en-US") -> list:
    """Get available voices for a language"""
    if language in POLLY_VOICES:
        return POLLY_VOICES[language]
    return POLLY_VOICES.get("en-US", ["Joanna"])

def get_default_voice(language: str = "en-US") -> str:
    """Get default voice for a language"""
    voices = get_available_voices(language)
    return voices[0] if voices else "Joanna"

def validate_voice(voice: str, language: str = "en-US") -> bool:
    """Validate if voice is available for language"""
    available_voices = get_available_voices(language)
    return voice in available_voices

def synthesize_text(
    text: str,
    voice: str,
    out_wav: str,
    tts_backend: str = "polly",
    language: str = "en-US",
    **kwargs
) -> None:
    """Main synthesis function that routes to appropriate TTS backend"""
    if tts_backend == "polly":
        # Validate voice for language
        if not validate_voice(voice, language):
            voice = get_default_voice(language)
            logger.warning(f"Voice not available for {language}, using {voice}")
        
        synthesize_polly(text, voice, out_wav, **kwargs)
    elif tts_backend == "local":
        synthesize_local(text, out_wav, voice, **kwargs)
    else:
        raise ValueError(f"Unsupported TTS backend: {tts_backend}")

def cleanup_cache(max_age_days: int = 30) -> None:
    """Clean up old cached audio files"""
    if not os.path.exists(CACHE_DIR):
        return
    
    import time
    current_time = time.time()
    max_age_seconds = max_age_days * 24 * 60 * 60
    
    for filename in os.listdir(CACHE_DIR):
        file_path = os.path.join(CACHE_DIR, filename)
        if os.path.isfile(file_path):
            file_age = current_time - os.path.getmtime(file_path)
            if file_age > max_age_seconds:
                os.unlink(file_path)
                logger.info(f"Cleaned up old cache file: {filename}")

def get_tts_status() -> Dict[str, Any]:
    """Get status of TTS backends"""
    status = {
        "polly": {"available": False, "error": None},
        "local": {"available": False, "engines": []}
    }
    
    # Check Polly
    try:
        boto3.client("polly", region_name="us-east-1")
        status["polly"]["available"] = True
    except Exception as e:
        status["polly"]["error"] = str(e)
    
    # Check local engines
    local_engines = ["flite", "espeak", "festival"]
    for engine in local_engines:
        try:
            subprocess.check_call([engine, "--version"], 
                                stdout=subprocess.DEVNULL, 
                                stderr=subprocess.DEVNULL)
            status["local"]["engines"].append(engine)
            status["local"]["available"] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
    
    return status
