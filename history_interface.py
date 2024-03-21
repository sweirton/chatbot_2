from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget
from PySide6.QtCore import Signal
import os

class ChatHistoryWidget(QWidget):
    sessionSelected = Signal(str)

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

         # Select a history item in the list
        self.chat_history_list.setSelectionMode(QListWidget.SingleSelection)

        # Connect the itemSelectionChanged signal to a slot
        self.chat_history_list.itemSelectionChanged.connect(self.onSelectionChanged)

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

    def onSelectionChanged(self):
        if selected_items := self.chat_history_list.selectedItems():
            selected_filename = selected_items[0].text()
            # Construct the full path for the selected session
            selected_file_path = os.path.join(self.history_dir, selected_filename)
            # Emit the full path
            self.sessionSelected.emit(selected_file_path)
