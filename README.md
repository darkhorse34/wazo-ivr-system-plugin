# Wazo IVR System Plugin

A comprehensive IVR (Interactive Voice Response) system plugin for Wazo UC platform that provides advanced call routing, multi-language support, and seamless integration with Wazo services.

## Features

### Core Features
- **Multi-level IVR menus** with DTMF input handling
- **Dynamic IVR flow definition** via API or configuration files (JSON/YAML)
- **Dual TTS backends**: Amazon Polly and local TTS engines (Flite, eSpeak, Festival)
- **Time-of-day and business-hours-based routing** logic
- **Queue and agent routing** with Wazo's calld module
- **Language selection support** for multilingual menus
- **Call recording triggers** and voicemail fallback paths
- **Fallback handling** for invalid/no input with configurable retries

### Advanced Features
- **RESTful API** for provisioning and CRM integration
- **Real-time Wazo integration** (calld, confd, dird)
- **Comprehensive logging** and monitoring
- **Audio caching** for improved performance
- **Flow validation** and error handling
- **CLI tools** for management and deployment

### Optional Features
- **Web GUI** for IVR tree configuration (React-based)
- **Speech-to-text (STT)** for voice input-driven navigation
- **Dynamic caller context** passing to agents
- **Plugin version control** and import/export of IVR flows
- **Dockerized testing** and CI/CD deployment support

## Requirements

- **Wazo UC Platform**: Version 22.0 or higher
- **Python**: 3.8 or higher
- **Asterisk**: Included with Wazo
- **System Dependencies**: sox, flite, espeak, festival
- **Python Dependencies**: boto3, flask, requests, pyyaml, jinja2

## Installation

### Quick Install

```bash
# Download and run the installation script
curl -sSL https://github.com/darkhorse34/wazo-ivr-system-plugin/main/install.sh | sudo bash
```

### Manual Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/darkhorse34/wazo-ivr-system-plugin.git
   cd wazo-ivr-system-plugin
   ```

2. **Run the installation script**:
   ```bash
   sudo ./install.sh
   ```

3. **Configure AWS credentials** (if using Polly TTS):
   ```bash
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_REGION=us-east-1
   ```

4. **Verify installation**:
   ```bash
   wazo-ivr status
   ```

## Configuration

### Basic Configuration

The plugin configuration is located at `/etc/wazo-ivr/config.yml`:

```yaml
# REST API Configuration
api:
  host: "0.0.0.0"
  port: 5000
  debug: false

# TTS Configuration
tts:
  default_backend: "polly"  # or "local"
  cache_enabled: true
  cache_max_age_days: 30

# AWS Polly Configuration
aws:
  region: "us-east-1"

# Local TTS Configuration
local_tts:
  default_engine: "flite"
  default_voice: "slt"
```

### Flow Configuration

IVR flows are defined in YAML or JSON format. Here's a basic example:

```yaml
id: sales
tenant: default
entry_context: dp-ivr-sales
tts_backend: polly
languages:
  - code: en-US
    voice: Joanna
  - code: es-US
    voice: Lupe

prompts:
  welcome:
    text:
      en-US: "Welcome to ACME. For Sales press 1, for Support press 2."
      es-US: "Bienvenido a ACME. Para Ventas presione 1, para Soporte presione 2."

menus:
  root:
    id: root
    prompt: welcome
    timeout_sec: 10
    max_retries: 3
    options:
      "1": 
        action: queue
        queue_ref: sales_q
      "2": 
        action: queue
        queue_ref: support_q
    fallback_action: voicemail

business_hours:
  name: business-hours
  timeframes:
    monday: ["09:00-17:00"]
    tuesday: ["09:00-17:00"]
    wednesday: ["09:00-17:00"]
    thursday: ["09:00-17:00"]
    friday: ["09:00-17:00"]
  timezone: "America/New_York"

voicemail_fallback: "1000"
call_recording:
  enabled: true
  format: "wav"
```

## Usage

### CLI Commands

The plugin provides a comprehensive CLI tool:

```bash
# Get system status
wazo-ivr status

# Build and deploy a flow
wazo-ivr build --flow /path/to/flow.yml --wazo-host your-wazo-host --token your-token

# Deploy an existing flow
wazo-ivr deploy --flow-id sales --wazo-host your-wazo-host --token your-token

# Undeploy a flow
wazo-ivr undeploy --flow-id sales

# Clean up old cache files
wazo-ivr cleanup --max-age-days 30
```

### REST API

The plugin exposes a REST API for programmatic access:

#### Flow Management

```bash
# List all flows
curl -X GET http://localhost:5000/api/ivr/flows

# Create a new flow
curl -X POST http://localhost:5000/api/ivr/flows \
  -H "Content-Type: application/json" \
  -d @flow.json

# Get a specific flow
curl -X GET http://localhost:5000/api/ivr/flows/sales

