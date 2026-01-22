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


class VoiceTTSGenerator:
    """语音生成器"""

    def __init__(self):
        """
        初始化语音生成器
        配置API端点和认证信息
        """
        self.api_endpoint = f"http://{API_HOST}:{API_PORT}/inference_{API_MODE}"
        self.model_name = "Fun-CosyVoice3-0.5B-2512"  # 模型名称
        self.prompt_text = PROMPT_TEXT  # prompt_text配置

    def generate_voice(
        self,
        reference_audio: str,
        text: str,
        prompt_audio_text: str = ""
    ) -> Tuple[str, str]:
        """
        根据参考音频和文本生成语音

        Args:
            reference_audio: 参考音频文件路径
            text: 要合成的文本内容
            prompt_audio_text: 参考音频对应的文本内容（可选）

        Returns:
            (生成的音频路径, 消息文本)
        """
        try:
            # 验证输入
            if not reference_audio:
                return None, "语音模型生成失败：请提供参考音频"

            if not text or text.strip() == "":
                return None, "语音模型生成失败：请输入要合成的文本"

            if not prompt_audio_text or prompt_audio_text.strip() == "":
                return None, "语音模型生成失败：请输入示例音频对应的文本内容"

            if len(text) > 1000:
                return None, "语音模型生成失败：文本长度超过1000字符限制"

            # 转换音频为WAV格式（如果需要）
            converter = AudioConverter()
            if not reference_audio.endswith('.wav'):
                reference_audio = converter.convert_to_wav(reference_audio)

            # 调用API生成语音（zero_shot模式）
            # 拼接prompt_text：将配置的PROMPT_TEXT与用户输入的示例音频文本拼接
            final_prompt_text = f"{self.prompt_text}{prompt_audio_text}"

            payload = {
                'tts_text': text,
                'prompt_text': final_prompt_text
            }

            # 打开文件
            try:
                with open(reference_audio, 'rb') as audio_file:
                    files = [
                        ('prompt_wav', ('prompt_wav', audio_file, 'application/octet-stream'))
                    ]

                    response = requests.request(
                        "GET",  # 使用GET方法，与client.py保持一致
                        self.api_endpoint,
                        data=payload,
                        files=files,
                        stream=True,
                        timeout=300  # 增加超时时间到300秒（5分钟）
                    )

            except FileNotFoundError:
                return None, f"语音模型生成失败：找不到音频文件 {reference_audio}"

            if response.status_code == 200:
                # 接收音频数据（处理分块传输）
                tts_audio = b''
                try:
                    # 使用iter_content处理分块传输的数据
                    for chunk in response.iter_content(chunk_size=8192, decode_unicode=False):
                        if chunk:  # 过滤掉keep-alive的空chunk
                            tts_audio += chunk
                except requests.exceptions.ChunkedEncodingError as e:
                    # 分块编码错误，但可能已经接收了部分数据
                    if len(tts_audio) > 0:
                        pass  # 尝试使用已接收的数据
                    else:
                        return None, f"语音模型生成失败：接收数据时连接中断 - {str(e)}"
                except Exception as e:
                    # 即使有异常，如果已经接收到数据，尝试使用
                    if len(tts_audio) > 0:
                        pass  # 尝试使用已接收的数据
                    else:
                        return None, f"语音模型生成失败：接收音频数据失败 - {str(e)}"

                # 检查数据是否有效
                if len(tts_audio) == 0:
                    return None, "语音模型生成失败：接收到的音频数据为空"

                # 将音频数据转换为int16数组
                try:
                    audio_array = np.frombuffer(tts_audio, dtype=np.int16)
                except Exception as e:
                    return None, f"语音模型生成失败：音频数据转换失败 - {str(e)}"

                # 使用wave模块保存音频
                output_path = os.path.join(tempfile.gettempdir(), 'generated_voice.wav')
                try:
                    with wave.open(output_path, 'wb') as wav_file:
                        wav_file.setnchannels(1)  # 单声道
                        wav_file.setsampwidth(2)  # 16-bit = 2 bytes
                        wav_file.setframerate(22050)  # 采样率 22050
                        wav_file.writeframes(audio_array.tobytes())
                except Exception as e:
                    return None, f"语音模型生成失败：保存音频文件失败 - {str(e)}"

                return output_path, "生成成功！"
            else:
                error_text = response.text
                return None, f"语音模型生成失败：API调用失败 - HTTP {response.status_code} - {error_text}"

        except requests.exceptions.ConnectionError as e:
            return None, f"语音模型生成失败：连接API失败 - {str(e)}"
        except requests.exceptions.Timeout as e:
            return None, f"语音模型生成失败：请求超时 - {str(e)}"
        except Exception as e:
            return None, f"语音模型生成失败：{str(e)}"


