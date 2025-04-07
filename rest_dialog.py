from aqt import mw
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QUrl
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
    QApplication,
    QGraphicsDropShadowEffect,
    QToolButton,
    QMenu,
    QLineEdit,
    QFormLayout,
    QComboBox,
    QDialogButtonBox,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QMessageBox,
    QStyledItemDelegate,
    QStyle,
    QGridLayout,
    QFileDialog,
    QTextEdit,
    QFrame,
)
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QFont, QMouseEvent, QCloseEvent, QDesktopServices, QAction, QIcon
from .config import get_config, get_active_timer_values, save_config
from .storage import get_storage
from .music_player import get_music_player, get_meditation_audio_player
from .constants import DEFAULT_MEDITATION_SESSIONS
import os
import datetime

# 添加全局变量来跟踪休息弹窗状态
rest_dialog_active = False


class MeditationEditDialog(QDialog):
    """冥想训练编辑对话框"""

    def __init__(self, parent=None, item=None):
        super().__init__(parent)
        self.setWindowTitle("编辑冥想训练")
        self.setMinimumWidth(400)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        
        self.item = item  # 要编辑的项目
        self.selected_emoji = "🧘" # 默认emoji图标
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建一个带圆角和阴影的容器
        container = QWidget()
        container.setObjectName("editContainer")
        container.setStyleSheet("""
            QWidget#editContainer {
                background-color: #ffffff;
                border-radius: 10px;
                border: 1px solid #e0e5eb;
            }
        """)
        
        # 容器布局
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(15)
        
        # 标题和图标
        title_layout = QHBoxLayout()
        title_icon = QLabel("✏️")
        title_icon.setStyleSheet("""
            font-size: 18px;
        """)
        
        title_label = QLabel("编辑冥想训练")
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #34495e;
            font-family: "Microsoft YaHei", "SimHei", sans-serif;
        """)
        
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 关闭按钮
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
        close_button.clicked.connect(self.reject)
        title_layout.addWidget(close_button)
        
        container_layout.addLayout(title_layout)
        
        # 添加分隔线
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #e0e5eb;")
        container_layout.addWidget(separator)
        
        # 创建表单布局
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # 设置标签样式
        label_style = """
            QLabel {
                color: #445566;
                font-size: 14px;
                font-family: "Microsoft YaHei", "SimHei", sans-serif;
                padding-right: 8px;
            }
        """
        
        # 创建输入框
        self.name_edit = QLineEdit()
        self.name_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #e0e5eb;
                border-radius: 6px;
                padding: 8px 10px;
                background-color: #f9fafc;
                color: #34495e;
                font-size: 14px;
                font-family: "Microsoft YaHei", "SimHei", sans-serif;
                selection-background-color: #d4e9f7;
            }
            QLineEdit:focus {
                border-color: #94c2e8;
                background-color: #ffffff;
            }
            QLineEdit:hover:!focus {
                border-color: #c0d0e0;
            }
        """)
        self.name_edit.setMinimumHeight(36)
        
        self.url_edit = QLineEdit()
        self.url_edit.setStyleSheet(self.name_edit.styleSheet())
        self.url_edit.setMinimumHeight(36)
        
        # 添加emoji图标选择
        from .constants import AVAILABLE_STATUSBAR_ICONS
        
        emoji_label = QLabel("图标:")
        emoji_label.setStyleSheet(label_style)
        
        # 创建emoji选择按钮
        self.emoji_button = QPushButton(self.selected_emoji)
        self.emoji_button.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                background-color: #f5f5f5;
                border: 1px solid #dddddd;
                border-radius: 6px;
                padding: 4px 8px;
                min-width: 40px;
                max-width: 40px;
                min-height: 36px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-color: #c0c0c0;
            }
        """)
        self.emoji_button.setToolTip("点击选择图标")
        self.emoji_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.emoji_button.clicked.connect(self.show_emoji_picker)
        
        # 添加本地音频选择
        self.audio_path_edit = QLineEdit()
        self.audio_path_edit.setStyleSheet(self.name_edit.styleSheet())
        self.audio_path_edit.setMinimumHeight(36)
        self.audio_path_edit.setPlaceholderText("选择本地音频文件(mp3, wav, ogg等)")
        self.audio_path_edit.setReadOnly(True)
        
        # 添加选择音频文件的按钮
        self.browse_button = QPushButton("浏览...")
        self.browse_button.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                color: #555555;
                border: 1px solid #dddddd;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 13px;
                font-family: "Microsoft YaHei", "SimHei", sans-serif;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-color: #c0c0c0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
                padding: 6px 9px 4px 11px;
            }
        """)
        self.browse_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browse_button.clicked.connect(self.browse_audio_file)
        
        # 添加批量选择音频文件的按钮
        self.batch_browse_button = QPushButton("批量添加...")
        self.batch_browse_button.setStyleSheet(self.browse_button.styleSheet())
        self.batch_browse_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.batch_browse_button.clicked.connect(self.batch_browse_audio_files)
        
        # 创建水平布局放置emoji按钮
        emoji_layout = QHBoxLayout()
        emoji_layout.addWidget(self.emoji_button)
        emoji_layout.addStretch()
        
        # 创建水平布局放置音频输入框和浏览按钮
        audio_layout = QHBoxLayout()
        audio_layout.addWidget(self.audio_path_edit)
        audio_layout.addWidget(self.browse_button)
        
        # 如果是编辑现有项目，填充数据
        if item and isinstance(item, dict):
            self.name_edit.setText(item.get("name", ""))
            self.url_edit.setText(item.get("url", ""))
            self.audio_path_edit.setText(item.get("audio_path", ""))
            if "emoji" in item:
                self.selected_emoji = item.get("emoji")
                self.emoji_button.setText(self.selected_emoji)
        
        # 创建标签
        name_label = QLabel("名称:")
        name_label.setStyleSheet(label_style)
        url_label = QLabel("链接:")
        url_label.setStyleSheet(label_style)
        audio_label = QLabel("本地音频:")
        audio_label.setStyleSheet(label_style)
        batch_label = QLabel("批量操作:")
        batch_label.setStyleSheet(label_style)
        
        # 添加到布局
        form_layout.addRow(name_label, self.name_edit)
        form_layout.addRow(url_label, self.url_edit)
        form_layout.addRow(emoji_label, emoji_layout)
        form_layout.addRow(audio_label, audio_layout)
        form_layout.addRow(batch_label, self.batch_browse_button)
        
        container_layout.addLayout(form_layout)
        
        # 创建按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        button_box.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-family: "Microsoft YaHei", "SimHei", sans-serif;
                min-width: 90px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #2472a4;
                padding: 9px 15px 7px 17px;
            }
            QPushButton[text="取消"] {
                background-color: #f5f5f5;
                color: #666666;
                border: 1px solid #dddddd;
            }
            QPushButton[text="取消"]:hover {
                background-color: #e0e0e0;
                color: #333333;
            }
            QPushButton[text="取消"]:pressed {
                background-color: #d0d0d0;
            }
        """)
        
        # 翻译按钮文本
        ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        if ok_button:
            ok_button.setText("确定")
            ok_button.setCursor(Qt.CursorShape.PointingHandCursor)
        if cancel_button:
            cancel_button.setText("取消")
            cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
            
        container_layout.addWidget(button_box)
        
        # 添加容器到主布局
        main_layout.addWidget(container)
        
        # 设置窗口阴影
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        container.setGraphicsEffect(shadow)
        
        self.setLayout(main_layout)
    
    def show_emoji_picker(self):
        """显示emoji选择器"""
        from .constants import AVAILABLE_STATUSBAR_ICONS
        
        # 创建一个新的对话框
        emoji_dialog = QDialog(self)
        emoji_dialog.setWindowTitle("选择图标")
        emoji_dialog.setWindowFlags(emoji_dialog.windowFlags() | Qt.WindowType.FramelessWindowHint)
        emoji_dialog.setMinimumWidth(350)
        emoji_dialog.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border-radius: 10px;
                border: 1px solid #e0e5eb;
            }
        """)
        
        # 对话框布局
        emoji_layout = QVBoxLayout(emoji_dialog)
        emoji_layout.setContentsMargins(15, 15, 15, 15)
        emoji_layout.setSpacing(10)
        
        # 标题部分
        title_layout = QHBoxLayout()
        title_label = QLabel("选择图标")
        title_label.setStyleSheet("""
            font-size: 15px;
            font-weight: bold;
            color: #34495e;
            font-family: "Microsoft YaHei", "SimHei", sans-serif;
        """)
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 关闭按钮
        close_button = QToolButton()
        close_button.setText("×")
        close_button.setStyleSheet("""
            QToolButton {
                color: #7f8c8d;
                background-color: transparent;
                border: none;
                font-size: 18px;
                font-weight: bold;
            }
            QToolButton:hover {
                color: #e74c3c;
            }
        """)
        close_button.clicked.connect(emoji_dialog.reject)
        title_layout.addWidget(close_button)
        
        emoji_layout.addLayout(title_layout)
        
        # 添加分隔线
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #e0e5eb;")
        emoji_layout.addWidget(separator)
        
        # 创建一个滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #f5f5f5;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # 创建一个容器来放置emoji按钮
        emoji_container = QWidget()
        emoji_grid = QGridLayout(emoji_container)
        emoji_grid.setContentsMargins(5, 5, 5, 5)
        emoji_grid.setSpacing(5)
        
        # 一行显示的按钮数量
        cols = 8
        
        # 添加所有emoji按钮
        for i, emoji in enumerate(AVAILABLE_STATUSBAR_ICONS):
            button = QPushButton(emoji)
            button.setFixedSize(35, 35)
            button.setStyleSheet("""
                QPushButton {
                    font-size: 16px;
                    background-color: #f8f9fa;
                    border: 1px solid #e0e5eb;
                    border-radius: 6px;
                    padding: 0px;
                }
                QPushButton:hover {
                    background-color: #e8f4fc;
                    border-color: #a4d8ff;
                }
                QPushButton:pressed {
                    background-color: #d4e9f7;
                }
            """)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            
            # 创建一个闭包来处理点击事件
            def make_callback(emoji_value):
                return lambda: self.select_emoji(emoji_value, emoji_dialog)
            
            button.clicked.connect(make_callback(emoji))
            emoji_grid.addWidget(button, i // cols, i % cols)
        
        scroll_area.setWidget(emoji_container)
        emoji_layout.addWidget(scroll_area)
        
        # 显示对话框
        emoji_dialog.exec()
    
    def select_emoji(self, emoji, dialog):
        """选择emoji图标"""
        self.selected_emoji = emoji
        self.emoji_button.setText(emoji)
        dialog.accept()
    
    def browse_audio_file(self):
        """打开文件对话框选择音频文件"""
        from PyQt6.QtWidgets import QFileDialog
        
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("选择音频文件")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter("音频文件 (*.mp3 *.wav *.ogg *.flac *.m4a *.aac)")
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.audio_path_edit.setText(selected_files[0])
    
    def batch_browse_audio_files(self):
        """批量添加音频文件"""
        from PyQt6.QtWidgets import QFileDialog
        
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("选择音频文件")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setNameFilter("音频文件 (*.mp3 *.wav *.ogg *.flac *.m4a *.aac)")
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.audio_path_edit.setText("\n".join(selected_files))
    
    def get_data(self):
        """获取输入的数据"""
        # 检查是否是批量添加模式
        audio_paths = self.audio_path_edit.text().strip().split("\n")
        if len(audio_paths) > 1:  # 批量模式
            return {
                "batch_files": audio_paths,
                "is_batch": True,
                "emoji": self.selected_emoji
            }
        else:  # 单文件模式
            return {
                "name": self.name_edit.text(),
                "url": self.url_edit.text(),
                "audio_path": self.audio_path_edit.text(),
                "emoji": self.selected_emoji
            }
    
    # 添加窗口拖动能力
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.offset = event.pos()
    
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and hasattr(self, 'offset'):
            self.move(event.globalPosition().toPoint() - self.offset)


def show_styled_message_box(parent, title, text, icon=QMessageBox.Icon.Question, buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, default_button=QMessageBox.StandardButton.No):
    """显示自定义样式的消息对话框"""
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(text)
    msg_box.setIcon(icon)
    msg_box.setStandardButtons(buttons)
    msg_box.setDefaultButton(default_button)
    
    # 设置无边框窗口
    msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
    
    # 添加鼠标拖动支持
    originalMousePressEvent = msg_box.mousePressEvent
    originalMouseMoveEvent = msg_box.mouseMoveEvent
    
    def mousePressEvent(event):
        if event.button() == Qt.MouseButton.LeftButton:
            msg_box.offset = event.pos()
        if originalMousePressEvent:
            originalMousePressEvent(event)
    
    def mouseMoveEvent(event):
        if event.buttons() & Qt.MouseButton.LeftButton and hasattr(msg_box, 'offset'):
            msg_box.move(event.globalPosition().toPoint() - msg_box.offset)
        if originalMouseMoveEvent:
            originalMouseMoveEvent(event)
    
    msg_box.mousePressEvent = mousePressEvent
    msg_box.mouseMoveEvent = mouseMoveEvent
    
    # 设置样式
    msg_box.setStyleSheet("""
        QMessageBox {
            background-color: #f5f8fa;
            border: 1px solid #e0e5eb;
            border-radius: 10px;
        }
        QLabel {
            color: #34495e;
            font-size: 14px;
            font-family: "Microsoft YaHei", "SimHei", sans-serif;
            margin: 10px;
        }
        QPushButton {
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 5px 12px;
            font-size: 13px;
            font-family: "Microsoft YaHei", "SimHei", sans-serif;
            min-width: 60px;
            max-height: 25px;
        }
        QPushButton:hover {
            background-color: #2980b9;
        }
        QPushButton:pressed {
            background-color: #2472a4;
        }
        QPushButton[text="取消"], QPushButton[text="否"] {
            background-color: #f5f5f5;
            color: #666666;
            border: 1px solid #dddddd;
        }
        QPushButton[text="取消"]:hover, QPushButton[text="否"]:hover {
            background-color: #e0e0e0;
            color: #333333;
        }
        QPushButton[text="取消"]:pressed, QPushButton[text="否"]:pressed {
            background-color: #d0d0d0;
        }
    """)
    
    # 翻译按钮
    for button in msg_box.buttons():
        if msg_box.buttonRole(button) == QMessageBox.ButtonRole.AcceptRole:
            if button.text() == "Yes":
                button.setText("是")
        elif msg_box.buttonRole(button) == QMessageBox.ButtonRole.RejectRole:
            if button.text() == "No":
                button.setText("否")
        
        button.setCursor(Qt.CursorShape.PointingHandCursor)
    
    # 创建自定义标题栏
    title_widget = QWidget()
    title_layout = QHBoxLayout(title_widget)
    title_layout.setContentsMargins(10, 5, 10, 0)
    
    # 图标根据消息类型选择
    icon_text = "❓"  # 默认为问号
    if icon == QMessageBox.Icon.Information:
        icon_text = "ℹ️"
    elif icon == QMessageBox.Icon.Warning:
        icon_text = "⚠️"
    elif icon == QMessageBox.Icon.Critical:
        icon_text = "❌"
    
    # 添加图标
    icon_label = QLabel(icon_text)
    icon_label.setStyleSheet("font-size: 14px;")
    title_layout.addWidget(icon_label)
    
    # 添加标题
    title_label = QLabel(title)
    title_label.setStyleSheet("""
        font-weight: bold; 
        font-size: 14px;
        color: #34495e;
        font-family: "Microsoft YaHei", "SimHei", sans-serif;
    """)
    title_layout.addWidget(title_label)
    title_layout.addStretch()
    
    # 添加关闭按钮
    close_button = QToolButton()
    close_button.setText("×")
    close_button.setStyleSheet("""
        QToolButton {
            color: #7f8c8d;
            background-color: transparent;
            border: none;
            font-size: 16px;
            font-weight: bold;
        }
        QToolButton:hover {
            color: #e74c3c;
        }
    """)
    close_button.clicked.connect(msg_box.reject)
    title_layout.addWidget(close_button)
    
    # 创建分隔线
    separator = QWidget()
    separator.setFixedHeight(1)
    separator.setStyleSheet("background-color: #e0e5eb;")
    
    # 获取消息框布局
    layout = msg_box.layout()
    
    # QMessageBox使用QGridLayout，需要特殊处理
    if layout and isinstance(layout, QGridLayout):
        # 移动原有内容向下
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item:
                # 获取项目的位置信息
                pos = layout.getItemPosition(i)
                if pos:
                    row, col, rowSpan, colSpan = pos
                    # 向下移动两行以便在顶部添加标题和分隔线
                    widget = item.widget()
                    if widget:
                        layout.removeWidget(widget)
                        layout.addWidget(widget, row + 2, col, rowSpan, colSpan)
        
        # 添加标题栏和分隔线
        layout.addWidget(title_widget, 0, 0, 1, -1)  # 第一行添加标题，跨越所有列
        layout.addWidget(separator, 1, 0, 1, -1)  # 第二行添加分隔线，跨越所有列
    
    return msg_box.exec()


class ConfirmDialog(QDialog):
    """自定义确认对话框"""
    
    def __init__(self, parent=None, title="确认", message="", icon_text="❓"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 设置拖动支持
        self.dragging = False
        self.offset = None
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建内容容器
        container = QWidget()
        container.setObjectName("confirmContainer")
        container.setStyleSheet("""
            QWidget#confirmContainer {
                background-color: #ffffff;
                border-radius: 10px;
                border: 1px solid #e0e5eb;
            }
        """)
        
        # 容器布局
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 15, 20, 20)
        container_layout.setSpacing(10)
        
        # 标题栏
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(8)
        
        # 图标
        icon_label = QLabel(icon_text)
        icon_label.setStyleSheet("""
            font-size: 18px;
        """)
        title_layout.addWidget(icon_label)
        
        # 标题
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 15px;
            font-weight: bold;
            color: #34495e;
            font-family: "Microsoft YaHei", "SimHei", sans-serif;
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 关闭按钮
        close_button = QToolButton()
        close_button.setText("×")
        close_button.setStyleSheet("""
            QToolButton {
                color: #7f8c8d;
                background-color: transparent;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QToolButton:hover {
                color: #e74c3c;
            }
        """)
        close_button.clicked.connect(self.reject)
        title_layout.addWidget(close_button)
        
        container_layout.addLayout(title_layout)
        
        # 分隔线
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #e0e5eb;")
        container_layout.addWidget(separator)
        
        # 消息文本
        message_label = QLabel(message)
        message_label.setStyleSheet("""
            font-size: 14px;
            color: #34495e;
            font-family: "Microsoft YaHei", "SimHei", sans-serif;
            padding: 10px 5px;
        """)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setWordWrap(True)
        container_layout.addWidget(message_label)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        
        # 是按钮
        yes_button = QPushButton("是")
        yes_button.setObjectName("yes_button")  # 设置对象名称
        yes_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 12px;
                font-size: 13px;
                font-family: "Microsoft YaHei", "SimHei", sans-serif;
                min-width: 60px;
                max-height: 25px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #2472a4;
            }
        """)
        yes_button.setCursor(Qt.CursorShape.PointingHandCursor)
        yes_button.clicked.connect(self.accept)
        
        # 否按钮
        no_button = QPushButton("否")
        no_button.setObjectName("no_button")  # 设置对象名称
        no_button.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                color: #666666;
                border: 1px solid #dddddd;
                border-radius: 5px;
                padding: 5px 12px;
                font-size: 13px;
                font-family: "Microsoft YaHei", "SimHei", sans-serif;
                min-width: 60px;
                max-height: 25px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                color: #333333;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        no_button.setCursor(Qt.CursorShape.PointingHandCursor)
        no_button.clicked.connect(self.reject)
        
        # 设置默认按钮为"否"
        no_button.setDefault(True)
        no_button.setFocus()
        
        button_layout.addStretch()
        button_layout.addWidget(yes_button)
        button_layout.addWidget(no_button)
        button_layout.addStretch()
        
        container_layout.addLayout(button_layout)
        
        # 设置对话框阴影
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        container.setGraphicsEffect(shadow)
        
        main_layout.addWidget(container)
        
        # 设置初始大小
        self.setMinimumWidth(280)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.offset = event.pos()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.offset)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            event.accept()

def show_confirm_dialog(parent, title, message, icon_text="❓"):
    """显示自定义确认对话框，返回True表示确认，False表示取消"""
    dialog = ConfirmDialog(parent, title, message, icon_text)
    result = dialog.exec()
    return result == QDialog.DialogCode.Accepted

class MeditationListDialog(QDialog):
    """冥想训练列表管理对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("冥想训练管理")
        self.setMinimumSize(500, 400)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        
        # 加载当前冥想训练列表
        self.config = get_config()
        self.meditation_sessions = self.config.get("meditation_sessions", [])
        
        # 设置窗口可调整大小
        self.setMouseTracking(True)
        self.resizing = False
        self.resize_direction = None
        self.border_width = 6  # 拖拽区域宽度
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建一个带圆角和阴影的容器
        container = QWidget()
        container.setObjectName("meditationContainer")
        container.setStyleSheet("""
            QWidget#meditationContainer {
                background-color: #ffffff;
                border-radius: 10px;
                border: 1px solid #e0e5eb;
            }
        """)
        
        # 容器布局
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(15)
        
        # 标题和图标
        title_layout = QHBoxLayout()
        title_icon = QLabel("🧘")
        title_icon.setStyleSheet("""
            font-size: 20px;
        """)
        
        title_label = QLabel("冥想训练管理")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #34495e;
            font-family: "Microsoft YaHei", "SimHei", sans-serif;
        """)
        
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 关闭按钮
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
        close_button.clicked.connect(self.reject)
        title_layout.addWidget(close_button)
        
        container_layout.addLayout(title_layout)
        
        # 添加分隔线
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #e0e5eb;")
        container_layout.addWidget(separator)
        
        # 列表
        self.list_widget = DragDropListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #f9fafc;
                border: 1px solid #e0e5eb;
                border-radius: 8px;
                padding: 5px;
                outline: none;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 6px;
                margin: 3px 0;
                color: #445566;
                font-family: "Microsoft YaHei", "SimHei", sans-serif;
            }
            QListWidget::item:selected {
                background-color: #e1f0fa;
                color: #2980b9;
                font-weight: bold;
            }
            QListWidget::item:hover:!selected {
                background-color: #f0f7fc;
                color: #3498db;
            }
            QListWidget::item:selected:active {
                background-color: #d4e9f7;
            }
            QScrollBar:vertical {
                border: none;
                background: #f5f5f5;
                width: 8px;
                border-radius: 4px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0d0e0;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0b0c0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
        """)
        self.list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.list_widget.itemSelectionChanged.connect(self.update_buttons)
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        
        # 添加所有项目到列表
        self.refresh_list()
        
        container_layout.addWidget(self.list_widget)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 创建统一的按钮样式
        button_style = """
            QPushButton {
                background-color: #f2f6fa;
                color: #445566;
                border: 1px solid #e0e5eb;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
                font-family: "Microsoft YaHei", "SimHei", sans-serif;
                min-width: 90px;
            }
            QPushButton:hover {
                background-color: #e1f0fa;
                color: #2980b9;
                border-color: #b0d0e5;
            }
            QPushButton:pressed {
                background-color: #d4e9f7;
                border-color: #a0c0da;
                padding: 9px 15px 7px 17px;
            }
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #bbbbbb;
                border-color: #dddddd;
            }
        """
        
        # 添加按钮
        self.add_button = QPushButton("添加", self)
        self.add_button.setStyleSheet(button_style)
        self.add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_button.clicked.connect(self.add_item)
        button_layout.addWidget(self.add_button)
        
        # 编辑按钮
        self.edit_button = QPushButton("编辑", self)
        self.edit_button.setStyleSheet(button_style)
        self.edit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_button.clicked.connect(self.edit_item)
        self.edit_button.setEnabled(False)  # 初始禁用
        button_layout.addWidget(self.edit_button)
        
        # 删除按钮
        self.delete_button = QPushButton("删除", self)
        self.delete_button.setStyleSheet(button_style)
        self.delete_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_button.clicked.connect(self.delete_item)
        self.delete_button.setEnabled(False)  # 初始禁用
        button_layout.addWidget(self.delete_button)
        
        # 恢复默认按钮
        self.reset_button = QPushButton("恢复默认", self)
        self.reset_button.setStyleSheet(button_style)
        self.reset_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_button.clicked.connect(self.reset_to_default)
        button_layout.addWidget(self.reset_button)
        
        container_layout.addLayout(button_layout)
        
        # 对话框底部按钮
        dialog_buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        dialog_buttons.accepted.connect(self.save_changes)
        dialog_buttons.rejected.connect(self.reject)
        
        # 自定义底部按钮样式
        dialog_buttons.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-size: 14px;
                font-family: "Microsoft YaHei", "SimHei", sans-serif;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #2472a4;
                padding: 9px 19px 7px 21px;
            }
            QPushButton[text="取消"] {
                background-color: #f5f5f5;
                color: #666666;
                border: 1px solid #dddddd;
            }
            QPushButton[text="取消"]:hover {
                background-color: #e0e0e0;
                color: #333333;
            }
            QPushButton[text="取消"]:pressed {
                background-color: #d0d0d0;
            }
        """)
        
        # 翻译按钮文本
        ok_button = dialog_buttons.button(QDialogButtonBox.StandardButton.Ok)
        cancel_button = dialog_buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if ok_button:
            ok_button.setText("确定")
            ok_button.setCursor(Qt.CursorShape.PointingHandCursor)
        if cancel_button:
            cancel_button.setText("取消")
            cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        container_layout.addWidget(dialog_buttons)
        
        # 添加容器到主布局
        main_layout.addWidget(container)
        
        # 设置窗口阴影
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 0)
        container.setGraphicsEffect(shadow)
        
        self.setLayout(main_layout)
    
    def refresh_list(self):
        """刷新列表显示"""
        self.list_widget.clear()
        for session in self.meditation_sessions:
            name = session.get("name", "未命名")
            
            # 创建带图标的列表项
            item = QListWidgetItem()
            item.setText("  " + name)  # 添加空格预留图标位置
            item.setData(Qt.ItemDataRole.UserRole, session)
            
            # 获取用户设置的emoji图标，如果没有则使用默认值
            icon = session.get("emoji", "🧘")
            
            # 设置左侧图标
            item.setIcon(QIcon())  # 创建一个空图标以保留空间
            # 在setData中存储图标文本，以便在绘制时使用
            item.setData(Qt.ItemDataRole.UserRole + 1, icon)
            
            self.list_widget.addItem(item)
        
        # 自定义列表项的绘制方式
        self.list_widget.setItemDelegate(MeditationItemDelegate(self.list_widget))
    
    def update_buttons(self):
        """根据选择状态更新按钮状态"""
        has_selection = len(self.list_widget.selectedItems()) > 0
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
    
    def add_item(self):
        """添加新项目"""
        dialog = MeditationEditDialog(self)
        if dialog.exec():
            new_item_data = dialog.get_data()
            
            # 检查是否是批量添加模式
            if new_item_data.get("is_batch", False):
                # 保存当前选中的emoji，用于批量添加
                self.current_emoji = new_item_data.get("emoji", "🎵")
                self.add_batch_items(new_item_data["batch_files"])
                return
                
            # 单个文件添加模式
            new_item = new_item_data
            # 修改条件，名称必填，但URL和音频路径至少要有一个
            if new_item["name"] and (new_item["url"] or new_item["audio_path"]):
                self.meditation_sessions.append(new_item)
                self.refresh_list()
                
                # 选中新添加的项目并滚动到可见区域
                last_item = self.list_widget.item(self.list_widget.count() - 1)
                self.list_widget.setCurrentItem(last_item)
                self.list_widget.scrollToItem(last_item)
    
    def add_batch_items(self, file_paths):
        """批量添加音频文件
        
        Args:
            file_paths: 音频文件路径列表
        """
        import os
        
        # 获取当前选择的emoji
        emoji = "🎵"  # 默认使用音乐图标
        if hasattr(self, 'current_emoji'):
            emoji = self.current_emoji
        
        for file_path in file_paths:
            # 提取文件名作为名称（不含扩展名）
            file_name = os.path.basename(file_path)
            name = os.path.splitext(file_name)[0]
            
            # 创建新项目
            new_item = {
                "name": name,
                "url": "",
                "audio_path": file_path,
                "emoji": emoji
            }
            
            # 添加到列表
            self.meditation_sessions.append(new_item)
            list_item = QListWidgetItem(name)
            list_item.setData(Qt.ItemDataRole.UserRole, new_item)
            self.list_widget.addItem(list_item)
            
        # 如果添加了项目，选中最后一个
        if file_paths:
            last_item = self.list_widget.item(self.list_widget.count() - 1)
            self.list_widget.setCurrentItem(last_item)
            self.list_widget.scrollToItem(last_item)
            
            # 显示添加成功的消息
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "批量添加成功",
                f"成功添加 {len(file_paths)} 个音频文件。\n文件名已自动设置为名称。",
                QMessageBox.StandardButton.Ok
            )
    
    def edit_item(self):
        """编辑选中项目"""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]
        item_data = item.data(Qt.ItemDataRole.UserRole)
        
        dialog = MeditationEditDialog(self, item_data)
        if dialog.exec():
            # 获取编辑后的数据
            edited_data = dialog.get_data()
            
            # 确保至少有一个非空的URL或音频路径
            if edited_data["name"] and (edited_data["url"] or edited_data["audio_path"]):
                # 更新数据
                row = self.list_widget.row(item)
                self.meditation_sessions[row] = edited_data
                
                # 刷新列表以显示更新
                self.refresh_list()
                
                # 重新选择编辑的项目
                if row < self.list_widget.count():
                    self.list_widget.setCurrentRow(row)
    
    def delete_item(self):
        """删除选中项目"""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]
        row = self.list_widget.row(item)
        
        # 使用新的确认对话框
        if show_confirm_dialog(self, "确认删除", f'确定要删除"{item.text().strip()}"吗？'):
            # 从列表中移除
            self.list_widget.takeItem(row)
            self.meditation_sessions.pop(row)
    
    def reset_to_default(self):
        """恢复默认列表"""
        # 使用新的确认对话框
        if show_confirm_dialog(self, "确认恢复", "确定要恢复默认冥想训练列表吗？当前自定义的项目将被删除。", "⚠️"):
            self.meditation_sessions = DEFAULT_MEDITATION_SESSIONS.copy()
            self.refresh_list()
    
    def save_changes(self):
        """保存更改"""
        # 根据列表当前顺序更新meditation_sessions
        self.meditation_sessions = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item_data = item.data(Qt.ItemDataRole.UserRole)
            self.meditation_sessions.append(item_data)
        
        # 保存到配置
        self.config["meditation_sessions"] = self.meditation_sessions
        save_config()
        
        self.accept()

    # 添加窗口拖动能力
    def mousePressEvent(self, event):
        if self.resizing:
            self.resizing = True
            self.start_pos = event.pos()
            self.start_geometry = self.geometry()
            event.accept()
        elif event.button() == Qt.MouseButton.LeftButton:
            edge = self.get_edge(event.pos())
            if edge:
                self.resizing = True
                self.resize_direction = edge
                self.start_pos = event.pos()
                self.start_geometry = self.geometry()
                event.accept()
            else:
                self.offset = event.pos()
    
    def mouseMoveEvent(self, event):
        if self.resizing and event.buttons() & Qt.MouseButton.LeftButton:
            # 处理窗口拖拽调整大小
            new_geo = self.geometry()
            
            # 根据拖拽方向直接将窗口边缘设置为鼠标当前位置
            if 'left' in self.resize_direction:
                # 左边缘直接设为鼠标当前位置的x坐标（相对于屏幕）
                new_width = new_geo.right() - event.globalPosition().toPoint().x()
                # 确保不小于最小宽度
                if new_width >= self.minimumWidth():
                    new_geo.setLeft(event.globalPosition().toPoint().x())
                
            elif 'right' in self.resize_direction:
                # 右边缘直接设为鼠标当前位置的x坐标（相对于屏幕）
                new_geo.setRight(event.globalPosition().toPoint().x())
            
            if 'top' in self.resize_direction:
                # 上边缘直接设为鼠标当前位置的y坐标（相对于屏幕）
                new_height = new_geo.bottom() - event.globalPosition().toPoint().y()
                # 确保不小于最小高度
                if new_height >= self.minimumHeight():
                    new_geo.setTop(event.globalPosition().toPoint().y())
                
            elif 'bottom' in self.resize_direction:
                # 下边缘直接设为鼠标当前位置的y坐标（相对于屏幕）
                new_geo.setBottom(event.globalPosition().toPoint().y())
            
            # 确保新几何形状符合最小尺寸要求
            if new_geo.width() >= self.minimumWidth() and new_geo.height() >= self.minimumHeight():
                self.setGeometry(new_geo)
            
        elif event.buttons() & Qt.MouseButton.LeftButton and hasattr(self, 'offset'):
            # 处理窗口拖动
            self.move(event.globalPosition().toPoint() - self.offset)
        else:
            # 改变鼠标光标
            edge = self.get_edge(event.pos())
            if edge:
                if edge in ['top', 'bottom']:
                    self.setCursor(Qt.CursorShape.SizeVerCursor)
                elif edge in ['left', 'right']:
                    self.setCursor(Qt.CursorShape.SizeHorCursor)
                elif edge in ['top-left', 'bottom-right']:
                    self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                elif edge in ['top-right', 'bottom-left']:
                    self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.resizing = False
            self.resize_direction = None
            # 恢复默认鼠标样式
            self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def get_edge(self, pos):
        """确定鼠标位于窗口的哪个边缘"""
        x, y = pos.x(), pos.y()
        width, height = self.width(), self.height()
        
        # 判断鼠标位于哪个边缘
        left = x < self.border_width
        right = x > width - self.border_width
        top = y < self.border_width
        bottom = y > height - self.border_width
        
        if top and left:
            return 'top-left'
        elif top and right:
            return 'top-right'
        elif bottom and left:
            return 'bottom-left'
        elif bottom and right:
            return 'bottom-right'
        elif top:
            return 'top'
        elif bottom:
            return 'bottom'
        elif left:
            return 'left'
        elif right:
            return 'right'
        
        return None

    def leaveEvent(self, event):
        """当鼠标离开窗口时，恢复默认鼠标样式"""
        self.setCursor(Qt.CursorShape.ArrowCursor)


class RestDialog(QDialog):
    """显示番茄钟结束后的休息对话框，包含休息时间倒计时和操作按钮"""

    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self.setWindowTitle("休息时间")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # 透明背景
        self.setMinimumSize(400, 350)  # 整体缩小窗口大小
        
        # 拖动相关变量
        self.dragging = False
        self.drag_position = None
        
        # 获取当前激活的番茄钟设置中的休息时间
        _, rest_minutes = get_active_timer_values()
        self.rest_seconds = rest_minutes * 60
        self.total_rest_seconds = self.rest_seconds
        self.is_resting = False
        self.current_rest_id = None
        self.storage = get_storage()
        
        # 创建计时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        
        # 当前显示的激励消息ID
        self.current_message_id = None
        
        self.init_ui()
        
        # 设置窗口位置
        self.center_on_anki_window()
        
        # 添加淡入动画
        self.setWindowOpacity(0)
        self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_animation.setDuration(500)
        self.fade_in_animation.setStartValue(0)
        self.fade_in_animation.setEndValue(1)
        
        # 确保窗口尺寸正确计算
        self.adjustSize()
        
        self.fade_in_animation.start()
    
    def center_on_anki_window(self):
        """将窗口居中显示在Anki主窗口上"""
        parent = self.parent()
        if parent:
            parent_geometry = parent.geometry()
            # 获取窗口推荐大小
            size = self.sizeHint()
            # 计算居中位置
            x = parent_geometry.x() + (parent_geometry.width() - size.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - size.height()) // 2
            # 使用move方法设置位置
            self.move(x, y)
        else:
            # 如果没有父窗口，居中在屏幕上
            screen = QApplication.primaryScreen().geometry()
            size = self.sizeHint()
            x = (screen.width() - size.width()) // 2
            y = (screen.height() - size.height()) // 2
            self.move(x, y)
    
    def init_ui(self):
        """初始化UI组件"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)  # 缩小外边距
        main_layout.setSpacing(8)  # 减小组件间距
        
        # 创建圆角背景容器
        container = QWidget(self)
        container.setObjectName("container")  # 设置对象名称，以便后续查找
        container.setStyleSheet("""
            QWidget#container {
                background-color: #ffffff;
                border-radius: 12px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 25, 20, 20)  # 缩小内边距
        container_layout.setSpacing(12)  # 减小组件间距
        
        # 标题和关闭按钮容器
        title_bar = QWidget()
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(0, 0, 0, 0)
        
        # 关闭按钮(移到左边)
        close_button = QToolButton()
        close_button.setText("×")
        close_button.setStyleSheet("""
            QToolButton {
                color: #7f8c8d;
                background-color: transparent;
                border: none;
                font-size: 16px;  /* 缩小关闭按钮字体 */
                font-weight: bold;
            }
            QToolButton:hover {
                color: #e74c3c;
            }
        """)
        close_button.clicked.connect(self.close)
        title_bar_layout.addWidget(close_button)
        
        # 标题标签
        title_label = QLabel("休息时间")
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 18px;  /* 缩小标题字体 */
                font-weight: bold;
                padding: 4px;  /* 减少内边距 */
                font-family: "Microsoft YaHei", "SimHei", sans-serif;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_bar_layout.addWidget(title_label, 1)  # 添加伸展因子，使标题居中
        
        # 添加空白项以平衡布局
        spacer = QWidget()
        spacer.setFixedWidth(close_button.sizeHint().width())  # 使空白宽度与关闭按钮相同
        spacer.setStyleSheet("background-color: transparent;")
        title_bar_layout.addWidget(spacer)
        
        # 添加标题栏到主容器
        container_layout.addWidget(title_bar)
        
        # 倒计时标签
        self.time_label = QLabel()
        self.time_label.setStyleSheet("""
            QLabel {
                color: #3498db;
                font-size: 36px;  /* 缩小时间字体 */
                font-weight: bold;
                padding: 8px;  /* 减少内边距 */
                font-family: "Microsoft YaHei", "SimHei", sans-serif;
            }
        """)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setMinimumHeight(60)  # 减小高度但确保数字显示完整
        self.update_time_display()
        container_layout.addWidget(self.time_label)
        
        # 提示文本和滚动区域
        self.info_label = QLabel("番茄钟时间到！请选择休息或开始新番茄", self)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 13px;  /* 缩小提示文字字体 */
                margin: 8px 0;  /* 减少上下边距 */
                font-family: "Microsoft YaHei", "SimHei", sans-serif;
                line-height: 1.3;
                background-color: transparent;
            }
        """)
        self.info_label.setMinimumHeight(40)  # 减小高度但确保文字显示完整
        
        # 创建滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.info_label)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)  # 移除边框
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0b0c0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
        """)
        
        # 初始隐藏滚动条
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 使标签可点击
        self.info_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.info_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.info_label.mousePressEvent = self.on_info_label_clicked
        
        # 是否显示全文的标志
        self.is_showing_full_text = False
        self.full_text = ""
        
        # 保存原始高度
        self.original_height = None
        
        # 创建激励消息按钮容器
        self.message_controls = QWidget()
        message_controls_layout = QHBoxLayout(self.message_controls)
        message_controls_layout.setContentsMargins(0, 0, 0, 0)
        message_controls_layout.setSpacing(10)
        message_controls_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 居中对齐按钮
        
        # 添加按钮 (+)
        self.add_message_button = QToolButton()
        self.add_message_button.setText("+")
        self.add_message_button.setToolTip("分享当下的快乐给未来的自己")
        self.add_message_button.setStyleSheet("""
            QToolButton {
                color: #2ecc71;
                background-color: transparent;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QToolButton:hover {
                color: #27ae60;
            }
        """)
        self.add_message_button.clicked.connect(self.add_user_message)
        message_controls_layout.addWidget(self.add_message_button)
        
        # 删除按钮 (-)
        self.remove_message_button = QToolButton()
        self.remove_message_button.setText("-")
        self.remove_message_button.setToolTip("删除当前显示的消息")
        self.remove_message_button.setStyleSheet("""
            QToolButton {
                color: #e74c3c;
                background-color: transparent;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QToolButton:hover {
                color: #c0392b;
            }
        """)
        self.remove_message_button.clicked.connect(self.remove_current_message)
        message_controls_layout.addWidget(self.remove_message_button)
        
        # 初始隐藏这些按钮
        self.add_message_button.setVisible(False)
        self.remove_message_button.setVisible(False)
        
        # 创建竖直布局容器来放置消息文本和控制按钮
        info_container = QWidget()
        info_container_layout = QVBoxLayout(info_container)
        info_container_layout.setContentsMargins(0, 0, 0, 0)
        info_container_layout.setSpacing(2)
        info_container_layout.addWidget(self.scroll_area)  # 使用滚动区域而不是直接添加info_label
        info_container_layout.addWidget(self.message_controls)
        
        # 增加加固定高度的间隔，确保控制按钮不会被遮挡
        spacer = QWidget()
        spacer.setFixedHeight(10)
        info_container_layout.addWidget(spacer)
        
        container_layout.addWidget(info_container)
        
        # 按钮布局
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(4, 0, 4, 4)  # 减少按钮容器边距
        btn_layout.setSpacing(15)  # 减小按钮间距
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 设置按钮水平居中
        
        # 休息按钮
        self.rest_button = QPushButton("开始休息", self)
        self.rest_button.clicked.connect(self.toggle_rest)
        self.rest_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 12px;  /* 减小圆角 */
                padding: 4px 16px;  /* 缩小内边距 */
                font-size: 14px;  /* 缩小字体 */
                font-weight: bold;
                font-family: "Microsoft YaHei", "SimHei", sans-serif;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1f6da8;
            }
        """)
        self.rest_button.setMinimumWidth(110)  # 缩小宽度
        self.rest_button.setFixedHeight(35)  # 缩小高度
        btn_layout.addWidget(self.rest_button)
        
        # 新番茄按钮
        self.new_pomodoro_button = QPushButton("开始新番茄", self)
        self.new_pomodoro_button.clicked.connect(self.start_new_pomodoro)
        self.new_pomodoro_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 12px;  /* 减小圆角 */
                padding: 4px 16px;  /* 缩小内边距 */
                font-size: 14px;  /* 缩小字体 */
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
        self.new_pomodoro_button.setMinimumWidth(110)  # 缩小宽度
        self.new_pomodoro_button.setFixedHeight(35)  # 缩小高度
        btn_layout.addWidget(self.new_pomodoro_button)
        
        container_layout.addWidget(btn_container)
        
        # 咖啡图标和休息文本布局（初始隐藏）
        self.resting_widget = QWidget()
        self.resting_widget.setStyleSheet("""
            QWidget {
                background-color: #e8f5fe;
                border-radius: 10px;
                padding: 5px;
            }
        """)
        resting_layout = QHBoxLayout(self.resting_widget)
        resting_layout.setContentsMargins(5, 6, 5, 6)  # 减少左右边距
        resting_layout.setSpacing(4)  # 减少组件之间的间距
        
        # 冥想训练按钮
        self.meditation_button = QPushButton("🧘 冥想训练")
        self.meditation_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #2980b9;
                border: none;
                padding: 5px 8px;
                font-size: 13px;
                font-weight: 600;
                font-family: "Microsoft YaHei", "SimHei", sans-serif;
                text-align: left;
            }
            QPushButton:hover {
                text-decoration: underline;
            }
            QPushButton:focus {
                outline: none;
            }
        """)
        self.meditation_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.meditation_button.setFixedHeight(30)
        self.meditation_button.setMinimumWidth(100)  # 设置最小宽度
        self.meditation_button.clicked.connect(self.show_meditation_menu)
        
        # 休息中文本
        self.resting_label = QLabel("正在享受休息时光...")
        self.resting_label.setStyleSheet("""
            font-size: 12px;  /* 调小字体 */
            color: #2980b9; 
            font-weight: bold;
            font-family: "Microsoft YaHei", "SimHei", sans-serif;
        """)
        self.resting_label.setMinimumHeight(30)  # 减小高度
        self.resting_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 音乐播放按钮
        self.music_button = QPushButton("🎵 播放音乐")
        self.music_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #2980b9;
                border: none;
                padding: 5px 8px;
                font-size: 13px;
                font-weight: 600;
                font-family: "Microsoft YaHei", "SimHei", sans-serif;
                text-align: right;
            }
            QPushButton:hover {
                text-decoration: underline;
            }
            QPushButton:focus {
                outline: none;
            }
        """)
        self.music_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.music_button.setFixedHeight(30)
        self.music_button.setMinimumWidth(100)  # 设置最小宽度
        self.music_button.clicked.connect(self.toggle_music)
        
        # 使用固定宽度的空白填充，以改善布局
        resting_layout.addWidget(self.meditation_button)
        resting_layout.addStretch(1)  # 添加可伸缩空间
        resting_layout.addWidget(self.resting_label)
        resting_layout.addStretch(1)  # 添加可伸缩空间
        resting_layout.addWidget(self.music_button)
        
        # 歌曲信息标签（初始隐藏）
        self.song_info_label = QLabel("")
        self.song_info_label.setWordWrap(True)
        self.song_info_label.setStyleSheet("""
            font-size: 13px;
            color: #7f8c8d;
            font-style: italic;
            margin-top: 5px;
            font-family: "Microsoft YaHei", "SimHei", sans-serif;
        """)
        self.song_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.song_info_label.setMinimumHeight(20)
        self.song_info_label.setVisible(False)
        container_layout.addWidget(self.song_info_label)
        
        self.resting_widget.setVisible(False)
        container_layout.addWidget(self.resting_widget)
        
        # 加载冥想训练列表
        self.meditation_sessions = get_config().get("meditation_sessions", DEFAULT_MEDITATION_SESSIONS.copy())
        
        # 添加容器到主布局
        main_layout.addWidget(container)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        container.setGraphicsEffect(shadow)
        
        self.setLayout(main_layout)
    
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
    
    def toggle_rest(self):
        """切换休息状态"""
        if not self.is_resting:
            # 开始休息
            self.is_resting = True
            self.rest_button.setVisible(False)
            self.new_pomodoro_button.setText("结束休息")
            self.new_pomodoro_button.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 15px;
                    padding: 5px 20px;
                    font-size: 15px;
                    font-weight: bold;
                    font-family: "Microsoft YaHei", "SimHei", sans-serif;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #1f6da8;
                }
            """)
            self.resting_widget.setVisible(True)
            self.info_label.setText("休息一下，放松身心，稍后将更有精力继续学习...")
            
            # 重新获取并设置休息时间
            _, rest_minutes = get_active_timer_values()
            self.rest_seconds = rest_minutes * 60
            self.total_rest_seconds = self.rest_seconds  # 保存总时间用于计算进度
            self.update_time_display()  # 更新时间显示
            
            # 启动计时器
            self.timer.start(1000)  # 每秒更新一次
            
            # 记录休息开始
            self.current_rest_id = self.storage.start_rest()
            
            # 检查是否启用了自动播放音乐
            if get_config().get("auto_play_music", False):
                music_player = get_music_player()
                if not music_player.is_playing:
                    # 模拟点击播放音乐按钮
                    self.toggle_music()
        else:
            # 手动结束休息
            self.timer.stop()
            self.is_resting = False
            self.resting_widget.setVisible(False)
            # 隐藏休息按钮，不再显示
            self.rest_button.setVisible(False)
            
            # 立即重置rest_dialog_active状态，确保状态栏图标可点击
            global rest_dialog_active
            rest_dialog_active = False
            
            # 停止音乐播放
            music_player = get_music_player()
            if music_player.is_playing:
                music_player.stop_playback()
                self.clear_song_info()
            
            # 停止冥想音频播放
            try:
                meditation_player = get_meditation_audio_player()
                if meditation_player.is_playing:
                    meditation_player.stop_playback()
            except:
                pass  # 如果获取播放器失败，忽略错误
            
            # 重置倒计时为零
            self.rest_seconds = 0
            self.update_time_display()
            self.info_label.setText("你已手动结束休息，可以开始新的番茄钟了！")
            
            # 居中显示和美化开始新番茄按钮
            self.new_pomodoro_button.setText("开始新番茄")
            self.new_pomodoro_button.setStyleSheet("""
                QPushButton {
                    background-color: #2ecc71;
                    color: white;
                    border: none;
                    border-radius: 15px;
                    padding: 5px 20px;
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
            
            # 修改按钮布局，使新番茄按钮居中
            btn_layout = self.new_pomodoro_button.parent().layout()
            btn_layout.setAlignment(self.new_pomodoro_button, Qt.AlignmentFlag.AlignCenter)
            
            # 记录休息结束
            if self.current_rest_id is not None:
                self.storage.end_rest(self.current_rest_id)
                self.current_rest_id = None
    
    def update_timer(self):
        """更新倒计时"""
        if not self.is_resting:
            return  # 如果不在休息状态，不更新计时
            
        if self.rest_seconds > 0:
            self.rest_seconds -= 1
            self.update_time_display()
        else:
            # 休息结束
            self.timer.stop()
            self.is_resting = False
            self.resting_widget.setVisible(False)
            
            # 立即重置rest_dialog_active状态，确保状态栏图标可点击
            global rest_dialog_active
            rest_dialog_active = False
            
            # 播放休息结束音效
            if get_config().get("sound_effect_enabled", False):
                try:
                    from .music_player import get_music_player
                    from .constants import DEFAULT_SOUND_EFFECT_FILE
                    from PyQt6.QtCore import QTimer
                    sound_file = get_config().get("sound_effect_file", DEFAULT_SOUND_EFFECT_FILE)
                    # 确保音效只播放一次
                    print(f"休息倒计时结束，准备播放音效: {sound_file}")
                    # 使用延迟调用，确保UI更新和音频设备不冲突
                    QTimer.singleShot(200, lambda: self._play_rest_end_sound(sound_file))
                except Exception as e:
                    print(f"准备播放休息结束音效时出错: {e}")
                    import traceback
                    traceback.print_exc()
            
            # 停止音乐播放
            music_player = get_music_player()
            if music_player.is_playing:
                music_player.stop_playback()
                self.clear_song_info()
                        # 停止冥想音频播放
            try:
                meditation_player = get_meditation_audio_player()
                if meditation_player.is_playing:
                    # 断开所有信号连接
                    try:
                        meditation_player.playback_started.disconnect(self.update_meditation_audio_info)
                        meditation_player.playback_stopped.disconnect(self.clear_meditation_audio_info)
                        meditation_player.playback_error.disconnect(self.handle_meditation_audio_error)
                    except:
                        pass  # 如果未连接，忽略错误
                    
                    meditation_player.stop_playback()
            except:
                pass  # 如果获取播放器失败，忽略错误
                
            # 不再显示休息按钮
            self.rest_button.setVisible(False)
            
            # 记录休息结束
            if self.current_rest_id is not None:
                self.storage.end_rest(self.current_rest_id)
                self.current_rest_id = None
            
            # 更新信息标签的样式为较小字体
            self.info_label.setStyleSheet("""
                QLabel {
                    color: #34495e;
                    font-size: 12px;
                    margin: 8px 0;
                    font-family: "Microsoft YaHei", "SimHei", sans-serif;
                    line-height: 1.3;
                    background-color: transparent;
                }
            """)
            
            # 重置滚动区域和文本显示状态
            self.is_showing_full_text = False
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.scroll_area.setFixedHeight(self.info_label.sizeHint().height() + 5)
            
            # 尝试从数据库获取随机激励消息
            try:
                inspiration = self.storage.get_random_inspiration()
                if inspiration:
                    self.current_message_id = inspiration['id']
                    message_content = inspiration['content']
                    self.full_text = message_content
                    
                    # 如果消息超过100个字符，则截断并显示...
                    if len(message_content) > 100:
                        displayed_text = message_content[:100] + "..."
                    else:
                        displayed_text = message_content
                    
                    # 显示消息和添加/删除按钮
                    self.info_label.setText(displayed_text)
                    self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.add_message_button.setVisible(True)
                    self.remove_message_button.setVisible(True)
                else:
                    # 如果没有找到消息，显示默认消息
                    self.current_message_id = None
                    default_message = "以梦为马，不负韶华，休息结束，开始学习吧！"
                    self.info_label.setText(default_message)
                    self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.full_text = default_message
                    self.add_message_button.setVisible(True)
                    self.remove_message_button.setVisible(False)
            except Exception as e:
                from .constants import log
                log(f"获取激励消息出错: {str(e)}")
                self.current_message_id = None
                default_message = "以梦为马，不负韶华，休息结束，开始学习吧！"
                self.info_label.setText(default_message)
                self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.full_text = default_message
                self.add_message_button.setVisible(True)
                self.remove_message_button.setVisible(False)
                
            # 强调开始新番茄按钮
            self.new_pomodoro_button.setText("开始新番茄")
            self.new_pomodoro_button.setStyleSheet("""
                QPushButton {
                    background-color: #2ecc71;
                    color: white;
                    border: none;
                    border-radius: 15px;
                    padding: 5px 20px;
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
            
            # 修改按钮布局，使新番茄按钮居中
            btn_layout = self.new_pomodoro_button.parent().layout()
            btn_layout.setAlignment(self.new_pomodoro_button, Qt.AlignmentFlag.AlignCenter)
    
    def _play_rest_end_sound(self, sound_file):
        """实际播放休息结束音效的方法，通过延迟调用避免冲突"""
        try:
            from .music_player import get_music_player
            from .constants import DEFAULT_SOUND_EFFECT_FILE
            
            print(f"执行休息结束音效播放: {sound_file}")
            player = get_music_player()
            result = player.play_sound_effect(sound_file)
            
            if not result:
                print(f"播放休息结束音效失败: {sound_file}")
                # 尝试播放默认音效作为备选
                if sound_file != DEFAULT_SOUND_EFFECT_FILE:
                    print(f"尝试播放默认音效: {DEFAULT_SOUND_EFFECT_FILE}")
                    player.play_sound_effect(DEFAULT_SOUND_EFFECT_FILE)
        except Exception as e:
            print(f"播放休息结束音效时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def update_time_display(self):
        """更新时间显示"""
        mins, secs = divmod(self.rest_seconds, 60)
        self.time_label.setText(f"{mins:02d}:{secs:02d}")
    
    def start_new_pomodoro(self):
        """开始新的番茄钟或结束休息"""
        from .hooks import start_pomodoro_manually
        
        # 停止音乐播放
        music_player = get_music_player()
        if music_player.is_playing:
            music_player.stop_playback()
            self.clear_song_info()
        
        # 停止冥想音频播放
        try:
            meditation_player = get_meditation_audio_player()
            if meditation_player.is_playing:
                meditation_player.stop_playback()
        except:
            pass  # 如果获取播放器失败，忽略错误
        
        if self.is_resting:
            # 如果正在休息，结束休息
            self.toggle_rest()
            return
        
        # 如果正在休息，记录休息结束
        if self.current_rest_id is not None:
            self.storage.end_rest(self.current_rest_id)
            self.current_rest_id = None
        
        # 立即将rest_dialog_active设为False，确保状态栏图标可点击
        global rest_dialog_active
        rest_dialog_active = False
        
        self.accept()
        start_pomodoro_manually()
    
    def toggle_music(self):
        """切换音乐播放状态"""
        music_player = get_music_player()
        is_playing = music_player.toggle_playback()
        
        if is_playing:
            self.music_button.setText("🔈 停止音乐")
            # 连接信号处理歌曲信息
            try:
                music_player.playback_started.disconnect(self.update_song_info)
                music_player.playback_stopped.disconnect(self.clear_song_info)
                music_player.playback_error.disconnect(self.handle_music_error)
            except:
                pass  # 如果未连接，忽略错误
                
            music_player.playback_started.connect(self.update_song_info)
            music_player.playback_stopped.connect(self.clear_song_info)
            music_player.playback_error.connect(self.handle_music_error)
        else:
            self.music_button.setText("🎵 播放音乐")
            # 断开信号连接
            try:
                music_player.playback_started.disconnect(self.update_song_info)
                music_player.playback_stopped.disconnect(self.clear_song_info)
                music_player.playback_error.disconnect(self.handle_music_error)
            except:
                pass  # 如果未连接，忽略错误
            self.clear_song_info()
    
    def update_song_info(self, song_info):
        """更新当前播放的歌曲信息"""
        self.song_info_label.setText(f"正在播放: {song_info}")
        self.song_info_label.setVisible(True)
        # 确保播放按钮状态正确
        self.music_button.setText("🔈 停止音乐")
    
    def clear_song_info(self):
        """清除歌曲信息"""
        self.song_info_label.setText("")
        self.song_info_label.setVisible(False)
    
    def handle_music_error(self, error_message):
        """处理音乐播放错误"""
        # 显示更友好的错误信息
        if "所有API尝试失败" in error_message:
            self.song_info_label.setText("无法连接到音乐服务，请稍后再试")
        else:
            self.song_info_label.setText(f"音乐播放错误，正在尝试其他歌曲...")
        
        self.song_info_label.setVisible(True)
        # 不需要重置按钮文本，因为音乐播放器会自动尝试下一首
    
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        global rest_dialog_active
        self.timer.stop()
        
        # 停止音乐播放
        music_player = get_music_player()
        if music_player.is_playing:
            # 断开所有信号连接
            try:
                music_player.playback_started.disconnect(self.update_song_info)
                music_player.playback_stopped.disconnect(self.clear_song_info)
                music_player.playback_error.disconnect(self.handle_music_error)
            except:
                pass  # 如果未连接，忽略错误
                
            # 确保停止播放
            music_player.stop_playback()
        
        # 停止冥想音频播放
        try:
            meditation_player = get_meditation_audio_player()
            if meditation_player.is_playing:
                # 断开所有信号连接
                try:
                    meditation_player.playback_started.disconnect(self.update_meditation_audio_info)
                    meditation_player.playback_stopped.disconnect(self.clear_meditation_audio_info)
                    meditation_player.playback_error.disconnect(self.handle_meditation_audio_error)
                except:
                    pass  # 如果未连接，忽略错误
                    
                # 确保停止播放
                meditation_player.stop_playback()
        except:
            pass  # 如果获取播放器失败，忽略错误
        
        # 如果正在休息，记录休息结束
        if self.is_resting and self.current_rest_id is not None:
            self.storage.end_rest(self.current_rest_id)
            self.current_rest_id = None
        
        # 设置休息弹窗状态为非活跃状态
        rest_dialog_active = False
        
        # 添加淡出动画
        self.fade_out_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_animation.setDuration(300)
        self.fade_out_animation.setStartValue(1)
        self.fade_out_animation.setEndValue(0)
        self.fade_out_animation.finished.connect(self._on_close_finished)
        self.fade_out_animation.start()
        event.ignore()  # 忽略原始关闭事件
    
    def _on_close_finished(self):
        """淡出动画完成后的处理"""
        # 正确关闭对话框
        QTimer.singleShot(0, self.deleteLater)

    def show_meditation_menu(self):
        """显示冥想训练菜单"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #e0e5eb;
                border-radius: 5px;
                padding: 5px;
            }
            QMenu::item {
                background-color: transparent;
                padding: 5px 25px 5px 20px;
                border-radius: 3px;
                color: #34495e;
                font-size: 13px;
                font-family: "Microsoft YaHei", "SimHei", sans-serif;
            }
            QMenu::item:selected {
                background-color: #f0f7fc;
                color: #2980b9;
            }
            QMenu::separator {
                height: 1px;
                background-color: #e0e5eb;
                margin: 5px 10px;
            }
        """)
        
        # 添加冥想训练项
        if self.meditation_sessions:
            has_items = False
            for session in self.meditation_sessions:
                name = session.get("name", "未命名")
                url = session.get("url", "")
                audio_path = session.get("audio_path", "")
                
                if url or audio_path:
                    has_items = True
                    
                    # 使用用户设置的emoji图标，如果没有则使用默认图标
                    icon = session.get("emoji", "🧘")  # 从session中获取用户设置的emoji
                    
                    # 创建带有图标的菜单项
                    action = QAction(f"{icon} {name}", self)
                    
                    # 创建一个闭包来保存链接和音频路径
                    def create_callback(link, audio):
                        if audio and os.path.exists(audio):
                            # 优先使用音频文件
                            return lambda: self.open_meditation_link(audio)
                        elif link:
                            # 如果没有音频或音频不存在，使用链接
                            return lambda: self.open_meditation_link(link)
                        else:
                            return lambda: None
                    
                    action.triggered.connect(create_callback(url, audio_path))
                    menu.addAction(action)
            if not has_items:
                menu.addAction("无冥想训练项").setEnabled(False)
            
            # 添加分隔线
            menu.addSeparator()
            
            # 添加管理项
            manage_action = QAction("🔧 管理冥想训练列表...", self)
            manage_action.triggered.connect(self.manage_meditation_list)
            menu.addAction(manage_action)
            
            # 在按钮下方显示菜单
            menu.exec(self.meditation_button.mapToGlobal(self.meditation_button.rect().bottomLeft()))
    
    def open_meditation_link(self, url):
        """打开冥想训练链接或播放本地音频"""
        if not url:
            return
            
        from .music_player import get_meditation_audio_player
        
        # 获取冥想音频播放器
        meditation_player = get_meditation_audio_player()
        
        # 先断开所有之前的信号连接，避免多次连接导致问题
        try:
            meditation_player.playback_started.disconnect(self.update_meditation_audio_info)
            meditation_player.playback_stopped.disconnect(self.clear_meditation_audio_info)
            meditation_player.playback_error.disconnect(self.handle_meditation_audio_error)
        except:
            pass  # 如果未连接，忽略错误
        
        # 停止当前音乐播放（如果正在播放）确保停止播放后再进行下一步操作
        if meditation_player.is_playing:
            meditation_player.stop_playback()
            # 给播放器一个短暂的时间来完全停止
            QTimer.singleShot(100, lambda: self._continue_open_meditation_link(url, meditation_player))
        else:
            # 如果没有正在播放，直接继续
            self._continue_open_meditation_link(url, meditation_player)
    
    def _continue_open_meditation_link(self, url, meditation_player):
        """继续打开冥想训练链接或播放本地音频（在确保之前的播放已停止后）"""
        # 判断是网络链接还是本地文件
        if url.startswith(("http://", "https://", "www.")):
            # 网络链接使用浏览器打开
            QDesktopServices.openUrl(QUrl(url))
        else:
            # 本地文件路径，使用音频播放器播放
            if os.path.exists(url):
                # 连接信号
                meditation_player.playback_started.connect(self.update_meditation_audio_info)
                meditation_player.playback_stopped.connect(self.clear_meditation_audio_info)
                meditation_player.playback_error.connect(self.handle_meditation_audio_error)
                
                # 播放音频
                meditation_player.play_local_audio(url)
            else:
                # 文件不存在，显示错误
                self.show_message("错误", f"找不到音频文件: {url}", QMessageBox.Icon.Warning)

    def update_meditation_audio_info(self, audio_name):
        """更新冥想音频信息"""
        # 可以在这里添加UI元素来显示当前播放的冥想音频信息
        # 例如在状态栏或某个标签显示音频名称
        print(f"正在播放冥想音频: {audio_name}")

    def clear_meditation_audio_info(self):
        """清除冥想音频信息"""
        print("冥想音频播放已停止")

    def handle_meditation_audio_error(self, error_message):
        """处理冥想音频播放错误"""
        self.show_message("播放错误", error_message, QMessageBox.Icon.Warning)

    def show_message(self, title, message, icon=QMessageBox.Icon.Information):
        """显示一个无边框的消息对话框"""
        # 选择合适的图标文本
        icon_text = "ℹ️"  # 默认信息图标
        if icon == QMessageBox.Icon.Warning:
            icon_text = "⚠️"
        elif icon == QMessageBox.Icon.Critical:
            icon_text = "❌"
        elif icon == QMessageBox.Icon.Question:
            icon_text = "❓"
            
        # 创建并显示无边框对话框
        dialog = ConfirmDialog(
            self, 
            title=title,
            message=message,
            icon_text=icon_text
        )
        
        # 修改确认对话框中的按钮文本从"是/否"变为"确定"
        yes_button = dialog.findChild(QPushButton, "yes_button")
        if yes_button:
            yes_button.setText("确定")
        
        no_button = dialog.findChild(QPushButton, "no_button")
        if no_button:
            no_button.setVisible(False)
            
        dialog.exec()
    
    def manage_meditation_list(self):
        """管理冥想训练列表"""
        dialog = MeditationListDialog(self)
        if dialog.exec():
            # 重新加载冥想训练列表
            self.meditation_sessions = get_config().get("meditation_sessions", [])

    def add_user_message(self):
        """添加用户消息的对话框"""
        # 创建无边框对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("分享给未来的自己")
        dialog.setMinimumWidth(400)
        dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 主布局
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建容器并设置背景和圆角
        container = QWidget()
        container.setObjectName("messageContainer")
        container.setStyleSheet("""
            QWidget#messageContainer {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e5eb;
            }
        """)
        
        # 容器布局
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(15)
        
        # 标题和图标
        title_layout = QHBoxLayout()
        title_icon = QLabel("💭")
        title_icon.setStyleSheet("font-size: 22px;")
        
        title_label = QLabel("分享当下的快乐给未来的自己")
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #34495e;
            font-family: "Microsoft YaHei", "SimHei", sans-serif;
        """)
        
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 关闭按钮
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
        close_button.clicked.connect(dialog.reject)
        title_layout.addWidget(close_button)
        
        container_layout.addLayout(title_layout)
        
        # 分隔线
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #e0e5eb;")
        container_layout.addWidget(separator)
        
        # 添加说明文字
        description = QLabel("写下你想对未来的自己说的话，休息时会随机显示给你看！")
        description.setWordWrap(True)
        description.setStyleSheet("""
            color: #7f8c8d;
            font-size: 13px;
            font-family: "Microsoft YaHei", "SimHei", sans-serif;
        """)
        container_layout.addWidget(description)
        
        # 导入emoji图标
        from .constants import AVAILABLE_STATUSBAR_ICONS
        
        # 创建emoji选择器区域
        emoji_label = QLabel("选择表情：")
        emoji_label.setStyleSheet("""
            color: #34495e;
            font-size: 13px;
            font-weight: bold;
            font-family: "Microsoft YaHei", "SimHei", sans-serif;
        """)
        container_layout.addWidget(emoji_label)
        
        # Emoji滚动区域
        emoji_scroll = QScrollArea()
        emoji_scroll.setWidgetResizable(True)
        emoji_scroll.setFrameShape(QFrame.Shape.NoFrame)
        emoji_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        emoji_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        emoji_scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 3px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
        """)
        
        # Emoji容器
        emoji_container = QWidget()
        emoji_layout = QGridLayout(emoji_container)
        emoji_layout.setContentsMargins(5, 5, 5, 5)
        emoji_layout.setSpacing(5)
        
        # 文本输入框 - 将在之后引用
        message_input = QTextEdit()
        
        # 添加emoji按钮
        row, col = 0, 0
        max_cols = 8  # 每行最多显示的emoji数量
        
        for emoji in AVAILABLE_STATUSBAR_ICONS:
            emoji_btn = QPushButton(emoji)
            emoji_btn.setFixedSize(30, 30)
            emoji_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            emoji_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f5f5f5;
                    border: none;
                    border-radius: 5px;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
                QPushButton:pressed {
                    background-color: #d0d0d0;
                }
            """)
            
            # 点击时将emoji添加到文本框
            emoji_btn.clicked.connect(lambda checked=False, e=emoji: message_input.insertPlainText(e))
            
            emoji_layout.addWidget(emoji_btn, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        emoji_scroll.setWidget(emoji_container)
        emoji_scroll.setFixedHeight(150)  # 设置emoji区域的固定高度
        container_layout.addWidget(emoji_scroll)
        
        # 文本输入框
        message_input.setPlaceholderText("我们的人生总共才几万天，何必记录那些让今天的自己不开心的事呢，让所有的不开心都离我们远去吧！\n今天的我只记录让自己开心的事，让未来的我也能感受到今天的我的快乐和喜悦。\n让今天的我抚慰明天的我，让今天的我为明天的我呐喊加油！\n实在不开心，那今天就不写了，好好睡一觉，没有什么事是睡一觉不能解决的，不想睡？那就出去跑一圈，让所有的不快都随风消散吧！")
        message_input.setMinimumHeight(100)
        message_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 8px;
                background-color: #f9f9f9;
                color: #34495e;
                font-size: 14px;
                font-family: "Microsoft YaHei", "SimHei", sans-serif;
            }
            QTextEdit:focus {
                border-color: #3498db;
                background-color: #ffffff;
            }
        """)
        container_layout.addWidget(message_input)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        cancel_button = QPushButton("取消")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #ecf0f1;
                color: #7f8c8d;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 14px;
                font-family: "Microsoft YaHei", "SimHei", sans-serif;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                color: #636e72;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        cancel_button.clicked.connect(dialog.reject)
        
        save_button = QPushButton("保存")
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
                font-family: "Microsoft YaHei", "SimHei", sans-serif;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1f6da8;
            }
        """)
        save_button.clicked.connect(lambda: self._save_message(message_input.toPlainText(), dialog))
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        
        container_layout.addLayout(button_layout)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect(dialog)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        container.setGraphicsEffect(shadow)
        
        main_layout.addWidget(container)
        
        # 添加拖动功能
        dialog.old_pos = None
        
        def mousePressEvent(event):
            if event.button() == Qt.MouseButton.LeftButton:
                dialog.old_pos = event.globalPosition().toPoint()
        
        def mouseMoveEvent(event):
            if dialog.old_pos is not None:
                delta = QPoint(event.globalPosition().toPoint() - dialog.old_pos)
                dialog.move(dialog.pos() + delta)
                dialog.old_pos = event.globalPosition().toPoint()
        
        def mouseReleaseEvent(event):
            if event.button() == Qt.MouseButton.LeftButton:
                dialog.old_pos = None
        
        dialog.mousePressEvent = mousePressEvent
        dialog.mouseMoveEvent = mouseMoveEvent
        dialog.mouseReleaseEvent = mouseReleaseEvent
        
        # 显示对话框并居中
        dialog.adjustSize()
        dialog.move(
            self.mapToGlobal(QPoint(
                (self.width() - dialog.width()) // 2,
                (self.height() - dialog.height()) // 2
            ))
        )
        
        dialog.exec()
    
    def _save_message(self, message, dialog):
        """保存用户消息到数据库"""
        if not message.strip():
            return
        
        try:
            # 添加日期前缀
            today = datetime.datetime.now()
            date_prefix = f"{today.year}.{today.month}.{today.day}的自己写道：\n"
            formatted_message = date_prefix + message.strip()
            
            # 保存消息到数据库
            message_id = self.storage.add_user_message(formatted_message)
            
            # 更新当前显示的消息
            self.current_message_id = message_id
            self.full_text = formatted_message
            
            # 如果消息超过100个字符，则截断显示
            if len(formatted_message) > 100:
                displayed_text = formatted_message[:100] + "..."
            else:
                displayed_text = formatted_message
                
            self.info_label.setText(displayed_text)
            self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # 确保保持小字体样式
            self.info_label.setStyleSheet("""
                QLabel {
                    color: #34495e;
                    font-size: 12px;
                    margin: 8px 0;
                    font-family: "Microsoft YaHei", "SimHei", sans-serif;
                    line-height: 1.3;
                    background-color: transparent;
                }
            """)
            
            # 重置全文显示状态
            self.is_showing_full_text = False
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            
            self.remove_message_button.setVisible(True)
            
            # 关闭对话框
            dialog.accept()
        except Exception as e:
            QMessageBox.warning(self, "保存失败", f"保存消息时出错：{str(e)}")
    
    def remove_current_message(self):
        """删除当前显示的消息"""
        if self.current_message_id is None:
            return
        
        # 使用自定义无边框确认对话框
        confirm_dialog = ConfirmDialog(
            self,
            title="删除确认",
            message="确定要删除吗，删除了就再也没有了！",
            icon_text="⚠️"
        )
        
        # 显示对话框并获取结果
        result = confirm_dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            try:
                # 保存当前位置
                current_pos = self.pos()
                
                # 首先保存当前消息ID，因为之后可能会被重置
                message_id_to_delete = self.current_message_id
                
                # 如果当前正在展开状态，先收起来
                if self.is_showing_full_text:
                    self.is_showing_full_text = False
                    
                    # 恢复显示为只有前100个字符
                    if self.full_text and len(self.full_text) > 100:
                        self.info_label.setText(self.full_text[:100] + "...")
                    
                    # 恢复居中对齐
                    self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    # 隐藏滚动条
                    self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                    
                    # 恢复原始高度
                    if self.original_height:
                        self.setFixedHeight(self.original_height)
                        # 重置滚动区域高度
                        self.scroll_area.setFixedHeight(self.info_label.sizeHint().height() + 5)
                
                # 从数据库删除消息
                success = self.storage.remove_message(message_id_to_delete)
                
                if success:
                    # 尝试获取新的随机消息
                    inspiration = self.storage.get_random_inspiration()
                    if inspiration:
                        self.current_message_id = inspiration['id']
                        message_content = inspiration['content']
                        self.full_text = message_content
                        
                        # 如果消息超过100个字符，则截断显示
                        if len(message_content) > 100:
                            displayed_text = message_content[:100] + "..."
                        else:
                            displayed_text = message_content
                        
                        self.info_label.setText(displayed_text)
                        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        
                        # 确保保持小字体样式
                        self.info_label.setStyleSheet("""
                            QLabel {
                                color: #34495e;
                                font-size: 12px;
                                margin: 8px 0;
                                font-family: "Microsoft YaHei", "SimHei", sans-serif;
                                line-height: 1.3;
                                background-color: transparent;
                            }
                        """)
                        
                        self.remove_message_button.setVisible(True)
                    else:
                        # 如果没有其他消息，显示默认消息
                        self.current_message_id = None
                        default_message = "以梦为马，不负韶华，休息结束，开始学习吧！"
                        self.info_label.setText(default_message)
                        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.full_text = default_message
                        
                        # 确保保持小字体样式
                        self.info_label.setStyleSheet("""
                            QLabel {
                                color: #34495e;
                                font-size: 12px;
                                margin: 8px 0;
                                font-family: "Microsoft YaHei", "SimHei", sans-serif;
                                line-height: 1.3;
                                background-color: transparent;
                            }
                        """)
                        
                        self.remove_message_button.setVisible(False)
                    
                    # 确保对话框大小正确，设置为原始高度
                    if self.original_height:
                        self.setFixedHeight(self.original_height)
                        self.scroll_area.setFixedHeight(self.info_label.sizeHint().height() + 5)
                    
                    # 重置全文显示状态
                    self.is_showing_full_text = False
                    
                    # 保持位置不变
                    self.move(current_pos)
                else:
                    self.show_message("删除失败", "无法删除消息，请稍后再试。", QMessageBox.Icon.Warning)
            except Exception as e:
                self.show_message("删除失败", f"删除消息时出错：{str(e)}", QMessageBox.Icon.Warning)

    def on_info_label_clicked(self, event):
        """处理信息标签的点击事件，展开或收起完整文本"""
        if not self.full_text or len(self.full_text) <= 100:
            return  # 如果没有全文或文本不需要截断，不做任何操作
            
        # 保存当前位置
        current_pos = self.pos()
        current_height = self.height()
            
        # 切换全文/截断文本显示状态
        self.is_showing_full_text = not self.is_showing_full_text
        
        if self.is_showing_full_text:
            # 保存原始高度
            if self.original_height is None:
                self.original_height = self.height()
                
            # 显示全文
            self.info_label.setText(self.full_text)
            self.info_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            
            # 设置滚动区域的固定高度
            self.scroll_area.setFixedHeight(240)  # 减小滚动区域高度
            
            # 显示滚动条
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            
            # 增加对话框高度 - 减小4cm
            expanded_height = self.original_height + 290  # 比之前减少160px (约4cm)
            
            # 计算新的位置，保持顶部位置不变
            new_y = current_pos.y()
            
            # 调整大小
            self.setFixedHeight(expanded_height)
            
            # 将对话框移动到新位置（保持左上角不变）
            self.move(current_pos.x(), new_y)
            
            # 确保滚动区域不会被遮挡或超出对话框
            QTimer.singleShot(50, self._ensure_visible_content)
            
            # 延迟滚动到顶部，确保文本正确加载
            QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(0))
        else:
            # 显示截断文本
            truncated = self.full_text[:100] + "..."
            self.info_label.setText(truncated)
            self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # 隐藏滚动条
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            
            # 恢复原始高度
            if self.original_height:
                # 计算新的Y位置（保持顶部位置不变）
                new_y = current_pos.y()
                
                # 设置高度并移动
                self.setFixedHeight(self.original_height)
                self.move(current_pos.x(), new_y)
                
                # 重置滚动区域高度
                self.scroll_area.setFixedHeight(self.info_label.sizeHint().height() + 5)
        
        # 确保始终应用正确的样式
        self.info_label.setStyleSheet("""
            QLabel {
                color: #34495e;
                font-size: 12px;
                margin: 8px 0;
                font-family: "Microsoft YaHei", "SimHei", sans-serif;
                line-height: 1.3;
                background-color: transparent;
            }
        """)

    def _ensure_visible_content(self):
        """确保所有内容都可见，防止底部控件被遮挡"""
        # 获取主容器和底部按钮的位置和大小
        container = self.findChild(QWidget, "container")
        if container:
            # 保存当前位置
            current_pos = self.pos()
            
            # 计算内容所需的高度
            required_height = container.sizeHint().height() + 40  # 添加一些额外空间
            
            # 如果当前高度不足，进一步增加高度
            if self.height() < required_height:
                self.setFixedHeight(required_height)
                # 保持位置不变
                self.move(current_pos)

