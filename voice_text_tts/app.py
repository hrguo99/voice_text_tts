"""
语音生成功能 - Gradio应用
基于Fun-CosyVoice3-0.5B-2512 API实现
"""

import gradio as gr
import numpy as np
import os
import tempfile
import requests
import wave
import json
from typing import Optional, Tuple
from ffmpy import FFmpeg
from config import API_HOST, API_PORT, API_MODE, PROMPT_TEXT


class AudioConverter:
    """音频格式转换器"""

    @staticmethod
    def convert_to_wav(input_path: str, output_path: Optional[str] = None) -> str:
        """
        将音频转换为WAV格式（16kHz, 单声道）

        Args:
            input_path: 输入音频文件路径
            output_path: 输出WAV文件路径，如果为None则自动生成

        Returns:
            转换后的WAV文件路径
        """
        if output_path is None:
            output_path = input_path.rsplit('.', 1)[0] + '_converted.wav'

        try:
            # 如果输入已经是WAV格式，直接返回
            if input_path.lower().endswith('.wav'):
                # 仍然使用ffmpeg确保格式正确
                pass

            # 使用ffmpy转换为WAV格式
            # -ar 16000: 采样率16kHz
            # -ac 1: 单声道
            # -acodec pcm_s16le: 16bit PCM编码
            ff = FFmpeg(
                global_options='-y',
                inputs={input_path: None},
                outputs={
                    output_path: '-ar 16000 -ac 1 -acodec pcm_s16le'
                }
            )

            ff.run()

            return output_path

        except Exception as e:
            # 如果转换失败，返回原文件（假设格式已经正确）
            print(f"音频转换警告: {str(e)}")
            return input_path


