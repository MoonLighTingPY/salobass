"""Previous command - goes back to the previous song."""

from typing import List
import discord
from commands.base_command import Command
from music_service import music_service


class PrevCommand(Command):
    """Command that goes back to the previous song."""
    
    def __init__(self):
        super().__init__("prev", "Goes back to the previous song")
    
    async def execute(self, message: discord.Message, args: List[str]) -> None:
        """Execute the previous command."""
        if not message.guild:
            await message.reply("This command can only be used in a server!")
            return
        
        success = await music_service.previous(message.guild.id)
        
        if success:
            await message.reply("⏮️ Playing previous song!")
        else:
            await message.reply("❌ No previous song in history!")
