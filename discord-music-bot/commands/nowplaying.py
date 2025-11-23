"""Now Playing command - displays current song with progress bar."""

from typing import List
import discord
from commands.base_command import Command
from music_service import music_service


class NowPlayingCommand(Command):
    """Command that displays the currently playing song with progress."""
    
    def __init__(self):
        super().__init__("nowplaying", "Displays the currently playing song")
    
    def _create_progress_bar(self, current: int, total: int, length: int = 20) -> str:
        """Create a visual progress bar."""
        if total == 0:
            return "░" * length
        
        filled = int((current / total) * length)
        bar = "█" * filled + "░" * (length - filled)
        return bar
    
    def _format_time(self, seconds: int) -> str:
        """Format seconds to MM:SS."""
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}:{secs:02d}"
    
    async def execute(self, message: discord.Message, args: List[str]) -> None:
        """Execute the nowplaying command."""
        if not message.guild:
            await message.reply("This command can only be used in a server!")
            return
        
        queue = music_service.queues.get(message.guild.id)
        
        if not queue or not queue.current_song:
            await message.reply("❌ No song is currently playing!")
            return
        
        song = queue.current_song
        current_pos = music_service.get_current_position(message.guild.id)
        
        # Create embed
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"**{song.title}**",
            color=discord.Color.blue()
        )
        
        # Add thumbnail if available
        if song.thumbnail:
            embed.set_thumbnail(url=song.thumbnail)
        
        # Add progress bar
        progress_bar = self._create_progress_bar(current_pos, song.duration_seconds)
        time_display = f"{self._format_time(current_pos)} / {song.duration}"
        
        embed.add_field(
            name="Progress",
            value=f"{progress_bar}\n{time_display}",
            inline=False
        )
        
        # Add additional info
        if song.requested_by:
            embed.add_field(name="Requested by", value=song.requested_by, inline=True)
        
        # Add loop status
        loop_mode = queue.loop_mode
        loop_emoji = "🔂" if loop_mode == "song" else "🔁" if loop_mode == "queue" else "➡️"
        loop_text = f"{loop_emoji} {loop_mode.title()}" if loop_mode != "off" else "➡️ Off"
        embed.add_field(name="Loop", value=loop_text, inline=True)
        
        # Add queue info
        queue_length = len(queue.songs) - 1  # Exclude current song
        if queue_length > 0:
            embed.add_field(name="Up Next", value=f"{queue_length} song(s) in queue", inline=True)
        
        # Add status
        status = "⏸️ Paused" if queue.is_paused else "▶️ Playing"
        embed.set_footer(text=status)
        
        await message.reply(embed=embed)