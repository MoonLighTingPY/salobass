"""Music control buttons for Discord bot."""

import discord
from music_service import music_service


class MusicControlView(discord.ui.View):
    """View with buttons for controlling music playback."""
    
    def __init__(self):
        super().__init__(timeout=None)  # Buttons never timeout
    
    @discord.ui.button(emoji="⏮️", style=discord.ButtonStyle.secondary, custom_id="music:previous")
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button to go to previous song."""
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server!", ephemeral=True)
            return
        
        success = await music_service.previous(interaction.guild.id)
        
        if success:
            await interaction.response.send_message("⏮️ Playing previous song!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ No previous song in history!", ephemeral=True)
    
    @discord.ui.button(emoji="⏯️", style=discord.ButtonStyle.primary, custom_id="music:pause_resume")
    async def pause_resume_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button to pause/resume playback."""
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server!", ephemeral=True)
            return
        
        queue = music_service.queues.get(interaction.guild.id)
        
        if not queue:
            await interaction.response.send_message("❌ No music is currently playing!", ephemeral=True)
            return
        
        if queue.is_paused:
            success = music_service.resume(interaction.guild.id)
            if success:
                await interaction.response.send_message("▶️ Resumed playback!", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Failed to resume!", ephemeral=True)
        else:
            success = music_service.pause(interaction.guild.id)
            if success:
                await interaction.response.send_message("⏸️ Paused playback!", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Failed to pause!", ephemeral=True)
    
    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary, custom_id="music:skip")
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button to skip current song."""
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server!", ephemeral=True)
            return
        
        skipped = music_service.skip(interaction.guild.id)
        
        if skipped:
            await interaction.response.send_message("⏭️ Skipped current song!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ No song is currently playing!", ephemeral=True)
    
    @discord.ui.button(emoji="🗑️", style=discord.ButtonStyle.danger, custom_id="music:clear")
    async def clear_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button to clear the queue and stop playback."""
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server!", ephemeral=True)
            return
        
        cleared = music_service.clear_and_stop(interaction.guild.id)
        
        if cleared > 0:
            await interaction.response.send_message(f"🗑️ Cleared {cleared} song(s) from the queue and stopped playback!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Queue is already empty!", ephemeral=True)
    
    @discord.ui.button(emoji="📜", style=discord.ButtonStyle.secondary, custom_id="music:queue")
    async def queue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button to display the current queue."""
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server!", ephemeral=True)
            return
        
        queue = music_service.get_queue(interaction.guild.id)
        
        if not queue or len(queue) == 0:
            await interaction.response.send_message("📜 Queue is empty!", ephemeral=True)
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
        
        await interaction.response.send_message(queue_text, ephemeral=True)

