"""
ASR客户端测试脚本
用于测试ASR服务器
"""

import asyncio
import websockets
import json
import logging
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_asr_server(uri: str = "ws://localhost:10095/ws"):
    """
    测试ASR服务器

    Args:
        uri: ASR服务器WebSocket地址
    """
    logger.info(f"连接到ASR服务器: {uri}")

    try:
        async with websockets.connect(uri) as websocket:
            logger.info("✓ 成功连接到服务器")

            # 创建模拟音频数据
            mock_audio_data = "mock_audio_data_" + "A" * 1000

            # 构造请求消息
            request = {
                "type": "audio",
                "data": mock_audio_data
            }

            logger.info("发送模拟音频数据...")
            await websocket.send(json.dumps(request))
            logger.info("✓ 音频数据已发送")

            # 接收响应
            logger.info("等待识别结果...")
            response = await websocket.recv()
            result = json.loads(response)

            logger.info("✓ 收到识别结果")
            print("\n" + "="*50)
            print("识别结果:")
            print("="*50)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print("="*50 + "\n")

            if result.get("status") == "success":
                text = result.get("text", "")
                confidence = result.get("confidence", 0)
                logger.info(f"识别成功！")
                logger.info(f"文本: {text}")
                logger.info(f"置信度: {confidence}")
                return True
            else:
                error = result.get("error", "未知错误")
                logger.error(f"识别失败: {error}")
                return False

    except ConnectionRefusedError:
        logger.error("✗ 连接被拒绝，请确认ASR服务器是否已启动")
        return False
    except Exception as e:
        logger.error(f"✗ 测试失败: {str(e)}")
        return False


async def test_multiple_requests(uri: str = "ws://localhost:10095/ws", count: int = 3):
    """
    测试多次请求

    Args:
        uri: ASR服务器WebSocket地址
        count: 请求次数
    """
    logger.info(f"进行 {count} 次连续测试...\n")

    success_count = 0

    for i in range(count):
        logger.info(f"--- 测试 {i+1}/{count} ---")
        success = await test_asr_server(uri)
        if success:
            success_count += 1

        # 等待1秒再进行下一次测试
        if i < count - 1:
            await asyncio.sleep(1)

    logger.info(f"\n测试完成: {success_count}/{count} 成功")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="ASR客户端测试")
    parser.add_argument(
        '--uri',
        type=str,
        default='ws://localhost:10095/ws',
        help='ASR服务器WebSocket地址 (默认: ws://localhost:10095/ws)'
    )
    parser.add_argument(
        '--count',
        type=int,
        default=1,
        help='测试次数 (默认: 1)'
    )

    args = parser.parse_args()

    print("\n" + "="*50)
    print("ASR客户端测试工具")
    print("="*50 + "\n")

    if args.count > 1:
        asyncio.run(test_multiple_requests(args.uri, args.count))
    else:
        success = asyncio.run(test_asr_server(args.uri))
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
