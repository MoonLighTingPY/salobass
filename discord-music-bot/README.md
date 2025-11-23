# Discord Music Bot (Python)

A simple Discord music bot written in Python that can play music from YouTube in voice channels.

## Features

- 🎵 Play music from YouTube (supports URLs and search queries)
- ⏭️ Skip current song
- 📝 Queue management
- 🔊 High-quality audio playback
- 💬 AI-powered chat with conversation history
- 🤖 Powered by Groq AI (llama-3.1-8b-instant)

## Prerequisites

Before running the bot, make sure you have:

- Python 3.8 or higher
- FFmpeg installed on your system
- A Discord Bot Token

### Installing FFmpeg

#### Windows
1. Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract the archive
3. Add the `bin` folder to your system PATH

Or use Chocolatey:
```powershell
choco install ffmpeg
```

#### macOS
```bash
brew install ffmpeg
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install ffmpeg
```

## Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd discord-music-bot
   ```

2. **Create a virtual environment (recommended)**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   - Copy `.env.example` to `.env`
   - Add your Discord bot token to the `.env` file:
   ```
   DISCORD_TOKEN=your_discord_bot_token_here
   GROQ_API_KEY=your_groq_api_key_here
   ```

## Getting API Keys

### Discord Bot Token

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section
4. Click "Add Bot"
5. Under "Token", click "Copy" to copy your bot token
6. Enable these Privileged Gateway Intents:
   - Message Content Intent
   - Server Members Intent (optional)

### Groq API Key (for AI chat feature)

1. Go to [Groq Console](https://console.groq.com/)
2. Sign up or log in
3. Navigate to [API Keys](https://console.groq.com/keys)
4. Click "Create API Key"
5. Copy the API key and add it to your `.env` file

**Note:** The chat feature is optional. If you don't provide a GROQ_API_KEY, the bot will still work but the chat command will be disabled.

## Inviting the Bot to Your Server

1. Go to the "OAuth2" → "URL Generator" section
2. Select these scopes:
   - `bot`
3. Select these bot permissions:
   - Send Messages
   - Connect
   - Speak
   - Use Voice Activity
4. Copy the generated URL and open it in your browser
5. Select your server and authorize the bot

## Running the Bot

```powershell
python bot.py
```

You should see:
```
✅ Bot is online as YourBotName (ID: ...)
Command prefix: s!
```

## Commands

All commands start with the prefix `s!`

| Command | Description | Usage |
|---------|-------------|-------|
| `s!play <query>` | Play a song from YouTube | `s!play never gonna give you up` |
| `s!skip` | Skip the current song | `s!skip` |
| `s!chat <message>` | Chat with the AI assistant | `s!chat Hello!` |
| `s!chat clear` | Clear your conversation history | `s!chat clear` |
| `s!chat help` | Show chat command help | `s!chat help` |
| `s!echo <text>` | Echo back the provided text | `s!echo Hello World` |

### Examples

```
s!play https://www.youtube.com/watch?v=dQw4w9WgXcQ
s!play never gonna give you up
s!skip
s!chat What's the weather like?
s!chat Tell me a joke
s!chat clear
s!echo Hello, Discord!
```

### Chat Feature

The chat command allows you to have conversations with an AI assistant powered by Groq:

- **Conversation Memory**: The AI remembers your last 10 messages
- **Per-User History**: Each user has their own conversation history
- **Fast Responses**: Uses the llama-3.1-8b-instant model for quick replies
- **Clear History**: Use `s!chat clear` to start a fresh conversation

## Project Structure

```
discord-music-bot/
├── bot.py                      # Main bot entry point
├── music_service.py            # Music playback and queue management
├── ai_service.py               # AI service using Groq API
├── chat_logic.py               # Conversation history management
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (create from .env.example)
├── .env.example               # Example environment file
└── commands/
    ├── base_command.py        # Base command interface
    ├── command_handler.py     # Command registry and handler
    ├── chat.py                # Chat command
    ├── echo.py                # Echo command
    ├── play.py                # Play command
    └── skip.py                # Skip command
```

## Dependencies

- **discord.py[voice]** - Discord API wrapper with voice support
- **yt-dlp** - YouTube video downloader and extractor
- **PyNaCl** - Audio encryption for Discord voice
- **python-dotenv** - Environment variable management
- **aiohttp** - Async HTTP client
- **groq** - Groq AI API client for chat functionality

## Troubleshooting

### "FFmpeg not found" error
Make sure FFmpeg is installed and added to your system PATH.

### Bot doesn't respond to commands
- Check that Message Content Intent is enabled in the Discord Developer Portal
- Make sure the bot has permissions to read messages in the channel

### Audio issues
- Ensure the bot has Connect and Speak permissions in voice channels
- Try reconnecting to the voice channel
- Check that FFmpeg is properly installed

### Import errors
Make sure all dependencies are installed:
```powershell
pip install -r requirements.txt
```

## Migrated from Node.js

This bot was originally written in Node.js/TypeScript and has been fully rewritten in Python. The functionality remains the same:

- ✅ Same command prefix (`s!`)
- ✅ Same commands (play, skip, echo)
- ✅ YouTube search and playback
- ✅ Queue management
- ✅ Voice channel integration

### Key Changes

- **Language**: TypeScript → Python
- **Discord Library**: discord.js → discord.py
- **Audio Library**: @discordjs/voice + play-dl → discord.py voice + yt-dlp
- **Package Manager**: npm → pip

## Contributing

Feel free to open issues or submit pull requests!

## License

This project is open source and available under the MIT License.
