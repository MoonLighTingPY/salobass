"""Echo command - echoes back the provided text."""

from typing import List
import discord
from commands.base_command import Command


class EchoCommand(Command):
    """Command that echoes back user input."""
    
    def __init__(self):
        super().__init__("echo", "Echoes back the provided text")
    
    async def execute(self, message: discord.Message, args: List[str]) -> None:
        """Execute the echo command."""
        if not args:
            await message.reply("Please provide text to echo!")
            return
        
        text = " ".join(args)
        await message.channel.send(text)
