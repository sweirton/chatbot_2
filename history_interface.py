from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QPushButton, QMessageBox, QMenu
from PySide6.QtCore import Signal
from datetime import datetime
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

        # Create New Session button
        self.create_session_btn = QPushButton("Create New Session")
        self.create_session_btn.clicked.connect(self.createNewSession)
        layout.addWidget(self.create_session_btn)

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

    def createNewSession(self):
        new_session_name = self.genSessionName()
        new_session_file_path = os.path.join(self.history_dir, f'{new_session_name}.json')

        # Create an empty JSON file for the new session
        with open(new_session_file_path, 'w') as file:
            file.write("[]")

        # Update the list of sessions displayed in the widget
        self.populateWithFilenames()

    def genSessionName(self):
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        return f"{self.profile_name}_Session_{timestamp}"
    
    def contextMenuEvent(self, event):
        context_menu = QMenu(self)

        # Add a Delete action
        delete_action = context_menu.addAction("Delete Session")
        action = context_menu.exec(self.mapToGlobal(event.pos()))

        if action == delete_action:
            self.deleteSelectedSession()

    def deleteSelectedSession(self):
        if selected_items := self.chat_history_list.selectedItems():
            selected_filename = selected_items[0].text()
            selected_file_path = os.path.join(self.history_dir, selected_filename)

            # Confirm deletion with the user (optional)
            reply = QMessageBox.question(self, 'Delete Session',
                                         f"Are you sure you want to delete the session '{selected_filename}'?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                # Delete the file
                os.remove(selected_file_path)

                # Optionally, refresh the list to reflect the deletion
                self.populateWithFilenames()
