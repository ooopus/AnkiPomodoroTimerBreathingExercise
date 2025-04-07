"""
轻量级图表组件模块 - 使用纯PyQt实现，无需额外依赖
"""
from typing import List, Dict, Tuple, Optional, Union
from PyQt6.QtCore import Qt, QRect, QRectF, QSize, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QFont
from PyQt6.QtWidgets import QWidget, QSizePolicy
import math


def format_time_seconds(seconds: int) -> str:
    """格式化秒数为时:分:秒格式"""
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"


class BarChart(QWidget):
    """简单的柱状图组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(150)
        
        # 数据
        self._labels: List[str] = []
        self._values: List[float] = []
        self._colors: List[QColor] = []
        
        # 标题和轴标签
        self._title: str = ""
        self._x_label: str = ""
        self._y_label: str = ""
        
        # 颜色设置
        self._default_color = QColor("#4CAF50")  # 默认深绿色
        self._grid_color = QColor(200, 200, 200)
        self._text_color = QColor(80, 80, 80)
        
        # 网格和边距设置
        self._show_grid = True
        self._margin_left = 50
        self._margin_right = 20
        self._margin_top = 40
        self._margin_bottom = 50
        self._bar_padding = 0.2  # 条形间的间距比例
    
    def setData(self, labels: List[str], values: List[float], colors: Optional[List[QColor]] = None):
        """设置图表数据"""
        if len(labels) != len(values):
            raise ValueError("标签和数值列表长度必须相同")
        
        self._labels = labels
        self._values = values
        
        if colors and len(colors) == len(values):
            self._colors = colors
        else:
            # 生成默认颜色
            self._colors = [self._default_color] * len(values)
        
        self.update()  # 触发重绘
    
    def setTitle(self, title: str):
        """设置图表标题"""
        self._title = title
        self.update()
    
    def title(self) -> str:
        """获取图表标题"""
        return self._title
    
    def getData(self) -> Tuple[List[str], List[float], List[QColor]]:
        """获取图表数据，用于导出"""
        return self._labels, self._values, self._colors
    
    def setAxisLabels(self, x_label: str, y_label: str):
        """设置坐标轴标签"""
        self._x_label = x_label
        self._y_label = y_label
        self.update()
    
    def paintEvent(self, event):
        """绘制图表"""
        if not self._values:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 获取绘图区域
        width = self.width()
        height = self.height()
        chart_rect = QRect(
            self._margin_left, 
            self._margin_top, 
            width - self._margin_left - self._margin_right,
            height - self._margin_top - self._margin_bottom
        )
        
        # 绘制标题
        if self._title:
            painter.setPen(self._text_color)
            font = painter.font()
            font.setPointSize(10)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(
                QRect(0, 5, width, int(self._margin_top - 5)),
                Qt.AlignmentFlag.AlignCenter,
                self._title
            )
        
        # 找到最大值确定Y轴范围
        max_value = max(self._values) if self._values else 0
        if max_value == 0:
            max_value = 1  # 避免除以零错误
        
        # 绘制Y轴网格线和标签
        painter.setPen(QPen(self._grid_color, 1, Qt.PenStyle.DashLine))
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        
        y_step = max(1, max_value / 5)  # 分成5个等份
        for i in range(6):  # 0到5
            y_value = i * y_step
            y_pos = chart_rect.bottom() - (y_value / max_value) * chart_rect.height()
            
            # 绘制水平网格线
            if self._show_grid and i > 0:
                painter.drawLine(int(chart_rect.left()), int(y_pos), int(chart_rect.right()), int(y_pos))
            
            # 绘制Y轴标签
            painter.setPen(self._text_color)
            value_text = f"{y_value:.1f}" if y_value < 10 else f"{int(y_value)}"
            painter.drawText(
                QRect(0, int(y_pos - 10), int(self._margin_left - 5), 20),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                value_text
            )
            
            # 恢复网格线画笔
            painter.setPen(QPen(self._grid_color, 1, Qt.PenStyle.DashLine))
        
        # 绘制X轴和Y轴
        painter.setPen(QPen(self._text_color, 1, Qt.PenStyle.SolidLine))
        painter.drawLine(int(chart_rect.left()), int(chart_rect.top()), int(chart_rect.left()), int(chart_rect.bottom()))
        painter.drawLine(int(chart_rect.left()), int(chart_rect.bottom()), int(chart_rect.right()), int(chart_rect.bottom()))
        
        # 绘制Y轴标签
        if self._y_label:
            painter.save()
            painter.translate(int(5), int(height / 2))
            painter.rotate(-90)
            font = painter.font()
            font.setPointSize(9)
            painter.setFont(font)
            painter.drawText(
                QRect(-100, 0, 200, 20),
                Qt.AlignmentFlag.AlignCenter,
                self._y_label
            )
            painter.restore()
        
        # 绘制X轴标签
        if self._x_label:
            font = painter.font()
            font.setPointSize(9)
            painter.setFont(font)
            painter.drawText(
                QRect(int(width / 2 - 100), height - 20, 200, 20),
                Qt.AlignmentFlag.AlignCenter,
                self._x_label
            )
        
        # 绘制条形
        bar_count = len(self._values)
        if bar_count == 0:
            return
        
        # 计算条形宽度和间距
        total_bar_width = chart_rect.width() / bar_count
        bar_width = total_bar_width * (1 - self._bar_padding)
        bar_spacing = total_bar_width * self._bar_padding / 2
        
        for i, (label, value) in enumerate(zip(self._labels, self._values)):
            # 计算条形位置
            bar_left = chart_rect.left() + i * total_bar_width + bar_spacing
            
            # 如果值为0，不绘制
            if value == 0:
                continue
            
            # 计算条形高度
            bar_height = (value / max_value) * chart_rect.height()
            
            # 绘制条形
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(self._colors[i]))
            
            # 条形位置和大小
            bar_rect = QRectF(
                int(bar_left),
                int(chart_rect.bottom() - bar_height),
                int(bar_width),
                int(bar_height)
            )
            
            painter.drawRect(bar_rect)
            
            # 在条形顶部绘制数值
            color = self._colors[i]
            luminance = (0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()) / 255
            text_color = QColor(Qt.GlobalColor.white) if luminance < 0.5 else QColor(Qt.GlobalColor.black)
            painter.setPen(text_color)
            font = painter.font()
            font.setPointSize(9)
            font.setBold(True)
            painter.setFont(font)
            
            # 格式化数值显示
            value_text = f"{value:.1f}"
            
            # 判断图表类型，决定显示格式
            if "时长" in self._title or "小时" in self._x_label or "小时" in self._y_label:
                # 转换为小时格式
                if "每小时" in self._title:
                    # 对于"每小时学习时长分布"，保持原值
                    value_text = f"{value:.1f}"
                else:
                    # 将分钟转为小时
                    hours = value / 60
                    value_text = f"{hours:.1f}h"
            
            # 绘制值文本
            value_rect = QRect(
                int(bar_left),
                int(chart_rect.bottom() - bar_height / 2 - 10),  # 位于条形内部中间位置
                int(bar_width),
                20
            )
            
            painter.drawText(
                value_rect,
                Qt.AlignmentFlag.AlignCenter,
                value_text
            )
            
            # 绘制X轴标签
            painter.setPen(self._text_color)
            label_rect = QRect(
                int(bar_left - bar_spacing),
                int(chart_rect.bottom() + 5),
                int(total_bar_width),
                int(self._margin_bottom - 5)
            )
            
            # 如果标签过长，旋转45度显示
            if bar_width < 40:  # 如果条形较窄
                painter.save()
                painter.translate(int(bar_left + bar_width / 2), int(chart_rect.bottom() + 5))
                painter.rotate(45)
                font = painter.font()
                font.setPointSize(8)
                painter.setFont(font)
                painter.drawText(
                    QRect(0, 0, 100, 20),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                    label
                )
                painter.restore()
            else:
                font = painter.font()
                font.setPointSize(8)
                painter.setFont(font)
                painter.drawText(
                    label_rect,
                    Qt.AlignmentFlag.AlignCenter,
                    label
                )
        
        painter.end()


class PieChart(QWidget):
    """简单的饼图组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(150)
        
        # 数据
        self._labels: List[str] = []
        self._values: List[float] = []
        self._colors: List[QColor] = []
        
        # 标题
        self._title: str = ""
        
        # 颜色设置
        self._default_colors = [
            QColor("#4CAF50"),  # 绿色
            QColor("#F44336"),  # 红色
            QColor("#2196F3"),  # 蓝色
            QColor("#FFC107"),  # 黄色
            QColor("#9C27B0"),  # 紫色
            QColor("#FF9800"),  # 橙色
            QColor("#795548"),  # 棕色
            QColor("#607D8B")   # 蓝灰色
        ]
        self._text_color = QColor(80, 80, 80)
        
        # 布局设置
        self._margin = 20
        self._legend_width = 750  # 增加图例宽度从600到750
        self._show_legend = True
        self._show_percentages = True
        self._legend_row_height = 30
        self.setMinimumSize(1200, 200)  # 增加最小宽度从1000到1200
    
    def setData(self, labels: List[str], values: List[float], colors: Optional[List[QColor]] = None):
        """设置图表数据"""
        if len(labels) != len(values):
            raise ValueError("标签和数值列表长度必须相同")
        
        self._labels = labels
        self._values = values
        
        if colors and len(colors) == len(values):
            self._colors = colors
        else:
            # 生成默认颜色，确保颜色数量足够
            self._colors = []
            for i in range(len(values)):
                self._colors.append(self._default_colors[i % len(self._default_colors)])
        
        self.update()  # 触发重绘
    
    def setTitle(self, title: str):
        """设置图表标题"""
        self._title = title
        self.update()
    
    def title(self) -> str:
        """获取图表标题"""
        return self._title
    
    def getData(self) -> Tuple[List[str], List[float], List[QColor]]:
        """获取图表数据，用于导出"""
        return self._labels, self._values, self._colors
    
    def showLegend(self, show: bool):
        """设置是否显示图例"""
        self._show_legend = show
        self.update()
    
    def showPercentages(self, show: bool):
        """设置是否显示百分比标签"""
        self._show_percentages = show
        self.update()
    
    def paintEvent(self, event):
        """绘制图表"""
        if not self._values:
            # 如果没有数据，显示"无数据"文本
            painter = QPainter(self)
            painter.setPen(self._text_color)
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "无数据可显示"
            )
            painter.end()
            return
        
        # 计算总和
        total = sum(self._values)
        if total <= 0:
            # 如果总和为0，显示"无数据"文本
            painter = QPainter(self)
            painter.setPen(self._text_color)
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "无有效数据可显示"
            )
            painter.end()
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 获取绘图区域
        width = self.width()
        height = self.height()
        
        # 计算饼图半径和中心位置
        legend_space = self._legend_width if self._show_legend else 0
        pie_size = min(width - self._margin * 2 - legend_space, height - self._margin * 2)
        
        # 如果空间不足，不显示图例
        if pie_size < 100 and self._show_legend:
            legend_space = 0
            self._show_legend = False
            pie_size = min(width - self._margin * 2, height - self._margin * 2)
        
        pie_rect = QRect(
            self._margin,
            (height - pie_size) // 2,
            pie_size,
            pie_size
        )
        
        # 如果标题存在，向下移动饼图位置
        if self._title:
            painter.setPen(self._text_color)
            font = painter.font()
            font.setPointSize(10)
            font.setBold(True)
            painter.setFont(font)
            
            # 仅绘制标题，不添加单位
            title_text = self._title
            # 确保番茄钟完成情况图表不显示"小时"单位
            painter.drawText(
                QRect(0, 5, width, 30),
                Qt.AlignmentFlag.AlignCenter,
                title_text
            )
            
            # 调整饼图位置
            pie_rect.moveTop(pie_rect.top() + 20)
        
        # 绘制饼图扇区
        start_angle = 0
        sector_data = []  # 存储扇区角度数据，用于后续绘制文本

        for i, value in enumerate(self._values):
            # 计算该扇区的角度 (16分之1度为单位)
            sweep_angle = int(360 * 16 * value / total)
            
            # 绘制扇区
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(self._colors[i]))
            painter.drawPie(pie_rect, start_angle, sweep_angle)
            
            # 保存扇区数据
            sector_data.append({
                "start_angle": start_angle / 16,  # 转换回度
                "sweep_angle": sweep_angle / 16,  # 转换回度
                "value": value,
                "color": self._colors[i]
            })
            
            # 计算下一个扇区的起始角度
            start_angle += sweep_angle
        
        # 在每个扇区上绘制时间标签
        for i, sector in enumerate(sector_data):
            # 计算扇区中心角度（弧度）
            center_angle_deg = sector["start_angle"] + sector["sweep_angle"] / 2
            center_angle = math.radians(center_angle_deg)
            
            # 计算标签位置（在扇区中心位置)
            radius = min(pie_rect.width(), pie_rect.height()) / 2 * 0.7  # 使用70%半径位置
            tx = pie_rect.center().x() + radius * math.cos(center_angle)
            ty = pie_rect.center().y() - radius * math.sin(center_angle)  # 注意Y轴是向下的
            
            # 设置文本颜色为白色或黑色 (取决于背景色)
            color = sector["color"]
            luminance = (0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()) / 255
            text_color = QColor(Qt.GlobalColor.white) if luminance < 0.5 else QColor(Qt.GlobalColor.black)
            
            # 格式化时间数值
            # 判断图表类型，决定如何格式化数值
            if "牌组使用时长" in self._title or "牌组学习时长" in self._title or "时长" in self._title:
                # 将分钟转为小时
                hours = sector["value"] / 60
                if hours >= 1:
                    time_text = f"{hours:.1f}h"
                else:
                    time_text = f"{hours:.1f}h"
            elif self._title == "番茄钟完成情况":
                # 直接显示番茄数量
                count = int(sector["value"])
                time_text = f"{count}次"
            else:
                # 默认以小时为单位显示
                hours = sector["value"]
                time_text = f"{hours:.1f}h"
            
            # 绘制时间文本
            painter.setPen(text_color)
            font = painter.font()
            font.setBold(True)
            font.setPointSize(9)
            painter.setFont(font)
            
            # 创建文本矩形并绘制
            text_rect = QRect(int(tx - 40), int(ty - 10), 80, 20)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, time_text)
        
        # 绘制图例
        if self._show_legend:
            # 计算图例位置
            legend_x = pie_rect.right() + 20
            legend_y = pie_rect.top() + 10
            
            # 设置图例字体
            font = painter.font()
            font.setPointSize(9)
            painter.setFont(font)
            
            for i, (label, value) in enumerate(zip(self._labels, self._values)):
                # 计算百分比
                percentage = value / total * 100
                
                # 绘制颜色框
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(self._colors[i]))
                painter.drawRect(QRect(int(legend_x), int(legend_y + i * self._legend_row_height), 15, 15))
                
                # 绘制标签文本
                painter.setPen(self._text_color)
                # 根据图表类型决定显示的内容
                if self._title == "番茄钟完成情况":
                    # 显示具体次数
                    text = f"{label}: {int(value)}次 ({percentage:.1f}%)"
                elif "牌组使用时长" in self._title or "牌组学习时长" in self._title or "时长" in self._title:
                    # 显示具体时间（小时）
                    hours = value / 60  # 分钟转小时
                    text = f"{label}: {hours:.1f}h ({percentage:.1f}%)"
                else:
                    # 默认以小时为单位显示
                    hours = value
                    text = f"{label}: {hours:.1f}h ({percentage:.1f}%)"
                
                painter.drawText(
                    QRect(int(legend_x + 20), int(legend_y + i * self._legend_row_height), 730, 20),  # 增加文本区域宽度从580到730
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    text
                )
        
        # 如果没有图例但需要显示百分比，直接在饼图上绘制
        elif self._show_percentages:
            center = pie_rect.center()
            radius = pie_size / 2
            
            # 累计角度
            current_angle = 0
            
            for i, value in enumerate(self._values):
                # 计算该扇区的角度和百分比
                angle = 360 * value / total
                percentage = value / total * 100
                
                # 计算并绘制标签
                center_angle = current_angle + angle / 2
                radius = min(pie_rect.width(), pie_rect.height()) / 2 - 10
                tx = pie_rect.center().x() + radius * 0.7 * math.cos(math.radians(center_angle))
                ty = pie_rect.center().y() - radius * 0.7 * math.sin(math.radians(center_angle))
                
                # 设置文本颜色为白色或黑色 (取决于背景色)
                color = self._colors[i]
                luminance = (0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()) / 255
                text_color = QColor(Qt.GlobalColor.white) if luminance < 0.5 else QColor(Qt.GlobalColor.black)
                
                # 绘制百分比文本
                painter.setPen(text_color)
                font = painter.font()
                font.setBold(True)
                painter.setFont(font)
                
                text = f"{percentage:.1f}%"
                text_rect = QRect(int(tx - 40), int(ty - 10), 80, 20)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)
                
                current_angle += angle
        
        painter.end()


