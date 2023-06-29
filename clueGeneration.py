import pygame

class ClueGenerator:
    def __init__(self, bg_image_path: str, output_path: str):
        # Start up pygame
        pygame.init()
        _ = pygame.display.set_mode((1, 1), pygame.NOFRAME)
        self.bg_image = pygame.image.load(bg_image_path).convert_alpha()
        self.bg_width, self.bg_height = self.bg_image.get_size()

        self.output_path = output_path
        self.font_colour = (255, 255, 0)

    def generate_clue(self, text_input: list[str], line_space: int = 2, scalar: int = 3, font_size: int = 48):
        bg_image = pygame.transform.scale(self.bg_image, (self.bg_width * scalar, self.bg_height * scalar))
        font = pygame.font.SysFont("Runescape Chat '07 Regular", font_size)

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

        pygame.image.save(bg_image, self.output_path)
