# TTS 模型服务

本项目使用 **Fun-CosyVoice3-0.5B-2512** 模型提供语音合成服务。

## 模型信息

- **模型名称**: Fun-CosyVoice3-0.5B-2512
- **模型来源**: [ModelScope](https://modelscope.cn/models/FunAudioLLM/Fun-CosyVoice3-0.5B-2512)
- **开发商**: FunAudioLLM
- **功能**: 零样本语音克隆、多说话人语音合成

## 文件说明

| 文件 | 说明 |
|------|------|
| `server.py` | FastAPI 服务器，提供 TTS 推理接口 |
| `client.py` | 测试客户端，用于验证服务功能 |
| `update_docker.sh` | Docker 容器代码更新脚本 |
| `logs.sh` | Docker 容器日志查看脚本 |

## Docker 部署

### 1. 拉取官方镜像

```bash
# 从 ModelScope 官方仓库拉取镜像
docker pull registry.cn-beijing.aliyuncs.com/modelscope-repos/cosyvoice3:v1.0.0
```

### 2. 启动容器

```bash
docker run -d \
  --name cosyvoice3-tts \
  --restart unless-stopped \
  -p 50000:50000 \
  -v ~/.cache/modelscope:/root/.cache/modelscope \
  registry.cn-beijing.aliyuncs.com/modelscope-repos/cosyvoice3:v1.0.0
```

### 3. 更新代码（使用修改后的 server.py）

首次启动后，使用本项目的更新脚本替换容器中的代码：

```bash
# 方法 1: 使用自动更新脚本（推荐）
./update_docker.sh

# 方法 2: 手动复制
docker cp server.py cosyvoice3-tts:/app/server.py
docker restart cosyvoice3-tts
```

### 4. 查看日志

```bash
# 使用日志查看脚本
./logs.sh

# 或直接使用 docker 命令
docker logs -f cosyvoice3-tts
```

## API 接口

### 推理模式

| 模式 | 端点 | 说明 |
|------|------|------|
| `sft` | `/inference_sft` | 固定说话人合成 |
| `zero_shot` | `/inference_zero_shot` | 零样本语音克隆 |
| `cross_lingual` | `/inference_cross_lingual` | 跨语言合成 |
| `instruct` | `/inference_instruct` | 指令控制合成 |

### 零样本语音克隆 (zero_shot)

```python
import requests

url = "http://localhost:50000/inference_zero_shot"

payload = {
    "tts_text": "你好，我是语音合成助手",
    "prompt_text": "希望你以后能够做的比我还好呦"
}

files = {
    "prompt_wav": open("reference.wav", "rb")
}

response = requests.post(url, data=payload, files=files, stream=True)

# 保存音频
with open("output.wav", "wb") as f:
    for chunk in response.iter_content(chunk_size=4096):
        f.write(chunk)
```

## 流式响应格式

更新后的 `server.py` 支持增强的流式响应：

```
[4字节长度][JSON元数据]\n[音频数据]
```

### 元数据结构

```json
{
  "chunk_index": 0,           // 当前 chunk 索引
  "total_chunks": -1,         // 总 chunk 数（-1 表示流式生成中）
  "progress": -1,             // 进度百分比（-1 表示未知）
  "audio_size": 2205,         // 当前音频块大小（字节）
  "sub_chunk_index": 0,       // 子块索引
  "sub_chunk_total": 10,      // 总子块数
  "is_last_sub_chunk": false, // 是否为最后一个子块
  "time_to_first_chunk": 1.2  // 首块生成时间（秒）
}
```

### 特殊标记

| chunk_index | 说明 |
|-------------|------|
| -1 | 开始生成标记 |
| -2 | 初始化完成，开始生成音频 |
| >=0 | 音频数据块 |
| 最后一个 | is_final: true，表示生成完成 |

## 测试

### 使用测试客户端

```bash
python client.py \
  --mode zero_shot \
  --tts_text "你好，我是语音合成助手" \
  --prompt_text "希望你以后能够做的比我还好呦" \
  --prompt_wav reference.wav \
  --tts_wav output.wav
```

### 使用 curl

```bash
curl -X POST "http://localhost:50000/inference_zero_shot" \
  -F "tts_text=你好，我是语音合成助手" \
  -F "prompt_text=希望你以后能够做的比我还好呦" \
  -F "prompt_wav=@reference.wav" \
  -o output.wav
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MODEL_DIR` | FunAudioLLM/Fun-CosyVoice3-0.5B-2512 | ModelScope 模型 ID |
| `PORT` | 50000 | 服务端口 |

## 常用命令

```bash
# 查看容器状态
docker ps | grep cosyvoice

# 进入容器
docker exec -it cosyvoice3-tts bash

# 重启容器
docker restart cosyvoice3-tts

# 停止容器
docker stop cosyvoice3-tts

# 删除容器
docker rm -f cosyvoice3-tts
```

## 故障排查

### 问题 1: 模型下载缓慢

**解决方案**: 使用国内镜像源

```bash
export MODELSCOPE_CACHE=/path/to/local/cache
```

### 问题 2: 容器启动失败

**检查步骤**:

```bash
# 查看容器日志
docker logs cosyvoice3-tts

# 检查端口占用
netstat -an | grep 50000

# 检查磁盘空间
df -h
```

### 问题 3: 代码更新不生效

**解决方案**:

```bash
# 1. 确认文件已复制
docker exec cosyvoice3-tts cat /app/server.py | head -20

# 2. 重启容器
docker restart cosyvoice3-tts

# 3. 查看启动日志
docker logs -f cosyvoice3-tts
```

## 相关链接

- [ModelScope 模型页](https://modelscope.cn/models/FunAudioLLM/Fun-CosyVoice3-0.5B-2512)
- [CosyVoice GitHub](https://github.com/FunAudioLLM/CosyVoice)
- [项目主文档](../README.md)

## 更新日志

### 2026-02-10
- 添加流式响应进度信息
- 优化首块生成时间
- 添加子块分割支持
- 增加 Docker 代码更新脚本

---

**维护者**: 郭浩然
**最后更新**: 2026-02-10
