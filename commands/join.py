"""Join command - joins the voice channel."""

from typing import List
import discord
from commands.base_command import Command


class JoinCommand(Command):
    """Command that joins the user's voice channel."""
    
    def __init__(self):
        super().__init__("join", "Joins your voice channel")
    
    async def execute(self, message: discord.Message, args: List[str]) -> None:
        """Execute the join command."""
        if not message.guild:
            await message.reply("This command can only be used in a server!")
            return
        
        # Check if user is in a voice channel
        if not message.author.voice or not message.author.voice.channel:
            await message.reply("❌ You need to be in a voice channel!")
            return
        
        voice_channel = message.author.voice.channel
        
        # Check bot permissions
        permissions = voice_channel.permissions_for(message.guild.me)
        if not permissions.connect or not permissions.speak:
            await message.reply("I need permissions to join and speak in your voice channel!")
            return
        
        try:
            # Check if bot is already in a voice channel
            voice_client = message.guild.voice_client
            
            if voice_client:
                if voice_client.channel == voice_channel:
                    await message.reply(f"✅ Already in {voice_channel.mention}!")
                    return
                else:
                    # Move to the new voice channel
                    await voice_client.move_to(voice_channel)
                    await message.reply(f"✅ Moved to {voice_channel.mention}!")
            else:
                # Connect to the voice channel
                await voice_channel.connect()
                await message.reply(f"✅ Joined {voice_channel.mention}!")
                
        except Exception as e:
            print(f"Error joining voice channel: {e}")
            await message.reply("❌ Failed to join voice channel!")