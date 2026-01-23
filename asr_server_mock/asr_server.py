"""
模拟ASR WebSocket服务器
用于测试ASR客户端功能
"""

import asyncio
import websockets
import json
import logging
import random
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 模拟的识别结果库
MOCK_RECOGNITION_RESULTS = [
    "希望你以后能够做得比我还好呦。",
    "你好，我是语音识别助手。",
    "今天的天气真不错。",
    "这是一个测试音频文件。",
    "语音识别功能正在运行中。",
    "请说话，我会帮您识别文字。",
    "人工智能技术正在快速发展。",
    "语音合成的效果越来越好了。",
    "欢迎使用语音识别服务。",
    "这是一个模拟的ASR服务器。"
]


class MockASRServer:
    """模拟ASR WebSocket服务器"""

    def __init__(self, host: str = "localhost", port: int = 10095, mode: str = "2pass-offline"):
        """
        初始化ASR服务器

        Args:
            host: 服务器地址
            port: 服务器端口
            mode: ASR模式 (2pass-offline, offline, streaming等)
        """
        self.host = host
        self.port = port
        self.mode = mode
        self.server = None
        logger.info(f"ASR服务器初始化 - 模式: {mode}")

    async def handle_client(self, websocket):
        """
        处理客户端连接

        Args:
            websocket: WebSocket连接对象
        """
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"[{client_id}] 新客户端连接")

        try:
            async for message in websocket:
                # 解析客户端消息
                try:
                    data = json.loads(message)
                    message_type = data.get("type", "unknown")

                    logger.info(f"[{client_id}] 收到消息类型: {message_type}")

                    if message_type == "audio":
                        # 模拟识别过程
                        await self._process_audio(websocket, client_id, data)
                    else:
                        logger.warning(f"[{client_id}] 未知消息类型: {message_type}")
                        await self._send_error(websocket, f"未知消息类型: {message_type}")

                except json.JSONDecodeError as e:
                    logger.error(f"[{client_id}] JSON解析错误: {str(e)}")
                    await self._send_error(websocket, f"JSON解析错误: {str(e)}")
                except Exception as e:
                    logger.error(f"[{client_id}] 处理消息时出错: {str(e)}")
                    await self._send_error(websocket, f"处理错误: {str(e)}")

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"[{client_id}] 客户端断开连接")
        except Exception as e:
            logger.error(f"[{client_id}] 连接错误: {str(e)}")

    async def _process_audio(self, websocket, client_id: str, data: dict):
        """
        处理音频数据（模拟识别过程）

        Args:
            websocket: WebSocket连接对象
            client_id: 客户端ID
            data: 音频数据
        """
        try:
            # 模拟处理延迟（1-3秒）
            processing_time = random.uniform(1.0, 3.0)
            logger.info(f"[{client_id}] 开始识别音频，预计耗时 {processing_time:.2f} 秒")

            # 模拟识别进度
            await asyncio.sleep(processing_time * 0.3)
            logger.info(f"[{client_id}] 正在识别...")

            await asyncio.sleep(processing_time * 0.4)
            logger.info(f"[{client_id}] 识别中...")

            await asyncio.sleep(processing_time * 0.3)

            # 随机选择一个识别结果
            # 如果数据中包含音频数据的十六进制，可以根据音频内容"定制"结果
            audio_hex = data.get("data", "")
            if audio_hex:
                # 根据音频数据生成一个"伪随机"但一致的结果
                audio_hash = hash(audio_hex[:100])  # 使用前100个字符计算hash
                result_index = abs(audio_hash) % len(MOCK_RECOGNITION_RESULTS)
                result_text = MOCK_RECOGNITION_RESULTS[result_index]
            else:
                # 随机选择
                result_text = random.choice(MOCK_RECOGNITION_RESULTS)

            # 构造响应
            response = {
                "status": "success",
                "text": result_text,
                "mode": self.mode,
                "confidence": round(random.uniform(0.85, 0.99), 2),
                "processing_time": round(processing_time, 2),
                "timestamp": datetime.now().isoformat()
            }

            # 发送识别结果
            await websocket.send(json.dumps(response))
            logger.info(f"[{client_id}] 识别完成: {result_text} (模式: {self.mode})")

        except Exception as e:
            logger.error(f"[{client_id}] 处理音频时出错: {str(e)}")
            await self._send_error(websocket, f"处理音频失败: {str(e)}")

    async def _send_error(self, websocket, error_message: str):
        """
        发送错误消息

        Args:
            websocket: WebSocket连接对象
            error_message: 错误消息
        """
        response = {
            "status": "error",
            "error": error_message,
            "timestamp": datetime.now().isoformat()
        }
        try:
            await websocket.send(json.dumps(response))
        except:
            pass

    async def start(self):
        """启动服务器"""
        logger.info(f"启动ASR服务器: ws://{self.host}:{self.port}")
        logger.info("等待客户端连接...")

        self.server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=20
        )

        logger.info(f"ASR服务器已启动在 ws://{self.host}:{self.port}")

    async def stop(self):
        """停止服务器"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("ASR服务器已停止")


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="模拟ASR WebSocket服务器")
    parser.add_argument(
        '--host',
        type=str,
        default='localhost',
        help='服务器地址 (默认: localhost)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=10095,
        help='服务器端口 (默认: 10095)'
    )
    parser.add_argument(
        '--mode',
        type=str,
        default='2pass-offline',
        choices=['2pass-offline', 'offline', 'streaming', 'online'],
        help='ASR模式 (默认: 2pass-offline)'
    )

    args = parser.parse_args()

    # 创建并启动服务器
    server = MockASRServer(host=args.host, port=args.port, mode=args.mode)

    try:
        await server.start()

        # 保持服务器运行
        logger.info("按 Ctrl+C 停止服务器")
        await asyncio.Future()  # 永远运行

    except KeyboardInterrupt:
        logger.info("\n收到停止信号")
    finally:
        await server.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("服务器已停止")
