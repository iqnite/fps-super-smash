import sys
import network
from level import Level


if __name__ == "__main__":
    if len(sys.argv) > 1:
        client = network.Client(sys.argv[1], network.PORT)
        try:
            with client:
                print(client.request(network.ECHO).decode())
                client.request(
                    network.JOIN_GAME
                    + f"images/player{sys.argv[2] if len(sys.argv) > 2 else 0}.png".encode()
                )
                client.main()
        except ConnectionRefusedError:
            print("Could not connect: Server is not running.")
            quit()
        except ConnectionResetError:
            print("Connection reset by server.")
            quit()
    else:
        server = network.Server()
        server.game.add_object(
            "level",
            Level.load,
            pos_filepath="level.csv",
            image_filepath="images/level/{}.png",
            y_velocity=1,
            common_sprite_args={"teleport": {"+y": {720: 200}}},
        )
        server.add_player(0, "images/player1.png")

        with server:
            server.main(lambda: server.players["player0"].keyboard_control())
