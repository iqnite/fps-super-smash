import pygame


class Game:
    def __init__(self, screen_size):
        pygame.init()
        self.screen = pygame.display.set_mode(screen_size)
        self.objects = {}
        self.clock = pygame.time.Clock()
        self.running = True
        self.dt = 0

    def main(self, func=None):
        while self.running:
            # poll for events
            # pygame.QUIT event means the user clicked X to close your window
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            if func:
                func()
            for obj in self.objects.values():
                if obj.loop:
                    obj.loop()
            # flip() the display to put your work on screen
            pygame.display.flip()
            # limits FPS to 60
            # dt is delta time in seconds since last frame, used for framerate-
            # independent physics.
            self.dt = self.clock.tick(60) / 1000
        pygame.quit()

    def add_object(self, name, func, *args, **kwargs):
        obj = func(self, *args, **kwargs)
        self.objects[name] = obj
        return obj

    @property
    def width(self):
        return self.screen.get_width()

    @property
    def height(self):
        return self.screen.get_height()


class Sprite:
    def __init__(
        self,
        game: Game,
        image_path: str,
        pos_vector=None,
        x=None,
        y=None,
        collidable=True,
        teleport=[],
    ):
        self.game = game
        self.teleport = teleport
        self.default_image = pygame.image.load(image_path)
        self.flipped_image = pygame.transform.flip(self.default_image, True, False)
        self.image = self.default_image
        if pos_vector is not None:
            self.pos = pos_vector
        elif x is not None and y is not None:
            self.pos = pygame.Vector2(x, y)
        else:
            raise ValueError("Either pos_vector or x and y must be provided")
        self.collidable = collidable
        self.rect = self.image.get_rect()
        self.rect.x = int(self.pos.x)
        self.rect.y = int(self.pos.y)

    def loop(self):
        self.check_teleport()
        self.draw()

    @property
    def x(self):
        return self.pos.x

    @x.setter
    def x(self, value):
        self.pos.x = value
        self.rect.x = int(self.pos.x)

    def x_move(self, value):
        self.x += value * self.game.dt

    @property
    def y(self):
        return self.pos.y

    @y.setter
    def y(self, value):
        self.pos.y = value
        self.rect.y = int(self.pos.y)

    def y_move(self, value):
        self.y += value * self.game.dt

    def collides_with(self, other):
        if not self.collidable:
            return False
        if isinstance(other, str):
            return self.collides_with(self.game.objects[other])
        if isinstance(other, MultiSprite):
            return self.collides_with(other.sprites)
        if isinstance(other, list):
            return any(self.collides_with(obj) for obj in other)
        if isinstance(other, Sprite):
            return self.rect.colliderect(other.rect)

    def collides_with_any(self):
        return any(
            self.collides_with(obj.sprites if isinstance(obj, MultiSprite) else obj)
            for obj in self.game.objects.values()
            if obj is not self
            and (
                not isinstance(obj, MultiSprite)
                or not any(sprite is self for sprite in obj.sprites)
            )
        )

    def check_teleport(self):
        if "top" in self.teleport and self.y < 0:
            self.y = self.game.height
        if "bottom" in self.teleport and self.y > self.game.height:
            self.y = 0
        if "left" in self.teleport and self.x < 0:
            self.x = self.game.width
        if "right" in self.teleport and self.x > self.game.width:
            self.x = 0

    def draw(self):
        self.game.screen.blit(self.image, (self.x, self.y))


class MultiSprite:
    def __init__(self, game: Game, sprite_args):
        self.game = game
        self.sprites = [Sprite(game=game, **arg) for arg in sprite_args]

    def loop(self):
        for sprite in self.sprites:
            sprite.loop()

    @property
    def x(self):
        return self.sprites[0].x

    def x_move(self, value):
        for sprite in self.sprites:
            sprite.x_move(value)

    @property
    def y(self):
        return self.sprites[0].y

    def y_move(self, value):
        for sprite in self.sprites:
            sprite.y_move(value)

    def collides_with(self, other):
        return any(sprite.collides_with(other) for sprite in self.sprites)

    def collides_with_any(self):
        return any(sprite.collides_with_any() for sprite in self.sprites)

    def check_teleport(self):
        for sprite in self.sprites:
            sprite.check_teleport()

    def draw(self):
        for sprite in self.sprites:
            sprite.draw()


class Button(Sprite):
    def __init__(self, game: Game, image_path: str, x, y, func):
        super().__init__(game, image_path, x=x, y=y, collidable=False)
        self.func = func

    def loop(self):
        super().loop()
        # TODO: Implement button logic


def button(image_path: str):
    def decorator(func):
        func._engine_type_ = Button
        func._engine_kwargs_ = {"image_path": image_path}
        return func

    return decorator


class Menu:
    def __init__(self, game: Game, button_distance: int):
        self.buttons = [
            func._engine_type_(
                **getattr(self, name)._engine_kwargs_,
                func=func,
                game=game,
                x=game.width / 2,
                y=game.height / 2 + i * button_distance
            )
            for i, (name, func) in enumerate(self.__class__.__dict__.items())
            if hasattr(func, "_engine_type_")
        ]

    def loop(self):
        for button in self.buttons:
            button.loop()
