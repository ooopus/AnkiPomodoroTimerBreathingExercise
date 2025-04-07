import os
import sys
import json
import math
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, date
import calendar

from PyQt6.QtCore import Qt, QSize, QDate, QTimer, pyqtSignal, QPoint, QTime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QGridLayout, QPushButton, QSizePolicy,
    QMessageBox, QScrollArea, QFrame, QListWidget, 
    QListWidgetItem, QMenu, QInputDialog, QComboBox, QFileDialog,
    QGraphicsDropShadowEffect, QLineEdit, QTimeEdit
)
from PyQt6.QtGui import QFont, QColor, QPalette, QAction, QIcon, QCursor, QDrag

from aqt import mw
from aqt.utils import tooltip

from ..storage import get_storage
from .simple_charts import create_color_list
from ..config import get_config, save_config, get_state
from ..constants import AVAILABLE_STATUSBAR_ICONS


class DailyTaskItem(QWidget):
    """单个打卡任务小部件"""
    
    def __init__(self, task_id, task_name, streak_days, parent=None, emoji="🍅"):
        super().__init__(parent)
        self.task_id = task_id
        self.task_name = task_name
        self.streak_days = streak_days
        self.checked_today = False
        self.emoji = emoji
        
        # 安装事件过滤器，以便捕获双击事件
        self.installEventFilter(self)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 3, 5, 3)  # 减小上下边距
        layout.setSpacing(10)
        
        # 显示任务的emoji图标
        config = get_config()
        displayed_tasks = config.get("statusbar_checkin_tasks", [])
        
        # 创建透明的emoji按钮，无背景
        self.emoji_button = QPushButton(emoji)
        self.emoji_button.setToolTip("点击切换是否在状态栏显示该任务")
        self.emoji_button.setFixedWidth(24)
        self.emoji_button.setFixedHeight(24)
        self.emoji_button.setCheckable(True)
        self.emoji_button.setChecked(task_id in displayed_tasks)
        self.emoji_button.clicked.connect(self.toggle_statusbar_display)
        
        # 移除所有背景和边框，只显示emoji文本，并垂直居中显示
        self.emoji_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
                text-align: center;
            }
        """)
        
        # 添加emoji按钮并设置垂直居中对齐
        layout.addWidget(self.emoji_button, 0, Qt.AlignmentFlag.AlignVCenter)
        
        # 任务名称
        self.name_label = QLabel(task_name)
        self.name_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.name_label, 0, Qt.AlignmentFlag.AlignVCenter)  # 添加垂直居中对齐
        
        layout.addStretch()
        
        # 连续打卡天数
        streak_text = f"连续 {streak_days} 天" if streak_days > 0 else ""
        self.streak_label = QLabel(streak_text)
        self.streak_label.setStyleSheet("color: #81C784; font-size: 13px;")
        layout.addWidget(self.streak_label)
        
        # 打卡按钮
        self.checkin_button = QPushButton("打卡")
        self.checkin_button.setStyleSheet(
            "QPushButton { background-color: #81C784; color: white; border-radius: 4px; padding: 3px 15px; min-height: 14px; }"
            "QPushButton:hover { background-color: #66BB6A; }"
        )
        self.checkin_button.setFixedWidth(80)
        self.checkin_button.setFixedHeight(24)  # 固定高度
        layout.addWidget(self.checkin_button, 0, Qt.AlignmentFlag.AlignVCenter)  # 垂直居中对齐
        
        # 设置整个小部件的样式 - 移除边框
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border: 0px;
                border-radius: 4px;
            }
            QWidget:hover {
                background-color: #f5f5f5;
            }
        """)
        
        # 更新按钮状态
        self.update_button_state()
        
        # 更新名称标签颜色，显示是否在状态栏中显示
        self.update_statusbar_display()
    
    def eventFilter(self, obj, event):
        """事件过滤器，用于捕获双击事件"""
        if obj == self and event.type() == event.Type.MouseButtonDblClick and event.button() == Qt.MouseButton.LeftButton:
            # 触发双击操作
            self.show_options_menu()
            return True
        return super().eventFilter(obj, event)
    
    def show_options_menu(self):
        """显示操作菜单（用于双击事件）"""
        # 查找父对话框
        parent_dialog = self.parent()
        while parent_dialog and not isinstance(parent_dialog, CheckinDialog):
            parent_dialog = parent_dialog.parent()
        
        if parent_dialog:
            # 创建菜单
            menu = QMenu()
            
            # 添加重命名选项
            rename_action = QAction("重命名任务", self)
            rename_action.triggered.connect(lambda: parent_dialog.rename_task(self.task_id))
            menu.addAction(rename_action)
            
            # 添加取消今日打卡选项（如果已打卡）
            if self.checked_today:
                cancel_action = QAction("取消今日打卡", self)
                cancel_action.triggered.connect(lambda: parent_dialog.cancel_checkin(self.task_id))
                menu.addAction(cancel_action)
            
            # 添加删除选项
            menu.addSeparator()
            delete_action = QAction("删除任务", self)
            delete_action.triggered.connect(lambda: parent_dialog.delete_task(self.task_id))
            menu.addAction(delete_action)
            
            # 在当前项的位置显示菜单
            menu.exec(self.mapToGlobal(self.rect().center()))
    
    def update_streak(self, streak_days):
        """更新连续打卡天数显示"""
        self.streak_days = streak_days
        streak_text = f"连续 {streak_days} 天" if streak_days > 0 else ""
        self.streak_label.setText(streak_text)
    
    def update_button_state(self, is_checked=False):
        """更新打卡按钮状态"""
        self.checked_today = is_checked
        if is_checked:
            self.checkin_button.setText("已打卡")
            self.checkin_button.setStyleSheet(
                "QPushButton { background-color: #C8E6C9; color: white; border-radius: 4px; padding: 3px 15px; min-height: 14px; }"
                "QPushButton:hover { background-color: #B8D8B9; }"
            )
            self.checkin_button.setEnabled(False)
        else:
            self.checkin_button.setText("打卡")
            self.checkin_button.setStyleSheet(
                "QPushButton { background-color: #81C784; color: white; border-radius: 4px; padding: 3px 15px; min-height: 14px; }"
                "QPushButton:hover { background-color: #66BB6A; }"
            )
            self.checkin_button.setEnabled(True)
    
    def update_statusbar_display(self):
        """更新状态栏显示状态的视觉效果"""
        # 使用任务名称颜色表示是否在状态栏显示
        if self.emoji_button.isChecked():
            # 在状态栏显示时，名称为绿色，与打卡按钮颜色一致
            self.name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #81C784;")
        else:
            # 不在状态栏显示时，名称为默认颜色
            self.name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
    
    def toggle_statusbar_display(self):
        """切换状态栏显示状态"""
        try:
            from aqt import mw
            from aqt.utils import tooltip
            
            # 获取全局配置
            config = get_config()
            displayed_tasks = config.get("statusbar_checkin_tasks", [])
            
            # 切换显示状态
            if self.emoji_button.isChecked():
                if self.task_id not in displayed_tasks:
                    displayed_tasks.append(self.task_id)
                    print(f"添加任务 {self.task_name} (ID: {self.task_id}) 到状态栏显示")
            else:
                if self.task_id in displayed_tasks:
                    displayed_tasks.remove(self.task_id)
                    print(f"从状态栏移除任务 {self.task_name} (ID: {self.task_id})")
            
            # 更新配置
            config["statusbar_checkin_tasks"] = displayed_tasks
            
            # 先获取全局配置单例对象
            state = get_state()
            # 更新配置
            state._config = config
            # 保存配置（不传参数）
            save_config()
            
            print(f"保存配置成功，当前状态栏显示任务IDs: {displayed_tasks}")
            
            # 更新显示样式 - 更改为更新名称颜色
            self.update_statusbar_display()
            
            # 立即更新状态栏显示 - 通过各种可能的方式尝试更新
            
            # 方式1: 直接更新countdown_info_label
            if hasattr(mw, 'countdown_info_label'):
                try:
                    print("尝试通过countdown_info_label更新状态栏...")
                    mw.countdown_info_label.updateCountdownDisplay()
                except Exception as e:
                    print(f"通过countdown_info_label更新状态栏出错: {e}")
            
            # 方式2: 通过pomodoro_status_widget更新
            if hasattr(mw, 'pomodoro_status_widget'):
                try:
                    print("尝试通过pomodoro_status_widget更新状态栏...")
                    if hasattr(mw.pomodoro_status_widget, 'info_label'):
                        mw.pomodoro_status_widget.info_label.updateCountdownDisplay()
                    mw.pomodoro_status_widget.update_display()
                except Exception as e:
                    print(f"通过pomodoro_status_widget更新状态栏出错: {e}")
            
            # 方式3: 使用statusbar.py中的get_status_widget函数
            try:
                print("尝试通过get_status_widget()更新状态栏...")
                from ..ui.statusbar import get_status_widget
                status_widget = get_status_widget()
                if status_widget:
                    status_widget.update_display()
            except Exception as e:
                print(f"通过get_status_widget()更新状态栏出错: {e}")
            
            # 方式4: 刷新整个状态栏
            if hasattr(mw, 'statusBar'):
                try:
                    print("尝试刷新整个状态栏...")
                    mw.statusBar().update()
                except Exception as e:
                    print(f"刷新状态栏出错: {e}")
            
            # 提示用户操作成功
            if self.emoji_button.isChecked():
                tooltip(f"已添加'{self.task_name}'到状态栏显示", period=1000)
            else:
                tooltip(f"已从状态栏移除'{self.task_name}'", period=1000)
                
        except Exception as e:
            print(f"切换状态栏显示状态出错: {e}")
            import traceback
            traceback.print_exc()


