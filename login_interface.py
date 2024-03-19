from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QLineEdit, QMessageBox, QSpacerItem, QSizePolicy, QInputDialog
from PySide6.QtCore import Qt
from PySide6.QtCore import Signal
import os

class LoginWindow(QDialog):
    profileInfoSignal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login")
        self.setGeometry(100, 100, 300, 300)
        self.profile_name = None
        self.setupUI()

    def setupUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 40, 30, 50)

        loginLabel = QLabel("Login")
        loginLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loginLabel.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(loginLabel)

        spacerItem = QSpacerItem(20, 50, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        layout.addItem(spacerItem)

        self.infoLabel = QLabel("Profile Name:")
        self.infoLabel.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.infoLabel)

        self.profileInput = QLineEdit()
        layout.addWidget(self.profileInput)

        layout.addItem(spacerItem)

        self.loginButton = QPushButton("LOGIN")
        self.loginButton.clicked.connect(self.handleLogin)
        self.loginButton.setStyleSheet("QPushButton { border-radius: 10px; padding: 5px; background-color: #EEE; border: 1px solid #AAA; }"
                                        "QPushButton:hover { background-color: #DDD; }"
                                        "QPushButton:pressed { background-color: #BBB; }")

        layout.addWidget(self.loginButton)

    def handleLogin(self):
        profile_name = self.profileInput.text().strip()
        if not profile_name:
            QMessageBox.warning(self, "Login Failed", "Please enter a profile name.")
            return

        profile_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'profiles', profile_name)
        if os.path.exists(profile_dir):
            self._extracted_from_createProfile_9(profile_name)
        else:
            reply = QMessageBox.question(self, "Profile Not Found", "Profile does not exist. Would you like to create a new one? Note: You will need an OpenAI API key to proceed.",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.createProfile(profile_name)

    def createProfile(self, profile_name):
        api_key, ok = QInputDialog.getText(self, "Enter API Key", "Enter your OpenAI API key:")
        if ok and api_key:
            profile_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'profiles', profile_name, 'tokens')
            os.makedirs(profile_dir, exist_ok=True)
            env_path = os.path.join(profile_dir, 'api_info.env')
            with open(env_path, 'w') as file:
                file.write(f'API_KEY="{api_key}"\n')
            QMessageBox.information(self, "Profile Created", f"Profile '{profile_name}' has been created successfully.")
            self._extracted_from_createProfile_9(profile_name)
        else:
            QMessageBox.warning(self, "Profile Creation Failed", "API key is required to create a new profile.")

    # TODO Rename this here and in `handleLogin` and `createProfile`
    def _extracted_from_createProfile_9(self, profile_name):
        self.profile_name = profile_name
        self.accept()
        self.profileInfoSignal.emit(self.profile_name)
