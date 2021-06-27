import threading
from threading import Thread

from common import *


class Server:
    def __init__(self, server_addr):
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.bind(server_addr)
        self.server_sock.listen(1)
        self.lock_map = dict()
        self.map_lock = threading.Lock()

    def print_map(self):
        self.map_lock.acquire()
        print('Map:', self.lock_map)
        self.map_lock.release()

    def accept_client(self):
        while True:
            conn, addr = self.server_sock.accept()
            print(f"Client {addr} connected to server")
            thread = Thread(target=self.receive_client_message, args=(conn, addr))
            thread.setDaemon(True)
            thread.start()

    def receive_client_message(self, conn: socket.socket, addr):
        buffer = bytearray()
        client_id = ''
        while True:
            try:
                data = conn.recv(BUFFER_SIZE)
            except ConnectionResetError:
                break
            if not data:
                break
            buffer = buffer + data
            while True:
                if len(buffer) < 4:
                    break
                length = length_from_bytes(buffer[0:4])
                if len(buffer) < length:
                    break
                body = buffer[4:length]
                buffer = buffer[length:]
                client_msg = decode_message(body)
                if client_msg['action'] == 'init':
                    client_id = client_msg['value']
                else:
                    self.handle_client_message(conn, client_msg, client_id)

        print(f"Client {addr} disconnected!")
        conn.close()

    def handle_client_message(self, conn, client_msg, client_id: str):
        pass

    def __del__(self):
        if self.server_sock:
            self.server_sock.close()
