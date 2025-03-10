import socket
import sys
import network

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        with network.Server() as server:
            server.start_game()
    else:
        with network.Client(
            socket.gethostbyname(socket.gethostname()), network.PORT
        ) as client:
            client.create_player()
            client.main()
