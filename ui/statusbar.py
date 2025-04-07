from aqt import mw
from PyQt6.QtWidgets import QLabel, QHBoxLayout, QWidget
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QCursor
from ..config import get_config, get_pomodoro_timer, get_timer_label, set_timer_label, get_active_timer_values
from ..constants import STATUSBAR_ICON, STATUSBAR_PAUSE_ICON
import datetime
import time


class CountdownInfoLabel(QLabel):
    """倒计时和连续专注天数信息标签"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextFormat(Qt.TextFormat.RichText)
        self.updateCountdownDisplay()
    
    def updateCountdownDisplay(self):
        """更新倒计时和连续专注天数显示"""
        try:
            # 每次都重新读取配置，确保数据最新
            config = get_config()
            
            # 检查是否应该显示倒计时和连续专注信息
            if not config.get("show_countdown_info", True):
                self.setVisible(False)
                return
                
            target_date_str = config.get("countdown_target_date", "")
            target_name = config.get("countdown_target_name", "")
            consecutive_days = config.get("consecutive_focus_days", 0)
            
            display_text = ""
            
            # 如果设置了目标日期，计算倒计时天数
            if target_date_str and target_name:
                try:
                    parts = target_date_str.split("-")
                    if len(parts) == 3:
                        year, month, day = map(int, parts)
                        target_date = QDate(year, month, day)
                        
                        if target_date.isValid():
                            current_date = QDate.currentDate()
                            days_left = current_date.daysTo(target_date)
                            
                            if days_left >= 0:
                                # 使用灰色显示天数
                                colored_days = f'<span style="color:#888888;">{days_left}</span>'
                                display_text += f"距离{target_name}还有{colored_days}天"
                except Exception as e:
                    print(f"计算倒计时出错: {e}")
            
            # 添加连续专注天数
            if consecutive_days > 0:
                if display_text:
                    display_text += " | "
                # 使用灰色显示天数
                colored_days = f'<span style="color:#888888;">{consecutive_days}</span>'
                display_text += f"已连续专注{colored_days}天"
            
            # 添加打卡任务连续天数
            try:
                from ..storage import get_storage
                storage = get_storage()
                
                # 获取用户选择显示在状态栏的打卡任务 - 每次重新读取最新配置
                displayed_tasks = config.get("statusbar_checkin_tasks", [])
                
                if displayed_tasks:
                    # 重新获取最新的任务数据
                    tasks = storage.get_checkin_tasks()
                    
                    # 过滤出需要在状态栏显示的任务
                    filtered_tasks = [task for task in tasks if task['id'] in displayed_tasks]
                    
                    # 显示任务的连续打卡天数
                    for task in filtered_tasks:
                        if display_text:
                            display_text += " | "
                        
                        task_name = task['name']
                        streak_days = task['streak_days']
                        
                        # 使用灰色显示天数
                        colored_days = f'<span style="color:#888888;">{streak_days}</span>'
                        display_text += f"连续{task_name}{colored_days}天"
            except Exception as e:
                print(f"显示打卡任务连续天数出错: {e}")
            
            if display_text:
                # 设置整体文本为浅灰色
                display_text = f'<span style="color:#999999;">{display_text}</span>'
                self.setText(display_text)
                self.setVisible(True)
            else:
                # 即使没有内容显示，如果开启了显示选项，也应该保留空间
                self.setText("")
                self.setVisible(False)
            
            # 强制刷新显示
            self.repaint()
        except RuntimeError as e:
            # 捕获C++对象已删除的错误
            if "has been deleted" in str(e):
                print(f"CountdownInfoLabel已被删除: {e}")
            else:
                raise
        except Exception as e:
            print(f"更新倒计时显示出错: {e}")


class PomodoroTimerLabel(QLabel):
    """自定义QLabel类，只显示番茄钟图标和时间，支持鼠标点击和双击事件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setTextFormat(Qt.TextFormat.RichText)
        
        # 获取当前激活的番茄钟时间和自定义图标
        pomo_minutes, _ = get_active_timer_values()
        config = get_config()
        icon = config.get("statusbar_icon", STATUSBAR_ICON)
        colored_icon = f'<span style="color:#4CAF50;">{icon}</span>'
        
        # 初始显示配置的番茄钟时间而不是00:00
        self.setText(f"{colored_icon} {pomo_minutes:02d}:00")
        
        self.setToolTip("单击暂停/继续，双击结束番茄钟")
        # 添加防抖标志和时间戳
        self.last_click_time = 0
        self.click_debounce_ms = 500  # 防抖间隔，毫秒
        # 添加一个标志，表示番茄钟是否被主动停止过
        self.timer_manually_stopped = False
        
    def updateTimerDisplay(self, timer):
        """更新计时器显示"""
        if timer and timer.remaining_seconds > 0:
            mins, secs = divmod(timer.remaining_seconds, 60)
            
            # 使用配置的自定义图标
            config = get_config()
            icon = config.get("statusbar_icon", STATUSBAR_ICON)
            colored_icon = f'<span style="color:#4CAF50;">{icon}</span>'
            
            # 构建新的显示文本
            if timer.is_paused:
                pauseText = f"{colored_icon} {STATUSBAR_PAUSE_ICON} {mins:02d}:{secs:02d}"
                self.setText(pauseText)
            else:
                normalText = f"{colored_icon} {mins:02d}:{secs:02d}"
                self.setText(normalText)
        else:
            # 如果没有计时，显示当前激活的番茄钟时长
            pomo_minutes, _ = get_active_timer_values()
            # 使用配置的自定义图标
            config = get_config()
            icon = config.get("statusbar_icon", STATUSBAR_ICON)
            colored_icon = f'<span style="color:#4CAF50;">{icon}</span>'
            
            self.setText(f"{colored_icon} {pomo_minutes:02d}:00")
    
    def mousePressEvent(self, event):
        """处理鼠标点击事件"""
        from ..pomodoro import PomodoroTimer
        from ..config import get_pomodoro_timer
        from ..hooks import start_pomodoro_manually, toggle_pomodoro_timer
        from ..rest_dialog import rest_dialog_active
        
        # 检查休息弹窗是否活跃，如果活跃则忽略点击
        if rest_dialog_active:
            super().mousePressEvent(event)
            return
            
        # 获取当前时间戳（毫秒）
        current_time = int(time.time() * 1000)
        
        # 检查是否在防抖期内
        if current_time - self.last_click_time < self.click_debounce_ms:
            super().mousePressEvent(event)
            return
            
        # 更新最后点击时间
        self.last_click_time = current_time
        
        # 获取计时器实例
        timer = PomodoroTimer.instance
        if timer is None:
            timer = get_pomodoro_timer()
        
        if event.button() == Qt.MouseButton.LeftButton:
            # 如果番茄钟被主动停止过，需要重置标志
            if self.timer_manually_stopped:
                self.timer_manually_stopped = False
                super().mousePressEvent(event)
                return
            
            if timer and timer.isActive():
                # 切换暂停/继续状态
                toggle_pomodoro_timer()
            else:
                # 如果计时器不活跃，则启动新的番茄钟
                start_pomodoro_manually()
        
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """处理鼠标双击事件，无论之前处于什么状态，立即暂停并显示退出对话框"""
        from ..pomodoro import PomodoroTimer
        from ..config import get_pomodoro_timer
        from ..hooks import show_pomodoro_exit_dialog, start_pomodoro_manually
        from ..rest_dialog import rest_dialog_active
        
        # 检查休息弹窗是否活跃，如果活跃则忽略双击
        if rest_dialog_active:
            super().mouseDoubleClickEvent(event)
            return
            
        # 获取当前时间戳（毫秒）
        current_time = int(time.time() * 1000)
        
        # 更新最后点击时间，防止双击后的单击被触发
        self.last_click_time = current_time
        
        if event.button() == Qt.MouseButton.LeftButton:
            # 获取计时器实例
            timer = PomodoroTimer.instance
            if timer is None:
                timer = get_pomodoro_timer()
            
            # 检查计时器是否活跃
            if timer and timer.isActive():
                # 无论之前状态如何，都先暂停计时器
                timer.pause()
                
                # 然后显示退出对话框
                show_pomodoro_exit_dialog()
            else:
                # 如果计时器不活跃，则启动新的番茄钟
                start_pomodoro_manually()
        
        super().mouseDoubleClickEvent(event)


