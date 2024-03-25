from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QPushButton, QMessageBox, QMenu, QInputDialog
from PySide6.QtCore import Signal
from datetime import datetime
import os

class ChatHistoryWidget(QWidget):
    sessionSelected = Signal(str)
    sessionCreated = Signal()

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

        # If there are no session files, create a new session
        if not session_files:
            self.createAndSelectNewSession()
            return
        
        # Filter to keep only .json files
        json_files = [file for file in session_files if file.endswith('.json')]

        # Clear existing items in the list widget before adding new ones
        self.chat_history_list.clear()

        # Add each JSON filename to the chat history list widget, without the '.json' extension
        for filename in json_files:
            display_name = os.path.splitext(filename)[0]  # Remove the '.json' extension
            self.chat_history_list.addItem(display_name)

        # Select the latest session if there are sessions available
        if json_files:
            latest_session = max(json_files)
            latest_session_path = os.path.join(self.history_dir, latest_session)
            self.sessionSelected.emit(latest_session_path)

    def onSelectionChanged(self):
        if selected_items := self.chat_history_list.selectedItems():
            selected_filename = f'{selected_items[0].text()}.json'
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

        # Find the index of the newly created session in the list of sessions
        session_files = os.listdir(self.history_dir)
        json_files = [file for file in session_files if file.endswith('.json')]
        new_session_index = json_files.index(f'{new_session_name}.json')

        # Select the newly created session in the widget
        self.chat_history_list.setCurrentRow(new_session_index)

        # Emit the signal to indicate that a new session has been created
        self.sessionCreated.emit()

    def genSessionName(self):
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        return f"{self.profile_name}_Session_{timestamp}"
    
    def contextMenuEvent(self, event):
        context_menu = QMenu(self)

        delete_action = context_menu.addAction("Delete Session")
        rename_action = context_menu.addAction("Rename Session")
        action = context_menu.exec(self.mapToGlobal(event.pos()))

        if action == delete_action:
            self.deleteSelectedSession()
        elif action == rename_action:
            self.renameSelectedSession()

    def deleteSelectedSession(self):
        if selected_items := self.chat_history_list.selectedItems():
            selected_filename = f'{selected_items[0].text()}.json'
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

    def renameSelectedSession(self):
        if not (selected_items := self.chat_history_list.selectedItems()):
            return
        selected_filename = f'{selected_items[0].text()}.json'
        selected_file_path = os.path.join(self.history_dir, selected_filename)

        # Prompt the user for a new name (without the .json extension)
        current_name_without_extension = os.path.splitext(selected_filename)[0]
        new_name, ok = QInputDialog.getText(self, "Rename Session", "Enter new name:", text=current_name_without_extension)

        if ok and new_name:
            # Ensure the new name has the .json extension
            if not new_name.endswith('.json'):
                new_name += '.json'

            new_file_path = os.path.join(self.history_dir, new_name)

            # Check if a file with the new name already exists
            if os.path.exists(new_file_path):
                QMessageBox.warning(self, "Rename Failed", f"A session with the name '{new_name}' already exists.")
                return

            # Rename the file
            os.rename(selected_file_path, new_file_path)

            # Refresh the list to reflect the name change
            self.populateWithFilenames()

    def updateProfileName(self, profile_name):
        self.profile_name = profile_name
        self.update_history_dir()
        self.populateWithFilenames()

    def update_history_dir(self):
        self.history_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'profiles', self.profile_name, 'chat_history')
        os.makedirs(self.history_dir, exist_ok=True)

    def selectRecentSession(self):
        # Get the number of items in the list
        count = self.chat_history_list.count()
        if count > 0:
            # Select the last item (most recent session)
            self.chat_history_list.setCurrentRow(count - 1)

    def createAndSelectNewSession(self):
        self.createNewSession()
        if self.chat_history_list.count() > 0:
            self.chat_history_list.setCurrentRow(self.chat_history_list.count() - 1)