def create_interface() -> gr.Blocks:
    """创建Gradio界面"""

    # 创建界面
    with gr.Blocks(title="语音生成功能") as app:

        # 主容器
        with gr.Column(elem_classes=["main-container"]):
            # 标题
            gr.Markdown(
                "# <span style='color: #ffffff;'>语音生成功能</span>",
                elem_classes=["app-title"]
            )

            # 主要功能区域
            with gr.Column():
                # 上部：输入区域
                with gr.Column(elem_classes=["input-section"]):
                    gr.Markdown("### 输入区域", elem_classes=["module-title"])

                    # 步骤1: 参考音频输入和输入文本
                    with gr.Row():
                        with gr.Column(scale=1):
                            gr.Markdown("### 参考音频", elem_classes=["module-title"])
                            with gr.Tabs(elem_classes=["audio-tabs"]):
                                with gr.Tab("上传音频"):
                                    audio_upload = gr.Audio(
                                        label="上传参考音频",
                                        type="filepath",
                                        sources=["upload"],
                                        waveform_options=gr.WaveformOptions(
                                            waveform_color="#667eea",
                                            waveform_progress_color="#764ba2"
                                        )
                                    )

                                with gr.Tab("录制音频"):
                                    audio_mic = gr.Audio(
                                        label="麦克风录制",
                                        type="filepath",
                                        sources=["microphone"],
                                        interactive=True,
                                        waveform_options=gr.WaveformOptions(
                                            waveform_color="#667eea",
                                            waveform_progress_color="#764ba2"
                                        )
                                    )

                        with gr.Column(scale=1):
                            # 步骤2: 参考音频文本输入框（必填）
                            gr.Markdown("### 参考音频文本", elem_classes=["module-title"])
                            prompt_audio_text = gr.Textbox(
                                label="参考音频文本内容 *",
                                placeholder="【必填】请输入上传的参考音频对应的文字内容",
                                lines=7,
                                max_lines=6
                            )

                    # 增加间距
                    gr.Markdown("", elem_classes=["spacer-xl"])

                    # 步骤3: 输入文本和使用说明
                    with gr.Row():
                        with gr.Column(scale=1):
                            gr.Markdown("### 输入文本", elem_classes=["module-title"])
                            text_input = gr.Textbox(
                                label="输入文本",
                                placeholder="请输入要合成的文字内容（建议1000字符以内）",
                                lines=7,
                                max_lines=12
                            )

                        with gr.Column(scale=1):
                            # 使用说明
                            gr.Markdown("### 使用说明", elem_classes=["module-title"])
                            gr.Markdown(
                                """
                                **步骤说明：**
                                1. 参考音频 - 选择上传音频文件或使用麦克风录制
                                2. 参考音频文本 - 【必填】输入参考音频对应的文字内容
                                3. 输入文本 - 在文本框中输入要合成的文字内容
                                4. 生成语音 - 点击"生成语音"按钮开始合成

                                **注意事项：**
                                1. 参考音频建议使用清晰、无背景噪音的语音
                                2. 参考音频文本将自动与系统提示词拼接，帮助AI更好地学习声音特征
                                3. 文本长度建议在 1000 字符以内
                                4. 支持的音频格式: WAV, MP3, M4A
                                """,
                                elem_classes=["instructions"]
                            )

                    # 步骤4: 生成按钮
                    generate_btn = gr.Button(
                        "生成语音",
                        variant="primary",
                        size="lg",
                        elem_classes=["generate-button-full-width"]
                    )

                # 下部：输出区域
                with gr.Row():
                    # 输出结果
                    with gr.Column(scale=1, elem_classes=["output-section"]):
                        gr.Markdown("### 输出结果", elem_classes=["module-title"])

                        # 进度条（默认隐藏）
                        progress_bar = gr.Slider(
                            label="生成进度 0.00%",
                            value=0,
                            minimum=0,
                            maximum=100,
                            step=0.01,  # 允许两位小数进度
                            visible=False,
                            interactive=False,
                            elem_classes=["progress-slider"]  # 添加自定义类名
                        )

                        # 输出区域 - 使用Column来容纳音频或错误消息
                        with gr.Column() as output_container:
                            # 输出音频
                            output_audio = gr.Audio(
                                label="生成的语音",
                                type="filepath",
                                interactive=False,
                                visible=True,
                                waveform_options=gr.WaveformOptions(
                                    waveform_color="#10b981",
                                    waveform_progress_color="#059669"
                                )
                            )

                            # 错误消息（初始隐藏）
                            output_error = gr.Markdown(
                                "",
                                visible=False,
                                elem_classes=["error-message"]
                            )

        # 进度更新辅助函数
        def _calculate_time_progress(elapsed_time: float, received_first_chunk: bool) -> float:
            """
            根据经过的时间计算估算进度

            Args:
                elapsed_time: 已经过的秒数
                received_first_chunk: 是否已收到第一个音频chunk

            Returns:
                估算的进度值（0-100）
            """
            if not received_first_chunk:
                # 还没收到第一个chunk：从8%平滑增长到48%
                if elapsed_time < 5:
                    progress_increase = (elapsed_time / 5.0) * 24
                elif elapsed_time < 10:
                    progress_increase = 24 + ((elapsed_time - 5) / 5.0) * 24
                else:
                    progress_increase = 40
                return min(48, 8 + progress_increase)
            else:
                # 已收到chunk：保持当前进度（等待服务端进度更新）
                return None

        def _update_progress(progress_value: float, label: str):
            """统一的进度更新接口"""
            return gr.update(value=progress_value, visible=True, label=f"生成进度 {progress_value:.2f}%")

        # 绑定事件
        def handle_generate(audio_upload_file, audio_mic_file, text, prompt_audio_text_val):
            """处理生成请求"""
            # 优先使用上传的音频，如果没有则使用录制的音频
            reference_audio = audio_upload_file or audio_mic_file

            import time
            start_time = time.time()
            last_update_time = 0
            last_progress = 0

            # 进度常量定义
            PROGRESS_INITIAL = 0
            PROGRESS_VALIDATED = 4
            PROGRESS_CONVERTED = 6
            PROGRESS_REQUEST_SENT = 8
            PROGRESS_FIRST_CHUNK = 65
            PROGRESS_RECEIVING_DONE = 95
            PROGRESS_CONVERTING = 96
            PROGRESS_SAVING = 98
            PROGRESS_DONE = 100

            # 步骤1: 验证输入（显示进度条）
            yield _update_progress(PROGRESS_INITIAL, f"生成进度 {PROGRESS_INITIAL:.2f}%"), gr.update(visible=False), gr.update(visible=False)

            if not reference_audio:
                yield gr.update(value=0, visible=False), gr.update(visible=False), gr.update(visible=True, value="### ❌ 请提供参考音频")
                return
            if not text or text.strip() == "":
                yield gr.update(value=0, visible=False), gr.update(visible=False), gr.update(visible=True, value="### ❌ 请输入要合成的文本")
                return
            if not prompt_audio_text_val or prompt_audio_text_val.strip() == "":
                yield gr.update(value=0, visible=False), gr.update(visible=False), gr.update(visible=True, value="### ❌ 请输入参考音频对应的文本内容")
                return
            if len(text) > 1000:
                yield gr.update(value=0, visible=False), gr.update(visible=False), gr.update(visible=True, value="### ❌ 文本长度超过1000字符限制")
                return

            # 步骤2: 转换音频格式
            yield _update_progress(PROGRESS_VALIDATED, f"生成进度 {PROGRESS_VALIDATED:.2f}%"), gr.update(visible=False), gr.update(visible=False)

            converter = AudioConverter()
            if not reference_audio.endswith('.wav'):
                reference_audio = converter.convert_to_wav(reference_audio)

            # 步骤3: 准备API请求
            yield _update_progress(PROGRESS_CONVERTED, f"生成进度 {PROGRESS_CONVERTED:.2f}%"), gr.update(visible=False), gr.update(visible=False)

            final_prompt_text = f"{PROMPT_TEXT}{prompt_audio_text_val}"
            payload = {
                'tts_text': text,
                'prompt_text': final_prompt_text
            }

            # 步骤4: 发送请求到API
            yield _update_progress(PROGRESS_REQUEST_SENT, f"生成进度 {PROGRESS_REQUEST_SENT:.2f}%"), gr.update(visible=False), gr.update(visible=False)

            try:
                with open(reference_audio, 'rb') as audio_file:
                    files = [
                        ('prompt_wav', ('prompt_wav', audio_file, 'application/octet-stream'))
                    ]

                    response = requests.request(
                        "GET",
                        f"http://{API_HOST}:{API_PORT}/inference_{API_MODE}",
                        data=payload,
                        files=files,
                        stream=True,
                        timeout=300
                    )

                    last_update_time = time.time() - 1.0  # 确保第一次循环就能触发更新

            except FileNotFoundError:
                yield gr.update(value=0, visible=False), gr.update(visible=False), gr.update(visible=True, value=f"### ❌ 找不到音频文件 {reference_audio}")
                return
            except requests.exceptions.ConnectionError as e:
                yield gr.update(value=0, visible=False), gr.update(visible=False), gr.update(visible=True, value=f"### ❌ 连接API失败 - {str(e)}")
                return
            except Exception as e:
                yield gr.update(value=0, visible=False), gr.update(visible=False), gr.update(visible=True, value=f"### ❌ 连接API失败 - {str(e)}")
                return

            if response.status_code == 200:
                # 步骤5: 接收音频数据（带真实进度信息）
                tts_audio = b''
                buffer = b''
                received_chunks = 0  # 本地计数器，用于时间估算
                first_chunk_received = False
                last_update_time = time.time() - 1.0

                try:
                    for tcp_chunk in response.iter_content(chunk_size=2048, decode_unicode=False):
                        current_time = time.time()
                        elapsed_time = current_time - start_time
                        time_since_last_update = (current_time - last_update_time) if last_update_time > 0 else 999

                        # 基于时间的进度估算（仅在未收到第一个chunk时）
                        if not first_chunk_received and time_since_last_update >= 0.2:
                            estimated_progress = _calculate_time_progress(elapsed_time, False)
                            if estimated_progress is not None:
                                yield _update_progress(estimated_progress, f"生成进度 {estimated_progress:.2f}%"), gr.update(visible=False), gr.update(visible=False)
                                last_progress = estimated_progress
                                last_update_time = current_time

                        if tcp_chunk:
                            buffer += tcp_chunk

                            # 解析buffer中的数据块（格式: 4字节长度 + JSON + 音频数据）
                            while len(buffer) >= 4:
                                metadata_length = int.from_bytes(buffer[:4], byteorder='big')

                                if len(buffer) < 4 + metadata_length:
                                    break

                                metadata_json = buffer[4:4 + metadata_length].decode('utf-8')
                                metadata = json.loads(metadata_json)

                                audio_data_start = 4 + metadata_length
                                audio_data_end = audio_data_start + metadata['audio_size']

                                if len(buffer) < audio_data_end:
                                    break

                                audio_chunk = buffer[audio_data_start:audio_data_end]
                                tts_audio += audio_chunk

                                buffer = buffer[audio_data_end:]

                                # 处理开始标记（服务端开始生成）
                                if metadata['chunk_index'] == -1 and metadata.get('status') == 'generating':
                                    continue

                                # 第一次接收到实际音频数据
                                if not first_chunk_received:
                                    yield _update_progress(PROGRESS_FIRST_CHUNK, f"生成进度 {PROGRESS_FIRST_CHUNK:.2f}%"), gr.update(visible=False), gr.update(visible=False)
                                    first_chunk_received = True
                                    last_progress = PROGRESS_FIRST_CHUNK
                                    last_update_time = current_time
                                    received_chunks = 0

                                # 检查是否是结束标记
                                if metadata.get('is_final', False):
                                    yield _update_progress(PROGRESS_RECEIVING_DONE, f"生成进度 {PROGRESS_RECEIVING_DONE:.2f}%"), gr.update(visible=False), gr.update(visible=False)
                                    break

                                # 更新本地计数器（用于估算）
                                received_chunks += 1

                                # 使用TTS模型返回的进度信息
                                total_chunks = metadata.get('total_chunks', -1)
                                server_progress = metadata.get('progress', -1)

                                if total_chunks > 0 and server_progress >= 0:
                                    # 服务端提供了准确的进度信息
                                    server_total_progress = 10 + (server_progress / 100) * 85
                                    server_total_progress = min(PROGRESS_RECEIVING_DONE, server_total_progress)

                                    chunk_index = metadata['chunk_index']
                                    is_last_chunk = (chunk_index == total_chunks - 1)

                                    # 只在进度显著变化或最后一个chunk时更新
                                    if abs(server_total_progress - last_progress) >= 1 or is_last_chunk:
                                        yield _update_progress(server_total_progress, f"生成进度 {server_total_progress:.2f}%"), gr.update(visible=False), gr.update(visible=False)
                                        last_progress = server_total_progress

                except requests.exceptions.ChunkedEncodingError:
                    if len(tts_audio) == 0:
                        yield gr.update(value=0, visible=False), gr.update(visible=False), gr.update(visible=True, value="### ❌ 接收数据时连接中断")
                        return
                except Exception as e:
                    if len(tts_audio) == 0:
                        yield gr.update(value=0, visible=False), gr.update(visible=False), gr.update(visible=True, value=f"### ❌ 接收音频数据失败 - {str(e)}")
                        return

                if len(tts_audio) == 0:
                    yield gr.update(value=0, visible=False), gr.update(visible=False), gr.update(visible=True, value="### ❌ 接收到的音频数据为空")
                    return

                # 步骤6: 转换音频数据
                yield _update_progress(PROGRESS_CONVERTING, f"生成进度 {PROGRESS_CONVERTING:.2f}%"), gr.update(visible=False), gr.update(visible=False)

                try:
                    audio_array = np.frombuffer(tts_audio, dtype=np.int16)
                except Exception as e:
                    yield gr.update(value=0, visible=False), gr.update(visible=False), gr.update(visible=True, value=f"### ❌ 音频数据转换失败 - {str(e)}")
                    return

                # 步骤7: 保存音频文件
                yield _update_progress(PROGRESS_SAVING, f"生成进度 {PROGRESS_SAVING:.2f}%"), gr.update(visible=False), gr.update(visible=False)

                output_path = os.path.join(tempfile.gettempdir(), 'generated_voice.wav')
                try:
                    with wave.open(output_path, 'wb') as wav_file:
                        wav_file.setnchannels(1)
                        wav_file.setsampwidth(2)
                        wav_file.setframerate(22050)
                        wav_file.writeframes(audio_array.tobytes())
                except Exception as e:
                    yield gr.update(value=0, visible=False), gr.update(visible=False), gr.update(visible=True, value=f"### ❌ 保存音频文件失败 - {str(e)}")
                    return

                # 完成（隐藏进度条，显示音频）
                yield gr.update(value=PROGRESS_DONE, visible=False, label=f"生成进度 {PROGRESS_DONE:.2f}%"), gr.update(value=output_path, visible=True), gr.update(visible=False)
            else:
                yield gr.update(value=0, visible=False), gr.update(visible=False), gr.update(visible=True, value=f"### ❌ API调用失败 - HTTP {response.status_code}")

        generate_btn.click(
            fn=handle_generate,
            inputs=[audio_upload, audio_mic, text_input, prompt_audio_text],
            outputs=[progress_bar, output_audio, output_error]
        )

    return app


