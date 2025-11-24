"""Pause command - pauses or resumes playback."""

from typing import List
import discord
from commands.base_command import Command
from music_service import music_service


class PauseCommand(Command):
    """Command that pauses or resumes playback."""
    
    def __init__(self):
        super().__init__("pause", "Pauses or resumes the current song")
    
    async def execute(self, message: discord.Message, args: List[str]) -> None:
        """Execute the pause command."""
        if not message.guild:
            await message.reply("This command can only be used in a server!")
            return
        
        queue = music_service.queues.get(message.guild.id)
        
        if not queue:
            await message.reply("❌ No music is currently playing!")
            return
        
        if queue.is_paused:
            success = music_service.resume(message.guild.id)
            if success:
                await message.reply("▶️ Resumed playback!")
            else:
                await message.reply("❌ Failed to resume!")
        else:
            success = music_service.pause(message.guild.id)
            if success:
                await message.reply("⏸️ Paused playback!")
            else:
                await message.reply("❌ Failed to pause!")
