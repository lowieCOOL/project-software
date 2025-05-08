import pygame
import pygame.freetype
import os

pygame.init()
pygame.freetype.init()

WIDTH, HEIGHT = 1920, 1020
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pygame Text Rendering")

BLUE = (60, 160, 237)
GRAY = (169, 169, 169)

image_path = "assets\\RADAR.jpg"
background_image = pygame.image.load(image_path).convert()
background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

def create_surface_with_text(text, font_size, text_rgb, font):
    font = pygame.freetype.SysFont(font, font_size)
    surface, _ = font.render(text=text, fgcolor=text_rgb)
    return surface.convert_alpha()

text_surface1 = create_surface_with_text("Air Traffic", 100, BLUE, "Arial Black")  # hoogte = 100, breedte = 546
text_surface2 = create_surface_with_text("Control Simulator", 100, BLUE, "Arial Black")  # hoogte = 100, breedte = 960
text_surface4 = create_surface_with_text("START", 30, BLUE, "Arial") # breedte "start" = 97
text_surface5 = create_surface_with_text("FREQUENTIE (%)", 30, BLUE, "Arial") # breedte "FREQUENTIE (%)" = 245
text_surface6 = create_surface_with_text("BACK", 30, BLUE, "Arial") # breedte "BACK" = 80

# Initialisatie van schuifknop
rect_schuifbar = pygame.Rect((WIDTH - 500) / 2, 800, 500, 14)
handle_x = rect_schuifbar.centerx  # Beginpositie van de schuifknop
handle_bol_radius = 20  # Straal van de schuifknop
dragging = False

show_buttons = True
show_button = False
rect1 = pygame.Rect(0, 0, 0, 0)
rect2 = pygame.Rect(0, 0, 0, 0)
rects = []
airport_names = []

current_freq = 50  # Startfreq
current_freq_text = f"{str(current_freq).zfill(2)}"

# Eventloop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Controleer voor muisklikken
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()

            # Controleer of een airportknop is aangeklikt
            for idx, rect in enumerate(rects):
                if rect.collidepoint(pos):  # Check of er op een knop is geklikt
                    selected_airport = airport_names[idx]
                    show_buttons = False
                    show_button = True
                    print(selected_airport)
                    break

            # Controleer of de startknop is aangeklikt
            if rect1.collidepoint(pos):
                show_button = False

            if rect2.collidepoint(pos):
                show_button = False
                show_buttons = True


            # Controleer of de schuifknop wordt aangeklikt
            if pygame.Rect(handle_x - handle_bol_radius, 807 - handle_bol_radius, 2 * handle_bol_radius, 2 * handle_bol_radius).collidepoint(pos):
                dragging = True  # Begin met slepen van de schuifknop

        # Stop met slepen bij muisklik loslaten
        elif event.type == pygame.MOUSEBUTTONUP:
            dragging = False  # Stop met slepen

        # Verplaats de schuifknop als er wordt gesleept
        elif event.type == pygame.MOUSEMOTION:
            if dragging:
                handle_x = event.pos[0] - handle_bol_radius  # Verplaats de schuifknop horizontaal

                # Beperk de beweging binnen de schuifbalk
                handle_x = max(rect_schuifbar.left, min(handle_x, rect_schuifbar.right ))
                new_freq = int((handle_x - rect_schuifbar.left) / rect_schuifbar.width * 100)
                current_freq = new_freq
                current_freq_text = f"{str(current_freq).zfill(2)}"



    if show_buttons or show_button:
        screen.blit(background_image, (0, 0))
        screen.blit(text_surface1, ((WIDTH - 546) / 2, 200))
        screen.blit(text_surface2, ((WIDTH - 960) / 2, 300))

    if show_buttons:
        airports = os.listdir("airports")
        i = 0

        for airport in airports:
            i += 1
            j = WIDTH - len(airports) * 160 + (len(airports) - 1) * 40
            text_surface3 = create_surface_with_text(airport, 30, BLUE, "Arial")
            text_width = text_surface3.get_width()
            rect = pygame.draw.rect(screen, GRAY, (j / 2 + 200 * (i - 1) - 80, 800, 160, 80))
            screen.blit(text_surface3, (j / 2 + 200 * (i - 1) - text_width / 2, 827))
            rects.append(rect)
            airport_names.append(airport)

    # Schuifbalk tekenen als de knoppen niet worden weergegeven
    if   show_button:
        pygame.draw.rect(screen, GRAY, rect_schuifbar)  # Schuifbalk
        pygame.draw.circle(screen, GRAY,  ((WIDTH - 500) / 2 + 500, 807), 7)  # Linker rand
        pygame.draw.circle(screen, GRAY,  ((WIDTH - 500) / 2 , 807), 7)  # Rechter rand
        pygame.draw.rect(screen, GRAY, ((WIDTH-160)/2, 650, 160, 80))
        pygame.draw.rect(screen, BLUE, ((WIDTH - 160) / 2, 650, 160, 80), width=5)
        rect1 = pygame.draw.rect(screen, GRAY, ((WIDTH - 160) / 2, 850, 160, 80))
        screen.blit(text_surface4, ((WIDTH - 97) / 2, 875))
        rect2 = pygame.draw.rect(screen, GRAY, (100, 845, 160, 80))
        screen.blit(text_surface6, ((100+40), 875))

        # Schuifknop tekenen
        pygame.draw.circle(screen, BLUE, (handle_x, 807), handle_bol_radius)
        screen.blit(create_surface_with_text(current_freq_text, 50, BLUE, "Arial Black"), ((WIDTH - 63) / 2, 670))  #breedte = 144
        screen.blit(text_surface5, ((WIDTH - 245) / 2, 620))

    #text_width = text_surface6.get_width()
    #print("De breedte van de tekst is:", text_width)
    pygame.display.flip()

pygame.quit()
