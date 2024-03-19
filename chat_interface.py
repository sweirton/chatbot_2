from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton

class ChatInterface(QWidget):
    def __init__(self):
        super().__init__()

        # Layout to organize widgets vertically
        layout = QVBoxLayout()

        # Text edit for displaying chat history, read-only
        self.chat_message_box = QTextEdit(styleSheet="background-color: #F5F5F5; border: none;")
        self.chat_message_box.setReadOnly(True)

        # Line edit for typing new messages
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Type your message here...")

        # Send button
        self.user_input_send_btn = QPushButton("Send")
        self.user_input_send_btn.clicked.connect(self.sendMessage)
        self.user_input.returnPressed.connect(self.sendMessage)

        # Add widgets to the layout
        layout.addWidget(self.chat_message_box)
        layout.addWidget(self.user_input)
        layout.addWidget(self.user_input_send_btn)

        # Set the layout for this widget
        self.setLayout(layout)

    def sendMessage(self):
        if message := self.user_input.text().strip():
            self.chat_message_box.append(message)
            self.user_input.clear()
