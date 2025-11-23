"""Music control buttons for Discord bot."""

import discord
from music_service import music_service


class MusicControlView(discord.ui.View):
    """View with buttons for controlling music playback."""
    
    def __init__(self, guild_id: int = None):
        super().__init__(timeout=None)  # Buttons never timeout
        self.guild_id = guild_id
        if guild_id:
            self._update_button_states()
    
    def _update_button_states(self):
        """Update button states based on queue state."""
        if not self.guild_id:
            return
        
        queue = music_service.queues.get(self.guild_id)
        
        # Disable previous button if no history
        if not queue or not queue.history:
            self.previous_button.disabled = True
        else:
            self.previous_button.disabled = False
        
        # Disable skip button if only 1 or 0 songs in queue
        if not queue or len(queue.songs) <= 1:
            self.skip_button.disabled = True
        else:
            self.skip_button.disabled = False
        
        # Disable shuffle if less than 2 songs
        if not queue or len(queue.songs) <= 1:
            self.shuffle_button.disabled = True
        else:
            self.shuffle_button.disabled = False
        
        # Update loop button style based on mode
        if queue:
            if queue.loop_mode == "song":
                self.loop_button.style = discord.ButtonStyle.success
                self.loop_button.emoji = "🔂"
            elif queue.loop_mode == "queue":
                self.loop_button.style = discord.ButtonStyle.success
                self.loop_button.emoji = "🔁"
            else:
                self.loop_button.style = discord.ButtonStyle.secondary
                self.loop_button.emoji = "🔁"
    
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
    
    @discord.ui.button(emoji="🔁", style=discord.ButtonStyle.secondary, custom_id="music:loop")
    async def loop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button to toggle loop mode."""
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server!", ephemeral=True)
            return
        
        current_mode = music_service.get_loop_mode(interaction.guild.id)
        
        # Cycle through modes: off -> song -> queue -> off
        if current_mode == "off":
            new_mode = "song"
            message = "🔂 Now looping current song!"
        elif current_mode == "song":
            new_mode = "queue"
            message = "🔁 Now looping entire queue!"
        else:
            new_mode = "off"
            message = "➡️ Loop disabled!"
        
        music_service.set_loop_mode(interaction.guild.id, new_mode)
        await interaction.response.send_message(message, ephemeral=True)
    
    @discord.ui.button(emoji="🔀", style=discord.ButtonStyle.secondary, custom_id="music:shuffle")
    async def shuffle_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button to shuffle the queue."""
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server!", ephemeral=True)
            return
        
        shuffled = music_service.shuffle_queue(interaction.guild.id)
        
        if shuffled:
            await interaction.response.send_message("🔀 Shuffled the queue!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Queue is too small to shuffle!", ephemeral=True)
    
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
        
        # Create pagination view and send it
        view = QueuePaginationView(interaction.guild.id, page=0)
        content = view.get_page_content()
        
        await interaction.response.send_message(content, view=view, ephemeral=True)


class QueuePaginationView(discord.ui.View):
    """View for paginated queue display."""
    
    def __init__(self, guild_id: int, page: int = 0):
        super().__init__(timeout=60)  # 60 second timeout
        self.guild_id = guild_id
        self.page = page
        self.songs_per_page = 10
        self._update_button_states()
    
    def _update_button_states(self):
        """Update button states based on current page."""
        queue = music_service.get_queue(self.guild_id)
        total_pages = (len(queue) - 1) // self.songs_per_page + 1 if queue else 1
        
        self.prev_page_button.disabled = self.page == 0
        self.next_page_button.disabled = self.page >= total_pages - 1
    
    def get_page_content(self) -> str:
        """Get the content for the current page."""
        queue = music_service.get_queue(self.guild_id)
        
        if not queue:
            return "📜 Queue is empty!"
        
        start_idx = self.page * self.songs_per_page
        end_idx = start_idx + self.songs_per_page
        page_songs = queue[start_idx:end_idx]
        
        total_pages = (len(queue) - 1) // self.songs_per_page + 1
        
        queue_text = f"**🎵 Current Queue (Page {self.page + 1}/{total_pages}):**\n\n"
        
        for i, song in enumerate(page_songs, start=start_idx + 1):
            status = "🎵 Now Playing" if i == 1 else f"#{i}"
            queue_text += f"{status}: **{song.title}** [{song.duration}]"
            if song.requested_by:
                queue_text += f" - *{song.requested_by}*"
            queue_text += "\n"
        
        queue_text += f"\n**Total songs:** {len(queue)}"
        
        return queue_text
    
    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.secondary, custom_id="queue:prev")
    async def prev_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Previous page button."""
        self.page -= 1
        self._update_button_states()
        await interaction.response.edit_message(content=self.get_page_content(), view=self)
    
    @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.secondary, custom_id="queue:next")
    async def next_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Next page button."""
        self.page += 1
        self._update_button_states()
        await interaction.response.edit_message(content=self.get_page_content(), view=self)
    
    @discord.ui.button(emoji="🗑️", style=discord.ButtonStyle.danger, custom_id="queue:clear")
    async def clear_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button to clear the queue."""
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server!", ephemeral=True)
            return
        
        cleared = music_service.clear_and_stop(interaction.guild.id)
        
        if cleared > 0:
            await interaction.response.edit_message(
                content=f"🗑️ Cleared {cleared} song(s) from the queue and stopped playback!",
                view=None
            )
        else:
            await interaction.response.send_message("❌ Queue is already empty!", ephemeral=True)

