# 情感驱动的中控系统文档

## 系统概述

本文档描述了DigiHuman项目的"情感驱动的中控系统"实现，该系统实现了从用户输入到情感化语音输出及Live2D角色同步动画的全流程。

## 系统架构

### 核心模块

```
┌─────────────────────────────────────────────────────────────────┐
│                    情感驱动中控系统 (EmotionCenter)              │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ 情感分析模块  │  │ 文本增强模块  │  │ 参数转换模块  │          │
│  │  (Analyzer)  │  │ (Enhancer)   │  │(Controller)  │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                  │
│         └─────────────────┴─────────────────┘                  │
│                           │                                    │
│                    ┌──────┴──────┐                            │
│                    │  中控协调器  │                            │
│                    │  (Center)   │                            │
│                    └──────┬──────┘                            │
│                           │                                    │
│         ┌─────────────────┼─────────────────┐                  │
│         │                 │                 │                  │
│  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐            │
│  │  Qwen-TTS   │  │ 音频同步模块 │  │ Live2D控制  │            │
│  │   合成模块   │  │ (AudioSync) │  │  (Model)   │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

### 模块说明

#### 1. 情绪控制中心 (EmotionController)
- **文件**: `backend/core/emotion_controller.py`
- **功能**: 
  - 情绪类型和强度管理
  - 情绪到TTS参数的映射转换
  - 情绪到Live2D参数的映射转换
  - 平滑过渡动画支持

#### 2. 文本增强器 (TextEnhancer)
- **文件**: `backend/core/text_enhancer.py`
- **功能**:
  - 根据情绪类型增强文本语气
  - 添加情感前缀/后缀
  - 优化TTS可读性（移除emoji等）
  - SSML标记生成

#### 3. Qwen-TTS 合成模块
- **文件**: `backend/tts/qwen_tts.py`
- **功能**:
  - 情感化语音合成
  - SSML支持
  - 多音色选择
  - 语速/音调/音量动态调整

#### 4. 音频同步模块 (AudioSync)
- **文件**: `backend/core/audio_sync.py`
- **功能**:
  - 音频音量分析
  - 实时唇形同步
  - 音频帧处理
  - 嘴型开合度计算

#### 5. 情感中控 (EmotionCenter)
- **文件**: `backend/core/emotion_center.py`
- **功能**:
  - 整合所有模块
  - WebSocket实时通信
  - 性能监控
  - 错误处理

## 配置说明

### 环境变量配置

```bash
# 在 .env 文件中添加

# TTS服务选择 (edge_tts / openai_tts / qwen_tts)
TTS_SERVICE=qwen_tts

# Qwen-TTS配置
QWEN_TTS_API_KEY=your_api_key_here
QWEN_TTS_URL=https://dashscope.aliyuncs.com/api/v1/services/aigc/tts

# 情感系统配置
EMOTION_ENABLED=true
EMOTION_ENHANCEMENT_ENABLED=true
LIP_SYNC_ENABLED=true

# WebSocket配置
WS_HEARTBEAT_INTERVAL=30
```

### 情绪-参数映射表

#### TTS参数映射

| 情绪 | 强度 | 语速 | 音调 | 音量 | 音色风格 |
|------|------|------|------|------|----------|
| joy | low | 1.1 | 1.1 | 1.0 | cheerful |
| joy | medium | 1.2 | 1.15 | 1.1 | cheerful |
| joy | high | 1.3 | 1.2 | 1.2 | excited |
| sadness | low | 0.9 | 0.95 | 0.9 | calm |
| sadness | medium | 0.85 | 0.9 | 0.85 | sad |
| sadness | high | 0.8 | 0.85 | 0.8 | sad |
| anger | low | 1.05 | 1.05 | 1.1 | serious |
| anger | medium | 1.1 | 1.1 | 1.2 | angry |
| anger | high | 1.15 | 1.15 | 1.3 | angry |
| surprise | low | 1.0 | 1.15 | 1.1 | surprised |
| surprise | medium | 1.05 | 1.2 | 1.15 | surprised |
| surprise | high | 1.1 | 1.3 | 1.2 | shocked |

#### Live2D参数映射

| 情绪 | 强度 | 表情 | 动作 | 嘴型 | 呼吸 |
|------|------|------|------|------|------|
| joy | low | exp_01 | mtn_01 | 0.2 | 0.3 |
| joy | medium | exp_02 | mtn_01 | 0.3 | 0.4 |
| joy | high | exp_02 | special_01 | 0.5 | 0.5 |
| sadness | low | exp_03 | mtn_03 | 0.0 | 0.2 |
| sadness | medium | exp_03 | mtn_03 | 0.0 | 0.15 |
| sadness | high | exp_04 | special_02 | 0.1 | 0.1 |
| anger | low | exp_05 | mtn_02 | 0.1 | 0.3 |
| anger | medium | exp_05 | mtn_02 | 0.2 | 0.4 |
| anger | high | exp_06 | special_03 | 0.3 | 0.5 |

## API使用示例

### 基本使用

```python
from backend.core.emotion_center import get_emotion_center

