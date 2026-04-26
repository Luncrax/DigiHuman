# Qwen3-TTS 语音模块集成文档

## 概述

本文档描述了基于Qwen3-TTS官方文档实现的语音模块，用于适配DigiHuman项目的对话功能。该模块支持本地模型加载、音色文件应用以及情绪识别驱动的语音合成。

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    情绪感知TTS服务层                              │
│              (EmotionAwareTTSService)                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  情绪分析模块  │  │  文本增强模块  │  │  语音合成模块  │          │
│  │  (Analyzer)  │  │ (Enhancer)   │  │ (Synthesis)  │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                  │
│         └─────────────────┴─────────────────┘                  │
│                           │                                    │
│                    ┌──────┴──────┐                            │
│                    │  Qwen3-TTS  │                            │
│                    │   Adapter   │                            │
│                    └──────┬──────┘                            │
│                           │                                    │
│              ┌────────────┼────────────┐                       │
│              │            │            │                       │
│       ┌──────┴──┐  ┌──────┴──┐  ┌──────┴──┐                   │
│       │Custom   │  │  Base   │  │ Voice   │                   │
│       │Voice    │  │  Model  │  │ Clone   │                   │
│       └─────────┘  └─────────┘  └─────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

## 核心模块

### 1. Qwen3-TTS 适配器 (qwen3_tts_adapter.py)

**文件**: `backend/tts/qwen3_tts_adapter.py`

**功能**:
- 集成本地Qwen3-TTS模型 (E:\big_work\Qwen3-TTS-main)
- 支持两种模型模式:
  - **CustomVoice模式**: 使用预定义音色，支持指令控制
  - **Base模式**: 支持声音克隆，可加载.pt音色文件
- 情绪到语音语气的映射

**主要方法**:
```python
# 创建适配器
adapter = create_qwen3_tts_adapter(
    model_type="custom_voice",  # 或 "base"
    voice_pt_path="path/to/voice.pt"  # 仅base模式
)

# 加载模型
adapter.load_model()

# 设置音色 (CustomVoice)
adapter.set_speaker("Vivian")

# 加载音色文件 (Base)
adapter.load_voice("voice_prompt.pt")

# 情绪感知合成
audio = adapter.generate_with_emotion(
    text="今天天气真好！",
    emotion="joy",
    intensity="high",
    language="Chinese"
)
```

**情绪-语气映射表**:

| 情绪 | 低强度 | 中强度 | 高强度 |
|------|--------|--------|--------|
| joy | 温和愉快 | 开心兴奋 | 非常激动高兴 |
| sadness | 略带忧伤 | 悲伤 | 非常悲伤难过 |
| anger | 严肃 | 生气 | 非常愤怒 |
| surprise | 略带惊讶 | 吃惊 | 非常震惊 |
| fear | 略带紧张 | 害怕 | 恐惧 |
| disgust | 不太满意 | 厌恶 | 非常反感恶心 |
| neutral | 平静 | 自然 | 清晰 |

### 2. 情绪感知TTS服务 (emotion_aware_tts.py)

**文件**: `backend/tts/emotion_aware_tts.py`

**功能**:
- 整合情绪识别与语音合成
- 自动检测文本情绪
- 文本增强（根据情绪添加语气词和标点）
- 支持声音克隆

**主要方法**:
```python
# 创建服务
service = EmotionAwareTTSService()

# 初始化模型
await service.initialize(model_type="custom_voice")

# 合成语音（自动检测情绪）
result = await service.synthesize(
    text="今天真是美好的一天！",
    use_text_enhancement=True
)

# 合成结果
print(f"检测到的情绪: {result.emotion}")
print(f"情绪强度: {result.intensity}")
print(f"增强后的文本: {result.enhanced_text}")
print(f"处理时间: {result.processing_time}s")

# 使用指定情绪
result = await service.synthesize(
    text="你好",
    emotion="joy",
    intensity="high"
)

# 声音克隆合成
result = await service.synthesize_with_voice_clone(
    text="这是克隆的声音",
    ref_audio_path="reference.wav",
    ref_text="参考文本内容",
    emotion="neutral"
)
```

## 配置使用

### 环境变量配置

在 `.env` 文件中添加:

```bash
# TTS服务选择
TTS_SERVICE=qwen3_tts  # 或 emotion_aware

# Qwen3-TTS配置 (可选，使用本地模型时不需要)
QWEN_TTS_API_KEY=your_api_key_here

# 模型路径配置 (可选，使用默认路径)
QWEN3_MODEL_PATH=E:\big_work\Qwen3-TTS-main\models\Qwen3-TTS-12Hz-1.7B-CustomVoice
```

### 在对话系统中使用

