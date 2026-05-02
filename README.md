# DeepSeek Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Official DeepSeek AI integration for Home Assistant. Bring the power of DeepSeek's advanced language models to your smart home.

## Features

- **🤖 Conversation Agent**: Use DeepSeek as your Home Assistant voice/chat assistant
- **🔧 Config Flow**: Easy UI-based setup - no YAML required
- **🎯 Multiple Models**: Support for `deepseek-chat`, `deepseek-reasoner`, `deepseek-coder`
- **💭 Reasoning Support**: Optional reasoning display with `deepseek-reasoner` model
- **🌐 Multi-language**: Support for all languages DeepSeek understands
- **⚡ Fast & Efficient**: Async implementation with proper error handling
- **🔌 OpenAI-Compatible**: Uses DeepSeek's OpenAI-compatible API

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click "Integrations"
3. Click the "+" button (Explore & Add Repositories)
4. Search for "DeepSeek"
5. Click "Install"
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/deepseek` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to Settings → Devices & Services → Add Integration
4. Search for "DeepSeek"

## Configuration

### Getting an API Key

1. Visit [DeepSeek Platform](https://platform.deepseek.com)
2. Sign up or log in
3. Go to API Keys section
4. Create a new API key
5. Copy the key (you'll only see it once!)

### Setup Steps

1. **Add Integration**: Go to Settings → Devices & Services → Add Integration → Search "DeepSeek"
2. **Enter API Key**: Paste your DeepSeek API key
3. **Configure Options** (optional):
   - **Model**: Choose between `deepseek-chat`, `deepseek-reasoner`, or `deepseek-coder`
   - **Max Tokens**: Response length limit (default: 2048)
   - **Temperature**: Creativity level (0.0-2.0, default: 0.7)
   - **Show Reasoning**: Display reasoning steps (only for `deepseek-reasoner`)
4. **Complete**: The integration is now ready!

## Usage

### As a Conversation Agent

Once installed, DeepSeek becomes available as a conversation agent:

- **Voice Commands**: "Hey Assistant, ask DeepSeek what's the weather forecast"
- **Chat Interface**: Use the chat feature in Home Assistant
- **Automations**: Trigger DeepSeek responses in automations

### Service: `deepseek.generate`

Use DeepSeek as a building block in automations, scripts, and other integrations. The service takes a prompt and returns the model's reply, which you can capture into a variable with `response_variable` and use in subsequent steps.

#### Fields

| Field           | Type   | Required | Description                                                                 |
| --------------- | ------ | -------- | --------------------------------------------------------------------------- |
| `prompt`        | string | yes      | The user message sent to the model.                                         |
| `system_prompt` | string | no       | Optional system instructions placed before the prompt.                      |
| `model`         | string | no       | Override the model configured for this entry (`deepseek-v4-flash`, etc.).   |
| `max_tokens`    | int    | no       | Maximum tokens to generate (1–8192).                                        |
| `temperature`   | float  | no       | Sampling temperature (0–2).                                                 |
| `top_p`         | float  | no       | Nucleus sampling threshold (0–1).                                           |
| `config_entry`  | string | no       | Specific DeepSeek entry to use, when more than one is configured.           |

#### Response

```yaml
text: "The model's reply..."
model: "deepseek-v4-flash"
finish_reason: "stop"
usage:
  prompt_tokens: 24
  completion_tokens: 86
  total_tokens: 110
```

#### Example: morning weather summary

```yaml
automation:
  - alias: Morning weather summary
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: deepseek.generate
        data:
          system_prompt: >-
            You are a concise weather presenter. Reply in one short sentence.
          prompt: >-
            Today's forecast: {{ states('weather.home') }},
            high {{ state_attr('weather.home', 'temperature') }}°C,
            wind {{ state_attr('weather.home', 'wind_speed') }} km/h.
        response_variable: weather_reply
      - service: notify.mobile_app
        data:
          message: "{{ weather_reply.text }}"
```

#### Example: smart device-status update

```yaml
script:
  living_room_status:
    sequence:
      - service: deepseek.generate
        data:
          model: deepseek-v4-pro
          temperature: 0.3
          prompt: >-
            Lights: {{ states('light.living_room') }}.
            Temperature: {{ states('sensor.living_room_temperature') }}°C.
            Write a friendly one-line status update for the living room.
        response_variable: status
      - service: tts.cloud_say
        data:
          entity_id: media_player.living_room
          message: "{{ status.text }}"
```

You can also call the service directly from **Developer Tools → Actions** to test prompts and see the full response object.

## Models

### Available Models

1. **`deepseek-v4-flash`** (Default)
   - Current generation, fast and inexpensive
   - 1M token context window
   - Supports tool calling — best for everyday conversations and Assist
2. **`deepseek-v4-pro`**
   - Higher capability, larger model
   - 1M token context window, also supports tool calling
   - Best for complex reasoning and longer prompts
3. **`deepseek-chat`** *(deprecated — kept for existing entries)*
4. **`deepseek-reasoner`** *(deprecated — kept for existing entries)*

DeepSeek announced the deprecation of `deepseek-chat` and `deepseek-reasoner` for **2026-07-24**. The integration keeps them in the dropdown so existing config entries don't break, but new installs default to `deepseek-v4-flash`.

### Model selection tips

- **General use / Assist**: `deepseek-v4-flash`
- **Complex reasoning, larger prompts**: `deepseek-v4-pro`
- **Creative tasks**: higher temperature (0.8–1.2)
- **Precise / factual tasks**: lower temperature (0.2–0.5)

## Troubleshooting

### Common Issues

#### "Invalid API key"
- Ensure you copied the key correctly
- Check if the key has expired
- Verify you have API access on DeepSeek Platform

#### "Cannot connect"
- Check your internet connection
- Verify DeepSeek API status at [status.deepseek.com](https://status.deepseek.com)
- Ensure your firewall allows connections to `api.deepseek.com`

#### "No response"
- Check the logs for detailed errors
- Verify the model is available in your region
- Ensure you have sufficient API credits

### Logs

Enable debug logging for detailed information:

```yaml
logger:
  default: info
  logs:
    custom_components.deepseek: debug
```

## Development

### Project Structure

```
custom_components/deepseek/
├── __init__.py              # Main integration setup
├── manifest.json           # Integration metadata
├── config_flow.py          # UI configuration
├── const.py               # Constants
├── conversation.py        # Conversation agent
├── strings.json           # UI strings
├── translations/          # Translations
│   └── en.json
├── services.yaml          # Service definitions
└── README.md             # This file
```

### Testing

```bash
# Run validation
hassfest validate

# Test with Home Assistant dev container
hass --script ensure_config
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run validation tests
5. Submit a pull request

## Privacy & Security

- **API Keys**: Stored securely in Home Assistant's config
- **Data**: Conversations are sent to DeepSeek's API
- **No Local Storage**: No conversation data is stored locally
- **Rate Limiting**: Built-in rate limit handling

Refer to [DeepSeek's Privacy Policy](https://www.deepseek.com/privacy) for more information.

## Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/deepseek-ai/deepseek-ha-integration/issues)
- **Documentation**: [DeepSeek API Docs](https://platform.deepseek.com/api-docs)
- **Community**: [Home Assistant Community](https://community.home-assistant.io)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built by DeepSeek for the Home Assistant community
- Uses the official OpenAI Python client
- Thanks to all contributors and testers

---

**DeepSeek: Making AI accessible for everyone's smart home.** 🏠✨