def main():
    """主函数"""
    app = create_interface()

    # 自定义CSS样式 - 参照cv_gradio的专业配色方案
    custom_css = """
    /* 全局样式 */
    .gradio-container {
        font-family: "Inter", "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
        background-color: #ffffff !important;
        color: #1a1a2e !important;
        zoom: 1.25 !important;
    }

    /* 隐藏 Gradio 底部页脚 */
    footer {
        display: none !important;
    }

    .gradio-container footer:has(.footer) {
        display: none !important;
    }

    /* 标题字体优化 */
    h1, h2, h3, h4, h5, h6 {
        font-family: "Inter", "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
        color: #1a1a2e !important;
    }

    /* 主容器 */
    .main-container {
        background-color: #ffffff !important;
        box-shadow: none !important;
        padding: 16px !important;
        margin: 0 !important;
        border: none !important;
        max-width: 100% !important;
    }

    /* 去掉页面的边框和阴影 */
    body, .gradio-container, .gradio-container > div {
        border: none !important;
        box-shadow: none !important;
    }

    /* 确保所有交互元素可点击 */
    .gradio-container button,
    .gradio-container .gradio-audio button,
    .gradio-container input[type="button"] {
        pointer-events: auto !important;
        z-index: 100 !important;
        position: relative !important;
    }

    /* 标题样式 - 深蓝背景白色文字 */
    .app-title {
        text-align: left;
        color: #ffffff !important;
        font-size: 36px !important;
        font-weight: 900 !important;
        background-color: #091a31 !important;
        padding: 6px 16px !important;
        display: flex !important;
        align-items: center !important;
        min-height: 40px !important;
        margin-bottom: 8px !important;
    }

    .app-title h1,
    .app-title span,
    .app-title p {
        color: #ffffff !important;
    }

    /* 按钮样式 - 参照cv_gradio */
    .gr-button,
    .generate-button-inline {
        padding: 14px 24px !important;
        border: none !important;
        border-radius: 4px !important;
        font-size: 15px !important;
        font-weight: 500 !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        letter-spacing: 0.02em !important;
        min-height: 48px !important;
        background: #091a31 !important;
        color: #ffffff !important;
        border: 1px solid #0a2544 !important;
    }

    .gr-button:hover,
    .generate-button-inline:hover {
        background: #0a2544 !important;
        box-shadow: 0 2px 8px rgba(15, 52, 96, 0.25) !important;
    }

    .gr-button:active,
    .generate-button-inline:active {
        transform: translateY(1px) !important;
    }

    /* 生成按钮特殊样式 */
    .generate-button-inline {
        width: 100% !important;
        margin-top: 20px !important;
    }

    /* 生成按钮居中样式 */
    .generate-button-centered {
        width: 300px !important;
        margin: 24px auto 0 auto !important;
        display: block !important;
        background-color: #091a31 !important;
    }

    /* 生成按钮全宽样式 */
    .generate-button-full-width {
        width: 100% !important;
        margin: 0 !important;
        background-color: #091a31 !important;
    }

    /* Tab按钮样式 - 简洁风格 */
    .tab-nav {
        border-radius: 4px !important;
        overflow: hidden !important;
        background-color: #ffffff !important;
        border: 1px solid #d0d3d9 !important;
    }

    .tab-item {
        border-radius: 0 !important;
        padding: 12px 16px !important;
        transition: all 0.2s ease !important;
        background-color: transparent !important;
        color: #2c3e50 !important;
        border-right: 1px solid #e8eaed !important;
    }

    .tab-item:hover {
        background-color: #f8f9fb !important;
        color: #1a1a2e !important;
    }

    .tab-item.selected {
        background-color: #0f3460 !important;
        color: #ffffff !important;
        font-weight: 500 !important;
    }

    /* 输入区域样式 */
    .input-section {
        background: #f8f9fa !important;
        border: 1px solid #e9ecef !important;
        border-radius: 8px !important;
        padding: 16px !important;
        margin-bottom: 0 !important;
        box-shadow: none !important;
    }

    /* 输出区域样式 */
    .output-section {
        background: #f8f9fa !important;
        border: 1px solid #e9ecef !important;
        border-radius: 8px !important;
        padding: 16px !important;
        margin-top: 2px !important;
        box-shadow: none !important;
    }

    /* 移除主容器内所有行和列的额外间距 */
    .main-container > .gradio-column,
    .main-container > div > .gradio-column {
        gap: 2px !important;
    }

    .main-container .gradio-row,
    .main-container > div > .gradio-row {
        gap: 0 !important;
        margin-bottom: 0 !important;
    }

    /* 说明区域样式 */
    .instructions-section {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
    }

    /* 模块标题样式 */
    .module-title {
        margin-top: 0 !important;
        margin-bottom: 6px !important;
        padding-bottom: 0 !important;
        border-bottom: none !important;
        color: #2c3e50 !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
    }

    /* 间距样式 */
    .spacer-xs {
        min-height: 1px !important;
        height: 1px !important;
        margin: 0 !important;
        padding: 0 !important;
        display: block !important;
    }

    .spacer-sm {
        min-height: 8px !important;
        height: 8px !important;
    }

    .spacer-medium {
        min-height: 16px !important;
        height: 16px !important;
    }

    .spacer-large {
        min-height: 32px !important;
        height: 32px !important;
    }

    .spacer-xl {
        min-height: 40px !important;
        height: 40px !important;
    }

    /* 说明区域样式 - 简洁风格 */
    .instructions {
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
        border-radius: 0 !important;
        margin-top: 0 !important;
        box-shadow: none !important;
        font-size: 13px !important;
    }

    /* 输入文本列样式 - 让输入文本靠下对齐 */
    .input-text-column {
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-end !important;
    }

    .instructions h3 {
        margin-top: 0 !important;
        margin-bottom: 6px !important;
        font-size: 13px !important;
        color: #1a1a2e !important;
        border: none !important;
        padding: 0 !important;
        font-weight: 600 !important;
    }

    .instructions p {
        color: #2a2a3a !important;
        font-size: 13px !important;
        line-height: 1.5 !important;
        margin: 3px 0 !important;
        text-align: left !important;
        padding-left: 0 !important;
    }

    .instructions ul {
        list-style-type: disc !important;
        padding-left: 18px !important;
        margin: 3px 0 !important;
        text-align: left !important;
    }

    .instructions li {
        text-align: left !important;
        color: #2a2a3a !important;
        font-size: 13px !important;
        line-height: 1.5 !important;
        margin: 1px 0 !important;
    }

    .instructions strong {
        color: #0f3460 !important;
        font-weight: 600 !important;
    }

    /* 输入框样式 - 简洁风格 */
    input[type="text"],
    textarea,
    .gradio-textbox {
        background-color: #ffffff !important;
        border: 1px solid #d0d3d9 !important;
        border-radius: 4px !important;
        color: #2c3e50 !important;
        padding: 12px 14px !important;
        box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.03) !important;
    }

    input[type="text"]:focus,
    textarea:focus,
    .gradio-textbox:focus {
        border-color: #0f3460 !important;
        box-shadow: 0 0 0 2px rgba(15, 52, 96, 0.1) !important;
        background-color: #ffffff !important;
    }

    /* 状态信息框样式 */
    .status-box {
        min-height: 48px !important;
        background-color: #f0f4f8 !important;
        border: 1px solid #d0d8e0 !important;
        border-radius: 4px !important;
        padding: 10px 13px !important;
        font-size: 13px !important;
        color: #2a3a4a !important;
    }

    /* 全局文字颜色 */
    p, span, div {
        color: #2a2a3a !important;
    }

    label {
        color: #2c3e50 !important;
        font-weight: 500 !important;
        font-size: 14px !important;
    }

    /* 隐藏Gradio页脚 */
    .gradio-container .footer,
    .gradio-container > div:last-child {
        display: none !important;
    }

    /* 滚动条样式 */
    ::-webkit-scrollbar {
        width: 8px !important;
        height: 8px !important;
    }

    ::-webkit-scrollbar-track {
        background: #f1f1f1 !important;
        border-radius: 4px !important;
    }

    ::-webkit-scrollbar-thumb {
        background: #c1c1c1 !important;
        border-radius: 4px !important;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #a8a8a8 !important;
    }

    /* 音频组件样式 */
    .gradio-audio {
        border: 1px solid #d0d3d9 !important;
        border-radius: 4px !important;
        padding: 6px !important;
        background: #ffffff !important;
        min-height: 90px !important;
        max-height: 100px !important;
        box-sizing: border-box !important;
        overflow: visible !important;
    }

    /* 确保录音按钮可见和可点击 */
    .gradio-audio .record-button,
    .gradio-audio .stop-button,
    .gradio-audio button {
        display: inline-flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        cursor: pointer !important;
    }

    /* 录音按钮样式 */
    .gradio-audio .record-button {
        background-color: #dc2626 !important;
        color: #ffffff !important;
        border: none !important;
        padding: 8px 16px !important;
        border-radius: 4px !important;
    }

    .gradio-audio .record-button:hover {
        background-color: #b91c1c !important;
    }

    .gradio-audio .stop-button {
        background-color: #1a1a2e !important;
        color: #ffffff !important;
        border: none !important;
        padding: 8px 16px !important;
        border-radius: 4px !important;
    }

    .gradio-audio .stop-button:hover {
        background-color: #0f172a !important;
    }

    /* 确保按钮没有被禁用 */
    .gradio-audio button:disabled {
        opacity: 0.5 !important;
        cursor: not-allowed !important;
    }

    /* Tab内容固定高度 */
    .audio-tabs {
        min-height: auto !important;
        max-height: none !important;
        overflow: visible !important;
        height: auto !important;
    }

    /* Tab内容内部音频组件更小 */
    .audio-tabs .gradio-audio {
        min-height: auto !important;
        max-height: none !important;
        padding: 8px !important;
        overflow: visible !important;
        box-sizing: border-box !important;
        height: auto !important;
    }

    /* 滑块样式 */
    input[type="range"],
    .gradio-slider {
        accent-color: #0f3460 !important;
    }

    /* 错误消息样式 */
    .error-message {
        background-color: #fee2e2 !important;
        border: 1px solid #fecaca !important;
        border-left: 4px solid #ef4444 !important;
        border-radius: 4px !important;
        padding: 16px !important;
        margin: 0 !important;
        color: #991b1b !important;
    }

    .error-message h3 {
        color: #dc2626 !important;
        font-size: 16px !important;
        margin: 0 0 8px 0 !important;
        font-weight: 600 !important;
    }

    .error-message p {
        color: #991b1b !important;
        margin: 0 !important;
    }

    /* 隐藏进度条右边的数值显示和重置按钮 */
    .progress-slider .tab-like-container {
        display: none !important;
    }

    .progress-slider input[type="number"] {
        display: none !important;
    }

    .progress-slider .reset-button {
        display: none !important;
    }

    /* 针对所有gradio slider的通用隐藏 */
    .gradio-slider .tab-like-container {
        display: none !important;
    }
    """

    # 定义主题 - 参照cv_gradio配色
    theme = gr.themes.Base(
        primary_hue="blue",
        font=gr.themes.GoogleFont("Inter", "Noto Sans SC")
    ).set(
        # 背景色 - 浅灰白色
        background_fill_primary="#fafbfc",
        background_fill_secondary="#ffffff",
        # 边框色 - 浅灰
        border_color_primary="#d0d3d9",
        # 按钮颜色 - 深蓝
        button_primary_background_fill="#0f3460",
        button_primary_background_fill_hover="#0a2544",
        button_primary_text_color="#ffffff",
        button_primary_border_color="#0a2544",
        # 次要按钮
        button_secondary_background_fill="#ffffff",
        button_secondary_text_color="#0f3460",
        button_secondary_border_color="#d0d3d9",
        # 输入框
        block_background_fill="#ffffff",
        block_border_color="#d0d3d9",
        # 文字颜色
        body_text_color="#2c3e50",
        block_label_text_color="#2c3e50",
        block_title_text_color="#1a1a2e",
        # 阴影
        shadow_drop="0 1px 3px rgba(0, 0, 0, 0.05)",
        # 其他
        link_text_color="#0f3460",
        link_text_color_hover="#0a2544",
    )

    app.launch(
        server_name="127.0.0.1",
        server_port=7862,
        share=False,
        show_error=True,
        quiet=False,
        theme=theme,
        css=custom_css
    )


if __name__ == "__main__":
    main()
