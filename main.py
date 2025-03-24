import pygame
import engine
import network
from level import Level


class StartMenu(engine.Menu):
    @engine.button("images/Menu/Login.png")
    def connect(self):
        self.game.running = False
        ip = input("Enter IP Address: ")
        client = network.Client(ip, network.PORT)
        try:
            with client:
                print(client.request(network.ECHO).decode())
                client.request(network.JOIN_GAME + f"images/player{0}.png".encode())
                client.main()
        except ConnectionRefusedError:
            print("Could not connect: Server is not running.")
            quit()
        except ConnectionResetError:
            print("Connection reset by server.")
            quit()

    @engine.button("images/Menu/Start.png")
    def start(self):
        self.game.running = False
        server = network.Server()
        server.game.add_object(
            "level",
            Level.load,
            pos_filepath="level.csv",
            image_filepath="images/level/{}.png",
            y_velocity=1,
            common_sprite_args={"teleport": {"+y": {720: 0}}},
        )
        server.add_player(0, "images/player1.png")

        with server:
            server.main()

    @engine.button("images/Menu/Cancel.png")
    def exit(self):
        self.game.running = False


game = engine.Game((0, 0))
bg_image = pygame.image.load("images/Menu/Background.png")
bg_image = pygame.transform.scale(bg_image, (game.width, game.height))
game.screen.blit(bg_image, (0, 0))
game.add_object("StartMenu", StartMenu, button_distance=100)
game.main()
