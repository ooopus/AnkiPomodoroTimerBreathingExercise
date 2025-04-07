from aqt import mw
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCalendarWidget,
    QDialogButtonBox,
    QGroupBox,
    QWidget,
    QFrame,
    QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import QDate, Qt, QPoint
from PyQt6.QtGui import QColor, QFont
from ..config import save_config, get_config


class CountdownDialog(QDialog):
    """倒计时设置对话框，设置目标日期和名称。"""

    def __init__(self, parent=None):
        super().__init__(parent or mw, Qt.WindowType.FramelessWindowHint)

        # 设置窗口属性，使背景透明
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 用于跟踪鼠标拖动窗口
        self.oldPos = None

        config = get_config()
        self.setWindowTitle("倒计时设置")
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
        title_label = QLabel("倒计时设置")
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

        # 目标设置组
        group_box = QGroupBox("倒计时目标设置")
        group_box.setStyleSheet("""
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
        group_layout = QVBoxLayout()
        group_layout.setSpacing(6)

        # 目标名称设置
        name_layout = QHBoxLayout()
        name_label = QLabel("目标名称:", self)
        name_label.setStyleSheet("""
            color: #697a84;
            font-size: 11px;
        """)
        self.name_edit = QLineEdit(self)
        self.name_edit.setText(config.get("countdown_target_name", ""))
        self.name_edit.setPlaceholderText("例如：期末考试")
        self.name_edit.setStyleSheet("""
            QLineEdit {
                padding: 4px;
                border: 1px solid #c0c0b8;
                border-radius: 4px;
                background-color: #fcfcf9;
                min-width: 200px;
                font-size: 11px;
                color: #697a84;
            }
            QLineEdit:hover, QLineEdit:focus {
                border: 1px solid #95aab5;
            }
        """)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        group_layout.addLayout(name_layout)

        # 日期选择
        date_label = QLabel("目标日期:", self)
        date_label.setStyleSheet("""
            color: #697a84;
            font-size: 11px;
        """)
        group_layout.addWidget(date_label)
        
        self.calendar = QCalendarWidget(self)
        self.calendar.setStyleSheet("""
            /* 整体日历容器样式 */
            QCalendarWidget {
                background-color: #fcfcf9;
                border: 1px solid #c0c0b8;
                border-radius: 8px;
                selection-background-color: #a9bec9;
                selection-color: white;
                font-size: 11px;
            }
            
            /* 日历导航栏样式 */
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #f5f5f5;
                border-top-left-radius: 7px;
                border-top-right-radius: 7px;
                border-bottom: 1px solid #e0e0d9;
                padding: 4px;
            }
            
            /* 月份年份下拉框样式 */
            QCalendarWidget QToolButton {
                color: #697a84;
                background-color: transparent;
                font-size: 12px;
                font-weight: bold;
                border-radius: 4px;
                padding: 3px 6px;
                margin: 2px;
            }
            
            QCalendarWidget QToolButton:hover {
                background-color: #f0f0f0;
            }
            
            QCalendarWidget QToolButton:pressed {
                background-color: #e0e0e0;
            }
            
            /* 月份标签样式 */
            QCalendarWidget QSpinBox {
                font-size: 12px;
                color: #697a84;
                background-color: #fcfcf9;
                selection-background-color: #a9bec9;
                selection-color: white;
                border: 1px solid #c0c0b8;
                border-radius: 3px;
            }
            
            /* 日历表格样式 */
            QCalendarWidget QTableView {
                alternate-background-color: transparent;
                background-color: #fcfcf9;
                outline: none;
                selection-background-color: transparent;
                selection-color: #333333;
                border: none;
                padding: 2px;
                font-size: 11px;
            }
            
            /* 表头（星期几）样式 */
            QCalendarWidget QTableView QHeaderView {
                background-color: #f5f5f5;
                color: #697a84;
                font-weight: bold;
                font-size: 11px;
                border: none;
                border-bottom: 1px solid #e0e0d9;
            }
            
            QCalendarWidget QTableView QHeaderView::section {
                background-color: transparent;
                color: #697a84;
                padding: 3px;
                border: none;
            }
            
            /* 日期单元格样式 */
            QCalendarWidget QTableView QAbstractItemView:enabled {
                outline: none;
                selection-background-color: transparent;
                selection-color: #333333;
            }
            
            /* 不在当前月的日期 */
            QCalendarWidget QTableView QAbstractItemView:disabled {
                color: #c0c0b8;
            }
            
            /* 今天日期样式 */
            QCalendarWidget QTableView QAbstractItemView:item:focus {
                background-color: #f0f0f0;
                border-radius: 4px;
            }
            
            /* 选中日期样式 */
            QCalendarWidget QTableView QAbstractItemView:item:selected {
                background-color: #a9bec9;
                color: white;
                border-radius: 4px;
            }
            
            /* 悬停日期样式 */
            QCalendarWidget QTableView QAbstractItemView:item:hover {
                background-color: #f0f0f0;
                border-radius: 4px;
            }
            
            /* 下拉菜单样式 */
            QCalendarWidget QMenu {
                background-color: #fcfcf9;
                border: 1px solid #c0c0b8;
                border-radius: 4px;
                padding: 2px;
                color: #697a84;
            }
            
            QCalendarWidget QMenu::item {
                padding: 3px 15px 3px 10px;
                border-radius: 3px;
            }
            
            QCalendarWidget QMenu::item:selected {
                background-color: #a9bec9;
                color: white;
            }
            
            /* 向左向右箭头按钮样式 */
            QCalendarWidget QToolButton#qt_calendar_prevmonth {
                qproperty-text: "上个月";
                icon-size: 0px;
                qproperty-icon: none;
                background-image: none;
                color: #006400;
                background-color: transparent;
                font-size: 11px;
                padding: 2px 5px;
                border-radius: 3px;
            }
            
            QCalendarWidget QToolButton#qt_calendar_nextmonth {
                qproperty-text: "下个月";
                icon-size: 0px;
                qproperty-icon: none;
                background-image: none;
                color: #006400;
                background-color: transparent;
                font-size: 11px;
                padding: 2px 5px;
                border-radius: 3px;
            }
        """)
        current_date = QDate.currentDate()
        
        # 如果已有设置的目标日期，则使用它
        target_date_str = config.get("countdown_target_date", "")
        if target_date_str:
            try:
                parts = target_date_str.split("-")
                if len(parts) == 3:
                    year, month, day = map(int, parts)
                    target_date = QDate(year, month, day)
                    if target_date.isValid():
                        self.calendar.setSelectedDate(target_date)
            except Exception as e:
                print(f"Error parsing target date: {e}")
        
        # 最小日期设置为今天
        self.calendar.setMinimumDate(current_date)
        group_layout.addWidget(self.calendar)
        
        group_box.setLayout(group_layout)
        container_layout.addWidget(group_box)
        
        # 连续专注天数显示
        focus_days = config.get("consecutive_focus_days", 0)
        focus_layout = QHBoxLayout()
        focus_label = QLabel(f"你已连续专注: {focus_days} 天", self)
        focus_label.setStyleSheet("""
            color: #697a84;
            font-size: 11px;
        """)
        focus_layout.addWidget(focus_label)
        
        reset_button = QPushButton("重置", self)
        reset_button.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #697a84;
                border: 1px solid #c0c0b8;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #95aab5;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """)
        reset_button.clicked.connect(self.reset_consecutive_days)
        focus_layout.addWidget(reset_button)
        
        container_layout.addLayout(focus_layout)

        # 按钮
        button_layout = QHBoxLayout()
        
        # 保存按钮
        save_button = QPushButton("保存", self)
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #a9bec9;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 11px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #95aab5;
            }
            QPushButton:pressed {
                background-color: #809aaa;
            }
        """)
        save_button.clicked.connect(self.accept)
        
        # 取消按钮
        cancel_button = QPushButton("取消", self)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #697a84;
                border: 1px solid #c0c0b8;
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 11px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #95aab5;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        
        container_layout.addLayout(button_layout)
        container_layout.addStretch()

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

    def accept(self):
        """保存设置并关闭对话框"""
        config = get_config()
        
        # 保存目标名称
        config["countdown_target_name"] = self.name_edit.text()
        
        # 保存目标日期
        selected_date = self.calendar.selectedDate()
        date_str = f"{selected_date.year()}-{selected_date.month()}-{selected_date.day()}"
        config["countdown_target_date"] = date_str
        
        # 保存配置
        save_config()
        
        # 更新状态栏显示
        self.update_statusbar()
        
        super().accept()
    
    def reset_consecutive_days(self):
        """重置连续专注天数"""
        config = get_config()
        config["consecutive_focus_days"] = 0
        config["last_focus_date"] = ""
        save_config()
        
        # 更新显示
        for child in self.findChildren(QLabel):
            if "连续专注" in child.text():
                child.setText("你已连续专注: 0 天")
                break
            
        # 更新状态栏显示
        self.update_statusbar()
    
    def update_statusbar(self):
        """更新状态栏信息显示"""
        try:
            from .statusbar import get_status_widget
            status_widget = get_status_widget()
            if status_widget:
                status_widget.update_display()
        except Exception as e:
            print(f"更新状态栏显示出错: {e}")


def show_countdown_dialog():
    """显示倒计时设置对话框"""
    dialog = CountdownDialog(mw)
    return dialog.exec() 