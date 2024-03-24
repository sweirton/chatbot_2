from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QProgressBar, QFileDialog, QMessageBox, QInputDialog
from PySide6.QtCore import QThread, Signal
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import os

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class ProfileConfig(QDialog):
    def __init__(self, parent=None, current_profile=None):
        super().__init__(parent)
        self.current_profile = current_profile
        self.setWindowTitle("AI Configuration")
        self.setGeometry(200, 200, 400, 300)
        self.setupUI()

    def setupUI(self):
        layout = QVBoxLayout(self)

        # Change Profile Name Button
        self.changeProfileNameButton = QPushButton("Change Profile Name")
        self.changeProfileNameButton.clicked.connect(self.changeProfileName)
        layout.addWidget(self.changeProfileNameButton)

        # Change API Key Button
        self.changeApiKeyButton = QPushButton("Change API Key")
        self.changeApiKeyButton.clicked.connect(self.changeApiKey)
        layout.addWidget(self.changeApiKeyButton)

        self.uploadButton = QPushButton("Upload Document")
        self.uploadButton.clicked.connect(self.uploadDocument)
        layout.addWidget(self.uploadButton)

        self.progressBar = QProgressBar()
        layout.addWidget(self.progressBar)

        # Save Changes Button
        self.saveButton = QPushButton("Save Changes")
        self.saveButton.clicked.connect(self.saveProfile)
        self.saveButton.setEnabled(False)  # Initially disabled
        layout.addWidget(self.saveButton)

    def changeProfileName(self):
        new_profile_name, ok = QInputDialog.getText(self, "Change Profile Name", "Enter new profile name:")
        if ok and new_profile_name:
            self.new_profile_name = new_profile_name
            self.saveButton.setEnabled(True)  # Enable Save button

    def changeApiKey(self):
        new_api_key, ok = QInputDialog.getText(self, "Change API Key", "Enter new API Key:")
        if ok and new_api_key:
            self.new_api_key = new_api_key
            self.saveButton.setEnabled(True)  # Enable Save button

    def uploadDocument(self):
        if not self.current_profile:
            QMessageBox.warning(self, "No Profile Loaded", "Please load or create a profile before uploading documents.")
            return

        filePath, _ = QFileDialog.getOpenFileName(self, "Open Document", "", "PDF Files (*.pdf);;Text Files (*.txt);;All Files (*)")
        if filePath:
            self._extracted_from_uploadDocument_8(filePath)

    # TODO Rename this here and in `uploadDocument`
    def _extracted_from_uploadDocument_8(self, filePath):
        data_store_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'profiles', self.current_profile, 'user_data_storage')
        os.makedirs(data_store_path, exist_ok=True)
        base_filename = f"{os.path.splitext(os.path.basename(filePath))[0]}.txt"
        dest_file_path = os.path.join(data_store_path, base_filename)

        self.worker = Worker(filePath, dest_file_path)
        self.worker.progress_updated.connect(self.progressBar.setValue)
        self.worker.finished.connect(self.onUploadFinished)
        self.worker.start()

    def onUploadFinished(self, dest_file_path):
        QMessageBox.information(self, "Upload Finished", f"Document processed and saved to {dest_file_path}")

    def saveProfile(self):
        if self.new_profile_name:
            profile_name = self.new_profile_name
        elif self.current_profile:
            profile_name = self.current_profile
        else:
            QMessageBox.warning(self, "No Profile", "Please create or load a profile before saving.")
            return

        profile_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'profiles', profile_name)
        if not os.path.exists(profile_dir):
            os.makedirs(profile_dir)

        env_path = os.path.join(profile_dir, 'api_info.env')
        with open(env_path, 'w') as file:
            api_key_line = f'API_KEY="{self.new_api_key}"' if self.new_api_key else 'API_KEY=""'
            file.write(api_key_line + '\n')

        QMessageBox.information(self, "Success", f"Profile '{profile_name}' saved successfully.")
        self.current_profile = profile_name  # Update the current profile
        self.saveButton.setEnabled(False)  # Disable Save button after saving

    def saveProfile(self):
        if not self.current_profile:
            # No profile is currently loaded
            create_new = QMessageBox.question(self, "Create New Profile?", "No profile is currently loaded. Would you like to create a new one?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if create_new == QMessageBox.No:
                return  # Do not proceed with saving

            # Prompt for a new profile name if decided to create a new one
            self.current_profile, ok = QInputDialog.getText(self, "New Profile Name", "Enter new profile name:")
            if not ok or not self.current_profile:
                QMessageBox.warning(self, "Profile Creation Cancelled", "No profile name provided. Profile creation cancelled.")
                return

        # Proceed with saving profile information
        profile_name = self.current_profile  # Use the loaded or newly provided profile name
        api_key = self.apiKeyLineEdit.text().strip()
        self.saveButton.setEnabled(False)

        if not api_key:
            QMessageBox.warning(self, "Warning", "API key is required.")
            return

        # Define the path for the profile directory and api_info.env file
        profile_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'profiles', profile_name)
        env_path = os.path.join(profile_dir, 'api_info.env')

        # Ensure the profile directory exists
        os.makedirs(profile_dir, exist_ok=True)

        # Write the API_KEY to the api_info.env file
        with open(env_path, 'w') as file:
            file.write(f'API_KEY="{api_key}"\n')
        
        QMessageBox.information(self, "Success", f"Profile '{profile_name}' saved successfully.")


class Worker(QThread):
    progress_updated = Signal(int)
    finished = Signal(str)

    def __init__(self, file_path, dest_file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.dest_file_path = dest_file_path

    def run(self):
        doc = fitz.open(self.file_path)
        content = ''
        total_pages = len(doc)
        for page_num in range(total_pages):
            page = doc.load_page(page_num)
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            content += pytesseract.image_to_string(img)
            self.progress_updated.emit(int((page_num + 1) / total_pages * 100))
        with open(self.dest_file_path, 'w', encoding='utf-8') as outfile:
            outfile.write(content)
        doc.close()
        self.finished.emit(self.dest_file_path)
