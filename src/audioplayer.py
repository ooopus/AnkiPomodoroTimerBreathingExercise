from typing import Union

from aqt import QDialog, QMainWindow, QObject, mw
from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer


class AudioPlayer(QObject):
    def __init__(self, parent: Union[QMainWindow, QDialog] = mw):
        super().__init__(parent)
        self.player = QMediaPlayer(parent)
        self._audio_output = QAudioOutput()
        self.player.setAudioOutput(self._audio_output)
        self._cache: dict[str, QUrl] = {}  # Cache for audio files: {file_path: QUrl}

    def play(self, file_path: str):
        """Play the audio file, using cached version if available."""
        if not file_path:
            return

        # Use cached URL if available
        if file_path in self._cache:
            url: QUrl = self._cache[file_path]
        else:
            url: QUrl = QUrl.fromLocalFile(file_path)
            self._cache[file_path] = url

        self.player.setSource(url)
        self.player.play()

    def stop(self):
        """Stop the audio playback."""
        self.player.stop()
