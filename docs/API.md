# Wazo IVR System Plugin API Documentation

## Overview

The Wazo IVR System Plugin provides a comprehensive REST API for managing IVR flows, TTS operations, and Wazo integration. The API is built with Flask and follows RESTful principles.

## Base URL

```
http://localhost:5000/api/ivr
```

## Authentication

Currently, the API does not require authentication for local access. For production deployments, consider implementing proper authentication mechanisms.

## Content Types

- **Request**: `application/json`
- **Response**: `application/json`

## Error Handling

All API endpoints return appropriate HTTP status codes and error messages in JSON format:

```json
{
  "error": "Error description"
}
```

## Endpoints

### Flow Management

#### List All Flows

**GET** `/flows`

Returns a list of all IVR flows.

**Response:**
```json
{
  "flows": [
    {
      "id": "sales",
      "tenant": "default",
      "entry_context": "dp-ivr-sales",
      "tts_backend": "polly",
      "languages": [
        {
          "code": "en-US",
          "voice": "Joanna"
        }
      ],
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00",
      "status": "active"
    }
  ],
  "count": 1
}
```

#### Create Flow

**POST** `/flows`

Create a new IVR flow.

**Request Body:**
```json
{
  "id": "support",
  "tenant": "default",
  "entry_context": "dp-ivr-support",
  "tts_backend": "polly",
  "languages": [
    {
      "code": "en-US",
      "voice": "Joanna"
    }
  ],
  "prompts": {
    "welcome": {
      "text": {
        "en-US": "Welcome to support. Press 1 for technical support."
      }
    }
  },
  "menus": {
    "root": {
      "id": "root",
      "prompt": "welcome",
      "timeout_sec": 10,
      "max_retries": 3,
      "options": {
        "1": {
          "action": "queue",
          "queue_ref": "support_q"
        }
      },
      "fallback_action": "voicemail"
    }
  },
  "business_hours": {
    "name": "business-hours",
    "timeframes": {
      "monday": ["09:00-17:00"],
      "tuesday": ["09:00-17:00"],
      "wednesday": ["09:00-17:00"],
      "thursday": ["09:00-17:00"],
      "friday": ["09:00-17:00"]
    },
    "timezone": "America/New_York"
  },
  "voicemail_fallback": "1000",
  "call_recording": {
    "enabled": true,
    "format": "wav"
  }
}
```

**Response:**
```json
{
  "message": "Flow created successfully",
  "flow": {
    "id": "support",
    "tenant": "default",
    "entry_context": "dp-ivr-support",
    "created_at": "2024-01-01T00:00:00"
  }
}
```

#### Get Flow

**GET** `/flows/{flow_id}`

Get a specific IVR flow by ID.

