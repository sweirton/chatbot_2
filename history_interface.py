from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget
import os

class ChatHistoryWidget(QWidget):
    def __init__(self, parent=None, profile_name=''):
        super().__init__(parent)

        # Create the chat history list widget
        self.chat_history_list = QListWidget()

        # Optional: Customize the list widget appearance
        self.chat_history_list.setStyleSheet("background-color: #F0F0F0;")

        # Set the layout for this widget
        layout = QVBoxLayout()
        layout.addWidget(self.chat_history_list)
        self.setLayout(layout)

        self.profile_name = profile_name
        self.history_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'profiles', self.profile_name, 'chat_history')
        self.populateWithFilenames()

    def populateWithFilenames(self):
        # List all files in the specified directory
        session_files = os.listdir(self.history_dir)

        # Filter to keep only .json files
        json_files = [file for file in session_files if file.endswith('.json')]

        # Clear existing items in the list widget before adding new ones
        self.chat_history_list.clear()

        # Add each JSON filename to the chat history list widget
        for filename in json_files:
            self.chat_history_list.addItem(filename)
