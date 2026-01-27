# 一键部署脚本使用说明

## 🚀 快速开始

### 使用一键部署脚本（推荐）

```bash
./deploy.sh voice-text-tts-docker-image-YYYYMMDD_HHMMSS.tar.gz
```

就这么简单！脚本会自动完成所有部署步骤。

## 📋 脚本功能

### 自动化步骤

1. **环境检查** ✓
   - 检查 Docker 是否安装
   - 检查 Docker 服务是否运行
   - 显示安装指南（如果 Docker 未安装）

2. **镜像导入** ✓
   - 检查镜像是否已存在
   - 可选删除旧镜像
   - 导入新镜像
   - 显示导入进度

3. **配置创建** ✓
   - 检查 `.env` 文件是否存在
   - 可选使用现有配置
   - 自动创建默认配置
   - 可选编辑配置文件

4. **容器启动** ✓
   - 检查端口冲突
   - 自动停止旧容器
   - 启动新容器
   - 配置网络（host.docker.internal）

5. **服务验证** ✓
   - 等待服务启动
   - 检查服务是否就绪
   - 显示访问地址

6. **结果显示** ✓
   - 显示访问地址
   - 显示管理命令
   - 显示注意事项

## 📖 详细说明

### 参数说明

```bash
./deploy.sh <镜像文件.tar.gz>
```

**必需参数**:
- 镜像文件：打包的 Docker 镜像文件（.tar.gz 格式）

### 交互式选项

脚本运行过程中会有以下交互选项：

1. **删除旧镜像**（如果镜像已存在）
   ```
   是否删除旧镜像并重新导入？(y/N):
   ```
   - `y` - 删除并重新导入
   - `N` - 使用现有镜像

2. **使用现有配置**（如果 .env 已存在）
   ```
   是否使用现有配置？(Y/n):
   ```
   - `Y` - 使用现有配置
   - `n` - 创建新配置

3. **编辑配置文件**
   ```
   是否现在编辑配置文件？(y/N):
   ```
   - `y` - 打开编辑器（使用 $EDITOR 或 vi）
   - `N` - 跳过编辑

4. **停止现有容器**（如果端口冲突）
   ```
   是否停止并删除现有容器？(y/N):
   ```
   - `y` - 停止并删除
   - `N` - 退出（端口冲突）

## 🔧 高级用法

### 非交互模式（自动化部署）

如果你想跳过所有提示，可以修改脚本或使用以下方法：

```bash
# 使用 yes 命令自动回答所有提示
yes | ./deploy.sh voice-text-tts-docker-image-YYYYMMDD_HHMMSS.tar.gz
```

### 仅导入镜像（不启动）

使用 `import-image.sh` 脚本：

```bash
./import-image.sh voice-text-tts-docker-image-YYYYMMDD_HHMMSS.tar.gz
```

### 自定义配置

1. 先运行脚本创建配置：
   ```bash
   ./deploy.sh voice-text-tts-docker-image-YYYYMMDD_HHMMSS.tar.gz
   ```

2. 编辑配置文件：
   ```bash
   vim .env
   ```

3. 重启容器应用配置：
   ```bash
   docker restart voice_text_tts_app
   ```

## 📝 配置说明

脚本会自动创建 `.env` 文件，包含以下配置：

### 必需配置

```bash
# API 服务器地址（容器访问宿主机）
API_HOST=host.docker.internal

# API 服务器端口
API_PORT=50000
```

### 可选配置

```bash
# Web 服务端口（默认 7862）
SERVER_PORT=7862

# Gradio Share 模式
GRADIO_SHARE=true

# 最大文本长度
MAX_TEXT_LENGTH=1000

# ASR 语音识别
ASR_ENABLED=false
```

## 🔍 故障排查

### Docker 未安装

```bash
# 检查 Docker
docker --version

# 安装 Docker（Ubuntu/Debian）
curl -fsSL https://get.docker.com | sh

# 启动 Docker
sudo systemctl start docker
```

### 镜像导入失败

```bash
# 检查磁盘空间
df -h

# 查看镜像文件
ls -lh voice-text-tts-docker-image-*.tar.gz

# 手动导入测试
gunzip -c voice-text-tts-docker-image-*.tar.gz | docker load
```

### 容器启动失败

```bash
# 查看容器日志
docker logs voice_text_tts_app

# 检查容器状态
docker ps -a | grep voice_text_tts_app

# 检查网络配置
docker exec voice_text_tts_app cat /etc/hosts
```

### 服务无法访问

```bash
# 检查端口
netstat -tuln | grep 7862

# 检查容器状态
docker ps | grep voice_text_tts_app

# 测试服务
curl http://localhost:7862
```

## 🌐 部署到新服务器

### 步骤 1: 传输文件

```bash
# 传输镜像和脚本
scp build/voice-text-tts-docker-image-*.tar.gz user@server:/path/
scp build/deploy.sh user@server:/path/
```

### 步骤 2: 在目标服务器执行

```bash
# 添加执行权限
chmod +x deploy.sh

# 运行部署脚本
./deploy.sh voice-text-tts-docker-image-*.tar.gz
```

### 步骤 3: 验证部署

```bash
# 访问服务
curl http://localhost:7862

# 或在浏览器中打开
http://server-ip:7862
```

## 📊 脚本输出示例

```
==========================================
Voice Text TTS Docker 一键部署工具
==========================================

===> 检查 Docker 环境...
[INFO] Docker 环境检查通过

===> 导入 Docker 镜像...
[INFO] 正在导入镜像（这可能需要 5-10 分钟）...
[INFO] 镜像导入完成！

===> 创建配置文件...
[INFO] 已创建 .env 配置文件

===> 启动容器...
[INFO] 容器启动成功！

===> 等待服务启动...
.........[INFO] 服务已就绪！

==========================================
部署完成！
==========================================

访问地址:
  本地访问: http://localhost:7862
  局域网: http://192.168.1.100:7862

容器管理:
  查看状态: docker ps | grep voice_text_tts_app
  查看日志: docker logs -f voice_text_tts_app
  停止容器: docker stop voice_text_tts_app
  重启容器: docker restart voice_text_tts_app

==========================================
```

## 💡 提示

1. **首次部署**: 建议使用交互模式，熟悉每个步骤
2. **批量部署**: 使用 `yes` 命令自动化
3. **配置修改**: 修改 `.env` 后需重启容器
4. **日志查看**: 使用 `docker logs -f voice_text_tts_app` 实时查看
5. **资源清理**: 使用 `docker system prune -a` 清理未使用的资源

## 🔄 更新部署

如果已有镜像在运行：

```bash
# 方式一：使用部署脚本（推荐）
./deploy.sh voice-text-tts-docker-image-new-version.tar.gz

# 方式二：手动更新
docker stop voice_text_tts_app
docker rm voice_text_tts_app
docker rmi voice-text-tts:latest
./import-image.sh new-image.tar.gz
./run.sh start
```
