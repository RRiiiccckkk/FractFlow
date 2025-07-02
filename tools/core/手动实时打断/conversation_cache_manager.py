#!/usr/bin/env python3
"""
对话缓存管理器
支持外部文件存储、上下文管理和对话连续性
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import hashlib
import threading
from pathlib import Path

class ConversationCacheManager:
    """对话缓存管理器"""
    
    def __init__(self, cache_dir: str = "conversation_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # 当前会话信息
        self.session_id = self._generate_session_id()
        self.session_file = self.cache_dir / f"session_{self.session_id}.json"
        
        # 对话历史
        self.conversation_history = []
        self.current_turn = 0
        
        # 配置参数
        self.max_context_length = 4000  # 最大上下文字符数
        self.max_turns_in_memory = 20   # 内存中保留的最大轮数
        self.auto_save_interval = 30    # 自动保存间隔（秒）
        
        # 线程安全
        self._lock = threading.Lock()
        
        # 启动时加载历史会话
        self._load_recent_session()
        
        print(f"📝 对话缓存管理器已初始化")
        print(f"💾 缓存目录: {self.cache_dir}")
        print(f"🆔 会话ID: {self.session_id}")
        print(f"📚 历史对话: {len(self.conversation_history)} 轮")
    
    def _generate_session_id(self) -> str:
        """生成会话ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_hash = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        return f"{timestamp}_{random_hash}"
    
    def _load_recent_session(self) -> None:
        """加载最近的会话历史"""
        try:
            # 查找最近的会话文件
            session_files = list(self.cache_dir.glob("session_*.json"))
            if not session_files:
                print("📄 未找到历史会话文件，开始新会话")
                return
            
            # 按修改时间排序，选择最新的
            latest_file = max(session_files, key=os.path.getmtime)
            
            # 检查文件是否太旧（超过24小时）
            file_age = time.time() - os.path.getmtime(latest_file)
            if file_age > 24 * 3600:  # 24小时
                print(f"📄 最近会话文件过旧（{file_age/3600:.1f}小时），开始新会话")
                return
            
            # 加载历史会话
            with open(latest_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
                
            self.conversation_history = session_data.get('conversation_history', [])
            self.current_turn = session_data.get('current_turn', 0)
            
            print(f"📚 已加载历史会话: {len(self.conversation_history)} 轮对话")
            print(f"⏰ 会话时间: {session_data.get('last_update', 'Unknown')}")
            
            # 显示最近的几轮对话摘要
            self._show_recent_summary()
            
        except Exception as e:
            print(f"⚠️ 加载历史会话失败: {e}")
            self.conversation_history = []
            self.current_turn = 0
    
    def _show_recent_summary(self) -> None:
        """显示最近对话的摘要"""
        if not self.conversation_history:
            return
            
        print("📋 最近对话摘要:")
        recent_conversations = self.conversation_history[-3:]  # 显示最近3轮
        
        for i, conv in enumerate(recent_conversations, 1):
            user_text = conv.get('user_text', 'No transcript')
            ai_text = conv.get('ai_text', 'No response')
            
            # 截断长文本
            user_preview = user_text[:50] + "..." if len(user_text) > 50 else user_text
            ai_preview = ai_text[:50] + "..." if len(ai_text) > 50 else ai_text
            
            print(f"   {i}. 👤: {user_preview}")
            print(f"      🤖: {ai_preview}")
        
        if len(self.conversation_history) > 3:
            print(f"   ... 共 {len(self.conversation_history)} 轮对话")
    
    def add_conversation_turn(self, user_text: str, ai_text: str, 
                            user_audio_duration: float = 0.0,
                            ai_audio_duration: float = 0.0) -> None:
        """添加一轮对话"""
        with self._lock:
            self.current_turn += 1
            
            conversation_turn = {
                'turn_id': self.current_turn,
                'timestamp': datetime.now().isoformat(),
                'user_text': user_text.strip(),
                'ai_text': ai_text.strip(),
                'user_audio_duration': user_audio_duration,
                'ai_audio_duration': ai_audio_duration,
                'metadata': {
                    'user_text_length': len(user_text),
                    'ai_text_length': len(ai_text),
                    'session_id': self.session_id
                }
            }
            
            self.conversation_history.append(conversation_turn)
            
            # 立即保存到文件
            self._save_to_file()
            
            print(f"💾 已保存第 {self.current_turn} 轮对话")
            print(f"📊 对话统计: 用户{len(user_text)}字, AI{len(ai_text)}字")
    
    def get_context_for_ai(self, max_length: Optional[int] = None) -> str:
        """获取给AI的上下文"""
        if not self.conversation_history:
            return ""
        
        max_length = max_length or self.max_context_length
        
        # 构建上下文字符串
        context_parts = ["以下是我们的对话历史，请参考这些信息回答我的问题：\n"]
        
        # 从最新的对话开始添加
        total_length = len(context_parts[0])
        added_turns = 0
        
        for conv in reversed(self.conversation_history):
            turn_text = f"\n第{conv['turn_id']}轮对话：\n"
            turn_text += f"用户: {conv['user_text']}\n"
            turn_text += f"AI: {conv['ai_text']}\n"
            
            # 检查是否超出长度限制
            if total_length + len(turn_text) > max_length:
                break
                
            context_parts.insert(1, turn_text)  # 插入到开头（时间顺序）
            total_length += len(turn_text)
            added_turns += 1
        
        # 如果添加的轮数较少，尝试生成摘要
        if added_turns < len(self.conversation_history) and len(self.conversation_history) > 5:
            summary = self._generate_conversation_summary()
            if summary:
                context_parts.insert(1, f"\n早期对话摘要: {summary}\n")
        
        context = "".join(context_parts)
        context += "\n请基于以上对话历史，自然地回答我的新问题："
        
        print(f"🧠 为AI生成上下文: {len(context)}字, 包含{added_turns}轮对话")
        return context
    
    def _generate_conversation_summary(self) -> str:
        """生成对话摘要"""
        if len(self.conversation_history) < 5:
            return ""
            
        # 获取早期对话（除了最近5轮）
        early_conversations = self.conversation_history[:-5]
        
        # 提取关键信息
        topics = set()
        key_info = []
        
        for conv in early_conversations:
            user_text = conv['user_text'].lower()
            ai_text = conv['ai_text']
            
            # 简单的关键词提取
            if any(keyword in user_text for keyword in ['介绍', '是什么', '怎么样', '如何']):
                key_info.append(f"用户询问了{conv['user_text'][:30]}")
            
            if any(keyword in user_text for keyword in ['天气', '时间', '日期']):
                topics.add('日常查询')
            elif any(keyword in user_text for keyword in ['学习', '工作', '项目']):
                topics.add('学习工作')
            elif any(keyword in user_text for keyword in ['帮助', '问题', '解决']):
                topics.add('问题解决')
        
        # 生成摘要
        summary_parts = []
        if topics:
            summary_parts.append(f"主要话题: {', '.join(topics)}")
        if key_info:
            summary_parts.append(f"关键信息: {'; '.join(key_info[:3])}")
        
        summary_parts.append(f"共{len(early_conversations)}轮早期对话")
        
        return "; ".join(summary_parts)
    
    def _save_to_file(self) -> None:
        """保存到文件"""
        try:
            session_data = {
                'session_id': self.session_id,
                'created_at': datetime.now().isoformat(),
                'last_update': datetime.now().isoformat(),
                'current_turn': self.current_turn,
                'conversation_history': self.conversation_history,
                'statistics': {
                    'total_turns': len(self.conversation_history),
                    'total_user_chars': sum(len(c['user_text']) for c in self.conversation_history),
                    'total_ai_chars': sum(len(c['ai_text']) for c in self.conversation_history),
                    'session_duration_minutes': self._get_session_duration()
                }
            }
            
            # 原子写入（先写临时文件，再重命名）
            temp_file = self.session_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            temp_file.rename(self.session_file)
            
        except Exception as e:
            print(f"❌ 保存会话文件失败: {e}")
    
    def _get_session_duration(self) -> float:
        """获取会话持续时间（分钟）"""
        if not self.conversation_history:
            return 0.0
            
        try:
            first_time = datetime.fromisoformat(self.conversation_history[0]['timestamp'])
            last_time = datetime.fromisoformat(self.conversation_history[-1]['timestamp'])
            duration = (last_time - first_time).total_seconds() / 60
            return round(duration, 1)
        except:
            return 0.0
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """获取对话统计信息"""
        if not self.conversation_history:
            return {'total_turns': 0}
            
        stats = {
            'total_turns': len(self.conversation_history),
            'session_duration_minutes': self._get_session_duration(),
            'total_user_chars': sum(len(c['user_text']) for c in self.conversation_history),
            'total_ai_chars': sum(len(c['ai_text']) for c in self.conversation_history),
            'average_user_response_length': sum(len(c['user_text']) for c in self.conversation_history) / len(self.conversation_history),
            'average_ai_response_length': sum(len(c['ai_text']) for c in self.conversation_history) / len(self.conversation_history),
            'current_context_length': len(self.get_context_for_ai()),
            'session_id': self.session_id,
            'cache_file': str(self.session_file)
        }
        
        return stats
    
    def cleanup_old_sessions(self, days_to_keep: int = 7) -> None:
        """清理旧的会话文件"""
        try:
            cutoff_time = time.time() - (days_to_keep * 24 * 3600)
            
            session_files = list(self.cache_dir.glob("session_*.json"))
            removed_count = 0
            
            for file_path in session_files:
                if os.path.getmtime(file_path) < cutoff_time:
                    file_path.unlink()
                    removed_count += 1
            
            if removed_count > 0:
                print(f"🧹 清理了 {removed_count} 个旧会话文件（超过{days_to_keep}天）")
                
        except Exception as e:
            print(f"⚠️ 清理旧会话文件失败: {e}")
    
    def export_conversation(self, export_format: str = "markdown") -> str:
        """导出对话历史"""
        if not self.conversation_history:
            return "没有对话历史可以导出"
            
        if export_format.lower() == "markdown":
            return self._export_as_markdown()
        elif export_format.lower() == "text":
            return self._export_as_text()
        else:
            return json.dumps(self.conversation_history, ensure_ascii=False, indent=2)
    
    def _export_as_markdown(self) -> str:
        """导出为Markdown格式"""
        lines = [
            f"# 对话历史导出",
            f"",
            f"**会话ID**: {self.session_id}",
            f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**对话轮数**: {len(self.conversation_history)}",
            f"**会话时长**: {self._get_session_duration():.1f} 分钟",
            f"",
            f"---",
            f""
        ]
        
        for i, conv in enumerate(self.conversation_history, 1):
            timestamp = datetime.fromisoformat(conv['timestamp']).strftime('%H:%M:%S')
            lines.extend([
                f"## 第 {i} 轮对话 ({timestamp})",
                f"",
                f"**👤 用户**: {conv['user_text']}",
                f"",
                f"**🤖 AI**: {conv['ai_text']}",
                f"",
                f"---",
                f""
            ])
        
        return "\n".join(lines)
    
    def _export_as_text(self) -> str:
        """导出为纯文本格式"""
        lines = [
            f"对话历史导出 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"会话ID: {self.session_id}",
            f"对话轮数: {len(self.conversation_history)}",
            f"会话时长: {self._get_session_duration():.1f} 分钟",
            f"",
            f"=" * 50,
            f""
        ]
        
        for i, conv in enumerate(self.conversation_history, 1):
            timestamp = datetime.fromisoformat(conv['timestamp']).strftime('%H:%M:%S')
            lines.extend([
                f"第 {i} 轮对话 ({timestamp})",
                f"",
                f"用户: {conv['user_text']}",
                f"",
                f"AI: {conv['ai_text']}",
                f"",
                f"-" * 30,
                f""
            ])
        
        return "\n".join(lines)
    
    def close(self) -> None:
        """关闭缓存管理器"""
        try:
            # 最后一次保存
            self._save_to_file()
            
            # 显示统计信息
            stats = self.get_conversation_stats()
            print(f"\n📊 对话会话统计:")
            print(f"   总轮数: {stats['total_turns']}")
            print(f"   会话时长: {stats['session_duration_minutes']:.1f} 分钟")
            print(f"   用户总字数: {stats['total_user_chars']}")
            print(f"   AI总字数: {stats['total_ai_chars']}")
            print(f"   会话文件: {stats['cache_file']}")
            
            # 清理旧文件
            self.cleanup_old_sessions()
            
            print("💾 对话缓存管理器已关闭")
            
        except Exception as e:
            print(f"⚠️ 关闭缓存管理器时出错: {e}") 