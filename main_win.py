from PySide6.QtWidgets import QMainWindow, QHBoxLayout, QWidget, QApplication
from .chat_interface import ChatInterface
from .history_interface import ChatHistoryWidget
from .options_menu import OptionsMenu
from menu_bar_options.options.profile_config import ProfileConfig

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

        # Center the app on screen
        self.centerWindow()

        # Initialize menu bar
        self.initializeMenuBar()

        # Signal from history widget selection
        self.chat_history_widget.sessionSelected.connect(self.chat_interface.loadChatSession)

        # Connect the profileConfigWindowSignal signal to the openProfileConfig slot
        self.optionsMenu.profileConfigWindowSignal.connect(self.openProfileConfig)
        
        self.optionsMenu.loadProfileSignal.connect(self.onProfileLoaded)
        self.optionsMenu.createProfileSignal.connect(self.onProfileCreate)

        self.chat_history_widget.sessionCreated.connect(self.onSessionCreated)

    def centerWindow(self):
        # Positions window based off of current screen dimensions
        screen = QApplication.primaryScreen().geometry()
        x = int((screen.width() - self.width()) / 2)
        y = int((screen.height() - self.height()) / 2 - 100)
        self.move(x, y)

    def initializeMenuBar(self):
        # Initialize and set up the menu bar
        self.optionsMenu = OptionsMenu(self)
        self.setMenuBar(self.optionsMenu.menubar)

    def openProfileConfig(self):
        self.profileConfigWindow = ProfileConfig(parent=self, current_profile=self.profile_name)
        self.profileConfigWindow.show()

    def onProfileLoaded(self, profile_name):
        # Update the interface to reflect name change
        self.nameChange(profile_name)
        self.chat_history_widget.selectRecentSession()

    def onProfileCreate(self, profile_name):
        # Update the interface to reflect name change
        self.nameChange(profile_name)

    def nameChange(self, profile_name):
        self.profile_name = profile_name
        self.chat_history_widget.updateProfileName(profile_name)
        self.chat_interface = ChatInterface(profile_name)
    
    def onSessionCreated(self):
        # Set the user input focus when creating a new session
        self.chat_interface.setFocusToUserInput()
