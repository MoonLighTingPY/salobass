"""Queue command - displays the current music queue."""

from typing import List
import discord
from commands.base_command import Command
from music_service import music_service


class QueueCommand(Command):
    """Command that displays the current music queue."""
    
    def __init__(self):
        super().__init__("queue", "Displays the current music queue")
    
    async def execute(self, message: discord.Message, args: List[str]) -> None:
        """Execute the queue command."""
        if not message.guild:
            await message.reply("This command can only be used in a server!")
            return
        
        queue = music_service.get_queue(message.guild.id)
        
        if not queue or len(queue) == 0:
            await message.reply("📜 Queue is empty!")
            return
        
        # Build queue message
        queue_text = "**🎵 Current Queue:**\n\n"
        
        # Show first 10 songs
        for i, song in enumerate(queue[:10], 1):
            status = "🎵 Now Playing" if i == 1 else f"#{i}"
            queue_text += f"{status}: **{song.title}** [{song.duration}]"
            if song.requested_by:
                queue_text += f" - *{song.requested_by}*"
            queue_text += "\n"
        
        if len(queue) > 10:
            queue_text += f"\n*...and {len(queue) - 10} more songs*"
        
        await message.reply(queue_text)
