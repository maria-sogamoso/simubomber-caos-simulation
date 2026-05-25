"""SimuBomber: Caos — entry point with full menu loop."""
import os, sys
_HERE=os.path.dirname(os.path.abspath(__file__))
_ROOT=os.path.dirname(_HERE)
for p in (_HERE,_ROOT):
    if p not in sys.path: sys.path.insert(0,p)

import pygame
import config
from config import WIDTH, HEIGHT, WINDOW_TITLE, FPS
from game.sounds    import init_sound
from game.menu      import run_main_menu
from game.game_loop import GameLoop


def main():
    pygame.init(); init_sound()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    config._chosen_char = "char1"   # default, overwritten by menu

    while True:
        result = run_main_menu(screen)   # blocks until "play" or "quit"
        if result == "quit": break
        # Play session
        game = GameLoop(screen, char_id=config._chosen_char)
        if game.run() == "quit": break
        # else "menu" → loop back to main menu

    pygame.quit()

if __name__ == "__main__":
    main()
