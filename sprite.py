import pygame


class GameContext:
    def __init__(
        self,
        *,
        screen: pygame.Surface,
        objects: dict = {},
        clock: pygame.time.Clock = pygame.time.Clock(),
        running: bool = True,
        dt: float = 0,
    ):
        self.screen = screen
        self.objects = objects
        self.clock = clock
        self.running = running
        self.dt = dt


class Sprite:
    def __init__(
        self,
        ctx: GameContext,
        image_path: str,
        pos_vector=None,
        x=None,
        y=None,
        collidable=True,
    ):
        self.ctx = ctx
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
        self.draw()

    @property
    def x(self):
        return self.pos.x

    @x.setter
    def x(self, value):
        self.pos.x = value
        self.draw()

    def x_move(self, value):
        self.x += value * self.ctx.dt

    def x_move_no_redraw(self, value):
        self.pos.x += value * self.ctx.dt
        self.rect.x = int(self.x)

    @property
    def y(self):
        return self.pos.y

    @y.setter
    def y(self, value):
        self.pos.y = value
        self.draw()

    def y_move(self, value):
        self.y += value * self.ctx.dt

    def y_move_no_redraw(self, value):
        self.pos.y += value * self.ctx.dt
        self.rect.y = int(self.y)

    def collides_with(self, other):
        if not self.collidable:
            return False
        if isinstance(other, str):
            return self.collides_with(self.ctx.objects[other])
        if isinstance(other, MultiSprite):
            return self.collides_with(other.sprites)
        if isinstance(other, list):
            return any(self.collides_with(obj) for obj in other)
        if isinstance(other, Sprite):
            return self.rect.colliderect(other.rect)

    def collides_with_any(self):
        return any(
            self.collides_with(obj.sprites if isinstance(obj, MultiSprite) else obj)
            for obj in self.ctx.objects.values()
            if obj is not self
            and (
                not isinstance(obj, MultiSprite)
                or not any(sprite is self for sprite in obj.sprites)
            )
        )

    def draw(self):
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        self.ctx.screen.blit(self.image, (self.x, self.y))


class MultiSprite:
    def __init__(self, ctx: GameContext, sprite_args):
        self.sprites = [Sprite(ctx=ctx, **arg) for arg in sprite_args]

    @property
    def x(self):
        return self.sprites[0].x

    def x_move(self, value):
        for sprite in self.sprites:
            sprite.x_move(value)

    def x_move_no_redraw(self, value):
        for sprite in self.sprites:
            sprite.x_move_no_redraw(value)

    @property
    def y(self):
        return self.sprites[0].y

    def y_move(self, value):
        for sprite in self.sprites:
            sprite.y_move(value)

    def y_move_no_redraw(self, value):
        for sprite in self.sprites:
            sprite.y_move_no_redraw(value)

    def collides_with(self, other):
        return any(sprite.collides_with(other) for sprite in self.sprites)

    def collides_with_any(self):
        return any(sprite.collides_with_any() for sprite in self.sprites)

    def draw(self):
        for sprite in self.sprites:
            sprite.draw()
