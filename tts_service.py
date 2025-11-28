"""Streaming text-to-speech service using Edge TTS."""

import os
import tempfile
import asyncio
from typing import Optional, AsyncGenerator
import discord
from discord import FFmpegPCMAudio
import edge_tts


class StreamingTTSService:
    """Service for streaming text-to-speech conversion and playback."""
    
    # Voice mapping for different languages
    VOICES = {
        "uk": "uk-UA-PolinaNeural",  # Ukrainian female voice
        "uk-m": "uk-UA-OstapNeural",  # Ukrainian male voice
        "en": "en-US-JennyNeural",  # English female voice
        "en-m": "en-US-GuyNeural",  # English male voice
        "ru": "ru-RU-SvetlanaNeural",  # Russian (fallback)
    }
    
    def __init__(self):
        """Initialize streaming TTS service."""
        self.ffmpeg_options = {
            'options': '-vn'
        }
        self.default_voice = self.VOICES["uk"]
        self.temp_files = []  # Track temp files for cleanup
        print("✅ Streaming TTS service initialized (Edge TTS)")
    
    def get_voice(self, lang: str = "uk") -> str:
        """
        Get the voice for a given language.
        
        Args:
            lang: Language code
            
        Returns:
            Voice identifier
        """
        return self.VOICES.get(lang, self.default_voice)
    
    async def text_to_speech_stream(
        self,
        text: str,
        lang: str = "uk"
    ) -> AsyncGenerator[bytes, None]:
        """
        Convert text to speech and yield audio chunks as a stream.
        
        Args:
            text: Text to convert
            lang: Language code
            
        Yields:
            Audio data chunks
        """
        voice = self.get_voice(lang)
        
        try:
            print(f"🔊 Streaming TTS: {text[:50]}..." if len(text) > 50 else f"🔊 Streaming TTS: {text}")
            
            communicate = edge_tts.Communicate(text, voice)
            
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]
                    
        except Exception as e:
            print(f"❌ Error streaming TTS: {e}")
    
    async def text_to_speech(self, text: str, lang: str = "uk") -> Optional[str]:
        """
        Convert text to speech and save to temporary file.
        
        Args:
            text: Text to convert
            lang: Language code
            
        Returns:
            Path to temporary audio file, or None if conversion failed
        """
        voice = self.get_voice(lang)
        
        try:
            print(f"🔊 Converting text to speech: {text[:50]}..." if len(text) > 50 else f"🔊 Converting text to speech: {text}")
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            temp_path = temp_file.name
            temp_file.close()
            
            # Generate speech using Edge TTS
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(temp_path)
            
            print(f"✅ TTS saved to {temp_path}")
            self.temp_files.append(temp_path)
            
            return temp_path
            
        except Exception as e:
            print(f"❌ Error converting text to speech: {e}")
            return None
    
    async def stream_to_voice_channel(
        self,
        voice_client: discord.VoiceClient,
        text: str,
        lang: str = "uk"
    ) -> bool:
        """
        Stream TTS audio directly to a Discord voice channel.
        
        This method streams audio chunks as they're generated,
        providing lower latency than generating the full audio first.
        
        Args:
            voice_client: Discord voice client
            text: Text to speak
            lang: Language code
            
        Returns:
            True if streaming started, False otherwise
        """
        try:
            # Stop any current playback
            if voice_client.is_playing():
                voice_client.stop()
            
            # For Discord, we need a file-based approach with FFmpeg
            # Generate audio file first, then stream play it
            audio_path = await self.text_to_speech(text, lang)
            
            if audio_path:
                return await self.play_in_voice_channel(voice_client, audio_path)
            
            return False
            
        except Exception as e:
            print(f"❌ Error streaming to voice channel: {e}")
            return False
    
    async def play_in_voice_channel(
        self, 
        voice_client: discord.VoiceClient, 
        audio_path: str
    ) -> bool:
        """
        Play audio file in Discord voice channel.
        
        Args:
            voice_client: Discord voice client
            audio_path: Path to audio file
            
        Returns:
            True if playback started, False otherwise
        """
        try:
            # Stop any current playback
            if voice_client.is_playing():
                voice_client.stop()
            
            # Play audio
            source = FFmpegPCMAudio(audio_path, **self.ffmpeg_options)
            
            def after_playing(error):
                if error:
                    print(f"Error playing TTS: {error}")
                # Clean up temporary file
                try:
                    os.remove(audio_path)
                    if audio_path in self.temp_files:
                        self.temp_files.remove(audio_path)
                except Exception:
                    pass
            
            voice_client.play(source, after=after_playing)
            print("🔊 Playing TTS in voice channel")
            
            return True
            
        except Exception as e:
            print(f"❌ Error playing audio: {e}")
            return False
    
    async def play_beep(self, voice_client: discord.VoiceClient) -> bool:
        """
        Play a simple beep sound.
        
        Args:
            voice_client: Discord voice client
            
        Returns:
            True if playback started, False otherwise
        """
        beep_path = await self.text_to_speech("beep", lang="en")
        if beep_path:
            return await self.play_in_voice_channel(voice_client, beep_path)
        return False
    
    def cleanup(self) -> None:
        """Clean up all temporary files."""
        for temp_file in self.temp_files:
            try:
                os.remove(temp_file)
            except Exception:
                pass
        self.temp_files = []


# Alias for backward compatibility
class TTSService(StreamingTTSService):
    """Backward compatible alias for StreamingTTSService."""
    pass


# Global TTS service instance
tts_service = TTSService()