def create_color_list(count: int) -> List[QColor]:
    """创建一个颜色列表，确保不同的颜色"""
    base_colors = [
        QColor("#4CAF50"),  # 绿色
        QColor("#F44336"),  # 红色
        QColor("#2196F3"),  # 蓝色
        QColor("#FFC107"),  # 黄色
        QColor("#9C27B0"),  # 紫色
        QColor("#FF9800"),  # 橙色
        QColor("#795548"),  # 棕色
        QColor("#607D8B")   # 蓝灰色
    ]
    
    # 如果需要的颜色多于基础颜色，则循环使用
    colors = []
    for i in range(count):
        colors.append(base_colors[i % len(base_colors)])
    
    return colors


class HorizontalBarChart(QWidget):
    """
    横道图组件，用于显示牌组层级时长统计
    支持按牌组层级折叠显示
    完整显示牌组层级结构，包括无数据的上级和下级牌组
    每个层级显示它本身的时长加上所有下级牌组的时长汇总
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(200)
        
        # 数据
        self._deck_data = []  # 包含层级结构的牌组数据
        self._complete_deck_tree = {}  # 完整的牌组层级树，包括无数据的牌组
        self._total_durations = {}  # 每个牌组ID的总时长(包括下级牌组)
        self._expanded_decks = set()  # 当前展开的牌组ID集合
        self._visible_decks = []  # 当前可见的牌组列表
        
        # 标题
        self._title = ""
        
        # 颜色设置
        self._study_color = QColor("#4CAF50")  # 学习时间颜色(绿色)
        self._text_color = QColor(80, 80, 80)
        self._grid_color = QColor(230, 230, 230)
        
        # 布局设置
        self._margin_left = 195  # 将左侧边距从390再减少一半
        self._margin_right = 60
        self._margin_top = 40
        self._margin_bottom = 30
        self._row_height = 20  # 将行高从27减少到20
        self._row_padding = 1  # 将行间距从3减少到1
        
        # 互动设置
        self.setMouseTracking(True)
        
    def setData(self, deck_data, rest_times=None):
        """设置图表数据
        
        Args:
            deck_data: 包含牌组层级结构的数据，格式为:
                [
                    {
                        "deck_id": "1",
                        "deck_name": "父牌组",
                        "parent_deck_id": None,
                        "parent_deck_name": None,
                        "duration": 3600  # 秒
                    },
                    {
                        "deck_id": "2",
                        "deck_name": "子牌组",
                        "parent_deck_id": "1",
                        "parent_deck_name": "父牌组",
                        "duration": 1800  # 秒
                    }
                ]
            rest_times: 每个牌组的休息时间，格式为 {"deck_id": rest_time_in_seconds}
                        (注：休息时间不再显示，但保留参数以兼容现有代码)
        """
        print(f"HorizontalBarChart.setData: 接收到 {len(deck_data) if deck_data else 0} 条牌组数据")
        
        # 确保deck_data是列表
        if deck_data is None:
            deck_data = []
        
        self._deck_data = deck_data
        
        # 构建完整的牌组层级结构(包括没有番茄数据的上下级牌组)
        self._buildCompleteDeckTree()
        
        # 计算每个牌组的总时长(包括下级牌组)
        self._calculateTotalDurations()
        
        # 初始状态下，只有有数据的牌组所在层级展开
        self._expanded_decks = set()
        for deck in self._deck_data:
            deck_id = deck.get("deck_id")
            if deck_id and deck.get("duration", 0) > 0:
                # 将其所有父牌组都展开
                current_parent_id = deck.get("parent_deck_id")
                while current_parent_id:
                    self._expanded_decks.add(current_parent_id)
                    # 查找父牌组的父牌组ID
                    for parent_deck in self._deck_data:
                        if parent_deck.get("deck_id") == current_parent_id:
                            current_parent_id = parent_deck.get("parent_deck_id")
                            break
                    else:
                        # 在完整层级结构中查找父牌组
                        if current_parent_id in self._complete_deck_tree:
                            parent_deck = self._complete_deck_tree[current_parent_id].get("deck", {})
                            current_parent_id = parent_deck.get("parent_deck_id")
                        else:
                            current_parent_id = None
        
        # 根据牌组名称长度调整左侧边距
        max_name_length = 0
        for deck_id, deck_info in self._complete_deck_tree.items():
            deck = deck_info.get("deck", {})
            name_length = len(deck.get("deck_name", ""))
            max_name_length = max(max_name_length, name_length)
        
        # 每个字符估计8像素宽度，加上基础宽度和缩进
        name_width = max_name_length * 4 + 25 + 20  # 每个字符宽度减半，基础宽度和缩进空间也减半
        base_width = max(190, name_width)  # 确保最小宽度，从380减少到190
        self._margin_left = base_width  # 不再使用固定值，直接使用计算出的宽度
        
        self._updateVisibleDecks()
        self.update()
        print(f"HorizontalBarChart.setData: 更新完毕，可见牌组数量: {len(self._visible_decks)}, 左侧边距: {self._margin_left}")
    
    def _calculateTotalDurations(self):
        """计算每个牌组的总时长(包括下级牌组)"""
        self._total_durations = {}
        
        # 初始化每个牌组的自身时长
        for deck_id, deck_info in self._complete_deck_tree.items():
            deck = deck_info.get("deck", {})
            self._total_durations[deck_id] = deck.get("duration", 0)
        
        # 从叶子节点向上计算累计时长
        def has_children(deck_id):
            return len(self._complete_deck_tree.get(deck_id, {}).get("children", {})) > 0
        
        # 找出所有叶子节点(没有子牌组的牌组)
        leaf_nodes = [deck_id for deck_id in self._complete_deck_tree if not has_children(deck_id)]
        
        # 从叶子节点开始，向上传递时长
        processed = set()
        
        def process_node(deck_id):
            if deck_id in processed:
                return
                
            # 获取牌组信息
            deck_info = self._complete_deck_tree.get(deck_id, {})
            deck = deck_info.get("deck", {})
            parent_id = deck.get("parent_deck_id")
            
            # 确保所有子节点已经处理过
            children = deck_info.get("children", {})
            for child_id in children:
                if child_id not in processed:
                    process_node(child_id)
            
            # 添加所有子节点的时长
            total_duration = self._total_durations.get(deck_id, 0)
            for child_id in children:
                total_duration += self._total_durations.get(child_id, 0)
            
            # 更新总时长
            self._total_durations[deck_id] = total_duration
            
            # 标记为已处理
            processed.add(deck_id)
            
            # 向上传递给父节点
            if parent_id and parent_id in self._complete_deck_tree and parent_id not in processed:
                parent_self_duration = self._complete_deck_tree[parent_id].get("deck", {}).get("duration", 0)
                self._total_durations[parent_id] = parent_self_duration
                # 注意：不在这里累加子节点时长，而是在父节点处理时统一处理
        
        # 处理所有牌组
        for deck_id in self._complete_deck_tree:
            if deck_id not in processed:
                process_node(deck_id)
        
        # 输出总时长信息，用于调试
        print(f"计算了 {len(self._total_durations)} 个牌组的总时长:")
        for deck_id, total_duration in self._total_durations.items():
            deck_name = self._complete_deck_tree.get(deck_id, {}).get("deck", {}).get("deck_name", "未知牌组")
            print(f"牌组: {deck_name} (ID: {deck_id}), 总时长: {total_duration} 秒")
    
    def _buildCompleteDeckTree(self):
        """构建完整的牌组层级树，包括无数据的上层和下层牌组"""
        self._complete_deck_tree = {}
        processed_parents = set()  # 已处理过的父牌组ID集合，避免重复处理
        
        # 先将有数据的牌组添加到树中
        for deck in self._deck_data:
            deck_id = deck.get("deck_id")
            if not deck_id:
                continue
                
            if deck_id not in self._complete_deck_tree:
                self._complete_deck_tree[deck_id] = {"deck": deck, "children": {}}
                
            # 如果有父牌组，确保父牌组存在于树中
            parent_id = deck.get("parent_deck_id")
            if parent_id:
                if parent_id not in self._complete_deck_tree:
                    # 创建父牌组占位符
                    self._complete_deck_tree[parent_id] = {
                        "deck": {
                            "deck_id": parent_id,
                            "deck_name": deck.get("parent_deck_name", "未知牌组"),
                            "parent_deck_id": None,  # 临时设为None，后续会更新
                            "parent_deck_name": None,
                            "duration": 0  # 无数据
                        },
                        "children": {}
                    }
                
                # 将当前牌组添加为父牌组的子牌组，避免重复添加
                if deck_id not in self._complete_deck_tree[parent_id]["children"]:
                    self._complete_deck_tree[parent_id]["children"][deck_id] = self._complete_deck_tree[deck_id]
        
        # 构建完整的牌组层级结构：向上查找直到顶级牌组
        added_parents = True
        while added_parents:
            added_parents = False
            deck_ids = list(self._complete_deck_tree.keys())  # 创建副本以避免在迭代中修改字典
            
            for deck_id in deck_ids:
                if deck_id in processed_parents:
                    continue  # 已处理过的父牌组，跳过
                    
                deck_info = self._complete_deck_tree[deck_id]
                deck = deck_info.get("deck", {})
                parent_id = deck.get("parent_deck_id")
                
                if parent_id and parent_id not in self._complete_deck_tree:
                    # 从Anki获取父牌组信息
                    from aqt import mw
                    all_decks = mw.col.decks.all_names_and_ids()
                    parent_name = None
                    grand_parent_id = None
                    
                    for deck_info in all_decks:
                        try:
                            if hasattr(deck_info, 'id') and str(deck_info.id) == parent_id:
                                parent_name = deck_info.name
                                # 尝试获取父牌组的父牌组
                                if "::" in parent_name:
                                    grand_parent_name = "::".join(parent_name.split("::")[:-1])
                                    for d in all_decks:
                                        if hasattr(d, 'name') and d.name == grand_parent_name:
                                            grand_parent_id = str(d.id)
                                            break
                                    else:
                                        grand_parent_id = None
                                else:
                                    grand_parent_id = None
                                break
                        except Exception as e:
                            print(f"获取牌组信息错误: {str(e)}")
                    
                    # 创建父牌组节点
                    self._complete_deck_tree[parent_id] = {
                        "deck": {
                            "deck_id": parent_id,
                            "deck_name": parent_name or deck.get("parent_deck_name", "未知牌组"),
                            "parent_deck_id": grand_parent_id,
                            "parent_deck_name": grand_parent_name if grand_parent_id else None,
                            "duration": 0  # 无数据
                        },
                        "children": {}
                    }
                    # 确保子牌组在父牌组的children中
                    if deck_id not in self._complete_deck_tree[parent_id]["children"]:
                        self._complete_deck_tree[parent_id]["children"][deck_id] = self._complete_deck_tree[deck_id]
                    
                    added_parents = True
                    processed_parents.add(parent_id)  # 标记为已处理
                    
                    # 如果找到了父牌组的父牌组，将其加入待处理列表
                    if grand_parent_id and grand_parent_id not in self._complete_deck_tree:
                        self._complete_deck_tree[grand_parent_id] = {
                            "deck": {
                                "deck_id": grand_parent_id,
                                "deck_name": grand_parent_name,
                                "parent_deck_id": None,  # 暂时未知，下一轮会处理
                                "parent_deck_name": None,
                                "duration": 0  # 无数据
                            },
                            "children": {}
                        }
                        # 父牌组成为其父牌组的子牌组
                        if parent_id not in self._complete_deck_tree[grand_parent_id]["children"]:
                            self._complete_deck_tree[grand_parent_id]["children"][parent_id] = self._complete_deck_tree[parent_id]
                
                # 处理子牌组关系
                if parent_id and parent_id in self._complete_deck_tree:
                    # 确保当前牌组是其父牌组的子牌组
                    parent_info = self._complete_deck_tree[parent_id]
                    if deck_id not in parent_info["children"]:
                        parent_info["children"][deck_id] = deck_info
                
                processed_parents.add(deck_id)  # 标记当前牌组为已处理
        
        # 最后检查，确保每个牌组只出现在一个层级
        self._cleanup_tree_structure()
        
        # 输出构建的牌组层级结构，用于调试
        print(f"_buildCompleteDeckTree: 构建了 {len(self._complete_deck_tree)} 个牌组的完整层级结构")
        for deck_id, deck_info in self._complete_deck_tree.items():
            deck = deck_info.get("deck", {})
            children_count = len(deck_info.get("children", {}))
            print(f"牌组: {deck.get('deck_name')} (ID: {deck_id}), 父牌组: {deck.get('parent_deck_name')} (ID: {deck.get('parent_deck_id')}), 子牌组数: {children_count}")
    
    def _cleanup_tree_structure(self):
        """清理树结构，确保没有重复的层级"""
        # 构建一个从子牌组ID到父牌组ID的映射
        child_to_parent = {}
        for parent_id, parent_info in self._complete_deck_tree.items():
            for child_id in parent_info.get("children", {}):
                child_to_parent[child_id] = parent_id
        
        # 确保每个牌组只在树中出现一次
        for deck_id in list(self._complete_deck_tree.keys()):
            # 跳过顶级牌组
            if deck_id not in child_to_parent:
                continue
                
            # 确保牌组只在其直接父牌组下显示
            parent_id = child_to_parent.get(deck_id)
            if parent_id:
                # 检查并删除任何不是直接父牌组的关系
                for other_parent_id, other_parent_info in self._complete_deck_tree.items():
                    if other_parent_id != parent_id and deck_id in other_parent_info.get("children", {}):
                        print(f"修复重复层级: 从牌组 {other_parent_id} 中移除子牌组 {deck_id}")
                        del other_parent_info["children"][deck_id]
    
    def setTitle(self, title):
        """设置图表标题"""
        self._title = title
        self.update()
    
    def title(self) -> str:
        """获取图表标题"""
        return self._title
    
    def getData(self) -> Tuple[List[Dict], List[float]]:
        """获取图表数据，用于导出"""
        data = []
        values = []
        for i, deck in enumerate(self._visible_decks):
            if i < len(self._values):
                deck_name = deck["pretty_name"] if "pretty_name" in deck else deck.get("name", f"牌组{i+1}")
                data.append({"name": deck_name, "id": deck.get("id", "")})
                values.append(self._values[i])
        return data, values
    
    def _updateVisibleDecks(self):
        """更新当前可见的牌组列表"""
        print(f"_updateVisibleDecks: 开始更新可见牌组，当前有 {len(self._complete_deck_tree)} 条牌组数据")
        self._visible_decks = []
        
        if not self._complete_deck_tree:
            print("_updateVisibleDecks: 没有牌组数据，可见牌组列表为空")
            return
        
        # 找出所有顶级牌组（没有父牌组的牌组）
        top_level_decks = {}
        for deck_id, deck_info in self._complete_deck_tree.items():
            deck = deck_info.get("deck", {})
            parent_id = deck.get("parent_deck_id")
            
            if not parent_id or parent_id not in self._complete_deck_tree:
                top_level_decks[deck_id] = deck_info
        
        print(f"_updateVisibleDecks: 找到 {len(top_level_decks)} 个顶级牌组")
        
        # 使用集合来跟踪已添加的牌组，避免重复
        added_deck_ids = set()
        
        # 递归构建可见牌组列表，保持正确的层级信息
        def add_visible_decks(deck_info, current_path=None):
            if not deck_info or not deck_info.get("deck"):
                return
            
            # 获取牌组信息
            deck = deck_info.get("deck", {}).copy()  # 复制以避免修改原始数据
            deck_id = deck.get("deck_id")
            deck_name = deck.get("deck_name", "")
            
            if not deck_id:
                return
                
            # 如果牌组已经添加过，跳过
            if deck_id in added_deck_ids:
                return
            
            # 确定当前牌组的路径和层级
            if current_path is None:
                current_path = []
            
            # 设置牌组的层级和完整路径信息
            deck["level"] = len(current_path)
            deck["path"] = current_path + [deck_name]
            
            # 添加当前牌组到可见列表
            self._visible_decks.append(deck)
            added_deck_ids.add(deck_id)  # 标记为已添加
            
            # 只有当牌组已展开时，才添加其子牌组
            if deck_id in self._expanded_decks:
                # 获取并添加所有子牌组，按名称排序
                children = deck_info.get("children", {})
                sorted_children = sorted(
                    children.items(),
                    key=lambda x: x[1].get("deck", {}).get("deck_name", "")
                )
                
                # 当前牌组路径，用于子牌组
                new_path = current_path + [deck_name]
                
                for child_id, child_info in sorted_children:
                    add_visible_decks(child_info, new_path)
        
        # 添加所有顶级牌组及其子牌组，按名称排序
        for deck_id, deck_info in sorted(
            top_level_decks.items(),
            key=lambda x: x[1].get("deck", {}).get("deck_name", "")
        ):
            add_visible_decks(deck_info, [])
        
        # 更新最小高度
        min_height = len(self._visible_decks) * (self._row_height + self._row_padding) + self._margin_top + self._margin_bottom
        self.setMinimumHeight(max(200, min_height))
        print(f"_updateVisibleDecks: 更新完成，可见牌组数量: {len(self._visible_decks)}")
        
        # 打印可见牌组的层级结构，用于调试
        for deck in self._visible_decks:
            level = deck.get("level", 0)
            indent = "  " * level
            print(f"{indent}- {deck.get('deck_name')} (ID: {deck.get('deck_id')}, 父ID: {deck.get('parent_deck_id')})")
    
    def mousePressEvent(self, event):
        """处理鼠标点击事件，实现折叠功能"""
        x, y = event.position().x(), event.position().y()
        
        # 检查是否点击了牌组名称区域
        if x <= self._margin_left:
            # 计算点击的行索引
            row_idx = int((y - self._margin_top) / (self._row_height + self._row_padding))
            
            # 确保索引有效
            if 0 <= row_idx < len(self._visible_decks):
                deck = self._visible_decks[row_idx]
                deck_id = deck.get("deck_id")
                
                # 检查此牌组是否有子牌组
                has_children = False
                if deck_id in self._complete_deck_tree:
                    has_children = len(self._complete_deck_tree[deck_id].get("children", {})) > 0
                
                if has_children:
                    # 切换展开/折叠状态
                    if deck_id in self._expanded_decks:
                        self._expanded_decks.remove(deck_id)
                    else:
                        self._expanded_decks.add(deck_id)
                    
                    self._updateVisibleDecks()
                    self.update()
    
    def paintEvent(self, event):
        """绘制图表"""
        print(f"横道图paintEvent: 牌组数据={len(self._deck_data)}, 可见牌组={len(self._visible_decks)}")
        
        # 即使没有数据，也创建画布
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 获取绘图区域
        width = self.width()
        height = self.height()
        
        # 绘制标题
        if self._title:
            painter.setPen(self._text_color)
            font = painter.font()
            font.setPointSize(10)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(
                QRect(0, 5, width, self._margin_top - 5),
                Qt.AlignmentFlag.AlignCenter,
                self._title
            )
        
        # 计算图表区域
        available_width = width - self._margin_left - self._margin_right
        chart_width = available_width // 2  # 只使用一半的可用宽度
        
        chart_rect = QRect(
            self._margin_left,
            self._margin_top,
            chart_width,  # 使用缩减的宽度
            height - self._margin_top - self._margin_bottom
        )
        
        # 查找最大持续时间值
        max_duration = 0
        for deck in self._visible_decks:
            deck_id = deck.get("deck_id")
            if deck_id:
                total_duration = self._total_durations.get(deck_id, 0)
                max_duration = max(max_duration, total_duration)
        
        if max_duration == 0:
            max_duration = 1  # 避免除以零错误
        
        # 绘制X轴网格线和标签
        painter.setPen(QPen(self._grid_color, 1, Qt.PenStyle.DashLine))
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        
        # X轴刻度步长 (每小时一个刻度)
        hour_in_seconds = 3600
        x_step = hour_in_seconds
        
        # 计算需要多少个小时刻度
        hours_needed = math.ceil(max_duration / hour_in_seconds)
        hours_needed = max(1, min(24, hours_needed))  # 至少1小时，最多24小时
        
        # 绘制X轴刻度和网格线
        for i in range(hours_needed + 1):
            # X坐标
            x = self._margin_left + (i * x_step / max_duration) * chart_rect.width()
            
            # 绘制网格线
            painter.drawLine(
                int(x),
                int(self._margin_top),
                int(x),
                int(height - self._margin_bottom)
            )
            
            # 绘制X轴标签
            time_text = f"{i}小时"
            painter.drawText(
                QRect(
                    int(x - 30),
                    int(height - self._margin_bottom),
                    int(60),
                    int(20)
                ),
                Qt.AlignmentFlag.AlignCenter,
                time_text
            )
        
        # 绘制每个牌组的横条
        for i, deck in enumerate(self._visible_decks):
            y_pos = self._margin_top + i * (self._row_height + self._row_padding)
            
            # 获取牌组ID和总时长
            deck_id = deck.get("deck_id")
            study_time = deck.get("duration", 0)  # 牌组自身的时长
            total_time = self._total_durations.get(deck_id, 0)  # 包含下级牌组的总时长
            has_data = total_time > 0
            
            # 绘制牌组名称
            is_parent = self._isParentDeck(deck)
            
            # 获取层级信息，确保即使折叠状态也保持正确的缩进
            deck_level = deck.get("level", 0)
            
            # 固定的缩进宽度
            indent_width = 20  # 每级缩进宽度
            
            # 牌组名和图标的起始位置（随层级增加而缩进）
            content_left = 10 + (deck_level * indent_width)
            
            # 折叠/展开指示符
            icon_width = 15
            if is_parent:
                if deck_id in self._expanded_decks:
                    expand_icon = "[-]"  # 展开状态
                else:
                    expand_icon = "[+]"  # 折叠状态
                
                # 绘制展开/折叠指示符
                painter.setPen(QColor(100, 100, 100))
                painter.drawText(
                    QRect(
                        int(content_left),
                        int(y_pos),
                        int(icon_width),
                        int(self._row_height)
                    ),
                    Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter,
                    expand_icon
                )
            
            # 绘制牌组名称
            painter.setPen(self._text_color)
            font = painter.font()
            font.setBold(deck_level == 0 or is_parent)  # 父牌组加粗显示
            font.setPointSize(9)
            painter.setFont(font)
            
            # 获取牌组名称 - 只显示当前级别的名称，不显示完整路径
            deck_name = deck.get("deck_name", "未知牌组")
            
            # 如果牌组名称包含"::"，只显示最后一部分（本级名称）
            if "::" in deck_name:
                deck_name = deck_name.split("::")[-1]
            
            # 文本位置（考虑父牌组是否有展开/折叠图标）
            text_left = content_left + (icon_width if is_parent else 0) + 5  # 额外添加5像素间距
            
            # 计算文本区域
            text_rect = QRect(
                int(text_left),
                int(y_pos),
                int(self._margin_left - text_left - 10),  # 留出右侧边距
                int(self._row_height)
            )
            
            # 绘制牌组名称
            painter.drawText(
                text_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                deck_name
            )
            
            # 如果有数据，绘制横条
            if has_data:
                # 计算总时长条的宽度
                total_width = int((total_time / max_duration) * chart_rect.width())
                
                if total_width > 0:
                    # 绘制总时长条
                    total_rect = QRect(
                        int(self._margin_left),
                        int(y_pos + 2),  # 上下稍微收缩，美观度更高
                        int(total_width),
                        int(self._row_height - 4)
                    )
                    
                    painter.fillRect(total_rect, self._study_color)
                    
                    # 如果宽度足够，显示时间信息
                    if total_width > 40:
                        painter.setPen(Qt.GlobalColor.white)
                        time_text = format_time_seconds(total_time)
                        painter.drawText(
                            total_rect,
                            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter,
                            time_text
                        )
        
        painter.end()
    
    def _isParentDeck(self, deck):
        """检查一个牌组是否是父牌组"""
        deck_id = deck.get("deck_id")
        if deck_id in self._complete_deck_tree:
            return len(self._complete_deck_tree[deck_id].get("children", {})) > 0
        return False 