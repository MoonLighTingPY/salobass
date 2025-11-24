"""Base command interface for Discord bot commands."""

from abc import ABC, abstractmethod
from typing import List
import discord


class Command(ABC):
    """Abstract base class for bot commands."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, message: discord.Message, args: List[str]) -> None:
        """
        Execute the command.
        
        Args:
            message: The Discord message that triggered the command
            args: List of arguments passed to the command
        """
        pass
