"""Command registry and handler."""

from typing import Dict
from commands.base_command import Command
from commands.echo import EchoCommand
from commands.play import PlayCommand
from commands.skip import SkipCommand
from commands.pause import PauseCommand
from commands.next import NextCommand
from commands.prev import PrevCommand
from commands.clear import ClearCommand
from commands.queue import QueueCommand
from commands.help import HelpCommand


# Command prefix
PREFIX = "s!"

# Command registry
commands: Dict[str, Command] = {}


def register_commands() -> None:
    """Register all available commands."""
    command_instances = [
        EchoCommand(),
        PlayCommand(),
        SkipCommand(),
        PauseCommand(),
        NextCommand(),
        PrevCommand(),
        ClearCommand(),
        QueueCommand(),
        HelpCommand(),
    ]
    
    for cmd in command_instances:
        commands[cmd.name] = cmd
    
    print(f"Registered {len(commands)} commands: {', '.join(commands.keys())}")


def get_command(name: str) -> Command:
    """
    Get a command by name.
    
    Args:
        name: Name of the command
        
    Returns:
        Command instance or None if not found
    """
    return commands.get(name.lower())
