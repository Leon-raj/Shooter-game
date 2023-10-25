import socket
import threading
import pickle
import random

host = '192.168.149.112'
port = 9090
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))


class Client():
    def __init__(self, conn, address):
        self.conn = conn
        self.address = address
        self.connected = True
        self.data = None
        print(f'Connected with {address}')

    def recive(self):
         while self.connected:
             self.data = self.conn.recv(2048)
             content = pickle.loads(self.data)

             if content == 'DISCONNECT':
                 self.connected = False

    def send(self, data):
        self.conn.send(data)

def start():
    server.listen(2)
    print(f'Server is running at {host}')
    clients = []

    while True:
        conn, addr = server.accept()
        client = Client(conn, addr)
        clients.append(client)

        if len(clients) == 2:
            break

    return clients

char1 = 'Punk', {'IDLE': 3, 'WALK': 3}, {'IDLE': ((5, 15), (4, 15), (4, 15), (5, 15)), 'WALK': ((5, 14), (5, 14), (5, 14), (5, 15), (5, 14), (5, 13))}
char2 = ()
characters = [char1, char2]

gun1 = 'Frostfire', 500, 20, 1, 1, {'Punk':((4, 11), (4, 11), (3, 12), (5, -4), (5, -10))}, ((-19, 16), (20, -19), (26, -22), (18, -47), (-22, -48))
gun2 = 'Microblast', 400, 20, 1, 1, {'Punk':((2, 6), (6, 9), (5, 8), (4, -10), (4, -10))}, ((-17, 25), (22, 21), (26, -19), (26, -45), (-19, -48))
guns = [gun1, gun2]

def game(clients):                                     #Need to make this multiplayer later

    choice = random.randint(0,1)
    if choice == 0:
        choice2 = 1
    else:
        choice2 = 0

    p1 = (characters[choice], guns[choice])
    p1 = pickle.dumps(p1)
    p2 = (characters[choice2], guns[choice2])
    p2 = pickle.dumps(p2)

    clients[0].send(p1)
    clients[1].send(p2)

    for client in clients:
        threading.Thread(target=client.recive).start()

    while True:
        clients[0].send(clients[1].data)
        clients[1].send(clients[0].data)

