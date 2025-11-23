"""Music service for Discord bot - handles YouTube playback and queue management."""

import asyncio
from typing import Optional, Dict, List
import discord
from discord import FFmpegPCMAudio
import yt_dlp


class Song:
    """Represents a song in the queue."""
    
    def __init__(self, title: str, url: str, duration: str, requested_by: Optional[str] = None):
        self.title = title
        self.url = url  # This is the YouTube webpage URL
        self.duration = duration
        self.requested_by = requested_by


class GuildQueue:
    """Represents the music queue for a guild."""
    
    def __init__(self, voice_client: discord.VoiceClient):
        self.songs: List[Song] = []
        self.voice_client = voice_client
        self.is_playing = False
        self.current_song: Optional[Song] = None
        self.is_paused = False
        self.history: List[Song] = []  # Track previous songs
        self.last_control_message: Optional[discord.Message] = None  # Track last message with buttons


class MusicService:
    """Service for managing music playback across guilds."""
    
    def __init__(self):
        self.queues: Dict[int, GuildQueue] = {}
        
        # yt-dlp options for streaming (no download)
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch',
            'source_address': '0.0.0.0',
        }
        
        # yt-dlp options for playlists
        self.ydl_playlist_opts = {
            'format': 'bestaudio/best',
            'noplaylist': False,
            'extract_flat': True,  # Don't download, just get metadata
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'source_address': '0.0.0.0',
        }
        
        self.ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn -b:a 128k'  # Set audio bitrate for consistent streaming
        }
    
    async def search_youtube(self, query: str) -> Optional[Song]:
        """
        Search YouTube for a video or get info from URL.
        
        Args:
            query: Search query or YouTube URL
            
        Returns:
            Song object if found, None otherwise
        """
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # Extract info without downloading
                info = await asyncio.to_thread(
                    lambda: ydl.extract_info(f"ytsearch:{query}", download=False)
                )
                
                if not info:
                    return None
                
                # If it's a search result, get the first video
                if 'entries' in info:
                    if not info['entries']:
                        return None
                    info = info['entries'][0]
                
                # Format duration
                duration_sec = info.get('duration', 0)
                duration = self._format_duration(duration_sec)
                
                print(f"YouTube video found: {info['title']}")
                print(f"Video URL: {info['webpage_url']}")
                print(f"Duration: {duration}")
                
                return Song(
                    title=info['title'],
                    url=info['webpage_url'],
                    duration=duration
                )
                
        except Exception as e:
            print(f"search_youtube error: {e}")
            return None
    
    async def search_youtube_playlist(self, url: str) -> Optional[List[Song]]:
        """
        Extract all songs from a YouTube playlist.
        
        Args:
            url: YouTube playlist URL
            
        Returns:
            List of Song objects, or None if extraction fails
        """
        try:
            with yt_dlp.YoutubeDL(self.ydl_playlist_opts) as ydl:
                print(f"Extracting playlist info from: {url}")
                
                # Extract playlist info
                info = await asyncio.to_thread(
                    lambda: ydl.extract_info(url, download=False)
                )
                
                if not info:
                    return None
                
                # Check if it's a playlist
                if 'entries' not in info:
                    print("URL is not a playlist")
                    return None
                
                songs = []
                entries = info['entries']
                
                print(f"Found {len(entries)} videos in playlist")
                
                for entry in entries:
                    if not entry:
                        continue
                    
                    # Get video URL
                    video_url = entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}"
                    
                    # Get duration and convert to int (handle float or None)
                    duration_sec = entry.get('duration', 0)
                    if duration_sec is None:
                        duration_sec = 0
                    duration_sec = int(duration_sec)  # Convert float to int
                    duration = self._format_duration(duration_sec)
                    
                    # Create song object
                    song = Song(
                        title=entry.get('title', 'Unknown Title'),
                        url=video_url,
                        duration=duration
                    )
                    songs.append(song)
                
                print(f"Successfully extracted {len(songs)} songs from playlist")
                return songs
                
        except Exception as e:
            print(f"search_youtube_playlist error: {e}")
            return None
    
    async def _get_stream_url(self, youtube_url: str) -> Optional[str]:
        """
        Get the direct streaming URL for a YouTube video.
        
        Args:
            youtube_url: YouTube video URL
            
        Returns:
            Direct audio stream URL or None
        """
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = await asyncio.to_thread(
                    lambda: ydl.extract_info(youtube_url, download=False)
                )
                return info['url']
        except Exception as e:
            print(f"Error getting stream URL: {e}")
            return None
    
    async def add_to_queue(self, guild_id: int, song: Song, voice_client: discord.VoiceClient) -> None:
        """
        Add a song to the guild's queue.
        
        Args:
            guild_id: ID of the guild
            song: Song to add
            voice_client: Voice client for the guild
        """
        if guild_id not in self.queues:
            self.queues[guild_id] = GuildQueue(voice_client)
        
        queue = self.queues[guild_id]
        queue.songs.append(song)
        
        # If nothing is playing, start playing
        if not queue.is_playing:
            await self._play_song(guild_id)
    
    async def add_playlist_to_queue(self, guild_id: int, songs: List[Song], voice_client: discord.VoiceClient) -> None:
        """
        Add multiple songs to the guild's queue.
        
        Args:
            guild_id: ID of the guild
            songs: List of songs to add
            voice_client: Voice client for the guild
        """
        if guild_id not in self.queues:
            self.queues[guild_id] = GuildQueue(voice_client)
        
        queue = self.queues[guild_id]
        queue.songs.extend(songs)
        
        # If nothing is playing, start playing
        if not queue.is_playing:
            await self._play_song(guild_id)
    
    async def _play_song(self, guild_id: int) -> None:
        """
        Play the next song in the queue by streaming directly from YouTube.
        
        Args:
            guild_id: ID of the guild
        """
        queue = self.queues.get(guild_id)
        
        if not queue or not queue.songs:
            if queue:
                queue.is_playing = False
            return
        
        song = queue.songs[0]
        queue.current_song = song
        queue.is_playing = True
        
        try:
            print(f"Streaming song: {song.title}")
            
            # Get the streaming URL (fresh URL each time to avoid expiration)
            stream_url = await self._get_stream_url(song.url)
            
            if not stream_url:
                print(f"Failed to get stream URL for: {song.title}")
                queue.songs.pop(0)
                await self._play_song(guild_id)
                return
            
            # Create audio source that streams directly
            source = FFmpegPCMAudio(stream_url, **self.ffmpeg_options)
            
            # Play the audio
            def after_playing(error):
                if error:
                    print(f"Error playing song: {error}")
                # Schedule the next song
                asyncio.run_coroutine_threadsafe(self._play_next(guild_id), queue.voice_client.loop)
            
            queue.voice_client.play(source, after=after_playing)
            
        except Exception as e:
            print(f"Error playing song: {e}")
            queue.songs.pop(0)
            await self._play_song(guild_id)
    
    async def _play_next(self, guild_id: int) -> None:
        """
        Play the next song in the queue.
        
        Args:
            guild_id: ID of the guild
        """
        queue = self.queues.get(guild_id)
        if not queue:
            return
        
        # Add current song to history before removing
        if queue.songs and queue.current_song:
            queue.history.append(queue.current_song)
            # Keep only last 10 songs in history
            if len(queue.history) > 10:
                queue.history.pop(0)
        
        # Remove the current song
        if queue.songs:
            queue.songs.pop(0)
        
        if not queue.songs:
            queue.is_playing = False
            queue.current_song = None
            return
        
        await self._play_song(guild_id)
    
    def skip(self, guild_id: int) -> bool:
        """
        Skip the current song.
        
        Args:
            guild_id: ID of the guild
            
        Returns:
            True if skipped, False if nothing was playing
        """
        queue = self.queues.get(guild_id)
        
        if not queue or not queue.is_playing:
            return False
        
        # Stop the current song (this will trigger the after callback)
        if queue.voice_client.is_playing():
            queue.voice_client.stop()
            return True
        
        return False
    
    def pause(self, guild_id: int) -> bool:
        """
        Pause the current song.
        
        Args:
            guild_id: ID of the guild
            
        Returns:
            True if paused, False if nothing was playing
        """
        queue = self.queues.get(guild_id)
        
        if not queue or not queue.is_playing:
            return False
        
        if queue.voice_client.is_playing() and not queue.is_paused:
            queue.voice_client.pause()
            queue.is_paused = True
            return True
        
        return False
    
    def resume(self, guild_id: int) -> bool:
        """
        Resume the current song.
        
        Args:
            guild_id: ID of the guild
            
        Returns:
            True if resumed, False if nothing was paused
        """
        queue = self.queues.get(guild_id)
        
        if not queue or not queue.is_playing:
            return False
        
        if queue.voice_client.is_paused() and queue.is_paused:
            queue.voice_client.resume()
            queue.is_paused = False
            return True
        
        return False
    
    async def previous(self, guild_id: int) -> bool:
        """
        Go back to the previous song.
        
        Args:
            guild_id: ID of the guild
            
        Returns:
            True if went to previous song, False if no history
        """
        queue = self.queues.get(guild_id)
        
        if not queue or not queue.history:
            return False
        
        # Get the last song from history
        previous_song = queue.history.pop()
        
        # Add current song back to front of queue if exists
        if queue.current_song:
            queue.songs.insert(0, queue.current_song)
        
        # Add previous song to front of queue
        queue.songs.insert(0, previous_song)
        
        # Stop current playback to trigger next song
        if queue.voice_client.is_playing() or queue.voice_client.is_paused():
            queue.voice_client.stop()
        else:
            # If nothing is playing, start playing
            await self._play_song(guild_id)
        
        return True
    
    def clear_queue(self, guild_id: int) -> int:
        """
        Clear the entire queue (except current song).
        
        Args:
            guild_id: ID of the guild
            
        Returns:
            Number of songs removed from queue
        """
        queue = self.queues.get(guild_id)
        
        if not queue:
            return 0
        
        # Keep only the first song (currently playing)
        queue_length = len(queue.songs) - 1
        if queue_length > 0:
            queue.songs = queue.songs[:1]
        
        return max(0, queue_length)
    
    def clear_and_stop(self, guild_id: int) -> int:
        """
        Clear the entire queue and stop playback completely.
        
        Args:
            guild_id: ID of the guild
            
        Returns:
            Number of songs removed from queue
        """
        queue = self.queues.get(guild_id)
        
        if not queue:
            return 0
        
        # Count songs to be cleared
        queue_length = len(queue.songs)
        
        # Stop playback
        if queue.voice_client.is_playing() or queue.voice_client.is_paused():
            queue.voice_client.stop()
        
        # Clear the queue completely
        queue.songs.clear()
        queue.is_playing = False
        queue.is_paused = False
        queue.current_song = None
        
        return queue_length
    
    def get_queue(self, guild_id: int) -> List[Song]:
        """
        Get the queue for a guild.
        
        Args:
            guild_id: ID of the guild
            
        Returns:
            List of songs in the queue
        """
        queue = self.queues.get(guild_id)
        return queue.songs if queue else []
    
    def _format_duration(self, seconds: int) -> str:
        """
        Format duration in seconds to HH:MM:SS or MM:SS format.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"


# Singleton instance
music_service = MusicService()
