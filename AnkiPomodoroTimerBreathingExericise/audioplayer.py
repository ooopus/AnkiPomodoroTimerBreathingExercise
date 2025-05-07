from aqt import QObject
from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer


class AudioPlayer(QObject):
    def __init__(self, parent=None):
        self.player = QMediaPlayer(parent)
        self._audio_output = QAudioOutput()
        self.player.setAudioOutput(self._audio_output)

    def play(self, file_path):
        """Play the audio file."""
        self.player.setSource(QUrl.fromLocalFile(file_path))
        self.player.play()

    def stop(self):
        """Stop the audio playback."""
        self.player.stop()
