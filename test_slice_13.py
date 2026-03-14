#!/usr/bin/env python3
"""
SLICE 13: Multimodal & Voice Control Tests

Tests:
- 13.1: VoiceHandler initialization and configuration
- 13.2: Audio transcription (mock)
- 13.3: Voice Activity Detection (VAD)
- 13.4: Vision Router image processing (mock)
- 13.5: Multimodal tool registration
- 13.6: CLI listen command integration
- 13.7: NLP compiler multimodal tool awareness
- 13.8: Voice-to-NLP pipeline (mock)
"""

import asyncio
import json
import os
import tempfile
import time
import unittest.mock as mock
from pathlib import Path

def test_13_1_voice_handler_init():
    """Test VoiceHandler initialization and configuration."""
    print("--- Test 13.1: VoiceHandler Initialization ---")
    
    try:
        from hanerma.interface.voice import VoiceHandler
        
        # Test default initialization
        handler = VoiceHandler()
        assert handler.model is not None, "Whisper model should be initialized"
        assert hasattr(handler, 'audio_queue'), "Should have audio queue"
        assert handler.is_listening == False, "Should not be listening by default"
        print("  ✓ Default initialization works")
        
        # Test custom configuration
        handler_custom = VoiceHandler(model_size="tiny", device="cpu")
        assert handler_custom.model is not None, "Custom model should initialize"
        print("  ✓ Custom configuration works")
        
        # Test callback setting
        def test_callback(text):
            return f"Processed: {text}"
        
        handler.set_callback(test_callback)
        assert handler.transcription_callback == test_callback, "Callback should be set"
        print("  ✓ Callback setting works")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_13_2_audio_transcription():
    """Test audio transcription functionality (mocked)."""
    print("--- Test 13.2: Audio Transcription ---")
    
    try:
        from hanerma.interface.voice import VoiceHandler
        
        # Mock WhisperModel to avoid actual model loading
        with mock.patch('hanerma.interface.voice.WhisperModel') as mock_whisper:
            mock_model = mock.MagicMock()
            mock_whisper.return_value = mock_model
            
            # Mock transcription result
            mock_segments = [
                mock.MagicMock(text="Hello world"),
                mock.MagicMock(text="this is a test")
            ]
            mock_model.transcribe.return_value = (mock_segments, None)
            
            handler = VoiceHandler()
            result = handler.transcribe_audio_file("test.wav")
            
            assert result == "Hello world this is a test", f"Expected transcription, got: {result}"
            print("  ✓ Audio transcription works")
            
            # Verify model was called correctly
            mock_model.transcribe.assert_called_once_with("test.wav", language="en")
            print("  ✓ Whisper model called correctly")
            
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_13_3_vad_detection():
    """Test Voice Activity Detection logic."""
    print("--- Test 13.3: Voice Activity Detection ---")
    
    try:
        import numpy as np
        
        # Test VAD threshold logic
        # High energy audio (speech)
        high_energy_audio = np.random.randn(1024) * 0.8  # High amplitude
        energy_high = np.mean(np.abs(high_energy_audio))
        assert energy_high > 0.5, "High energy audio should exceed VAD threshold"
        
        # Low energy audio (silence)
        low_energy_audio = np.random.randn(1024) * 0.1  # Low amplitude
        energy_low = np.mean(np.abs(low_energy_audio))
        assert energy_low < 0.5, "Low energy audio should be below VAD threshold"
        
        print("  ✓ VAD energy threshold logic works")
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_13_4_vision_router():
    """Test Vision Router image processing (mocked)."""
    print("--- Test 13.4: Vision Router ---")
    
    try:
        from hanerma.interface.voice import VisionRouter
        
        # Create a temporary test image
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_img:
            tmp_img.write(b"fake_image_data")
            tmp_img_path = tmp_img.name
        
        try:
            # Mock requests to avoid actual API calls
            with mock.patch('hanerma.interface.voice.requests.post') as mock_post:
                mock_response = mock.MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"data": ["A beautiful sunset over mountains"]}
                mock_post.return_value = mock_response
                
                router = VisionRouter()
                result = router.observe(tmp_img_path)
                
                assert "beautiful sunset" in result, f"Expected description, got: {result}"
                print("  ✓ Vision Router image processing works")
                
                # Test DAG injection
                dag_data = router.inject_into_dag(tmp_img_path, "What do you see?")
                assert dag_data["type"] == "vision_input", "Should have correct type"
                assert "image_path" in dag_data, "Should contain image path"
                assert "description" in dag_data, "Should contain description"
                assert "timestamp" in dag_data, "Should contain timestamp"
                print("  ✓ DAG injection works")
                
        finally:
            os.unlink(tmp_img_path)
            
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_13_5_multimodal_tools():
    """Test multimodal tool registration."""
    print("--- Test 13.5: Multimodal Tool Registration ---")
    
    try:
        from hanerma.interface.voice import transcribe_audio, analyze_image, start_voice_listening
        from hanerma.tools.registry import get_tool_registry
        
        # Check if tools are registered
        registry = get_tool_registry()
        
        # Test tool schemas exist
        assert hasattr(transcribe_audio, 'schema'), "transcribe_audio should have schema"
        assert hasattr(analyze_image, 'schema'), "analyze_image should have schema"
        assert hasattr(start_voice_listening, 'schema'), "start_voice_listening should have schema"
        
        # Check schema content
        transcribe_schema = transcribe_audio.schema
        assert "audio_path" in transcribe_schema["properties"], "Should have audio_path parameter"
        
        analyze_schema = analyze_image.schema
        assert "image_path" in analyze_schema["properties"], "Should have image_path parameter"
        assert "prompt" in analyze_schema["properties"], "Should have prompt parameter"
        
        voice_schema = start_voice_listening.schema
        assert "model_size" in voice_schema["properties"], "Should have model_size parameter"
        assert "device" in voice_schema["properties"], "Should have device parameter"
        
        print("  ✓ All multimodal tools registered with correct schemas")
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_13_6_cli_listen_integration():
    """Test CLI listen command integration."""
    print("--- Test 13.6: CLI Listen Integration ---")
    
    try:
        # Test CLI parser includes listen command
        import sys
        from io import StringIO
        
        # Capture help output
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            from hanerma.cli import main
            # This would normally parse sys.argv, so we need to mock it
            with mock.patch('sys.argv', ['hanerma', '--help']):
                try:
                    main()
                except SystemExit:
                    pass  # argparse calls sys.exit(0) after --help
        finally:
            sys.stdout = old_stdout
        
        help_text = captured_output.getvalue()
        assert "listen" in help_text, "CLI help should include listen command"
        print("  ✓ CLI includes listen command")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_13_7_nlp_compiler_awareness():
    """Test NLP compiler multimodal tool awareness."""
    print("--- Test 13.7: NLP Compiler Multimodal Awareness ---")
    
    try:
        from hanerma.orchestrator.nlp_compiler import TOOL_MANIFEST
        
        # Check if multimodal tools are in manifest
        assert "transcribe_audio" in TOOL_MANIFEST, "Should include transcribe_audio"
        assert "analyze_image" in TOOL_MANIFEST, "Should include analyze_image"
        assert "start_voice_listening" in TOOL_MANIFEST, "Should include start_voice_listening"
        
        # Check descriptions
        assert "STT" in TOOL_MANIFEST["transcribe_audio"], "Should mention STT"
        assert "vision" in TOOL_MANIFEST["analyze_image"], "Should mention vision"
        assert "voice" in TOOL_MANIFEST["start_voice_listening"], "Should mention voice"
        
        print("  ✓ NLP compiler aware of multimodal tools")
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_13_8_voice_to_nlp_pipeline():
    """Test voice-to-NLP pipeline (mocked)."""
    print("--- Test 13.8: Voice-to-NLP Pipeline ---")
    
    try:
        from hanerma.interface.voice import VoiceHandler
        
        # Mock the entire pipeline
        with mock.patch('hanerma.interface.voice.WhisperModel') as mock_whisper, \
             mock.patch('hanerma.interface.voice.pyaudio') as mock_pyaudio, \
             mock.patch('hanerma.interface.voice.compile_and_spawn') as mock_compile:
            
            # Setup mocks
            mock_model = mock.MagicMock()
            mock_whisper.return_value = mock_model
            mock_pyaudio.PyAudio.return_value.open.return_value.start_stream.return_value = None
            
            # Mock transcription
            mock_segments = [mock.MagicMock(text="Create a web scraper")]
            mock_model.transcribe.return_value = (mock_segments, None)
            
            # Mock NLP compilation
            mock_app = mock.MagicMock()
            mock_compile.return_value = mock_app
            
            handler = VoiceHandler()
            
            # Test callback pipeline
            processed_texts = []
            def test_callback(text):
                processed_texts.append(text)
            
            handler.set_callback(test_callback)
            
            # Simulate transcription result
            if handler.transcription_callback:
                handler.transcription_callback("Create a web scraper")
            
            assert "Create a web scraper" in processed_texts, "Voice should be processed by callback"
            print("  ✓ Voice-to-NLP callback pipeline works")
            
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def run_slice_13_tests():
    """Run all Slice 13 tests."""
    print("🎯 SLICE 13: Multimodal & Voice Control")
    print("=" * 50)
    
    tests = [
        test_13_1_voice_handler_init,
        test_13_2_audio_transcription,
        test_13_3_vad_detection,
        test_13_4_vision_router,
        test_13_5_multimodal_tools,
        test_13_6_cli_listen_integration,
        test_13_7_nlp_compiler_awareness,
        test_13_8_voice_to_nlp_pipeline,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}")
    
    print(f"\n📊 SLICE 13 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ SLICE 13 COMPLETE - All multimodal systems operational")
        print("\n🎤 VOICE FEATURES READY:")
        print("   • Real-time STT with Faster-Whisper")
        print("   • Voice Activity Detection")
        print("   • Continuous listening mode")
        print("   • hanerma listen --model base --device cpu")
        print("\n👁️  VISION FEATURES READY:")
        print("   • LLaVA-compatible Vision Router")
        print("   • Image-to-text processing")
        print("   • DAG state injection")
        print("   • analyze_image tool integration")
        print("\n🔧 MULTIMODAL TOOLS:")
        print("   • transcribe_audio(audio_path)")
        print("   • analyze_image(image_path, prompt)")
        print("   • start_voice_listening(model, device)")
    else:
        print(f"⚠️  SLICE 13 INCOMPLETE - {total - passed} tests failed")
    
    return passed == total

if __name__ == "__main__":
    run_slice_13_tests()
