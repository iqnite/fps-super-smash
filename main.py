import pygame
from sprite import GameContext, Sprite

# pygame setup
pygame.init()
ctx = GameContext(screen=pygame.display.set_mode((1920, 1080)))

while ctx.running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # fill the screen with a color to wipe away anything from last frame
    ctx.screen.fill("black")

    player = Sprite(
        ctx,
        "images/player0.png",
        pygame.Vector2(ctx.screen.get_width() / 2, ctx.screen.get_height() / 2),
    )

    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        player.y -= 300
    if keys[pygame.K_s]:
        player.y += 300
    if keys[pygame.K_a]:
        player.x -= 300
    if keys[pygame.K_d]:
        player.x += 300

    # flip() the display to put your work on screen
    pygame.display.flip()

    # limits FPS to 60
    # dt is delta time in seconds since last frame, used for framerate-
    # independent physics.
    ctx.dt = ctx.clock.tick(60) / 1000

pygame.quit()
