# 情感驱动中控系统部署指南

## 系统要求

### 硬件要求
- **CPU**: 4核以上
- **内存**: 8GB以上
- **存储**: 10GB可用空间
- **网络**: 稳定的互联网连接

### 软件要求
- **Python**: 3.10+
- **Node.js**: 18+ (前端)
- **操作系统**: Windows 10/11, Linux, macOS

## 安装步骤

### 1. 克隆/准备代码

```bash
cd e:\big_work\DigiHuman
```

### 2. 安装Python依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装额外的情感系统依赖
pip install numpy aiohttp
```

### 3. 配置环境变量

创建或编辑 `.env` 文件：

```bash
# 应用配置
APP_NAME=DigiHuman
APP_VERSION=2.0.0
DEBUG=false

# API配置
HOST=0.0.0.0
PORT=8001

# LLM配置
LLM_MODEL_NAME=glm-4.6v-flash
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
LLM_API_KEY=your_key_here
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=512

# TTS配置 (关键配置)
TTS_SERVICE=qwen_tts  # 或 edge_tts
TTS_VOICE=zh-CN-XiaoxiaoNeural
TTS_MODEL=tts-1

# Qwen-TTS配置 (如需使用)
QWEN_TTS_API_KEY=your_qwen_key_here
QWEN_TTS_URL=https://dashscope.aliyuncs.com/api/v1/services/aigc/tts

# 情感系统配置
EMOTION_ENABLED=true
EMOTION_ENHANCEMENT_ENABLED=true
LIP_SYNC_ENABLED=true

# ASR配置
ASR_ENABLED=true
ASR_SERVICE=openai_whisper

# Live2D配置
LIVE2D_ENABLED=true
LIVE2D_MODEL_PATH=./models/live2d/character.model3.json

# WebSocket配置
WS_MAX_CONNECTIONS=100
WS_HEARTBEAT_INTERVAL=30
```

### 4. 前端配置

```bash
cd frontend

# 安装依赖
npm install

# 构建
npm run build
```

## 启动服务

### 开发模式

```bash
# 启动后端
python run_server.py

# 启动前端（新终端）
cd frontend
npm run dev
```

### 生产模式

```bash
# 使用启动脚本
python start_all.py
```

## 验证部署

### 1. 服务健康检查

```bash
# 检查后端API
curl http://localhost:8001/api/v1/health

# 检查WebSocket
# 使用浏览器访问前端页面，查看WebSocket连接状态
```

### 2. 功能测试

```bash
# 运行集成测试
python test_emotion_center.py
```

### 3. 手动测试

1. 打开浏览器访问 `http://localhost:3000`
2. 在对话框中输入测试文本：
   - "今天天气真好！"（测试joy情绪）
   - "我感到很伤心..."（测试sadness情绪）
   - "这太令人震惊了！"（测试surprise情绪）
3. 观察Live2D角色的表情和动作变化
4. 听取语音合成的情感表达

## 配置文件详解

### 情绪-参数映射配置

编辑 `backend/core/emotion_controller.py`：

```python
# 修改TTS参数映射
EMOTION_TTS_MAP = {
    "joy": {
        "low": TTSParameters(speed=1.1, pitch=1.1, volume=1.0, voice_style="cheerful"),
        "medium": TTSParameters(speed=1.2, pitch=1.15, volume=1.1, voice_style="cheerful"),
        "high": TTSParameters(speed=1.3, pitch=1.2, volume=1.2, voice_style="excited")
    },
    # ... 其他情绪
}

# 修改Live2D参数映射
EMOTION_LIVE2D_MAP = {
    "joy": {
        "low": Live2DParameters(expression="exp_01", motion="mtn_01", mouth_open=0.2),
        "medium": Live2DParameters(expression="exp_02", motion="mtn_01", mouth_open=0.3),
        "high": Live2DParameters(expression="exp_02", motion="special_01", mouth_open=0.5)
    },
    # ... 其他情绪
}
```

### 文本增强规则配置

编辑 `backend/core/text_enhancer.py`：

```python
# 添加自定义增强规则
EMOTION_ENHANCEMENT_RULES = {
    "joy": {
        "high": {
            "prefixes": ["太棒了！", "哇！", "好开心啊，"],
            "suffixes": ["！", "哈哈！", "🎉"],
            "intensifiers": ["超级", "非常", "特别"]
        }
    }
}
```

