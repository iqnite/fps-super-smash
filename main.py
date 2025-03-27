import pygame
import engine
import network


class StartMenu(engine.Menu):
    button_distance = 100

    @engine.button("images/Menu/Login.png")
    def connect(self):
        self.game.running = False
        ip = input("Enter IP Address: ")
        client = network.Client(ip, network.PORT)
        try:
            with client:
                client.main()
        except TimeoutError:
            print("Connection timed out.")
            quit()
        except ConnectionAbortedError:
            print("Connection aborted by server.")
            quit()
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
        with server:
            server.main()

    @engine.button("images/Menu/Cancel.png")
    def exit(self):
        self.game.running = False


game = engine.Game((0, 0))
bg_image = pygame.image.load("images/Menu/Background.png")
bg_image = pygame.transform.scale(bg_image, (game.width, game.height))
game.add_object("StartMenu", StartMenu)
game.main(lambda: game.screen.blit(bg_image, (0, 0)))
