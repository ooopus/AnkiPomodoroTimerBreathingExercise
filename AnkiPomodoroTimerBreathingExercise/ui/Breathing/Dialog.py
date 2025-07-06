from typing import Optional

from aqt import (
    QCloseEvent,
    QDialog,
    QLabel,
    QMainWindow,
    QPushButton,
    Qt,
    QVBoxLayout,
    mw,
)

from ...config.enums import BreathingPhase
from ...translator import _
from .AnimationWidget import BreathingAnimationWidget


# --- Breathing Dialog UI ---
class BreathingDialog(QDialog):
    """Dialog window for the guided breathing exercise based on cycles."""

    from ...breathing import BreathingController

    def __init__(
        self, breathing_controller: BreathingController, parent: QMainWindow = mw
    ):
        super().__init__(parent or mw)
        self.controller = breathing_controller
        self.setWindowTitle(_("呼吸训练"))
        self.setModal(True)

        # 初始化UI组件
        self._init_ui()

        # 连接控制器信号
        self._connect_signals()

    def _init_ui(self):
        """初始化UI组件"""
        # --- UI Elements ---
        layout = QVBoxLayout(mw)
        self.animation_widget = BreathingAnimationWidget(self)
        layout.addWidget(self.animation_widget, 1)

        self.instruction_label = QLabel(_("准备..."), self)
        self.instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instruction_label.setStyleSheet(
            "font-size: 20px; font-weight: bold; margin-top: 10px;"
        )

        self.cycle_label = QLabel(
            _("循环: {current} / {total}").format(
                current=1, total=self.controller.target_cycles
            ),
            self,
        )
        self.cycle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cycle_label.setStyleSheet("font-size: 16px; margin-bottom: 10px;")

        self.skip_button = QPushButton(_("跳过训练"), self)

        layout.addWidget(self.instruction_label)
        layout.addWidget(self.cycle_label)
        layout.addWidget(self.skip_button)
        self.setLayout(layout)

        self.resize(300, 350)

    def _connect_signals(self):
        """连接信号和槽"""
        self.skip_button.clicked.connect(self.reject)

    def update_phase_display(
        self, label: str, duration: int, phase_key: BreathingPhase
    ):
        """更新当前阶段的显示"""
        self.instruction_label.setText(f"{label} ({duration}s)")
        self.animation_widget.set_phase(phase_key, duration)

    def update_cycle_display(self, current_cycle: int, total_cycles: int):
        """更新循环计数的显示"""
        self.cycle_label.setText(
            _("循环: {current} / {total}").format(
                current=current_cycle, total=total_cycles
            )
        )

    def stop_all_timers(self):
        """停止所有计时器"""
        self.animation_widget.stop_animation()
        if hasattr(self.controller, "stop_timers"):
            self.controller.stop_timers()

    def closeEvent(self, a0: Optional[QCloseEvent]):
        """Called when the dialog is closed (e.g., by window manager)."""
        self.stop_all_timers()
        super().closeEvent(a0)

    def accept(self):
        """Called when the exercise completes successfully."""
        self.stop_all_timers()
        super().accept()

    def reject(self):
        """Called when the dialog is skipped or closed prematurely."""
        self.stop_all_timers()
        super().reject()
