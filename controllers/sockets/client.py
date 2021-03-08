import socket

print("Connecting...")

client_socket = socket.create_connection(("127.0.0.1", 5000))

print("Connection established!")

while True:
    message = input("Type command (no command will exit):\n")

    if message == "":
        break
    
    client_socket.send(bytes(message, "utf-8"))
    print("Command sent!")
    
    response = client_socket.recv(32).decode("utf-8")

    print("Response from server:")
    print(response)

client_socket.close()
print("Closed connection.")