def show_rest_dialog():
    """显示休息对话框"""
    global rest_dialog_active
    dialog = RestDialog(mw)
    dialog.show()  # 使用show()方法替代exec()，使对话框非模态
    rest_dialog_active = True  # 设置休息弹窗活跃状态为True
    
    return dialog  # 返回对话框实例而不是执行结果

class MeditationItemDelegate(QStyledItemDelegate):
    """冥想训练项的自定义绘制代理"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hover_animation = {}  # 存储每个项目的悬停动画状态
    
    def paint(self, painter, option, index):
        """自定义绘制列表项"""
        # 获取图标和文本
        icon_text = index.data(Qt.ItemDataRole.UserRole + 1) or "🧘"
        text = index.data(Qt.ItemDataRole.DisplayRole)
        if text.startswith("  "):  # 去掉预留的图标空间
            text = text[2:]
        
        # 判断鼠标是否悬停在项目上
        is_hover = option.state & QStyle.StateFlag.State_MouseOver
        is_selected = option.state & QStyle.StateFlag.State_Selected
        
        # 判断项目是否正在被拖拽
        is_dragging = index.data(Qt.ItemDataRole.UserRole + 2)
        
        # 保存原始画笔透明度
        painter.save()
        
        # 如果是拖拽中的项，设置半透明效果
        if is_dragging:
            painter.setOpacity(0.5)
            
        # 绘制背景
        if is_selected:
            painter.fillRect(option.rect, QColor("#e1f0fa"))
        elif is_hover:
            painter.fillRect(option.rect, QColor("#f0f7fc"))
        else:
            painter.fillRect(option.rect, QColor("#f9fafc"))
        
        # 设置字体和颜色
        font = painter.font()
        font.setFamily("Microsoft YaHei")
        
        if is_selected:
            font.setBold(True)
            painter.setPen(QColor("#2980b9"))
        elif is_hover:
            painter.setPen(QColor("#3498db"))
        else:
            painter.setPen(QColor("#445566"))
        
        painter.setFont(font)
        
        # 绘制左侧图标
        icon_rect = option.rect.adjusted(10, 0, 0, 0)
        icon_rect.setWidth(30)
        
        # 设置图标字体和大小
        icon_font = QFont(painter.font())
        icon_font.setPointSize(14)
        painter.setFont(icon_font)
        
        # 绘制图标
        painter.drawText(icon_rect, Qt.AlignmentFlag.AlignVCenter, icon_text)
        
        # 恢复原字体
        painter.setFont(font)
        
        # 绘制文本
        text_rect = option.rect.adjusted(45, 0, -10, 0)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter, text)
        
        # 恢复原始画笔设置
        painter.restore()
    
    def sizeHint(self, option, index):
        """返回项目的推荐大小"""
        size = super().sizeHint(option, index)
        size.setHeight(48)  # 设置更高的高度，使项目更加突出
        return size

class DragDropListWidget(QListWidget):
    """支持拖拽项半透明效果的列表控件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.drag_item = None
    
    def startDrag(self, supportedActions):
        """开始拖拽操作时被调用"""
        # 保存当前被拖拽的项
        self.drag_item = self.currentItem()
        
        # 设置被拖拽项为半透明
        if self.drag_item:
            self.drag_item.setData(Qt.ItemDataRole.UserRole + 2, True)  # 标记为正在拖拽
            
        # 调用父类方法以执行实际的拖拽
        super().startDrag(supportedActions)
        
        # 拖拽结束后恢复透明度
        if self.drag_item:
            self.drag_item.setData(Qt.ItemDataRole.UserRole + 2, False)  # 取消拖拽标记
            self.drag_item = None
            self.update()  # 强制刷新视图