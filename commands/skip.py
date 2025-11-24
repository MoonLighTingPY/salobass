"""Skip command - skips the current song."""

from typing import List
import discord
from commands.base_command import Command
from music_service import music_service


class SkipCommand(Command):
    """Command that skips the current playing song."""
    
    def __init__(self):
        super().__init__("skip", "Skips the current playing song")
    
    async def execute(self, message: discord.Message, args: List[str]) -> None:
        """Execute the skip command."""
        if not message.guild:
            await message.reply("This command can only be used in a server!")
            return
        
        skipped = music_service.skip(message.guild.id)
        
        if skipped:
            await message.reply("⏭️ Skipped current song!")
        else:
            await message.reply("❌ No song is currently playing!")
