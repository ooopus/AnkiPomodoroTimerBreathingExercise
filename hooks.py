from aqt import mw
from aqt.utils import showInfo, tooltip
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFrame, QApplication
from .constants import DEFAULT_POMODORO_MINUTES, log
from .config import get_config, get_pomodoro_timer, save_config, set_pomodoro_timer, get_active_timer_values
from .pomodoro import PomodoroTimer
from .rest_dialog import show_rest_dialog, rest_dialog_active
from .storage import get_storage
import time
import datetime

# 添加全局变量，跟踪当前牌组使用记录
current_deck_id = None
current_deck_usage_id = None

# 添加智能番茄提醒的全局变量
review_start_time = None
review_reminder_sent = False
do_not_remind_this_session = False
anki_start_time = time.time()  # 记录Anki启动时间
timer_started_this_session = False  # 本次Anki启动后是否开始过番茄计时

# --- Anki 钩子函数 ---


def get_current_deck_info():
    """获取当前牌组信息"""
    try:
        # 检查当前是否在复习界面
        if not mw.state == "review":
            log(f"获取牌组信息：当前不在复习界面，状态为 {mw.state}")
            return None, None, None, None
            
        # 获取当前牌组ID和名称
        deck_id = str(mw.col.decks.current()['id'])
        deck_name = mw.col.decks.current()['name']
        log(f"获取牌组信息：成功，ID={deck_id}, 名称={deck_name}")
        
        # 判断是否是子牌组
        if "::" in deck_name:
            # 获取父牌组名称
            parent_name = "::".join(deck_name.split("::")[:-1])
            
            # 获取所有牌组，检查兼容性
            all_decks = mw.col.decks.all()
            log(f"获取牌组信息：尝试查找父牌组 {parent_name}")
            
            for deck_info in all_decks:
                # 检查对象类型，适配新版Anki API
                try:
                    # 新版Anki使用具有name和id属性的对象
                    if hasattr(deck_info, 'name') and hasattr(deck_info, 'id'):
                        current_deck_name = deck_info.name
                        current_deck_id = str(deck_info.id)
                    else:
                        # 旧版方式
                        current_deck_id, current_deck = deck_info
                        current_deck_name = current_deck.name if hasattr(current_deck, 'name') else current_deck
                        
                    if current_deck_name == parent_name:
                        parent_id = current_deck_id
                        log(f"获取牌组信息：找到父牌组，ID={parent_id}, 名称={parent_name}")
                        return deck_id, deck_name, parent_id, parent_name
                except Exception as e:
                    log(f"获取牌组信息：处理牌组时出错 {str(e)}")
                    continue
            
            # 如果没找到父牌组，可能是直接顶级牌组
            log("获取牌组信息：未找到父牌组，可能是顶级牌组")
            return deck_id, deck_name, None, None
        else:
            # 不是子牌组，直接返回
            log("获取牌组信息：不是子牌组")
            return deck_id, deck_name, None, None
    except Exception as e:
        log(f"获取牌组信息出错：{str(e)}")
        return None, None, None, None
        
def track_deck_change():
    """跟踪牌组变化并记录使用时间"""
    global current_deck_id, current_deck_usage_id
    
    # 获取当前番茄钟计时器
    timer = get_pomodoro_timer()
    if not timer or not timer.isActive() or timer.current_session_id is None:
        log("跟踪牌组变化：计时器未激活或没有会话ID")
        return

    # 获取当前牌组信息
    deck_id, deck_name, parent_id, parent_name = get_current_deck_info()
    
    log(f"跟踪牌组变化：当前牌组ID={deck_id}, 名称={deck_name}, 父牌组ID={parent_id}, 父牌组名称={parent_name}")
    
    # 如果不在复习界面，使用特殊ID表示牌组界面
    if deck_id is None:
        deck_id = "0"
        deck_name = "牌组管理界面"
        parent_id = None
        parent_name = None
        log("跟踪牌组变化：不在复习界面，使用牌组管理界面")
    
    # 如果牌组变化，结束上一个记录，开始新记录
    if current_deck_id != deck_id:
        log(f"跟踪牌组变化：牌组已变化，原ID={current_deck_id}, 新ID={deck_id}")
        # 如果有正在记录的牌组使用，结束它
        if current_deck_usage_id is not None:
            timer.storage.end_deck_usage(current_deck_usage_id)
            log(f"跟踪牌组变化：结束牌组使用，记录ID={current_deck_usage_id}")
            
        # 开始新的牌组使用记录
        current_deck_usage_id = timer.storage.start_deck_usage(
            timer.current_session_id, 
            deck_id, 
            deck_name,
            parent_id,
            parent_name
        )
        current_deck_id = deck_id
        log(f"开始记录牌组使用: {deck_name}, 记录ID={current_deck_usage_id}")
    else:
        log(f"跟踪牌组变化：牌组未变化，仍然使用 {deck_name}")


