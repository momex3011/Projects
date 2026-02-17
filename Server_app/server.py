import socket
import threading

# --- Server Configuration ---
HOST = '0.0.0.0'  # Listen on all available network interfaces
PORT = 12345      # An unused port (you can change this)

# --- State ---
clients = []
clients_lock = threading.Lock() # A lock to ensure thread-safe access to the clients list

def broadcast(message, sender_socket):
    """Sends a message to all clients except the sender."""
    with clients_lock:
        for client_socket in clients:
            if client_socket != sender_socket:
                try:
                    client_socket.send(message)
                except:
                    # If sending fails, assume the client disconnected
                    remove_client(client_socket)

def remove_client(client_socket):
    """Removes a client socket from the list."""
    if client_socket in clients:
        clients.remove(client_socket)

def handle_client(client_socket):
    """Handles a single client connection in its own thread."""
    print(f"[NEW CONNECTION] {client_socket.getpeername()} connected.")
    
    # Add the new client to our list
    with clients_lock:
        clients.append(client_socket)

    try:
        while True:
            # Receive messages from the client
            message = client_socket.recv(1024)
            if not message:
                # An empty message means the client disconnected
                break
            
            # Broadcast the message to other clients
            print(f"[MESSAGE] Received: {message.decode('utf-8')}")
            broadcast(message, client_socket)
    except:
        # Catches any other disconnection errors
        pass
    finally:
        # Cleanup: remove the client and close the socket
        with clients_lock:
            remove_client(client_socket)
        client_socket.close()
        print(f"[DISCONNECTED] {client_socket.getpeername()} disconnected.")


def start_server():
    """Initializes and starts the chat server."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"[LISTENING] Server is listening on {HOST}:{PORT}")

    while True:
        # Accept new connections
        client_socket, address = server_socket.accept()
        
        # Create a new thread to handle this client
        # This allows the server to handle multiple clients at once
        thread = threading.Thread(target=handle_client, args=(client_socket,))
        thread.start()

if __name__ == "__main__":
    start_server()