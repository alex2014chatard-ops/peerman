import socket
import secrets
import threading
import time
import requests

print("------ // peerman // -------")

mode = input("Are you the (H)ost or (C)lient? ").strip().lower()
PORT = int(input("Enter a port (5000 or 5050 recommended): "))


# Function to get public IP
def get_public_ip():
    try:
        return requests.get('https://api.ipify.org').text
    except:
        return "Unable to determine"


if mode == 'h':
    # HOST MODE
    HOST = "0.0.0.0"
    public_ip = get_public_ip()

    print(r"=== HOST MODE ===")
    print(f"Your Public IP: {public_ip}")
    print(f"Port: {PORT}")
    print("Share these with your peer to connect remotely.")
    print("(Make sure to port forward on your router!)\n")

    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen(1)
    except Exception as e:
        print("[ :( ] Error!", e)
        exit()

    print("[ . . . ] PeerMan waiting for connection...")
    conn, addr = server.accept()
    print("[ :) ] Connected:", addr)

elif mode == 'c':
    # CLIENT MODE
    print(r"=== CLIENT MODE ===")
    remote_host = input("Enter the host's IP address: ")

    try:
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"[ . . . ] Connecting to {remote_host}:{PORT}...")
        conn.connect((remote_host, PORT))
        print("[ :) ] Connected!")
    except Exception as e:
        print("[ :( ] Connection failed!", e)
        exit()

    server = None
else:
    print("[ :( ] Invalid mode!")
    exit()


def receive_messages():
    while True:
        try:
            data = conn.recv(4096)

            if not data:
                print("\n[ ! ] Connection closed.")
                break

            print(f"\n[<] {data.decode()}")
            print(f"netdog_i{HOST}_p{PORT}-$ ", end="", flush=True)

        except Exception as e:
            print("\n[ ! ] Connection lost:", e)
            break


threading.Thread(target=receive_messages, daemon=True).start()

exit_code = secrets.token_hex(3)
print(f"Send the following hash to exit: {exit_code}")

while True:
    message = input(f"peerman_i{HOST}_p{PORT}-$ ")

    if message == exit_code:
        message = "The host has disconnected! Thank you for using this service!"
        conn.sendall(message.encode())

        print("You have disconnected from the server! Thank you for using this service!")

        time.sleep(2)
        break

    conn.sendall(message.encode())

conn.close()
if server:
    server.close()