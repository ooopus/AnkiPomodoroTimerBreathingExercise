from aqt import mw
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QSpinBox,
    QDialogButtonBox,
    QGroupBox,
    QComboBox,
    QGridLayout,
    QFrame,
    QPushButton,
    QGraphicsDropShadowEffect,
    QWidget,
    QScrollArea,
    QSizePolicy,
    QToolButton,
)
from PyQt6.QtCore import Qt, QPoint, QSize
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon, QCursor
from ..constants import (
    DEFAULT_POMODORO_MINUTES, 
    DEFAULT_REST_MINUTES, 
    AVAILABLE_STATUSBAR_ICONS, 
    STATUSBAR_ICON
)
from ..config import save_config, get_config, get_pomodoro_timer
from .statusbar import show_timer_in_statusbar, get_status_widget


class ConfigDialog(QDialog):
    """Configuration dialog for Pomodoro settings."""

    def __init__(self, parent=None):
        super().__init__(parent or mw, Qt.WindowType.FramelessWindowHint)
        
        # 设置窗口属性，使背景透明
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 用于跟踪鼠标拖动窗口
        self.oldPos = None

        # Use our config system instead of Anki's
        self.config = get_config()

        # 设置窗口属性
        self.setWindowTitle("设置")
        self.setMinimumWidth(400)
        
        # 创建一个内容容器，这个容器将有背景色和圆角
        self.container = QWidget(self)
        self.container.setObjectName("container")
        self.container.setStyleSheet("""
            #container {
                background-color: #ffffff;
                border-radius: 8px;
                border: none;
            }
        """)
        
        # 添加阴影效果到容器
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 1)
        self.container.setGraphicsEffect(shadow)
        
        # 容器的布局
        container_layout = QVBoxLayout(self.container)
        container_layout.setSpacing(9)
        container_layout.setContentsMargins(13, 13, 13, 13)
        
        # 窗口的主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(9, 9, 9, 9)
        main_layout.addWidget(self.container)
        
        # 标题栏和关闭按钮
        title_bar = QHBoxLayout()
        title_label = QLabel("设置")
        title_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #697a84;
        """)
        
        close_button = QPushButton("×")
        close_button.setFixedSize(20, 20)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #7a8c97;
                font-size: 14px;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #e1b2a9;
                color: white;
            }
            QPushButton:pressed {
                background-color: #d1a298;
            }
        """)
        close_button.clicked.connect(self.close)
        
        title_bar.addWidget(title_label)
        title_bar.addStretch()
        title_bar.addWidget(close_button)
        
        container_layout.addLayout(title_bar)
        
        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #e0e0d9;")
        container_layout.addWidget(separator)

        # --- General Settings ---
        general_group = QGroupBox("常规设置")
        general_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: none;
                border-radius: 5px;
                margin-top: 9px;
                padding-top: 9px;
                font-size: 13px;
                color: #697a84;
                background-color: #f5f5f5;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 9px;
                padding: 0 4px;
                color: #697a84;
                background-color: #ffffff;
            }
        """)
        general_layout = QVBoxLayout()
        general_layout.setSpacing(6)

        # 创建更美观的复选框样式
        checkbox_style = """
            QCheckBox {
                spacing: 6px;
                color: #697a84;
                font-size: 11px;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
                border-radius: 4px;
                border: 1px solid #c0c0b8;
            }
            QCheckBox::indicator:checked {
                background-color: #a9bec9;
                border: 1px solid #95aab5;
            }
            QCheckBox::indicator:hover {
                border: 1px solid #95aab5;
            }
        """

        # 显示选项布局
        display_layout = QVBoxLayout()
        display_layout.setSpacing(6)
        
        # 样式表定义
        label_style = """
            QLabel {
                color: #697a84;
                font-size: 11px;
            }
        """
        
        spinbox_style = """
            QSpinBox {
                padding: 4px;
                border: 1px solid #c0c0b8;
                border-radius: 4px;
                background-color: #fcfcf9;
                min-width: 59px;
                font-size: 11px;
                color: #697a84;
            }
            QSpinBox:hover {
                border: 1px solid #95aab5;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 14px;
                border-radius: 1px;
                background-color: #f0f0e8;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #e5e5dd;
            }
        """
        
        self.show_timer_checkbox = QCheckBox("在状态栏显示计时器", self)
        self.show_timer_checkbox.setChecked(self.config.get("show_statusbar_timer", True))
        self.show_timer_checkbox.setStyleSheet(checkbox_style)
        self.show_timer_checkbox.toggled.connect(self.on_show_timer_toggled)
        display_layout.addWidget(self.show_timer_checkbox)
        
        self.show_countdown_info_checkbox = QCheckBox("在状态栏显示倒计时和连续专注天数", self)
        self.show_countdown_info_checkbox.setChecked(self.config.get("show_countdown_info", True))
        self.show_countdown_info_checkbox.setStyleSheet(checkbox_style)
        self.show_countdown_info_checkbox.toggled.connect(self.on_show_countdown_info_toggled)
        display_layout.addWidget(self.show_countdown_info_checkbox)
        
        self.smart_timer_reminder_checkbox = QCheckBox("智能提醒开始番茄计时", self)
        self.smart_timer_reminder_checkbox.setChecked(self.config.get("smart_timer_reminder", False))
        self.smart_timer_reminder_checkbox.setStyleSheet(checkbox_style)
        self.smart_timer_reminder_checkbox.toggled.connect(self.on_smart_timer_reminder_toggled)
        display_layout.addWidget(self.smart_timer_reminder_checkbox)
        
        # 添加智能提醒时间阈值选择器
        reminder_time_layout = QHBoxLayout()
        reminder_time_layout.setContentsMargins(22, 0, 0, 0)  # 左侧缩进，与复选框对齐
        
        reminder_time_label = QLabel("在卡片复习界面停留超过", self)
        reminder_time_label.setStyleSheet(label_style)
        reminder_time_layout.addWidget(reminder_time_label)
        
        self.reminder_time_spinbox = QSpinBox(self)
        self.reminder_time_spinbox.setMinimum(1)
        self.reminder_time_spinbox.setMaximum(60)
        self.reminder_time_spinbox.setValue(self.config.get("smart_timer_reminder_minutes", 15))
        self.reminder_time_spinbox.setStyleSheet(spinbox_style)
        self.reminder_time_spinbox.valueChanged.connect(self.on_reminder_time_changed)
        reminder_time_layout.addWidget(self.reminder_time_spinbox)
        
        reminder_unit_label = QLabel("分钟而未开启番茄计时时提醒", self)
        reminder_unit_label.setStyleSheet(label_style)
        reminder_time_layout.addWidget(reminder_unit_label)
        
        reminder_time_layout.addStretch()
        display_layout.addLayout(reminder_time_layout)
        
        # 设置初始启用状态
        is_reminder_enabled = self.config.get("smart_timer_reminder", False)
        self.reminder_time_spinbox.setEnabled(is_reminder_enabled)
        reminder_time_label.setEnabled(is_reminder_enabled)
        reminder_unit_label.setEnabled(is_reminder_enabled)
        
        # 保存布局引用，供后续使用
        self.reminder_time_layout = reminder_time_layout

        general_layout.addLayout(display_layout)
        general_group.setLayout(general_layout)
        container_layout.addWidget(general_group)

        # --- 番茄钟配置组 ---
        pomodoro_group = QGroupBox("番茄钟时长设置")
        pomodoro_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: none;
                border-radius: 5px;
                margin-top: 9px;
                padding-top: 9px;
                font-size: 13px;
                color: #697a84;
                background-color: #f5f5f5;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 9px;
                padding: 0 4px;
                color: #697a84;
                background-color: #ffffff;
            }
        """)

        # 使用网格布局更紧凑地排列控件
        pomodoro_layout = QGridLayout()
        pomodoro_layout.setVerticalSpacing(10)
        pomodoro_layout.setHorizontalSpacing(9)
        
        # 表头
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(11)
        
        config_label = QLabel("配置组", self)
        config_label.setFont(header_font)
        config_label.setStyleSheet(label_style)
        config_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        pomo_header = QLabel("番茄钟时长", self)
        pomo_header.setFont(header_font)
        pomo_header.setStyleSheet(label_style)
        pomo_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        rest_header = QLabel("休息时长", self)
        rest_header.setFont(header_font)
        rest_header.setStyleSheet(label_style)
        rest_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        pomodoro_layout.addWidget(config_label, 0, 0)
        pomodoro_layout.addWidget(pomo_header, 0, 1)
        pomodoro_layout.addWidget(rest_header, 0, 2)
        
        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #e0e0d9;")
        pomodoro_layout.addWidget(separator, 1, 0, 1, 3)

        # 获取当前激活的组（默认第一组）
        active_group = self.config.get("active_timer_group", 0)

        # 创建三组设置控件
        self.timer_checkboxes = []
        self.pomo_spinboxes = []
        self.rest_spinboxes = []
        
        # 创建配置组
        for i in range(3):
            row = i + 2  # 从第二行开始（表头和分隔线占用了前两行）
            
            # 配置复选框
            checkbox = QCheckBox(f"配置 {i+1}", self)
            checkbox.setChecked(active_group == i)
            checkbox.setStyleSheet(checkbox_style)
            self.timer_checkboxes.append(checkbox)
            pomodoro_layout.addWidget(checkbox, row, 0, Qt.AlignmentFlag.AlignCenter)
        
            # 番茄钟时长部分
            pomo_layout = QHBoxLayout()
            pomo_spinbox = QSpinBox(self)
            pomo_spinbox.setMinimum(1)
            pomo_spinbox.setMaximum(180)
            pomo_spinbox.setStyleSheet(spinbox_style)
            
            # 设置不同配置组的默认值
            if i == 0:
                pomo_spinbox.setValue(self.config.get("pomodoro_minutes", DEFAULT_POMODORO_MINUTES))
            elif i == 1:
                pomo_spinbox.setValue(self.config.get("pomodoro_minutes_2", 25))
            else:
                pomo_spinbox.setValue(self.config.get("pomodoro_minutes_3", 50))
                
            self.pomo_spinboxes.append(pomo_spinbox)
            
            # 实时更新
            pomo_spinbox.valueChanged.connect(lambda value, idx=i: self.on_pomo_time_changed(idx, value))
            
            pomo_label_unit = QLabel("分钟", self)
            pomo_label_unit.setStyleSheet(label_style)
            
            pomo_layout.addWidget(pomo_spinbox)
            pomo_layout.addWidget(pomo_label_unit)
            pomo_layout.setContentsMargins(9, 0, 9, 0)
            pomodoro_layout.addLayout(pomo_layout, row, 1, Qt.AlignmentFlag.AlignCenter)
        
            # 休息时长部分
            rest_layout = QHBoxLayout()
            rest_spinbox = QSpinBox(self)
            rest_spinbox.setMinimum(1)
            rest_spinbox.setMaximum(60)
            rest_spinbox.setStyleSheet(spinbox_style)
            
            # 设置不同配置组的默认值
            if i == 0:
                rest_spinbox.setValue(self.config.get("rest_minutes", DEFAULT_REST_MINUTES))
            elif i == 1:
                rest_spinbox.setValue(self.config.get("rest_minutes_2", 5))
            else:
                rest_spinbox.setValue(self.config.get("rest_minutes_3", 10))
                
            self.rest_spinboxes.append(rest_spinbox)
            
            # 实时更新
            rest_spinbox.valueChanged.connect(lambda value, idx=i: self.on_rest_time_changed(idx, value))
            
            rest_label_unit = QLabel("分钟", self)
            rest_label_unit.setStyleSheet(label_style)
            
            rest_layout.addWidget(rest_spinbox)
            rest_layout.addWidget(rest_label_unit)
            rest_layout.setContentsMargins(9, 0, 9, 0)
            pomodoro_layout.addLayout(rest_layout, row, 2, Qt.AlignmentFlag.AlignCenter)

        # 设置单选逻辑
        for i, checkbox in enumerate(self.timer_checkboxes):
            checkbox.toggled.connect(lambda checked, idx=i: self.on_timer_group_toggled(idx, checked))

        pomodoro_group.setLayout(pomodoro_layout)
        container_layout.addWidget(pomodoro_group)
        
        # --- 状态栏图标设置 ---
        icon_group = QGroupBox("状态栏图标设置")
        icon_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: none;
                border-radius: 5px;
                margin-top: 9px;
                padding-top: 9px;
                font-size: 13px;
                color: #697a84;
                background-color: #f5f5f5;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 9px;
                padding: 0 4px;
                color: #697a84;
                background-color: #ffffff;
            }
        """)
        
        icon_layout = QHBoxLayout()
        
        # 当前图标显示
        current_icon_label = QLabel("当前图标：", self)
        current_icon_label.setStyleSheet(label_style)
        
        # 获取当前图标
        config = get_config()
        current_icon = config.get("statusbar_icon", STATUSBAR_ICON)
        
        self.icon_display = QLabel(current_icon, self)
        self.icon_display.setStyleSheet("""
            QLabel {
                font-size: 16px;
                padding: 4px;
                background-color: #fcfcf9;
                border: 1px solid #c0c0b8;
                border-radius: 4px;
                min-width: 30px;
                min-height: 30px;
                text-align: center;
                cursor: pointer;
            }
            QLabel:hover {
                background-color: #e5e5dd;
                border: 1px solid #95aab5;
            }
        """)
        self.icon_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_display.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.icon_display.setToolTip("点击选择图标")
        
        # 连接鼠标点击事件
        self.icon_display.mousePressEvent = self.on_icon_clicked
        
        icon_layout.addWidget(current_icon_label)
        icon_layout.addWidget(self.icon_display)
        icon_layout.addStretch()
        
        icon_group.setLayout(icon_layout)
        container_layout.addWidget(icon_group)

        # 添加空白区域作为填充
        container_layout.addStretch()
        
        # 去掉对话框的样式表，因为现在我们使用容器的样式
        self.setStyleSheet("")

    def mousePressEvent(self, event):
        """记录鼠标按下的位置，用于窗口拖动"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.oldPos = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """实现窗口拖动"""
        if self.oldPos and event.buttons() == Qt.MouseButton.LeftButton:
            delta = QPoint(event.globalPosition().toPoint() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """清除鼠标位置记录"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.oldPos = None
        super().mouseReleaseEvent(event)

    def on_show_timer_toggled(self, checked):
        """实时更新显示计时器设置"""
        self.config["show_statusbar_timer"] = checked
        save_config()

        # 更新UI显示
        show_timer = self.config.get("enabled", True) and checked
        show_timer_in_statusbar(show_timer)
        
        # 刷新状态栏信息
        status_widget = get_status_widget()
        if status_widget:
            status_widget.update_display()
    
    def on_show_countdown_info_toggled(self, checked):
        """实时更新显示倒计时和连续专注天数设置"""
        self.config["show_countdown_info"] = checked
        save_config()
        
        # 刷新状态栏信息
        status_widget = get_status_widget()
        if status_widget:
            status_widget.update_display()
            
    def on_smart_timer_reminder_toggled(self, checked):
        """实时更新智能提醒开始番茄计时设置"""
        self.config["smart_timer_reminder"] = checked
        save_config()
        
        # 根据复选框状态启用或禁用时间选择器
        self.reminder_time_spinbox.setEnabled(checked)
        # 若有标签，也相应地启用或禁用它们
        for i in range(self.reminder_time_layout.count()):
            widget = self.reminder_time_layout.itemAt(i).widget()
            if widget and isinstance(widget, QLabel):
                widget.setEnabled(checked)
            
    def on_timer_group_toggled(self, index, checked):
        """处理配置组选择变更"""
        if checked:
            # 确保其他复选框取消选中
            for i, checkbox in enumerate(self.timer_checkboxes):
                if i != index and checkbox.isChecked():
                    checkbox.setChecked(False)
            
            # 更新配置
            self.config["active_timer_group"] = index
            save_config()
            
            # 更新计时器显示
            timer = get_pomodoro_timer()
            if timer and not timer.isActive():
                status_widget = get_status_widget()
                if status_widget and hasattr(status_widget, 'timer_label'):
                    status_widget.timer_label.updateTimerDisplay(timer)
        else:
            # 防止所有复选框都取消选中
            if not any(checkbox.isChecked() for checkbox in self.timer_checkboxes):
                self.timer_checkboxes[index].setChecked(True)
    
    def on_pomo_time_changed(self, index, value):
        """处理番茄钟时长变更"""
        if index == 0:
            self.config["pomodoro_minutes"] = value
        elif index == 1:
            self.config["pomodoro_minutes_2"] = value
        else:
            self.config["pomodoro_minutes_3"] = value
        
        save_config()
        
        # 如果修改的是当前活动的配置，且计时器未运行，则更新显示
        if self.config.get("active_timer_group", 0) == index:
            timer = get_pomodoro_timer()
            if timer and not timer.isActive():
                status_widget = get_status_widget()
                if status_widget and hasattr(status_widget, 'timer_label'):
                    status_widget.timer_label.updateTimerDisplay(timer)

    def on_rest_time_changed(self, index, value):
        """处理休息时长变更"""
        if index == 0:
            self.config["rest_minutes"] = value
        elif index == 1:
            self.config["rest_minutes_2"] = value
        else:
            self.config["rest_minutes_3"] = value
        
        save_config()

    def show_emoji_selector(self):
        """显示Emoji选择器对话框"""
        # 直接使用自定义对话框类
        class EmojiDialog(QDialog):
            def __init__(self, parent=None):
                super().__init__(parent, Qt.WindowType.FramelessWindowHint)
                self.oldPos = None
                
                # 设置窗口属性，使背景透明
                self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
                self.setWindowTitle("选择图标")
                self.setMinimumWidth(300)
                self.setMinimumHeight(400)
                
            def mousePressEvent(self, event):
                if event.button() == Qt.MouseButton.LeftButton:
                    self.oldPos = event.globalPosition().toPoint()
                super().mousePressEvent(event)
                
            def mouseMoveEvent(self, event):
                if self.oldPos and event.buttons() == Qt.MouseButton.LeftButton:
                    delta = QPoint(event.globalPosition().toPoint() - self.oldPos)
                    self.move(self.x() + delta.x(), self.y() + delta.y())
                    self.oldPos = event.globalPosition().toPoint()
                super().mouseMoveEvent(event)
                
            def mouseReleaseEvent(self, event):
                if event.button() == Qt.MouseButton.LeftButton:
                    self.oldPos = None
                super().mouseReleaseEvent(event)
        
        # 创建自定义对话框
        emoji_dialog = EmojiDialog(self)
        
        # 创建一个内容容器，这个容器将有背景色和圆角
        container = QWidget(emoji_dialog)
        container.setObjectName("container")
        container.setStyleSheet("""
            #container {
                background-color: #ffffff;
                border-radius: 8px;
                border: none;
            }
        """)
        
        # 添加阴影效果到容器
        shadow = QGraphicsDropShadowEffect(emoji_dialog)
        shadow.setBlurRadius(18)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 1)
        container.setGraphicsEffect(shadow)
        
        # 容器的布局
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(9)
        container_layout.setContentsMargins(13, 13, 13, 13)
        
        # 窗口的主布局
        main_layout = QVBoxLayout(emoji_dialog)
        main_layout.setContentsMargins(9, 9, 9, 9)
        main_layout.addWidget(container)
        
        # 标题栏和关闭按钮
        title_bar = QHBoxLayout()
        title_label = QLabel("选择状态栏图标")
        title_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #697a84;
        """)
        
        close_button = QPushButton("×")
        close_button.setFixedSize(20, 20)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #7a8c97;
                font-size: 14px;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #e1b2a9;
                color: white;
            }
            QPushButton:pressed {
                background-color: #d1a298;
            }
        """)
        close_button.clicked.connect(emoji_dialog.close)
        
        title_bar.addWidget(title_label)
        title_bar.addStretch()
        title_bar.addWidget(close_button)
        
        container_layout.addLayout(title_bar)
        
        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #e0e0d9;")
        container_layout.addWidget(separator)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #f0f0e8;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0b8;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # 创建容纳emoji按钮的部件
        emoji_widget = QWidget()
        emoji_layout = QGridLayout(emoji_widget)
        emoji_layout.setSpacing(5)
        
        # 计算每行显示的emoji数量
        emojis_per_row = 6
        
        # 添加emoji按钮
        for i, emoji in enumerate(AVAILABLE_STATUSBAR_ICONS):
            row = i // emojis_per_row
            col = i % emojis_per_row
            
            emoji_button = QToolButton()
            emoji_button.setText(emoji)
            emoji_button.setFixedSize(QSize(40, 40))
            emoji_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
            emoji_button.setStyleSheet("""
                QToolButton {
                    font-size: 18px;
                    background-color: #f5f5f5;
                    border: 1px solid #e0e0d9;
                    border-radius: 5px;
                }
                QToolButton:hover {
                    background-color: #e9e9e2;
                }
                QToolButton:pressed {
                    background-color: #d5d5cc;
                }
            """)
            # 使用lambda确保每个按钮都使用正确的emoji
            emoji_button.clicked.connect(lambda checked=False, e=emoji: self.set_statusbar_icon(e))
            emoji_button.clicked.connect(emoji_dialog.close)  # 选择后自动关闭对话框
            
            emoji_layout.addWidget(emoji_button, row, col)
        
        scroll_area.setWidget(emoji_widget)
        container_layout.addWidget(scroll_area)
        
        # 显示对话框
        emoji_dialog.exec()
    
    def set_statusbar_icon(self, emoji):
        """设置状态栏图标"""
        self.config["statusbar_icon"] = emoji
        save_config()
        
        # 更新图标显示
        self.icon_display.setText(emoji)
        
        # 更新状态栏显示
        status_widget = get_status_widget()
        if status_widget and hasattr(status_widget, 'timer_label'):
            timer = get_pomodoro_timer()
            status_widget.timer_label.updateTimerDisplay(timer)

    def on_icon_clicked(self, event):
        """处理图标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.show_emoji_selector()
        # 调用父类的mousePressEvent以保持其他功能不变
        super(QLabel, self.icon_display).mousePressEvent(event)

    def on_reminder_time_changed(self, value):
        """处理智能提醒时间阈值变更"""
        self.config["smart_timer_reminder_minutes"] = value
        save_config()
