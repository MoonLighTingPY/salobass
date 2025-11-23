# Chat Feature Setup Guide

## Overview

The Discord Music Bot now includes an AI-powered chat feature using Groq's fast LLM API. Users can have natural conversations with the bot using the `s!chat` command.

## Features

- 💬 Natural language conversations
- 🧠 Conversation memory (last 10 messages per user)
- 👤 Per-user conversation history
- ⚡ Fast responses using `llama-3.1-8b-instant` model
- 🔄 Clear conversation history with `s!chat clear`

## Files Created

### 1. `ai_service.py`
- Handles communication with Groq API
- Manages AI model configuration
- Provides async response generation
- Error handling for API issues

### 2. `chat_logic.py`
- Manages conversation history per user
- Maintains context for each conversation
- Provides conversation management utilities
- Configurable system prompts

### 3. `commands/chat.py`
- Implements the chat command
- Handles user input and AI responses
- Splits long responses for Discord's character limit
- Provides help and usage information

## Setup Instructions

### 1. Get a Groq API Key

1. Visit [Groq Console](https://console.groq.com/)
2. Sign up or log in
3. Go to [API Keys](https://console.groq.com/keys)
4. Create a new API key
5. Copy the key

### 2. Configure Environment Variables

Add your Groq API key to `.env`:

```env
DISCORD_TOKEN=your_discord_bot_token_here
GROQ_API_KEY=your_groq_api_key_here
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

This will install the `groq` package along with other dependencies.

### 4. Run the Bot

```powershell
python bot.py
```

## Usage

### Basic Chat

```
s!chat Hello, how are you?
s!chat What can you help me with?
s!chat Tell me a joke
```

### Clear History

```
s!chat clear
```

This clears your conversation history with the bot.

### Get Help

```
s!chat help
```

Shows detailed help about the chat command.

## Configuration

### Change AI Model

In `ai_service.py`, you can modify the model:

```python
self.model = "llama-3.1-8b-instant"  # Default fast model
# Or use other models:
# self.model = "llama-3.1-70b-versatile"  # More capable, slower
# self.model = "mixtral-8x7b-32768"  # Good balance
```

### Adjust Conversation History

In `chat_logic.py`, modify the `ConversationHistory` class:

```python
def __init__(self, max_messages: int = 10):  # Change this number
```

### Customize System Prompt

In `chat_logic.py`, modify the `ChatManager` initialization:

```python
self.system_prompt = "Your custom system prompt here"
```

## Available Groq Models

- `llama-3.1-8b-instant` - Fast, good for quick responses (default)
- `llama-3.1-70b-versatile` - More capable, slower
- `mixtral-8x7b-32768` - Good balance of speed and capability
- `gemma2-9b-it` - Google's efficient model

## Error Handling

The chat command handles various errors:

- **Missing API Key**: Prompts user to add GROQ_API_KEY
- **Authentication Errors**: Indicates invalid API key
- **Rate Limiting**: Notifies user to wait before retrying
- **Long Responses**: Automatically splits messages over 1900 characters

## Troubleshooting

### "AI service is not configured"

Make sure you have:
1. Added `GROQ_API_KEY` to your `.env` file
2. Restarted the bot after adding the key

### "Authentication error"

- Check that your API key is correct
- Verify the key is valid at [Groq Console](https://console.groq.com/keys)

### "Rate limit exceeded"

- Wait a moment before sending another message
- Groq free tier has rate limits

### Bot not responding to chat commands

- Check that the bot is online
- Verify the command handler registered the chat command
- Look for error messages in the console

## Architecture

```
User Message
    ↓
commands/chat.py (ChatCommand)
    ↓
chat_logic.py (ChatManager)
    ├── Stores message in history
    └── Retrieves conversation context
        ↓
ai_service.py (AIService)
    ├── Formats messages for API
    ├── Calls Groq API
    └── Returns AI response
        ↓
commands/chat.py
    ├── Stores AI response in history
    └── Sends reply to Discord
```

## Future Enhancements

Potential improvements:

- [ ] Add conversation branching
- [ ] Implement multiple AI personas
- [ ] Add image generation capabilities
- [ ] Support for voice chat integration
- [ ] Admin commands to manage system prompts
- [ ] Per-server conversation settings
- [ ] Export conversation history

## Cost Considerations

Groq offers a generous free tier:
- Free API access with rate limits
- Fast inference speeds
- No credit card required for basic usage

For production use, check [Groq Pricing](https://console.groq.com/pricing) for latest information.

## Security Notes

- Never commit your `.env` file to version control
- Keep your API keys secure
- Use environment variables for sensitive data
- Monitor API usage in Groq console

## Support

If you encounter issues:
1. Check the console for error messages
2. Verify all environment variables are set
3. Ensure dependencies are installed
4. Check Groq API status
5. Review the troubleshooting section

## License

This feature follows the same license as the main project.
