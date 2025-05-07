from aqt import (
    QTimer,
    mw,
)

from .audioplayer import AudioPlayer
from .constants import PHASES
from .state import get_app_state
from .ui.Breathing import BreathingDialog


# --- Breathing Exercise Controller ---
class BreathingController:
    """控制呼吸训练的业务逻辑"""

    def __init__(self, target_cycles: int):
        self.target_cycles = max(1, target_cycles)  # 确保至少有一个循环
        self.completed_cycles = 0
        self.current_phase_index = -1
        self._phase_timer = None
        self._current_audio_player = None

        # 从配置中获取活动阶段
        self._load_active_phases()

        # UI对话框
        self.dialog = None

    def _load_active_phases(self):
        """从配置中加载活动的呼吸阶段"""
        app_state = get_app_state()
        config = app_state.config

        # --- 根据配置动态构建活动阶段 ---
        self.active_phases = []
        for phase_def in PHASES:
            key = phase_def["key"]
            is_enabled = config.get(f"{key}_enabled", phase_def["default_enabled"])
            duration = config.get(f"{key}_duration", phase_def["default_duration"])
            audio_path = config.get(f"{key}_audio", phase_def.get("default_audio", ""))
            if is_enabled:
                self.active_phases.append(
                    {
                        "label": phase_def["label"],
                        "duration": duration,
                        "key": key,
                        "audio_path": audio_path,
                    }
                )

    def start(self, parent=None):
        """启动呼吸训练"""
        if not self.active_phases:
            return False

        # 创建对话框
        self.dialog = BreathingDialog(self, parent)

        self.audio_player = AudioPlayer(self.dialog)

        # 创建阶段计时器
        self._phase_timer = QTimer(mw)
        self._phase_timer.setSingleShot(True)
        self._phase_timer.timeout.connect(self._advance_to_next_phase)

        # 开始第一个阶段
        self._advance_to_next_phase()

        # 显示对话框并返回结果
        return self.dialog.exec()

    def _advance_to_next_phase(self):
        """处理进入下一个阶段或完成练习的逻辑"""
        # 确定下一个阶段索引，并检查是否刚完成一个循环
        next_phase_index = (self.current_phase_index + 1) % len(self.active_phases)
        just_completed_cycle = (
            next_phase_index == 0 and self.current_phase_index != -1
        )  # 如果回到开始，则表示完成了一个循环

        self.audio_player.stop()

        # 在完成循环的最后一个阶段后增加循环计数
        if just_completed_cycle:
            self.completed_cycles += 1
            self.dialog.update_cycle_display(
                min(self.completed_cycles + 1, self.target_cycles), self.target_cycles
            )

            # 检查是否达到目标循环次数
            if self.completed_cycles >= self.target_cycles:
                self.dialog.accept()
                return

        self.current_phase_index = next_phase_index
        current_phase_data = self.active_phases[self.current_phase_index]
        duration = current_phase_data["duration"]
        label = current_phase_data["label"]
        phase_key = current_phase_data["key"]
        audio_path = current_phase_data["audio_path"]

        # 更新UI显示当前阶段
        self.dialog.update_phase_display(label, duration, phase_key)
        self.dialog.update_cycle_display(self.completed_cycles + 1, self.target_cycles)

        if audio_path:
            self.audio_player.play(audio_path)

        if duration > 0:
            self._phase_timer.start(duration * 1000)
        else:
            # 如果持续时间为0，立即前进（带有微小延迟以便事件循环）
            self._phase_timer.start(10)

    def stop_timers(self):
        """停止阶段计时器"""
        if self._phase_timer and self._phase_timer.isActive():
            self._phase_timer.stop()
        self.audio_player.stop()


# --- 便捷函数 ---
def start_breathing_exercise(target_cycles: int = None, parent=None):
    """启动呼吸训练练习"""
    # 如果未指定目标循环次数，则从配置中获取
    if target_cycles is None:
        app_state = get_app_state()
        target_cycles = app_state.config.get("breathing_cycles", 3)

    # 创建控制器并启动训练
    controller = BreathingController(target_cycles)
    return controller.start(parent)
