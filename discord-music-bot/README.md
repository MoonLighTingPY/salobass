# Discord Music Bot (Python)

A simple Discord music bot written in Python that can play music from YouTube in voice channels.

## Features

- 🎵 Play music from YouTube (supports URLs and search queries)
- ⏭️ Skip current song
- 📝 Queue management
- 🔊 High-quality audio playback
- 💬 Echo command for testing

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
   ```

## Getting a Discord Bot Token

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section
4. Click "Add Bot"
5. Under "Token", click "Copy" to copy your bot token
6. Enable these Privileged Gateway Intents:
   - Message Content Intent
   - Server Members Intent (optional)

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
| `s!echo <text>` | Echo back the provided text | `s!echo Hello World` |

### Examples

```
s!play https://www.youtube.com/watch?v=dQw4w9WgXcQ
s!play never gonna give you up
s!skip
s!echo Hello, Discord!
```

## Project Structure

```
discord-music-bot/
├── bot.py                      # Main bot entry point
├── music_service.py            # Music playback and queue management
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (create from .env.example)
├── .env.example               # Example environment file
└── commands/
    ├── base_command.py        # Base command interface
    ├── command_handler.py     # Command registry and handler
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
