"""Loop command - toggles loop mode."""

from typing import List
import discord
from commands.base_command import Command
from music_service import music_service


class LoopCommand(Command):
    """Command that toggles loop mode."""
    
    def __init__(self):
        super().__init__("loop", "Toggles loop mode (off/song/queue)")
    
    async def execute(self, message: discord.Message, args: List[str]) -> None:
        """Execute the loop command."""
        if not message.guild:
            await message.reply("This command can only be used in a server!")
            return
        
        # Check if a specific mode was requested
        if args:
            mode = args[0].lower()
            if mode not in ["off", "song", "queue"]:
                await message.reply("❌ Invalid loop mode! Use: `off`, `song`, or `queue`")
                return
            
            success = music_service.set_loop_mode(message.guild.id, mode)
            if success:
                if mode == "off":
                    await message.reply("➡️ Loop disabled!")
                elif mode == "song":
                    await message.reply("🔂 Now looping current song!")
                else:
                    await message.reply("🔁 Now looping entire queue!")
            else:
                await message.reply("❌ Failed to set loop mode!")
        else:
            # Cycle through modes
            current_mode = music_service.get_loop_mode(message.guild.id)
            
            if current_mode == "off":
                new_mode = "song"
                message_text = "🔂 Now looping current song!"
            elif current_mode == "song":
                new_mode = "queue"
                message_text = "🔁 Now looping entire queue!"
            else:
                new_mode = "off"
                message_text = "➡️ Loop disabled!"
            
            music_service.set_loop_mode(message.guild.id, new_mode)
            await message.reply(message_text)