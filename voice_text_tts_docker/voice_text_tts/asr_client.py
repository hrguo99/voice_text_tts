"""
ASR (Automatic Speech Recognition) 客户端
通过WebSocket连接实现语音转文本功能

支持多种ASR服务：
- FunASR (2pass-offline, 2pass-online, offline, online)
- 通用的WebSocket ASR服务
- 其他通过ASRBackend接口实现的服务
"""

import asyncio
import logging
from typing import Optional, Callable
from asr_backends import ASRBackend, ASRBackendFactory

logger = logging.getLogger(__name__)


class ASRClient:
    """
    通用ASR客户端（使用后端模式）

    支持多种ASR后端，通过backend_type指定使用的后端
    """

    def __init__(
        self,
        backend_type: str = "funasr",
        audio_format: str = "wav",
        sample_rate: int = 16000,
        **kwargs
    ):
        """
        初始化ASR客户端

        Args:
            backend_type: 后端类型 (funasr, websocket, etc.)
            audio_format: 音频格式 (wav, mp3, etc.)
            sample_rate: 采样率
            **kwargs: 传递给后端的其他参数
        """
        self.backend_type = backend_type
        self.audio_format = audio_format
        self.sample_rate = sample_rate
        self.backend_params = kwargs
        self.backend: Optional[ASRBackend] = None

    async def connect(self) -> bool:
        """
        连接到ASR服务器

        Returns:
            bool: 连接是否成功
        """
        if not self.backend:
            self.backend = ASRBackendFactory.create_backend(
                self.backend_type,
                audio_format=self.audio_format,
                sample_rate=self.sample_rate,
                **self.backend_params
            )

        return await self.backend.connect()

    async def disconnect(self):
        """断开ASR服务器连接"""
        if self.backend:
            await self.backend.disconnect()
            self.backend = None

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
        if not self.backend:
            self.backend = ASRBackendFactory.create_backend(
                self.backend_type,
                audio_format=self.audio_format,
                sample_rate=self.sample_rate,
                **self.backend_params
            )

        return await self.backend.transcribe(audio_path, progress_callback)

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.disconnect()


def transcribe_audio_sync(
    audio_path: str,
    backend_type: str = "funasr",
    audio_format: str = "wav",
    sample_rate: int = 16000,
    progress_callback: Optional[Callable[[str], None]] = None,
    **kwargs
) -> Optional[str]:
    """
    同步接口：转录音频文件

    Args:
        audio_path: 音频文件路径
        backend_type: ASR后端类型 (funasr, websocket, etc.)
        audio_format: 音频格式
        sample_rate: 采样率
        progress_callback: 进度回调函数
        **kwargs: 传递给后端的其他参数

    Returns:
        str: 转录的文本，如果失败则返回None
    """
    async def _transcribe():
        async with ASRClient(
            backend_type=backend_type,
            audio_format=audio_format,
            sample_rate=sample_rate,
            **kwargs
        ) as client:
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
