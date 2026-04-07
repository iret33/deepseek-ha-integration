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

### Services

The integration provides these services:

#### `deepseek.chat`
Send a message to DeepSeek and get a response.

```yaml
service: deepseek.chat
data:
  message: "What's the weather like today?"
  conversation_id: "optional_conversation_id"
```

Response data includes:
- `response`: The AI's response
- `conversation_id`: Conversation ID for context
- `tokens_used`: Number of tokens used
- `reasoning`: Reasoning steps (if enabled)

#### `deepseek.summarize`
Summarize text using DeepSeek.

```yaml
service: deepseek.summarize
data:
  text: "Long article text here..."
  max_length: 100
```

#### `deepseek.translate`
Translate text using DeepSeek.

```yaml
service: deepseek.translate
data:
  text: "Hello, how are you?"
  target_language: "Spanish"
  source_language: "auto"
```

### Example Automations

#### Weather Summary
```yaml
automation:
  - alias: "Morning weather summary"
    trigger:
      platform: time
      at: "07:00:00"
    action:
      - service: weather.get_forecast
        target:
          entity_id: weather.home
        data:
          type: daily
      - service: deepseek.chat
        data:
          message: >
            Summarize today's weather forecast: {{ states.weather.home.attributes.forecast[0] }}
```

#### Smart Home Control via Chat
```yaml
automation:
  - alias: "Process DeepSeek home control requests"
    trigger:
      platform: event
      event_type: conversation_result
      event_data:
        agent_id: deepseek
    action:
      - choose:
          - conditions:
              - "{{ 'turn on' in trigger.event.data.response|lower }}"
            sequence:
              - service: light.turn_on
                target:
                  entity_id: light.living_room
```

## Models

### Available Models

1. **`deepseek-chat`** (Default)
   - General purpose chat model
   - 128K context window
   - Best for everyday conversations

2. **`deepseek-reasoner`**
   - Chain-of-thought reasoning
   - Shows reasoning steps (optional)
   - Best for complex problem solving

3. **`deepseek-coder`**
   - Specialized for code generation
   - Best for programming tasks

### Model Selection Tips

- **General Use**: `deepseek-chat`
- **Complex Questions**: `deepseek-reasoner` with reasoning enabled
- **Programming Help**: `deepseek-coder`
- **Creative Tasks**: Higher temperature (0.8-1.2)
- **Precise Tasks**: Lower temperature (0.2-0.5)

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