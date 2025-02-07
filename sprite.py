import pygame


class GameContext:
    def __init__(
        self,
        *,
        screen: pygame.Surface,
        clock: pygame.time.Clock = pygame.time.Clock(),
        running: bool = True,
        dt: float = 0,
    ):
        self.screen = screen
        self.clock = clock
        self.running = running
        self.dt = dt


class Sprite:
    def __init__(self, ctx: GameContext, image_path: str, pos_vector=None, x=None, y=None):
        self.ctx = ctx
        self.image = pygame.image.load(image_path)
        if pos_vector:
            self.pos = pos_vector
        elif x and y:
            self.pos = pygame.Vector2(x, y)
        else:
            raise ValueError("Either pos_vector or x and y must be provided")

    @property
    def x(self):
        return self.pos.x

    @x.setter
    def x(self, value):
        self.pos.x = value
        self.draw()

    @property
    def y(self):
        return self.pos.y
    
    @y.setter
    def y(self, value):
        self.pos.y = value
        self.draw()

    def draw(self):
        self.ctx.screen.blit(self.image, (self.x, self.y))
