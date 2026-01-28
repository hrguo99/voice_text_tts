# Docker 镜像优化指南

## 已应用的优化技术

### 1. 多阶段构建优化
- 使用 `python:3.12-slim` 基础镜像（相比标准镜像小 5 倍）

### 2. 层级优化
- 合并 RUN 命令减少层数
- 先复制依赖文件，利用 Docker 缓存
- 后复制应用代码

### 3. 清理不必要文件
- 删除 Python 缓存文件 (`__pycache__`, `*.pyc`)
- 删除文档和示例文件 (`*.md`, `*.txt`)
- 删除编译工具（gcc, g++）安装后
- 清理 apt 缓存和 pip 缓存

### 4. 环境变量优化
- 使用 `PIP_NO_CACHE_DIR=1` 禁用 pip 缓存
- 使用 `PYTHONUNBUFFERED=1` 禁用 Python 输出缓冲
- 使用 `PYTHONDONTWRITEBYTECODE=1` 禁止生成 .pyc 文件

### 5. .dockerignore 优化
- 排除所有不必要的文件和目录
- 减少构建上下文大小

## 镜像大小对比

### 优化前
- 预计大小：~800MB - 1GB

### 优化后
- 预计大小：~400MB - 600MB
- **减小约 40-50%**

## 构建优化镜像

```bash
./build.sh
```

## 查看镜像大小

```bash
docker images voice-text-tts:latest
```

## 进一步优化（可选）

### 使用 Alpine Linux（更小，但可能有兼容性问题）

```dockerfile
FROM python:3.12-alpine
```

**注意**: Alpine 使用 musl libc 而不是 glibc，某些 Python 包可能不兼容。

### 使用 Upx 压缩二进制文件（高级）

```dockerfile
RUN apt-get install -y upx && \
    upx --best --lzma /usr/local/bin/python* && \
    apt-get remove -y upx
```

### 多阶段构建（如果需要编译 C 扩展）

```dockerfile
# 构建阶段
FROM python:3.12-slim as builder
RUN apt-get update && apt-get install -y gcc g++
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 运行阶段
FROM python:3.12-slim
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
```

## 验证优化效果

### 查看镜像层
```bash
docker history voice-text-tts:latest
```

### 查看镜像大小
```bash
docker images | grep voice-text-tts
```

### 分析镜像内容
```bash
docker run --rm -it --entrypoint /bin/sh voice-text-tts:latest du -sh /usr/*
```

## 性能影响

✅ **不影响功能**
- 所有功能保持完整
- 性能基本一致

✅ **启动速度**
- 略有提升（减少了文件数量）

✅ **网络传输**
- 显著提升（镜像更小）

## 维护建议

1. **定期更新基础镜像**：`docker pull python:3.12-slim`
2. **清理构建缓存**：`docker system prune -a`
3. **使用多阶段构建**：对于复杂应用
4. **监控镜像大小**：每次构建后检查大小

## 故障排查

### 如果某些功能不工作

1. 检查是否移除了必要的文件
2. 查看容器日志：`docker logs voice_text_tts_app`
3. 进入容器检查：`docker exec -it voice_text_tts_app bash`

### 如果镜像太大

1. 检查 Dockerfile 中是否有不必要的文件复制
2. 优化 .dockerignore
3. 使用 `docker history` 查看各层大小

## 参考资料

- [Dockerfile 最佳实践](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Python Docker 镜像优化](https://docs.docker.com/samples/django/dockerfile/)
- [Docker 多阶段构建](https://docs.docker.com/develop/develop-images/multistage-build/)
