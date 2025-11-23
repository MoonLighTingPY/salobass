"""Play command - plays music from YouTube."""

from typing import List
import discord
from commands.base_command import Command
from music_service import music_service
from music_controls import MusicControlView  # Import only the class


class PlayCommand(Command):
    """Command that plays music from YouTube."""
    
    def __init__(self):
        super().__init__("play", "Plays a song from YouTube")
        self.music_control_view = None  # Initialize as None

    def set_music_control_view(self, view: MusicControlView):
        """Set the MusicControlView instance."""
        self.music_control_view = view

    async def execute(self, message: discord.Message, args: List[str]) -> None:
        """Execute the play command."""
        if not self.music_control_view:
            await message.reply("Music control view is not initialized!")
            return
        
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
                
                # Send confirmation message
                if queue_length == 0:
                    await search_msg.edit(
                        content=f"🎵 Now playing playlist with **{len(songs)}** songs!\nStarting with: **{songs[0].title}**\nRequested by: {message.author.name}",
                        view=self.music_control_view
                    )
                else:
                    await search_msg.edit(
                        content=f"✅ Added **{len(songs)}** songs from playlist to queue!\nRequested by: {message.author.name}",
                        view=self.music_control_view
                    )
            else:
                # Single song logic (existing code)
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
                
                # Send appropriate message
                if queue_length == 0:
                    await search_msg.edit(
                        content=f"🎵 Now playing: **{song.title}** [{song.duration}]\nRequested by: {song.requested_by}",
                        view=self.music_control_view
                    )
                else:
                    await search_msg.edit(
                        content=f"✅ Added to queue (Position #{queue_length + 1}): **{song.title}** [{song.duration}]",
                        view=self.music_control_view
                    )
                
        except Exception as e:
            print(f"Error playing music: {e}")
            await message.reply("❌ Failed to play the song!")
