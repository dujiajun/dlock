import json
import socket
from enum import Enum
from typing import Union

BUFFER_SIZE = 1024


class ClientActionType(Enum):
    """消息类型"""
    INIT = 'init'
    LOCK = 'lock'
    UNLOCK = 'unlock'
    QUERY = 'query'


def create_client_message(action: Union[ClientActionType, str], value: Union[str, bool]) -> str:
    if isinstance(value, bool):
        value = 'success' if value else 'failed'
    if isinstance(action, ClientActionType):
        msg = {'action': action.value, 'value': value}
    else:
        msg = {'action': action, 'value': value}
    return json.dumps(msg)


class FollowerActionType(Enum):
    """消息类型"""
    INIT = 'init'
    REQUEST = 'request'


def create_follower_message(client_id: str, client_msg: dict) -> str:
    msg = {'client_id': client_id, 'client_msg': client_msg}
    return json.dumps(msg)


class LeaderActionType(Enum):
    """消息类型"""
    RESPONSE = 'response'
    BROADCAST = 'broadcast'


def create_leader_message(action: LeaderActionType, value: dict) -> str:
    msg = {'action': action.value, 'value': value}
    return json.dumps(msg)


def length_from_bytes(data: bytes) -> int:
    return int.from_bytes(data, byteorder='big', signed=False)


def decode_message(data: bytes) -> dict:
    body = data.decode('utf-8')
    msg = json.loads(body)
    return msg


def create_packet(payload: str) -> bytes:
    body = payload.encode('utf-8')
    length = (len(body) + 4).to_bytes(length=4, byteorder='big', signed=False)
    # print(len(body) + 4, payload)
    return length + body


def send(sock: socket.socket, msg: str):
    packet = create_packet(msg)
    sock.sendall(packet)
