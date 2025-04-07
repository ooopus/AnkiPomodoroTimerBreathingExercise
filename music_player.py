import json
import random
import requests
import os
from PyQt6.QtCore import QUrl, QTimer, pyqtSignal, QObject
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest

class MusicPlayer(QObject):
    """音乐播放器，支持从多个免费电台API获取并播放音乐"""
    
    # 信号定义
    playback_started = pyqtSignal(str)  # 发射当前播放的歌曲信息
    playback_error = pyqtSignal(str)    # 发射播放错误信息
    playback_stopped = pyqtSignal()     # 播放停止信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化媒体播放器
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
        # 初始化音效播放器
        self.sound_player = QMediaPlayer()
        self.sound_audio_output = QAudioOutput()
        self.sound_player.setAudioOutput(self.sound_audio_output)
        
        # 音效播放器事件处理已注册标志
        self._sound_handlers_connected = False
        
        # 网络请求管理器
        self.network_manager = QNetworkAccessManager()
        
        # 播放相关变量
        self.is_playing = False
        self.current_api = None
        self.current_stream_url = None
        self.current_song_info = None
        
        # 重试机制相关变量
        self.retry_timer = QTimer()
        self.retry_timer.timeout.connect(self.try_next_api)
        self.max_retries = 3
        self.current_retries = 0
        
        # 健康检查定时器 - 每5秒检查一次播放状态
        self.health_check_timer = QTimer()
        self.health_check_timer.timeout.connect(self.check_playback_health)
        
        # 连接播放器信号
        self.player.errorOccurred.connect(self.handle_player_error)
        self.player.mediaStatusChanged.connect(self.on_media_status_changed)
        self.player.playbackStateChanged.connect(self.on_playback_state_changed)
        
        # 初始化音效播放器信号连接
        self._setup_sound_player_handlers()
        
        # 电台API列表
        self.radio_apis = [
            {
                "name": "开发者平台电台",
                "url": "https://api.uomg.com/api/rand.music",
                "params": {"sort": "热歌榜", "format": "json"},
                "stream_extractor": lambda data: data.get("data", {}).get("url"),
                "info_extractor": lambda data: f"{data.get('data', {}).get('name', '未知')} - {data.get('data', {}).get('artistsname', '未知')}"
            },
            {
                "name": "MiGu音乐电台",
                "url": "https://api.uomg.com/api/rand.music",
                "params": {"sort": "飙升榜", "format": "json"},
                "stream_extractor": lambda data: data.get("data", {}).get("url"),
                "info_extractor": lambda data: f"{data.get('data', {}).get('name', '未知')} - {data.get('data', {}).get('artistsname', '未知')}"
            },
            {
                "name": "网易云音乐电台",
                "url": "https://api.uomg.com/api/rand.music",
                "params": {"sort": "新歌榜", "format": "json"},
                "stream_extractor": lambda data: data.get("data", {}).get("url"),
                "info_extractor": lambda data: f"{data.get('data', {}).get('name', '未知')} - {data.get('data', {}).get('artistsname', '未知')}"
            }
        ]
    
    def _setup_sound_player_handlers(self):
        """设置音效播放器的事件处理器"""
        if self._sound_handlers_connected:
            return
            
        # 添加错误处理
        def on_sound_error(error, error_string):
            print(f"音效播放错误: {error} - {error_string}")
        
        # 添加状态变化监听
        def on_sound_status_changed(status):
            from PyQt6.QtMultimedia import QMediaPlayer
            if status == QMediaPlayer.MediaStatus.LoadedMedia:
                print("音效文件已加载，准备播放")
            elif status == QMediaPlayer.MediaStatus.EndOfMedia:
                print("音效播放完成")
            elif status == QMediaPlayer.MediaStatus.InvalidMedia:
                print(f"无效的音效文件")
        
        # 添加播放状态监听
        def on_sound_state_changed(state):
            from PyQt6.QtMultimedia import QMediaPlayer
            if state == QMediaPlayer.PlaybackState.PlayingState:
                print("音效正在播放中")
        
        # 连接信号
        self.sound_player.errorOccurred.connect(on_sound_error)
        self.sound_player.mediaStatusChanged.connect(on_sound_status_changed)
        self.sound_player.playbackStateChanged.connect(on_sound_state_changed)
        
        self._sound_handlers_connected = True
    
    def play_sound_effect(self, sound_file):
        """播放指定的本地音效文件"""
        try:
            # 构建音效文件的完整路径
            # 获取当前插件目录 (而不是addons21目录)
            addon_dir = os.path.dirname(os.path.abspath(__file__))
            sound_path = os.path.join(addon_dir, sound_file)
            
            # 检查文件是否存在
            if not os.path.exists(sound_path):
                print(f"音效文件不存在: {sound_path}")
                return False
            
            print(f"正在播放音效文件: {sound_path}")
            
            # 确保音效播放器处于停止状态
            self.sound_player.stop()
            
            # 等待一段时间确保资源已释放
            QTimer.singleShot(100, lambda: self._play_sound(sound_path))
            
            return True
        except Exception as e:
            print(f"播放音效时出错: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _play_sound(self, sound_path):
        """实际播放音效的函数，在短暂延迟后调用"""
        try:
            # 设置音效源并播放
            self.sound_player.setSource(QUrl.fromLocalFile(sound_path))
            self.sound_audio_output.setVolume(1.0)  # 设置音量为100%
            self.sound_player.play()
        except Exception as e:
            print(f"播放音效文件时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def toggle_playback(self):
        """切换播放状态"""
        if self.is_playing:
            self.stop_playback()
        else:
            self.start_playback()
        
        return self.is_playing
    
    def start_playback(self):
        """开始播放音乐"""
        if self.is_playing:
            return
        
        self.is_playing = True
        self.current_retries = 0
        
        # 启动健康检查定时器
        self.health_check_timer.start(5000)  # 每5秒检查一次
        
        # 随机选择一个API
        self.try_next_api()
    
    def try_next_api(self):
        """尝试使用下一个API获取音乐"""
        # 停止之前的重试计时器
        self.retry_timer.stop()
        
        # 如果已不再播放状态，直接返回
        if not self.is_playing:
            return
            
        # 如果已达到最大重试次数，则停止播放
        if self.current_retries >= self.max_retries * len(self.radio_apis):
            self.playback_error.emit("所有API尝试失败，无法播放音乐")
            self.stop_playback()
            return
        
        # 随机选择一个API
        self.current_api = random.choice(self.radio_apis)
        self.current_retries += 1
        
        try:
            # 请求音乐URL
            response = requests.get(
                self.current_api["url"],
                params=self.current_api["params"],
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") == 1:  # 请求成功
                # 获取流媒体URL和歌曲信息
                stream_url = self.current_api["stream_extractor"](data)
                song_info = self.current_api["info_extractor"](data)
                
                if stream_url:
                    self.current_stream_url = stream_url
                    self.current_song_info = song_info
                    
                    # 设置音频源并播放
                    self.player.setSource(QUrl(stream_url))
                    self.audio_output.setVolume(0.7)  # 设置音量为70%
                    self.player.play()
                    
                    # 触发播放开始信号
                    self.playback_started.emit(song_info)
                    return
            
            # 如果无法获取有效URL，尝试下一个API
            print(f"API {self.current_api['name']} 没有返回有效的音乐URL，尝试另一个API")
            self.retry_timer.start(500)  # 500毫秒后重试
            
        except Exception as e:
            print(f"从API获取音乐时出错: {e}")
            self.retry_timer.start(1000)  # 1秒后重试
    
    def stop_playback(self):
        """停止播放音乐"""
        if not self.is_playing:
            return
        
        self.is_playing = False
        self.retry_timer.stop()
        self.health_check_timer.stop()  # 停止健康检查
        self.player.stop()
        self.current_stream_url = None
        self.current_song_info = None
        self.playback_stopped.emit()
    
    def handle_player_error(self, error, error_string):
        """处理播放器错误"""
        print(f"播放器错误: {error} - {error_string}")
        if self.is_playing:
            # 尝试下一个API
            self.retry_timer.start(1000)
    
    def on_media_status_changed(self, status):
        """监听媒体状态变化"""
        from PyQt6.QtMultimedia import QMediaPlayer
        
        # 记录状态变化，帮助调试
        status_names = {
            QMediaPlayer.MediaStatus.NoMedia: "NoMedia",
            QMediaPlayer.MediaStatus.LoadingMedia: "LoadingMedia",
            QMediaPlayer.MediaStatus.LoadedMedia: "LoadedMedia",
            QMediaPlayer.MediaStatus.StalledMedia: "StalledMedia",
            QMediaPlayer.MediaStatus.BufferingMedia: "BufferingMedia",
            QMediaPlayer.MediaStatus.BufferedMedia: "BufferedMedia",
            QMediaPlayer.MediaStatus.EndOfMedia: "EndOfMedia",
            QMediaPlayer.MediaStatus.InvalidMedia: "InvalidMedia"
        }
        status_name = status_names.get(status, f"未知状态({status})")
        print(f"冥想音频状态变化: {status_name}")
        
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            print("冥想音频播放结束")
            # 音频播放完毕，循环播放
            if self.is_playing and self.current_stream_url:
                self.try_next_api()
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            print(f"无效的媒体: {self.current_stream_url}")
            if self.is_playing:
                self.retry_timer.start(500)
        elif status == QMediaPlayer.MediaStatus.NoMedia and self.is_playing:
            # 如果播放器处于无媒体状态但我们认为应该在播放，可能是出现了问题
            print("冥想音频媒体丢失")
            self.is_playing = False
            self.playback_stopped.emit()
    
    def on_playback_state_changed(self, state):
        """监听播放状态变化"""
        from PyQt6.QtMultimedia import QMediaPlayer
        
        state_names = {
            QMediaPlayer.PlaybackState.StoppedState: "StoppedState",
            QMediaPlayer.PlaybackState.PlayingState: "PlayingState",
            QMediaPlayer.PlaybackState.PausedState: "PausedState"
        }
        state_name = state_names.get(state, f"未知状态({state})")
        print(f"冥想音频播放状态变化: {state_name}")
        
        if state == QMediaPlayer.PlaybackState.StoppedState and self.is_playing:
            # 如果播放器停止但我们认为应该在播放，可能是出现了问题
            print("冥想音频播放意外停止")
            self.is_playing = False
            self.playback_stopped.emit()
    
    def check_playback_health(self):
        """定期检查播放状态是否健康"""
        from PyQt6.QtMultimedia import QMediaPlayer
        
        # 如果显示正在播放，但实际已停止或暂停，尝试恢复
        if self.is_playing and (
            self.player.playbackState() == QMediaPlayer.PlaybackState.StoppedState or 
            self.player.playbackState() == QMediaPlayer.PlaybackState.PausedState
        ):
            print("健康检查：播放状态不一致，自动恢复")
            self.try_next_api()

# 单例模式，确保只有一个音乐播放器实例
_instance = None

def get_music_player():
    """获取音乐播放器单例"""
    global _instance
    if _instance is None:
        _instance = MusicPlayer()
    return _instance

# 冥想训练音频播放器类
class MeditationAudioPlayer(QObject):
    """专门用于冥想训练的音频播放器，与休息窗的音乐播放器隔离"""
    
    # 信号定义
    playback_started = pyqtSignal(str)  # 发射当前播放的歌曲信息
    playback_error = pyqtSignal(str)    # 发射播放错误信息
    playback_stopped = pyqtSignal()     # 播放停止信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化媒体播放器
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
        # 播放相关变量
        self.is_playing = False
        self.current_audio_path = None
        self.current_audio_name = None
        
        # 连接播放器信号
        self.player.errorOccurred.connect(self.handle_player_error)
        self.player.mediaStatusChanged.connect(self.on_media_status_changed)
        self.player.playbackStateChanged.connect(self.on_playback_state_changed)
    
    def play_local_audio(self, file_path, display_name=None):
        """播放本地音频文件"""
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                self.playback_error.emit(f"音频文件不存在: {file_path}")
                return False
            
            # 如果正在播放，先停止当前播放
            if self.is_playing:
                self.stop_playback()
                # 等待一下确保资源已释放
                QTimer.singleShot(50, lambda: self._play_audio_with_delay(file_path, display_name))
                return True
            
            return self._play_audio_with_delay(file_path, display_name)
        except Exception as e:
            print(f"播放本地音频时出错: {e}")
            import traceback
            traceback.print_exc()
            self.playback_error.emit(f"播放错误: {str(e)}")
            self.is_playing = False
            return False
    
    def _play_audio_with_delay(self, file_path, display_name=None):
        """在短暂延迟后播放音频，确保之前的资源已释放"""
        try:
            self.is_playing = True
            self.current_audio_path = file_path
            self.current_audio_name = display_name or os.path.basename(file_path)
            
            # 设置音频源并播放
            self.player.setSource(QUrl.fromLocalFile(file_path))
            self.audio_output.setVolume(0.7)  # 设置音量为70%
            
            # 设置播放位置为0，确保从文件开头开始播放
            self.player.setPosition(0)
            
            # 确保资源已准备好后播放
            from PyQt6.QtMultimedia import QMediaPlayer
            if self.player.mediaStatus() == QMediaPlayer.MediaStatus.LoadedMedia:
                # 如果媒体已加载，立即播放
                self.player.play()
            else:
                # 否则等待媒体加载完成后播放
                def on_loaded(status):
                    if status == QMediaPlayer.MediaStatus.LoadedMedia:
                        if self.is_playing:  # 再次检查是否应该播放
                            self.player.play()
                        # 播放后取消连接，避免重复触发
                        try:
                            self.player.mediaStatusChanged.disconnect(on_loaded)
                        except:
                            pass
                
                # 连接mediaStatusChanged信号
                self.player.mediaStatusChanged.connect(on_loaded)
                
                # 同时也立即尝试播放，如果资源准备足够快，这会立即播放
                if self.is_playing:  # 再次检查是否应该播放
                    self.player.play()
            
            # 触发播放开始信号
            self.playback_started.emit(self.current_audio_name)
            return True
        except Exception as e:
            print(f"播放本地音频时出错: {e}")
            import traceback
            traceback.print_exc()
            self.is_playing = False
            self.playback_error.emit(f"播放错误: {str(e)}")
            return False
    
    def toggle_playback(self):
        """切换播放状态"""
        if self.is_playing:
            self.stop_playback()
            return False
        elif self.current_audio_path:
            # 恢复之前的音频
            return self.play_local_audio(self.current_audio_path, self.current_audio_name)
        return False
    
    def stop_playback(self):
        """停止播放音乐"""
        if not self.is_playing:
            return
        
        # 标记为非播放状态
        self.is_playing = False
        
        # 停止播放器
        self.player.stop()
        
        # 重置位置
        self.player.setPosition(0)
        
        # 发出停止信号
        self.playback_stopped.emit()
        
        # 记录停止日志，帮助调试
        print(f"冥想音频已停止播放: {self.current_audio_name}")
    
    def handle_player_error(self, error, error_string):
        """处理播放器错误"""
        print(f"冥想音频播放器错误: {error} - {error_string}")
        self.playback_error.emit(f"播放错误: {error_string}")
        self.is_playing = False
    
    def on_media_status_changed(self, status):
        """监听媒体状态变化"""
        from PyQt6.QtMultimedia import QMediaPlayer
        
        # 记录状态变化，帮助调试
        status_names = {
            QMediaPlayer.MediaStatus.NoMedia: "NoMedia",
            QMediaPlayer.MediaStatus.LoadingMedia: "LoadingMedia",
            QMediaPlayer.MediaStatus.LoadedMedia: "LoadedMedia",
            QMediaPlayer.MediaStatus.StalledMedia: "StalledMedia",
            QMediaPlayer.MediaStatus.BufferingMedia: "BufferingMedia",
            QMediaPlayer.MediaStatus.BufferedMedia: "BufferedMedia",
            QMediaPlayer.MediaStatus.EndOfMedia: "EndOfMedia",
            QMediaPlayer.MediaStatus.InvalidMedia: "InvalidMedia"
        }
        status_name = status_names.get(status, f"未知状态({status})")
        print(f"冥想音频状态变化: {status_name}")
        
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            print("冥想音频播放结束")
            # 音频播放完毕，循环播放
            if self.is_playing and self.current_audio_path:
                # 使用定时器延迟重新开始播放，避免资源冲突
                self.player.setPosition(0)
                QTimer.singleShot(50, self.player.play)
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            print(f"无效的媒体: {self.current_audio_path}")
            self.is_playing = False
            self.playback_error.emit(f"无效的音频文件")
        elif status == QMediaPlayer.MediaStatus.NoMedia and self.is_playing:
            # 如果播放器处于无媒体状态但我们认为应该在播放，可能是出现了问题
            print("冥想音频媒体丢失")
            self.is_playing = False
            self.playback_stopped.emit()
    
    def on_playback_state_changed(self, state):
        """监听播放状态变化"""
        from PyQt6.QtMultimedia import QMediaPlayer
        
        state_names = {
            QMediaPlayer.PlaybackState.StoppedState: "StoppedState",
            QMediaPlayer.PlaybackState.PlayingState: "PlayingState",
            QMediaPlayer.PlaybackState.PausedState: "PausedState"
        }
        state_name = state_names.get(state, f"未知状态({state})")
        print(f"冥想音频播放状态变化: {state_name}")
        
        if state == QMediaPlayer.PlaybackState.StoppedState and self.is_playing:
            # 如果播放器停止但我们认为应该在播放，可能是出现了问题
            print("冥想音频播放意外停止")
            self.is_playing = False
            self.playback_stopped.emit()

# 冥想音频播放器单例
_meditation_player_instance = None

def get_meditation_audio_player():
    """获取冥想音频播放器单例"""
    global _meditation_player_instance
    if _meditation_player_instance is None:
        _meditation_player_instance = MeditationAudioPlayer()
    return _meditation_player_instance 