# Standard library imports
from datetime import datetime
import json
import os

# Third-party imports
from dotenv import dotenv_values
import requests
from PySide6.QtCore import QThread, Signal, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton

# Local application/library specific imports
from guidance.models import OpenAI as GuidanceOpenAI
from llama_index.core import QueryBundle, SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.question_gen.guidance import GuidanceQuestionGenerator


class ChatInterface(QWidget):
    """ the ChatInterface class encapsulates the functionality required for a chat interface, including user input handling, message display, session management, and integration with external APIs for message processing. It's designed to provide a user-friendly interface for textual interaction within an application"""
    def __init__(self, profile_name):
        super().__init__()

        layout = QVBoxLayout()

        self.chat_message_box = QTextEdit(styleSheet="background-color: #F5F5F5; border: none;")
        self.chat_message_box.setReadOnly(True)

        self.user_input = QLineEdit()
        self.user_input.setStyleSheet("font-size: 14px;")
        self.user_input.setPlaceholderText("Type your message here...")
        
        self.user_input_send_btn = QPushButton("Send")
        self.user_input_send_btn.clicked.connect(self.prepareMessage)
        self.user_input.returnPressed.connect(self.prepareMessage)
        QTimer.singleShot(100, lambda: self.user_input.setFocus())

        layout.addWidget(self.chat_message_box)
        layout.addWidget(self.user_input)
        layout.addWidget(self.user_input_send_btn)

        self.setLayout(layout)

        self.conversation_history = []
        self.profile_name = profile_name
        self.api_key = self.loadApiKey()
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        self.api_url = "https://api.openai.com/v1/chat/completions"

        self.history_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'profiles', self.profile_name, 'chat_history')

        os.makedirs(self.history_dir, exist_ok=True)

        self.current_session_file_path = None

        self.query_handler = self.createQueryHandler()

        self.messages_html = []  # Initialize a list to keep track of message HTML segments

    def createQueryHandler(self):
        # Configure the directory path for selected files
        selected_files_directory = os.path.join(
            os.path.dirname(__file__), 
            '..', '..', 
            'profiles', 
            self.profile_name, 
            'user_data_storage', 
            'selected_files'
        )

        # Initialize variables for selected documents and acceptable extensions
        # These can be set based on your application's requirements
        selected_documents = []
        acceptable_extensions = None

        # Create and return a new QueryHandler instance
        return QueryHandler(
            selected_files_directory=selected_files_directory,
            selected_documents=selected_documents,
            acceptable_extensions=acceptable_extensions,
            profile_name=self.profile_name,
            api_url=self.api_url,
            headers=self.headers
        )

    def loadApiKey(self):
        # Configure the directory and path for the API key file
        token_dir = os.path.join(
            os.path.dirname(__file__), 
            '..', '..', 
            'profiles', 
            self.profile_name, 
            'tokens'
        )
        env_path = os.path.join(token_dir, 'api_info.env')

        # Validate the existence of the API key file
        if not os.path.exists(env_path):
            raise FileNotFoundError(f"API key file not found for profile {self.profile_name}")

        # Load environment variables from the .env file
        profile_env = dotenv_values(env_path)

        # Retrieve and validate the API key
        api_key = profile_env.get('API_KEY', '').strip('"')
        if not api_key:
            raise ValueError(f"No API key found in {env_path}")

        # Set the API key in the environment variables
        os.environ["OPENAI_API_KEY"] = api_key

        # Return the API key
        return api_key

    def prepareMessage(self):
        if user_message := self.user_input.text().strip():
            # Display the user's message in the chat interface
            self.displayMessage("user", user_message)

            # Clear the input field for the next message
            self.user_input.clear()

            # Append the message to the conversation history
            self.conversation_history.append({"role": "user", "content": user_message})

            # Persist the updated conversation history
            self.writeToStorage()

            # Display the "Thinking..." message
            self.displayMessage("assistant", "Thinking...", replace_last=False)
            
            # Initialize a background worker for processing the message
            self.worker = ChatWorker(self.query_handler, self.conversation_history, {"role": "user", "content": user_message})

            # Connect the worker's completion signal to the method for handling responses
            self.worker.finished.connect(self.realtimeResponse)

            # Start the background worker
            self.worker.start()

    def realtimeResponse(self, response):
        # Display the assistant's response in the chat interface
        # Replace the "Thinking..." message with the actual response
        self.displayMessage("assistant", response, replace_last=True)

        # Update the conversation history with the assistant's response
        self.conversation_history.append({"role": "assistant", "content": response})

        # Persist the updated conversation history
        self.writeToStorage()

    def displayMessage(self, role, message, replace_last=False):
        # Define message styling based on the sender's role
        if role == "user":
            color = "blue"
            sender = "You"
        elif role == "assistant":
            color = "green"
            sender = "Digital Assistant"
        else:
            color = "gray"  # Default color for undefined roles
            sender = "Unknown"

        # Construct the HTML for the message
        message_html = f'''
        <div style="font-size: 16px; color: {color}; margin: 2px; padding: 10px;">
            <b>{sender}</b><br>{message}
        </div><br>'''

        if replace_last and self.messages_html:
            # Replace the last message HTML with the new one
            self.messages_html[-1] = message_html
        else:
            # Append the new message HTML to the list
            self.messages_html.append(message_html)

        # Join all message HTML segments and set it as the content of the chat_message_box
        self.chat_message_box.setHtml(''.join(self.messages_html))

        # Scroll to the bottom of the chat_message_box to ensure the latest message is visible
        self.chat_message_box.verticalScrollBar().setValue(self.chat_message_box.verticalScrollBar().maximum())

    def genSessionName(self):
        # Get the current datetime
        now = datetime.now()

        # Format the current datetime as a timestamp string
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        # Construct and return the session name using the profile name and the timestamp
        return f"{self.profile_name}_Session_{timestamp}"

    def writeToStorage(self):
        # Initialize the session file path if it hasn't been set
        if not self.current_session_file_path:
            # Generate a new session name and construct the file path
            self.current_session_file_path = os.path.join(
                self.history_dir, f"{self.genSessionName()}.json"
            )

        # Attempt to load existing messages from the session file
        try:
            with open(self.current_session_file_path, 'r', encoding='utf-8') as file:
                session_messages = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            # If the file doesn't exist or the content is not valid JSON, start with an empty list
            session_messages = []

        # Append the current conversation history to the loaded messages
        session_messages.extend(self.conversation_history)

        # Write the updated message list back to the session file
        with open(self.current_session_file_path, 'w', encoding='utf-8') as file:
            json.dump(session_messages, file, ensure_ascii=False, indent=4)

        # Clear the in-memory conversation history after it's been persisted
        self.conversation_history.clear()

    def loadChatSession(self, session_file_path):
        # Update the current session file path
        self.current_session_file_path = session_file_path

        # Load the session data from the specified file
        try:
            with open(session_file_path, 'r', encoding='utf-8') as file:
                session_data = json.load(file)
        except Exception as e:
            print(f"Failed to load chat session: {e}")
            return

        # Clear the chat interface to prepare for loading the session messages
        self.chat_message_box.clear()

        # Iterate over each message in the loaded session data
        for message in session_data:
            # Extract the role and content for each message
            role = message.get("role")
            content = message.get("content")

            # Display the message in the chat interface if both role and content are available
            if role and content:
                self.displayMessage(role, content)

        # After loading and displaying the session messages:
        self.chat_message_box.verticalScrollBar().setValue(self.chat_message_box.verticalScrollBar().maximum())

    def readCurrentSessionData(self):
        # Ensure there is a session file path set
        if not self.current_session_file_path:
            print("No current session file path set.")
            return []

        # Attempt to read and parse the session data from the file
        try:
            with open(self.current_session_file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Session file not found: {self.current_session_file_path}")
        except json.JSONDecodeError:
            print(f"Invalid JSON format in session file: {self.current_session_file_path}")
        except Exception as e:
            print(f"Error reading session data: {e}")

        # Return an empty list in case of any errors
        return []

    def setFocusToUserInput(self):
        # Makes it so the user can start typing without selecting the input text field.
        self.user_input.setFocus()


class ChatWorker(QThread):
    """The ChatWorker class encapsulates the asynchronous processing of chat messages, leveraging the capabilities of QThread to perform potentially time-consuming operations, such as API calls or complex logic, without blocking the main application UI. It communicates the results of its processing back to the main thread via signals, allowing for a responsive and interactive user experience in chat applications."""
    finished = Signal(str)

    def __init__(self, query_handler, session_messages, new_message):
        super().__init__()
        self.query_handler = query_handler
        self.session_messages = session_messages + [new_message]  # Combine session messages with the new message
        self.new_message = new_message  # Store the new message separately

    def run(self):
        # Attempt to process the new message using the query handler
        try:
            # Extract the content of the new message
            query = self.new_message.get('content', '').strip()

            # Pass the query and session messages to the query handler for processing
            response_data = self.query_handler.handleQuery(query=query, session_messages=self.session_messages)

            # Check if the response contains valid data
            if 'choices' not in response_data or not response_data['choices']:
                # Emit a signal indicating the request could not be processed
                self.finished.emit("I'm sorry, I couldn't process that request.")
                return

            # Extract and emit the bot's response
            bot_response = response_data['choices'][0].get('message', {}).get('content', '').strip()
            self.finished.emit(bot_response)

        except Exception as e:
            # Emit a signal indicating an error occurred during processing
            self.finished.emit(f"Error processing the response: {e}")


class ToolMetadataCreation:
    """The ToolMetadataCreation class serves as a utility for loading, representing, and transforming metadata about tools or modules within the application. It provides a clear separation between the raw metadata (as might be stored in JSON files or similar) and the application's internal representation of such metadata, facilitating ease of use, better organization, and potential reusability of the metadata handling logic. This class could be particularly useful in applications that involve dynamic loading or utilization of various processing tools, plugins, or modules, where maintaining a clear and consistent representation of each tool's capabilities and characteristics is important."""
    def __init__(self, name, description):
        self.name = name
        self.description = description

    @staticmethod
    def loadToolsFromJson(json_file_path):
        tools = []
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as file:
                data = json.load(file)
                # Create an instance of ToolMetadataCreation for each tool in the JSON file
                tools.extend(
                    ToolMetadataCreation(name=key, description=value)
                    for key, value in data.items()
                )
        else:
            print(f"File not found: {json_file_path}")
        return tools

    def toToolMetadata(self):
        # Convert this instance's properties into a ToolMetadata object
        return ToolMetadata(name=self.name, description=self.description)


class QueryHandler:
    """The QueryHandler class encapsulates the logic for processing user queries in a flexible and dynamic manner, capable of leveraging both local document resources and external AI services. It demonstrates a thoughtful architecture that accommodates a range of processing strategies, from local document indexing and search to sophisticated AI-driven query understanding and response generation. This design allows for scalable and context-aware query handling within applications that require dynamic information retrieval and processing capabilities."""
    def __init__(self, selected_files_directory, selected_documents, acceptable_extensions, profile_name, api_url, headers):
        self.selected_files_directory = selected_files_directory
        self.selected_documents = selected_documents
        self.acceptable_extensions = acceptable_extensions
        self.current_profile = profile_name
        self.api_url = api_url
        self.headers = headers

    def queryAvailableFiles(self):
        # Check if the selected files directory exists
        if not os.path.exists(self.selected_files_directory):
            print(f"Directory {self.selected_files_directory} does not exist.")
            return False
        
        # Check for the presence of relevant files (ignoring JSON files and subdirectories)
        for filename in os.listdir(self.selected_files_directory):
            file_path = os.path.join(self.selected_files_directory, filename)
            
            # Check if the file is not a directory and does not have a JSON extension
            if os.path.isfile(file_path) and not filename.endswith('.json'):
                return True  # A relevant file is found, no need to check further
    
        return False  # No relevant files were found
    
    def processQueryWithLlamaIndex(self, query):
        # Path to the JSON file containing metadata about the selected files
        selected_files_metadata_path = os.path.join(self.selected_files_directory, 'selected_descriptions.json')

        # Load tool metadata from the JSON file
        tools_metadata = ToolMetadataCreation.loadToolsFromJson(selected_files_metadata_path)

        # Convert the loaded tool metadata into a different format, if necessary
        converted_tools_metadata = [tm.toToolMetadata() for tm in tools_metadata]

        # Initialize a list to hold the query engine tools
        query_engine_tools = []

        # Iterate over files in the selected directory, skipping JSON files
        for filename in os.listdir(self.selected_files_directory):
            if filename.endswith(".json"):
                continue

            # Construct the full path to the file and read its content
            full_path = os.path.join(self.selected_files_directory, filename)
            document_content = SimpleDirectoryReader(input_files=[full_path]).load_data()

            # Create a query engine index from the document content
            document_index = VectorStoreIndex.from_documents(document_content).as_query_engine(similarity_top_k=3)

            # Find the corresponding tool metadata for the current file
            filename_without_extension = os.path.splitext(filename)[0]
            for tm in tools_metadata:
                if tm.name == filename_without_extension:
                    tool_metadata_converted = tm.toToolMetadata()

                    # Create a query engine tool with the document index and tool metadata
                    query_engine_tool = QueryEngineTool(query_engine=document_index, metadata=tool_metadata_converted)

                    # Add the query engine tool to the list
                    query_engine_tools.append(query_engine_tool)
                    break

        # Initialize the question generator with default settings
        question_gen = GuidanceQuestionGenerator.from_defaults(guidance_llm=GuidanceOpenAI(model="gpt-3.5-turbo"), verbose=False)

        # Generate sub-questions to further analyze or break down the main query
        sub_questions = question_gen.generate(
            tools=converted_tools_metadata,
            query=QueryBundle("Compare and contrast the available documents, and select information relevant to the question asked by the user."),
        )

        # Initialize the sub-question query engine with the generated questions and query engine tools
        s_engine = SubQuestionQueryEngine.from_defaults(question_gen=question_gen, query_engine_tools=query_engine_tools)

        # Execute the query using the sub-question query engine and obtain the response
        response = s_engine.query(query)

        # Return the response in a structured format
        return {'choices': [{'message': {'content': response.response}}]}
    
    def processQueryWithOpenAI(self, session_messages):
        # Prepare the payload for the OpenAI API request
        payload = {
            "model": "gpt-3.5-turbo",  # Specify the OpenAI model to use
            "messages": session_messages,  # Include the session messages for context
            "max_tokens": 1000,  # Set the maximum length of the model's response
            "temperature": 0.7  # Control the randomness of the model's response
        }

        # Send the request to the OpenAI API and capture the response
        response = requests.post(self.api_url, headers=self.headers, json=payload)

        # Return the parsed JSON response
        return response.json()

    def handleQuery(self, query, session_messages):
        # Check if there are local files available for processing the query
        if self.queryAvailableFiles():
            # Process the query using local resources
            return self.processQueryWithLlamaIndex(query)
        else:
            # Fallback to processing the query with OpenAI's API
            return self.processQueryWithOpenAI(session_messages)
