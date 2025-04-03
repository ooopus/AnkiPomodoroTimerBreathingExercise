# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import QWidget, QDialog, QApplication
from PyQt6.QtCore import Qt, QPointF, pyqtSignal
from PyQt6.QtGui import QColor, QPalette, QResizeEvent
import sys # Needed for standalone app

# --- Determine Environment and Setup Mocks ---
_anki_context = False
try:
    # Attempt to import Anki modules
    from aqt import mw, theme
    # Attempt to import config *relative to the addon structure*
    # If timer_common.py is in the root of your addon, use:
    # from .config import get_config
    # If it's in a subfolder 'timer', use:
    # from ..config import get_config
    # Assuming it's in the root for now:
    try:
        from ..config import get_config # Use relative import
    except ImportError:
        print("Running standalone or config.py not found relative to timer_common.py.")
        # Fallback to basic mock if relative import fails
        def get_config():
            print("WARNING: Using basic mock get_config() in timer_common.")
            return {"timer_position": "右上角", "enabled": True, "timer_style": "gradient"} # Add style default

    _anki_context = True
    print("Running in Anki context (detected by timer_common.py).")

except ImportError:
    print("Running outside Anki. Using mock objects (defined in timer_common.py).")

    # --- Mocks for Standalone Execution ---
    class MockThemeManager:
        night_mode = False # Set True for dark mode testing

    class MockTheme:
        theme_manager = MockThemeManager()

    class MockPm:
        night_mode = MockThemeManager.night_mode

    class MockMw:
        pm = MockPm()
        app = None

    mw = MockMw()
    theme = MockTheme()

    # Define get_config mock ONLY if not running in Anki
    def get_config():
        # Simulate config for standalone testing
        return {"timer_position": "右上角", "enabled": True, "timer_style": "gradient"} # Default style


# --- Single `is_dark_mode` Function (Common) ---
def is_dark_mode() -> bool:
    """Checks if dark mode is active, handling both Anki and standalone contexts."""
    if _anki_context:
        try:
            if hasattr(theme, 'theme_manager') and isinstance(theme.theme_manager.night_mode, bool):
                return theme.theme_manager.night_mode
            elif hasattr(mw, 'pm') and hasattr(mw.pm, 'night_mode') and isinstance(mw.pm.night_mode, bool):
                return mw.pm.night_mode
        except Exception:
            pass
    else:
        if (hasattr(theme, 'theme_manager') and
            hasattr(theme.theme_manager, 'night_mode') and
            isinstance(theme.theme_manager.night_mode, bool)):
            return theme.theme_manager.night_mode
        elif (hasattr(mw, 'pm') and
              hasattr(mw.pm, 'night_mode') and
              isinstance(mw.pm.night_mode, bool)):
            return mw.pm.night_mode

    try:
        app = QApplication.instance()
        if app and hasattr(app, 'palette'):
            if isinstance(app, QApplication):
                palette = app.palette()
                if hasattr(palette, 'color'):
                    window_color = palette.color(QPalette.ColorRole.Window)
                    if hasattr(window_color, 'value'):
                        return window_color.value() < 128
    except Exception:
        pass
    return False

# --- Constants (Common) ---
# Define all potential colors here
# Light Mode Colors
BG_COLOR_START_LIGHT = QColor(230, 230, 230, 200)
BG_COLOR_END_LIGHT = QColor(200, 200, 200, 220)
PROGRESS_COLOR_START_LIGHT = QColor(0, 150, 255)
PROGRESS_COLOR_END_LIGHT = QColor(0, 100, 200)
TEXT_COLOR_START_LIGHT = QColor(50, 50, 50)     # Used by gradient style
TEXT_COLOR_END_LIGHT = QColor(80, 80, 80)      # Used by gradient style
SHADOW_COLOR_LIGHT = QColor(0, 0, 0, 40)

# Dark Mode Colors (Night Mode)
BG_COLOR_START_DARK = QColor(70, 70, 80, 200)
BG_COLOR_END_DARK = QColor(50, 50, 60, 220)
PROGRESS_COLOR_START_DARK = QColor(20, 180, 255)
PROGRESS_COLOR_END_DARK = QColor(10, 130, 220)
TEXT_COLOR_START_DARK = QColor(220, 220, 220)  # Used by gradient style
TEXT_COLOR_END_DARK = QColor(240, 240, 240)  # Used by gradient style
SHADOW_COLOR_DARK = QColor(0, 0, 0, 70)


