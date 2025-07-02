from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .api_entry import get_api, HKUSTAssistantAPI  # 业务逻辑层

# ---------------------------------------------
# 常量配置
# ---------------------------------------------
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
AUDIO_DIR = STATIC_DIR / "audio"

# 确保静态目录存在
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------
# Pydantic 请求/响应模型（严格遵守用户定义）
# ---------------------------------------------
class ChatRequest(BaseModel):
    message: str
    sessionId: str | None = None

class ChatResponse(BaseModel):
    response: str
    sessionId: str

class STTResponse(BaseModel):
    text: str

class TTSRequest(BaseModel):
    text: str
    language: str | None = "zh-CN"

class TTSResponse(BaseModel):
    audioUrl: str

# ---------------------------------------------
# FastAPI 应用实例
# ---------------------------------------------
app = FastAPI(title="FractFlow API Gateway", version="1.0.0")

# 允许所有来源，实际部署可按需收敛
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件（提供语音文件 URL）
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ---------------------------------------------
# Session 管理器
# ---------------------------------------------
class SessionManager:
    """简单的 sessionId -> HKUSTAssistantAPI 单例映射"""
    def __init__(self):
        self._sessions: Dict[str, HKUSTAssistantAPI] = {}

    def get_assistant(self, session_id: str) -> HKUSTAssistantAPI:
        if session_id not in self._sessions:
            self._sessions[session_id] = get_api()
        return self._sessions[session_id]

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = get_api()
        return session_id

    async def shutdown_all(self):
        for api in self._sessions.values():
            await api.shutdown()
        self._sessions.clear()

session_manager = SessionManager()

# ---------------------------------------------
# API 路由实现
# ---------------------------------------------
@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    # 获取或创建 session
    session_id = payload.sessionId or session_manager.create_session()
    assistant_api = session_manager.get_assistant(session_id)

    # 确保默认学术模式已初始化
    if not assistant_api.assistant:
        await assistant_api.start_academic_mode()

    result = await assistant_api.process_message(payload.message)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])

    return ChatResponse(response=result["response"], sessionId=session_id)

@app.post("/api/speech-to-text", response_model=STTResponse)
async def speech_to_text_endpoint(
    sampleRate: int | None = 16000,
    audioData: UploadFile = File(...),
):
    # 保存上传的文件到临时目录
    temp_wav = AUDIO_DIR / f"input_{uuid.uuid4()}.wav"
    try:
        with temp_wav.open("wb") as f:
            f.write(await audioData.read())

        # TODO: 在此接入真正的 ASR 模型；目前返回占位符文本
        # 为了示例，简单返回文件名
        recognized_text = "(placeholder)"

        return STTResponse(text=recognized_text)
    finally:
        if temp_wav.exists():
            temp_wav.unlink(missing_ok=True)

@app.post("/api/text-to-speech", response_model=TTSResponse)
async def text_to_speech_endpoint(payload: TTSRequest, background_tasks: BackgroundTasks):
    # 生成唯一文件名
    audio_filename = f"tts_{uuid.uuid4()}.mp3"
    audio_path = AUDIO_DIR / audio_filename

    # 使用 edge_tts 直接生成语音文件，避免依赖 pygame
    import edge_tts

    voice_map = {
        "zh-CN": "zh-CN-XiaoyiNeural",
        "en-US": "en-US-AnaNeural",
        "ja-JP": "ja-JP-NanamiNeural",
        "fr-FR": "fr-FR-DeniseNeural",
        "es-ES": "ca-ES-JoanaNeural",
        "de-DE": "de-DE-KatjaNeural",
    }
    voice = voice_map.get(payload.language, "zh-CN-XiaoyiNeural")

    communicate = edge_tts.Communicate(payload.text, voice)
    await communicate.save(str(audio_path))

    # 后台任务：可选的文件清理（例如 10 分钟后删除）
    def _remove_file(path: Path):
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass

    background_tasks.add_task(_remove_file, audio_path)

    # 构建可访问 URL
    audio_url = f"/static/audio/{audio_filename}"
    return TTSResponse(audioUrl=audio_url)

# ---------------------------------------------
# 健康检查端点
# ---------------------------------------------
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# ---------------------------------------------
# 清理任务 (shutdown)
# ---------------------------------------------
@app.on_event("shutdown")
async def shutdown_event():
    await session_manager.shutdown_all() 