"""Shuffle command - shuffles the queue."""

from typing import List
import discord
from commands.base_command import Command
from music_service import music_service


class ShuffleCommand(Command):
    """Command that shuffles the queue."""
    
    def __init__(self):
        super().__init__("shuffle", "Shuffles the queue")
    
    async def execute(self, message: discord.Message, args: List[str]) -> None:
        """Execute the shuffle command."""
        if not message.guild:
            await message.reply("This command can only be used in a server!")
            return
        
        shuffled = music_service.shuffle_queue(message.guild.id)
        
        if shuffled:
            await message.reply("🔀 Shuffled the queue!")
        else:
            await message.reply("❌ Queue is too small to shuffle (need at least 2 songs)!")