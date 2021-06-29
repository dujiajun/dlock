import sys
from threading import Thread

from common import *
from server import Server


class Follower(Server):
    def __init__(self, server_addr: tuple):
        super().__init__(server_addr)
        self.quorum_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.pending = dict()

    def connect(self, quorum_addr: tuple):
        self.quorum_sock.connect(quorum_addr)
        thread = Thread(target=self.receive_leader_message)
        thread.setDaemon(True)
        thread.start()

    def handle_client_message(self, conn: socket.socket, client_msg: dict, client_id: str):
        print(f"Receiving client {client_id}' request: {client_msg}")
        lock_key = client_msg['value']
        action = client_msg['action']
        if action == ClientActionType.LOCK.value or action == ClientActionType.UNLOCK.value:
            self.request_leader(client_msg, client_id)
            self.pending[client_id] = conn
        elif action == ClientActionType.QUERY.value:
            self.map_lock.acquire()
            msg = create_client_message(action, self.lock_map.get(lock_key, None))
            send(conn, msg)
            self.map_lock.release()
        self.print_map()

    def request_leader(self, client_msg: dict, client_id: str):
        msg = create_follower_message(client_id, client_msg)
        send(self.quorum_sock, msg)

    def receive_leader_message(self):
        buffer = bytearray()
        while True:
            try:
                data = self.quorum_sock.recv(BUFFER_SIZE)
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
                self.handle_leader_message(msg)

    def handle_leader_message(self, leader_msg: dict):
        print(f"Receiving leader's request: {leader_msg['action']}", )
        if leader_msg['action'] == LeaderActionType.BROADCAST.value:
            self.map_lock.acquire()
            self.lock_map = leader_msg['value']
            print('Map:', self.lock_map)
            self.map_lock.release()
        elif leader_msg['action'] == LeaderActionType.RESPONSE.value:
            value = leader_msg['value']
            conn = self.pending.get(value['client_id'], None)
            if conn:
                msg = create_client_message(value['action'], value['value'])
                send(conn, msg)
                del self.pending[value['client_id']]

    def __del__(self):
        if self.quorum_sock:
            self.quorum_sock.close()
        super().__del__()


def main():
    follower = Follower((sys.argv[1], int(sys.argv[2])))
    follower.connect((sys.argv[3], int(sys.argv[4])))
    follower.accept_client()


if __name__ == '__main__':
    main()
