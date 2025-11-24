"""Text-to-speech service using gTTS."""

import os
import tempfile
from typing import Optional
from gtts import gTTS
import discord
from discord import FFmpegPCMAudio


class TTSService:
    """Service for text-to-speech conversion and playback."""
    
    def __init__(self):
        """Initialize TTS service."""
        self.ffmpeg_options = {
            'options': '-vn'
        }
        print("✅ TTS service initialized")
    
    async def text_to_speech(self, text: str, lang: str = "uk") -> Optional[str]:
        """
        Convert text to speech and save to temporary file.
        
        Args:
            text: Text to convert
            lang: Language code (default: "uk" for Ukrainian)
            
        Returns:
            Path to temporary audio file, or None if conversion failed
        """
        try:
            print(f"🔊 Converting text to speech: {text}")
            
            # Create TTS
            tts = gTTS(text=text, lang=lang, slow=False)
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            tts.save(temp_file.name)
            
            print(f"✅ TTS saved to {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            print(f"❌ Error converting text to speech: {e}")
            return None
    
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
                except:
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
        # Create a simple beep using text-to-speech
        beep_path = await self.text_to_speech("beep", lang="en")
        if beep_path:
            return await self.play_in_voice_channel(voice_client, beep_path)
        return False


# Global TTS service instance
tts_service = TTSService()