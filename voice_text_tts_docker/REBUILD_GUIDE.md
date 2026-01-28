# Docker 镜像重新构建指南

## 构建脚本说明

### 1. `build.sh` - 标准构建（自动删除旧镜像）

每次运行时自动删除旧镜像并重新构建。

```bash
./build.sh
```

**行为**：
- ✅ 自动检查并删除旧镜像
- ✅ 清理悬空镜像
- ✅ 重新构建镜像
- ✅ 保留 Docker 构建缓存（加快重建速度）

**适用场景**：
- 源代码有更新
- 需要重新打包镜像
- 日常开发使用

---

### 2. `start.sh` - 启动应用（可选重新构建）

交互式脚本，询问是否重新构建。

```bash
./start.sh
```

**行为**：
- 提示是否重新构建镜像
- 选择重新构建时：
  - ✅ 自动停止旧容器
  - ✅ 删除旧镜像
  - ✅ 重新构建（`--no-cache`）
  - ✅ 启动新容器
- 选择不重新构建：
  - 直接使用现有镜像启动

**适用场景**：
- 首次启动应用
- 需要交互式选择是否重建

---

### 3. `rebuild.sh` - 完全重新构建（彻底清理）

完全清理并重建，不使用任何缓存。

```bash
./rebuild.sh
```

**行为**：
- ✅ 停止并删除所有相关容器
- ✅ 删除旧镜像（强制）
- ✅ 清理悬空镜像
- ✅ 清理 Docker 构建缓存
- ✅ 重新复制源代码
- ✅ 全新构建（`--no-cache`）
- ✅ 询问是否立即启动

**适用场景**：
- 怀疑缓存导致问题
- 需要完全干净的构建
- 镜像大小异常
- 构建出现错误需要重试

---

## 构建策略对比

| 脚本 | 删除旧镜像 | 清理缓存 | 速度 | 使用场景 |
|------|-----------|---------|------|---------|
| `build.sh` | ✅ | ❌ | 快 | 日常开发 |
| `start.sh` | ✅ | ❌ | 快 | 启动应用 |
| `rebuild.sh` | ✅ | ✅ | 慢 | 问题排查 |

## 推荐工作流

### 开发阶段
```bash
# 代码更新后
./build.sh

# 启动应用
./start.sh
```

### 生产部署
```bash
# 完全重新构建
./rebuild.sh
```

### 问题排查
```bash
# 怀疑缓存问题
./rebuild.sh

# 查看构建日志
docker build --no-cache -t voice-text-tts:latest .
```

## 镜像大小管理

### 查看镜像大小
```bash
docker images voice-text-tts:latest
```

### 查看镜像层
```bash
docker history voice-text-tts:latest
```

### 清理所有未使用镜像
```bash
docker image prune -a
```

### 查看磁盘使用
```bash
docker system df
```

## 常见问题

### Q: 为什么 build.sh 删除旧镜像但保留缓存？
A: 保留缓存可以加快重建速度，只有在 rebuild.sh 中才会清理所有缓存。

### Q: 如何强制完全重新构建？
A: 使用 `./rebuild.sh` 或手动运行：
```bash
docker system prune -a -f
docker build --no-cache -t voice-text-tts:latest .
```

### Q: 旧镜像删除失败怎么办？
A: 停止所有使用该镜像的容器：
```bash
docker-compose down
docker rmi voice-text-tts:latest -f
```

### Q: 如何减少镜像大小？
A: 查看优化指南：[OPTIMIZATION.md](OPTIMIZATION.md)

## 提示

- ✅ `build.sh` - 快速重建，适合日常使用
- ✅ `start.sh` - 交互式，方便选择
- ✅ `rebuild.sh` - 彻底重建，解决问题
- ✅ 使用 `--no-cache` 确保全新构建
- ✅ 定期清理悬空镜像节省空间
