from client import ChatClient
import threading
import socket
import sys

PORT = 5004


class ChatServer(threading.Thread):
    def __init__(self, port, host='localhost'):
        super().__init__(daemon=True)
        self.port = port
        self.host = host
        self.server = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
            socket.IPPROTO_TCP,
        )

        self.client_pool = []

        try:
            self.server.bind((self.host, self.port))
        except OSError:
            self.port += 1
            self.server.bind((self.host, self.port))
            print('Bind failed on Port {}. Switching to Port {}'.format(self.port - 1,self.port))
        except socket.error:
            print('Bind failed {}'.format(socket.error))
            sys.exit()

        self.server.listen(1)

    def parser(self, id, nick, conn, message):
        if message.startswith('@'):
            data = message.split(maxsplit=1)

            if data[0] == '@quit':
                conn.sendall(b'You have left the chatroom')
                reply = nick.encode() + b' has left the channel'
                [c.conn.sendall(reply) for c in self.client_pool if len(self.client_pool)]
                self.client_pool = [c for c in self.client_pool if c.id != id]
                conn.close()

            elif data[0] == '@list':
                list_of_users = ''
                for user in self.client_pool:
                    list_of_users += user.nick + '\n'
                conn.sendall(list_of_users.encode())

            elif data[0] == '@nickname':
                if len(data[1].split(' ')) > 1:
                    response = 'User Name can only be one word.\n'
                    conn.sendall(response.encode())
                else:
                    for c in self.client_pool:
                        if c.id == id:
                            c.nick = data[1].strip('\n')
                            response = 'Your nickname is now {}\n'.format(c.nick)
                            c.conn.sendall(response.encode())

            elif data[0] == '@dm':
                recipient = data[1].split(maxsplit=1)[0]
                message = 'DM from {}: '.format(nick) + data[1].split(maxsplit=1)[1]
                [c.conn.sendall(message.encode()) for c in self.client_pool if c.nick == recipient]

            else:
                conn.sendall(b'Invalid command. Please try again.\n')

        elif message == 'LeftWithControlC':
            conn.sendall(b'You have left the chatroom')
            reply = nick.encode() + b' has left the channel'
            [c.conn.sendall(reply) for c in self.client_pool if len(self.client_pool)]
            self.client_pool = [c for c in self.client_pool if c.id != id]
            conn.close()

        else:
            reply = nick.encode() + b': ' + message.encode()
            [c.conn.sendall(reply) for c in self.client_pool if len(self.client_pool)]

    def run_thread(self, client):
        print('{} connected with {}:{}'.format(
            client.nick, client.addr[0], str(client.addr[1])))
        message_complete = False
        message = ''
        buffer_length = 4096

        try:
            while not message_complete:
                part = client.conn.recv(buffer_length)
                message += part.decode()
                if len(part) < buffer_length:
                    self.parser(client.id, client.nick, client.conn, message)
                    message = ''

        except (ConnectionResetError, BrokenPipeError):
            client.conn.close()

        except (OSError):
            global PORT
            PORT += 1

        except (KeyboardInterrupt):
            message = 'LeftWithControlC'
            self.parser(client.id, client.nick, client.conn, message)

    def run(self):
        print('Server is runing on {}'.format(self.port))
        while True:
            conn, addr = self.server.accept()
            client = ChatClient(conn, addr)
            self.client_pool.append(client)
            threading.Thread(
                target=self.run_thread,
                args=(client,),
                daemon=True
            ).start()

    def exit(self):
        self.server.close()


if __name__ == '__main__':
    server = ChatServer(PORT)
    try:
        server.run()
    except (KeyboardInterrupt, OSError) as e:
        if isinstance(e, OSError):
            PORT += 1
            server.run()
        else:
            [c.conn.close() for c in server.client_pool if len(server.client_pool)]
            server.exit()