```python
from backend.tts import get_tts_service_by_config
from backend.tts.emotion_aware_tts import EmotionAwareTTSService

# 获取TTS服务
tts_service = get_tts_service_by_config()

# 如果是情绪感知服务，可以获取详细信息
if isinstance(tts_service, EmotionAwareTTSService):
    result = await tts_service.synthesize(
        text="用户的输入文本",
        use_text_enhancement=True
    )
    
    # 返回结果包含情绪信息
    return {
        "audio": result.audio_data,
        "emotion": result.emotion,
        "intensity": result.intensity,
        "enhanced_text": result.enhanced_text
    }
```

## 音色文件使用

### 创建音色文件

使用Base模型从参考音频创建音色文件:

```python
from backend.tts.qwen3_tts_adapter import create_qwen3_tts_adapter

# 创建Base模型适配器
adapter = create_qwen3_tts_adapter(model_type="base")
adapter.load_model()

# 从参考音频创建音色提示
adapter.create_voice_clone_prompt(
    ref_audio_path="path/to/reference.wav",
    ref_text="参考音频对应的文本内容",
    output_path="voice_prompts/my_voice.pt"
)
```

### 加载并使用音色

```python
# 加载已保存的音色
adapter.load_voice("voice_prompts/my_voice.pt")

# 使用克隆的音色合成
audio = adapter.synthesize(
    text="使用克隆的音色说话",
    emotion="joy",
    intensity="medium"
)
```

## 支持的语言和音色

### CustomVoice支持的音色

默认支持6种预定义音色:
- **Vivian**: 女声
- **Ryan**: 男声
- **Emma**: 女声
- **Jack**: 男声
- **Alice**: 女声
- **Bob**: 男声

### 支持的语言

- 中文 (Chinese)
- 英文 (English)
- 日文 (Japanese)
- 韩文 (Korean)
- 德文 (German)
- 法文 (French)
- 俄文 (Russian)
- 葡萄牙文 (Portuguese)
- 西班牙文 (Spanish)
- 意大利文 (Italian)

## 性能优化

### 生成参数调优

```python
# 调整生成参数以获得更好效果
adapter.gen_kwargs = {
    "max_new_tokens": 2048,
    "do_sample": True,
    "top_k": 50,
    "top_p": 1.0,
    "temperature": 0.9,
    "repetition_penalty": 1.05,
}
```

### 流式生成支持

Qwen3-TTS支持流式生成，可实现低延迟实时合成:

```python
# 启用流式生成 (如果模型支持)
adapter.gen_kwargs["streaming"] = True
```

## 故障排除

### 问题1: 模型加载失败

**症状**: `Failed to load Qwen3-TTS model`

**解决方案**:
1. 检查模型路径是否正确
2. 确认已安装所有依赖: `pip install -r E:\big_work\Qwen3-TTS-main\requirements.txt`
3. 检查CUDA可用性（如果使用GPU）

### 问题2: 音色文件加载失败

**症状**: `Failed to load voice`

**解决方案**:
1. 确认使用的是Base模型（CustomVoice不支持.pt文件）
2. 检查.pt文件是否存在且格式正确
3. 参考音频文件应同时存在(.wav)

### 问题3: 情绪检测不准确

**症状**: 合成语音情绪与预期不符

**解决方案**:
1. 手动指定情绪参数
2. 调整情绪强度
3. 增强文本提示词

## API参考

### Qwen3TTSAdapter

#### 构造函数
```python
Qwen3TTSAdapter(
    model_path: Optional[str] = None,      # 模型路径
    voice_pt_path: Optional[str] = None,  # 音色文件路径
    device: Optional[str] = None,          # 设备 (cuda:0/cpu)
    use_custom_voice: bool = True          # 使用CustomVoice或Base
)
```

#### 主要方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `load_model()` | - | `bool` | 加载模型 |
| `set_speaker(speaker)` | `str` | `bool` | 设置音色 |
| `load_voice(path)` | `str` | `bool` | 加载音色文件 |
| `generate_with_emotion()` | text, emotion, intensity, language, speaker | `np.ndarray` | 生成音频 |
| `synthesize()` | 同上 | `bytes` | 合成WAV音频 |
| `async_synthesize()` | 同上 | `bytes` | 异步合成 |

### EmotionAwareTTSService

#### 主要方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `initialize()` | model_type, voice_pt_path | `bool` | 初始化服务 |
| `synthesize()` | text, emotion, intensity, ... | `EmotionTTSResult` | 合成语音 |
| `synthesize_with_voice_clone()` | text, ref_audio, ref_text, ... | `EmotionTTSResult` | 克隆合成 |
| `set_speaker()` | speaker | `bool` | 设置音色 |
| `health_check()` | - | `dict` | 健康检查 |

## 更新日志

### v1.0.0 (2026-04-24)
- 初始版本发布
- 集成Qwen3-TTS本地模型
- 支持CustomVoice和Base两种模式
- 实现情绪-语气映射
- 支持音色文件加载
- 整合情绪识别与语音合成
