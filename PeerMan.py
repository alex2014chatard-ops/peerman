import socket
import secrets
import threading
import time
import os
import ipaddress
import subprocess
import platform
import json


os.system("cls" if os.name == "nt" else "clear")
print("------ // peerman // -------")

mode = input("Are you the (H)ost or (C)lient? ").strip().lower()
PORT = int(input("Enter a port (5000 or 5050 recommended): "))

HOST = "0.0.0.0"
server = None
conn = None


def is_private_ip(address):
    try:
        ip = ipaddress.ip_address(address)
        return ip.version == 4 and ip.is_private
    except ValueError:
        return False


# Each connected peer gets its own working directory.
working_dir = os.path.expanduser("~")

def handle_remote_command(command):
    global working_dir

    parts = command.strip().split(maxsplit=1)
    if not parts:
        return "Empty command"

    name = parts[0].lower()
    argument = parts[1] if len(parts) > 1 else ""

    if name == "pwd":
        return working_dir

    if name == "cd":
        target = argument or os.path.expanduser("~")
        new_dir = os.path.abspath(os.path.join(working_dir, target))

        if os.path.isdir(new_dir):
            working_dir = new_dir
            return f"Changed directory to {working_dir}"

        return "Directory not found"

    if name in ("ls", "dir"):
        try:
            entries = os.listdir(working_dir)
            return "\n".join(entries) or "(empty directory)"
        except OSError as error:
            return str(error)

    return "Unknown command. Supported: ls, dir, cd, pwd"


def send_message(sock, message):
    # Newline-delimited messages
    sock.sendall((message + "\n").encode("utf-8"))


def receive_messages(sock):
    buffer = ""

    try:
        while True:
            data = sock.recv(4096)

            if not data:
                print("\n[ ! ] Connection closed.")
                break

            buffer += data.decode("utf-8", errors="replace")

            while "\n" in buffer:
                if message.startswith("/cmd "):
                    command = message[5:].strip().lower()
                    result = handle_remote_command(command)

                    send_message(
                        sock,
                        json.dumps({"type": "response", "result": result})
                    )
                else:
                    print(f"\n[<] {message}")



    except OSError as error:
        print(f"\n[ ! ] Connection lost: {error}")


if not 1 <= PORT <= 65535:
    print("[ :( ] Invalid port!")
    raise SystemExit(1)

if mode == "h":
    print("\n=== HOST MODE ===")
    print("Listening on all local interfaces.")
    print("Give your peer your private IPv4 address and port.")
    print("Both peers must be on the same LAN or connected VPN.\n")

    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen(1)

        print(f"[ . . . ] PeerMan listening on port {PORT}...")
        conn, addr = server.accept()
        print(f"[ :) ] Connected: {addr[0]}:{addr[1]}")

    except OSError as error:
        print(f"[ :( ] Host error: {error}")
        raise SystemExit(1)

elif mode == "c":
    print("\n=== CLIENT MODE ===")
    remote_host = input("Enter the host's private IPv4 address: ").strip()

    if not is_private_ip(remote_host):
        print("[ :( ] Enter a valid private IPv4 address.")
        raise SystemExit(1)

    try:
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.settimeout(10)

        print(f"[ . . . ] Connecting to {remote_host}:{PORT}...")
        conn.connect((remote_host, PORT))
        conn.settimeout(None)

        print("[ :) ] Connected!")

    except OSError as error:
        print(f"[ :( ] Connection failed: {error}")
        raise SystemExit(1)

else:
    print("[ :( ] Invalid mode!")
    raise SystemExit(1)

try:
    threading.Thread(
        target=receive_messages,
        args=(conn,),
        daemon=True
    ).start()

    exit_code = secrets.token_hex(3)
    print(f"Send this code to disconnect gracefully: {exit_code}")

    while True:
        try:
            message = input("peerman-$ ")
        except (EOFError, KeyboardInterrupt):
            break

        if message == exit_code:
            send_message(
                conn,
                "The peer has disconnected. Thank you for using PeerMan!"
            )
            print("Disconnecting from PeerMan...")
            time.sleep(0.2)
            break

        try:
            send_message(conn, message)
        except OSError as error:
            print(f"[ :( ] Send failed: {error}")
            break

finally:
    if conn:
        conn.close()

    if server:
        server.close()

    print("PeerMan closed.")
