# Standard libraries
import json
import os
import shutil

# Third-party libraries for GUI
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QProgressBar, QFileDialog, QMessageBox, QListWidget, QListWidgetItem

# Third-party libraries for document processing and OCR
import fitz  # PyMuPDF
from PIL import Image
import pytesseract

# Application-specific imports
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from main_win.chat_interface import ChatInterface


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


class ProfileConfig(QDialog):
    """The ProfileConfig class, derived from QDialog, encapsulates functionalities for managing and configuring user profiles within a GUI application, possibly for a chat interface or document management system. """
    def __init__(self, parent=None, current_profile=None):
        super().__init__(parent)
        self.current_profile = current_profile
        self.setWindowTitle("Configuration")
        self.setGeometry(600, 300, 400, 300)
        self.setupUI()
        self.loadDocuments()
        self.chat_interface = ChatInterface(current_profile)
        api_key = self.chat_interface.loadApiKey()
        os.environ["OPENAI_API_KEY"] = api_key

    def setupUI(self):
        layout = QVBoxLayout(self)

        self.documentListWidget = QListWidget()
        layout.addWidget(self.documentListWidget)

        self.uploadButton = QPushButton("Upload Document")
        self.uploadButton.clicked.connect(self.uploadDocument)
        layout.addWidget(self.uploadButton)

        # Finalize selection button setup
        self.finalizeSelectionButton = QPushButton("Finalize Selection")
        self.finalizeSelectionButton.clicked.connect(self.finalizeDocumentSelection)
        layout.addWidget(self.finalizeSelectionButton)

        self.progressBar = QProgressBar()
        layout.addWidget(self.progressBar)

    def uploadDocument(self):
        # Check if there's a currently loaded profile
        if not self.current_profile:
            # Show a warning message if no profile is loaded
            QMessageBox.warning(self, "No Profile Loaded", "Please load or create a profile before uploading documents.")
            return  # Exit the method if no profile is loaded

        # Open a file dialog for the user to select a document to upload
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Document", "", "PDF Files (*.pdf);;Text Files (*.txt);;All Files (*)")

        # If a file was selected (file_path is not empty)
        if file_path:
            # Call the method to process the selected file and store it in user data storage
            self.userDataStorage(file_path)

    def userDataStorage(self, file_path):
        # Construct the path to the data storage directory for the current profile
        data_store_path = os.path.join(
            os.path.dirname(__file__), '..', '..', '..', 
            'profiles', self.current_profile, 'user_data_storage'
        )

        # Ensure the data storage directory exists; create it if it doesn't
        os.makedirs(data_store_path, exist_ok=True)

        # Extract the base filename from the original file path and change its extension to .txt
        base_filename = f"{os.path.splitext(os.path.basename(file_path))[0]}.txt"

        # Set the destination file path within the data store directory
        dest_file_path = os.path.join(data_store_path, base_filename)

        # Initialize a Worker thread for processing the uploaded document
        self.worker = Worker(file_path, dest_file_path)

        # Connect signals from the Worker to update the progress bar and handle the upload's completion
        self.worker.progress_updated.connect(self.progressBar.setValue)  # Update the progress bar as the Worker reports progress
        self.worker.finished.connect(self.onUploadFinished)  # Handle the completion of the upload process

        # Start the Worker thread to process the document
        self.worker.start()

    def onUploadFinished(self, dest_file_path):
        # Notify the user that the document has been processed and saved
        QMessageBox.information(self, "Upload Finished", f"Document processed and saved to {dest_file_path}")

        # Extract the base name of the document for labeling
        document_label, _ = os.path.splitext(os.path.basename(dest_file_path))
        # Determine the directory where the document is saved
        directory_path = os.path.dirname(dest_file_path)
        # Specify a temporary processing subfolder within that directory
        subfolder_path = os.path.join(directory_path, "temp_processing")

        # Ensure the temporary processing subfolder exists
        os.makedirs(subfolder_path, exist_ok=True)

        # Temporarily move the file to the subfolder for further processing
        temp_file_path = shutil.move(dest_file_path, subfolder_path)

        # Load the document from the temporary subfolder for querying
        file_for_query = SimpleDirectoryReader(input_dir=subfolder_path).load_data()
        # Initialize a vector query engine with the loaded document
        vector_query_engine = VectorStoreIndex.from_documents(file_for_query, use_async=True).as_query_engine()
        # Perform a query to generate a brief description of the document
        response = vector_query_engine.query("Please provide a brief description of this document in 200 words or less.")

        # Construct a dictionary with the document label and its generated description
        description_data = {document_label: str(response)}

        # Determine the path for a JSON file to store descriptions in the original directory
        json_file_path = os.path.join(directory_path, 'descriptions.json')

        # Load existing descriptions from the JSON file, if it exists, and update with the new description
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as file:
                data = json.load(file)
            data.update(description_data)
        else:
            data = description_data

        # Write the updated descriptions back to the JSON file
        with open(json_file_path, 'w') as file:
            json.dump(data, file, indent=4)

        # Move the processed file back to its original location
        shutil.move(temp_file_path, dest_file_path)

        # Refresh the list of documents to reflect any updates
        self.loadDocuments()

    def loadDocuments(self):
        # Clear the document list widget to refresh the list of documents
        self.documentListWidget.clear()

        # Construct the path to the data storage directory for the current profile
        data_store_path = os.path.join(
            os.path.dirname(__file__), '..', '..', '..', 
            'profiles', self.current_profile, 'user_data_storage'
        )

        # Check if the data storage directory exists
        if os.path.exists(data_store_path):
            # Iterate over each file in the data storage directory
            for filename in os.listdir(data_store_path):
                # Create a new list widget item for each document
                item = QListWidgetItem(filename)
                
                # Enable the item to be checkable by setting the appropriate flag
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                
                # Set the initial state of the item to unchecked
                item.setCheckState(Qt.Unchecked)
                
                # Add the item to the document list widget
                self.documentListWidget.addItem(item)

    def selectedDocs(self):
        # Initialize an empty list to hold the full paths of selected documents
        checked_items = []

        # Construct the base path to the user data storage directory
        data_store_path = os.path.join(
            os.path.dirname(__file__), '..', '..', '..', 
            'profiles', self.current_profile, 'user_data_storage'
        )

        # Iterate over each item in the document list widget
        for index in range(self.documentListWidget.count()):
            item = self.documentListWidget.item(index)  # Retrieve the item at the current index
            
            # Check if the item is selected (checked)
            if item.checkState() == Qt.Checked:
                # Construct the full path to the selected document
                full_path = os.path.join(data_store_path, item.text())
                # Add the full path of the selected document to the list
                checked_items.append(full_path)

        # Pass the list of selected documents' paths to be copied or further processed
        self.copy_selected_files(checked_items)

    def copy_selected_files(self, selected_docs_paths):
        # Define the target directory for selected files within the current profile's data storage
        target_directory = os.path.join(
            os.path.dirname(__file__), '..', '..', '..', 
            'profiles', self.current_profile, 'user_data_storage', 'selected_files'
        )
        
        # Ensure the target directory exists, creating it if necessary
        os.makedirs(target_directory, exist_ok=True)

        # Extract the base filenames of the selected documents to manage file presence in the target directory
        selected_filenames = {os.path.basename(path) for path in selected_docs_paths}

        # Copy each selected document to the target directory
        for file_path in selected_docs_paths:
            filename = os.path.basename(file_path)
            dest_path = os.path.join(target_directory, filename)
            shutil.copy2(file_path, dest_path)  # copy2 is used to preserve file metadata

        # Remove any files in the target directory that were not selected
        for filename in os.listdir(target_directory):
            if filename not in selected_filenames:
                os.remove(os.path.join(target_directory, filename))

        # Define the path to the source JSON file containing document descriptions
        source_json_path = os.path.join(
            os.path.dirname(__file__), '..', '..', '..', 
            'profiles', self.current_profile, 'user_data_storage', 'descriptions.json'
        )

        # Synchronize the metadata from the source JSON file to the selected files in the target directory
        self.sync_json_metadata_to_selected_files(source_json_path, target_directory)

    def sync_json_metadata_to_selected_files(self, source_json_path, selected_files_folder):
        # Check if the source JSON file exists
        if not os.path.exists(source_json_path):
            print(f"Source JSON file not found: {source_json_path}")
            return

        # Load data from the source JSON file
        with open(source_json_path, 'r') as file:
            data = json.load(file)

        # Create a set of selected filenames without their extensions
        selected_filenames_no_ext = {
            os.path.splitext(filename)[0] for filename in os.listdir(selected_files_folder)
        }

        # Filter the data to include only entries that match the selected filenames
        selected_data = {
            filename: desc for filename, desc in data.items() 
            if filename in selected_filenames_no_ext
        }

        # Define the path for the target JSON file within the selected files folder
        target_json_path = os.path.join(selected_files_folder, 'selected_descriptions.json')

        # Write the filtered metadata to the target JSON file
        with open(target_json_path, 'w') as file:
            json.dump(selected_data, file, indent=4)

    def finalizeDocumentSelection(self):
        # This method will be called when the "Finalize Selection" button is clicked
        # It can call selectedDocs, which processes and copies the selected documents
        self.selectedDocs()

        # Optional: Provide feedback to the user or further actions after selection
        QMessageBox.information(self, "Selection Finalized", "You can now chat with the selected documents!")

