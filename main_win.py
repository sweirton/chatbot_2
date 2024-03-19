from PySide6.QtWidgets import QMainWindow, QHBoxLayout, QWidget, QApplication
from .chat_interface import ChatInterface
from .history_interface import ChatHistoryWidget

class MainWindow(QMainWindow):
    def __init__(self, profile_name):
        super().__init__()
        self.profile_name = profile_name
        self.chat_interface = ChatInterface(self.profile_name)

        self.setWindowTitle("Chatbot 2")
        self.setGeometry(100, 100, 800, 600)

        # Create a container widget for the chat interface and history
        chat_box = QWidget()
        self.setCentralWidget(chat_box)

        # Set up a horizontal layout for the container widget
        layout = QHBoxLayout()

        # Initialize the chat history widget and add it to the layout
        self.chat_history_widget = ChatHistoryWidget(profile_name=self.profile_name)
        layout.addWidget(self.chat_history_widget, stretch=3)
        chat_box.setLayout(layout)

        # Chat interface widget
        layout.addWidget(self.chat_interface, 8)


        # Apply the layout to the container widget
        chat_box.setLayout(layout)

        self.centerWindow()

    def centerWindow(self):
        # Positions window based off of current screen dimensions
        screen = QApplication.primaryScreen().geometry()
        x = int((screen.width() - self.width()) / 2)
        y = int((screen.height() - self.height()) / 2 - 100)
        self.move(x, y)
