"""Speech recognition service using Groq Whisper with streaming support."""

import os
import tempfile
import wave
import asyncio
import io
from typing import Optional, AsyncGenerator, Callable
from groq import Groq
from dotenv import load_dotenv
import numpy as np

load_dotenv()


class StreamingSpeechService:
    """Service for streaming speech recognition using Groq Whisper."""
    
    def __init__(self):
        """Initialize speech recognition service."""
        # Set default values first
        self.model = "whisper-large-v3"
        self.sample_rate = 16000
        self.chunk_duration = 0.5  # seconds per chunk for streaming
        self.silence_threshold = 500  # amplitude threshold for silence detection
        self.silence_duration = 1.5  # seconds of silence to stop recording
        self.max_recording_duration = 30  # maximum recording duration
        self.audio_buffer = []
        self.is_recording = False
        
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            print("Warning: GROQ_API_KEY not found in environment variables")
            self.client = None
            return
        
        try:
            self.client = Groq(api_key=self.api_key)
            print("✅ Streaming speech recognition service initialized")
        except Exception as e:
            print(f"❌ Error initializing speech service: {e}")
            self.client = None
    
    def _is_silent(self, audio_data: bytes) -> bool:
        """
        Check if audio data is silent.
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            True if audio is silent, False otherwise
        """
        try:
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            amplitude = np.abs(audio_array).mean()
            return amplitude < self.silence_threshold
        except Exception:
            return False
    
    async def start_streaming_recognition(
        self,
        on_partial_result: Optional[Callable[[str], None]] = None,
        on_final_result: Optional[Callable[[str], None]] = None
    ) -> None:
        """
        Start streaming speech recognition from Discord audio buffer.
        
        This method processes audio that's been accumulated in the buffer
        and triggers callbacks for partial and final results.
        
        Args:
            on_partial_result: Callback for partial transcription results
            on_final_result: Callback for final transcription result
        """
        self.is_recording = True
        self.audio_buffer = []
        print("🎤 Started streaming speech recognition...")
    
    def add_audio_chunk(self, audio_data: bytes) -> None:
        """
        Add an audio chunk to the buffer for processing.
        
        Args:
            audio_data: Raw PCM audio data (16kHz, mono, 16-bit)
        """
        if self.is_recording:
            self.audio_buffer.append(audio_data)
    
    async def stop_streaming_recognition(self) -> Optional[str]:
        """
        Stop streaming recognition and get final transcription.
        
        Returns:
            Final transcribed text, or None if failed
        """
        self.is_recording = False
        
        if not self.audio_buffer:
            print("❌ No audio data in buffer")
            return None
        
        # Combine all audio chunks
        audio_data = b''.join(self.audio_buffer)
        self.audio_buffer = []
        
        return await self.transcribe_audio_data(audio_data)
    
    async def transcribe_audio_data(self, audio_data: bytes) -> Optional[str]:
        """
        Transcribe raw audio data using Groq Whisper.
        
        Args:
            audio_data: Raw PCM audio data (16kHz, mono, 16-bit)
            
        Returns:
            Transcribed text, or None if transcription failed
        """
        if not self.client:
            print("❌ Speech service not initialized")
            return None
        
        try:
            print("🔄 Transcribing audio stream...")
            
            # Create a WAV file in memory
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit audio
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data)
            
            wav_buffer.seek(0)
            
            # Run transcription in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            transcription = await loop.run_in_executor(
                None,
                lambda: self.client.audio.transcriptions.create(
                    file=("audio.wav", wav_buffer.read()),
                    model=self.model,
                    temperature=0,
                    response_format="text",
                )
            )
            
            text = transcription.strip() if isinstance(transcription, str) else transcription.text.strip()
            print(f"✅ Transcription: {text}")
            
            return text if text else None
            
        except Exception as e:
            print(f"❌ Error transcribing audio: {e}")
            return None
    
    async def transcribe_audio_file(self, audio_path: str) -> Optional[str]:
        """
        Transcribe audio file using Groq Whisper.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text, or None if transcription failed
        """
        if not self.client:
            print("❌ Speech service not initialized")
            return None
        
        try:
            print("🔄 Transcribing audio file...")
            
            with open(audio_path, "rb") as file:
                loop = asyncio.get_event_loop()
                transcription = await loop.run_in_executor(
                    None,
                    lambda: self.client.audio.transcriptions.create(
                        file=(audio_path, file.read()),
                        model=self.model,
                        temperature=0,
                        response_format="text",
                    )
                )
            
            text = transcription.strip() if isinstance(transcription, str) else transcription.text.strip()
            print(f"✅ Transcription: {text}")
            
            # Clean up temporary file
            try:
                os.remove(audio_path)
            except Exception:
                pass
            
            return text if text else None
            
        except Exception as e:
            print(f"❌ Error transcribing audio: {e}")
            return None
    
    def process_discord_audio(self, pcm_data: bytes) -> bytes:
        """
        Process Discord audio data for transcription.
        
        Discord sends 48kHz stereo audio, we need 16kHz mono.
        
        Args:
            pcm_data: Raw PCM audio from Discord (48kHz, stereo, 16-bit)
            
        Returns:
            Processed audio data (16kHz, mono, 16-bit)
        """
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(pcm_data, dtype=np.int16)
            
            # Convert stereo to mono by taking every other sample
            if len(audio_array) % 2 == 0:
                mono_audio = audio_array[::2]
            else:
                mono_audio = audio_array
            
            # Downsample from 48kHz to 16kHz (factor of 3)
            downsampled = mono_audio[::3]
            
            return downsampled.tobytes()
            
        except Exception as e:
            print(f"Error processing Discord audio: {e}")
            return b''


# Alias for backward compatibility
class SpeechService(StreamingSpeechService):
    """Backward compatible alias for StreamingSpeechService."""
    
    async def record_audio(self, duration: int = 5, sample_rate: int = 16000) -> Optional[str]:
        """
        Record audio from microphone (legacy method).
        
        This method is kept for backward compatibility.
        For new implementations, use streaming methods instead.
        """
        try:
            import pyaudio
            
            print(f"🎤 Recording for {duration} seconds...")
            
            pa = pyaudio.PyAudio()
            
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=sample_rate,
                input=True,
                frames_per_buffer=1024
            )
            
            frames = []
            for _ in range(0, int(sample_rate / 1024 * duration)):
                data = stream.read(1024, exception_on_overflow=False)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            pa.terminate()
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            
            wf = wave.open(temp_file.name, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            print(f"✅ Recording saved to {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            print(f"❌ Error recording audio: {e}")
            return None
    
    async def recognize_speech(self, duration: int = 5) -> Optional[str]:
        """
        Record and transcribe speech (legacy method).
        """
        audio_path = await self.record_audio(duration)
        if not audio_path:
            return None
        
        return await self.transcribe_audio_file(audio_path)


# Global speech service instance
speech_service = SpeechService()