import pygame

lineSpace = 2 # Spacing between lines
scalar = 3 # Background image upscalar
fontSize = 48 # Font size
fontColour =  (255, 255, 0) # Font colour
outputFileName = "generatedClue.png"

def clueFromString(clueText: str) -> None:
    clueFromLines(clueText.split("\n"))

def clueFromLines(clueText: list[str]) -> None:
    pygame.init()
    _ = pygame.display.set_mode((1, 1), pygame.NOFRAME)
    bg = pygame.image.load("blankClue.png").convert_alpha()
    bg = pygame.transform.scale(bg, (bg.get_width() * scalar, bg.get_height() * scalar))
    font = pygame.font.SysFont("Runescape Chat '07 Regular", fontSize)

    srf = pygame.Surface(bg.get_size(), pygame.SRCALPHA)
    srf.blit(bg, (0, 0))

    renderedText = [font.render(text, False, fontColour) for text in clueText]
    textHeight = renderedText[0].get_height()
    totalHeight = (len(renderedText) * (lineSpace + textHeight)) - lineSpace

    topOffset = (bg.get_height() - totalHeight) // 2
    xPos = bg.get_width() // 2
    for idx, text in enumerate(renderedText):
        yPos = topOffset + (idx * (textHeight + lineSpace))
        rct = text.get_rect()
        rct.midtop = (xPos, yPos)
        srf.blit(text, rct)

    pygame.image.save(srf, outputFileName)
