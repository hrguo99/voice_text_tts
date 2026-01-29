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
import shutil
from datetime import datetime
from typing import Optional, Tuple, List, Dict
from ffmpy import FFmpeg
from config import API_HOST, API_PORT, API_MODE, PROMPT_TEXT, ASR_ENABLED, ASR_BACKEND_TYPE, ASR_BACKEND_CONFIG, MAX_TEXT_LENGTH, SERVER_NAME, SERVER_PORT, PRESETS_DIR
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


class VoicePresetManager:
    """音色预设管理器"""

    def __init__(self):
        """初始化预设管理器"""
        # 确定预设保存目录
        if PRESETS_DIR:
            # 使用配置文件中指定的路径
            self.presets_dir = PRESETS_DIR
        else:
            # 使用系统临时目录
            self.presets_dir = os.path.join(tempfile.gettempdir(), 'voice_presets')

        # 创建预设目录和音频文件目录
        os.makedirs(self.presets_dir, exist_ok=True)
        self.presets_file = os.path.join(self.presets_dir, 'presets.json')
        self.audio_dir = os.path.join(self.presets_dir, 'audio_files')
        os.makedirs(self.audio_dir, exist_ok=True)

        print(f"预设保存路径: {self.presets_dir}")  # 打印预设保存路径，方便调试
        self.presets = self._load_presets()

    def _load_presets(self) -> List[Dict]:
        """从文件加载预设"""
        if os.path.exists(self.presets_file):
            try:
                with open(self.presets_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载预设失败: {e}")
                return []
        return []

    def _save_presets(self):
        """保存预设到文件"""
        try:
            with open(self.presets_file, 'w', encoding='utf-8') as f:
                json.dump(self.presets, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存预设失败: {e}")

    def add_preset(self, name: str, audio_path: str, prompt_text: str) -> Dict:
        """添加新的音色预设

        Args:
            name: 预设名称
            audio_path: 音频文件路径
            prompt_text: 参考音频文本

        Returns:
            新创建的预设字典
        """
        # 生成唯一ID
        preset_id = f"preset_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 复制音频文件到预设目录
        audio_ext = os.path.splitext(audio_path)[1]
        saved_audio_path = os.path.join(self.audio_dir, f"{preset_id}{audio_ext}")

        try:
            shutil.copy2(audio_path, saved_audio_path)
        except Exception as e:
            print(f"复制音频文件失败: {e}")
            return None

        # 创建预设
        preset = {
            'id': preset_id,
            'name': name,
            'audio_path': saved_audio_path,
            'prompt_text': prompt_text,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        self.presets.append(preset)
        self._save_presets()

        return preset

    def delete_preset(self, preset_id: str) -> bool:
        """删除预设

        Args:
            preset_id: 预设ID

        Returns:
            是否删除成功
        """
        # 查找预设
        preset = next((p for p in self.presets if p['id'] == preset_id), None)
        if not preset:
            return False

        # 删除音频文件
        try:
            if os.path.exists(preset['audio_path']):
                os.remove(preset['audio_path'])
        except Exception as e:
            print(f"删除音频文件失败: {e}")

        # 从列表中移除
        self.presets = [p for p in self.presets if p['id'] != preset_id]
        self._save_presets()

        return True

    def get_presets(self) -> List[Dict]:
        """获取所有预设"""
        return self.presets.copy()

    def get_preset(self, preset_id: str) -> Optional[Dict]:
        """根据ID获取预设"""
        return next((p for p in self.presets if p['id'] == preset_id), None)

    def get_presets_display(self) -> str:
        """获取预设的显示文本（用于gradio显示）"""
        if not self.presets:
            return "暂无保存的音色预设"

        display_lines = []
        for i, preset in enumerate(self.presets, 1):
            display_lines.append(
                f"{i}. **{preset['name']}** ({preset['created_at']})\n"
                f"   文本: {preset['prompt_text'][:50]}{'...' if len(preset['prompt_text']) > 50 else ''}\n"
            )

        return "\n".join(display_lines)

    def get_preset_choices(self) -> List[str]:
        """获取预设选择列表（用于gradio下拉框）"""
        if not self.presets:
            return []

        return [f"{p['name']} ({p['created_at']})" for p in self.presets]


# 创建全局预设管理器实例
preset_manager = VoicePresetManager()


def create_interface() -> gr.Blocks:
    """创建Gradio界面"""

    # 创建界面
    with gr.Blocks(title="智能语音克隆演示系统") as app:

        # 主容器
        with gr.Column(elem_classes=["main-container"]):
            # 标题
            gr.Markdown(
                "# <span style='color: #ffffff;'>智能语音克隆演示系统</span>",
                elem_classes=["app-title"]
            )

            # 步骤指示器 - 横向显示所有步骤（3步）
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
                    '<div class="step-item"><span class="step-number">3</span><span class="step-label">生成语音</span></div>',
                    elem_classes=["step-nav-item"]
                )

            # ==================== 步骤1：上传参考音频 ====================
            with gr.Column(visible=True, elem_classes=["step-container"]) as step1_container:
                gr.Markdown("### 请上传参考音频或使用麦克风录制", elem_classes=["step-title"])

                with gr.Tabs(elem_classes=["audio-tabs"]):
                    with gr.Tab("上传音频"):
                        audio_upload = gr.Audio(
                            label="上传参考音频（建议3-30秒，超30秒需裁剪）",
                            type="filepath",
                            sources=["upload"],
                            interactive=True,
                            waveform_options=gr.WaveformOptions(
                                waveform_color="#667eea",
                                waveform_progress_color="#764ba2"
                            )
                        )

                    with gr.Tab("录制音频"):
                        audio_mic = gr.Audio(
                            label="麦克风录制（建议3-30秒，超30秒需裁剪）",
                            type="filepath",
                            sources=["microphone"],
                            interactive=True,
                            waveform_options=gr.WaveformOptions(
                                waveform_color="#667eea",
                                waveform_progress_color="#764ba2"
                            )
                        )

                # 音频时长提示（只在需要时显示）
                audio_trim_warning = gr.Markdown("", visible=False, elem_classes=["trim-warning"])

                # 说明
                gr.Markdown("""
                **提示：**
                - 支持的音频格式: WAV, MP3, M4A
                - 建议音频时长: 3-30秒
                - 如果音频超过30秒，请使用播放器下方的编辑/裁剪功能进行裁剪
                - 裁剪完成后点击播放器右下角"Trim"，然后点击"下一步"继续
                - 建议使用清晰、无背景噪音的语音
                """, elem_classes=["instructions"])

                # 音色预设区域
                # 标题（始终创建，但根据预设状态设置可见性）
                preset_title = gr.Markdown("### 已保存的音色预设", elem_classes=["module-title"], visible=False)

                # 预设列表
                with gr.Row() as preset_list_row:
                    preset_list = gr.Markdown(
                        "",
                        elem_classes=["preset-list"],
                        visible=False
                    )

                # 下拉框和按钮
                with gr.Row() as preset_control_row:
                    load_preset_dropdown = gr.Dropdown(
                        label="选择音色预设",
                        choices=[],
                        value=None,
                        interactive=True,
                        scale=2,
                        visible=False
                    )
                    load_preset_btn = gr.Button("加载预设", variant="primary", size="sm", scale=1, visible=False, interactive=False)
                    delete_preset_btn = gr.Button("删除预设", variant="stop", size="sm", scale=1, visible=False, interactive=False)

                # 状态消息和分隔符
                preset_load_status = gr.Markdown("", visible=False, elem_classes=["instructions"])
                preset_divider = gr.Markdown("---", elem_classes=["divider"], visible=False)

                # 如果启动时有预设，显示预设区域
                if preset_manager.get_presets():
                    preset_title.value = "### 已保存的音色预设"
                    preset_title.visible = True
                    preset_list.value = preset_manager.get_presets_display()
                    preset_list.visible = True
                    load_preset_dropdown.choices = preset_manager.get_preset_choices()
                    load_preset_dropdown.visible = True
                    load_preset_btn.visible = True
                    delete_preset_btn.visible = True
                    preset_divider.visible = True

                # 导航按钮
                with gr.Row(elem_classes=["nav-buttons"]):
                    step1_next = gr.Button("下一步", variant="primary", size="lg", interactive=False)

            # ==================== 步骤2：输入参考音频文本 ====================
            with gr.Column(visible=False, elem_classes=["step-container"]) as step2_container:
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

                # 参考音频文本输入 - 根据ASR是否启用设置不同的placeholder
                if ASR_ENABLED:
                    prompt_placeholder = "请输入上传的参考音频对应的文字内容，或点击下方按钮自动识别"
                else:
                    prompt_placeholder = "请输入上传的参考音频对应的文字内容"

                prompt_audio_text = gr.Textbox(
                    label="参考音频文本内容 *",
                    placeholder=prompt_placeholder,
                    lines=6,
                    max_lines=10
                )

                # ASR和清空按钮
                with gr.Row():
                    if ASR_ENABLED:
                        asr_btn = gr.Button(
                            "提取音频文字",
                            variant="secondary",
                            size="sm",
                            scale=3
                        )
                    else:
                        asr_btn = gr.Button(
                            "提取音频文字",
                            variant="secondary",
                            size="sm",
                            scale=3,
                            visible=False
                        )
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

                # 保存预设区域
                gr.Markdown("---", elem_classes=["divider"])
                gr.Markdown("### 保存当前音色为预设", elem_classes=["module-title"])
                with gr.Row():
                    preset_name_input = gr.Textbox(
                        label="预设名称（可选）",
                        placeholder="不填则使用默认名称",
                        scale=2,
                        max_lines=1
                    )
                    save_preset_btn = gr.Button("保存预设", variant="primary", size="sm", scale=1, interactive=False)
                preset_save_status = gr.Markdown("", visible=False, elem_classes=["instructions"])
                gr.Markdown("""
**提示：**
- 保存后可在步骤1快速加载此音色预设
""", elem_classes=["instructions"])

                # 导航按钮
                with gr.Row(elem_classes=["nav-buttons"]):
                    step2_prev = gr.Button("上一步", variant="secondary", size="lg")
                    step2_next = gr.Button("下一步", variant="primary", size="lg", interactive=False)

            # ==================== 步骤3：输入文本并生成语音 ====================
            with gr.Column(visible=False, elem_classes=["step-container"]) as step3_container:
                gr.Markdown("### 请输入要合成的文字内容并生成语音", elem_classes=["step-title"])

                # 已完成的步骤摘要
                step3_summary = gr.Markdown("", elem_classes=["summary-text", "step3-summary"], visible=False)

                # 输入文本区域
                with gr.Row():
                    with gr.Column(scale=1):
                        text_input = gr.Textbox(
                            label=f"输入文本（建议{MAX_TEXT_LENGTH}字符以内）",
                            placeholder="请输入要合成的文字内容",
                            lines=10,
                            max_lines=15
                        )

                        # 清空和生成按钮行
                        with gr.Row():
                            clear_text_btn = gr.Button("清空文本", variant="secondary", size="sm")
                            generate_btn = gr.Button("生成语音", variant="primary", size="lg", scale=2, interactive=False)

                # 说明
                gr.Markdown(f"""
                **提示：**
                - 文本长度建议在 {MAX_TEXT_LENGTH} 字符以内
                - 点击"生成语音"按钮开始生成
                - 生成完成后，可以继续输入新的文本并再次生成，无需重新上传参考音频
                - 点击"重新开始"可以更换参考音频
                """, elem_classes=["instructions"])

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
                        visible=False,
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
                    step3_prev = gr.Button("上一步", variant="secondary", size="lg")
                    step3_restart = gr.Button("重新开始", variant="secondary", size="lg")

        # ==================== 事件处理函数 ====================

        # 步骤导航函数
        def go_to_step1():
            """返回步骤1"""
            has_presets = preset_manager.get_presets()

            updates = [
                gr.update(value='<div class="step-item active"><span class="step-number">1</span><span class="step-label">上传参考音频</span></div>'),  # step1_indicator
                gr.update(value='<div class="step-item"><span class="step-number">2</span><span class="step-label">输入音频文本</span></div>'),  # step2_indicator
                gr.update(value='<div class="step-item"><span class="step-number">3</span><span class="step-label">生成语音</span></div>'),  # step3_indicator
                gr.update(visible=True),   # step1_container
                gr.update(visible=False),  # step2_container
                gr.update(visible=False),  # step3_container
                gr.update(value="", visible=False),  # step3_summary (清空并隐藏)
                gr.update(value=None),     # output_audio (清空)
                gr.update(visible=False),  # output_error
                gr.update(value=0, visible=False, label="生成进度 0.00%"),  # progress_bar
                gr.update(visible=False, value=""),  # audio_trim_warning (隐藏警告框)
                gr.update(visible=False, value=""),  # preset_save_status (隐藏保存状态)
                # 预设相关组件
                gr.update(value=preset_manager.get_presets_display() if has_presets else "", visible=has_presets),  # preset_list
                gr.update(choices=preset_manager.get_preset_choices() if has_presets else [], value=None, visible=has_presets),  # load_preset_dropdown (重置选择)
                gr.update(visible=has_presets, interactive=False),  # load_preset_btn (禁用)
                gr.update(visible=has_presets, interactive=False),  # delete_preset_btn (禁用)
                gr.update(visible=False, value=""),  # preset_load_status
                gr.update(visible=has_presets),  # preset_title
                gr.update(visible=has_presets),  # preset_divider
            ]

            return tuple(updates)

        def go_to_step2(audio_upload_file, audio_mic_file):
            """进入步骤2"""
            reference_audio = audio_upload_file or audio_mic_file

            # 基础更新列表
            updates = [
                gr.update(value='<div class="step-item completed"><span class="step-number">1</span><span class="step-label">上传参考音频</span></div>'),  # step1_indicator
                gr.update(value='<div class="step-item active"><span class="step-number">2</span><span class="step-label">输入音频文本</span></div>'),  # step2_indicator
                gr.update(value='<div class="step-item"><span class="step-number">3</span><span class="step-label">生成语音</span></div>'),  # step3_indicator
                gr.update(visible=False),  # step1_container
                gr.update(visible=True),   # step2_container
                gr.update(visible=False),  # step3_container
                gr.update(value=reference_audio),  # step2_audio_display
                gr.update(value="", visible=False),  # step3_summary (清空并隐藏)
                gr.update(value=None),     # output_audio (清空)
                gr.update(visible=False),  # output_error
                gr.update(value=0, visible=False, label="生成进度 0.00%"),  # progress_bar
                gr.update(visible=False, value=""),  # audio_trim_warning (隐藏警告框)
                gr.update(visible=False, value=""),  # preset_save_status (隐藏保存状态)
                gr.update(interactive=False),  # save_preset_btn (初始禁用，等输入文本后启用)
            ]

            # 如果有预设，添加预设加载状态的更新
            if preset_manager.get_presets():
                updates.append(gr.update(visible=False, value=""))  # preset_load_status

            return tuple(updates)

        def go_to_step3(audio_upload_file, audio_mic_file, prompt_text):
            """进入步骤3"""
            reference_audio = audio_upload_file or audio_mic_file
            audio_name = reference_audio.split("/")[-1] if reference_audio else "未知"

            summary = f"""
**参考信息：**

**✓ 已上传参考音频：** {audio_name}

**✓ 参考音频文本：** {prompt_text[:100]}{"..." if len(prompt_text) > 100 else ""}
            """

            # 基础更新列表
            updates = [
                gr.update(value='<div class="step-item completed"><span class="step-number">1</span><span class="step-label">上传参考音频</span></div>'),  # step1_indicator
                gr.update(value='<div class="step-item completed"><span class="step-number">2</span><span class="step-label">输入音频文本</span></div>'),  # step2_indicator
                gr.update(value='<div class="step-item active"><span class="step-number">3</span><span class="step-label">生成语音</span></div>'),  # step3_indicator
                gr.update(visible=False),  # step1_container
                gr.update(visible=False),  # step2_container
                gr.update(visible=True),   # step3_container
                gr.update(value=summary, visible=True),  # step3_summary (显示)
                gr.update(value=None),     # output_audio (清空之前的输出)
                gr.update(visible=False),  # output_error
                gr.update(value=0, visible=False, label="生成进度 0.00%"),  # progress_bar
                gr.update(visible=False, value=""),  # audio_trim_warning (隐藏警告框)
                gr.update(visible=False, value=""),  # preset_save_status (隐藏保存状态)
            ]

            # 如果有预设，添加预设加载状态的更新
            if preset_manager.get_presets():
                updates.append(gr.update(visible=False, value=""))  # preset_load_status

            return tuple(updates)

        # 输入验证函数
        def validate_step1(audio_upload_file, audio_mic_file):
            """验证步骤1：检查是否上传了音频，并验证时长"""
            import wave
            import contextlib

            reference_audio = audio_upload_file or audio_mic_file

            if not reference_audio:
                # 没有音频
                return gr.update(interactive=False), gr.update(visible=False, value="")

            # 获取音频时长
            duration = None
            try:
                # 尝试用wave读取（适用于WAV文件）
                with contextlib.closing(wave.open(reference_audio, 'r')) as f:
                    frames = f.getnframes()
                    rate = f.getframerate()
                    duration = frames / float(rate)
            except:
                # 如果不是WAV格式，尝试用pydub
                try:
                    from pydub import AudioSegment
                    audio = AudioSegment.from_file(reference_audio)
                    duration = len(audio) / 1000.0  # 毫秒转秒
                except:
                    # 无法获取时长，允许继续（在生成时会再次验证）
                    return gr.update(interactive=True), gr.update(visible=False, value="")

            if duration is not None:
                if duration < 3:
                    warning_text = f"### ⚠️ 音频时长不足3秒（当前：{duration:.1f}秒）\n\n**请上传或录制3-30秒的音频**"
                    return gr.update(interactive=False), gr.update(visible=True, value=warning_text)
                elif duration > 30:
                    warning_text = f"""### ⚠️ 音频时长超过30秒（当前：{duration:.1f}秒）

**需要裁剪音频**

当前音频时长为 **{duration:.1f}秒**，超过了30秒限制。

**请按以下步骤操作：**
1. 使用音频播放器下方的编辑/裁剪功能
2. 拖动播放器中的蓝色条框，将音频裁剪至 **3-30秒** 范围内
3. 点击播放器右下角"Trim"完成裁剪

**提示：** 选择音频中最清晰、最有代表性的片段进行裁剪"""
                    return gr.update(interactive=False), gr.update(visible=True, value=warning_text)
                else:
                    # 音频时长正常，确保警告框隐藏
                    return gr.update(interactive=True), gr.update(visible=False, value="")

            return gr.update(interactive=True), gr.update(visible=False, value="")

        def ensure_warning_hidden(audio_upload_file, audio_mic_file):
            """确保警告框被隐藏（用于导航时强制隐藏）"""
            return gr.update(visible=False, value="")

        def go_back_to_step1(audio_upload_file, audio_mic_file):
            """返回步骤1并更新预设列表"""
            has_presets = preset_manager.get_presets()

            base_updates = [
                gr.update(value='<div class="step-item active"><span class="step-number">1</span><span class="step-label">上传参考音频</span></div>'),  # step1_indicator
                gr.update(value='<div class="step-item"><span class="step-number">2</span><span class="step-label">输入音频文本</span></div>'),  # step2_indicator
                gr.update(value='<div class="step-item"><span class="step-number">3</span><span class="step-label">生成语音</span></div>'),  # step3_indicator
                gr.update(visible=True),   # step1_container
                gr.update(visible=False),  # step2_container
                gr.update(visible=False),  # step3_container
                gr.update(value="", visible=False),  # step3_summary (清空并隐藏)
                gr.update(value=None, visible=False),  # output_audio (清空并隐藏)
                gr.update(value="", visible=False),    # output_error (清空并隐藏)
                gr.update(value=0, visible=False, label="生成进度 0.00%"),  # progress_bar (重置)
                gr.update(visible=False, value=""),  # audio_trim_warning (强制隐藏警告框)
                gr.update(visible=False, value=""),  # preset_save_status (隐藏保存状态)
                gr.update(value=audio_upload_file),  # audio_upload (保持原值以触发change事件)
                # 预设相关组件
                gr.update(value=preset_manager.get_presets_display() if has_presets else "", visible=has_presets),  # preset_list
                gr.update(choices=preset_manager.get_preset_choices() if has_presets else [], value=None, visible=has_presets),  # load_preset_dropdown (重置选择)
                gr.update(visible=has_presets, interactive=False),  # load_preset_btn (禁用)
                gr.update(visible=has_presets, interactive=False),  # delete_preset_btn (禁用)
                gr.update(visible=False, value=""),  # preset_load_status
                gr.update(visible=has_presets),  # preset_title
                gr.update(visible=has_presets),  # preset_divider
            ]

            return tuple(base_updates)

        def validate_step2(prompt_text):
            """验证步骤2：检查是否输入了参考音频文本"""
            return gr.update(interactive=bool(prompt_text and prompt_text.strip()))

        def validate_step3(text):
            """验证步骤3：检查是否输入了要合成的文本"""
            is_valid = bool(text and text.strip() and len(text) <= MAX_TEXT_LENGTH)
            return gr.update(interactive=is_valid)

        def validate_preset_dropdown(preset_choice):
            """验证预设下拉框：检查是否选择了预设"""
            is_selected = bool(preset_choice and preset_choice.strip())
            return (
                gr.update(interactive=is_selected),  # load_preset_btn
                gr.update(interactive=is_selected),  # delete_preset_btn
                gr.update(visible=False, value="")   # preset_load_status (隐藏状态消息)
            )

        def validate_save_preset(prompt_text):
            """验证保存预设：检查是否输入了参考文本（音频已在步骤1上传）"""
            has_text = bool(prompt_text and prompt_text.strip())
            return gr.update(interactive=has_text)

        # ASR提取按钮处理函数
        def handle_asr_extract(audio_upload_file, audio_mic_file):
            """处理ASR音频文字提取"""
            reference_audio = audio_upload_file or audio_mic_file

            if not reference_audio:
                return "错误：请先上传或录制参考音频"

            if not ASR_ENABLED:
                return "错误：ASR功能未启用。请在 config.py 中设置 ASR_ENABLED = True 来启用此功能。"

            try:
                import logging
                logging.info(f"开始ASR识别: {reference_audio}, 后端: {ASR_BACKEND_TYPE}")

                backend_config = ASR_BACKEND_CONFIG.get(ASR_BACKEND_TYPE, {})
                result = transcribe_audio_sync(
                    reference_audio,
                    backend_type=ASR_BACKEND_TYPE,
                    **backend_config
                )

                if result and result.strip():
                    logging.info(f"ASR识别成功: {result[:50]}...")
                    return result.strip()
                else:
                    logging.warning("ASR识别返回空结果")
                    return "识别失败：ASR服务返回空结果，请检查音频质量或ASR服务状态。您可以手动输入参考音频文本。"

            except Exception as e:
                logging.error(f"ASR识别出错: {str(e)}")
                return f"识别出错：{str(e)}\n\n建议：1. 检查ASR服务是否已启动 2. 检查音频文件格式 3. 查看控制台日志\n\n您可以手动输入参考音频文本。"

        # 音色预设处理函数
        def handle_save_preset(preset_name, audio_upload_file, audio_mic_file, prompt_text):
            """保存音色预设"""
            reference_audio = audio_upload_file or audio_mic_file

            if not reference_audio:
                return gr.update(value="❌ 请先上传或录制参考音频", visible=True)

            if not prompt_text or not prompt_text.strip():
                return gr.update(value="❌ 请先输入参考音频文本", visible=True)

            # 使用自定义名称或默认名称
            if not preset_name or not preset_name.strip():
                preset_name = f"音色预设_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # 保存预设
            preset = preset_manager.add_preset(preset_name.strip(), reference_audio, prompt_text.strip())

            if preset:
                return gr.update(value=f"✅ 音色预设 '{preset_name}' 保存成功！返回步骤1即可加载使用", visible=True)
            else:
                return gr.update(value="❌ 保存失败，请检查音频文件", visible=True)

        def handle_load_preset_and_go(preset_choice):
            """加载音色预设并直接跳转到步骤3"""
            if not preset_choice:
                return (
                    gr.update(value="", visible=False),  # status message
                    gr.update(interactive=False),  # generate_btn
                )

            # 从选择字符串中提取预设ID（格式：name (date)）
            presets = preset_manager.get_presets()
            # 找到匹配的预设
            selected_preset = None
            for preset in presets:
                if f"{preset['name']} ({preset['created_at']})" == preset_choice:
                    selected_preset = preset
                    break

            if not selected_preset:
                return (
                    gr.update(value="❌ 未找到选中的预设", visible=True),
                    gr.update(interactive=False),
                )

            audio_name = selected_preset['audio_path'].split("/")[-1]
            summary = f"""
**参考信息：**

**✓ 已加载音色预设：** {selected_preset['name']}

**✓ 参考音频文本：** {selected_preset['prompt_text'][:100]}{"..." if len(selected_preset['prompt_text']) > 100 else ""}
            """

            return (
                gr.update(value=f"✅ 已加载预设 '{selected_preset['name']}'，请输入要生成的文本", visible=True),
                gr.update(value=summary, visible=True),  # step3_summary (设置值并显示)
                selected_preset['audio_path'],
                selected_preset['prompt_text'],
                # 步骤指示器更新
                gr.update(value='<div class="step-item completed"><span class="step-number">1</span><span class="step-label">上传参考音频</span></div>'),
                gr.update(value='<div class="step-item completed"><span class="step-number">2</span><span class="step-label">输入音频文本</span></div>'),
                gr.update(value='<div class="step-item active"><span class="step-number">3</span><span class="step-label">生成语音</span></div>'),
                # 容器可见性
                gr.update(visible=False),  # step1_container
                gr.update(visible=False),  # step2_container
                gr.update(visible=True),   # step3_container
                # 其他组件
                gr.update(value=None),     # output_audio
                gr.update(visible=False),  # output_error
                gr.update(value=0, visible=False, label="生成进度 0.00%"),  # progress_bar
                gr.update(visible=False, value=""),  # audio_trim_warning (隐藏警告框)
                gr.update(visible=False, value=""),  # preset_save_status (隐藏保存状态)
            )

        def handle_delete_preset(preset_choice):
            """删除音色预设"""
            if not preset_choice:
                has_presets = preset_manager.get_presets()
                return (
                    gr.update(value="❌ 请先选择要删除的预设", visible=True),  # preset_load_status
                    gr.update(value=preset_manager.get_presets_display() if has_presets else "", visible=has_presets),  # preset_list
                    gr.update(choices=preset_manager.get_preset_choices() if has_presets else [], value=None, visible=has_presets),  # load_preset_dropdown
                    gr.update(visible=has_presets, interactive=False),  # load_preset_btn (禁用)
                    gr.update(visible=has_presets, interactive=False),  # delete_preset_btn (禁用)
                    gr.update(visible=has_presets),  # preset_title
                    gr.update(visible=has_presets),  # preset_divider
                )

            # 从选择字符串中提取预设ID（格式：name (date)）
            presets = preset_manager.get_presets()
            # 找到匹配的预设
            selected_preset = None
            for preset in presets:
                if f"{preset['name']} ({preset['created_at']})" == preset_choice:
                    selected_preset = preset
                    break

            if not selected_preset:
                has_presets = preset_manager.get_presets()
                return (
                    gr.update(value="❌ 未找到选中的预设", visible=True),  # preset_load_status
                    gr.update(value=preset_manager.get_presets_display() if has_presets else "", visible=has_presets),  # preset_list
                    gr.update(choices=preset_manager.get_preset_choices() if has_presets else [], value=None, visible=has_presets),  # load_preset_dropdown
                    gr.update(visible=has_presets, interactive=False),  # load_preset_btn (禁用)
                    gr.update(visible=has_presets, interactive=False),  # delete_preset_btn (禁用)
                    gr.update(visible=has_presets),  # preset_title
                    gr.update(visible=has_presets),  # preset_divider
                )

            # 删除预设
            success = preset_manager.delete_preset(selected_preset['id'])

            if success:
                # 检查是否还有预设
                if preset_manager.get_presets():
                    return (
                        gr.update(value=f"✅ 音色预设 '{selected_preset['name']}' 已删除", visible=True),  # preset_load_status
                        gr.update(value=preset_manager.get_presets_display(), visible=True),  # preset_list
                        gr.update(choices=preset_manager.get_preset_choices(), value=None, visible=True),  # load_preset_dropdown (重置选择)
                        gr.update(visible=True, interactive=False),  # load_preset_btn (禁用)
                        gr.update(visible=True, interactive=False),  # delete_preset_btn (禁用)
                        gr.update(visible=True),  # preset_title
                        gr.update(visible=True),  # preset_divider
                    )
                else:
                    # 如果没有预设了，隐藏所有预设相关组件
                    return (
                        gr.update(value=f"✅ 音色预设 '{selected_preset['name']}' 已删除，当前没有保存的预设", visible=True),  # preset_load_status
                        gr.update(value="", visible=False),  # preset_list
                        gr.update(choices=[], value=None, visible=False),  # load_preset_dropdown
                        gr.update(visible=False),  # load_preset_btn
                        gr.update(visible=False),  # delete_preset_btn
                        gr.update(visible=False),  # preset_title
                        gr.update(visible=False),  # preset_divider
                    )
            else:
                has_presets = preset_manager.get_presets()
                return (
                    gr.update(value=f"❌ 删除预设 '{selected_preset['name']}' 失败", visible=True),  # preset_load_status
                    gr.update(value=preset_manager.get_presets_display() if has_presets else "", visible=has_presets),  # preset_list
                    gr.update(choices=preset_manager.get_preset_choices() if has_presets else [], value=None, visible=has_presets),  # load_preset_dropdown (重置选择)
                    gr.update(visible=has_presets, interactive=False),  # load_preset_btn (禁用)
                    gr.update(visible=has_presets, interactive=False),  # delete_preset_btn (禁用)
                    gr.update(visible=has_presets),  # preset_title
                    gr.update(visible=has_presets),  # preset_divider
                )

        # 进度更新辅助函数
        def _calculate_time_progress(elapsed_time: float, received_first_chunk: bool) -> float:
            """
            根据经过的时间计算估算进度

            Args:
                elapsed_time: 已经过的秒数
                received_first_chunk: 是否已收到第一个音频chunk

            Returns:
                估算的进度值（0-100），如果无法估算则返回None
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
                # 已收到chunk：从65%继续基于时间平滑增长到92%
                # 假设生成过程大约需要20-30秒
                time_since_first_chunk = max(0, elapsed_time - 10)  # 假设前10秒等待首个chunk

                if time_since_first_chunk < 15:
                    # 前15秒：从65%增长到85%
                    progress = 65 + (time_since_first_chunk / 15.0) * 20
                elif time_since_first_chunk < 30:
                    # 15-30秒：继续增长到92%
                    progress = 85 + ((time_since_first_chunk - 15) / 15.0) * 7
                else:
                    # 30秒后：保持在92%
                    progress = 92

                return min(92, progress)

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
                yield gr.update(value=0, visible=False), gr.update(visible=False), gr.update(visible=True, value="### 请输入参考音频对应的文本内容，或点击\"提取音频文字\"按钮自动识别")
                return
            if len(text) > 1000:
                yield gr.update(value=0, visible=False), gr.update(visible=False), gr.update(visible=True, value="### ❌ 文本长度超过1000字符限制")
                return

            # 验证音频时长（3-30秒）
            try:
                import wave
                import contextlib

                # 检查音频时长
                try:
                    with contextlib.closing(wave.open(reference_audio, 'r')) as f:
                        frames = f.getnframes()
                        rate = f.getframerate()
                        duration = frames / float(rate)

                        if duration < 3:
                            yield gr.update(value=0, visible=False), gr.update(visible=False), gr.update(visible=True, value=f"### ❌ 音频时长不足3秒（当前：{duration:.1f}秒），请上传3-30秒的音频")
                            return
                        if duration > 30:
                            yield gr.update(value=0, visible=False), gr.update(visible=False), gr.update(visible=True, value=f"### ❌ 音频时长超过30秒限制（当前：{duration:.1f}秒），请上传3-30秒的音频")
                            return
                except:
                    # 如果不是WAV格式，暂时跳过验证（会在转换时处理）
                    pass
            except Exception as e:
                # 验证失败不中断流程
                pass

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
            except requests.exceptions.ConnectTimeout as e:
                yield gr.update(value=0, visible=False), gr.update(visible=False), gr.update(visible=True, value=f"### ❌ 连接API超时 - 服务端未响应，请检查API服务是否运行\n\n错误详情: {str(e)}")
                return
            except requests.exceptions.ReadTimeout as e:
                yield gr.update(value=0, visible=False), gr.update(visible=False), gr.update(visible=True, value=f"### ❌ 生成超时 - 文本过长或服务端处理时间过长（超过300秒）\n\n建议：\n1. 缩短文本长度\n2. 检查服务端性能\n\n错误详情: {str(e)}")
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
                has_server_progress = False  # 标记服务端是否提供进度信息

                # 预先发送几个进度更新，防止在等待第一个TCP chunk时进度卡住
                # 这是因为iter_content会阻塞，直到有数据到达才会执行循环
                import socket
                try:
                    # 设置socket超时，让iter_content可以定期返回（即使没有数据）
                    # 这样我们就能在等待期间更新进度
                    response.raw._fp.fp._sock.settimeout(0.1)  # 100ms超时
                except:
                    pass  # 如果设置失败也没关系，继续使用默认行为

                try:
                    # 使用流式响应
                    for tcp_chunk in response.iter_content(chunk_size=1024, decode_unicode=False):
                        # 每次循环都检查时间并更新进度（即使没有新数据）
                        current_time = time.time()
                        elapsed_time = current_time - start_time
                        time_since_last_update = (current_time - last_update_time) if last_update_time > 0 else 999

                        # 基于时间的进度估算（仅在服务端无进度信息时使用）
                        if not has_server_progress and time_since_last_update >= 0.1:
                            estimated_progress = _calculate_time_progress(elapsed_time, first_chunk_received)
                            if estimated_progress is not None:
                                # 确保不会倒退
                                estimated_progress = max(estimated_progress, last_progress)
                                # 确保不会超过接收完成进度
                                estimated_progress = min(estimated_progress, PROGRESS_RECEIVING_DONE - 1)
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

                                # 处理初始化标记（服务端正在初始化模型）
                                if metadata['chunk_index'] == -1 and metadata.get('status') == 'initializing':
                                    yield _update_progress(PROGRESS_REQUEST_SENT, f"初始化模型 {PROGRESS_REQUEST_SENT:.2f}%"), gr.update(visible=False), gr.update(visible=False)
                                    continue

                                # 处理生成开始标记（模型初始化完成，开始生成音频）
                                if metadata['chunk_index'] == -2 and metadata.get('status') == 'generating':
                                    init_time = metadata.get('init_time', 0)
                                    yield _update_progress(PROGRESS_REQUEST_SENT + 1, f"生成音频中 {PROGRESS_REQUEST_SENT + 1:.2f}% (初始化耗时: {init_time:.2f}s)"), gr.update(visible=False), gr.update(visible=False)
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

                                # 检查是否有 sub-chunk 信息（二次分块）
                                sub_chunk_index = metadata.get('sub_chunk_index')
                                sub_chunk_total = metadata.get('sub_chunk_total')
                                chunk_index = metadata.get('chunk_index', 0)

                                if sub_chunk_index is not None and sub_chunk_total is not None:
                                    # 使用 sub-chunk 信息计算进度（更细粒度）
                                    has_server_progress = True
                                    # 基于 sub-chunk 的进度：已经完成了的 chunk + 当前 chunk 的 sub-chunk 进度
                                    sub_chunk_progress = (sub_chunk_index + 1) / sub_chunk_total
                                    # 假设总共有 5 个大 chunk（估算），可以调整这个值
                                    estimated_total_chunks = max(5, chunk_index + 2)
                                    server_total_progress = PROGRESS_FIRST_CHUNK + (chunk_index + sub_chunk_progress) / estimated_total_chunks * (PROGRESS_RECEIVING_DONE - PROGRESS_FIRST_CHUNK)
                                    server_total_progress = min(PROGRESS_RECEIVING_DONE - 1, server_total_progress)

                                    # 每 2% 或最后一个 sub-chunk 时更新（更频繁）
                                    if abs(server_total_progress - last_progress) >= 2 or metadata.get('is_last_sub_chunk'):
                                        yield _update_progress(server_total_progress, f"生成进度 {server_total_progress:.2f}%"), gr.update(visible=False), gr.update(visible=False)
                                        last_progress = server_total_progress

                                elif total_chunks > 0 and server_progress >= 0:
                                    # 服务端提供了准确的进度信息，使用服务端进度并禁用时间估算
                                    has_server_progress = True
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
                except requests.exceptions.Timeout as e:
                    if len(tts_audio) == 0:
                        yield gr.update(value=0, visible=False), gr.update(visible=False), gr.update(visible=True, value=f"### ❌ 接收数据超时 - 生成时间过长\n\n建议缩短文本长度或增加服务端性能")
                        return
                    else:
                        # 如果已经接收到部分数据，仍然尝试处理
                        yield gr.update(value=0, visible=False), gr.update(visible=False), gr.update(visible=True, value=f"### ⚠️ 接收数据超时，但已接收 {len(tts_audio)} 字节，尝试处理...")
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
                        wav_file.setframerate(24000)
                        wav_file.writeframes(audio_array.tobytes())
                except Exception as e:
                    yield gr.update(value=0, visible=False), gr.update(visible=False), gr.update(visible=True, value=f"### ❌ 保存音频文件失败 - {str(e)}")
                    return

                # 完成（隐藏进度条，显示音频）
                yield gr.update(value=PROGRESS_DONE, visible=False, label=f"生成进度 {PROGRESS_DONE:.2f}%"), gr.update(value=output_path, visible=True), gr.update(visible=False)
            else:
                yield gr.update(value=0, visible=False), gr.update(visible=False), gr.update(visible=True, value=f"### ❌ API调用失败 - HTTP {response.status_code}")

        # ==================== 事件绑定 ====================

        # 步骤1：音频上传/录制后验证时长并启用"下一步"按钮
        audio_upload.change(
            fn=validate_step1,
            inputs=[audio_upload, audio_mic],
            outputs=[step1_next, audio_trim_warning]
        )
        audio_mic.change(
            fn=validate_step1,
            inputs=[audio_upload, audio_mic],
            outputs=[step1_next, audio_trim_warning]
        )

        # 步骤1：点击"下一步"进入步骤2
        step1_next.click(
            fn=go_to_step2,
            inputs=[audio_upload, audio_mic],
            outputs=[step1_indicator, step2_indicator, step3_indicator, step1_container, step2_container, step3_container, step2_audio_display, step3_summary, output_audio, output_error, progress_bar, audio_trim_warning, preset_save_status, save_preset_btn]
        )

        # 步骤1：加载预设按钮（始终绑定事件，按钮可见性由其他逻辑控制）
        load_preset_btn.click(
            fn=handle_load_preset_and_go,
            inputs=[load_preset_dropdown],
            outputs=[
                preset_load_status,      # status message
                step3_summary,           # summary
                audio_upload,            # audio path (for internal use)
                prompt_audio_text,       # prompt text (for internal use)
                step1_indicator,         # step indicators
                step2_indicator,
                step3_indicator,
                step1_container,         # container visibility
                step2_container,
                step3_container,
                output_audio,
                output_error,
                progress_bar,
                audio_trim_warning,      # hide warning
                preset_save_status       # hide save status
            ]
        )

        # 步骤1：删除预设按钮（始终绑定事件）
        delete_preset_btn.click(
            fn=handle_delete_preset,
            inputs=[load_preset_dropdown],
            outputs=[
                preset_load_status,      # status message
                preset_list,             # update preset list display
                load_preset_dropdown,   # update dropdown choices
                load_preset_btn,        # update button visibility
                delete_preset_btn,      # update button visibility
                preset_title,           # update title visibility
                preset_divider          # update divider visibility
            ]
        )

        # 步骤1：预设下拉框选择验证
        load_preset_dropdown.change(
            fn=validate_preset_dropdown,
            inputs=[load_preset_dropdown],
            outputs=[load_preset_btn, delete_preset_btn, preset_load_status]
        )

        # 步骤2：ASR提取按钮
        asr_btn.click(
            fn=handle_asr_extract,
            inputs=[audio_upload, audio_mic],
            outputs=[prompt_audio_text]
        )

        # 步骤2：清空按钮
        clear_prompt_btn.click(
            fn=lambda: (gr.update(value=""), gr.update(value="")),
            outputs=[prompt_audio_text, preset_name_input]
        )

        # 步骤2：音色预设保存按钮
        save_preset_btn.click(
            fn=handle_save_preset,
            inputs=[preset_name_input, audio_upload, audio_mic, prompt_audio_text],
            outputs=[preset_save_status]
        )

        # 步骤2：文本输入后启用"下一步"和"保存预设"按钮
        prompt_audio_text.change(
            fn=lambda text: (
                validate_step2(text),
                validate_save_preset(text)
            ),
            inputs=[prompt_audio_text],
            outputs=[step2_next, save_preset_btn]
        )

        # 步骤2：音频变化时验证保存预设按钮
        # 注意：这个会在进入步骤2时通过 go_to_step2 触发 audio_upload 的 change 事件

        # 步骤2：导航按钮
        step2_prev.click(
            fn=go_back_to_step1,
            inputs=[audio_upload, audio_mic],
            outputs=[
                step1_indicator, step2_indicator, step3_indicator,
                step1_container, step2_container, step3_container,
                step3_summary, output_audio, output_error, progress_bar,
                audio_trim_warning, preset_save_status, audio_upload,
                preset_list, load_preset_dropdown, load_preset_btn,
                delete_preset_btn, preset_load_status, preset_title, preset_divider
            ]
        )
        step2_next.click(
            fn=go_to_step3,
            inputs=[audio_upload, audio_mic, prompt_audio_text],
            outputs=[step1_indicator, step2_indicator, step3_indicator, step1_container, step2_container, step3_container, step3_summary, output_audio, output_error, progress_bar, audio_trim_warning, preset_save_status]
        )

        # 步骤3：清空按钮
        clear_text_btn.click(
            fn=lambda: (gr.update(value=""), gr.update(interactive=False)),
            outputs=[text_input, generate_btn]
        )

        # 步骤3：文本输入后启用"生成语音"按钮
        text_input.change(
            fn=validate_step3,
            inputs=[text_input],
            outputs=[generate_btn]
        )

        # 步骤3：生成按钮
        generate_btn.click(
            fn=handle_generate,
            inputs=[audio_upload, audio_mic, text_input, prompt_audio_text],
            outputs=[progress_bar, output_audio, output_error]
        )

        # 步骤3：导航按钮
        step3_prev.click(
            fn=lambda audio_upload_file, audio_mic_file: (
                gr.update(value='<div class="step-item completed"><span class="step-number">1</span><span class="step-label">上传参考音频</span></div>'),
                gr.update(value='<div class="step-item active"><span class="step-number">2</span><span class="step-label">输入音频文本</span></div>'),
                gr.update(value='<div class="step-item"><span class="step-number">3</span><span class="step-label">生成语音</span></div>'),
                gr.update(visible=False),  # step1_container
                gr.update(visible=True),   # step2_container
                gr.update(visible=False),  # step3_container
                gr.update(value="", visible=False),  # step3_summary (清空并隐藏)
                gr.update(value=None, visible=False),  # output_audio (清空并隐藏)
                gr.update(value="", visible=False),    # output_error (清空并隐藏)
                gr.update(value=0, visible=False, label="生成进度 0.00%"),  # progress_bar (重置)
                gr.update(visible=False, value=""),  # audio_trim_warning (隐藏警告框)
                gr.update(visible=False, value=""),  # preset_save_status (隐藏保存状态)
                gr.update(interactive=True),  # save_preset_btn (已有音频和文本，启用)
            ),
            inputs=[audio_upload, audio_mic],
            outputs=[step1_indicator, step2_indicator, step3_indicator, step1_container, step2_container, step3_container, step3_summary, output_audio, output_error, progress_bar, audio_trim_warning, preset_save_status, save_preset_btn]
        )
        step3_restart.click(
            fn=lambda: (
                gr.update(value='<div class="step-item active"><span class="step-number">1</span><span class="step-label">上传参考音频</span></div>'),
                gr.update(value='<div class="step-item"><span class="step-number">2</span><span class="step-label">输入音频文本</span></div>'),
                gr.update(value='<div class="step-item"><span class="step-number">3</span><span class="step-label">生成语音</span></div>'),
                gr.update(visible=True),   # step1_container
                gr.update(visible=False),  # step2_container
                gr.update(visible=False),  # step3_container
                None,  # audio_upload
                None,  # audio_mic
                "",    # prompt_audio_text
                "",    # text_input
                gr.update(value="", visible=False),  # step3_summary (清空并隐藏)
                gr.update(value=None, interactive=False),  # output_audio (清空并隐藏)
                gr.update(value="", visible=False),    # output_error (清空并隐藏)
                gr.update(value=0, visible=False, label="生成进度 0.00%"),  # progress_bar (重置值、隐藏、重置label)
                gr.update(interactive=False),  # generate_btn (禁用)
                gr.update(visible=False, value=""),  # audio_trim_warning (隐藏警告框)
                gr.update(visible=False, value=""),  # preset_save_status (隐藏保存状态)
            ),
            outputs=[step1_indicator, step2_indicator, step3_indicator, step1_container, step2_container, step3_container,
                    audio_upload, audio_mic, prompt_audio_text, text_input, step3_summary, output_audio, output_error, progress_bar, generate_btn, audio_trim_warning, preset_save_status]
        )

        # 页面加载时初始化预设显示
        def init_presets_on_load():
            """页面加载/刷新时初始化预设组件"""
            has_presets = bool(preset_manager.get_presets())
            return (
                gr.update(visible=has_presets),  # preset_title
                gr.update(value=preset_manager.get_presets_display() if has_presets else "", visible=has_presets),  # preset_list
                gr.update(choices=preset_manager.get_preset_choices() if has_presets else [], visible=has_presets),  # load_preset_dropdown
                gr.update(visible=has_presets),  # load_preset_btn
                gr.update(visible=has_presets),  # delete_preset_btn
                gr.update(visible=has_presets),  # preset_divider
            )

        app.load(
            fn=init_presets_on_load,
            inputs=[],
            outputs=[preset_title, preset_list, load_preset_dropdown, load_preset_btn, delete_preset_btn, preset_divider]
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

    /* 步骤导航样式 - 横向显示所有步骤 */
    .steps-nav {
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        gap: 8px !important;
        margin: 16px 0 !important;
        padding: 0 !important;
    }

    .step-nav-item {
        flex: 1 !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    .step-item {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 16px 12px !important;
        background: #e9ecef !important;
        border: 2px solid #dee2e6 !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
        position: relative !important;
        cursor: default !important;
    }

    .step-item .step-number {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 36px !important;
        height: 36px !important;
        background: #adb5bd !important;
        color: #ffffff !important;
        border-radius: 50% !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        margin-bottom: 8px !important;
    }

    .step-item .step-label {
        color: #6c757d !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        text-align: center !important;
        line-height: 1.3 !important;
    }

    /* 当前步骤高亮样式 */
    .step-item.active {
        background: linear-gradient(135deg, #091a31 0%, #0f3460 100%) !important;
        border-color: #0f3460 !important;
        box-shadow: 0 4px 12px rgba(9, 26, 49, 0.3) !important;
    }

    .step-item.active .step-number {
        background: #ffffff !important;
        color: #091a31 !important;
    }

    .step-item.active .step-label {
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    /* 已完成步骤样式 */
    .step-item.completed {
        background: #d4edda !important;
        border-color: #28a745 !important;
    }

    .step-item.completed .step-number {
        background: #28a745 !important;
        color: #ffffff !important;
    }

    .step-item.completed .step-label {
        color: #155724 !important;
        font-weight: 500 !important;
    }

    /* 步骤容器样式 */
    .step-container {
        background: #f8f9fa !important;
        border: 2px solid #e9ecef !important;
        border-radius: 12px !important;
        padding: 24px !important;
        margin: 16px 0 !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
    }

    /* 步骤标题样式 */
    .step-title {
        color: #091a31 !important;
        font-size: 20px !important;
        font-weight: 700 !important;
        margin-bottom: 16px !important;
        padding-bottom: 12px !important;
        border-bottom: none !important;
    }

    .step-title h3 {
        color: #091a31 !important;
        margin: 0 !important;
    }

    /* 导航按钮容器 */
    .nav-buttons {
        display: flex !important;
        gap: 12px !important;
        margin-top: 24px !important;
        justify-content: center !important;
    }

    .nav-buttons button {
        flex: 1 !important;
        max-width: 200px !important;
    }

    /* 摘要文本样式 */
    .summary-text {
        background-color: #f0f4f8 !important;
        padding: 16px !important;
        border-radius: 8px !important;
        border: 1px solid #d0d8e0 !important;
        font-size: 14px !important;
        line-height: 1.8 !important;
        margin-bottom: 16px !important;
        min-height: auto !important;
    }

    /* 隐藏的摘要文本完全不可见（针对 Gradio visible=False） */
    .summary-text[style*="display: none"],
    .step-container .summary-text[style*="display: none"],
    .step3-summary[style*="display: none"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        border: none !important;
        height: 0 !important;
        min-height: 0 !important;
        max-height: 0 !important;
        background: none !important;
        width: 0 !important;
        overflow: hidden !important;
    }

    /* 空摘要文本不显示 - 更强的规则 */
    .summary-text:empty,
    .summary-text[value=""],
    .summary-text:not(:has(*)):not(:has(:not(:empty))) {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        border: none !important;
        height: 0 !important;
        min-height: 0 !important;
        background: none !important;
    }

    /* 父容器中的空 Markdown 组件完全隐藏 */
    .step-container .summary-text:empty {
        display: none !important;
        height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    /* 隐藏隐藏元素的包装器 */
    .step3-summary[style*="display: none"] {
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    .summary-text p {
        margin: 8px 0 !important;
        color: #2c3e50 !important;
    }

    .summary-text strong {
        color: #091a31 !important;
        font-weight: 600 !important;
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

    /* 禁用状态按钮样式 */
    .gr-button:disabled,
    button:disabled {
        background: #9ca3af !important;
        color: #e5e7eb !important;
        cursor: not-allowed !important;
        opacity: 0.6 !important;
    }

    /* 生成按钮特殊样式 */
    .generate-button-inline,
    .generate-button-large {
        width: 100% !important;
        margin: 20px auto !important;
        max-width: 400px !important;
        display: block !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        padding: 18px 32px !important;
        min-height: 56px !important;
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
        margin-top: 16px !important;
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
        margin-bottom: 8px !important;
        padding-bottom: 0 !important;
        border-bottom: none !important;
        color: #2c3e50 !important;
        font-size: 15px !important;
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

    /* 提取音频文字按钮 - 强制白色文字和加粗 */
    .generate-button-full-width {
        color: #ffffff !important;
        font-weight: 700 !important;
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

    /* 裁剪警告样式 - 统一的警告提示框 */
    .trim-warning {
        background-color: #fff3e0 !important;
        border: 2px solid #ff9800 !important;
        border-left: 4px solid #f57c00 !important;
        border-radius: 6px !important;
        padding: 16px 20px !important;
        margin: 16px 0 !important;
        font-size: 14px !important;
        color: #e65100 !important;
        line-height: 1.6 !important;
        animation: pulse 2s infinite !important;
    }

    /* 当警告框为空时，完全隐藏它（包括padding和margin） */
    .trim-warning:empty,
    .trim-warning[value=""],
    .trim-warning[data-value=""] {
        display: none !important;
        padding: 0 !important;
        margin: 0 !important;
        border: none !important;
        animation: none !important;
    }

    .trim-warning strong {
        color: #bf360c !important;
        font-weight: 700 !important;
    }

    @keyframes pulse {
        0%, 100% {
            box-shadow: 0 0 0 0 rgba(255, 152, 0, 0.4) !important;
        }
        50% {
            box-shadow: 0 0 0 8px rgba(255, 152, 0, 0) !important;
        }
    }

    /* 音色预设列表样式 */
    .preset-list {
        background-color: #f8f9fa !important;
        border: 1px solid #dee2e6 !important;
        border-radius: 6px !important;
        padding: 12px 16px !important;
        margin: 12px 0 !important;
        font-size: 13px !important;
        line-height: 1.6 !important;
        max-height: 200px !important;
        overflow-y: auto !important;
    }

    /* 预设保存和加载区域样式 */
    .preset-save-section,
    .preset-load-section {
        background-color: #fafbfc !important;
        border: 1px solid #e9ecef !important;
        border-radius: 6px !important;
        padding: 12px !important;
        margin: 8px 0 !important;
    }

    .subsection-title {
        font-size: 14px !important;
        font-weight: 600 !important;
        color: #091a31 !important;
        margin-bottom: 8px !important;
    }

    /* 分割线样式 */
    .divider {
        border: none !important;
        border-top: 1px solid #e9ecef !important;
        margin: 20px 0 !important;
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
        # 不指定 font 参数，使用 Gradio 默认字体以避免加载外部 Google Fonts
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
        server_name=SERVER_NAME,
        server_port=SERVER_PORT,
        share=False,
        show_error=True,
        quiet=False,
        theme=theme,
        css=custom_css
    )


if __name__ == "__main__":
    main()
