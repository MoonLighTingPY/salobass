"""Main Discord bot entry point."""

import os
import discord
from discord.ext import commands as discord_commands
from dotenv import load_dotenv
from commands.command_handler import register_commands, get_command, PREFIX
from music_controls import MusicControlView  # Import the class, not the instance
from commands.play import PlayCommand

# Load environment variables
load_dotenv()

# Bot setup with required intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

# Create bot instance
bot = discord_commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

music_control_view = None  # Declare the view globally but don't instantiate it yet

@bot.event
async def on_ready():
    """Event handler for when the bot is ready."""
    global music_control_view
    music_control_view = MusicControlView()  # Instantiate the view here
    bot.add_view(music_control_view)  # Register the persistent view

    # Pass the music_control_view instance to the PlayCommand
    play_command = get_command("play")
    if isinstance(play_command, PlayCommand):
        play_command.set_music_control_view(music_control_view)

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
        await message.reply(f"Unknown command: {command_name}")
        return
    
    try:
        await command.execute(message, args)
    except Exception as e:
        print(f"Error executing command {command_name}: {e}")
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
