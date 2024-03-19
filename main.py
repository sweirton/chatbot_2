from PySide6.QtWidgets import QApplication
from main_win.main_win import MainWindow
from login_win import login_interface

def main():
    app = QApplication([])

    loginWindow = login_interface.LoginWindow()
    if loginWindow.exec():  # Show the login window and wait
        if profile_name := loginWindow.profile_name:
            mainWindow = MainWindow(profile_name)

            mainWindow.show()
            app.exec()
        else:
            print("No profile selected, exiting.")
    else:
        # Handle the case where the login window is closed without logging in
        print("Login was cancelled.")

if __name__ == "__main__":
    main()