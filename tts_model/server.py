# Copyright (c) 2024 Alibaba Inc (authors: Xiang Lyu)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import sys
import argparse
import logging
import tempfile
import json
logging.getLogger('matplotlib').setLevel(logging.WARNING)
from fastapi import FastAPI, UploadFile, Form, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import numpy as np
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append('{}/../../..'.format(ROOT_DIR))
sys.path.append('{}/../../../third_party/Matcha-TTS'.format(ROOT_DIR))
from cosyvoice.cli.cosyvoice import AutoModel
from cosyvoice.utils.file_utils import load_wav

app = FastAPI()
# set cross region allowance
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])


def generate_data(model_output):
    """生成器函数：带进度信息的音频数据流"""
    # 先将模型输出转换为列表以获取总片段数
    model_output_list = list(model_output)
    total_chunks = len(model_output_list)

    for idx, i in enumerate(model_output_list):
        tts_audio = (i['tts_speech'].numpy() * (2 ** 15)).astype(np.int16).tobytes()

        # 创建进度元数据
        progress_info = {
            "chunk_index": idx,
            "total_chunks": total_chunks,
            "progress": (idx + 1) / total_chunks * 100,  # 百分比
            "audio_size": len(tts_audio)
        }

        # 格式: JSON元数据 + \n + 音频数据
        yield json.dumps(progress_info).encode('utf-8') + b'\n' + tts_audio


@app.get("/inference_sft")
@app.post("/inference_sft")
async def inference_sft(tts_text: str = Form(), spk_id: str = Form()):
    model_output = cosyvoice.inference_sft(tts_text, spk_id)
    return StreamingResponse(generate_data(model_output))


@app.get("/inference_zero_shot")
@app.post("/inference_zero_shot")
async def inference_zero_shot(tts_text: str = Form(), prompt_text: str = Form(), prompt_wav: UploadFile = File()):
    # 保存上传文件
    contents = await prompt_wav.read()

    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
        tmp_file.write(contents)
        tmp_file_path = tmp_file.name

    try:
        # 真正的流式生成：边生成边发送（不等待全部生成完成）
        def generate_stream():
            try:
                import time
                import asyncio
                start_time = time.time()

                # 配置：每个子块的大小（字节）
                # 22050Hz * 2字节 * 0.05秒 ≈ 2205 字节
                SUB_CHUNK_SIZE = 2205  # 约0.05秒的音频数据（更细粒度）

                # 先立即发送一个"开始生成"的标记，让客户端知道服务端正在工作
                start_info = {
                    "chunk_index": -1,  # -1 表示开始标记
                    "total_chunks": -1,
                    "progress": 0,
                    "audio_size": 0,
                    "status": "initializing"  # 状态：正在初始化模型
                }
                metadata_json = json.dumps(start_info) + '\n'
                metadata_bytes = metadata_json.encode('utf-8')
                metadata_length = len(metadata_bytes).to_bytes(4, byteorder='big')
                yield metadata_length + metadata_bytes + b''  # 空音频数据

                # 异步调用模型推理，避免阻塞
                model_start_time = time.time()

                # 调用 inference_zero_shot，传递文件路径字符串
                # 这是一个生成器，第一次迭代时会触发模型初始化和首次推理
                model_output = cosyvoice.inference_zero_shot(
                    tts_text,
                    prompt_text,
                    tmp_file_path  # 传递文件路径字符串
                )

                model_init_time = time.time() - model_start_time
                print(f"[Server] Model inference initialized in {model_init_time:.2f}s")

                # 发送模型初始化完成标记
                init_info = {
                    "chunk_index": -2,  # -2 表示初始化完成
                    "total_chunks": -1,
                    "progress": 0,
                    "audio_size": 0,
                    "status": "generating",  # 状态：开始生成音频
                    "init_time": model_init_time
                }
                metadata_json = json.dumps(init_info) + '\n'
                metadata_bytes = metadata_json.encode('utf-8')
                metadata_length = len(metadata_bytes).to_bytes(4, byteorder='big')
                yield metadata_length + metadata_bytes + b''

                chunk_idx = 0

                # 使用生成器，边生成边发送
                for i in model_output:
                    chunk_start_time = time.time()
                    tts_audio = (i['tts_speech'].numpy() * (2 ** 15)).astype(np.int16).tobytes()
                    chunk_elapsed = time.time() - chunk_start_time
                    total_time_to_first_chunk = time.time() - start_time

                    # 如果是第一个 chunk，记录时间
                    if chunk_idx == 0:
                        print(f"[Server] First chunk received in {total_time_to_first_chunk:.2f}s "
                              f"(init: {model_init_time:.2f}s + first_chunk: {chunk_elapsed:.2f}s)")

                    # 二次分块：将大 chunk 切分成更小的子块
                    total_audio_size = len(tts_audio)
                    sub_chunk_idx = 0
                    sub_chunk_total = (total_audio_size + SUB_CHUNK_SIZE - 1) // SUB_CHUNK_SIZE

                    for offset in range(0, total_audio_size, SUB_CHUNK_SIZE):
                        sub_chunk_audio = tts_audio[offset:offset + SUB_CHUNK_SIZE]
                        is_last_sub = (offset + SUB_CHUNK_SIZE >= total_audio_size)

                        # 流式进度信息
                        progress_info = {
                            "chunk_index": chunk_idx,
                            "total_chunks": -1,  # -1 表示总数未知（流式生成中）
                            "progress": -1,  # -1 表示进度未知
                            "audio_size": len(sub_chunk_audio),
                            "generation_time": chunk_elapsed,  # 原始chunk生成耗时
                            "sub_chunk_index": sub_chunk_idx,
                            "sub_chunk_total": sub_chunk_total,
                            "is_last_sub_chunk": is_last_sub,
                            "time_to_first_chunk": total_time_to_first_chunk if chunk_idx == 0 else None
                        }

                        # 格式: JSON元数据长度(4字节) + JSON元数据 + 音频数据
                        metadata_json = json.dumps(progress_info) + '\n'
                        metadata_bytes = metadata_json.encode('utf-8')
                        metadata_length = len(metadata_bytes).to_bytes(4, byteorder='big')

                        yield metadata_length + metadata_bytes + sub_chunk_audio

                        sub_chunk_idx += 1

                    total_elapsed = time.time() - start_time
                    print(f"[Server] Sent chunk {chunk_idx}, split into {sub_chunk_total} sub-chunks, "
                          f"total_audio_size={total_audio_size}, "
                          f"chunk_time={chunk_elapsed:.2f}s, total_time={total_elapsed:.2f}s")

                    chunk_idx += 1

                # 发送结束标记（一个空的音频块，但包含最终统计）
                final_info = {
                    "chunk_index": chunk_idx,
                    "total_chunks": chunk_idx,  # 现在知道总数了
                    "progress": 100,  # 完成
                    "audio_size": 0,  # 空数据，表示结束
                    "is_final": True  # 标记为最后一个
                }
                metadata_json = json.dumps(final_info) + '\n'
                metadata_bytes = metadata_json.encode('utf-8')
                metadata_length = len(metadata_bytes).to_bytes(4, byteorder='big')
                yield metadata_length + metadata_bytes + b''  # 空音频数据

                total_elapsed = time.time() - start_time
                print(f"[Server] Completed: {chunk_idx} chunks in {total_elapsed:.2f}s")

            finally:
                # 确保清理临时文件
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)

        return StreamingResponse(generate_stream(), media_type="application/octet-stream")

    except Exception as e:
        # 发生异常时清理文件
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        raise e


