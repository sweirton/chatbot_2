import os
from PySide6.QtWidgets import QInputDialog, QMessageBox
from dotenv import dotenv_values

class ProfileManager:
    def __init__(self, parent=None):
        self.parent = parent

    def create_profile(self, profile_name):
        if not profile_name:
            QMessageBox.warning(self.parent, "Invalid Profile Name", "Profile name cannot be empty.")
            return

        profile_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'profiles', profile_name)
        user_data_dir = os.path.join(profile_dir, 'user_data_storage')

        # Create directories if they don't exist
        os.makedirs(user_data_dir, exist_ok=True)

        # Create tokens directory
        user_tokens_dir = os.path.join(profile_dir, 'tokens')
        os.makedirs(user_tokens_dir, exist_ok=True)

        # Prompt for API Key
        api_key, ok = QInputDialog.getText(self.parent, 'API Key', 'Enter your API Key:')
        self.token_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'profiles', profile_name, 'tokens')
        if ok and api_key:
            env_path = os.path.join(self.token_dir, 'api_info.env')
            with open(env_path, 'w') as file:
                file.write(f'API_KEY="{api_key}"\n')
            QMessageBox.information(self.parent, 'Profile Created', f'Profile "{profile_name}" created successfully.\nAPI Key stored in {env_path}')
        else:
            QMessageBox.warning(self.parent, 'No API Key', 'No API Key was provided. Profile creation aborted.')

    def load_profile(self, profile_name):
        profile_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'profiles', profile_name)
        env_path = os.path.join(profile_dir, 'api_info.env')

        if not os.path.exists(env_path):
            QMessageBox.warning(self.parent, 'API Key Not Found', f'The API Key for profile "{profile_name}" is missing.')
            return None

        profile_env = dotenv_values(env_path)
        return profile_env.get('API_KEY', '').strip('"')
