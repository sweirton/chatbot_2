from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QProgressBar, QFileDialog, QMessageBox, QInputDialog, QLabel, QListWidget, QListWidgetItem
from PySide6.QtCore import QThread, Signal, Qt
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import os
import json
import shutil
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from main_win.chat_interface import ChatInterface


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


class ProfileConfig(QDialog):
    def __init__(self, parent=None, current_profile=None):
        super().__init__(parent)
        self.current_profile = current_profile
        self.setWindowTitle("Configuration")
        self.setGeometry(600, 300, 400, 300)
        self.setupUI()
        self.loadDocuments()
        self.chat_interface = ChatInterface(current_profile)
        api_key = self.chat_interface.loadAPIKey()
        os.environ["OPENAI_API_KEY"] = api_key

    def setupUI(self):
        layout = QVBoxLayout(self)

        self.documentListWidget = QListWidget()
        layout.addWidget(self.documentListWidget)

        self.uploadButton = QPushButton("Upload Document")
        self.uploadButton.clicked.connect(self.uploadDocument)
        layout.addWidget(self.uploadButton)

        self.progressBar = QProgressBar()
        layout.addWidget(self.progressBar)

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

        document_label, _ = os.path.splitext(os.path.basename(dest_file_path))
        directory_path = os.path.dirname(dest_file_path)
        subfolder_path = os.path.join(directory_path, "temp_processing")

        # Ensure the subfolder exists
        os.makedirs(subfolder_path, exist_ok=True)

        # Move the file to the subfolder
        temp_file_path = shutil.move(dest_file_path, subfolder_path)

        # Process the file in the subfolder
        file_for_query = SimpleDirectoryReader(input_dir=subfolder_path).load_data()
        vector_query_engine = VectorStoreIndex.from_documents(file_for_query, use_async=True).as_query_engine()
        response = vector_query_engine.query("Please provide a brief description of this document in 200 words or less.")

        # Construct the description data
        description_data = {document_label: str(response)}

        # Path for the descriptions.json file in the original directory
        json_file_path = os.path.join(directory_path, 'descriptions.json')

        # Check if the JSON file exists and update it
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as file:
                data = json.load(file)
                data.update(description_data)
        else:
            data = description_data

        # Write the updated data back to the JSON file
        with open(json_file_path, 'w') as file:
            json.dump(data, file, indent=4)

        # Move the file back to its original location
        shutil.move(temp_file_path, dest_file_path)

        # Load or refresh documents as needed
        self.loadDocuments()

    def loadDocuments(self):
        self.documentListWidget.clear()
        # Load documents from the user_data_storage directory
        data_store_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'profiles', self.current_profile, 'user_data_storage')
        if os.path.exists(data_store_path):
            for filename in os.listdir(data_store_path):
                item = QListWidgetItem(filename)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)  # Make items checkable
                item.setCheckState(Qt.Unchecked)  # Initially unchecked
                self.documentListWidget.addItem(item)

    def selectedDocs(self):
        checked_items = []
        for index in range(self.documentListWidget.count()):
            item = self.documentListWidget.item(index)
            if item.checkState() == Qt.Checked:
                checked_items.append(item.text())

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
