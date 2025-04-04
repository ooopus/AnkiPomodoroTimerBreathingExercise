from typing import Optional
from aqt import QLabel, QTimer


class TimerState:
    def __init__(self):
        self._pomodoro_timer = None
        self._timer_label = None

    @property
    def pomodoro_timer(self) -> Optional[QTimer]:
        return self._pomodoro_timer

    @pomodoro_timer.setter
    def pomodoro_timer(self, value):
        self._pomodoro_timer = value

    @property
    def timer_label(self) -> Optional[QLabel]:
        return self._timer_label

    @timer_label.setter
    def timer_label(self, value: Optional[QLabel]):
        self._timer_label = value


_timer_state = None


def get_timer_state() -> TimerState:
    global _timer_state
    if _timer_state is None:
        _timer_state = TimerState()
    return _timer_state


def get_pomodoro_timer():
    return get_timer_state().pomodoro_timer


def set_pomodoro_timer(timer) -> None:
    get_timer_state().pomodoro_timer = timer


def get_timer_label() -> Optional[QLabel]:
    return get_timer_state().timer_label


def set_timer_label(label: Optional[QLabel]) -> None:
    get_timer_state().timer_label = label