## 性能优化

### 1. 启用缓存

```python
# 在 emotion_controller.py 中
class EmotionController:
    def __init__(self):
        self._cache = {}  # 添加缓存
    
    def process_emotion(self, emotion, intensity, confidence, intensity_value):
        cache_key = f"{emotion}_{intensity}_{intensity_value}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # ... 处理逻辑
        
        self._cache[cache_key] = (tts_params, live2d_params)
        return tts_params, live2d_params
```

### 2. 异步优化

```python
# 并行处理TTS和参数转换
async def process(self, text, ...):
    # 并行执行
    tts_task = asyncio.create_task(self._synthesize_tts(text))
    emotion_task = asyncio.create_task(self._analyze_emotion(text))
    
    audio_data, emotion_result = await asyncio.gather(tts_task, emotion_task)
```

### 3. 资源预加载

```python
# 在应用启动时预加载
@app.on_event("startup")
async def startup_event():
    # 预加载TTS服务
    get_tts_service()
    # 预加载情感分析器
    get_emotion_analyzer()
    # 预加载控制器
    get_emotion_controller()
```

## 监控与日志

### 日志配置

```python
# 在配置文件中
LOG_LEVEL=INFO
LOG_FILE=logs/emotion_system.log
```

### 性能监控

```python
# 获取性能指标
from backend.core.emotion_center import get_emotion_center

center = get_emotion_center()
metrics = center.get_metrics()

print(f"总请求数: {metrics['total_requests']}")
print(f"平均处理时间: {metrics['avg_processing_time']*1000:.2f}ms")
```

## 故障排除

### 问题1: Qwen-TTS API调用失败

**症状**: TTS合成失败，返回错误

**解决方案**:
1. 检查API密钥是否正确配置
2. 确认网络连接正常
3. 检查API配额是否已用完
4. 切换到备用TTS服务（Edge TTS）

```bash
# 切换到Edge TTS
export TTS_SERVICE=edge_tts
```

### 问题2: 情绪识别不准确

**症状**: 情绪检测结果与预期不符

**解决方案**:
1. 调整置信度阈值
2. 优化LLM提示词
3. 增加上下文信息

```python
# 在 emotion_analyzer.py 中调整
class LangChainEmotionAnalyzer:
    def __init__(self):
        self.min_confidence = 0.3  # 调整此值
```

### 问题3: 唇形同步延迟

**症状**: 嘴型动画与语音不同步

**解决方案**:
1. 调整响应速度参数
2. 降低音频分析精度
3. 优化WebSocket传输

```python
# 在 audio_sync.py 中调整
lip_sync_engine = LipSyncEngine(
    response_speed=0.5  # 增加响应速度
)
```

### 问题4: 内存占用过高

**症状**: 系统运行一段时间后内存不足

**解决方案**:
1. 限制历史记录大小
2. 定期清理缓存
3. 使用流式处理

```python
# 限制历史记录
class EmotionController:
    max_history_size = 20  # 减少历史记录
```

## 更新与维护

### 更新步骤

1. 备份配置文件
2. 拉取最新代码
3. 更新依赖
4. 重启服务

```bash
# 备份
 cp .env .env.backup

# 更新代码
 git pull

# 更新依赖
 pip install -r requirements.txt --upgrade

# 重启服务
 python start_all.py
```

### 备份策略

定期备份以下内容：
- 配置文件 (.env)
- 聊天记录 (chat_history/)
- 记忆数据 (chat_memory/)

```bash
# 备份脚本
#!/bin/bash
BACKUP_DIR="backup/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

cp .env $BACKUP_DIR/
cp -r chat_history $BACKUP_DIR/
cp -r chat_memory $BACKUP_DIR/

echo "Backup completed: $BACKUP_DIR"
```

## 安全建议

1. **API密钥保护**
   - 不要将API密钥提交到版本控制
   - 使用环境变量或密钥管理服务

2. **输入验证**
   - 对所有用户输入进行验证
   - 防止注入攻击

3. **访问控制**
   - 限制WebSocket连接数
   - 实现用户认证

## 支持与联系

如有问题，请：
1. 查看日志文件
2. 运行测试脚本
3. 检查配置是否正确
4. 参考系统文档
