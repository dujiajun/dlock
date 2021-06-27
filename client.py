import sys
import uuid

from common import *


class Client:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_id = uuid.uuid1()
        print('client id:', self.client_id)

    def connect(self, server_addr: tuple):
        self.sock.connect(server_addr)
        msg = create_client_message(ClientActionType.INIT, self.client_id.hex)
        send(self.sock, msg)

    def try_lock(self, lock_key: str):
        msg = create_client_message(ClientActionType.LOCK, lock_key)
        send(self.sock, msg)

    def try_unlock(self, lock_key: str):
        msg = create_client_message(ClientActionType.UNLOCK, lock_key)
        send(self.sock, msg)

    def query_lock(self, lock_key: str):
        msg = create_client_message(ClientActionType.QUERY, lock_key)
        send(self.sock, msg)

    def action(self, action: str, lock_key: str):
        if action == ClientActionType.LOCK.value:
            self.try_lock(lock_key)
        elif action == ClientActionType.UNLOCK.value:
            self.try_unlock(lock_key)
        elif action == ClientActionType.QUERY.value:
            self.query_lock(lock_key)
        else:
            print('Wrong command!')
            return
        return self.receive()

    def receive(self):
        buffer = bytearray()
        msg = {}
        flag = True
        while flag:
            try:
                data = self.sock.recv(BUFFER_SIZE)
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
                msg = decode_message(body)
                flag = False
        return msg

    def __del__(self):
        if self.sock:
            self.sock.close()


def main():
    client = Client()
    client.connect((sys.argv[1], int(sys.argv[2])))
    while True:
        action, lock_key = input().split(' ')
        msg = client.action(action, lock_key)
        print(msg['value'])


if __name__ == '__main__':
    main()
