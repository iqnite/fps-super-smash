import pygame
import pygame_textinput
import engine
import network


class StartMenu(engine.Menu):
    button_distance = 100

    @engine.button("images/Menu/Login.png")
    def connect(self):
        self.game.running = False
        font = pygame.font.Font("images/Anta-Regular.ttf", 30)
        enter_text = font.render(
            "Enter the server IP address and press Enter to connect.", True, "white"
        )
        ip_input = pygame_textinput.TextInputVisualizer(
            font_color="white",
            font_object=font,
            cursor_color="white",
        )

        screen = pygame.display.set_mode((0, 0))
        clock = pygame.time.Clock()

        wating = True
        while wating:
            if self.game.background:
                screen.blit(self.game.background, (0, 0))
            else:
                screen.fill("black")

            events = pygame.event.get()
            ip_input.update(events)  # type: ignore
            screen.blit(enter_text, (10, screen.get_height() / 2 - 50))
            screen.blit(ip_input.surface, (10, screen.get_height() / 2))

            for event in events:
                if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                ):
                    quit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    wating = False

            pygame.display.update()
            clock.tick(30)
        client = network.Client(ip_input.value, network.PORT)
        self.game.objects["music"].stop()
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
        self.game.objects["music"].stop()
        with server:
            server.main()

    @engine.button("images/Menu/Cancel.png")
    def exit(self):
        self.game.running = False


game = engine.Game((0, 0), "images/Menu/Background.png")
game.add_object(
    "logo",
    engine.Sprite,
    image_path="images/fps-logo.svg",
    x=game.width / 2 - 200,
    y=10,
)
game.add_object("StartMenu", StartMenu)
game.sound_loop("sounds/menu_music.mp3", id="music")
game.main()
