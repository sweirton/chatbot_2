from PySide6.QtWidgets import QMainWindow

class MainWindow(QMainWindow):
    def __init__(self, profile_name):
        super().__init__()
        self.setWindowTitle("Chatbot 2")
        # Set the window's position and size: (x position, y position, width, height)
        self.setGeometry(100, 100, 800, 600)

        self.profile_name = profile_name

