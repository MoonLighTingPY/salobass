"""Main Discord bot entry point."""

import os
import discord
from discord.ext import commands as discord_commands
from discord.ext import voice_recv
from dotenv import load_dotenv
from commands.command_handler import register_commands, get_command, PREFIX
import logging

# Load environment variables
load_dotenv()

# Suppress RTCP packet warnings
logging.getLogger('discord.ext.voice_recv.reader').setLevel(logging.WARNING)

# Bot setup with required intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True
intents.members = True  # Required for voice receive

# Create bot instance with voice receive support
bot = discord_commands.Bot(
    command_prefix=PREFIX, 
    intents=intents, 
    help_command=None
)

# Override the default voice client class to support receiving
class VoiceRecvClient(voice_recv.VoiceRecvClient):
    """Custom voice client with receive support."""
    pass

# Register the custom voice client
discord.VoiceClient.warn_nacl = False


@bot.event
async def on_ready():
    """Event handler for when the bot is ready."""
    print(f"✅ Bot is online as {bot.user.name} (ID: {bot.user.id})")
    print(f"Command prefix: {PREFIX}")
    print("------")


@bot.event
async def on_message(message: discord.Message):
    """Event handler for incoming messages."""
    # Ignore messages from bots
    if message.author.bot:
        return
    
    # Check if message starts with prefix
    if not message.content.startswith(PREFIX):
        return
    
    # Parse command and arguments
    content = message.content[len(PREFIX):].strip()
    if not content:
        return
    
    parts = content.split()
    command_name = parts[0].lower()
    args = parts[1:]
    
    # Get and execute command
    command = get_command(command_name)
    if not command:
        await message.reply(f"Unknown command: {command_name}\nUse `{PREFIX}help` to see available commands!")
        return
    
    try:
        await command.execute(message, args)
    except Exception as e:
        print(f"Error executing command {command_name}: {e}")
        import traceback
        traceback.print_exc()
        await message.reply("There was an error executing that command!")


def main():
    """Main entry point for the bot."""
    # Register all commands
    register_commands()
    
    # Get bot token
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ Error: DISCORD_TOKEN not found in environment variables!")
        print("Please create a .env file with your bot token.")
        return
    
    # Start the bot
    print("Starting bot...")
    try:
        bot.run(token)
    except discord.LoginFailure:
        print("❌ Error: Invalid bot token!")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")


if __name__ == "__main__":
    main()
