import io
import contextlib
from pathlib import Path
with contextlib.redirect_stdout(None):
    import pygame

class ClueGenerator:
    def __init__(self, bg_image_path: Path, font_path: Path, generated_clue_name: str):
        # Relevant file paths
        self.bg_image_path = bg_image_path
        self.font_path = font_path
        self.generated_clue_name = generated_clue_name

        # Start up pygame
        pygame.init()
        _ = pygame.display.set_mode((1, 1), pygame.NOFRAME)

        # Pygame settings
        self.bg_image = pygame.image.load(bg_image_path).convert_alpha()
        self.bg_width, self.bg_height = self.bg_image.get_size()
        self.font_colour = (255, 255, 0)

    def generate_clue(self, text_input: list[str], line_space: int = 2, scalar: float = 1.0, font_size: int = 48) -> io.BytesIO:
        # Scale normal image to 3x for normal appearance with font
        bg_image = pygame.transform.scale(self.bg_image, (int(self.bg_width * 3 * scalar), (self.bg_height * 3 * scalar)))
        font = pygame.font.Font(self.font_path, font_size)

        rendered_text = [font.render(text, False, self.font_colour) for text in text_input]
        text_height = rendered_text[0].get_height()
        total_height = (len(rendered_text) * (line_space + text_height)) - line_space

        top_offset = (bg_image.get_height() - total_height) // 2
        x_pos = bg_image.get_width() // 2
        for idx, text in enumerate(rendered_text):
            y_pos = top_offset + (idx * (text_height + line_space))
            rct = text.get_rect()
            rct.midtop = (x_pos, y_pos)
            bg_image.blit(text, rct)

        img = io.BytesIO()
        pygame.image.save(bg_image, img, self.generated_clue_name)
        img.seek(0)
        return img
