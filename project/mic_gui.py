import sys
import pyaudio
import audioop
import speech_recognition as sr
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QColor, QBrush, QFont, QPen
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal

class SpeechToTextThread(QThread):
    text_updated = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.running = True

    def run(self):
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
            while self.running:
                try:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                    text = self.recognizer.recognize_google(audio)
                    self.text_updated.emit(text)
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    self.text_updated.emit("Could not understand audio")
                except Exception as e:
                    self.text_updated.emit(f"Error: {str(e)}")

    def stop(self):
        self.running = False
        self.wait()

class VoiceVisualizer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Voice Visualizer")
        self.setStyleSheet("background-color: black;")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.showFullScreen()

        # Audio stream setup
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )

        self.volume_level = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_visual)
        self.timer.start(30)

        # Speech to text setup
        self.speech_text = "Speak now..."
        self.speech_thread = SpeechToTextThread()
        self.speech_thread.text_updated.connect(self.update_speech_text)
        self.speech_thread.start()

        # Font setup for text
        self.font = QFont()
        self.font.setPointSize(16)
        self.font.setBold(True)

    def update_visual(self):
        data = self.stream.read(self.CHUNK, exception_on_overflow=False)
        rms = audioop.rms(data, 2)
        self.volume_level = min(rms / 30, 100)
        self.update()

    def update_speech_text(self, text):
        self.speech_text = text
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        # Draw the circle
        radius = 50 + int(self.volume_level)
        painter.setBrush(QBrush(QColor(0, 200, 255)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center_x - radius, center_y - radius - 100, radius * 2, radius * 2)
        
        # Draw the square box below the circle
        box_width = self.width() - 200
        box_height = 120
        box_x = center_x - box_width // 2
        box_y = center_y + radius + 20  # Position below the circle
        
        # Draw square box
        painter.setPen(QPen(QColor(0, 200, 255), 2))
        painter.setBrush(QBrush(QColor(0, 0, 0, 200)))  # Semi-transparent black
        painter.drawRect(box_x, box_y, box_width, box_height)
        
        # Draw text inside the box
        painter.setFont(self.font)
        painter.setPen(QColor(255, 255, 255))  # White text
        
        # Format text with word wrapping
        text_rect = painter.boundingRect(
            box_x + 20, box_y + 20, box_width - 40, box_height - 40,
            Qt.TextWordWrap, self.speech_text
        )
        painter.drawText(text_rect, Qt.TextWordWrap, self.speech_text)

    def closeEvent(self, event):
        self.timer.stop()
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        self.speech_thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    visualizer = VoiceVisualizer()
    sys.exit(app.exec_())