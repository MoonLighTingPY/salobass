"""Queue command - displays the current music queue with pagination."""

from typing import List
import discord
from commands.base_command import Command
from music_service import music_service
from music_controls import QueuePaginationView


class QueueCommand(Command):
    """Command that displays the current music queue with pagination."""
    
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
        
        # Create pagination view
        view = QueuePaginationView(message.guild.id, page=0)
        content = view.get_page_content()
        
        await message.reply(content, view=view)
