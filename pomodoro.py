from aqt import mw
from PyQt6.QtCore import QTimer, QDate
from PyQt6.QtGui import QColor
from .config import get_config, set_pomodoro_timer, get_timer_label
from .constants import STATUSBAR_ICON, STATUSBAR_PAUSE_ICON, log, DEFAULT_SOUND_EFFECT_FILE
from .storage import get_storage
import datetime
import time


class PomodoroTimer(QTimer):
    # 添加类属性，用于实现单例模式
    instance = None
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.remaining_seconds = 0
        self.total_seconds = 0
        self.timeout.connect(self.update_timer)
        self.is_paused = False  # 添加暂停状态标志
        self.current_session_id = None  # 当前番茄钟会话ID
        self.current_pause_id = None  # 当前暂停记录ID
        self.storage = get_storage()  # 获取存储实例
        
        # 设置当前实例为类的实例属性
        PomodoroTimer.instance = self
        
        set_pomodoro_timer(self)

    def start_timer(self, minutes):
        """Starts the Pomodoro timer for the given number of minutes."""
        from .ui import show_timer_in_statusbar

        config = get_config()  # Use our config getter

        if not config.get("enabled", True):
            log("Pomodoro timer disabled in config.")
            return
        
        if minutes <= 0:
            log(f"Invalid Pomodoro duration: {minutes} minutes. Timer not started.")
            return
            
        # 正常计时模式
        self.total_seconds = minutes * 60
        self.remaining_seconds = self.total_seconds
        self.is_paused = False  # 确保开始时不处于暂停状态
        
        # 记录番茄钟开始
        self.current_session_id = self.storage.start_pomodoro(minutes)
        
        log(f"Pomodoro timer started for {minutes} minutes.")
        self.update_display()
        self.start(1000)  # Tick every second
        show_timer_in_statusbar(config.get("show_statusbar_timer", True))

    def stop_timer(self):
        """停止计时器并清除显示"""
        if not self.isActive():
            return
        self.stop()
        self.remaining_seconds = 0
        
        # 清除显示
        def _clear_display():
            self.remaining_seconds = 0
            self.total_seconds = 0
            self.update_display()

        mw.progress.single_shot(10, _clear_display)

    def update_timer(self):
        """Called every second to decrease remaining time and check for finish."""
        if self.is_paused:
            # 如果处于暂停状态，不更新倒计时，但要确保显示更新
            self.update_display()
            return
            
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.update_display()
        else:
            from .hooks import on_pomodoro_finished

            log("Pomodoro timer finished.")
            
            # 记录番茄钟完成
            if self.current_session_id is not None:
                actual_duration = self.total_seconds
                self.storage.complete_pomodoro(self.current_session_id, actual_duration)
                self.current_session_id = None
                
                # 更新连续专注天数
                self.update_consecutive_focus_days()
                
            # 播放结束音效
            config = get_config()
            if config.get("sound_effect_enabled", False):
                try:
                    from PyQt6.QtCore import QTimer
                    sound_file = config.get("sound_effect_file", DEFAULT_SOUND_EFFECT_FILE)
                    # 确保音效只播放一次
                    log(f"番茄钟计时结束，准备播放音效: {sound_file}")
                    # 使用延迟调用，确保UI更新和音频设备不冲突
                    QTimer.singleShot(200, lambda: self._play_pomodoro_end_sound(sound_file))
                except Exception as e:
                    log(f"准备播放番茄钟结束音效时出错: {e}")
                    import traceback
                    traceback.print_exc()
                
            # 停止计时器
            self.stop()
            
            # 回调完成事件
            on_pomodoro_finished()
            
    def _play_pomodoro_end_sound(self, sound_file):
        """实际播放番茄钟结束音效的方法，通过延迟调用避免冲突"""
        try:
            from .music_player import get_music_player
            from .constants import DEFAULT_SOUND_EFFECT_FILE
            
            log(f"执行番茄钟结束音效播放: {sound_file}")
            player = get_music_player()
            result = player.play_sound_effect(sound_file)
            
            if not result:
                log(f"播放番茄钟结束音效失败: {sound_file}")
                # 尝试播放默认音效作为备选
                if sound_file != DEFAULT_SOUND_EFFECT_FILE:
                    log(f"尝试播放默认音效: {DEFAULT_SOUND_EFFECT_FILE}")
                    player.play_sound_effect(DEFAULT_SOUND_EFFECT_FILE)
        except Exception as e:
            log(f"播放番茄钟结束音效时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def update_consecutive_focus_days(self):
        """更新连续专注天数统计"""
        config = get_config()
        today = datetime.date.today().strftime("%Y-%m-%d")
        last_focus_date = config.get("last_focus_date", "")
        consecutive_days = config.get("consecutive_focus_days", 0)
        
        if last_focus_date == today:
            # 今天已经计算过了，不需要再次增加
            return
            
        if not last_focus_date:
            # 第一次完成番茄钟
            consecutive_days = 1
        else:
            try:
                # 将字符串转换为日期对象
                last_date = datetime.datetime.strptime(last_focus_date, "%Y-%m-%d").date()
                today_date = datetime.datetime.strptime(today, "%Y-%m-%d").date()
                
                # 计算日期差
                date_diff = (today_date - last_date).days
                
                if date_diff == 1:
                    # 连续的下一天
                    consecutive_days += 1
                elif date_diff > 1:
                    # 中断了，重新开始计数
                    consecutive_days = 1
                # 如果date_diff为0，说明是同一天，保持不变
            except Exception as e:
                log(f"计算连续专注天数出错: {e}")
                consecutive_days = 1
        
        # 更新配置
        config["last_focus_date"] = today
        config["consecutive_focus_days"] = consecutive_days
        
        # 保存配置
        from .config import save_config
        save_config()
        
        # 更新状态栏显示
        def _update_display():
            try:
                # 获取状态栏组件并更新显示
                from .ui.statusbar import get_status_widget
                status_widget = get_status_widget()
                if status_widget:
                    status_widget.update_display()
            except Exception as e:
                log(f"更新连续专注天数显示出错: {e}")
        
        # 使用单次计时器确保在主线程中执行
        mw.progress.single_shot(100, _update_display)

    def update_display(self):
        def _update():
            try:
                from .ui import show_timer_in_statusbar
                from .ui.statusbar import get_status_widget

                # 获取状态栏组件
                status_widget = get_status_widget()
                if status_widget and not status_widget.isVisible():
                    # 如果组件存在但不可见，说明可能已被Qt标记为删除
                    # 重新创建状态栏组件
                    log("状态栏组件不可见，尝试重新创建")
                    show_timer_in_statusbar(True)
                    return
                
                if status_widget and not status_widget.isHidden():
                    # 确保组件存在且未被隐藏
                    try:
                        # 直接使用组件的更新方法，捕获可能的异常
                        status_widget.update_display()
                    except RuntimeError as e:
                        # 如果出现C++对象已删除的错误，重新创建组件
                        if "has been deleted" in str(e):
                            log(f"状态栏组件已被删除，尝试重新创建: {e}")
                            show_timer_in_statusbar(True)
                        else:
                            # 其他RuntimeError，重新抛出
                            raise
                else:
                    # 如果状态栏组件不存在，确保创建它
                    show_timer_in_statusbar(True)
            except Exception as e:
                # 捕获并记录所有异常，但不中断程序
                log(f"更新显示时出错: {e}")

        # 确保在主线程执行UI更新
        mw.progress.single_shot(10, _update)
        
    def pause(self):
        """暂停番茄钟计时"""
        if not self.is_paused and self.isActive():
            self.is_paused = True
            
            # 记录暂停事件
            if self.current_session_id is not None:
                self.current_pause_id = self.storage.record_pause(self.current_session_id)
                
            log("Pomodoro timer paused.")
            self.update_display()
            
    def resume(self):
        """恢复番茄钟计时，无条件启动计时器"""
        log(f"恢复计时器: 当前状态 is_paused={self.is_paused}, isActive={self.isActive()}")
        
        # 无论之前状态如何，都将暂停标志设为False
        self.is_paused = False
        
        # 记录恢复事件
        if self.current_pause_id is not None:
            self.storage.record_resume(self.current_pause_id)
            self.current_pause_id = None
            
        log("Pomodoro timer resumed - 无条件启动计时")
        
        # 无条件重置和启动计时器
        if not self.isActive():
            self.start(1000)  # 如果计时器未激活，重新启动
        
        # 更新显示
        self.update_display()
        # 再次延迟更新以确保UI正确显示
        QTimer.singleShot(200, lambda: self.update_display())
    
    def abandon(self):
        """中途放弃番茄钟"""
        if self.isActive():
            actual_duration = self.total_seconds - self.remaining_seconds
            
            # 记录放弃事件
            if self.current_session_id is not None:
                self.storage.abandon_pomodoro(self.current_session_id, actual_duration)
                self.current_session_id = None
                
            log("Pomodoro timer abandoned.")
            self.stop_timer()

    def is_active(self):
        """提供与isActive方法的兼容性"""
        return self.isActive()
