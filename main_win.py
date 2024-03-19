from PySide6.QtWidgets import QMainWindow, QHBoxLayout, QWidget, QApplication
from .chat_interface import ChatInterface

class MainWindow(QMainWindow):
    def __init__(self, profile_name):
        super().__init__()
        self.profile_name = profile_name
        self.chatInterface = ChatInterface()

        self.setWindowTitle("Chatbot 2")
        self.setGeometry(100, 100, 800, 600)

        # Setting up chat interface as central widget
        chat_box = QWidget()
        self.setCentralWidget(chat_box)
        layout = QHBoxLayout(chat_box)
        layout.addWidget(self.chatInterface, 3)
        chat_box.setLayout(layout)
        self.centerWindow()

    def centerWindow(self):
        # Positions window based off of current screen dimensions
        screen = QApplication.primaryScreen().geometry()
        x = int((screen.width() - self.width()) / 2)
        y = int((screen.height() - self.height()) / 2 - 100)
        self.move(x, y)
