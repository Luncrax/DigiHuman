"""
Qwen3-TTS Usage Examples
Demonstrates how to use the Qwen3-TTS module with emotion awareness
"""
import asyncio
import sys
sys.path.insert(0, 'e:\\big_work\\DigiHuman')


async def example_1_basic_synthesis():
    """Example 1: Basic emotion-aware synthesis"""
    print("=" * 60)
    print("Example 1: Basic Emotion-Aware Synthesis")
    print("=" * 60)
    
    from backend.tts.emotion_aware_tts import EmotionAwareTTSService
    
    # Create and initialize service
    service = EmotionAwareTTSService()
    await service.initialize(model_type="custom_voice")
    
    # Synthesize with automatic emotion detection
    result = await service.synthesize(
        text="今天真是一个美好的日子！",
        use_text_enhancement=True
    )
    
    print(f"Detected emotion: {result.emotion}")
    print(f"Intensity: {result.intensity}")
    print(f"Enhanced text: {result.enhanced_text}")
    print(f"Audio size: {len(result.audio_data)} bytes")
    
    # Save audio to file
    with open("output_joy.wav", "wb") as f:
        f.write(result.audio_data)
    print("Audio saved to output_joy.wav")


async def example_2_specify_emotion():
    """Example 2: Specify emotion explicitly"""
    print("\n" + "=" * 60)
    print("Example 2: Specify Emotion Explicitly")
    print("=" * 60)
    
    from backend.tts.emotion_aware_tts import EmotionAwareTTSService
    
    service = EmotionAwareTTSService()
    await service.initialize(model_type="custom_voice")
    
    # Synthesize with specific emotion
    result = await service.synthesize(
        text="我很伤心...",
        emotion="sadness",
        intensity="high",
        use_text_enhancement=True
    )
    
    print(f"Emotion: {result.emotion}")
    print(f"Enhanced text: {result.enhanced_text}")
    
    with open("output_sadness.wav", "wb") as f:
        f.write(result.audio_data)
    print("Audio saved to output_sadness.wav")


async def example_3_change_speaker():
    """Example 3: Change speaker"""
    print("\n" + "=" * 60)
    print("Example 3: Change Speaker")
    print("=" * 60)
    
    from backend.tts.emotion_aware_tts import EmotionAwareTTSService
    
    service = EmotionAwareTTSService()
    await service.initialize(model_type="custom_voice")
    
    # Set different speakers
    speakers = ["Vivian", "Ryan", "Emma"]
    
    for speaker in speakers:
        service.set_speaker(speaker)
        result = await service.synthesize(
            text=f"你好，我是{speaker}",
            emotion="neutral",
            intensity="medium"
        )
        
        filename = f"output_{speaker.lower()}.wav"
        with open(filename, "wb") as f:
            f.write(result.audio_data)
        print(f"Speaker {speaker}: audio saved to {filename}")


async def example_4_voice_clone():
    """Example 4: Voice cloning"""
    print("\n" + "=" * 60)
    print("Example 4: Voice Cloning")
    print("=" * 60)
    
    from backend.tts.emotion_aware_tts import EmotionAwareTTSService
    
    service = EmotionAwareTTSService()
    
    # Note: This requires Base model and reference audio
    try:
        result = await service.synthesize_with_voice_clone(
            text="这是克隆的声音说话",
            ref_audio_path="path/to/reference.wav",
            ref_text="参考音频的文本内容",
            emotion="joy",
            intensity="medium"
        )
        
        with open("output_cloned.wav", "wb") as f:
            f.write(result.audio_data)
        print("Cloned voice audio saved to output_cloned.wav")
        
    except Exception as e:
        print(f"Voice cloning requires Base model and reference audio: {e}")


async def example_5_batch_synthesis():
    """Example 5: Batch synthesis with different emotions"""
    print("\n" + "=" * 60)
    print("Example 5: Batch Synthesis")
    print("=" * 60)
    
    from backend.tts.emotion_aware_tts import EmotionAwareTTSService
    
    service = EmotionAwareTTSService()
    await service.initialize(model_type="custom_voice")
    
    texts = [
        ("今天天气真好", "joy", "high"),
        ("我感到很失落", "sadness", "medium"),
        ("这太令人震惊了", "surprise", "high"),
        ("你做得很好", "joy", "medium"),
        ("我很生气", "anger", "high"),
    ]
    
    for i, (text, emotion, intensity) in enumerate(texts, 1):
        result = await service.synthesize(
            text=text,
            emotion=emotion,
            intensity=intensity
        )
        
        filename = f"output_{i}_{emotion}.wav"
        with open(filename, "wb") as f:
            f.write(result.audio_data)
        print(f"[{i}] {text} -> {emotion} ({intensity}): {filename}")


async def example_6_health_check():
    """Example 6: Health check"""
    print("\n" + "=" * 60)
    print("Example 6: Health Check")
    print("=" * 60)
    
    from backend.tts.emotion_aware_tts import EmotionAwareTTSService
    
    service = EmotionAwareTTSService()
    await service.initialize(model_type="custom_voice")
    
    health = await service.health_check()
    print("Health check results:")
    for key, value in health.items():
        print(f"  {key}: {value}")


async def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("Qwen3-TTS Usage Examples")
    print("=" * 60 + "\n")
    
    try:
        # Run examples (comment out ones you don't want to run)
        await example_1_basic_synthesis()
        await example_2_specify_emotion()
        await example_3_change_speaker()
        # await example_4_voice_clone()  # Requires reference audio
        await example_5_batch_synthesis()
        await example_6_health_check()
        
        print("\n" + "=" * 60)
        print("All examples completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
