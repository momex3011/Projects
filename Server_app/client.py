import socket
import threading
import customtkinter

class ChatClient(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("LAN Chat Client")
        self.geometry("500x600")

        self.client_socket = None
        self.is_connected = False

        # --- Login Frame ---
        self.login_frame = customtkinter.CTkFrame(self)
        self.login_frame.pack(pady=20, padx=20, fill="both", expand=True)

        self.server_ip_entry = customtkinter.CTkEntry(self.login_frame, placeholder_text="Server IP Address")
        self.server_ip_entry.pack(pady=10)
        self.username_entry = customtkinter.CTkEntry(self.login_frame, placeholder_text="Enter Username")
        self.username_entry.pack(pady=10)
        self.connect_button = customtkinter.CTkButton(self.login_frame, text="Connect", command=self.connect_to_server)
        self.connect_button.pack(pady=10)

        # --- Chat Frame (initially hidden) ---
        self.chat_frame = customtkinter.CTkFrame(self)
        # self.chat_frame will be packed later

        self.chat_display = customtkinter.CTkTextbox(self.chat_frame, state="disabled", wrap="word")
        self.chat_display.pack(pady=10, padx=10, fill="both", expand=True)
        
        self.message_entry = customtkinter.CTkEntry(self.chat_frame, placeholder_text="Type your message...")
        self.message_entry.pack(pady=10, padx=10, fill="x")
        self.message_entry.bind("<Return>", self.send_message) # Bind Enter key
        
        self.send_button = customtkinter.CTkButton(self.chat_frame, text="Send", command=self.send_message)
        self.send_button.pack(pady=10, padx=10)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def connect_to_server(self):
        server_ip = self.server_ip_entry.get()
        self.username = self.username_entry.get()
        if not server_ip or not self.username:
            # You would normally show an error message here
            return

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((server_ip, 12345))
            self.is_connected = True

            # Switch to the chat view
            self.login_frame.pack_forget()
            self.chat_frame.pack(pady=20, padx=20, fill="both", expand=True)
            
            # Start a thread to listen for messages from the server
            receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            receive_thread.start()

        except Exception as e:
            print(f"Error connecting to server: {e}")
            # You would normally show an error message in the GUI

    def receive_messages(self):
        """Receives messages from the server and displays them."""
        while self.is_connected:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if message:
                    self.display_message(message)
            except:
                print("Disconnected from server.")
                self.is_connected = False
                self.client_socket.close()
                break
    
    def send_message(self, event=None): # event=None for button click
        message_text = self.message_entry.get()
        if message_text:
            formatted_message = f"{self.username}: {message_text}"
            self.client_socket.send(formatted_message.encode('utf-8'))
            self.display_message(f"You: {message_text}") # Show your own message
            self.message_entry.delete(0, 'end')

    def display_message(self, message):
        """Safely updates the chat display from any thread."""
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", message + "\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end") # Auto-scroll to the bottom

    def on_closing(self):
        """Handles closing the window."""
        if self.is_connected:
            self.client_socket.close()
        self.destroy()


if __name__ == "__main__":
    app = ChatClient()
    app.mainloop()