def on_reviewer_did_start(reviewer):
    """当进入复习界面时的处理函数"""
    global review_start_time, review_reminder_sent
    
    # 检查是否启用了番茄钟
    config = get_config()
    if not config.get("enabled", True):
        return
        
    # 调用牌组变化跟踪
    track_deck_change()
    
    # 初始化复习开始时间，用于智能提醒
    if mw.state == "review" and review_start_time is None:
        review_start_time = time.time()
        review_reminder_sent = False
        log(f"复习界面开始时间记录: {review_start_time}")
        
        # 设置计时器检查是否需要提醒
        QTimer.singleShot(60000, check_review_time_for_reminder)  # 每分钟检查一次


def check_review_time_for_reminder():
    """检查复习时间并在需要时显示提醒"""
    global review_start_time, review_reminder_sent, do_not_remind_this_session, timer_started_this_session
    
    # 如果用户选择了本次会话不再提醒，直接返回
    if do_not_remind_this_session:
        log("用户选择本次会话不再提醒")
        return
        
    # 如果本次Anki启动后已经开始过番茄计时，不再提醒
    if timer_started_this_session:
        log("本次Anki启动后已开始过番茄计时，不再提醒")
        do_not_remind_this_session = True
        return
        
    # 检查本次Anki启动后是否已完成过至少一个番茄钟
    storage = get_storage()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    # 使用全局变量获取应用启动时间的时间戳
    start_time = anki_start_time
    # 获取今天已完成的番茄钟数量
    completed_pomodoros = storage.get_completed_pomodoros_since(start_time, today)
    if completed_pomodoros > 0:
        log(f"本次启动后已完成{completed_pomodoros}个番茄钟，不再提醒")
        do_not_remind_this_session = True
        return
    
    # 如果不在复习界面或者还没开始记录时间，重置变量
    if mw.state != "review" or review_start_time is None:
        log(f"不在复习界面或未开始记录时间，当前状态: {mw.state}")
        # 如果离开了复习界面，重置时间跟踪
        review_start_time = None
        review_reminder_sent = False
        return
    
    # 如果已经发送过提醒，不再重复发送
    if review_reminder_sent:
        log("本次复习已发送过提醒")
        # 仍然设置下一次检查
        QTimer.singleShot(60000, check_review_time_for_reminder)
        return
    
    # 计算复习时间（分钟）
    current_time = time.time()
    review_duration_minutes = (current_time - review_start_time) / 60
    
    # 获取提醒阈值（分钟）
    reminder_threshold = get_config().get("smart_timer_reminder_minutes", 15)
    
    log(f"当前复习时间: {review_duration_minutes:.2f}分钟, 提醒阈值: {reminder_threshold}分钟")
    
    # 如果复习时间超过阈值，显示提醒
    if review_duration_minutes >= reminder_threshold:
        log("复习时间已超过阈值，触发提醒")
        review_reminder_sent = True
        
        # 确保在主线程中显示对话框
        mw.progress.single_shot(100, show_timer_reminder)
    
    # 设置下一次检查
    if mw.state == "review":
        QTimer.singleShot(60000, check_review_time_for_reminder)


def show_timer_reminder():
    """显示番茄钟提醒对话框"""
    global do_not_remind_this_session
    
    # 如果用户不想在本次会话中收到提醒，则直接返回
    if do_not_remind_this_session:
        return
    
    # 如果当前在牌组浏览界面，不显示提醒
    if mw.state == "browse":
        log("当前在牌组浏览界面，不显示番茄钟提醒")
        return
    
    # 导入函数
    from .ui import show_timer_reminder_dialog
    
    # 显示对话框
    do_not_remind_this_session = show_timer_reminder_dialog()
    
    log(f"番茄钟提醒对话框已显示，用户选择本次不再提醒: {do_not_remind_this_session}")


