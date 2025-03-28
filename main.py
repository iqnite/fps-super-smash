import pygame
import pygame_textinput
import engine
import network


class StartMenu(engine.Menu):
    button_distance = 100

    @engine.button("images/Menu/Login.png")
    def connect(self):
        self.game.running = False
        ip_input = pygame_textinput.TextInputVisualizer()

        screen = pygame.display.set_mode((500, 100))
        clock = pygame.time.Clock()

        wating = True
        while wating:
            screen.fill((225, 225, 225))

            events = pygame.event.get()
            ip_input.update(events)  # type: ignore
            screen.blit(ip_input.surface, (10, 10))

            for event in events:
                if event.type == pygame.QUIT:
                    quit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    wating = False

            pygame.display.update()
            clock.tick(30)
        client = network.Client(ip_input.value, network.PORT)
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
        except ValueError:
            print("Invalid IP address.")
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


game = engine.Game((0, 0), "images/Menu/Background.png")
game.add_object("StartMenu", StartMenu)
game.main()