class CalendarWidget(QWidget):
    """日历打卡记录显示小部件"""
    
    # 添加自定义信号
    date_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
        # 当前选择的月份和年份
        self.current_date = datetime.now()
        
        # 当前选择的任务ID
        self.current_task_id = None
        
        # 显示数据
        self.check_data = {}  # {日期: 是否打卡}
        
        # 选中的日期
        self.selected_date = None
        
        # 初始化时更新日历显示
        self.update_calendar()
    
    def initUI(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 顶部月份导航栏
        nav_layout = QHBoxLayout()
        
        # 上个月按钮
        self.prev_month_btn = QPushButton("◀")
        self.prev_month_btn.setFixedWidth(30)
        self.prev_month_btn.setFixedHeight(24)  # 增加高度
        self.prev_month_btn.setStyleSheet("font-size: 14px; padding: 2px;")
        self.prev_month_btn.clicked.connect(self.prev_month)
        nav_layout.addWidget(self.prev_month_btn)
        
        # 月份年份显示
        self.month_label = QLabel()
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.month_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 4px;")
        self.month_label.setFixedHeight(24)  # 增加高度
        nav_layout.addWidget(self.month_label)
        
        # 下个月按钮
        self.next_month_btn = QPushButton("▶")
        self.next_month_btn.setFixedWidth(30)
        self.next_month_btn.setFixedHeight(24)  # 增加高度
        self.next_month_btn.setStyleSheet("font-size: 14px; padding: 2px;")
        self.next_month_btn.clicked.connect(self.next_month)
        nav_layout.addWidget(self.next_month_btn)
        
        # 增加导航栏的上下边距
        nav_layout.setContentsMargins(0, 6, 0, 6)
        
        layout.addLayout(nav_layout)
        
        # 日历网格
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(5)
        
        # 添加星期几标签
        weekdays = ["一", "二", "三", "四", "五", "六", "日"]
        for i, day in enumerate(weekdays):
            label = QLabel(day)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-weight: bold; color: #666;")
            self.grid_layout.addWidget(label, 0, i)
        
        # 创建日期单元格
        self.date_cells = []
        for row in range(1, 7):
            row_cells = []
            for col in range(7):
                cell = QPushButton()
                cell.setFixedSize(35, 35)
                cell.setStyleSheet("""
                    QPushButton {
                        border: 1px solid #ddd;
                        border-radius: 17px;
                        padding: 5px;
                        background-color: white;
                        text-align: center;
                    }
                    QPushButton:hover {
                        background-color: #f0f0f0;
                    }
                """)
                # 连接点击事件
                cell.clicked.connect(self.on_date_cell_clicked)
                self.grid_layout.addWidget(cell, row, col)
                row_cells.append(cell)
            self.date_cells.append(row_cells)
        
        layout.addLayout(self.grid_layout)
    
    def on_date_cell_clicked(self):
        """当日期单元格被点击时触发"""
        # 获取发送信号的按钮
        sender = self.sender()
        if not sender or not sender.text():
            return
        
        # 获取日期
        try:
            day = int(sender.text())
            year = self.current_date.year
            month = self.current_date.month
            selected_date = date(year, month, day)
            
            # 如果是未来日期，不处理
            if selected_date > datetime.now().date():
                return
            
            # 格式化为字符串
            date_str = selected_date.strftime("%Y-%m-%d")
            
            # 更新选中状态
            self.selected_date = date_str
            self.update_calendar()
            
            # 发出信号
            self.date_selected.emit(date_str)
        except ValueError:
            pass
    
    def update_calendar(self):
        """更新日历显示"""
        # 清空所有单元格
        for row in self.date_cells:
            for cell in row:
                cell.setText("")
                cell.setStyleSheet("""
                    QPushButton {
                        border: 1px solid #ddd;
                        border-radius: 17px;
                        padding: 5px;
                        background-color: white;
                        text-align: center;
                    }
                    QPushButton:hover {
                        background-color: #f0f0f0;
                    }
                """)
                cell.setEnabled(False)
                cell.setVisible(True)  # 默认所有单元格可见
        
        # 更新月份标题
        month_name = self.current_date.strftime("%Y年%m月")
        self.month_label.setText(month_name)
        
        # 获取月份第一天是星期几 (0是星期一)
        year = self.current_date.year
        month = self.current_date.month
        first_day = datetime(year, month, 1)
        weekday = first_day.weekday()  # 0是星期一
        
        # 获取月份的天数
        _, num_days = calendar.monthrange(year, month)
        
        # 填充日期
        day = 1
        today = datetime.now().date()
        
        for row in range(6):
            row_empty = True  # 标记当前行是否为空
            
            for col in range(7):
                date_cell = self.date_cells[row][col]
                
                if (row == 0 and col < weekday) or day > num_days:
                    date_cell.setText("")
                    date_cell.setEnabled(False)
                    date_cell.setStyleSheet("""
                        QPushButton {
                            border: 1px solid #ddd;
                            border-radius: 17px;
                            padding: 5px;
                            background-color: white;
                            text-align: center;
                        }
                    """)
                    continue
                
                # 如果这行至少有一个单元格有内容，标记为非空
                if day <= num_days:
                    row_empty = False
                
                date_cell.setText(str(day))
                date_cell.setEnabled(True)
                
                # 构建当前单元格日期
                cell_date = date(year, month, day)
                date_str = cell_date.strftime("%Y-%m-%d")
                
                # 检查是否打卡以及是否为今天
                is_checked = self.check_data.get(date_str, False)
                is_today = (cell_date == today)
                is_selected = (date_str == self.selected_date)
                is_future = (cell_date > today)
                
                # 根据不同情况设置样式
                if is_future:
                    # 未来日期禁用且显示灰色
                    date_cell.setEnabled(False)
                    date_cell.setStyleSheet("""
                        QPushButton {
                            border: 1px solid #ddd;
                            border-radius: 17px;
                            padding: 5px;
                            background-color: #f5f5f5;
                            color: #aaa;
                            text-align: center;
                        }
                    """)
                elif is_today:
                    if is_checked:
                        if is_selected:
                            # 今天被选中且已打卡
                            date_cell.setStyleSheet("""
                                QPushButton {
                                    border: 2px solid #FF7F50;
                                    color: white;
                                    border-radius: 17px;
                                    padding: 5px;
                                    background-color: #4CAF50;
                                    font-weight: bold;
                                    text-align: center;
                                }
                                QPushButton:hover {
                                    background-color: #45a049;
                                }
                            """)
                        else:
                            # 今天未被选中，但已打卡
                            date_cell.setStyleSheet("""
                                QPushButton {
                                    border: 2px solid #4CAF50;
                                    color: white;
                                    border-radius: 17px;
                                    padding: 5px;
                                    background-color: #4CAF50;
                                    font-weight: bold;
                                    text-align: center;
                                }
                                QPushButton:hover {
                                    background-color: #45a049;
                                }
                            """)
                    else:
                        if is_selected:
                            # 今天被选中且未打卡
                            date_cell.setStyleSheet("""
                                QPushButton {
                                    border: 2px solid #FF7F50;
                                    color: #2196F3;
                                    border-radius: 17px;
                                    padding: 5px;
                                    background-color: white;
                                    font-weight: bold;
                                    text-align: center;
                                }
                                QPushButton:hover {
                                    background-color: #e3f2fd;
                                }
                            """)
                        else:
                            # 今天未被选中且未打卡
                            date_cell.setStyleSheet("""
                                QPushButton {
                                    border: 2px solid #2196F3;
                                    color: #2196F3;
                                    border-radius: 17px;
                                    padding: 5px;
                                    background-color: white;
                                    font-weight: bold;
                                    text-align: center;
                                }
                                QPushButton:hover {
                                    background-color: #e3f2fd;
                                }
                            """)
                elif is_selected:
                    # 选中日期使用珊瑚红色边框
                    if is_checked:
                        date_cell.setStyleSheet("""
                            QPushButton {
                                border: 2px solid #FF7F50;
                                color: white;
                                border-radius: 17px;
                                padding: 5px;
                                background-color: #81C784;
                                font-weight: bold;
                                text-align: center;
                            }
                            QPushButton:hover {
                                background-color: #66BB6A;
                            }
                        """)
                    else:
                        date_cell.setStyleSheet("""
                            QPushButton {
                                border: 2px solid #FF7F50;
                                color: #2E7D32;
                                border-radius: 17px;
                                padding: 5px;
                                background-color: #E8F5E9;
                                font-weight: bold;
                                text-align: center;
                            }
                            QPushButton:hover {
                                background-color: #C8E6C9;
                            }
                        """)
                elif is_checked:
                    date_cell.setStyleSheet("""
                        QPushButton {
                            border: 1px solid #4CAF50;
                            color: white;
                            border-radius: 17px;
                            padding: 5px;
                            background-color: #4CAF50;
                            text-align: center;
                        }
                        QPushButton:hover {
                            background-color: #45a049;
                        }
                    """)
                
                day += 1
            
            # 如果当前行为空，隐藏整行
            if row_empty:
                for col in range(7):
                    self.date_cells[row][col].setVisible(False)
    
    def set_task(self, task_id):
        """设置当前任务ID并更新日历"""
        self.current_task_id = task_id
        
        # 如果传入None，清空日历
        if task_id is None:
            self.check_data = {}
        
        self.update_calendar()
    
    def set_check_data(self, check_data):
        """设置打卡数据"""
        self.check_data = check_data
        self.update_calendar()
    
    def prev_month(self):
        """显示上个月"""
        year = self.current_date.year
        month = self.current_date.month - 1
        
        if month < 1:
            year -= 1
            month = 12
        
        self.current_date = self.current_date.replace(year=year, month=month, day=1)
        self.update_calendar()
    
    def next_month(self):
        """显示下个月"""
        year = self.current_date.year
        month = self.current_date.month + 1
        
        if month > 12:
            year += 1
            month = 1
        
        self.current_date = self.current_date.replace(year=year, month=month, day=1)
        self.update_calendar()


class TaskListWidget(QListWidget):
    """自定义的任务列表Widget，支持拖动时的半透明效果"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setSpacing(3)  # 设置项目之间的间距
    
    def startDrag(self, supportedActions):
        """重写开始拖动方法，实现半透明效果"""
        drag = QDrag(self)
        mimeData = self.model().mimeData(self.selectedIndexes())
        drag.setMimeData(mimeData)
        
        # 获取当前选中的项并设置透明度
        item = self.currentItem()
        if item:
            # 启动拖动操作时设置透明度和边框效果
            widget = self.itemWidget(item)
            if widget:
                orig_style = widget.styleSheet()
                # 设置半透明效果和虚线边框
                drag_style = """
                QWidget {
                    opacity: 0.7; 
                    background-color: rgba(225, 245, 254, 0.6);
                    border: 0px;
                    border-radius: 4px;
                }
                """
                widget.setStyleSheet(orig_style + drag_style)
                
            # 执行拖动操作
            result = drag.exec(supportedActions)
            
            # 拖动结束后恢复原来的样式
            if widget:
                widget.setStyleSheet(orig_style)
        else:
            super().startDrag(supportedActions)


class CheckinDialog(QDialog):
    """每日打卡对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self.setWindowTitle("每日打卡")
        self.resize(800, 600)
        
        # 设置无边框模式
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 窗口拖动相关变量
        self.dragging = False
        self.drag_position = None
        
        self.storage = get_storage()
        self.task_items = {}  # {task_id: DailyTaskItem}
        
        self.init_ui()
        self.load_tasks()
    
    # 鼠标按下事件处理
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    # 鼠标移动事件处理
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    # 鼠标释放事件处理
    def mouseReleaseEvent(self, event):
        self.dragging = False
        event.accept()
    
    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)  # 调整边距
        
        # 创建一个用于背景的主容器，添加阴影和圆角
        main_widget = QWidget(self)
        main_widget.setObjectName("mainContainer")
        main_widget.setStyleSheet("""
            QWidget#mainContainer {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        # 创建阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 0)
        main_widget.setGraphicsEffect(shadow)
        
        # 主容器的布局
        container_layout = QVBoxLayout(main_widget)
        container_layout.setContentsMargins(10, 10, 10, 10)
        
        # 顶部标题栏和关闭按钮
        title_bar = QHBoxLayout()
        
        # 顶部标题
        title_label = QLabel("每日打卡")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 5px 0;")
        title_bar.addWidget(title_label)
        
        title_bar.addStretch()
        
        # 添加关闭按钮
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
        close_btn.clicked.connect(self.accept)
        title_bar.addWidget(close_btn)
        
        container_layout.addLayout(title_bar)
        
        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #e0e0e0;")
        container_layout.addWidget(separator)
        
        # 主要内容布局
        content_layout = QHBoxLayout()
        
        # 左侧任务列表区域
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 任务列表标题和添加按钮
        task_header_layout = QHBoxLayout()
        task_list_label = QLabel("打卡任务列表")
        task_list_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        task_header_layout.addWidget(task_list_label)
        
        task_header_layout.addStretch()
        
        # 添加任务按钮
        add_task_button = QPushButton("添加任务")
        add_task_button.setStyleSheet(
            "QPushButton { background-color: #78A5D1; color: white; border-radius: 4px; padding: 5px 10px; }"
            "QPushButton:hover { background-color: #6B95BD; }"
        )
        add_task_button.clicked.connect(self.add_task)
        task_header_layout.addWidget(add_task_button)
        
        left_layout.addLayout(task_header_layout)
        
        # 任务列表
        self.task_list = TaskListWidget()
        self.task_list.setStyleSheet("""
            QListWidget { 
                border: 1px solid #ddd; 
                border-radius: 4px; 
                background-color: #f9f9f9;
            }
            QListWidget::item { 
                margin: 3px 0px;
                background-color: transparent;
                border: 0px;
                border-radius: 4px;
            }
            QListWidget::item:selected { 
                background-color: #e1f5fe; 
                border: 0px;
            }
            QListWidget::item:hover { 
                background-color: #f5f5f5; 
            }
        """)
        self.task_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.task_list.customContextMenuRequested.connect(self.show_task_context_menu)
        self.task_list.currentRowChanged.connect(self.on_task_selected)
        self.task_list.model().rowsMoved.connect(self.on_tasks_reordered)
        
        left_layout.addWidget(self.task_list)
        
        # 右侧日历区域
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 日历标题和补打卡部分
        calendar_header = QHBoxLayout()
        
        # 日历标题和"今天"按钮
        calendar_title_layout = QHBoxLayout()
        calendar_title = QLabel("打卡日历")
        calendar_title.setStyleSheet("font-size: 15px; font-weight: bold;")
        calendar_title_layout.addWidget(calendar_title)
        
        # 添加"今天"按钮
        today_button = QPushButton("今天")
        today_button.setStyleSheet(
            "QPushButton { background-color: #A5D6A7; color: white; border-radius: 4px; padding: 2px 10px; }"
            "QPushButton:hover { background-color: #93C595; }"
        )
        today_button.setFixedWidth(60)
        today_button.setFixedHeight(24)
        today_button.clicked.connect(self.goto_today)
        calendar_title_layout.addWidget(today_button)
        
        calendar_title_layout.addStretch()
        calendar_header.addLayout(calendar_title_layout)
        
        # 补打卡部分
        makeup_label = QLabel("补打卡日期:")
        calendar_header.addWidget(makeup_label)
        
        # 日期选择器
        self.date_selector = QComboBox()
        # 首先添加今天的日期选项
        today = datetime.now().date()
        today_str = today.strftime("%Y-%m-%d")
        self.date_selector.addItem("今天", today_str)
        # 添加过去15天的日期选项
        for i in range(1, 16):
            past_date = today - timedelta(days=i)
            date_str = past_date.strftime("%Y-%m-%d")
            display_str = past_date.strftime("%m-%d")
            self.date_selector.addItem(f"{display_str}", date_str)
        # 当选择的日期变化时更新取消按钮状态
        self.date_selector.currentIndexChanged.connect(self.update_cancel_button_state)
        calendar_header.addWidget(self.date_selector)
        
        # 补打卡按钮
        self.makeup_button = QPushButton("补打卡")
        self.makeup_button.setStyleSheet(
            "QPushButton { background-color: #FFB74D; color: white; border-radius: 4px; padding: 5px 10px; }"
            "QPushButton:hover { background-color: #FFA726; }"
        )
        self.makeup_button.clicked.connect(self.makeup_checkin)
        self.makeup_button.setEnabled(False)  # 默认禁用，直到选择任务
        calendar_header.addWidget(self.makeup_button)
        
        # 取消打卡按钮
        self.cancel_date_button = QPushButton("取消打卡")
        self.cancel_date_button.setStyleSheet(
            "QPushButton { background-color: #EF9A9A; color: white; border-radius: 4px; padding: 5px 10px; }"
            "QPushButton:hover { background-color: #E57373; }"
        )
        self.cancel_date_button.clicked.connect(self.cancel_date_checkin)
        self.cancel_date_button.setEnabled(False)  # 默认禁用
        calendar_header.addWidget(self.cancel_date_button)
        
        right_layout.addLayout(calendar_header)
        
        # 添加一个空白间隔，将日历下移
        spacer = QFrame()
        spacer.setFrameShape(QFrame.Shape.NoFrame)
        spacer.setFixedHeight(10)  # 10像素的垂直间隔
        right_layout.addWidget(spacer)
        
        # 日历组件
        self.calendar = CalendarWidget()
        self.calendar.date_selected.connect(self.on_calendar_date_selected)
        right_layout.addWidget(self.calendar)
        
        # 打卡信息显示
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("font-size: 14px; color: #666;")
        right_layout.addWidget(self.info_label)
        
        # 设置左右两侧的拉伸比例
        content_layout.addWidget(left_panel, 4)
        content_layout.addWidget(right_panel, 6)
        
        container_layout.addLayout(content_layout)
        
        # 将主容器添加到对话框布局
        main_layout.addWidget(main_widget, 1)  # 1是拉伸系数，使其填充整个对话框
        
        # 底部区域
        bottom_layout = QHBoxLayout()
        
        # 打卡提醒设置
        reminder_layout = QHBoxLayout()
        
        # 提醒标签和按钮
        reminder_label = QLabel("打卡提醒:")
        reminder_label.setStyleSheet("font-size: 14px;")
        reminder_layout.addWidget(reminder_label)
        
        # 提醒开关按钮
        self.reminder_button = QPushButton("启用提醒")
        self.reminder_button.setStyleSheet(
            "QPushButton { background-color: #81C784; color: white; border-radius: 4px; padding: 5px 10px; }"
            "QPushButton:hover { background-color: #66BB6A; }"
            "QPushButton:disabled { background-color: #B0BEC5; color: white; }"
        )
        self.reminder_button.clicked.connect(self.toggle_reminder)
        reminder_layout.addWidget(self.reminder_button)
        
        # 时间选择器 - 使用QTimeEdit替代QComboBox
        self.time_selector = QTimeEdit()
        self.time_selector.setDisplayFormat("HH:mm")
        self.time_selector.setFixedWidth(100)
        self.time_selector.setStyleSheet("""
            QTimeEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 2px 8px;
                min-height: 25px;
                background-color: #ffffff;
            }
            QTimeEdit::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 16px;
                border-left: 1px solid #ccc;
                border-top-right-radius: 3px;
            }
            QTimeEdit::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 16px;
                border-left: 1px solid #ccc;
                border-bottom-right-radius: 3px;
            }
            QTimeEdit::up-button:hover, QTimeEdit::down-button:hover {
                background-color: #f0f0f0;
            }
        """)
        
        # 设置当前时间为默认选中的时间
        current_time = QTime.currentTime()
        self.time_selector.setTime(current_time)
        
        # 时间改变时保存设置
        self.time_selector.timeChanged.connect(self.save_reminder_time)
        reminder_layout.addWidget(self.time_selector)
        
        reminder_layout.addStretch()
        bottom_layout.addLayout(reminder_layout)
        
        # 右侧留空
        bottom_layout.addStretch()
        
        container_layout.addLayout(bottom_layout)
        
        # 加载现有的提醒设置
        self.load_reminder_settings()
    
    def toggle_reminder(self):
        """切换提醒状态"""
        if self.reminder_button.text() == "启用提醒":
            # 启用提醒
            reminder_time = self.time_selector.time().toString("HH:mm")
            reminder_id = self.storage.save_reminder(reminder_time)
            if reminder_id:
                self.reminder_button.setText("已启用")
                self.reminder_button.setStyleSheet(
                    "QPushButton { background-color: #C8E6C9; color: white; border-radius: 4px; padding: 5px 10px; }"
                    "QPushButton:hover { background-color: #B8D8B9; }"
                )
                tooltip("打卡提醒已设置")
        else:
            # 禁用提醒
            reminder = self.storage.get_reminder()
            if reminder and self.storage.disable_reminder(reminder['id']):
                self.reminder_button.setText("启用提醒")
                self.reminder_button.setStyleSheet(
                    "QPushButton { background-color: #81C784; color: white; border-radius: 4px; padding: 5px 10px; }"
                    "QPushButton:hover { background-color: #66BB6A; }"
                )
                tooltip("打卡提醒已关闭")
    
    def save_reminder_time(self):
        """保存提醒时间"""
        # 仅当提醒已启用时才更新时间
        if self.reminder_button.text() == "已启用":
            reminder_time = self.time_selector.time().toString("HH:mm")
            reminder_id = self.storage.save_reminder(reminder_time)
            # 删除提示消息
            # if reminder_id:
            #     tooltip("已更新打卡提醒时间")
    
    def load_reminder_settings(self):
        """加载提醒设置"""
        reminder = self.storage.get_reminder()
        if reminder and reminder['enabled']:
            self.reminder_button.setText("已启用")
            self.reminder_button.setStyleSheet(
                "QPushButton { background-color: #C8E6C9; color: white; border-radius: 4px; padding: 5px 10px; }"
                "QPushButton:hover { background-color: #B8D8B9; }"
            )
            # 设置时间选择器为保存的时间
            if reminder['reminder_time']:
                time = QTime.fromString(reminder['reminder_time'], "HH:mm")
                if time.isValid():
                    self.time_selector.setTime(time)
        else:
            self.reminder_button.setText("启用提醒")
            self.reminder_button.setStyleSheet(
                "QPushButton { background-color: #81C784; color: white; border-radius: 4px; padding: 5px 10px; }"
                "QPushButton:hover { background-color: #66BB6A; }"
            )
    
    def load_tasks(self):
        """从数据库加载所有打卡任务"""
        self.task_items.clear()
        self.task_list.clear()
        
        tasks = self.storage.get_checkin_tasks()
        
        for task in tasks:
            emoji = task.get('emoji', '🍅')  # 获取emoji，如果没有则使用默认值
            self.add_task_to_list(task['id'], task['name'], task['streak_days'], task['checked_today'], emoji)
    
    def add_task_to_list(self, task_id, task_name, streak_days, checked_today=False, emoji="🍅"):
        """添加任务到列表显示"""
        # 创建任务项组件
        task_item = DailyTaskItem(task_id, task_name, streak_days, emoji=emoji)
        task_item.update_button_state(checked_today)
        task_item.checkin_button.clicked.connect(lambda: self.check_in_task(task_id))
        
        # 保存到字典中
        self.task_items[task_id] = task_item
        
        # 创建列表项并添加到列表
        list_item = QListWidgetItem()
        list_item.setSizeHint(task_item.sizeHint())
        list_item.setData(Qt.ItemDataRole.UserRole, task_id)
        
        self.task_list.addItem(list_item)
        self.task_list.setItemWidget(list_item, task_item)
    
    def add_task(self):
        """添加新任务"""
        task_name, ok, emoji = CustomInputDialog.getText(
            self, "添加任务", "请输入任务名称:", 
            default_text="新任务",
            show_emoji_selector=True
        )
        
        if ok and task_name.strip():
            task_id = self.storage.add_checkin_task(task_name.strip(), emoji)
            
            if task_id:
                self.add_task_to_list(task_id, task_name.strip(), 0, False, emoji)
                tooltip(f"已添加任务: {task_name}")
    
    def delete_task(self, task_id):
        """删除任务"""
        task_name = self.task_items[task_id].task_name
        confirm = QMessageBox.question(
            self, "删除任务", 
            f"确定要删除任务 \"{task_name}\" 吗？这将删除所有相关打卡记录。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            # 从数据库删除
            deleted = self.storage.delete_checkin_task(task_id)
            
            if deleted:
                # 从界面移除
                for i in range(self.task_list.count()):
                    item = self.task_list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == task_id:
                        self.task_list.takeItem(i)
                        break
                
                # 从字典中移除
                if task_id in self.task_items:
                    del self.task_items[task_id]
                
                # 清空日历
                if self.calendar.current_task_id == task_id:
                    self.calendar.set_task(None)
                    self.info_label.setText("")
                
                # 从状态栏显示配置中移除该任务
                config = get_config()
                displayed_tasks = config.get("statusbar_checkin_tasks", [])
                if task_id in displayed_tasks:
                    displayed_tasks.remove(task_id)
                    config["statusbar_checkin_tasks"] = displayed_tasks
                    
                    # 获取全局配置单例对象并更新
                    state = get_state()
                    state._config = config
                    save_config()
                    
                    # 更新状态栏显示
                    self.update_statusbar_display()
                
                tooltip(f"已删除任务: {task_name}")
    
    def rename_task(self, task_id):
        """重命名任务"""
        old_name = self.task_items[task_id].task_name
        old_emoji = self.task_items[task_id].emoji
        new_name, ok, new_emoji = CustomInputDialog.getText(
            self, "编辑任务", "请输入新的任务名称:", 
            default_text=old_name,
            show_emoji_selector=True
        )
        
        if ok and new_name.strip() and (new_name != old_name or new_emoji != old_emoji):
            # 更新数据库
            updated = self.storage.rename_checkin_task(task_id, new_name.strip(), new_emoji)
            
            if updated:
                # 更新界面显示
                self.task_items[task_id].name_label.setText(new_name.strip())
                self.task_items[task_id].task_name = new_name.strip()
                
                # 更新emoji
                if new_emoji != old_emoji:
                    self.task_items[task_id].emoji = new_emoji
                    self.task_items[task_id].emoji_button.setText(new_emoji)
                
                tooltip(f"已更新任务: {old_name} -> {new_name}")
    
    def check_in_task(self, task_id):
        """打卡任务"""
        # 更新数据库
        success, streak_days = self.storage.check_in_task(task_id)
        
        if success:
            # 更新界面
            task_item = self.task_items[task_id]
            task_item.update_button_state(True)
            task_item.update_streak(streak_days)
            
            # 如果当前选中的是这个任务，更新日历显示
            if self.calendar.current_task_id == task_id:
                self.update_calendar_for_task(task_id)
            
            # 更新状态栏显示
            self.update_statusbar_display()
            
            tooltip("打卡成功！")
    
    def cancel_checkin(self, task_id):
        """取消今日打卡"""
        confirm = QMessageBox.question(
            self, "取消打卡", 
            "确定要取消今日的打卡记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            # 更新数据库
            success, streak_days = self.storage.cancel_checkin(task_id)
            
            if success:
                # 更新界面
                task_item = self.task_items[task_id]
                task_item.update_button_state(False)
                task_item.update_streak(streak_days)
                
                # 更新日历
                if self.calendar.current_task_id == task_id:
                    self.update_calendar_for_task(task_id)
                
                # 更新状态栏显示
                self.update_statusbar_display()
                
                tooltip("已取消今日打卡")
    
    def show_task_context_menu(self, position):
        """显示任务的右键菜单"""
        item = self.task_list.itemAt(position)
        if not item:
            return
        
        task_id = item.data(Qt.ItemDataRole.UserRole)
        task_item = self.task_items.get(task_id)
        if not task_item:
            return
        
        # 创建菜单
        context_menu = QMenu(self)
        
        # 添加重命名选项
        rename_action = QAction("重命名任务", self)
        rename_action.triggered.connect(lambda: self.rename_task(task_id))
        context_menu.addAction(rename_action)
        
        # 添加取消今日打卡选项（如果已打卡）
        if task_item.checked_today:
            cancel_action = QAction("取消今日打卡", self)
            cancel_action.triggered.connect(lambda: self.cancel_checkin(task_id))
            context_menu.addAction(cancel_action)
        
        # 添加删除选项
        context_menu.addSeparator()
        delete_action = QAction("删除任务", self)
        delete_action.triggered.connect(lambda: self.delete_task(task_id))
        context_menu.addAction(delete_action)
        
        # 在鼠标位置显示
        context_menu.exec(QCursor.pos())
    
    def on_task_selected(self, row):
        """当选择任务时更新日历显示"""
        if row < 0:
            self.calendar.set_task(None)
            self.info_label.setText("")
            self.makeup_button.setEnabled(False)
            self.cancel_date_button.setEnabled(False)
            return
        
        item = self.task_list.item(row)
        if not item:
            return
        
        task_id = item.data(Qt.ItemDataRole.UserRole)
        self.update_calendar_for_task(task_id)
        
        # 根据选中日期是否已打卡来启用或禁用取消打卡按钮
        # 获取选中的日期
        selected_date = self.date_selector.currentData()
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 只有选择的不是今天，才启用补打卡按钮
        if selected_date == today:
            self.makeup_button.setEnabled(False)
        else:
            self.makeup_button.setEnabled(True)
            
        self.update_cancel_button_state()
    
    def update_calendar_for_task(self, task_id):
        """更新指定任务的日历显示"""
        # 获取任务的打卡记录
        task_info = self.storage.get_task_checkin_history(task_id)
        
        if not task_info:
            return
        
        # 设置日历任务
        self.calendar.set_task(task_id)
        
        # 更新日历数据
        self.calendar.set_check_data(task_info['check_history'])
        
        # 更新信息标签
        streak_days = task_info['streak_days']
        max_streak = task_info['max_streak']
        total_days = task_info['total_days']
        
        info_text = f"当前连续打卡: {streak_days}天   |   历史最长连续: {max_streak}天   |   总打卡次数: {total_days}天"
        self.info_label.setText(info_text)
    
    def makeup_checkin(self):
        """补打卡功能"""
        # 获取当前选中的任务
        current_item = self.task_list.currentItem()
        if not current_item:
            return
        
        task_id = current_item.data(Qt.ItemDataRole.UserRole)
        task_name = self.task_items[task_id].task_name
        
        # 获取选中的日期
        selected_date = self.date_selector.currentData()
        display_date = self.date_selector.currentText()
        
        # 确认是否要补打卡
        confirm = CustomConfirmDialog.confirm(
            self, "补打卡确认", 
            f"确定要为任务 \"{task_name}\" 补上 {display_date} 的打卡记录吗？",
            "question"
        )
        
        if confirm:
            # 调用补打卡方法
            success, streak_days = self.storage.makeup_checkin(task_id, selected_date)
            
            if success:
                # 更新任务连续天数显示
                self.task_items[task_id].update_streak(streak_days)
                
                # 更新日历显示
                self.update_calendar_for_task(task_id)
                
                # 更新状态栏显示
                self.update_statusbar_display()
                
                tooltip(f"已成功为 {display_date} 补打卡！")
            else:
                CustomConfirmDialog.confirm(
                    self, "补打卡失败", 
                    "该日期可能已经有打卡记录，或者补打卡失败。",
                    "warning"
                )
    
    def on_calendar_date_selected(self, date_str):
        """当从日历中选择日期时调用"""
        # 确保日期不是未来（只排除未来日期，允许选择今天）
        today = datetime.now().date().strftime("%Y-%m-%d")
        if date_str > today:
            return
        
        # 如果是今天，选择第一个选项（"今天"）
        if date_str == today:
            self.date_selector.setCurrentIndex(0)
            # 今天不能补打卡，禁用补打卡按钮
            self.makeup_button.setEnabled(False)
        else:
            # 对于过去的日期，查找匹配的索引
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            display_date = selected_date.strftime("%m-%d")
            
            # 查找匹配的索引
            for i in range(self.date_selector.count()):
                if self.date_selector.itemData(i) == date_str:
                    self.date_selector.setCurrentIndex(i)
                    break
            else:
                # 如果在选择器中找不到这个日期（超出15天范围），则更新选择器
                # 先清空原来的选项
                self.date_selector.clear()
                
                # 重新添加今天选项
                self.date_selector.addItem("今天", today)
                
                # 添加选中的日期
                self.date_selector.addItem(display_date, date_str)
                
                # 添加过去15天的其他日期
                today_date = datetime.now().date()
                for i in range(1, 16):
                    past_date = today_date - timedelta(days=i)
                    past_date_str = past_date.strftime("%Y-%m-%d")
                    
                    # 避免重复添加选中的日期
                    if past_date_str != date_str and past_date_str != today:
                        display_str = past_date.strftime("%m-%d")
                        self.date_selector.addItem(display_str, past_date_str)
                
                # 选择匹配的日期
                for i in range(self.date_selector.count()):
                    if self.date_selector.itemData(i) == date_str:
                        self.date_selector.setCurrentIndex(i)
                        break
            
            # 过去日期可以补打卡，启用补打卡按钮
            self.makeup_button.setEnabled(True)
        
        # 更新取消打卡按钮状态
        self.update_cancel_button_state()
    
    def update_cancel_button_state(self):
        """根据当前选中的日期是否已打卡来更新取消打卡按钮状态"""
        # 检查是否有选中的任务
        current_item = self.task_list.currentItem()
        if not current_item:
            self.cancel_date_button.setEnabled(False)
            self.makeup_button.setEnabled(False)
            return
        
        task_id = current_item.data(Qt.ItemDataRole.UserRole)
        
        # 获取选中的日期
        selected_date = self.date_selector.currentData()
        if not selected_date:
            self.cancel_date_button.setEnabled(False)
            return
        
        # 判断是否是今天的日期
        today = datetime.now().strftime("%Y-%m-%d")
        if selected_date == today:
            # 检查任务今天是否已打卡
            task_item = self.task_items.get(task_id)
            if task_item and task_item.checked_today:
                self.cancel_date_button.setEnabled(True)
            else:
                self.cancel_date_button.setEnabled(False)
            
            # 今天的打卡只能通过打卡按钮，禁用补打卡按钮
            self.makeup_button.setEnabled(False)
        else:
            # 对于过去的日期，启用补打卡按钮
            self.makeup_button.setEnabled(True)
            
            # 检查该日期是否已打卡
            if self.calendar.check_data.get(selected_date, False):
                self.cancel_date_button.setEnabled(True)
            else:
                self.cancel_date_button.setEnabled(False)
    
    def cancel_date_checkin(self):
        """取消指定日期的打卡"""
        # 获取当前选中的任务
        current_item = self.task_list.currentItem()
        if not current_item:
            return
        
        task_id = current_item.data(Qt.ItemDataRole.UserRole)
        task_name = self.task_items[task_id].task_name
        
        # 获取选中的日期
        selected_date = self.date_selector.currentData()
        display_date = self.date_selector.currentText()
        
        # 判断是否是今天的日期
        today = datetime.now().strftime("%Y-%m-%d")
        is_today = (selected_date == today)
        
        # 确认是否要取消打卡
        confirm = CustomConfirmDialog.confirm(
            self, "取消打卡确认", 
            f"确定要取消任务 \"{task_name}\" 在 {display_date if not is_today else '今天'} 的打卡记录吗？",
            "question"
        )
        
        if confirm:
            # 调用取消指定日期打卡方法
            success, streak_days = self.storage.cancel_date_checkin(task_id, selected_date)
            
            if success:
                # 更新任务连续天数显示
                self.task_items[task_id].update_streak(streak_days)
                
                # 如果是今天的打卡，更新打卡按钮状态
                if is_today:
                    task_item = self.task_items.get(task_id)
                    if task_item:
                        task_item.update_button_state(False)
                
                # 更新日历显示
                self.update_calendar_for_task(task_id)
                
                # 更新取消按钮状态
                self.update_cancel_button_state()
                
                # 更新状态栏显示
                self.update_statusbar_display()
                
                tooltip(f"已取消 {display_date if not is_today else '今天'} 的打卡记录！")
            else:
                CustomConfirmDialog.confirm(
                    self, "取消打卡失败", 
                    "该日期可能没有打卡记录，或者取消失败。",
                    "warning"
                )
    
    def update_statusbar_display(self):
        """更新左下角状态栏显示"""
        from aqt import mw
        
        # 方式1: 直接更新countdown_info_label
        if hasattr(mw, 'countdown_info_label'):
            try:
                mw.countdown_info_label.updateCountdownDisplay()
            except Exception as e:
                print(f"更新状态栏显示出错: {e}")
        
        # 方式2: 通过pomodoro_status_widget更新
        if hasattr(mw, 'pomodoro_status_widget'):
            try:
                if hasattr(mw.pomodoro_status_widget, 'info_label'):
                    mw.pomodoro_status_widget.info_label.updateCountdownDisplay()
                mw.pomodoro_status_widget.update_display()
            except Exception as e:
                print(f"更新pomodoro_status_widget出错: {e}")
        
        # 方式3: 使用statusbar.py中的get_status_widget函数
        try:
            from ..ui.statusbar import get_status_widget
            status_widget = get_status_widget()
            if status_widget:
                status_widget.update_display()
        except Exception as e:
            print(f"通过get_status_widget()更新状态栏出错: {e}")
        
        # 方式4: 刷新整个状态栏
        if hasattr(mw, 'statusBar'):
            try:
                mw.statusBar().update()
            except Exception as e:
                print(f"刷新状态栏出错: {e}")

    def on_tasks_reordered(self, parent, start, end, destination, row):
        """当任务被拖动重新排序后调用"""
        # 创建任务ID的新顺序列表
        new_order = []
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            task_id = item.data(Qt.ItemDataRole.UserRole)
            new_order.append(task_id)
        
        # 更新数据库中任务的顺序
        self.storage.update_tasks_order(new_order)
        
        # 实时更新状态栏显示
        self.update_statusbar_display()

    def goto_today(self):
        """切换到当天"""
        # 设置下拉框为今天
        self.date_selector.setCurrentIndex(0)
        
        # 将日历切换到当前月份
        today = datetime.now()
        
        # 如果当前显示的不是当月，切换到当月
        if self.calendar.current_date.year != today.year or self.calendar.current_date.month != today.month:
            self.calendar.current_date = today
            self.calendar.update_calendar()
        
        # 选中今天的日期
        today_str = today.date().strftime("%Y-%m-%d")
        self.calendar.selected_date = today_str
        self.calendar.update_calendar()
        
        # 更新取消按钮状态
        self.update_cancel_button_state()


class CustomInputDialog(QDialog):
    """自定义无边框输入对话框"""
    
    def __init__(self, parent=None, title="输入", label="请输入:", default_text="", show_emoji_selector=False):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(350, show_emoji_selector and 300 or 150)
        
        # 设置无边框模式
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 窗口拖动相关变量
        self.dragging = False
        self.drag_position = None
        
        # 结果值
        self.result_text = ""
        self.result_ok = False
        self.selected_emoji = "🍅" # 默认emoji
        
        self.init_ui(title, label, default_text, show_emoji_selector)
    
    def init_ui(self, title, label, default_text, show_emoji_selector):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 创建主容器
        main_widget = QWidget(self)
        main_widget.setObjectName("mainContainer")
        main_widget.setStyleSheet("""
            QWidget#mainContainer {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        # 创建阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 0)
        main_widget.setGraphicsEffect(shadow)
        
        # 主容器的布局
        container_layout = QVBoxLayout(main_widget)
        container_layout.setContentsMargins(15, 15, 15, 15)
        
        # 顶部标题和关闭按钮
        title_layout = QHBoxLayout()
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        close_btn = QPushButton("×")
        close_btn.setStyleSheet("""
            QPushButton {
                font-size: 18px;
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
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #e0e0e0;")
        container_layout.addWidget(separator)
        
        # Emoji选择器
        if show_emoji_selector:
            emoji_label = QLabel("选择图标:")
            emoji_label.setStyleSheet("font-size: 14px; margin-top: 10px;")
            container_layout.addWidget(emoji_label)
            
            # 创建滚动区域
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll_area.setStyleSheet("""
                QScrollArea {
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background-color: white;
                }
            """)
            
            # 创建一个容器用于放置emoji网格
            emoji_container = QWidget()
            
            # Emoji选择器区域
            emoji_layout = QGridLayout(emoji_container)
            emoji_layout.setSpacing(5)
            
            # 使用constants.py中的完整图标库
            emojis = AVAILABLE_STATUSBAR_ICONS
            
            row, col = 0, 0
            for emoji in emojis:
                btn = QPushButton(emoji)
                btn.setFixedSize(35, 35)
                btn.setStyleSheet("""
                    QPushButton {
                        font-size: 18px;
                        background-color: #f5f5f5;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #e3f2fd;
                        border: 1px solid #2196F3;
                    }
                """)
                # 连接点击事件
                btn.clicked.connect(lambda checked, e=emoji: self.select_emoji(e))
                emoji_layout.addWidget(btn, row, col)
                
                col += 1
                if col >= 6:  # 每行显示6个emoji
                    col = 0
                    row += 1
            
            # 设置滚动区域的内容
            scroll_area.setWidget(emoji_container)
            
            # 设置滚动区域的固定高度
            scroll_area.setFixedHeight(150)
            
            # 显示当前选中的emoji
            self.selected_emoji_label = QLabel()
            self.selected_emoji_label.setStyleSheet("font-size: 24px; margin: 10px 0;")
            self.selected_emoji_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.selected_emoji_label.setText(f"已选择: {self.selected_emoji}")
            
            container_layout.addWidget(scroll_area)
            container_layout.addWidget(self.selected_emoji_label)
            
            # 再添加一个分隔线
            separator2 = QFrame()
            separator2.setFrameShape(QFrame.Shape.HLine)
            separator2.setFrameShadow(QFrame.Shadow.Sunken)
            separator2.setStyleSheet("background-color: #e0e0e0;")
            container_layout.addWidget(separator2)
        
        # 输入框标签
        input_label = QLabel(label)
        input_label.setStyleSheet("font-size: 14px; margin-top: 10px;")
        container_layout.addWidget(input_label)
        
        # 输入框
        self.text_input = QLineEdit()
        self.text_input.setText(default_text)
        self.text_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #2196F3;
            }
        """)
        self.text_input.selectAll()  # 选中所有文本，方便直接输入
        container_layout.addWidget(self.text_input)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 取消按钮
        cancel_button = QPushButton("取消")
        cancel_button.setStyleSheet("""
            QPushButton {
            background-color: #f5f5f5;
                color: #333;
            border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px 15px;
            font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        # 确定按钮
        ok_button = QPushButton("确定")
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
            color: white;
            border-radius: 4px;
                padding: 5px 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)
        
        container_layout.addLayout(button_layout)
        
        # 添加容器到主布局
        main_layout.addWidget(main_widget)
        
        # 设置回车键确认
        self.text_input.returnPressed.connect(ok_button.click)
        
        # 设置初始焦点
        self.text_input.setFocus()
    
    def select_emoji(self, emoji):
        """选择emoji图标"""
        self.selected_emoji = emoji
        self.selected_emoji_label.setText(f"已选择: {emoji}")
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        self.dragging = False
        event.accept()
    
    def accept(self):
        """确定按钮点击时调用"""
        self.result_text = self.text_input.text()
        self.result_ok = True
        super().accept()
    
    def reject(self):
        """取消按钮点击时调用"""
        self.result_text = ""
        self.result_ok = False
        super().reject()
    
    @staticmethod
    def getText(parent=None, title="输入", label="请输入:", default_text="", show_emoji_selector=False):
        """静态方法，用于获取文本输入，类似于QInputDialog.getText"""
        dialog = CustomInputDialog(parent, title, label, default_text, show_emoji_selector)
        result = dialog.exec()
        
        return dialog.result_text, dialog.result_ok, dialog.selected_emoji


class CustomConfirmDialog(QDialog):
    """自定义无边框确认对话框"""
    
    def __init__(self, parent=None, title="确认", message="", icon_type="question"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(350, 180)
        
        # 设置无边框模式
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 窗口拖动相关变量
        self.dragging = False
        self.drag_position = None
        
        # 结果值
        self.result_ok = False
        
        self.init_ui(title, message, icon_type)
    
    def init_ui(self, title, message, icon_type):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 创建主容器
        main_widget = QWidget(self)
        main_widget.setObjectName("mainContainer")
        main_widget.setStyleSheet("""
            QWidget#mainContainer {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        # 创建阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 0)
        main_widget.setGraphicsEffect(shadow)
        
        # 主容器的布局
        container_layout = QVBoxLayout(main_widget)
        container_layout.setContentsMargins(15, 15, 15, 15)
        
        # 顶部标题和关闭按钮
        title_layout = QHBoxLayout()
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        close_btn = QPushButton("×")
        close_btn.setStyleSheet("""
            QPushButton {
                font-size: 18px;
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
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #e0e0e0;")
        container_layout.addWidget(separator)
        
        # 内容区域 - 图标和消息
        content_layout = QHBoxLayout()
        
        # 图标
        icon_label = QLabel()
        icon_size = 48
        
        # 根据类型设置图标
        if icon_type == "question":
            # 问号图标
            icon_label.setText("❓")
            icon_label.setStyleSheet("font-size: 36px; color: #2196F3; min-width: 48px;")
        elif icon_type == "warning":
            # 警告图标
            icon_label.setText("⚠️")
            icon_label.setStyleSheet("font-size: 36px; color: #FF9800; min-width: 48px;")
        elif icon_type == "error":
            # 错误图标
            icon_label.setText("❌")
            icon_label.setStyleSheet("font-size: 36px; color: #F44336; min-width: 48px;")
        elif icon_type == "info":
            # 信息图标
            icon_label.setText("ℹ️")
            icon_label.setStyleSheet("font-size: 36px; color: #2196F3; min-width: 48px;")
        
        content_layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignTop)
        content_layout.addSpacing(10)
        
        # 消息文本
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("font-size: 14px; color: #333; margin: 10px 0;")
        content_layout.addWidget(message_label, 1)
        
        container_layout.addLayout(content_layout)
        
        container_layout.addStretch(1)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 根据图标类型决定按钮布局
        if icon_type == "warning" or icon_type == "error" or icon_type == "info":
            # 警告/错误/信息对话框只显示一个"确定"按钮
            ok_button = QPushButton("确定")
            ok_button.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border-radius: 4px;
                    padding: 5px 15px;
                    font-size: 14px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
            ok_button.clicked.connect(self.accept)
            button_layout.addWidget(ok_button)
        else:
            # 问题确认对话框显示"是"和"否"两个按钮
            no_button = QPushButton("否(N)")
            no_button.setStyleSheet("""
                QPushButton {
                    background-color: #f5f5f5;
                    color: #333;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 5px 15px;
                    font-size: 14px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """)
            no_button.clicked.connect(self.reject)
            button_layout.addWidget(no_button)
            
            # 是按钮
            yes_button = QPushButton("确定(Y)")
            yes_button.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border-radius: 4px;
                    padding: 5px 15px;
                    font-size: 14px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
            yes_button.clicked.connect(self.accept)
            button_layout.addWidget(yes_button)
        
        container_layout.addLayout(button_layout)
        
        # 添加容器到主布局
        main_layout.addWidget(main_widget)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        self.dragging = False
        event.accept()
    
    def accept(self):
        """确定按钮点击时调用"""
        self.result_ok = True
        super().accept()
    
    def reject(self):
        """取消按钮点击时调用"""
        self.result_ok = False
        super().reject()
    
    @staticmethod
    def confirm(parent=None, title="确认", message="", icon_type="question"):
        """静态方法，用于显示确认对话框"""
        dialog = CustomConfirmDialog(parent, title, message, icon_type)
        result = dialog.exec()
        
        return dialog.result_ok


def show_checkin_dialog(parent=None):
    """显示打卡对话框"""
    dialog = CheckinDialog(parent)
    dialog.exec() 