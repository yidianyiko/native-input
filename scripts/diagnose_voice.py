#!/usr/bin/env python3
"""
Voice Service Diagnostic Tool
Helps diagnose voice recording issues by testing components individually
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.voice.voice_service_v2 import VoiceService, VoiceState
from src.services.voice.realtime_client_v2 import RealtimeClient
from src.utils.config import ConfigManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def test_audio_processor():
    """Test if audio processor is working"""
    logger.info("Testing Audio Processor...")
    
    try:
        from src.services.voice.audio_processor import AudioProcessor
        
        audio_processor = AudioProcessor()
        logger.info("Audio processor created successfully")
        
        # Try to get a few audio chunks
        chunks_received = 0
        for i in range(5):
            chunk = await audio_processor.get_audio_chunk()
            if chunk:
                chunks_received += 1
                logger.info(f"Received audio chunk {i+1}: {len(chunk)} bytes")
            else:
                logger.warning(f"No audio chunk received for attempt {i+1}")
            
            await asyncio.sleep(0.1)
        
        audio_processor.cleanup()
        
        if chunks_received > 0:
            logger.info(f"Audio processor test PASSED - received {chunks_received}/5 chunks")
            return True
        else:
            logger.error("Audio processor test FAILED - no chunks received")
            return False
            
    except Exception as e:
        logger.error(f"Audio processor test FAILED: {e}")
        return False


async def test_realtime_connection():
    """Test OpenAI Realtime API connection"""
    logger.info("Testing OpenAI Realtime API Connection...")
    
    try:
        # Load config to get API key
        config_manager = ConfigManager()
        config_manager.load_config()
        
        api_key = config_manager.get_secret('openai_api_key')
        if not api_key:
            logger.error("No OpenAI API key found")
            return False
        
        logger.info(f"Using API key: {api_key[:10]}...")
        
        # Test connection
        client = RealtimeClient(api_key)
        
        logger.info("Attempting to connect...")
        success = await client.connect()
        
        if not success:
            logger.error("Connection failed")
            return False
        
        logger.info("Connected successfully")
        
        # Test sending a small message
        try:
            await client.start_recording()
            logger.info("Start recording successful")
            
            # Send a small audio chunk (minimal test data)
            test_audio = b"\x00" * 1024  # Silent audio data for connection test
            await client.send_audio(test_audio)
            logger.info("Audio send successful")
            
            # Wait a bit
            await asyncio.sleep(1)
            
            # Check connection health
            if client.is_connection_healthy():
                logger.info("Connection still healthy after audio send")
            else:
                logger.warning("Connection unhealthy after audio send")
            
            # Try to stop
            transcript = await client.stop_recording()
            logger.info(f"Stop recording result: {transcript}")
            
        except Exception as e:
            logger.error(f"Error during recording test: {e}")
        
        # Disconnect
        await client.disconnect()
        logger.info("Disconnected successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Realtime connection test FAILED: {e}")
        return False


async def test_voice_service_integration():
    """Test full voice service integration"""
    logger.info("Testing Voice Service Integration...")
    
    try:
        # Create config manager
        config_manager = ConfigManager()
        config_manager.load_config()
        
        # Create voice service
        voice_service = VoiceService(config_manager)
        
        # Initialize
        logger.info("Initializing voice service...")
        success = await voice_service.initialize()
        if not success:
            logger.error("Voice service initialization failed")
            return False
        
        logger.info("Voice service initialized")
        
        # Start recording
        logger.info("Starting recording...")
        success = await voice_service.start_recording()
        if not success:
            logger.error("Failed to start recording")
            return False
        
        logger.info("Recording started")
        logger.info(f"State: {voice_service.state}")
        
        # Let it record for a few seconds
        logger.info("Recording for 3 seconds...")
        for i in range(30):  # 3 seconds at 0.1s intervals
            await asyncio.sleep(0.1)
            
            # Check connection health every second
            if i % 10 == 0:
                if voice_service.realtime_client and voice_service.realtime_client.is_connection_healthy():
                    logger.info(f"Connection healthy at {i/10:.1f}s")
                else:
                    logger.warning(f"Connection unhealthy at {i/10:.1f}s")
        
        # Stop recording
        logger.info("Stopping recording...")
        transcript = await voice_service.stop_recording()
        
        logger.info(f"Transcript: {transcript}")
        logger.info(f"Final state: {voice_service.state}")
        
        # Get stats
        stats = voice_service.get_stats()
        logger.info(f"Stats: {stats}")
        
        if voice_service.realtime_client:
            client_stats = voice_service.realtime_client.get_stats()
            logger.info(f"Client stats: {client_stats}")
        
        # Cleanup
        await voice_service.async_cleanup()
        
        return True
        
    except Exception as e:
        logger.error(f"Voice service integration test FAILED: {e}")
        return False


async def run_diagnostics():
    """Run all diagnostic tests"""
    logger.info("Voice Service Diagnostics")
    logger.info("=" * 50)
    
    tests = [
        ("Audio Processor", test_audio_processor),
        ("Realtime Connection", test_realtime_connection),
        ("Voice Service Integration", test_voice_service_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\nRunning: {test_name}")
        logger.info("-" * 30)
        
        try:
            result = await test_func()
            results.append((test_name, result))
            
            if result:
                logger.info(f"{test_name}: PASSED")
            else:
                logger.error(f"{test_name}: FAILED")
                
        except Exception as e:
            logger.error(f"{test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("DIAGNOSTIC SUMMARY")
    logger.info("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("All diagnostics passed!")
        logger.info("The voice service should be working correctly.")
    else:
        logger.error(f"{total - passed} diagnostics failed")
        logger.info("Check the logs above for specific issues.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_diagnostics())
    sys.exit(0 if success else 1)