def create_interface() -> gr.Blocks:
    """创建Gradio界面"""

    # 初始化语音生成器
    generator = VoiceTTSGenerator()

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

                    # 步骤1: 参考音频输入
                    gr.Markdown("### 参考音频", elem_classes=["module-title"])

                    with gr.Row():
                        with gr.Column(scale=1):
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
                                        waveform_options=gr.WaveformOptions(
                                            waveform_color="#667eea",
                                            waveform_progress_color="#764ba2"
                                        )
                                    )

                        with gr.Column(scale=1):
                            # 步骤2: 示例音频文本输入框（必填）
                            gr.Markdown("### 示例音频文本", elem_classes=["module-title"])
                            prompt_audio_text = gr.Textbox(
                                label="示例音频文本内容 *",
                                placeholder="【必填】请输入上传的示例音频对应的文字内容",
                                lines=2,
                                max_lines=3
                            )

                    # 增加间距
                    gr.Markdown("", elem_classes=["spacer-xl"])

                    # 步骤3: 输入文本
                    gr.Markdown("### 输入文本", elem_classes=["module-title"])
                    text_input = gr.Textbox(
                        label="输入文本",
                        placeholder="请输入要合成的文字内容（建议1000字符以内）",
                        lines=4,
                        max_lines=6
                    )

                    # 步骤4: 生成按钮
                    gr.Markdown("### 生成", elem_classes=["module-title"])
                    generate_btn = gr.Button(
                        "生成语音",
                        variant="primary",
                        size="lg",
                        elem_classes=["generate-button-full-width"]
                    )

                # 增加间距
                gr.Markdown("", elem_classes=["spacer-medium"])

                # 下部：输出区域
                with gr.Row():
                    # 左列：输出结果
                    with gr.Column(scale=1, elem_classes=["output-section"]):
                        gr.Markdown("### 输出结果", elem_classes=["module-title"])

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

                    # 右列：使用说明
                    with gr.Column(scale=1, elem_classes=["instructions-section"]):
                        gr.Markdown(
                            """
                            ### 使用说明

                            **步骤说明:**
                            - 1. 参考音频 - 选择上传音频文件或使用麦克风录制
                            - 2. 填写示例音频文本 - 【必填】输入参考音频对应的文字内容
                            - 3. 输入文本 - 在文本框中输入要合成的文字内容
                            - 4. 生成语音 - 点击"生成语音"按钮开始合成

                            **注意事项:**
                            - 参考音频建议使用清晰、无背景噪音的语音
                            - 示例音频文本将自动与系统提示词拼接，帮助AI更好地学习声音特征
                            - 文本长度建议在 1000 字符以内
                            - 支持的音频格式: WAV, MP3, M4A
                            """,
                            elem_classes=["instructions"]
                        )

        # 绑定事件
        def handle_generate(audio_upload_file, audio_mic_file, text, prompt_audio_text_val):
            """处理生成请求"""
            # 优先使用上传的音频，如果没有则使用录制的音频
            reference_audio = audio_upload_file or audio_mic_file

            audio_path, message = generator.generate_voice(reference_audio, text, prompt_audio_text_val)

            # 如果生成失败（audio_path为None），隐藏音频，显示错误消息
            if audio_path is None:
                return (
                    gr.update(visible=False),  # 隐藏音频
                    gr.update(visible=True, value=f"### ❌ {message}")  # 显示错误
                )
            # 如果成功，显示音频，隐藏错误消息
            return (
                gr.update(value=audio_path, visible=True),  # 显示音频
                gr.update(visible=False)  # 隐藏错误消息
            )

        generate_btn.click(
            fn=handle_generate,
            inputs=[audio_upload, audio_mic, text_input, prompt_audio_text],
            outputs=[output_audio, output_error]
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
        padding: 24px !important;
        margin: 0 !important;
        border: none !important;
    }

    /* 去掉页面的边框和阴影 */
    body, .gradio-container, .gradio-container > div {
        border: none !important;
        box-shadow: none !important;
    }

    /* 标题样式 - 深蓝背景白色文字 */
    .app-title {
        text-align: left;
        color: #ffffff !important;
        font-size: 45px !important;
        font-weight: 900 !important;
        background-color: #091a31 !important;
        padding: 8px 24px !important;
        display: flex !important;
        align-items: center !important;
        min-height: 50px !important;
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
        padding: 20px !important;
        margin-bottom: 16px !important;
        box-shadow: none !important;
    }

    /* 输出区域样式 */
    .output-section {
        background: #f8f9fa !important;
        border: 1px solid #e9ecef !important;
        border-radius: 8px !important;
        padding: 20px !important;
        box-shadow: none !important;
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
        margin-top: 4px !important;
        margin-bottom: 4px !important;
        padding-bottom: 0 !important;
        border-bottom: none !important;
        color: #2c3e50 !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
    }

    /* 间距样式 */
    .spacer-medium {
        min-height: 16px !important;
        height: 16px !important;
    }

    .spacer-large {
        min-height: 32px !important;
        height: 32px !important;
    }

    .spacer-xl {
        min-height: 120px !important;
        height: 120px !important;
    }

    /* 说明区域样式 - 简洁风格 */
    .instructions {
        background-color: transparent !important;
        border: none !important;
        padding: 16px 0 !important;
        border-radius: 0 !important;
        margin-top: 0 !important;
        box-shadow: none !important;
    }

    .instructions h3 {
        margin-top: 0 !important;
        margin-bottom: 12px !important;
        font-size: 14px !important;
        color: #1a1a2e !important;
        border: none !important;
        padding: 0 !important;
        font-weight: 600 !important;
    }

    .instructions p,
    .instructions li {
        color: #2a2a3a !important;
        font-size: 14px !important;
        line-height: 1.7 !important;
        margin: 6px 0 !important;
        text-align: left !important;
        padding-left: 0 !important;
    }

    .instructions strong {
        color: #0f3460 !important;
        font-weight: 600 !important;
    }

    /* 去掉列表前的圆点 */
    .instructions ul {
        list-style-type: none !important;
        padding-left: 0 !important;
        margin-left: 0 !important;
        text-align: left !important;
    }

    .instructions li {
        text-align: left !important;
        padding-left: 0 !important;
        margin-left: 0 !important;
        display: block !important;
        width: 100% !important;
    }

    .instructions li::marker {
        content: "" !important;
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
        padding: 8px !important;
        background: #ffffff !important;
        min-height: 80px !important;
        max-height: 80px !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
    }

    /* Tab内容固定高度 */
    .audio-tabs {
        min-height: 140px !important;
        max-height: 140px !important;
        overflow: visible !important;
    }

    /* Tab内容内部音频组件更小 */
    .audio-tabs .gradio-audio {
        min-height: 80px !important;
        max-height: 80px !important;
        padding: 6px !important;
        overflow: visible !important;
        box-sizing: border-box !important;
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
