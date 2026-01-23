"""
ASR (Automatic Speech Recognition) 客户端
通过WebSocket连接实现语音转文本功能
"""

import asyncio
import websockets
import json
import logging
from typing import Optional, Callable
import numpy as np
import wave
import os

logger = logging.getLogger(__name__)


class ASRClient:
    """ASR WebSocket客户端"""

    def __init__(self, uri: str = "ws://localhost:10095/ws"):
        """
        初始化ASR客户端

        Args:
            uri: WebSocket服务器地址
        """
        self.uri = uri
        self.websocket = None
        self.is_connected = False

    async def connect(self) -> bool:
        """
        连接到ASR服务器

        Returns:
            bool: 连接是否成功
        """
        try:
            self.websocket = await websockets.connect(self.uri)
            self.is_connected = True
            logger.info(f"成功连接到ASR服务器: {self.uri}")
            return True
        except Exception as e:
            logger.error(f"连接ASR服务器失败: {str(e)}")
            self.is_connected = False
            return False

    async def disconnect(self):
        """断开ASR服务器连接"""
        if self.websocket:
            try:
                await self.websocket.close()
                logger.info("已断开ASR服务器连接")
            except Exception as e:
                logger.error(f"断开连接时出错: {str(e)}")
            finally:
                self.websocket = None
                self.is_connected = False

    async def transcribe_audio_file(
        self,
        audio_path: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """
        发送音频文件进行转录

        Args:
            audio_path: 音频文件路径
            progress_callback: 进度回调函数，接收状态消息

        Returns:
            str: 转录的文本，如果失败则返回None
        """
        if not self.is_connected:
            if progress_callback:
                progress_callback("正在连接ASR服务器...")
            if not await self.connect():
                return None

        try:
            # 读取音频文件
            if progress_callback:
                progress_callback("正在读取音频文件...")

            audio_data = self._read_audio_file(audio_path)
            if audio_data is None:
                return None

            # 发送音频数据
            if progress_callback:
                progress_callback("正在发送音频数据...")

            await self._send_audio_data(audio_data)

            # 接收转录结果
            if progress_callback:
                progress_callback("正在识别语音...")

            result = await self._receive_result()

            if result and progress_callback:
                progress_callback("识别完成")

            return result

        except Exception as e:
            logger.error(f"转录音频失败: {str(e)}")
            return None

    def _read_audio_file(self, audio_path: str) -> Optional[bytes]:
        """
        读取音频文件

        Args:
            audio_path: 音频文件路径

        Returns:
            bytes: 音频数据（只读取前面一部分用于模拟识别）
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(audio_path):
                logger.error(f"音频文件不存在: {audio_path}")
                return None

            # 直接读取文件的一部分用于模拟识别
            # 模拟ASR服务不需要完整音频，只需要文件信息来生成"伪随机"结果
            try:
                with open(audio_path, 'rb') as f:
                    # 只读取前面1KB数据用于hash计算
                    audio_sample = f.read(1024)
                    # 获取文件大小
                    f.seek(0, 2)  # 移到文件末尾
                    file_size = f.tell()

                    logger.info(f"读取音频文件: {audio_path}, 大小={file_size}字节")
                    # 将文件大小附加到样本数据，用于生成一致的识别结果
                    return audio_sample + str(file_size).encode()
            except Exception as e:
                logger.error(f"读取音频文件失败: {str(e)}")
                return None

        except Exception as e:
            logger.error(f"读取音频文件失败: {str(e)}")
            return None

    async def _send_audio_data(self, audio_data: bytes):
        """
        发送音频数据到ASR服务器

        Args:
            audio_data: 音频数据
        """
        if not self.websocket:
            raise Exception("WebSocket连接未建立")

        # 发送音频数据
        # 根据ASR服务的协议，这里可能需要调整数据格式
        # 示例：发送JSON格式的数据
        message = {
            "type": "audio",
            "data": audio_data.hex()  # 将二进制数据转换为十六进制字符串
        }

        await self.websocket.send(json.dumps(message))
        logger.info(f"已发送音频数据，大小: {len(audio_data)} 字节")

    async def _receive_result(self) -> Optional[str]:
        """
        接收ASR识别结果

        Returns:
            str: 识别的文本
        """
        if not self.websocket:
            raise Exception("WebSocket连接未建立")

        try:
            # 接收响应
            response = await self.websocket.recv()

            # 解析响应
            try:
                result = json.loads(response)

                # 根据ASR服务的响应格式提取文本
                # 这里需要根据实际ASR服务的响应格式进行调整
                if isinstance(result, dict):
                    # 常见的ASR服务响应格式
                    text = result.get("text", "")
                    if not text:
                        text = result.get("result", "")
                    if not text:
                        text = result.get("transcription", "")

                    logger.info(f"识别结果: {text}")
                    return text

                elif isinstance(result, str):
                    logger.info(f"识别结果: {result}")
                    return result

                else:
                    logger.warning(f"未知的响应格式: {type(result)}")
                    return None

            except json.JSONDecodeError:
                # 如果响应不是JSON，直接返回
                logger.info(f"识别结果（非JSON）: {response}")
                return response

        except Exception as e:
            logger.error(f"接收识别结果失败: {str(e)}")
            return None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.disconnect()


def transcribe_audio_sync(
    audio_path: str,
    asr_uri: str = "ws://localhost:10095/ws",
    progress_callback: Optional[Callable[[str], None]] = None
) -> Optional[str]:
    """
    同步接口：转录音频文件

    Args:
        audio_path: 音频文件路径
        asr_uri: ASR服务WebSocket地址
        progress_callback: 进度回调函数

    Returns:
        str: 转录的文本，如果失败则返回None
    """
    async def _transcribe():
        async with ASRClient(uri=asr_uri) as client:
            return await client.transcribe_audio_file(audio_path, progress_callback)

    try:
        # 获取或创建事件循环
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # 运行异步任务
        return loop.run_until_complete(_transcribe())

    except Exception as e:
        logger.error(f"同步转录失败: {str(e)}")
        return None
