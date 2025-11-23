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
from commands.nowplaying import NowPlayingCommand
from commands.loop import LoopCommand
from commands.shuffle import ShuffleCommand
from commands.chat import ChatCommand


# Command prefix
PREFIX = "s!"

# Command registry
commands: Dict[str, Command] = {}

# Command aliases
aliases: Dict[str, str] = {
    "p": "play",
    "s": "skip",
    "n": "next",
    "np": "nowplaying",
    "q": "queue",
}


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
        NowPlayingCommand(),
        LoopCommand(),
        ShuffleCommand(),
        ChatCommand(),
    ]
    
    for cmd in command_instances:
        commands[cmd.name] = cmd
    
    print(f"Registered {len(commands)} commands: {', '.join(commands.keys())}")
    print(f"Registered {len(aliases)} aliases: {', '.join(f'{k}->{v}' for k, v in aliases.items())}")


def get_command(name: str) -> Command:
    """
    Get a command by name or alias.
    
    Args:
        name: Name or alias of the command
        
    Returns:
        Command instance or None if not found
    """
    name = name.lower()
    
    # Check if it's an alias
    if name in aliases:
        name = aliases[name]
    
    return commands.get(name)
