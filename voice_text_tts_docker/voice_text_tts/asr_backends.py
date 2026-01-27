"""
通用ASR后端接口
支持多种ASR服务：FunASR, Whisper, 通用WebSocket ASR等
"""

from abc import ABC, abstractmethod
from typing import Optional, Callable, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ASRBackend(ABC):
    """ASR后端抽象基类"""

    def __init__(
        self,
        audio_format: str = "wav",
        sample_rate: int = 16000,
        **kwargs
    ):
        """
        初始化ASR后端

        Args:
            audio_format: 音频格式 (wav, mp3, etc.)
            sample_rate: 采样率
            **kwargs: 其他自定义参数
        """
        self.audio_format = audio_format
        self.sample_rate = sample_rate
        self.extra_params = kwargs

    @abstractmethod
    async def transcribe(
        self,
        audio_path: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """
        转录音频文件

        Args:
            audio_path: 音频文件路径
            progress_callback: 进度回调函数，接收状态消息

        Returns:
            str: 转录的文本，如果失败则返回None
        """
        pass

    @abstractmethod
    async def connect(self) -> bool:
        """
        连接到ASR服务

        Returns:
            bool: 连接是否成功
        """
        pass

    @abstractmethod
    async def disconnect(self):
        """断开ASR服务连接"""
        pass


class FunASRBackend(ASRBackend):
    """FunASR后端实现"""

    def __init__(
        self,
        uri: str = "ws://localhost:10095/ws",
        mode: str = "2pass-offline",
        chunk_size: list = None,
        chunk_interval: int = 10,
        encoder_chunk_look_back: int = 4,
        decoder_chunk_look_back: int = 0,
        hotwords: str = "{}",
        use_itn: bool = True,
        **kwargs
    ):
        """
        初始化FunASR后端

        Args:
            uri: WebSocket服务器地址
            mode: ASR模式 (2pass-offline, 2pass-online, offline, online)
            chunk_size: 分块大小 [chunk_size_s, chunk_size_ms, chunk_interval]
            chunk_interval: 分块间隔（毫秒）
            encoder_chunk_look_back: 编码器回看块数
            decoder_chunk_look_back: 解码器回看块数
            hotwords: 热词配置
            use_itn: 是否使用ITN
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)
        self.uri = uri
        self.mode = mode
        self.chunk_size = chunk_size or [5, 10, 5]
        self.chunk_interval = chunk_interval
        self.encoder_chunk_look_back = encoder_chunk_look_back
        self.decoder_chunk_look_back = decoder_chunk_look_back
        self.hotwords = hotwords
        self.use_itn = use_itn
        self.websocket = None
        self.is_connected = False

    async def connect(self) -> bool:
        """连接到FunASR服务器"""
        import websockets

        try:
            self.websocket = await websockets.connect(self.uri)
            self.is_connected = True
            logger.info(f"成功连接到FunASR服务器: {self.uri}, 模式: {self.mode}")
            return True
        except Exception as e:
            logger.error(f"连接FunASR服务器失败: {str(e)}")
            self.is_connected = False
            return False

    async def disconnect(self):
        """断开FunASR服务器连接"""
        if self.websocket:
            try:
                await self.websocket.close()
                logger.info("已断开FunASR服务器连接")
            except Exception as e:
                logger.error(f"断开连接时出错: {str(e)}")
            finally:
                self.websocket = None
                self.is_connected = False

    async def transcribe(
        self,
        audio_path: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """转录音频文件"""
        if not self.is_connected:
            if progress_callback:
                progress_callback("正在连接ASR服务器...")
            if not await self.connect():
                return None

        try:
            # 读取音频文件
            if progress_callback:
                progress_callback("正在读取音频文件...")

            audio_bytes = self._read_audio_file(audio_path)
            if audio_bytes is None:
                return None

            # 发送音频数据
            if progress_callback:
                progress_callback("正在发送音频数据...")

            await self._send_audio_data(audio_bytes, progress_callback)

            # 接收转录结果
            if progress_callback:
                progress_callback("正在识别语音...")

            result = await self._receive_result(progress_callback)

            if result and progress_callback:
                progress_callback("识别完成")

            return result

        except Exception as e:
            logger.error(f"转录音频失败: {str(e)}")
            return None

    def _read_audio_file(self, audio_path: str) -> Optional[bytes]:
        """读取音频文件"""
        import os

        try:
            if not os.path.exists(audio_path):
                logger.error(f"音频文件不存在: {audio_path}")
                return None

            with open(audio_path, 'rb') as f:
                audio_data = f.read()

            logger.info(f"读取音频文件: {audio_path}, 大小={len(audio_data)}字节")
            return audio_data

        except Exception as e:
            logger.error(f"读取音频文件失败: {str(e)}")
            return None

    async def _send_audio_data(
        self,
        audio_data: bytes,
        progress_callback: Optional[Callable[[str], None]] = None
    ):
        """发送音频数据到FunASR服务器"""
        import asyncio
        import json
        import os

        if not self.websocket:
            raise Exception("WebSocket连接未建立")

        try:
            # 发送初始化消息（FunASR协议）
            init_message = {
                "mode": self.mode,
                "chunk_size": self.chunk_size,
                "chunk_interval": self.chunk_interval,
                "encoder_chunk_look_back": self.encoder_chunk_look_back,
                "decoder_chunk_look_back": self.decoder_chunk_look_back,
                "audio_fs": self.sample_rate,
                "wav_name": "audio",
                "wav_format": self.audio_format,
                "is_speaking": True,
                "hotwords": self.hotwords,
                "itn": 1 if self.use_itn else 0
            }

            await self.websocket.send(json.dumps(init_message))
            logger.info(f"已发送初始化消息: mode={self.mode}")

            # 计算分块数量
            stride = int(self.sample_rate * self.chunk_size[1] / self.chunk_interval * 2)
            chunk_num = (len(audio_data) + stride - 1) // stride

            # 发送音频分块
            for i in range(chunk_num):
                beg = i * stride
                data = audio_data[beg:beg + stride]

                # 发送二进制数据
                await self.websocket.send(data)

                if progress_callback and i % 10 == 0:
                    progress_callback(f"发送中... {i+1}/{chunk_num}")

                # 控制发送速率
                await asyncio.sleep(0.001 if self.mode == "offline" or "2pass-offline" in self.mode else 0.6)

            # 发送结束标记
            end_message = {"is_speaking": False}
            await self.websocket.send(json.dumps(end_message))
            logger.info(f"音频数据已发送，总分块数: {chunk_num}")

        except Exception as e:
            logger.error(f"发送音频数据失败: {str(e)}")
            raise e

    async def _receive_result(self, progress_callback: Optional[Callable[[str], None]] = None) -> Optional[str]:
        """接收FunASR识别结果"""
        import asyncio
        import json

        if not self.websocket:
            raise Exception("WebSocket连接未建立")

        try:
            final_text = ""
            offline_received = False
            online_received = False

            # 接收响应
            while True:
                try:
                    response = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=60.0
                    )
                except asyncio.TimeoutError:
                    logger.warning("等待响应超时")
                    break

                if isinstance(response, bytes):
                    try:
                        response = response.decode('utf-8')
                    except:
                        continue

                # 解析响应
                try:
                    if isinstance(response, str):
                        result = json.loads(response)
                    else:
                        logger.warning(f"未知的响应类型: {type(response)}")
                        continue

                    if isinstance(result, dict):
                        mode = result.get("mode", "")
                        text = result.get("text", "")
                        is_final = result.get("is_final", False)

                        # 2pass模式处理
                        if "2pass" in self.mode:
                            if mode == "2pass-offline":
                                final_text = text
                                offline_received = True
                                if progress_callback:
                                    progress_callback(f"第一遍识别完成: {text[:50]}...")
                            elif mode == "2pass-online":
                                final_text = text
                                online_received = True
                                if progress_callback:
                                    progress_callback(f"第二遍识别完成: {text[:50]}...")
                                if is_final:
                                    break
                            elif mode in ["offline", "online"]:
                                final_text = text
                                if is_final:
                                    break
                        else:
                            # 简单模式
                            if text:
                                final_text = text
                                if is_final:
                                    break

                except json.JSONDecodeError:
                    if isinstance(response, str) and len(response) > 0:
                        final_text = response
                        break

                except Exception as e:
                    logger.error(f"解析响应时出错: {str(e)}")
                    continue

            # 返回最佳结果
            if online_received:
                logger.info(f"使用2pass-online结果: {final_text[:50]}...")
            elif offline_received:
                logger.info(f"使用2pass-offline结果: {final_text[:50]}...")

            return final_text if final_text else None

        except Exception as e:
            logger.error(f"接收识别结果失败: {str(e)}")
            return None


class GenericWebSocketASRBackend(ASRBackend):
    """通用WebSocket ASR后端实现"""

    def __init__(
        self,
        uri: str = "ws://localhost:10095/ws",
        init_message: Dict[str, Any] = None,
        end_message: Dict[str, Any] = None,
        **kwargs
    ):
        """
        初始化通用WebSocket ASR后端

        Args:
            uri: WebSocket服务器地址
            init_message: 初始化消息模板
            end_message: 结束消息模板
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)
        self.uri = uri
        self.init_message = init_message or {"is_speaking": True}
        self.end_message = end_message or {"is_speaking": False}
        self.websocket = None
        self.is_connected = False

    async def connect(self) -> bool:
        """连接到WebSocket ASR服务器"""
        import websockets

        try:
            self.websocket = await websockets.connect(self.uri)
            self.is_connected = True
            logger.info(f"成功连接到WebSocket ASR服务器: {self.uri}")
            return True
        except Exception as e:
            logger.error(f"连接WebSocket ASR服务器失败: {str(e)}")
            self.is_connected = False
            return False

    async def disconnect(self):
        """断开WebSocket ASR服务器连接"""
        if self.websocket:
            try:
                await self.websocket.close()
                logger.info("已断开WebSocket ASR服务器连接")
            except Exception as e:
                logger.error(f"断开连接时出错: {str(e)}")
            finally:
                self.websocket = None
                self.is_connected = False

    async def transcribe(
        self,
        audio_path: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """转录音频文件"""
        import json
        import os

        if not self.is_connected:
            if progress_callback:
                progress_callback("正在连接ASR服务器...")
            if not await self.connect():
                return None

        try:
            # 读取音频文件
            if progress_callback:
                progress_callback("正在读取音频文件...")

            if not os.path.exists(audio_path):
                logger.error(f"音频文件不存在: {audio_path}")
                return None

            with open(audio_path, 'rb') as f:
                audio_data = f.read()

            # 发送初始化消息
            await self.websocket.send(json.dumps(self.init_message))

            # 发送音频数据
            if progress_callback:
                progress_callback("正在发送音频数据...")

            await self.websocket.send(audio_data)

            # 发送结束消息
            await self.websocket.send(json.dumps(self.end_message))

            # 接收结果
            if progress_callback:
                progress_callback("正在识别语音...")

            response = await self.websocket.recv()
            if isinstance(response, bytes):
                response = response.decode('utf-8')

            result = json.loads(response) if isinstance(response, str) else response

            # 尝试多种字段名获取文本
            text = None
            if isinstance(result, dict):
                text = result.get("text") or result.get("result") or result.get("transcript")
            elif isinstance(result, str):
                text = result

            if text and progress_callback:
                progress_callback("识别完成")

            return text

        except Exception as e:
            logger.error(f"转录音频失败: {str(e)}")
            return None


class ASRBackendFactory:
    """ASR后端工厂类"""

    _backends = {
        "funasr": FunASRBackend,
        "websocket": GenericWebSocketASRBackend,
    }

    @classmethod
    def create_backend(cls, backend_type: str, **kwargs) -> ASRBackend:
        """
        创建ASR后端实例

        Args:
            backend_type: 后端类型 (funasr, websocket, etc.)
            **kwargs: 后端初始化参数

        Returns:
            ASRBackend: ASR后端实例

        Raises:
            ValueError: 未知的后端类型
        """
        backend_class = cls._backends.get(backend_type.lower())
        if not backend_class:
            raise ValueError(f"未知的ASR后端类型: {backend_type}. 可用类型: {list(cls._backends.keys())}")

        return backend_class(**kwargs)

    @classmethod
    def register_backend(cls, name: str, backend_class: type):
        """
        注册自定义ASR后端

        Args:
            name: 后端名称
            backend_class: 后端类（必须继承自ASRBackend）
        """
        if not issubclass(backend_class, ASRBackend):
            raise TypeError(f"{backend_class} 必须继承自ASRBackend")

        cls._backends[name.lower()] = backend_class
        logger.info(f"已注册ASR后端: {name}")