# --- TimerWindow (Container Dialog - Common) ---
# This class is independent of how the timer *looks* inside it.
class TimerWindow(QDialog):
    closed = pyqtSignal()

    # Modified __init__ to accept the class of the timer widget
    def __init__(self, timer_widget_class: type[QWidget], parent=None):
        super().__init__(parent)

        use_frameless = True # Default to frameless
        if _anki_context and use_frameless:
            self.setWindowFlags(
                Qt.WindowType.Tool |
                Qt.WindowType.WindowStaysOnTopHint |
                Qt.WindowType.FramelessWindowHint
            )
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self._offset = QPointF()
        else:
            self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
            self._offset = None # No dragging if not frameless

        self.setWindowTitle("番茄钟计时器")
        self.setMinimumSize(100, 100)
        # Instantiate the *passed* timer widget class
        self.timer_widget = timer_widget_class(self)
        self.resize(150, 150)
        self._position_window()
        self._center_timer_widget()

    def _position_window(self):
        # Logic is identical, uses common get_config
        screen = QApplication.primaryScreen()
        if not screen:
            return
        margin = 20
        screen_rect = screen.availableGeometry()
        config = get_config() # Assumes get_config is available
        position = config.get("timer_position", "右上角")
        window_width, window_height = self.width(), self.height()
        x, y = margin, margin
        if position == "右上角":
            x = screen_rect.width() - window_width - margin
        elif position == "左下角":
            y = screen_rect.height() - window_height - margin
        elif position == "右下角":
            x = screen_rect.width() - window_width - margin
            y = screen_rect.height() - window_height - margin
        self.move(x, y)

    def _center_timer_widget(self):
        # Logic is identical
        dialog_w, dialog_h = self.width(), self.height()
        margin = 0 if (self.windowFlags() & Qt.WindowType.FramelessWindowHint) else 5
        widget_size = max(self.timer_widget.minimumSize().width(), min(dialog_w, dialog_h) - 2 * margin)
        # Ensure timer_widget exists before setting size
        if hasattr(self, 'timer_widget') and self.timer_widget:
             self.timer_widget.setFixedSize(widget_size, widget_size)
             widget_x = (dialog_w - widget_size) // 2
             widget_y = (dialog_h - widget_size) // 2
             self.timer_widget.move(widget_x, widget_y)

    def resizeEvent(self, event: QResizeEvent):
        # Logic is identical
        super().resizeEvent(event)
        self._center_timer_widget()

    # --- Frameless Window Dragging Methods (Identical) ---
    def mousePressEvent(self, event):
        if self._offset is not None and event.button() == Qt.MouseButton.LeftButton:
            self._offset = event.globalPosition() - QPointF(self.pos())
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition() - self._offset
            self.move(new_pos.toPoint())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._offset is not None and event.button() == Qt.MouseButton.LeftButton:
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    # --- Close Event (Identical) ---
    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)


# --- Setup Function (Common - Modified) ---
_timer_window_instance = None
# Modified to accept the specific CircularTimer class to use
def setup_circular_timer(timer_widget_class: type[QWidget], force_new=False):
    """创建或显示独立的计时器窗口 (使用指定的计时器样式类)."""
    global _timer_window_instance

    config = get_config() # Assumes get_config is available
    if not config.get("enabled", True):
        if _timer_window_instance:
            _timer_window_instance.close()
            _timer_window_instance = None
        return None

    # Check if the existing window was created with the *same* timer class
    # If the style changed, we need a new window.
    style_changed = False
    if _timer_window_instance and hasattr(_timer_window_instance, 'timer_widget'):
        if not isinstance(_timer_window_instance.timer_widget, timer_widget_class):
            style_changed = True
            force_new = True # Force recreation if style is different

    if _timer_window_instance and not force_new:
        _timer_window_instance._position_window()
        _timer_window_instance.show()
        _timer_window_instance.raise_()
        _timer_window_instance.activateWindow()
    else:
        if _timer_window_instance and (force_new or style_changed):
             print(f"Closing existing timer window (force_new={force_new}, style_changed={style_changed})")
             _timer_window_instance.close()
             # Ensure instance is None before creating new one
             # The on_closed signal might take a moment, set explicitly
             _timer_window_instance = None


        print(f"Creating new TimerWindow with widget class: {timer_widget_class.__name__}")
        parent_mw = mw if _anki_context else None
        # Pass the specific timer widget class to TimerWindow
        _timer_window_instance = TimerWindow(timer_widget_class=timer_widget_class, parent=parent_mw)
        _timer_window_instance.show()

        # Define nested function for clarity (identical logic)
        def on_closed():
            global _timer_window_instance
            # Check if the closed window is the one we think it is
            # (Prevents issues if closed signal arrives after a new window was forced)
            # This check might be overly cautious but can prevent race conditions.
            # sender_window = self.sender() # This won't work easily here
            print("Signal 'closed' received. Setting _timer_window_instance to None.")
            _timer_window_instance = None


        _timer_window_instance.closed.connect(on_closed)

    # Return the actual timer widget *inside* the window
    return _timer_window_instance.timer_widget if _timer_window_instance else None

# --- Basic Standalone Runner Function (Helper) ---
def run_standalone_test(timer_widget_class: type[QWidget]):
    """Runs a standalone test application for the given timer widget class."""
    app = QApplication(sys.argv)

    # --- Optional: Force Dark/Light Mode for Standalone Test ---
    # theme.theme_manager.night_mode = True
    # print(f"Standalone Test - Dark Mode: {is_dark_mode()}")
    # ----------------------------------------------------------

    timer_widget = setup_circular_timer(timer_widget_class=timer_widget_class, force_new=True)

    if timer_widget:
        total_duration = 120
        current_time = total_duration

        from PyQt6.QtCore import QTimer # Import QTimer locally for test

        def update_timer_test():
            nonlocal current_time, timer_widget # Use nonlocal
            # Check if the window (and thus the widget) still exists
            if _timer_window_instance and _timer_window_instance.isVisible():
                current_time -= 1
                if current_time < 0:
                    current_time = total_duration

                # Access set_progress via the widget returned by setup_circular_timer
                timer_widget.set_progress(current_time, total_duration)

                QTimer.singleShot(1000, update_timer_test)
            else:
                print("Timer window closed or not visible, stopping test updates.")
                # Optionally exit the app when the window closes
                # QApplication.instance().quit()


        # Start the test timer updates
        update_timer_test()
        print(f"Standalone test running with {timer_widget_class.__name__}...")
        sys.exit(app.exec())
    else:
        print("Timer widget could not be created (likely disabled in config).")
        sys.exit(1)