def on_state_did_change(new_state: str, old_state: str):
    """当状态变更时，跟踪牌组变化"""
    global review_start_time
    
    # 检查是否启用了番茄钟
    config = get_config()
    if not config.get("enabled", True):
        return
        
    # 调用牌组变化跟踪
    track_deck_change()
    
    # 处理智能提醒相关的状态变化
    if new_state == "review" and old_state != "review":
        # 进入复习界面
        if review_start_time is None:
            review_start_time = time.time()
            log(f"状态变更: 进入复习界面，开始记录时间: {review_start_time}")
            # 设置检查提醒的计时器
            QTimer.singleShot(60000, check_review_time_for_reminder)
    elif new_state != "review" and old_state == "review":
        # 离开复习界面
        log(f"状态变更: 离开复习界面，重置时间记录")
        review_start_time = None


def start_pomodoro_manually():
    """手动启动番茄钟"""
    global current_deck_id, current_deck_usage_id, timer_started_this_session
    
    # 设置本次会话已开始过番茄计时
    timer_started_this_session = True
    log("手动启动番茄钟，标记本次会话已开始过番茄计时")
    
    # 如果休息弹窗正在显示，不允许启动番茄钟
    if rest_dialog_active:
        tooltip("请先关闭休息弹窗", period=2000)
        return
    
    config = get_config()
    timer = get_pomodoro_timer()

    if not config.get("enabled", True):
        return

    # 确保只有一个计时器实例
    if timer is None or not isinstance(timer, PomodoroTimer):
        timer = PomodoroTimer(mw)
        # 确保单例属性设置正确
        PomodoroTimer.instance = timer
        set_pomodoro_timer(timer)

    # 确保在主线程操作
    def _start_timer():
        # 打印调试信息
        log(f"尝试启动番茄钟: timer={timer}, isActive={timer.isActive() if timer else None}")
        
        if not timer.isActive():
            # 使用当前激活的番茄钟设置
            pomo_minutes, _ = get_active_timer_values()
            timer.start_timer(pomo_minutes)
            tooltip("番茄钟已启动，加油！", period=2000)
            
            # 重置牌组跟踪变量
            current_deck_id = None
            current_deck_usage_id = None
            
            # 立即开始跟踪牌组
            track_deck_change()

    mw.progress.single_shot(100, _start_timer)


def on_pomodoro_finished():
    """Called when the Pomodoro timer reaches zero."""
    global current_deck_usage_id
    
    # 结束当前牌组使用记录
    if current_deck_usage_id is not None:
        timer = get_pomodoro_timer()
        if timer:
            timer.storage.end_deck_usage(current_deck_usage_id)
        current_deck_usage_id = None
    
    tooltip(
        "番茄钟时间到！", period=3000
    )
    # Ensure we are on the main thread before showing dialog
    mw.progress.single_shot(100, _after_pomodoro_finish_tasks)


def _after_pomodoro_finish_tasks():
    """Actions to perform after the Pomodoro finishes (runs on main thread)."""
    # 显示休息对话框
    QTimer.singleShot(200, show_rest_dialog)


