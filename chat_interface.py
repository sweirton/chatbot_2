from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton
from PySide6.QtCore import QThread, Signal, QTimer
from dotenv import dotenv_values
from datetime import datetime
import json
import requests
import os


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

        # Used for writing to the current session file
        self.current_session_file_path = None

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
            self.writeToStorage()  # Write the conversation history including the user's message to storage
            current_session_data = self.readCurrentSessionData()
            self.worker = ChatWorker(self.api_url, self.headers, current_session_data, {"role": "user", "content": user_message})
            self.worker.finished.connect(self.realtimeResponse)
            self.worker.start()

    def realtimeResponse(self, response):
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

    def genSessionName(self):
        # Generate a session name using data-time
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        return f"{self.profile_name}_Session_{timestamp}"

    def writeToStorage(self):
        # Initialize session file path if not set
        if not self.current_session_file_path:
            self.current_session_file_path = os.path.join(
                self.history_dir, f"{self.genSessionName()}.json"
            )

        # Combine existing and new conversation history
        try:
            with open(self.current_session_file_path, 'r', encoding='utf-8') as file:
                session_messages = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            session_messages = []

        session_messages.extend(self.conversation_history)

        # Write combined history to the session file
        with open(self.current_session_file_path, 'w', encoding='utf-8') as file:
            json.dump(session_messages, file, ensure_ascii=False, indent=4)

        # Clear the local conversation history after it's been saved
        self.conversation_history.clear()

    def loadChatSession(self, session_file_path):
        self.current_session_file_path = session_file_path  # Store the current session file path
        
        # Open and read the session file
        with open(session_file_path, 'r', encoding='utf-8') as file:
            # Read the session data as a string
            session_data = json.load(file)

        # Clear the chat window before loading the new session
        self.chat_message_box.clear()

        # Iterate through each message in the session
        for message in session_data:
            role = message.get("role")
            content = message.get("content")
            if role and content:
                # Use the displayMessage method to format and append each message
                self.displayMessage(role, content)

    def readCurrentSessionData(self):
        # This is used to append past conversation history to current chat for LLM's conversational context
        try:
            with open(self.current_session_file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            print(f"Error reading session data: {e}")
            return []

class ChatWorker(QThread):
    finished = Signal(str)

    def __init__(self, api_url, headers, session_messages, new_message):
        super().__init__()
        self.api_url = api_url
        self.headers = headers
        self.session_messages = session_messages + [new_message]

    def run(self):
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": self.session_messages,
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
