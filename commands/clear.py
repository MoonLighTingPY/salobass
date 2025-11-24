"""Clear command - clears the queue and stops playback."""

from typing import List
import discord
from commands.base_command import Command
from music_service import music_service


class ClearCommand(Command):
    """Command that clears the entire queue and stops playback."""
    
    def __init__(self):
        super().__init__("clear", "Clears the queue and stops playback")
    
    async def execute(self, message: discord.Message, args: List[str]) -> None:
        """Execute the clear command."""
        if not message.guild:
            await message.reply("This command can only be used in a server!")
            return
        
        cleared = music_service.clear_and_stop(message.guild.id)
        
        if cleared > 0:
            await message.reply(f"🗑️ Cleared {cleared} song(s) from the queue and stopped playback!")
        else:
            await message.reply("❌ Queue is already empty!")
