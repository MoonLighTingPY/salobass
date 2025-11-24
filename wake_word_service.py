"""Wake word detection service using Porcupine."""

import os
import struct
import pyaudio
import pvporcupine
from typing import Optional, Callable
import discord
from discord.ext import voice_recv
from dotenv import load_dotenv
import asyncio
from threading import Thread
import numpy as np
import io
import wave

load_dotenv()


class WakeWordService:
    """Service for detecting wake words using Porcupine."""
    
    def __init__(self, keyword_path: str = "models/ok-Salo_en_windows_v3_0_0.ppn"):
        """
        Initialize wake word detection service.
        
        Args:
            keyword_path: Path to the Porcupine keyword file
        """
        self.keyword_path = keyword_path
        self.access_key = os.getenv("PORCUPINE_ACCESS_KEY")
        self.porcupine: Optional[pvporcupine.Porcupine] = None
        self.audio_stream: Optional[pyaudio.Stream] = None
        self.pa: Optional[pyaudio.PyAudio] = None
        self.is_listening = False
        self.detection_callback: Optional[Callable] = None
        self.event_loop: Optional[asyncio.AbstractEventLoop] = None
        self.voice_client: Optional[discord.VoiceClient] = None
        self.audio_buffer = []
        self.frame_count = 0
        
        if not self.access_key:
            print("Warning: PORCUPINE_ACCESS_KEY not found in environment variables")
            return
        
        # Verify keyword file exists
        if not os.path.exists(keyword_path):
            print(f"Warning: Keyword file not found at {keyword_path}")
            return
        
        try:
            # Initialize Porcupine
            self.porcupine = pvporcupine.create(
                access_key=self.access_key,
                keyword_paths=[keyword_path]
            )
            print(f"✅ Wake word service initialized (keyword: 'Ok Salo')")
            print(f"   Sample rate: {self.porcupine.sample_rate} Hz")
            print(f"   Frame length: {self.porcupine.frame_length}")
        except Exception as e:
            print(f"❌ Error initializing Porcupine: {e}")
            self.porcupine = None
    
    def set_detection_callback(self, callback: Callable, event_loop: asyncio.AbstractEventLoop) -> None:
        """
        Set the callback function to be called when wake word is detected.
        
        Args:
            callback: Async function to call when wake word is detected
            event_loop: The event loop to schedule the callback in
        """
        self.detection_callback = callback
        self.event_loop = event_loop
    
    def start_listening(self) -> bool:
        """
        Start listening for wake word from Discord voice channel.
        
        Returns:
            True if listening started successfully, False otherwise
        """
        if not self.porcupine:
            print("❌ Porcupine not initialized")
            return False
        
        if self.is_listening:
            print("Already listening for wake word")
            return True
        
        try:
            self.is_listening = True
            self.audio_buffer = []
            self.frame_count = 0
            
            print("🎤 Started listening for 'Ok Salo' in Discord voice channel...")
            print("📝 Make sure you're speaking in Discord (not local microphone)")
            
            return True
            
        except Exception as e:
            print(f"❌ Error starting Discord audio listening: {e}")
            return False
    
    def process_audio_packet(self, user, data):
        """
        Process incoming audio packet from Discord voice channel.
        
        Args:
            user: Discord user who sent the audio
            data: Raw PCM audio data (48kHz, stereo, 16-bit)
        """
        if not self.is_listening or not self.porcupine:
            return
        
        try:
            # Discord sends 48kHz stereo audio, we need 16kHz mono for Porcupine
            # Convert bytes to numpy array
            audio_array = np.frombuffer(data, dtype=np.int16)
            
            # Convert stereo to mono by taking every other sample (left channel)
            if len(audio_array) % 2 == 0:
                mono_audio = audio_array[::2]
            else:
                mono_audio = audio_array
            
            # Downsample from 48kHz to 16kHz
            # Simple decimation by factor of 3 (48000/3 = 16000)
            downsampled = mono_audio[::3]
            
            # Add to buffer
            self.audio_buffer.extend(downsampled)
            
            # Process in chunks matching Porcupine's frame length
            while len(self.audio_buffer) >= self.porcupine.frame_length:
                # Extract one frame
                frame = self.audio_buffer[:self.porcupine.frame_length]
                self.audio_buffer = self.audio_buffer[self.porcupine.frame_length:]
                
                # Process with Porcupine
                keyword_index = self.porcupine.process(frame)
                
                if keyword_index >= 0:
                    print(f"🔔 Wake word detected from user: {user}")
                    
                    # Trigger callback in the bot's event loop
                    if self.detection_callback and self.event_loop:
                        asyncio.run_coroutine_threadsafe(
                            self.detection_callback(),
                            self.event_loop
                        )
                    
                    # Clear buffer after detection
                    self.audio_buffer = []
                    break
                
        except Exception as e:
            print(f"Error processing audio: {e}")
    
    def stop_listening(self) -> None:
        """Stop listening for wake word."""
        self.is_listening = False
        self.audio_buffer = []
        self.frame_count = 0
        
        print("🔇 Stopped listening for wake word")
    
    def cleanup(self) -> None:
        """Clean up resources."""
        self.stop_listening()
        
        if self.porcupine:
            self.porcupine.delete()
            self.porcupine = None


# Global wake word service instance
wake_word_service = WakeWordService()