**Response:**
```json
{
  "id": "sales",
  "tenant": "default",
  "entry_context": "dp-ivr-sales",
  "tts_backend": "polly",
  "languages": [
    {
      "code": "en-US",
      "voice": "Joanna"
    }
  ],
  "prompts": {
    "welcome": {
      "text": {
        "en-US": "Welcome to ACME. For Sales press 1, for Support press 2."
      }
    }
  },
  "menus": {
    "root": {
      "id": "root",
      "prompt": "welcome",
      "timeout_sec": 10,
      "max_retries": 3,
      "options": {
        "1": {
          "action": "queue",
          "queue_ref": "sales_q"
        },
        "2": {
          "action": "queue",
          "queue_ref": "support_q"
        }
      },
      "fallback_action": "voicemail"
    }
  },
  "business_hours": {
    "name": "business-hours",
    "timeframes": {
      "monday": ["09:00-17:00"],
      "tuesday": ["09:00-17:00"],
      "wednesday": ["09:00-17:00"],
      "thursday": ["09:00-17:00"],
      "friday": ["09:00-17:00"]
    },
    "timezone": "America/New_York"
  },
  "voicemail_fallback": "1000",
  "call_recording": {
    "enabled": true,
    "format": "wav"
  },
  "max_call_duration": 300,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

#### Update Flow

**PUT** `/flows/{flow_id}`

Update an existing IVR flow.

**Request Body:** Same as create flow

**Response:**
```json
{
  "message": "Flow updated successfully",
  "flow": {
    "id": "sales",
    "updated_at": "2024-01-01T00:00:00"
  }
}
```

#### Delete Flow

**DELETE** `/flows/{flow_id}`

Delete an IVR flow.

**Response:**
```json
{
  "message": "Flow deleted successfully"
}
```

#### Deploy Flow

**POST** `/flows/{flow_id}/deploy`

Deploy an IVR flow to the Wazo system.

**Request Body:**
```json
{
  "wazo_host": "your-wazo-host",
  "token": "your-wazo-token"
}
```

**Response:**
```json
{
  "message": "Flow deployed successfully"
}
```

### TTS Management

#### Get Available Voices

**GET** `/tts/voices`

Get available TTS voices for a specific language.

**Query Parameters:**
- `language` (optional): Language code (default: en-US)

**Response:**
```json
{
  "language": "en-US",
  "voices": [
    "Joanna",
    "Matthew",
    "Kimberly",
    "Amy",
    "Brian",
    "Emma"
  ],
  "all_languages": [
    "en-US",
    "en-GB",
    "es-ES",
    "es-US",
    "fr-FR",
    "de-DE",
    "it-IT",
    "pt-BR",
    "ja-JP",
    "ko-KR",
    "zh-CN",
    "ru-RU"
  ]
}
```

#### Synthesize Speech

**POST** `/tts/synthesize`

Synthesize speech for testing purposes.

**Request Body:**
```json
{
  "text": "Hello, this is a test",
  "voice": "Joanna",
  "language": "en-US",
  "tts_backend": "polly"
}
```

**Response:**
```json
{
  "message": "Speech synthesized successfully",
  "audio_file": "/tmp/wazo-ivr-test/test_abc123.wav",
  "text": "Hello, this is a test",
  "voice": "Joanna",
  "language": "en-US"
}
```

### Wazo Integration

#### Get Wazo Queues

**GET** `/wazo/queues`

Get all queues from Wazo confd.

**Query Parameters:**
- `wazo_host` (required): Wazo server hostname/IP
- `token` (required): Wazo authentication token

**Response:**
```json
{
  "queues": {
    "sales_q": {
      "id": 1,
      "name": "sales_q",
      "context": "ctx-queue",
      "number": "1001",
      "strategy": "leastrecent",
      "timeout": 20,
      "retry": 2,
      "music_on_hold": "default",
      "service_level": 20
    },
    "support_q": {
      "id": 2,
      "name": "support_q",
      "context": "ctx-queue",
      "number": "1002",
      "strategy": "rrmemory",
      "timeout": 20,
      "retry": 2,
      "music_on_hold": "default",
      "service_level": 20
    }
  }
}
```

#### Get Wazo Agents

**GET** `/wazo/agents`

Get all agents from Wazo confd.

**Query Parameters:**
- `wazo_host` (required): Wazo server hostname/IP
- `token` (required): Wazo authentication token

**Response:**
```json
{
  "agents": {
    "1001": {
      "id": 1,
      "number": "1001",
      "firstname": "John",
      "lastname": "Doe",
      "context": "default",
      "language": "en_US",
      "timezone": "UTC",
      "enabled": true
    },
    "1002": {
      "id": 2,
      "number": "1002",
      "firstname": "Jane",
      "lastname": "Smith",
      "context": "default",
      "language": "en_US",
      "timezone": "UTC",
      "enabled": true
    }
  }
}
```

### System Management

#### Get System Status

**GET** `/status`

Get overall system status including TTS backends and Wazo connectivity.

**Response:**
```json
{
  "tts": {
    "polly": {
      "available": true,
      "error": null
    },
    "local": {
      "available": true,
      "engines": ["flite", "espeak"]
    }
  },
  "wazo": {
    "available": false,
    "error": "No credentials provided"
  },
  "flows": {
    "total": 2,
    "active": 1,
    "inactive": 1
  },
  "timestamp": "2024-01-01T00:00:00"
}
```

#### Cleanup System

**POST** `/maintenance/cleanup`

Clean up old cache files and temporary data.

**Request Body:**
```json
{
  "max_age_days": 30
}
```

**Response:**
```json
{
  "message": "Cleanup completed for files older than 30 days"
}
```

## Flow Configuration Schema

### IVRFlow Object

```json
{
  "id": "string (required)",
  "tenant": "string (default: 'default')",
  "entry_context": "string (auto-generated if not provided)",
  "tts_backend": "string (enum: 'polly', 'local')",
  "languages": [
    {
      "code": "string (required)",
      "voice": "string (required)"
    }
  ],
  "prompts": {
    "prompt_id": {
      "text": {
        "language_code": "string"
      }
    }
  },
  "menus": {
    "menu_id": {
      "id": "string (required)",
      "prompt": "string (required)",
      "timeout_sec": "integer (default: 5)",
      "max_retries": "integer (default: 3)",
      "options": {
        "option_key": {
          "action": "string (enum: 'menu', 'queue', 'extension', 'voicemail', 'hangup', 'transfer', 'language')",
          "menu_ref": "string (required if action is 'menu')",
          "queue_ref": "string (required if action is 'queue')",
          "context": "string (required if action is 'extension' or 'voicemail')",
          "extension": "string (required if action is 'extension')",
          "voicemail_box": "string (required if action is 'voicemail')",
          "destination": "string (required if action is 'transfer')",
          "timeout": "integer (optional for 'transfer')",
          "language": "string (required if action is 'language')"
        }
      },
      "fallback_action": "string (enum: 'voicemail', 'queue', 'hangup')",
      "parent_menu": "string (optional)"
    }
  },
  "business_hours": {
    "name": "string (required)",
    "timeframes": {
      "day_of_week": ["time_range"]
    },
    "timezone": "string (default: 'UTC')"
  },
  "voicemail_fallback": "string (optional)",
  "call_recording": {
    "enabled": "boolean (default: false)",
    "format": "string (default: 'wav')"
  },
  "max_call_duration": "integer (default: 300)",
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)"
}
```

### Menu Options

#### Menu Action
```json
{
  "action": "menu",
  "menu_ref": "target_menu_id"
}
```

#### Queue Action
```json
{
  "action": "queue",
  "queue_ref": "queue_name"
}
```

#### Extension Action
```json
{
  "action": "extension",
  "context": "context_name",
  "extension": "extension_number"
}
```

#### Voicemail Action
```json
{
  "action": "voicemail",
  "voicemail_box": "box_number",
  "context": "context_name"
}
```

#### Hangup Action
```json
{
  "action": "hangup",
  "prompt": "prompt_id"
}
```

#### Transfer Action
```json
{
  "action": "transfer",
  "destination": "destination_number",
  "timeout": 30
}
```

#### Language Action
```json
{
  "action": "language",
  "language": "language_code",
  "prompt": "prompt_id"
}
```

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input data |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error - Server error |

## Rate Limiting

Currently, no rate limiting is implemented. For production deployments, consider implementing rate limiting to prevent abuse.

## Examples

### Complete Flow Example

```bash
# Create a complete IVR flow
curl -X POST http://localhost:5000/api/ivr/flows \
  -H "Content-Type: application/json" \
  -d '{
    "id": "customer-service",
    "tenant": "default",
    "tts_backend": "polly",
    "languages": [
      {"code": "en-US", "voice": "Joanna"},
      {"code": "es-US", "voice": "Lupe"}
    ],
    "prompts": {
      "welcome": {
        "text": {
          "en-US": "Welcome to customer service. Press 1 for sales, 2 for support, 3 for billing.",
          "es-US": "Bienvenido al servicio al cliente. Presione 1 para ventas, 2 para soporte, 3 para facturación."
        }
      }
    },
    "menus": {
      "root": {
        "id": "root",
        "prompt": "welcome",
        "timeout_sec": 10,
        "max_retries": 3,
        "options": {
          "1": {"action": "queue", "queue_ref": "sales_q"},
          "2": {"action": "queue", "queue_ref": "support_q"},
          "3": {"action": "queue", "queue_ref": "billing_q"}
        },
        "fallback_action": "voicemail"
      }
    },
    "business_hours": {
      "name": "business-hours",
      "timeframes": {
        "monday": ["09:00-17:00"],
        "tuesday": ["09:00-17:00"],
        "wednesday": ["09:00-17:00"],
        "thursday": ["09:00-17:00"],
        "friday": ["09:00-17:00"]
      },
      "timezone": "America/New_York"
    },
    "voicemail_fallback": "1000",
    "call_recording": {
      "enabled": true,
      "format": "wav"
    }
  }'
```

### Deploy Flow Example

```bash
# Deploy the flow to Wazo
curl -X POST http://localhost:5000/api/ivr/flows/customer-service/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "wazo_host": "192.168.1.100",
    "token": "your-wazo-token"
  }'
```

### Test TTS Example

```bash
# Test TTS synthesis
curl -X POST http://localhost:5000/api/ivr/tts/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test of the TTS system.",
    "voice": "Joanna",
    "language": "en-US",
    "tts_backend": "polly"
  }'
```
