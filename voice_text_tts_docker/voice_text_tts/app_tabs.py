"""
语音生成功能 - Gradio应用（使用Tabs架构）
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
from config import API_HOST, API_PORT, API_MODE, PROMPT_TEXT, ASR_ENABLED, ASR_BACKEND_TYPE, ASR_BACKEND_CONFIG, MAX_TEXT_LENGTH, SERVER_NAME, SERVER_PORT
from asr_client import transcribe_audio_sync


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
                pass

            # 使用ffmpy转换为WAV格式
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
            print(f"音频转换警告: {str(e)}")
            return input_path


def create_interface() -> gr.Blocks:
    """创建Gradio界面 - 使用Tabs架构"""

    with gr.Blocks(title="语音生成功能") as app:

        # 主容器
        with gr.Column(elem_classes=["main-container"]):
            # 标题
            gr.Markdown(
                "# <span style='color: #ffffff;'>语音生成功能</span>",
                elem_classes=["app-title"]
            )

            # 步骤指示器 - 横向显示所有步骤
            with gr.Row(elem_classes=["steps-nav"]):
                step1_indicator = gr.Markdown(
                    '<div class="step-item active"><span class="step-number">1</span><span class="step-label">上传参考音频</span></div>',
                    elem_classes=["step-nav-item"]
                )
                step2_indicator = gr.Markdown(
                    '<div class="step-item"><span class="step-number">2</span><span class="step-label">输入音频文本</span></div>',
                    elem_classes=["step-nav-item"]
                )
                step3_indicator = gr.Markdown(
                    '<div class="step-item"><span class="step-number">3</span><span class="step-label">输入合成文本</span></div>',
                    elem_classes=["step-nav-item"]
                )
                step4_indicator = gr.Markdown(
                    '<div class="step-item"><span class="step-number">4</span><span class="step-label">生成语音</span></div>',
                    elem_classes=["step-nav-item"]
                )

            # 使用Tabs来管理步骤，隐藏Tab标签
            with gr.Tabs(selected=0, elem_classes=["hidden-tabs"]) as tabs:
                # ==================== 步骤1：上传参考音频 ====================
                with gr.Tab("步骤1", elem_id="step1_tab"):
                    with gr.Column(elem_classes=["step-container"]):
                        gr.Markdown("### 请上传参考音频或使用麦克风录制", elem_classes=["step-title"])

                        with gr.Tabs(elem_classes=["audio-tabs"]):
                            with gr.Tab("上传音频"):
                                audio_upload = gr.Audio(
                                    label="上传参考音频（限30秒内）",
                                    type="filepath",
                                    sources=["upload"],
                                    waveform_options=gr.WaveformOptions(
                                        waveform_color="#667eea",
                                        waveform_progress_color="#764ba2"
                                    )
                                )

                            with gr.Tab("录制音频"):
                                audio_mic = gr.Audio(
                                    label="麦克风录制（限30秒内）",
                                    type="filepath",
                                    sources=["microphone"],
                                    interactive=True,
                                    waveform_options=gr.WaveformOptions(
                                        waveform_color="#667eea",
                                        waveform_progress_color="#764ba2"
                                    )
                                )

                        # 说明
                        gr.Markdown("""
                        **提示：**
                        - 支持的音频格式: WAV, MP3, M4A
                        - 音频时长限制在30秒以内
                        - 建议使用清晰、无背景噪音的语音
                        - 上传或录制完成后，可点击"下一步"继续
                        """, elem_classes=["instructions"])

                        # 导航按钮
                        with gr.Row(elem_classes=["nav-buttons"]):
                            step1_next = gr.Button("下一步", variant="primary", size="lg", interactive=False)

                # ==================== 步骤2：输入参考音频文本 ====================
                with gr.Tab("步骤2", elem_id="step2_tab"):
                    with gr.Column(elem_classes=["step-container"]):
                        gr.Markdown("### 请输入参考音频对应的文字内容", elem_classes=["step-title"])

                        # 显示已上传的音频（只读）
                        step2_audio_display = gr.Audio(
                            label="已上传的参考音频",
                            type="filepath",
                            interactive=False,
                            waveform_options=gr.WaveformOptions(
                                waveform_color="#667eea",
                                waveform_progress_color="#764ba2"
                            )
                        )

                        # 参考音频文本输入
                        prompt_audio_text = gr.Textbox(
                            label="参考音频文本内容 *",
                            placeholder="请输入上传的参考音频对应的文字内容，或点击下方按钮自动识别",
                            lines=6,
                            max_lines=10
                        )

                        # ASR和清空按钮
                        with gr.Row():
                            if ASR_ENABLED:
                                asr_btn = gr.Button("提取音频文字", variant="secondary", size="sm", scale=3)
                            else:
                                asr_btn = gr.Button("提取音频文字", variant="secondary", size="sm", scale=3, visible=False)
                            clear_prompt_btn = gr.Button("清空", variant="secondary", size="sm", scale=1)

                        # 说明
                        if ASR_ENABLED:
                            step2_info = """
                            **提示：**
                            - 您可以手动输入文字内容，或点击"提取音频文字"按钮自动识别
                            - ASR识别后，您可以查看并修改识别结果
                            - 此文本将用于帮助AI学习声音特征
                            """
                        else:
                            step2_info = """
                            **提示：**
                            - 请手动输入参考音频对应的文字内容
                            - 此文本将用于帮助AI学习声音特征
                            """
                        gr.Markdown(step2_info, elem_classes=["instructions"])

                        # 导航按钮
                        with gr.Row(elem_classes=["nav-buttons"]):
                            step2_prev = gr.Button("上一步", variant="secondary", size="lg")
                            step2_next = gr.Button("下一步", variant="primary", size="lg", interactive=False)

                # ==================== 步骤3：输入要合成的文本 ====================
                with gr.Tab("步骤3", elem_id="step3_tab"):
                    with gr.Column(elem_classes=["step-container"]):
                        gr.Markdown("### 请输入要合成的文字内容", elem_classes=["step-title"])

                        # 已完成的步骤摘要
                        step3_summary = gr.Markdown("", elem_classes=["summary-text"])

                        # 输入文本
                        text_input = gr.Textbox(
                            label=f"输入文本（建议{MAX_TEXT_LENGTH}字符以内）",
                            placeholder="请输入要合成的文字内容",
                            lines=8,
                            max_lines=15
                        )

                        clear_text_btn = gr.Button("清空", variant="secondary", size="sm")

                        # 说明
                        gr.Markdown(f"""
                        **提示：**
                        - 文本长度建议在 {MAX_TEXT_LENGTH} 字符以内
                        - 输入完成后，点击"下一步"进入生成步骤
                        """, elem_classes=["instructions"])

                        # 导航按钮
                        with gr.Row(elem_classes=["nav-buttons"]):
                            step3_prev = gr.Button("上一步", variant="secondary", size="lg")
                            step3_next = gr.Button("下一步", variant="primary", size="lg", interactive=False)

                # ==================== 步骤4：生成语音 ====================
                with gr.Tab("步骤4", elem_id="step4_tab"):
                    with gr.Column(elem_classes=["step-container"]):
                        gr.Markdown("### 生成语音", elem_classes=["step-title"])

                        # 所有输入的摘要
                        step4_summary = gr.Markdown("", elem_classes=["summary-text"])

                        # 生成按钮
                        generate_btn = gr.Button(
                            "生成语音",
                            variant="primary",
                            size="lg",
                            elem_classes=["generate-button-large"]
                        )

                        # 进度条（默认隐藏）
                        progress_bar = gr.Slider(
                            label="生成进度 0.00%",
                            value=0,
                            minimum=0,
                            maximum=100,
                            step=0.01,
                            visible=False,
                            interactive=False,
                            elem_classes=["progress-slider"]
                        )

                        # 输出区域
                        with gr.Column(elem_classes=["output-section"]):
                            gr.Markdown("### 输出结果", elem_classes=["module-title"])

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

                        # 导航按钮
                        with gr.Row(elem_classes=["nav-buttons"]):
                            step4_prev = gr.Button("上一步", variant="secondary", size="lg")
                            step4_restart = gr.Button("重新开始", variant="secondary", size="lg")

        # 导航逻辑 - 更新指示器并切换标签页
        def go_to_step(step_num, audio_upload_file=None, audio_mic_file=None, prompt_text=None, text=None):
            """统一的步骤切换函数"""
            # 更新步骤指示器
            indicators = []
            for i in range(1, 5):
                if i < step_num:
                    indicators.append(gr.update(value=f'<div class="step-item completed"><span class="step-number">{i}</span><span class="step-label">{["上传参考音频", "输入音频文本", "输入合成文本", "生成语音"][i-1]}</span></div>'))
                elif i == step_num:
                    indicators.append(gr.update(value=f'<div class="step-item active"><span class="step-number">{i}</span><span class="step-label">{["上传参考音频", "输入音频文本", "输入合成文本", "生成语音"][i-1]}</span></div>'))
                else:
                    indicators.append(gr.update(value=f'<div class="step-item"><span class="step-number">{i}</span><span class="step-label">{["上传参考音频", "输入音频文本", "输入合成文本", "生成语音"][i-1]}</span></div>'))

            result = indicators + [gr.Tabs(selected=step_num-1)]  # 切换到对应的Tab

            # 根据步骤添加额外的更新
            if step_num == 2 and (audio_upload_file or audio_mic_file):
                reference_audio = audio_upload_file or audio_mic_file
                result.append(gr.update(value=reference_audio))
            elif step_num == 3 and prompt_text:
                reference_audio = audio_upload_file or audio_mic_file
                audio_name = reference_audio.split("/")[-1] if reference_audio else "未知"
                summary = f"""