class PomodoroStatusWidget(QWidget):
    """番茄钟状态栏组件，包含倒计时信息和番茄钟计时器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # 番茄钟计时器
        self.timer_label = PomodoroTimerLabel(self)
        layout.addWidget(self.timer_label)
        
        # 倒计时和连续专注天数信息
        self.info_label = CountdownInfoLabel(self)
        layout.addWidget(self.info_label)
        
        # 设置初始显示
        self.update_display()
    
    def update_display(self):
        """更新状态栏显示"""
        try:
            # 首先检查组件是否被删除
            if not self.isVisible() or not self.window():
                return
                
            # 更新倒计时和连续专注天数信息
            if hasattr(self, 'info_label') and self.info_label and self.info_label.isVisible():
                try:
                    # 强制刷新状态栏信息
                    self.info_label.updateCountdownDisplay()
                except RuntimeError as e:
                    if "has been deleted" in str(e):
                        pass
                    else:
                        raise
            
            # 更新番茄钟计时器显示
            if hasattr(self, 'timer_label') and self.timer_label and self.timer_label.isVisible():
                try:
                    timer = get_pomodoro_timer()
                    if timer and timer.isActive():
                        self.timer_label.updateTimerDisplay(timer)
                    else:
                        # 更新为默认显示
                        pomo_minutes, _ = get_active_timer_values()
                        config = get_config()
                        icon = config.get("statusbar_icon", STATUSBAR_ICON)
                        colored_icon = f'<span style="color:#4CAF50;">{icon}</span>'
                        self.timer_label.setText(f"{colored_icon} {pomo_minutes:02d}:00")
                except RuntimeError as e:
                    if "has been deleted" in str(e):
                        pass
                    else:
                        raise
        except Exception as e:
            print(f"更新状态栏显示出错: {e}")


# 全局变量，保存状态栏组件实例
_status_widget = None

def get_status_widget():
    """获取状态栏组件实例"""
    global _status_widget
    return _status_widget

def show_timer_in_statusbar(show=None):
    """在状态栏中显示或隐藏计时器"""
    global _status_widget
    
    if show is None:
        # 如果没有指定，获取配置中的显示设置
        show = get_config().get("show_timer_in_statusbar", True)
    
    # 获取Anki主窗口状态栏
    statusbar = mw.statusBar()
    
    # 检查状态栏组件是否已存在
    if _status_widget:
        try:
            # 如果存在，先检查状态栏组件是否有效
            if not _status_widget.isVisible() or not _status_widget.window():
                # 如果组件不可见或已被删除，先移除它
                try:
                    statusbar.removeWidget(_status_widget)
                    _status_widget.deleteLater()
                except Exception as e:
                    print(f"移除失效状态栏组件出错: {e}")
                _status_widget = None
            else:
                # 组件有效，根据显示设置显示或隐藏
                _status_widget.setVisible(show)
        except RuntimeError as e:
            # 捕获C++对象已删除的错误
            if "has been deleted" in str(e):
                _status_widget = None
            else:
                raise
    
    # 如果需要显示但组件不存在，创建新组件
    if show and not _status_widget:
        try:
            # 创建新组件
            _status_widget = PomodoroStatusWidget(statusbar)
            statusbar.addWidget(_status_widget)
            _status_widget.show()
        except Exception as e:
            print(f"创建状态栏组件出错: {e}")
    
    return _status_widget
