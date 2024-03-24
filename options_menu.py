# options_menu_ui.py

from PySide6.QtWidgets import QMenuBar, QInputDialog
from PySide6.QtGui import QAction
from PySide6.QtCore import Signal, QObject
from menu_bar_options.options.profile_manager import ProfileManager


class OptionsMenu(QObject):
    loadProfileSignal = Signal(str)
    createProfileSignal = Signal(str)
    profileConfigWindowSignal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.profileManager = ProfileManager(parent=self.parent)
        self.setupUI()

    def setupUI(self):
        self.menubar = QMenuBar(self.parent)
        optionsMenu = self.menubar.addMenu('Options')

        loadProfileAction = QAction('Load Profile', self.parent)
        loadProfileAction.triggered.connect(self.onLoadProfile)
        optionsMenu.addAction(loadProfileAction)

        createProfileAction = QAction('Create Profile', self.parent)
        createProfileAction.triggered.connect(self.onCreateProfile)
        optionsMenu.addAction(createProfileAction)

        profileConfigAction = QAction('Configuration', self.parent)
        profileConfigAction.triggered.connect(self.onprofileConfigWindow)
        optionsMenu.addAction(profileConfigAction)

    def onLoadProfile(self):
        profile_name, ok = QInputDialog.getText(self.parent, 'Load Profile', 'Enter your profile name:')
        if ok and profile_name:
            self.loadProfileSignal.emit(profile_name)

    def onCreateProfile(self):
        profile_name, ok = QInputDialog.getText(self.parent, 'Create Profile', 'Enter a new profile name:')
        if ok and profile_name:
            self.profileManager.create_profile(profile_name)
            self.createProfileSignal.emit(profile_name)

    def onprofileConfigWindow(self):
        self.profileConfigWindowSignal.emit()
