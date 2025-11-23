"""Play command - plays music from YouTube."""

from typing import List
import discord
from commands.base_command import Command
from music_service import music_service
from music_controls import MusicControlView


class PlayCommand(Command):
    """Command that plays music from YouTube."""
    
    def __init__(self):
        super().__init__("play", "Plays a song from YouTube")

    async def _remove_old_buttons(self, guild_id: int):
        """Remove buttons from the previous message."""
        queue = music_service.queues.get(guild_id)
        if queue and queue.last_control_message:
            try:
                await queue.last_control_message.edit(view=None)
            except discord.NotFound:
                pass  # Message was deleted
            except discord.HTTPException:
                pass  # Failed to edit

    async def execute(self, message: discord.Message, args: List[str]) -> None:
        """Execute the play command."""
        if not args:
            await message.reply("Please provide a song name or URL!")
            return
        
        # Check if user is in a voice channel
        if not message.author.voice or not message.author.voice.channel:
            await message.reply("You need to be in a voice channel to play music!")
            return
        
        voice_channel = message.author.voice.channel
        
        # Check bot permissions
        permissions = voice_channel.permissions_for(message.guild.me)
        if not permissions.connect or not permissions.speak:
            await message.reply("I need permissions to join and speak in your voice channel!")
            return
        
        try:
            song_query = " ".join(args)
            
            # Check if it's a playlist URL
            is_playlist = "playlist" in song_query.lower() or "list=" in song_query
            
            if is_playlist:
                search_msg = await message.reply(f"🔍 Loading playlist...")
                
                # Extract playlist
                songs = await music_service.search_youtube_playlist(song_query)
                
                if not songs or len(songs) == 0:
                    await search_msg.edit(content="❌ No videos found in that playlist!")
                    return
                
                # Set requested_by for all songs
                for song in songs:
                    song.requested_by = message.author.name
                
                # Connect to voice channel if not already connected
                voice_client = message.guild.voice_client
                if not voice_client:
                    voice_client = await voice_channel.connect()
                elif voice_client.channel != voice_channel:
                    await voice_client.move_to(voice_channel)
                
                # Get current queue length
                queue_length = len(music_service.get_queue(message.guild.id))
                
                # Add all songs to queue
                await music_service.add_playlist_to_queue(message.guild.id, songs, voice_client)
                
                # Remove buttons from old message
                await self._remove_old_buttons(message.guild.id)
                
                # Create control view with button states
                control_view = MusicControlView(guild_id=message.guild.id)
                
                # Send confirmation message
                if queue_length == 0:
                    new_msg = await search_msg.edit(
                        content=f"🎵 Now playing playlist with **{len(songs)}** songs!\nStarting with: **{songs[0].title}**\nRequested by: {message.author.name}",
                        view=control_view
                    )
                    # Store the new message with buttons
                    queue = music_service.queues.get(message.guild.id)
                    if queue:
                        queue.last_control_message = new_msg
                else:
                    new_msg = await search_msg.edit(
                        content=f"✅ Added **{len(songs)}** songs from playlist to queue!\nRequested by: {message.author.name}",
                        view=control_view
                    )
                    # Store the new message with buttons
                    queue = music_service.queues.get(message.guild.id)
                    if queue:
                        queue.last_control_message = new_msg
            else:
                # Single song logic
                search_msg = await message.reply(f"🔍 Searching for: **{song_query}**...")
                
                # Search for the song
                song = await music_service.search_youtube(song_query)
                
                if not song:
                    await search_msg.edit(content="❌ No results found for that query!")
                    return
                
                song.requested_by = message.author.name
                
                # Connect to voice channel if not already connected
                voice_client = message.guild.voice_client
                if not voice_client:
                    voice_client = await voice_channel.connect()
                elif voice_client.channel != voice_channel:
                    await voice_client.move_to(voice_channel)
                
                # Get current queue length
                queue_length = len(music_service.get_queue(message.guild.id))
                
                # Add to queue
                await music_service.add_to_queue(message.guild.id, song, voice_client)
                
                # Remove buttons from old message
                await self._remove_old_buttons(message.guild.id)
                
                # Create control view with button states
                control_view = MusicControlView(guild_id=message.guild.id)
                
                # Send appropriate message
                if queue_length == 0:
                    new_msg = await search_msg.edit(
                        content=f"🎵 Now playing: **{song.title}** [{song.duration}]\nRequested by: {song.requested_by}",
                        view=control_view
                    )
                    # Store the new message with buttons
                    queue = music_service.queues.get(message.guild.id)
                    if queue:
                        queue.last_control_message = new_msg
                else:
                    new_msg = await search_msg.edit(
                        content=f"✅ Added to queue (Position #{queue_length + 1}): **{song.title}** [{song.duration}]",
                        view=control_view
                    )
                    # Store the new message with buttons
                    queue = music_service.queues.get(message.guild.id)
                    if queue:
                        queue.last_control_message = new_msg
                
        except Exception as e:
            print(f"Error playing music: {e}")
            await message.reply("❌ Failed to play the song!")