**已完成的步骤：**

**✓ 已上传参考音频：** {audio_name}

**✓ 参考音频文本：** {prompt_text[:100]}{"..." if len(prompt_text) > 100 else ""}
                """
                result.append(gr.update(value=summary))
            elif step_num == 4 and text:
                reference_audio = audio_upload_file or audio_mic_file
                audio_name = reference_audio.split("/")[-1] if reference_audio else "未知"
                summary = f"""
**输入信息摘要：**

**✓ 参考音频：** {audio_name}

**✓ 参考音频文本：** {prompt_text[:100]}{"..." if len(prompt_text) > 100 else ""}

**✓ 要合成的文本：** {text[:200]}{"..." if len(text) > 200 else ""}
                """
                result.append(gr.update(value=summary))
                result.append(gr.update(value=None))  # output_audio
                result.append(gr.update(visible=False))  # output_error

            return tuple(result)

        # 验证函数
        def validate_step1(audio_upload_file, audio_mic_file):
            return gr.update(interactive=bool(audio_upload_file or audio_mic_file))

        def validate_step2(prompt_text):
            return gr.update(interactive=bool(prompt_text and prompt_text.strip()))

        def validate_step3(text):
            is_valid = bool(text and text.strip() and len(text) <= MAX_TEXT_LENGTH)
            return gr.update(interactive=is_valid)

        # ASR提取
        def handle_asr_extract(audio_upload_file, audio_mic_file):
            reference_audio = audio_upload_file or audio_mic_file
            if not reference_audio:
                return "错误：请先上传或录制参考音频"
            if not ASR_ENABLED:
                return "错误：ASR功能未启用。"
            try:
                backend_config = ASR_BACKEND_CONFIG.get(ASR_BACKEND_TYPE, {})
                result = transcribe_audio_sync(reference_audio, backend_type=ASR_BACKEND_TYPE, **backend_config)
                if result and result.strip():
                    return result.strip()
                else:
                    return "识别失败：ASR服务返回空结果。"
            except Exception as e:
                return f"识别出错：{str(e)}"

        # 生成函数（简化版，使用原有逻辑）
        # ... 这里应该包含完整的handle_generate函数

        # 事件绑定
        audio_upload.change(validate_step1, [audio_upload, audio_mic], [step1_next])
        audio_mic.change(validate_step1, [audio_upload, audio_mic], [step1_next])

        step1_next.click(
            lambda a, m: go_to_step(2, a, m),
            [audio_upload, audio_mic],
            [step1_indicator, step2_indicator, step3_indicator, step4_indicator, tabs, step2_audio_display]
        )

        prompt_audio_text.change(validate_step2, [prompt_audio_text], [step2_next])
        clear_prompt_btn.click(lambda: "", outputs=[prompt_audio_text])

        step2_prev.click(
            lambda: go_to_step(1),
            outputs=[step1_indicator, step2_indicator, step3_indicator, step4_indicator, tabs]
        )
        step2_next.click(
            lambda a, m, p: go_to_step(3, a, m, p),
            [audio_upload, audio_mic, prompt_audio_text],
            [step1_indicator, step2_indicator, step3_indicator, step4_indicator, tabs, step3_summary]
        )

        text_input.change(validate_step3, [text_input], [step3_next])
        clear_text_btn.click(lambda: "", outputs=[text_input])

        step3_prev.click(
            lambda a, m: go_to_step(2, a, m),
            [audio_upload, audio_mic],
            [step1_indicator, step2_indicator, step3_indicator, step4_indicator, tabs, step2_audio_display]
        )
        step3_next.click(
            lambda a, m, p, t: go_to_step(4, a, m, p, t),
            [audio_upload, audio_mic, prompt_audio_text, text_input],
            [step1_indicator, step2_indicator, step3_indicator, step4_indicator, tabs, step4_summary, output_audio, output_error]
        )

        step4_prev.click(
            lambda a, m, p: go_to_step(3, a, m, p),
            [audio_upload, audio_mic, prompt_audio_text],
            [step1_indicator, step2_indicator, step3_indicator, step4_indicator, tabs, step3_summary]
        )
        step4_restart.click(
            lambda: go_to_step(1) + (None, None, "", "", None, gr.update(visible=False), gr.update(value=0, visible=False)),
            outputs=[step1_indicator, step2_indicator, step3_indicator, step4_indicator, tabs, audio_upload, audio_mic, prompt_audio_text, text_input, output_audio, output_error, progress_bar]
        )

        if ASR_ENABLED:
            asr_btn.click(handle_asr_extract, [audio_upload, audio_mic], [prompt_audio_text])

    return app