def toggle_pomodoro_timer():
    """暂停或恢复番茄钟计时"""
    # 检查是否启用了番茄钟
    config = get_config()
    if not config.get("enabled", True):
        tooltip("请先启用番茄钟", period=2000)
        return
        
    # 如果休息弹窗正在显示，不允许暂停/恢复番茄钟
    if rest_dialog_active:
        tooltip("请先关闭休息弹窗", period=2000)
        return
        
    timer = get_pomodoro_timer()
    if not timer:
        # 如果没有计时器，尝试获取单例
        from .pomodoro import PomodoroTimer
        timer = PomodoroTimer.instance
        if not timer:
            log("无法获取计时器实例，尝试创建新的计时器")
            timer = PomodoroTimer(mw)
            PomodoroTimer.instance = timer
            set_pomodoro_timer(timer)
            return start_pomodoro_manually()
    
    log(f"Toggle pomodoro timer: isActive={timer.isActive()}, is_paused={timer.is_paused}")
    
    if timer.isActive() and not timer.is_paused:
        # 暂停计时
        log("暂停番茄钟")
        timer.pause()
        tooltip("番茄钟已暂停", period=1000)
    elif timer.isActive() and timer.is_paused:
        # 恢复计时
        log("恢复番茄钟")
        timer.resume()
        tooltip("番茄钟已恢复", period=1000)
        
        # 重新开始跟踪牌组，因为可能在暂停期间切换了牌组
        track_deck_change()
    else:
        # 如果计时器不活跃，启动新的番茄钟
        log("计时器不活跃，启动新的番茄钟")
        start_pomodoro_manually()


