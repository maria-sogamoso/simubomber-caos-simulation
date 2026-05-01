"""Map definition and rendering."""

from __future__ import annotations

import pygame

from config import MAP_BORDER_COLOR, MAP_COLOR, MAP_MARGIN, HEIGHT, WIDTH


class Map:
    """Rectangular play area used to constrain movement."""

    def __init__(self) -> None:
        self.rect = pygame.Rect(
            MAP_MARGIN,
            MAP_MARGIN,
            WIDTH - MAP_MARGIN * 2,
            HEIGHT - MAP_MARGIN * 2,
        )

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the map background and border."""
        pygame.draw.rect(screen, MAP_COLOR, self.rect)
        pygame.draw.rect(screen, MAP_BORDER_COLOR, self.rect, width=4)