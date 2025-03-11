import sys
import network
from level import Level


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        server = network.Server()
        server.game.add_object(
            "level",
            Level.load,
            pos_filepath="level.csv",
            image_filepath="images/level/{}.png",
            y_velocity=1,
            common_sprite_args={"teleport": {"+y": {720: 200}}},
        )
        with server:
            server.main()
    else:
        client = network.Client(network.get_wlan_ip(), network.PORT)  # TODO: Change to server IP
        try:
            with client:
                print(client.request(network.ECHO))
                client.main()
        except ConnectionRefusedError:
            print("Could not connect: Server is not running.")
            quit()