def show_pomodoro_exit_dialog():
    """显示退出番茄钟对话框，用户选择继续时会自动恢复计时，选择退出时会停止计时"""
    global current_deck_usage_id
    
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
        QWidget, QGraphicsDropShadowEffect, QToolButton
    )
    from PyQt6.QtCore import Qt, QPropertyAnimation
    from PyQt6.QtGui import QColor, QMouseEvent
    from .pomodoro import PomodoroTimer
    
    # 获取计时器实例
    timer = PomodoroTimer.instance
    if timer is None:
        timer = get_pomodoro_timer()
        
    if not timer or not timer.isActive():
        return
    
    # 确保计时器已暂停
    if not timer.is_paused:
        timer.pause()
    
    log(f"显示退出对话框：计时器当前状态 is_paused={timer.is_paused}")
    
    # 自定义对话框
    class ExitPomodoroDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self.setMinimumWidth(350)
            
            # 拖动相关变量
            self.dragging = False
            self.drag_position = None
            
            # 用户选择结果
            self.user_choice = "none"  # "continue", "exit", "none"
            
            self.initUI()
            
            # 淡入动画
            self.setWindowOpacity(0)
            self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity")
            self.fade_in_animation.setDuration(300)
            self.fade_in_animation.setStartValue(0)
            self.fade_in_animation.setEndValue(1)
            self.fade_in_animation.start()
        
        def initUI(self):
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(20, 20, 20, 20)
            
            # 主容器
            container = QWidget()
            container.setObjectName("container")
            container.setStyleSheet("""
                QWidget#container {
                    background-color: white;
                    border-radius: 15px;
                }
            """)
            
            # 容器阴影
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(20)
            shadow.setColor(QColor(0, 0, 0, 60))
            shadow.setOffset(0, 0)
            container.setGraphicsEffect(shadow)
            
            # 容器布局
            container_layout = QVBoxLayout(container)
            container_layout.setSpacing(15)
            
            # 标题栏 (标题+关闭按钮)
            title_bar = QWidget()
            title_bar_layout = QHBoxLayout(title_bar)
            title_bar_layout.setContentsMargins(15, 10, 15, 0)
            
            # 关闭按钮(移到左边)
            close_button = QToolButton()
            close_button.setText("×")
            close_button.setStyleSheet("""
                QToolButton {
                    color: #7f8c8d;
                    background-color: transparent;
                    border: none;
                    font-size: 20px;
                    font-weight: bold;
                }
                QToolButton:hover {
                    color: #e74c3c;
                }
            """)
            close_button.clicked.connect(self.handle_continue)
            title_bar_layout.addWidget(close_button)
            
            # 番茄钟图标和标题
            title_label = QLabel("🍅 番茄钟")
            title_label.setStyleSheet("""
                font-size: 20px;
                font-weight: bold;
                color: #e74c3c;
                font-family: "Microsoft YaHei", "SimHei", sans-serif;
            """)
            title_bar_layout.addWidget(title_label)
            title_bar_layout.addStretch()
            
            # 添加空白项以平衡布局
            spacer = QWidget()
            spacer.setFixedWidth(close_button.sizeHint().width())  # 使空白宽度与关闭按钮相同
            spacer.setStyleSheet("background-color: transparent;")
            title_bar_layout.addWidget(spacer)
            
            container_layout.addWidget(title_bar)
            
            # 消息内容
            mins, secs = divmod(timer.remaining_seconds, 60)
            message_label = QLabel(f"番茄钟正在进行中...\n当前剩余时间：{mins:02d}:{secs:02d}")
            message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            message_label.setStyleSheet("""
                font-size: 16px;
                color: #2c3e50;
                margin: 10px 0;
                line-height: 1.5;
                font-family: "Microsoft YaHei", "SimHei", sans-serif;
            """)
            container_layout.addWidget(message_label)
            
            # 按钮区域
            button_container = QWidget()
            button_layout = QHBoxLayout(button_container)
            button_layout.setContentsMargins(10, 0, 10, 10)
            button_layout.setSpacing(15)
            
            # 继续坚持按钮
            continue_button = QPushButton("继续坚持")
            continue_button.setStyleSheet("""
                QPushButton {
                    background-color: #2ecc71;
                    color: white;
                    border: none;
                    border-radius: 15px;
                    padding: 10px 20px;
                    font-size: 15px;
                    font-weight: bold;
                    font-family: "Microsoft YaHei", "SimHei", sans-serif;
                }
                QPushButton:hover {
                    background-color: #27ae60;
                }
                QPushButton:pressed {
                    background-color: #219a52;
                }
            """)
            continue_button.clicked.connect(self.handle_continue)
            button_layout.addWidget(continue_button)
            
            # 残忍退出按钮
            exit_button = QPushButton("残忍退出")
            exit_button.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    border-radius: 15px;
                    padding: 10px 20px;
                    font-size: 15px;
                    font-weight: bold;
                    font-family: "Microsoft YaHei", "SimHei", sans-serif;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
                QPushButton:pressed {
                    background-color: #a93226;
                }
            """)
            exit_button.clicked.connect(self.handle_exit)
            button_layout.addWidget(exit_button)
            
            container_layout.addWidget(button_container)
            
            main_layout.addWidget(container)
            self.setLayout(main_layout)
        
        def handle_continue(self):
            """选择继续，关闭对话框"""
            log("用户点击了'继续坚持'，将关闭对话框")
            self.user_choice = "continue"
            self.close_with_animation()
        
        def handle_exit(self):
            """选择退出，关闭对话框"""
            log("用户点击了'残忍退出'，将关闭对话框")
            self.user_choice = "exit"
            self.close_with_animation()
        
        def close_with_animation(self):
            """带动画关闭窗口"""
            self.fade_out_animation = QPropertyAnimation(self, b"windowOpacity")
            self.fade_out_animation.setDuration(200)
            self.fade_out_animation.setStartValue(1)
            self.fade_out_animation.setEndValue(0)
            self.fade_out_animation.finished.connect(self.close)
            self.fade_out_animation.start()
        
        def mousePressEvent(self, event: QMouseEvent):
            """实现窗口拖动功能 - 鼠标按下"""
            if event.button() == Qt.MouseButton.LeftButton:
                self.dragging = True
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
            
        def mouseMoveEvent(self, event: QMouseEvent):
            """实现窗口拖动功能 - 鼠标移动"""
            if self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
                self.move(event.globalPosition().toPoint() - self.drag_position)
                event.accept()
            
        def mouseReleaseEvent(self, event: QMouseEvent):
            """实现窗口拖动功能 - 鼠标释放"""
            if event.button() == Qt.MouseButton.LeftButton:
                self.dragging = False
                event.accept()
        
        def closeEvent(self, event):
            """处理窗口关闭事件"""
            if event.spontaneous() and self.user_choice == "none":
                # 点击窗口关闭按钮，视为"继续坚持"
                self.user_choice = "continue"
            
            # 接受关闭事件
            event.accept()
    
    # 创建并显示对话框
    dialog = ExitPomodoroDialog(mw)
    
    # 移动到Anki主窗口中心
    parent_geometry = mw.geometry()
    x = parent_geometry.x() + (parent_geometry.width() - dialog.width()) // 2
    y = parent_geometry.y() + (parent_geometry.height() - dialog.height()) // 2
    dialog.move(x, y)
    
    # 显示对话框并等待关闭
    dialog.exec()
    
    # 处理用户选择
    if dialog.user_choice == "exit":
        # 残忍退出 - 完全停止计时器
        log("执行退出番茄钟操作")
        
        # 结束当前牌组使用记录
        if current_deck_usage_id is not None:
            timer.storage.end_deck_usage(current_deck_usage_id)
            current_deck_usage_id = None
        
        # 停止计时器
        timer.abandon()  # 记录放弃
        timer.stop_timer()  # 停止计时
        
        # 重置计时器状态
        timer.is_paused = False
        timer.remaining_seconds = 0
        timer.total_seconds = 0
        timer.current_session_id = None
        
        # 设置状态栏标签的停止标志
        try:
            from .ui.statusbar import get_status_widget
            status_widget = get_status_widget()
            if status_widget and hasattr(status_widget, 'timer_label'):
                status_widget.timer_label.timer_manually_stopped = True
                log("已设置计时器手动停止标志")
        except Exception as e:
            log(f"设置计时器手动停止标志出错: {e}")
        
        # 更新显示
        timer.update_display()
        
        # 显示提示
        tooltip("已退出番茄钟", period=2000)
        
        # 防止鼠标事件穿透导致重新启动
        def _prevent_auto_restart():
            from .ui.statusbar import get_status_widget
            status_widget = get_status_widget()
            if status_widget and hasattr(status_widget, 'timer_label'):
                import time
                # 设置防抖时间
                status_widget.timer_label.last_click_time = int(time.time() * 1000) + 2000
                
        # 使用延迟执行
        QTimer.singleShot(50, _prevent_auto_restart)
        
    else:  # continue 或 none
        # 继续坚持 - 恢复计时
        log("执行继续计时操作")
        
        # 防止鼠标事件穿透导致误操作
        def _prevent_auto_click():
            from .ui.statusbar import get_status_widget
            status_widget = get_status_widget()
            if status_widget and hasattr(status_widget, 'timer_label'):
                import time
                # 设置防抖时间
                status_widget.timer_label.last_click_time = int(time.time() * 1000) + 1000
                
        # 立即设置防抖
        _prevent_auto_click()
        
        # 恢复计时
        timer.resume()
        
        # 更新UI
        def _update_ui():
            timer.update_display()
            tooltip("继续番茄钟计时", period=1000)
            # 重新开始跟踪牌组
            track_deck_change()
            
        # 延迟执行更新UI
        QTimer.singleShot(100, _update_ui)


def show_statistics_dialog():
    """显示统计对话框"""
    from .ui import show_statistics_dialog as show_dialog
    show_dialog(mw)

# 在插件卸载时清理状态栏组件
def cleanup_on_unload():
    from .pomodoro import PomodoroTimer
    
    # 保存进行中的番茄钟已完成时长
    if PomodoroTimer.instance and PomodoroTimer.instance.isActive():
        timer = PomodoroTimer.instance
        
        # 计算已经完成的时长
        completed_seconds = timer.total_seconds - timer.remaining_seconds
        
        # 如果有正在进行的番茄钟会话，保存已完成的时长
        if timer.current_session_id is not None and completed_seconds > 0:
            # 将session标记为未完成，但保存已经学习的时长
            log(f"保存进行中的番茄钟：会话ID={timer.current_session_id}，已完成时长={completed_seconds}秒")
            timer.storage.save_partial_pomodoro(timer.current_session_id, completed_seconds)
            
            # 更新连续专注天数（如果学习时间超过一定阈值，例如5分钟）
            if completed_seconds >= 300:  # 5分钟
                timer.update_consecutive_focus_days()
        
        # 然后停止计时器
        timer.stop_timer()
    
    # 移除状态栏组件
    try:
        from .ui.statusbar import get_status_widget
        status_widget = get_status_widget()
        if status_widget:
            mw.statusBar().removeWidget(status_widget)
            status_widget.deleteLater()
    except Exception as e:
        log(f"清理状态栏组件出错: {e}")
    
    # 清理其他资源
    save_config()

# 重置智能提醒状态
from . import hooks
hooks.do_not_remind_this_session = False
hooks.review_start_time = None
hooks.review_reminder_sent = False
hooks.timer_started_this_session = False  # 重置本次会话是否开始过番茄计时标志
