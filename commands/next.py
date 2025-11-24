"""Next command - skips to the next song."""

from typing import List
import discord
from commands.base_command import Command
from music_service import music_service


class NextCommand(Command):
    """Command that skips to the next song (same as skip button)."""
    
    def __init__(self):
        super().__init__("next", "Skips to the next song")
    
    async def execute(self, message: discord.Message, args: List[str]) -> None:
        """Execute the next command."""
        if not message.guild:
            await message.reply("This command can only be used in a server!")
            return
        
        skipped = music_service.skip(message.guild.id)
        
        if skipped:
            await message.reply("⏭️ Skipped to next song!")
        else:
            await message.reply("❌ No song is currently playing!")
