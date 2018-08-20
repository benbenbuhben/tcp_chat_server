import socket


def setup_server():
    """
    """
    # Instantiate a socket instance
    echo_server = socket.socket(
        socket.AF_INET,  # Family
        socket.SOCK_STREAM,  # Type
        socket.IPPROTO_TCP,  # Protocol
    )
    # Bind an endpoint (HOST, PORT) to the socket
    echo_server.bind(('127.0.0.1', 8000))
    # Activate the listener for the socket
    echo_server.listen(1)
    # Return the socket and the method (accept) which starts the server
    return echo_server, echo_server.accept()


if __name__ == '__main__':
    server, (conn, addr) = setup_server()
    print('Received a client connection for {}'.format(addr))
    buffer_length = 16
    message_complete = False
    message = ''

    while not message_complete:
        part = conn.recv(buffer_length)
        message += part.decode()
        if len(part) < buffer_length:
            break

    # message = 'The server received your message!'
    conn.sendall(message.encode())

    conn.close()
    server.close()