@app.get("/inference_cross_lingual")
@app.post("/inference_cross_lingual")
async def inference_cross_lingual(tts_text: str = Form(), prompt_wav: UploadFile = File()):
    # 保存上传文件
    contents = await prompt_wav.read()

    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
        tmp_file.write(contents)
        tmp_file_path = tmp_file.name

    try:
        # 调用 inference_cross_lingual，传递文件路径字符串
        model_output = cosyvoice.inference_cross_lingual(
            tts_text,
            tmp_file_path  # 传递文件路径字符串
        )

        # 使用同步生成器
        def generate_stream():
            try:
                for i in model_output:
                    tts_audio = (i['tts_speech'].numpy() * (2 ** 15)).astype(np.int16).tobytes()
                    yield tts_audio
            finally:
                # 确保清理临时文件
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)

        return StreamingResponse(generate_stream(), media_type="audio/wav")

    except Exception as e:
        # 发生异常时清理文件
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        raise e


@app.get("/inference_instruct")
@app.post("/inference_instruct")
async def inference_instruct(tts_text: str = Form(), spk_id: str = Form(), instruct_text: str = Form()):
    model_output = cosyvoice.inference_instruct(tts_text, spk_id, instruct_text)
    return StreamingResponse(generate_data(model_output))


@app.get("/inference_instruct2")
@app.post("/inference_instruct2")
async def inference_instruct2(tts_text: str = Form(), instruct_text: str = Form(), prompt_wav: UploadFile = File()):
    # 保存上传文件
    contents = await prompt_wav.read()

    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
        tmp_file.write(contents)
        tmp_file_path = tmp_file.name

    try:
        # 调用 inference_instruct2，传递文件路径字符串
        model_output = cosyvoice.inference_instruct2(
            tts_text,
            instruct_text,
            tmp_file_path  # 传递文件路径字符串
        )

        # 使用同步生成器
        def generate_stream():
            try:
                for i in model_output:
                    tts_audio = (i['tts_speech'].numpy() * (2 ** 15)).astype(np.int16).tobytes()
                    yield tts_audio
            finally:
                # 确保清理临时文件
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)

        return StreamingResponse(generate_stream(), media_type="audio/wav")

    except Exception as e:
        # 发生异常时清理文件
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        raise e


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port',
                        type=int,
                        default=50000)
    parser.add_argument('--model_dir',
                        type=str,
                        default='iic/CosyVoice2-0.5B',
                        help='local path or modelscope repo id')
    args = parser.parse_args()
    cosyvoice = AutoModel(model_dir=args.model_dir)
    uvicorn.run(app, host="0.0.0.0", port=args.port)
