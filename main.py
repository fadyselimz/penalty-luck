"""
main.py
Entry point for the Penalty Shootout game. Creates the window and runs the
main loop at a fixed 60 FPS, delegating all logic to the Game class.
"""

import sys

import pygame

from game import Game
from settings import WIDTH, HEIGHT, FPS, TITLE


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    game = Game(screen)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            game.handle_event(event)

        if game.request_quit:
            running = False
            continue

        game.update(dt)
        game.draw()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()