import asyncio
import queue
import threading
import numpy as np
import pyaudio
import base64
import requests
import json
import os
from faster_whisper import WhisperModel
from hanerma.orchestrator.nlp_compiler import compile_and_spawn
from hanerma.tools.registry import tool
from typing import Optional, Dict, Any

class VoiceHandler:
    """
    Lightweight local Speech-to-Text using Faster-Whisper.
    Real-time audio streaming with continuous transcription.
    """
    
    def __init__(self, model_size: str = "base", device: str = "cpu"):
        self.model = WhisperModel(model_size, device=device, compute_type="int8")
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.transcription_callback = None
        
    def set_callback(self, callback):
        """Set callback for handling transcribed text."""
        self.transcription_callback = callback
        
    def transcribe_audio_file(self, audio_path: str) -> str:
        """Transcribe a single audio file."""
        segments, _ = self.model.transcribe(audio_path, language="en")
        return " ".join([segment.text for segment in segments])
        
    def start_listening(self, vad_threshold: float = 0.5):
        """
        Keeps mic open, converts audio to text, pipes to NLP compiler.
        """
        self.is_listening = True
        
        def audio_callback(in_data, frame_count, time_info, status):
            audio_np = np.frombuffer(in_data, dtype=np.int16).astype(np.float32) / 32768.0
            self.audio_queue.put(audio_np)
            return (in_data, pyaudio.paContinue)
        
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024,
            stream_callback=audio_callback
        )
        
        stream.start_stream()
        print("[VOICE] 🎤 Listening... (Ctrl+C to stop)")
        
        try:
            buffer = []
            silence_counter = 0
            
            while self.is_listening:
                try:
                    audio_chunk = self.audio_queue.get(timeout=0.1)
                    buffer.append(audio_chunk)
                    
                    # Simple VAD: check audio energy
                    energy = np.mean(np.abs(audio_chunk))
                    if energy > vad_threshold:
                        silence_counter = 0
                    else:
                        silence_counter += 1
                    
                    # Process when we have enough audio or silence detected
                    if (len(buffer) * 1024 / 16000 > 3) or (silence_counter > 50 and len(buffer) > 0):
                        audio_combined = np.concatenate(buffer)
                        
                        try:
                            segments, _ = self.model.transcribe(audio_combined, language="en")
                            text = " ".join([segment.text for segment in segments]).strip()
                            
                            if text:
                                print(f"[VOICE] 🗣  {text}")
                                
                                # Use callback if set, otherwise pipe to NLP compiler
                                if self.transcription_callback:
                                    self.transcription_callback(text)
                                else:
                                    # Default: pipe to NLP compiler
                                    app = compile_and_spawn(text)
                                    asyncio.run(app.run())
                        except Exception as e:
                            print(f"[VOICE] Transcription error: {e}")
                        
                        buffer = []
                        silence_counter = 0
                        
                except queue.Empty:
                    continue
                    
        except KeyboardInterrupt:
            print("\n[VOICE] ⏹  Stopped listening")
        finally:
            self.is_listening = False
            stream.stop_stream()
            stream.close()
            p.terminate()
    
    def stop_listening(self):
        """Stop the listening loop."""
        self.is_listening = False

class VisionRouter:
    """
    Vision Router for image-to-text processing using local Vision models.
    Supports LLaVA, CogVLG, and other multimodal models.
    """
    
    def __init__(self, model_endpoint: str = "http://localhost:7860/api/predict"):
        self.model_endpoint = model_endpoint
        self.default_prompt = "Describe this image in detail. What do you see?"
        
    def observe(self, image_path: str, prompt: Optional[str] = None) -> str:
        """
        Takes image file path, sends to local Vision model, returns description.
        
        Args:
            image_path: Path to image file
            prompt: Custom prompt for vision model (optional)
            
        Returns:
            Detailed description of the image
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
            
        # Read and encode image
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        # Use custom prompt or default
        vision_prompt = prompt or self.default_prompt
        
        try:
            # Try LLaVA-style API first
            response = requests.post(
                self.model_endpoint,
                json={
                    "data": [image_data, vision_prompt],
                    "fn_index": 0  # Common for Gradio APIs
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if "data" in result and result["data"]:
                    return result["data"][0]
                elif "output" in result:
                    return result["output"]
                else:
                    return str(result)
            else:
                raise requests.RequestException(f"HTTP {response.status_code}")
                
        except Exception as e:
            # Fallback: try OpenAI-compatible API
            try:
                response = requests.post(
                    self.model_endpoint.replace("/api/predict", "/v1/chat/completions"),
                    json={
                        "model": "llava",
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": vision_prompt},
                                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                                ]
                            }
                        ],
                        "max_tokens": 500
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    raise requests.RequestException(f"HTTP {response.status_code}")
                    
            except Exception as fallback_error:
                raise RuntimeError(f"Vision model unavailable: {e}, fallback failed: {fallback_error}")
    
    def inject_into_dag(self, image_path: str, prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Process image and inject description into DAG state.
        
        Returns:
            Dict with vision data ready for NLP compiler
        """
        description = self.observe(image_path, prompt)
        
        return {
            "type": "vision_input",
            "image_path": image_path,
            "description": description,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "prompt_used": prompt or self.default_prompt
        }


# Tool registration for multimodal capabilities
@tool
def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio file to text using Faster-Whisper.
    
    Args:
        audio_path: Path to audio file (wav, mp3, etc.)
    """
    handler = VoiceHandler()
    return handler.transcribe_audio_file(audio_path)


@tool  
def analyze_image(image_path: str, prompt: str = "Describe this image in detail.") -> str:
    """Analyze image using local vision model.
    
    Args:
        image_path: Path to image file
        prompt: Custom prompt for analysis (optional)
    """
    router = VisionRouter()
    return router.observe(image_path, prompt)


@tool
def start_voice_listening(model_size: str = "base", device: str = "cpu") -> str:
    """Start continuous voice listening mode.
    
    Args:
        model_size: Whisper model size (tiny, base, small, medium, large)
        device: Device to use (cpu, cuda)
    """
    handler = VoiceHandler(model_size=model_size, device=device)
    
    def voice_callback(text: str):
        """Handle transcribed voice input."""
        print(f"[VOICE_CALLBACK] Processing: {text}")
        # This would integrate with the DAG state
        return text
    
    handler.set_callback(voice_callback)
    
    # Start listening in background thread
    import threading
    thread = threading.Thread(target=handler.start_listening)
    thread.daemon = True
    thread.start()
    
    return f"Voice listening started with {model_size} model on {device}"
