"""Music service for Discord bot - handles YouTube playback and queue management."""

import asyncio
import random
import time
from typing import Optional, Dict, List, Tuple
from functools import lru_cache
import discord
from discord import FFmpegPCMAudio
import yt_dlp


class Song:
    """Represents a song in the queue."""
    
    def __init__(self, title: str, url: str, duration: str, duration_seconds: int = 0, requested_by: Optional[str] = None, thumbnail: Optional[str] = None):
        self.title = title
        self.url = url  # This is the YouTube webpage URL
        self.duration = duration
        self.duration_seconds = duration_seconds
        self.requested_by = requested_by
        self.thumbnail = thumbnail
        self.start_time: Optional[float] = None  # Track when song started playing


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
        self.loop_mode: str = "off"  # "off", "song", or "queue"
        self.ffmpeg_process = None  # Track FFmpeg process


class MusicService:
    """Service for managing music playback across guilds."""
    
    def __init__(self):
        self.queues: Dict[int, GuildQueue] = {}
        self._metadata_cache: Dict[str, Tuple[dict, float]] = {}  # url -> (metadata, timestamp)
        self._cache_ttl = 3600  # Cache for 1 hour
        
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
    
    def _get_cached_metadata(self, url: str) -> Optional[dict]:
        """Get cached metadata if available and not expired."""
        if url in self._metadata_cache:
            metadata, timestamp = self._metadata_cache[url]
            if time.time() - timestamp < self._cache_ttl:
                print(f"Using cached metadata for: {url}")
                return metadata
            else:
                # Remove expired cache
                del self._metadata_cache[url]
        return None
    
    def _cache_metadata(self, url: str, metadata: dict) -> None:
        """Cache metadata for a URL."""
        self._metadata_cache[url] = (metadata, time.time())
        # Clean up old cache entries (keep only last 100)
        if len(self._metadata_cache) > 100:
            oldest = min(self._metadata_cache.items(), key=lambda x: x[1][1])
            del self._metadata_cache[oldest[0]]
    
    async def search_youtube(self, query: str) -> Optional[Song]:
        """
        Search YouTube for a video or get info from URL.
        
        Args:
            query: Search query or YouTube URL
            
        Returns:
            Song object if found, None otherwise
        """
        try:
            # Check cache first for direct URLs
            if query.startswith('http'):
                cached = self._get_cached_metadata(query)
                if cached:
                    return Song(
                        title=cached['title'],
                        url=cached['webpage_url'],
                        duration=self._format_duration(cached.get('duration', 0)),
                        duration_seconds=cached.get('duration', 0),
                        thumbnail=cached.get('thumbnail')
                    )
            
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
                
                # Cache the metadata
                self._cache_metadata(info['webpage_url'], info)
                
                # Format duration
                duration_sec = info.get('duration', 0)
                duration = self._format_duration(duration_sec)
                
                print(f"YouTube video found: {info['title']}")
                print(f"Video URL: {info['webpage_url']}")
                print(f"Duration: {duration}")
                
                return Song(
                    title=info['title'],
                    url=info['webpage_url'],
                    duration=duration,
                    duration_seconds=duration_sec,
                    thumbnail=info.get('thumbnail')
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
                        duration=duration,
                        duration_seconds=duration_sec,
                        thumbnail=entry.get('thumbnail')
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
    
    def _cleanup_ffmpeg(self, guild_id: int) -> None:
        """Clean up FFmpeg process for a guild."""
        queue = self.queues.get(guild_id)
        if queue and queue.ffmpeg_process:
            try:
                if queue.ffmpeg_process.poll() is None:  # Process is still running
                    queue.ffmpeg_process.terminate()
                    queue.ffmpeg_process.wait(timeout=2)
                    print(f"Cleaned up FFmpeg process for guild {guild_id}")
            except Exception as e:
                print(f"Error cleaning up FFmpeg: {e}")
            finally:
                queue.ffmpeg_process = None
    
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
                self._cleanup_ffmpeg(guild_id)
            return
        
        # Clean up any existing FFmpeg process
        self._cleanup_ffmpeg(guild_id)
        
        song = queue.songs[0]
        queue.current_song = song
        queue.is_playing = True
        song.start_time = time.time()  # Record start time
        
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
            
            # Store FFmpeg process reference
            if hasattr(source, '_process'):
                queue.ffmpeg_process = source._process
            
            # Play the audio
            def after_playing(error):
                if error:
                    print(f"Error playing song: {error}")
                # Clean up FFmpeg
                self._cleanup_ffmpeg(guild_id)
                # Schedule the next song
                asyncio.run_coroutine_threadsafe(self._play_next(guild_id), queue.voice_client.loop)
            
            queue.voice_client.play(source, after=after_playing)
            
        except Exception as e:
            print(f"Error playing song: {e}")
            self._cleanup_ffmpeg(guild_id)
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
        
        # Handle loop modes
        if queue.loop_mode == "song" and queue.current_song:
            # Don't remove current song, just replay it
            queue.current_song.start_time = None  # Reset start time
            await self._play_song(guild_id)
            return
        
        # Add current song to history before removing (if not looping queue)
        if queue.songs and queue.current_song:
            queue.history.append(queue.current_song)
            # Keep only last 10 songs in history
            if len(queue.history) > 10:
                queue.history.pop(0)
        
        # Remove the current song
        if queue.songs:
            removed_song = queue.songs.pop(0)
            
            # If looping queue, add song back to end
            if queue.loop_mode == "queue":
                queue.songs.append(removed_song)
        
        if not queue.songs:
            queue.is_playing = False
            queue.current_song = None
            self._cleanup_ffmpeg(guild_id)
            return
        
        await self._play_song(guild_id)
    
    def shuffle_queue(self, guild_id: int) -> bool:
        """
        Shuffle the queue (keeping currently playing song at front).
        
        Args:
            guild_id: ID of the guild
            
        Returns:
            True if shuffled, False if queue is too small
        """
        queue = self.queues.get(guild_id)
        
        if not queue or len(queue.songs) <= 1:
            return False
        
        # Keep first song (currently playing), shuffle the rest
        current_song = queue.songs[0]
        remaining_songs = queue.songs[1:]
        random.shuffle(remaining_songs)
        queue.songs = [current_song] + remaining_songs
        
        return True
    
    def set_loop_mode(self, guild_id: int, mode: str) -> bool:
        """
        Set the loop mode for a guild.
        
        Args:
            guild_id: ID of the guild
            mode: "off", "song", or "queue"
            
        Returns:
            True if mode was set, False otherwise
        """
        if mode not in ["off", "song", "queue"]:
            return False
        
        queue = self.queues.get(guild_id)
        if not queue:
            return False
        
        queue.loop_mode = mode
        return True
    
    def get_loop_mode(self, guild_id: int) -> str:
        """Get the current loop mode for a guild."""
        queue = self.queues.get(guild_id)
        return queue.loop_mode if queue else "off"
    
    def get_current_position(self, guild_id: int) -> int:
        """
        Get current playback position in seconds.
        
        Args:
            guild_id: ID of the guild
            
        Returns:
            Current position in seconds
        """
        queue = self.queues.get(guild_id)
        if not queue or not queue.current_song or not queue.current_song.start_time:
            return 0
        
        if queue.is_paused:
            # Return position at pause time (would need to track pause time separately for accuracy)
            return 0
        
        elapsed = int(time.time() - queue.current_song.start_time)
        return min(elapsed, queue.current_song.duration_seconds)
    
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
        
        # Clean up FFmpeg
        self._cleanup_ffmpeg(guild_id)
        
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
