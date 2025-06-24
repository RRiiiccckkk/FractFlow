import pyaudio
import webrtcvad
import wave
import threading
import time
from queue import Queue
from funasr import AutoModel

class AudioInput:
    def __init__(self, rate=16000, channels=1, chunk=1024, vad_mode=3):
        """初始化录音和VAD参数"""
        self.rate = rate
        self.channels = channels
        self.chunk = chunk
        self.vad_mode = vad_mode
        
        # VAD初始化
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(self.vad_mode)
        
        # 录音相关
        self._recording = False
        self._audio_queue = Queue()
        self._audio_buffer = []
        self.last_active_time = time.time()
        
        # ASR模型
        self.asr_model = AutoModel(
            model=r"E:\mnt\e\LLM\ModelScope\SenseVoiceSmall",
            trust_remote_code=True,
        )
        
        # PyAudio初始化
        self._pyaudio = pyaudio.PyAudio()
        self._stream = None
        self._interrupt_stream = None
        
        # 打断检测相关
        self._interrupt_thread = None
        self._interrupt_flag = False
        self._is_detecting = False
        self._detection_buffer = []
        
        # 状态显示相关
        self._last_status = ""

    def _check_vad_activity(self, audio_data):
        """检测是否有语音活动"""
        num, rate = 0, 0.3  # 降低阈值，提高灵敏度
        step = int(self.rate * 0.02)  # 20ms块大小
        flag_rate = round(rate * len(audio_data) // step)

        for i in range(0, len(audio_data), step):
            chunk = audio_data[i:i + step]
            if len(chunk) == step:
                if self.vad.is_speech(chunk, sample_rate=self.rate):
                    num += 1

        return num > flag_rate

    def _interrupt_detection_thread(self):
        """专门用于打断检测的线程"""
        self._interrupt_stream = self._pyaudio.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        
        while self._is_detecting:
            try:
                data = self._interrupt_stream.read(self.chunk, exception_on_overflow=False)
                self._detection_buffer.append(data)
                
                # 保持缓冲区在0.3秒左右
                if len(self._detection_buffer) > int(0.3 * self.rate / self.chunk):
                    combined_data = b''.join(self._detection_buffer)
                    if self._check_vad_activity(combined_data):
                        self._interrupt_flag = True
                    self._detection_buffer = []
                    
            except Exception as e:
                print(f"打断检测出错: {e}")
                break
                
        # 清理资源
        if self._interrupt_stream:
            self._interrupt_stream.stop_stream()
            self._interrupt_stream.close()
            self._interrupt_stream = None

    def start_interrupt_detection(self):
        """开始打断检测"""
        if not self._is_detecting:
            self._is_detecting = True
            self._interrupt_flag = False
            self._detection_buffer = []
            self._interrupt_thread = threading.Thread(target=self._interrupt_detection_thread)
            self._interrupt_thread.daemon = True
            self._interrupt_thread.start()

    def stop_interrupt_detection(self):
        """停止打断检测"""
        self._is_detecting = False
        if self._interrupt_thread:
            self._interrupt_thread.join(timeout=1.0)
            self._interrupt_thread = None
        self._interrupt_flag = False
        self._detection_buffer = []

    def is_interrupting(self) -> bool:
        """检查是否有打断发生"""
        if self._interrupt_flag:
            self._interrupt_flag = False  # 重置标志
            return True
        return False

    def _print_status(self, status: str):
        """打印状态，避免重复"""
        if status != self._last_status:
            print(f"\r{status}", end="", flush=True)
            self._last_status = status

    def record_once(self) -> bytes:
        """录制一段语音（带VAD，自动结束），返回原始音频数据"""
        self._recording = True
        self._audio_buffer = []
        self._stream = self._pyaudio.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        
        print("\n开始录音...")
        no_speech_time = 0
        last_speech_time = time.time()
        has_speech = False  # 是否检测到过语音
        
        while self._recording:
            data = self._stream.read(self.chunk)
            self._audio_buffer.append(data)
            
            # 每0.5秒检查一次VAD
            if len(self._audio_buffer) * self.chunk / self.rate >= 0.5:
                raw_audio = b''.join(self._audio_buffer[-int(0.5 * self.rate / self.chunk):])
                if self._check_vad_activity(raw_audio):
                    self._print_status("检测到语音活动...")
                    last_speech_time = time.time()
                    no_speech_time = 0
                    has_speech = True
                else:
                    no_speech_time = time.time() - last_speech_time
                    if has_speech:  # 只有在之前检测到语音后才显示静音状态
                        self._print_status("静音中...")
                    else:
                        self._print_status("等待说话...")
                
                # 如果检测到过语音，且1.5秒没有新的语音，结束录音
                if has_speech and no_speech_time > 1.5 and len(self._audio_buffer) * self.chunk / self.rate > 1.0:
                    print("\n录音结束")
                    break
                
                # 如果5秒都没有检测到语音，提示用户并重新开始
                if not has_speech and time.time() - last_speech_time > 5.0:
                    print("\n未检测到语音，请重新说话...")
                    self._audio_buffer = []
                    last_speech_time = time.time()
        
        self._stream.stop_stream()
        self._stream.close()
        
        # 如果没有检测到任何语音，返回空
        if not has_speech:
            return b''
            
        return b''.join(self._audio_buffer)

    def asr_once(self) -> str:
        """录音+ASR，返回一句话的文本"""
        while True:  # 循环直到获得有效的语音输入
            audio_data = self.record_once()
            
            # 如果没有检测到语音，继续录音
            if not audio_data:
                continue
                
            # 保存临时wav文件
            temp_file = "temp_audio.wav"
            with wave.open(temp_file, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)  # 16-bit PCM
                wf.setframerate(self.rate)
                wf.writeframes(audio_data)
            
            # ASR识别
            res = self.asr_model.generate(
                input=temp_file,
                cache={},
                language="auto",
                use_itn=False,
            )
            
            # 删除临时文件
            import os
            os.remove(temp_file)
            
            text = res[0]['text'].split(">")[-1]
            if text.strip():  # 如果识别出的文本不为空
                return text
            print("\n未能识别语音，请重新说话...")

    def close(self):
        """释放资源"""
        self._recording = False
        self.stop_interrupt_detection()
        
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except:
                pass
            self._stream = None
            
        if self._interrupt_stream:
            try:
                self._interrupt_stream.stop_stream()
                self._interrupt_stream.close()
            except:
                pass
            self._interrupt_stream = None
            
        if self._pyaudio:
            self._pyaudio.terminate()
            self._pyaudio = None