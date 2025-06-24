import os
import asyncio
import pygame
import edge_tts
import langid
import json
import uuid
from typing import Callable

class TTSOutput:
    def __init__(self):
        """初始化TTS输出"""
        self.language_speaker = {
            "ja": "ja-JP-NanamiNeural",     # 日语
            "fr": "fr-FR-DeniseNeural",     # 法语
            "es": "ca-ES-JoanaNeural",      # 西班牙语
            "de": "de-DE-KatjaNeural",      # 德语
            "zh": "zh-CN-XiaoyiNeural",     # 中文
            "en": "en-US-AnaNeural",        # 英语
        }
        # 初始化pygame mixer用于音频播放
        pygame.mixer.init()
        # 临时文件目录
        self.temp_dir = "temp_tts"
        if os.path.exists(self.temp_dir):
            self._cleanup_temp_dir()
        os.makedirs(self.temp_dir, exist_ok=True)
        self.current_file = None

    def _cleanup_temp_dir(self):
        """清理临时目录中的所有文件"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"清理临时目录失败: {e}")

    def _detect_language(self, text: str) -> str:
        """检测文本语言并返回对应的speaker"""
        language, _ = langid.classify(text)
        return self.language_speaker.get(language, "zh-CN-XiaoyiNeural")

    async def _generate_speech(self, text: str, output_file: str):
        """生成语音文件"""
        voice = self._detect_language(text)
        communicate = edge_tts.Communicate(text, voice)
        # 确保在生成新文件前释放旧文件
        if self.current_file and os.path.exists(self.current_file):
            try:
                pygame.mixer.music.unload()
                os.remove(self.current_file)
            except:
                pass
        await communicate.save(output_file)
        self.current_file = output_file

    async def speak(self, text: str, interrupt_checker: Callable[[], bool] = None):
        """
        播放文本对应的语音，支持实时打断

        Args:
            text: 要播放的文本（JSON字符串或普通文本）
            interrupt_checker: 检查是否需要打断的回调函数
        """
        # 生成唯一的临时文件名
        temp_file = os.path.join(self.temp_dir, f"speech_{uuid.uuid4()}.mp3")
        
        # 尝试解析JSON，获取response_text
        try:
            response_data = json.loads(text)
            text_to_speak = response_data.get("response_text", text)
        except (json.JSONDecodeError, AttributeError):
            # 如果解析失败，直接使用原文本
            text_to_speak = text
        
        try:
            # 生成语音文件
            await self._generate_speech(text_to_speak, temp_file)
            
            # 确保pygame mixer已初始化
            if not pygame.mixer.get_init():
                pygame.mixer.init()
                pygame.mixer.music.set_volume(1.0)
            
            # 等待50ms确保文件写入完成
            await asyncio.sleep(0.05)
            
            # 加载并播放音频
            try:
                pygame.mixer.music.load(temp_file)
                pygame.mixer.music.play()
            except Exception as e:
                print(f"音频加载或播放出错: {e}")
                return
            
            # 播放时检查打断
            check_interval = 0.05  # 降低检查间隔到50ms
            try:
                while pygame.mixer.music.get_busy():
                    if interrupt_checker and interrupt_checker():
                        print("\n检测到语音输入，停止当前播放...")
                        pygame.mixer.music.stop()
                        pygame.mixer.music.unload()  # 立即卸载音频
                        break
                    await asyncio.sleep(check_interval)
            except Exception as e:
                print(f"播放监控出错: {e}")
                
        except Exception as e:
            print(f"语音合成出错: {e}")
        finally:
            # 确保在播放结束后释放资源
            try:
                if pygame.mixer.get_init():
                    pygame.mixer.music.stop()
                    pygame.mixer.music.unload()
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                print(f"资源清理出错: {e}")

    def close(self):
        """清理资源"""
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
                pygame.mixer.quit()
        except Exception as e:
            print(f"Pygame清理出错: {e}")
            
        self._cleanup_temp_dir()