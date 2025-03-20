import pygame
import pygame.freetype

pygame.init()
pygame.freetype.init()

WIDTH, HEIGHT = 1920, 1020
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pygame Text Rendering")

BLUE = (60, 160, 237)
GRAY = (169, 169, 169)

image_path = r"C:\Users\matsd\Downloads\RADAR.jpg"
background_image = pygame.image.load(image_path).convert()
background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

def create_surface_with_text(text, font_size, text_rgb, font):
    font = pygame.freetype.SysFont(font, font_size)
    surface, _ = font.render(text=text, fgcolor=text_rgb)
    return surface.convert_alpha()

text_surface1 = create_surface_with_text("Air Traffic", 100, BLUE, "Arial Black")   # hoogte = 100, breedte = 546
text_surface2 = create_surface_with_text("Control Simulator", 100, BLUE, "Arial Black")  # hoogte = 100, breedte = 960
text_surface3 = create_surface_with_text("START", 30, BLUE, "Arial")
text_surface4 = create_surface_with_text("EBBR", 30, BLUE, "Arial")

show_button = True

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            if show_button and rect.collidepoint(pos):
                print("clicked on rectangle")
                show_button = False


    screen.blit(background_image, (0, 0))

    screen.blit(text_surface1, ((WIDTH - 546) / 2, 200))
    screen.blit(text_surface2, ((WIDTH - 960) / 2, 300))

    rect = pygame.draw.rect(screen, GRAY, ((WIDTH - 160) / 2, 800, 160, 80))

    if show_button:
        screen.blit(text_surface3, ((WIDTH - 97) / 2, 825))  #breedte START = 97

    if not show_button:
        screen.blit(text_surface4, ((WIDTH - 80) / 2, 825)) #breedte EBBR = 80
    pygame.display.flip()



    #text_width = text_surface4.get_width()
    #print("De breedte van de tekst is:", text_width)

pygame.quit()
