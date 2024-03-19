from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton
from PySide6.QtCore import QThread, Signal, QTimer
from dotenv import dotenv_values
from datetime import datetime
import json
import requests
import os
import glob


class ChatInterface(QWidget):
    def __init__(self, profile_name):
        super().__init__()

        # Layout to organize widgets vertically
        layout = QVBoxLayout()

        # Text edit for displaying chat history, read-only
        self.chat_message_box = QTextEdit(styleSheet="background-color: #F5F5F5; border: none;")
        self.chat_message_box.setReadOnly(True)

        # Line edit for typing new messages
        self.user_input = QLineEdit()
        self.user_input.setStyleSheet("font-size: 14px;")
        self.user_input.setPlaceholderText("Type your message here...")
        
        # Send button
        self.user_input_send_btn = QPushButton("Send")
        self.user_input_send_btn.clicked.connect(self.prepareMessage)
        self.user_input.returnPressed.connect(self.prepareMessage)
        QTimer.singleShot(100, lambda: self.user_input.setFocus())  # set a timer for the focus because it wouldn't position automatically.

        # Add widgets to the layout
        layout.addWidget(self.chat_message_box)
        layout.addWidget(self.user_input)
        layout.addWidget(self.user_input_send_btn)

        # Set the layout for this widget
        self.setLayout(layout)

        # Initialize LLM API
        self.conversation_history = []
        self.profile_name = profile_name
        self.api_key = self.loadAPIKey()
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        self.api_url = "https://api.openai.com/v1/chat/completions"

        # Profile directories
        self.history_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'profiles', self.profile_name, 'chat_history')

        # Ensure the history directory exist
        os.makedirs(self.history_dir, exist_ok=True)

        # Load or create a session file automatically after all setup is complete
        self.session_file = self.loadSessionFile()

    def loadAPIKey(self):
        self.token_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'profiles', self.profile_name, 'tokens')
        env_path = os.path.join(self.token_dir, 'api_info.env')
        if not os.path.exists(env_path):
            raise FileNotFoundError(f"API key file not found for profile {self.profile_name}")
        profile_env = dotenv_values(env_path)
        if api_key := profile_env.get('API_KEY', '').strip('"'):
            return api_key
        else:
            raise ValueError(f"No API key found in {env_path}")

    def prepareMessage(self):
        if user_message := self.user_input.text().strip():
            self.displayMessage("user", user_message)
            self.user_input.clear()
            self.conversation_history.append({"role": "user", "content": user_message})
            self.worker = ChatWorker(self.api_url, self.headers, self.conversation_history)
            self.worker.finished.connect(self.displayResponse)
            self.worker.start()

    def displayResponse(self, response):
        # Directly call displayMessage for the assistant's response
        self.displayMessage("assistant", response)

        # Append the assistant's response to the conversation history
        self.conversation_history.append({"role": "assistant", "content": response})
        self.writeToStorage()

    def displayMessage(self, role, message):
        # Customize the styling based on the role (user or assistant)
        if role == "user":
            message_html = f'<div style="font-size: 16px; color: blue; margin: 2px; padding: 10px;"><b>You</b><br>{message}</div><br>'
        else:  # For any other role, assume assistant for now
            message_html = f'<div style="font-size: 16px; color: green; margin: 2px; padding: 10px;"><b>Digital Assistant</b><br>{message}</div><br>'

        # Append the stylized HTML message to the chat_message_box
        self.chat_message_box.append(message_html)

    def loadSessionFile(self):
        if session_files := glob.glob(os.path.join(self.history_dir, '*.json')):
            # Sort the files by their modification time, newest first
            session_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            latest_session_file = session_files[0]
            print(f"Latest session found: {latest_session_file}")
            return latest_session_file
        else:
            # No session files found, create a new one
            new_session_name = self.genSessionName()
            new_session_file_path = os.path.join(self.history_dir, f'{new_session_name}.json')

            # Create an empty JSON file for the new session
            with open(new_session_file_path, 'w') as f:
                f.write("{}")

            print(f"New session file created: {new_session_file_path}")
            return new_session_file_path

    def genSessionName(self):
        # Your existing method to generate a session name
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        return f"{self.profile_name}_Session_{timestamp}"

    def writeToStorage(self):
        # Define the file path for storing this session's chat history
        chat_file_path = os.path.join(self.history_dir, self.session_file)

        # Write the conversation history to the file
        with open(chat_file_path, 'a', encoding='utf-8') as file:
            json.dump(self.conversation_history, file, ensure_ascii=False, indent=4)
        
class ChatWorker(QThread):
    finished = Signal(str)

    def __init__(self, api_url, headers, conversation_history):
        super().__init__()
        self.api_url = api_url
        self.headers = headers
        self.conversation_history = conversation_history

    def run(self):
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": self.conversation_history,
            "max_tokens": 1000,
            "temperature": 0.7
        }
        response = requests.post(self.api_url, headers=self.headers, json=payload)
        try:
            response_data = response.json()
            if not response_data.get('choices'):
                self.finished.emit("I'm sorry, I couldn't process that request.")
                return
            bot_response = response_data['choices'][0].get('message', {}).get('content', '').strip()
            self.finished.emit(bot_response)
        except Exception as e:
            self.finished.emit(f"Error processing the API response: {e}")