class Worker(QThread):
    """The Worker class, inheriting from QThread, is designed to perform document processing in a separate thread, converting document pages to images and then extracting text using Optical Character Recognition (OCR) with PyTesseract."""
    progress_updated = Signal(int)
    finished = Signal(str)

    def __init__(self, file_path, dest_file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path  # Path to the source document
        self.dest_file_path = dest_file_path  # Path where the extracted text will be saved

    def run(self):
        # Open the source document using PyMuPDF
        doc = fitz.open(self.file_path)
        content = ''  # Initialize an empty string to accumulate extracted text

        total_pages = len(doc)  # Get the total number of pages in the document

        # Iterate over each page in the document
        for page_num in range(total_pages):
            page = doc.load_page(page_num)  # Load the current page
            pix = page.get_pixmap()  # Render the page as a pixmap (image)
            
            # Convert the pixmap to a PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Use PyTesseract to perform OCR on the image and extract text
            content += pytesseract.image_to_string(img)
            
            # Emit a signal to update the progress based on the current page number
            self.progress_updated.emit(int((page_num + 1) / total_pages * 100))

        # Write the accumulated text content to the destination file
        with open(self.dest_file_path, 'w', encoding='utf-8') as outfile:
            outfile.write(content)

        doc.close()  # Close the document to free resources

        # Emit a signal indicating that the processing is finished, along with the destination path
        self.finished.emit(self.dest_file_path)
