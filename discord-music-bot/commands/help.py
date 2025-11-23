"""Help command - displays all available commands."""

from typing import List
import discord
from commands.base_command import Command


class HelpCommand(Command):
    """Command that displays all available bot commands."""
    
    def __init__(self):
        super().__init__("help", "Displays all available commands")
    
    async def execute(self, message: discord.Message, args: List[str]) -> None:
        """Execute the help command."""
        from commands.command_handler import commands, PREFIX
        
        help_text = "**🎵 Discord Music Bot - Available Commands:**\n\n"
        
        # Organize commands by category
        music_commands = []
        other_commands = []
        
        for cmd in commands.values():
            cmd_line = f"`{PREFIX}{cmd.name}` - {cmd.description}"
            
            # Categorize commands
            if cmd.name in ["play", "pause", "skip", "next", "prev", "queue", "clear"]:
                music_commands.append(cmd_line)
            else:
                other_commands.append(cmd_line)
        
        # Add music commands
        if music_commands:
            help_text += "**Music Controls:**\n"
            for cmd_line in sorted(music_commands):
                help_text += f"{cmd_line}\n"
            help_text += "\n"
        
        # Add other commands
        if other_commands:
            help_text += "**Other Commands:**\n"
            for cmd_line in sorted(other_commands):
                help_text += f"{cmd_line}\n"
        
        # Add additional info
        help_text += f"\n**Command Prefix:** `{PREFIX}`\n"
        help_text += "\n**Music Controls:**\n"
        help_text += "⏮️ Previous | ⏯️ Pause/Resume | ⏭️ Skip | 🗑️ Clear | 📜 Queue\n"
        help_text += "\nYou can use either commands or the interactive buttons!"
        
        await message.reply(help_text)
