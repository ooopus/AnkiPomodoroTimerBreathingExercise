from PyQt6.QtCore import Qt, QPropertyAnimation, QTimer, QPoint
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget,
    QGraphicsDropShadowEffect, QApplication
)
from PyQt6.QtGui import QColor, QFont

from aqt import mw
from aqt.utils import tooltip

from ..constants import log
from ..hooks import start_pomodoro_manually


class TimerReminderDialog(QDialog):
    """番茄计时提醒弹窗"""
    
    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self.setWindowTitle("番茄计时提醒")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # 透明背景
        self.setMinimumSize(350, 180)  # 设置最小尺寸
        
        # 标记该会话不再提醒
        self.do_not_remind_again = False
        
        # 拖动相关变量
        self.dragging = False
        self.drag_position = None
        
        self.init_ui()
        
        # 设置窗口位置
        self.center_on_anki_window()
        
        # 添加淡入动画
        self.setWindowOpacity(0)
        self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_animation.setDuration(500)
        self.fade_in_animation.setStartValue(0)
        self.fade_in_animation.setEndValue(1)
        self.fade_in_animation.start()
    
    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 创建一个用于背景的主容器，添加阴影和圆角
        container = QWidget(self)
        container.setObjectName("timerReminderContainer")
        container.setStyleSheet("""
            QWidget#timerReminderContainer {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        # 创建阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 0)
        container.setGraphicsEffect(shadow)
        
        # 容器的布局
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(15, 15, 15, 15)
        
        # 标题部分
        title_layout = QHBoxLayout()
        
        # 标题图标和文字
        icon_label = QLabel("🍅")
        icon_label.setFont(QFont("", 16))
        title_layout.addWidget(icon_label)
        
        title_label = QLabel("番茄钟提醒")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # 关闭按钮
        close_btn = QPushButton("×")
        close_btn.setStyleSheet("""
            QPushButton {
                font-size: 20px;
                font-weight: bold;
                color: #666;
                border: none;
                background: transparent;
            }
            QPushButton:hover {
                color: #F44336;
            }
        """)
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.reject)
        title_layout.addWidget(close_btn)
        
        container_layout.addLayout(title_layout)
        
        # 添加分隔线
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #e0e0e0;")
        container_layout.addWidget(separator)
        
        # 提醒内容
        message_label = QLabel("您已学习一段时间，是否开启番茄计时以提高专注力？")
        message_label.setStyleSheet("font-size: 14px; color: #333; margin: 10px 0;")
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(message_label)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        
        # 本次不再提醒按钮
        no_remind_btn = QPushButton("本次不再提醒")
        no_remind_btn.setStyleSheet("""
            QPushButton {
                background-color: #ECEFF1;
                color: #546E7A;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #CFD8DC;
            }
        """)
        no_remind_btn.clicked.connect(self.do_not_remind)
        button_layout.addWidget(no_remind_btn)
        
        # 空白间隔
        button_layout.addStretch()
        
        # 立即开启按钮
        start_now_btn = QPushButton("立即开启")
        start_now_btn.setStyleSheet("""
            QPushButton {
                background-color: #81C784;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #66BB6A;
            }
        """)
        start_now_btn.clicked.connect(self.start_pomodoro)
        button_layout.addWidget(start_now_btn)
        
        container_layout.addLayout(button_layout)
        
        # 将容器添加到主布局
        main_layout.addWidget(container)
    
    def center_on_anki_window(self):
        """将窗口居中显示在Anki主窗口上"""
        if mw:
            geometry = mw.geometry()
            x = geometry.x() + (geometry.width() - self.width()) // 2
            y = geometry.y() + (geometry.height() - self.height()) // 2
            self.move(x, y)
        else:
            # 如果无法获取Anki主窗口，则居中显示在屏幕上
            screen = QApplication.primaryScreen().geometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)
    
    def start_pomodoro(self):
        """开启番茄钟"""
        self.accept()
        start_pomodoro_manually()
    
    def do_not_remind(self):
        """本次不再提醒"""
        self.do_not_remind_again = True
        self.accept()
        tooltip("本次会话将不再提醒开启番茄钟", period=2000)
    
    def mousePressEvent(self, event):
        """鼠标按下事件，用于拖动窗口"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件，用于拖动窗口"""
        if event.buttons() & Qt.MouseButton.LeftButton and self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件，用于拖动窗口"""
        self.dragging = False
        event.accept()
    
    def closeEvent(self, event):
        """重写关闭事件，添加淡出动画"""
        self.fade_out_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_animation.setDuration(300)
        self.fade_out_animation.setStartValue(1)
        self.fade_out_animation.setEndValue(0)
        self.fade_out_animation.finished.connect(super().closeEvent)
        self.fade_out_animation.start()
        event.ignore()  # 忽略原始关闭事件


def show_timer_reminder_dialog():
    """显示番茄钟提醒弹窗，返回是否选择了"本次不再提醒" """
    dialog = TimerReminderDialog()
    dialog.exec()
    return dialog.do_not_remind_again 