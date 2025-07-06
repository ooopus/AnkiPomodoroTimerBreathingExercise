import sys
from pathlib import Path

# Add the 'vendor' directory to Python's path
vendor_dir = Path(__file__).resolve().parent.parent / "vendor"
if str(vendor_dir) not in sys.path:
    sys.path.insert(0, str(vendor_dir))
# 由于anki使用自带的python，必须先导入外部依赖

import dataclasses
from pathlib import Path
from typing import Optional

from koda_validate import DataclassValidator

from .constants import AUDIO_FILENAMES
from .enums import (
    BreathingPhase,
    CircularTimerStyle,
    StatusBarFormat,
    TimerPosition,
)
from .languages import LanguageCode


def get_default_audio_path(
    phase: BreathingPhase, language_code: LanguageCode
) -> Optional[str]:
    """
    根据呼吸阶段和语言，获取默认的音频文件路径。
    """
    # Correctly determine the media path relative to this file
    media_path = Path(__file__).resolve().parent.parent / "media"

    # Get the filename from the new constants structure
    phase_audio = AUDIO_FILENAMES.get(language_code, {})
    if not phase_audio:
        # Fallback to English if the language is not defined
        phase_audio = AUDIO_FILENAMES.get(LanguageCode.ENGLISH, {})

    file_name = phase_audio.get(phase)
    if not file_name:
        return None  # No audio for this phase

    # Check for language-specific version
    language_path = media_path / language_code.value
    if not language_path.exists() and "_" in language_code.value:
        # Fallback to base language (e.g., 'zh' from 'zh_CN')
        language_path = media_path / language_code.value.split("_")[0]

    if language_path.exists() and (language_path / file_name).exists():
        return str(language_path / file_name)

    # Fallback to English if no specific audio is found
    english_file_name = AUDIO_FILENAMES[LanguageCode.ENGLISH].get(phase)
    if english_file_name:
        return str(media_path / LanguageCode.ENGLISH.value / english_file_name)

    return None


@dataclasses.dataclass
class AppConfig:
    """
    应用程序的主配置数据类。
    存储经过验证和填充的配置值。
    """

    # 常规设置
    enabled: bool = True
    pomodoro_minutes: int = 25
    long_break_minutes: int = 15
    pomodoros_before_long_break: int = 4
    work_across_decks: bool = True
    language: LanguageCode = LanguageCode.AUTO

    # 呼吸练习设置
    breathing_cycles: int = 25
    inhale_duration: int = 5
    inhale_enabled: bool = True
    inhale_audio: Optional[str] = dataclasses.field(
        default_factory=lambda: get_default_audio_path(
            BreathingPhase.INHALE, LanguageCode.ENGLISH
        )
    )
    exhale_duration: int = 5
    exhale_enabled: bool = True
    exhale_audio: Optional[str] = dataclasses.field(
        default_factory=lambda: get_default_audio_path(
            BreathingPhase.EXHALE, LanguageCode.ENGLISH
        )
    )
    hold_after_inhale_duration: int = 0
    hold_after_inhale_enabled: bool = False
    hold_after_inhale_audio: Optional[str] = None
    hold_after_exhale_duration: int = 0
    hold_after_exhale_enabled: bool = False
    hold_after_exhale_audio: Optional[str] = None

    # 界面设置
    show_circular_timer: bool = True
    circular_timer_style: CircularTimerStyle = CircularTimerStyle.DEFAULT
    statusbar_format: StatusBarFormat = (
        StatusBarFormat.ICON_COUNTDOWN_PROGRESS_WITH_TOTAL_TIME
    )
    timer_position: TimerPosition = TimerPosition.TOP_RIGHT

    # 状态字段
    completed_pomodoros: int = 0
    daily_pomodoro_seconds: int = 0
    max_break_duration: int = 1800  # 以秒为单位
    last_pomodoro_time: float = 0.0
    last_date: str = ""


# --- 2. 使用 DataclassValidator 简化并修正验证逻辑 ---
# 这一行代码会根据上面的 AppConfig 类自动生成一个完整的、正确的验证器。
# 它会处理所有字段的类型检查和默认值。
config_validator = DataclassValidator(AppConfig)