# Update a flow
curl -X PUT http://localhost:5000/api/ivr/flows/sales \
  -H "Content-Type: application/json" \
  -d @updated-flow.json

# Delete a flow
curl -X DELETE http://localhost:5000/api/ivr/flows/sales

# Deploy a flow
curl -X POST http://localhost:5000/api/ivr/flows/sales/deploy \
  -H "Content-Type: application/json" \
  -d '{"wazo_host": "your-wazo-host", "token": "your-token"}'
```

#### TTS Management

```bash
# Get available voices
curl -X GET "http://localhost:5000/api/ivr/tts/voices?language=en-US"

# Synthesize speech for testing
curl -X POST http://localhost:5000/api/ivr/tts/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test", "voice": "Joanna", "language": "en-US"}'
```

#### Wazo Integration

```bash
# Get Wazo queues
curl -X GET "http://localhost:5000/api/ivr/wazo/queues?wazo_host=your-host&token=your-token"

# Get Wazo agents
curl -X GET "http://localhost:5000/api/ivr/wazo/agents?wazo_host=your-host&token=your-token"
```

### Flow Actions

The plugin supports various flow actions:

- **`menu`**: Navigate to another menu
- **`queue`**: Transfer to a Wazo queue
- **`extension`**: Transfer to a specific extension
- **`voicemail`**: Transfer to voicemail
- **`hangup`**: End the call
- **`transfer`**: Transfer to external number
- **`language`**: Change caller's language

### Business Hours

Configure time-based routing:

```yaml
business_hours:
  name: business-hours
  timeframes:
    monday: ["09:00-17:00"]
    tuesday: ["09:00-17:00"]
    wednesday: ["09:00-17:00"]
    thursday: ["09:00-17:00"]
    friday: ["09:00-17:00"]
    saturday: ["10:00-14:00"]
  timezone: "America/New_York"
```

### Multi-language Support

Support multiple languages with different voices:

```yaml
languages:
  - code: en-US
    voice: Joanna
  - code: es-US
    voice: Lupe
  - code: fr-FR
    voice: Celine
  - code: de-DE
    voice: Marlene
```

## TTS Backends

### Amazon Polly

High-quality neural voices with extensive language support:

```yaml
tts_backend: polly
languages:
  - code: en-US
    voice: Joanna  # Neural voice
  - code: en-US
    voice: Matthew # Standard voice
```

**Setup**:
1. Create AWS account and IAM user
2. Set environment variables:
   ```bash
   export AWS_ACCESS_KEY_ID=your_key
   export AWS_SECRET_ACCESS_KEY=your_secret
   export AWS_REGION=us-east-1
   ```

### Local TTS

Use local TTS engines for offline operation:

```yaml
tts_backend: local
languages:
  - code: en-US
    voice: slt  # Flite voice
```

**Available engines**:
- **Flite**: Fast, lightweight
- **eSpeak**: Multi-language support
- **Festival**: High-quality synthesis

## Monitoring and Logs

### Log Files

- **Plugin logs**: `/var/log/wazo-ivr/plugin.log`
- **Installation logs**: `/var/log/wazo-ivr-install.log`
- **System logs**: `journalctl -u wazo-ivr-api`

### Monitoring

```bash
# Check service status
systemctl status wazo-ivr-api

# View real-time logs
journalctl -u wazo-ivr-api -f

# Check system status
wazo-ivr status
```

## Troubleshooting

### Common Issues

1. **TTS not working**:
   - Check AWS credentials (if using Polly)
   - Verify local TTS engines are installed
   - Check audio file permissions

2. **Flow not deploying**:
   - Validate flow configuration
   - Check Wazo connectivity
   - Verify queue names exist

3. **Audio quality issues**:
   - Adjust TTS voice settings
   - Check audio file format
   - Verify Asterisk audio configuration

### Debug Mode

Enable debug logging:

```yaml
logging:
  level: "DEBUG"
```

### Validation

Validate flows before deployment:

```bash
wazo-ivr build --flow flow.yml --wazo-host host --token token --no-validate
```

## Development

### Project Structure

```
wazo-ivr-system-plugin/
├── src/wazo_ivr_plugin/     # Main plugin code
│   ├── __init__.py
│   ├── api.py               # CLI and core API
│   ├── flows.py             # Flow management
│   ├── tts.py               # TTS backends
│   ├── dialplan.py          # Asterisk dialplan generation
│   ├── wazo.py              # Wazo API integration
│   └── rest_api.py          # REST API server
├── examples/                # Example flows
├── etc/                     # Configuration templates
├── wazo/                    # Plugin metadata
└── docs/                    # Documentation
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Testing

```bash
# Run unit tests
python -m pytest tests/

# Test CLI commands
wazo-ivr status

# Test REST API
curl http://localhost:5000/api/ivr/status
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