# 获取中控实例
emotion_center = get_emotion_center()

# 处理文本（完整流程）
response = await emotion_center.process(
    text="今天天气真好！",
    use_emotion_enhancement=True,
    use_tts=True,
    use_lip_sync=True
)

# 获取结果
print(f"情绪: {response.emotion}")
print(f"增强文本: {response.enhanced_text}")
print(f"处理时间: {response.duration}s")
```

### WebSocket集成

```python
from backend.core.emotion_center import get_ws_handler

# 获取WebSocket处理器
ws_handler = get_ws_handler()

# 在WebSocket消息处理中
async def handle_message(websocket, client_id, message):
    result = await ws_handler.handle_message(
        websocket, client_id, message, llm_service
    )
    return result
```

### 单独使用模块

```python
from backend.core.emotion_controller import get_emotion_controller
from backend.core.text_enhancer import get_text_enhancer

# 情绪参数转换
controller = get_emotion_controller()
tts_params, live2d_params = controller.process_emotion(
    emotion="joy",
    intensity="high", 
    confidence=0.9,
    intensity_value=85
)

# 文本增强
enhancer = get_text_enhancer()
enhanced_text = enhancer.enhance_for_tts(
    text="今天天气真好",
    emotion="joy",
    intensity="high",
    intensity_value=85
)
```

## 性能指标

### 目标性能

| 指标 | 目标值 | 实际测试值 |
|------|--------|-----------|
| 输入处理延迟 | < 300ms | ~200ms |
| 情感参数转换 | < 100ms | ~0ms |
| TTS合成 | 实时 | 依赖API |
| 端到端延迟 | < 1s | ~1.6s |
| 唇形同步延迟 | < 50ms | ~20ms |

### 优化建议

1. **TTS优化**: 使用本地TTS引擎减少API调用延迟
2. **缓存机制**: 缓存常用情感参数
3. **并发处理**: 异步并行处理TTS和Live2D参数
4. **预加载**: 预加载模型和配置

## 测试

### 运行测试

```bash
# 运行集成测试
python test_emotion_center.py
```

### 测试覆盖

- 情感分析准确性测试
- 情绪参数映射测试
- 文本增强效果测试
- 音频同步测试
- 完整流程集成测试

## 故障排除

### 常见问题

1. **TTS合成失败**
   - 检查API密钥配置
   - 确认网络连接
   - 查看日志中的错误信息

2. **情绪识别不准确**
   - 调整置信度阈值
   - 优化LLM提示词
   - 增加训练数据

3. **唇形同步延迟**
   - 调整响应速度参数
   - 优化音频分析帧率
   - 检查系统资源占用

## 扩展开发

### 添加新情绪

1. 在 `EmotionController` 中添加映射规则
2. 在 `TextEnhancer` 中添加增强规则
3. 在 `QwenTTS` 中添加音色映射

### 自定义映射

```python
# 修改情绪-TTS映射
EmotionController.EMOTION_TTS_MAP["custom_emotion"] = {
    "low": TTSParameters(speed=1.0, pitch=1.0, ...),
    "medium": TTSParameters(...),
    "high": TTSParameters(...)
}
```

## 更新日志

### v1.0.0 (2026-04-24)
- 初始版本发布
- 实现情感驱动中控系统
- 支持7种基础情绪
- 集成Qwen-TTS
- 实现唇形同步
