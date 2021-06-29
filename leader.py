import sys
import threading
from threading import Thread

from common import *
from server import Server


class Leader(Server):
    def __init__(self, server_addr: tuple, quorum_addr: tuple):
        super().__init__(server_addr)
        self.quorum_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.quorum_sock.bind(quorum_addr)
        self.quorum_sock.listen(1)
        self.follower_lock = threading.Lock()
        self.followers = set()

    def operate_lock_map(self, client_msg: dict, client_id: str) -> bool:
        lock_key = client_msg['value']
        action = client_msg['action']
        result = False
        self.map_lock.acquire()
        if action == ClientActionType.LOCK.value:
            if self.lock_map.get(lock_key, None) is None:
                self.lock_map[lock_key] = client_id
                result = True
            else:
                result = False
        elif action == ClientActionType.UNLOCK.value:
            if self.lock_map.get(lock_key, None) == client_id:
                del self.lock_map[lock_key]
                result = True
            else:
                result = False
        self.map_lock.release()
        self.broadcast_to_followers()
        self.print_map()
        return result

    def handle_client_message(self, conn: socket.socket, client_msg: dict, client_id: str) -> None:
        print(f"Receiving client {client_id}' request: {client_msg}")
        action = client_msg['action']
        if action == ClientActionType.QUERY.value:
            lock_key = client_msg['value']
            self.map_lock.acquire()
            msg = create_client_message(action, self.lock_map.get(lock_key, None))
            self.map_lock.release()
        else:
            result = self.operate_lock_map(client_msg, client_id)
            msg = create_client_message(action, result)
        send(conn, msg)

    def accept_follower(self) -> None:
        while True:
            conn, addr = self.quorum_sock.accept()
            print(f"Follower {addr} connected to server")
            self.follower_lock.acquire()
            self.followers.add(conn)
            self.follower_lock.release()
            thread = Thread(target=self.receive_follower_message, args=(conn, addr))
            thread.setDaemon(True)
            thread.start()

    def receive_follower_message(self, conn: socket.socket, addr: tuple) -> None:
        buffer = bytearray()
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
                follower_msg = decode_message(body)
                self.handle_follower_message(conn, follower_msg)
                buffer = buffer[length:]

        print(f"Follower {addr} disconnected!")
        self.follower_lock.acquire()
        self.followers.remove(conn)
        self.follower_lock.release()
        conn.close()

    def handle_follower_message(self, conn: socket.socket, follower_msg: dict) -> None:
        client_id = follower_msg['client_id']
        client_msg = follower_msg['client_msg']
        print(f"Receiving follower's request: {client_id} {client_msg}")
        result = self.operate_lock_map(client_msg, client_id)
        op_msg = {'client_id': client_id, 'action': client_msg['action'], 'value': result}
        leader_msg = create_leader_message(LeaderActionType.RESPONSE, op_msg)
        send(conn, leader_msg)

    def broadcast_to_followers(self) -> None:
        print('Broadcasting to all followers')
        self.map_lock.acquire()
        msg = create_leader_message(LeaderActionType.BROADCAST, self.lock_map)
        self.map_lock.release()
        for conn in self.followers:
            send(conn, msg)

    def __del__(self):
        if self.quorum_sock:
            self.quorum_sock.close()
        super().__del__()


def main():
    leader = Leader((sys.argv[1], int(sys.argv[2])), (sys.argv[3], int(sys.argv[4])))
    quorum_thread = Thread(target=leader.accept_follower)
    quorum_thread.setDaemon(True)
    quorum_thread.start()
    leader.accept_client()


if __name__ == '__main__':
    main()
