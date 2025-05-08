import pygame
import json
import math
import os
from scipy.ndimage import gaussian_filter
from airport_mapper import *
from aircraft_generator import generate_flight, read_schedule, read_performance, read_runways
from geopy.distance import geodesic

json_file_name = "osm_data.json"
# Load OSM JSON data
with open(json_file_name, "r") as file:
    osm_data = json.load(file)

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((0, 0))
pygame.display.set_caption("OSM Airport Map")
original_target = pygame.transform.rotate(pygame.image.load('target.png'),45)
clock = pygame.time.Clock()
WIDTH,HEIGHT = screen.get_size()

# Screen settings
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pygame Text Rendering")
PADDING = 50
BG_COLOR = (30, 30, 30)  # Dark background
BLUE = (60, 160, 237)
GRAY = (169, 169, 169)

#START SCREN BACKGROUND
image_path = "assets\\RADAR.jpg"
background_image = pygame.image.load(image_path).convert()
background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

# plane icon sizer
def update_plane_icon_scale():
    global target  # Zorg dat we de globale `target` variabele aanpassen

    seize_plane = 100  # meter
    height_p = HEIGHT - 2 * PADDING
    print(list(network))
    height_m = geodesic((limits[0][0], limits[1][0]), (limits[0][1], limits[1][0])).meters  # calculate_distance(network['all_nodes'], (limits[0][0], limits[1][0]), (limits[0][1], limits[1][0]))
    x = height_p / height_m * seize_plane
    target = pygame.transform.smoothscale(original_target, (x, x))
# TEXT GENERATOR
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
spatie_onder = 150
rect_schuifbar = pygame.Rect((WIDTH - 500) / 2, HEIGHT-spatie_onder-75, 500, 14)
handle_x = rect_schuifbar.centerx  # Beginpositie van de schuifknop
handle_bol_radius = 20  # Straal van de schuifknop
dragging = False

show_buttons = True
show_button = False
rect1 = pygame.Rect(0, 0, 0, 0)
rect2 = pygame.Rect(0, 0, 0, 0)
rect3 = pygame.Rect(0, 0, 0, 0)

rects = []
airport_names = []

current_freq = 50  # Startfreq
current_freq_text = f"{str(current_freq).zfill(2)}"
aircraft_list = []
game_started = False
last_time_aircraft = time.time()


# Function to convert lat/lon to screen coordinates
def latlon_to_screen(lat, lon, min_lat, max_lat, min_lon, max_lon, width, height, padding, offset_x=0, offset_y=0):
    lat, min_lat, max_lat = lat2y(lat), lat2y(min_lat), lat2y(max_lat)
    lon, min_lon, max_lon = lon2x(lon), lon2x(min_lon), lon2x(max_lon)

    drawable_width = width - 2 * padding
    drawable_height = height - 2 * padding

    #scales the position to be fit to the screen with some padding on the side, the largest of the 2 is taken and the other is offset so it remains in the center
    x_scale = (max_lon - min_lon) / drawable_width
    y_scale = (max_lat - min_lat) / drawable_height
    scale = max(x_scale, y_scale)

    x_offset = (scale - x_scale)* drawable_width / scale / 2  + padding
    y_offset = (scale - y_scale)* drawable_height / scale / 2  + padding

    x = int((lon + offset_x - min_lon) / scale + x_offset)
    y = int(height - (((lat + offset_y - min_lat) / scale) + y_offset))
    return x, y

# function to smooth the screen, type of AA
def smooth_screen(screen, sigma):
    """Apply a gaussian filter to each colour plane"""
    # Get reference pixels for each colour plane and then apply filter
    r = pygame.surfarray.pixels_red(screen)
    gaussian_filter(r, sigma=sigma, mode="nearest", output=r)
    g = pygame.surfarray.pixels_green(screen)
    gaussian_filter(g, sigma=sigma, mode="nearest", output=g)
    b = pygame.surfarray.pixels_blue(screen)
    gaussian_filter(b, sigma=sigma, mode="nearest", output=b)

# Extract bounding box, the max and min from the osm data
all_nodes = {}
min_lat, max_lat = float("inf"), float("-inf")
min_lon, max_lon = float("inf"), float("-inf")

# Collect node data and determine bounds
for element in osm_data["elements"]:
    if element["type"] == "node":
        lat, lon = element["lat"], element["lon"]
        all_nodes[element["id"]] = (lat, lon)
        min_lat, max_lat = min(min_lat, lat), max(max_lat, lat)
        min_lon, max_lon = min(min_lon, lon), max(max_lon, lon)
limits = [[min_lat, max_lat], [min_lon, max_lon]]
limits_begin = [[min_lat, max_lat], [min_lon, max_lon]]



# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((0, 0))
pygame.display.set_caption("OSM Airport Map")
target = pygame.transform.smoothscale(pygame.transform.rotate(pygame.image.load('target.png'),45),(20,20))
clock = pygame.time.Clock()

# process the osm data, generate a route via a few taxiways to show pathfinding
network = map_airport(json_file_name, all_nodes)
path = calculate_via_route(network['taxi_nodes'],all_nodes,5900058194, destination=2425624616, vias=['OUT 2', 'R1', 'OUT 7','W3' , 'Y', 'E3'])
#path = calculate_via_route(network['taxi_nodes'],all_nodes,12435822847, destination=12436227961, vias=['A'])

WIDTH,HEIGHT = screen.get_size()

# read the schedule and performance data and generate 20 departure aircraft, not yet continuous
schedule = read_schedule('EBBR')
performance = read_performance()
runway_configs = read_runways("EBBR")
activate_runways = runway_configs['25R/25L']

# active runways menu
menu_open = False
menu_toggle_rect = pygame.Rect(WIDTH - 130, 100, 100, 50)  # Rechtsboven
menu_rect = pygame.Rect(WIDTH - 230, 170, 200, 310)  # Menu aan rechterkant
menu_buttons = []



# gameloop
running = True
while running:
    clock.tick(60)
    screen.fill(BG_COLOR)

    # smooth the screen, type of AA
    smooth_screen(screen, 0.6)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Controleer voor muisklikken
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()

            if menu_toggle_rect.collidepoint(pos):
                menu_open = not menu_open

            if menu_open:
                for idx, btn in enumerate(menu_buttons):
                    if btn.collidepoint(pos):
                        print(f"Knop {idx + 1} geklikt")

            # Controleer of een airportknop is aangeklikt
            for idx, rect in enumerate(rects):
                if rect.collidepoint(pos):  # Check of er op een knop is geklikt
                    selected_airport = airport_names[idx]
                    show_button = True
                    show_buttons = False
                    print(selected_airport)

            # controleren of de zoom standaard knop is ingedrukt
            if rect3.collidepoint(pos):
                min_lat, max_lat = limits_begin[0]
                min_lon, max_lon = limits_begin[1]
                limits = [[min_lat, max_lat], [min_lon, max_lon]]
                update_plane_icon_scale()

            # Controleer of de startknop is aangeklikt
            if rect1.collidepoint(pos):
                show_button = False
                show_buttons = False
                game_started = True
                aircraft_list = [
                    generate_flight(schedule, performance, 'departure', all_nodes, activate_runways, network)
                    for i in range(int(45 * current_freq / 100))
                ]
                last_time_aircraft = time.time()

            #controleer of de back button wordt ingedrukt
            if rect2.collidepoint(pos):
                show_buttons = True
                show_button = False


            # Controleer of de schuifknop wordt aangeklikt
            if pygame.Rect(handle_x - handle_bol_radius, HEIGHT-spatie_onder-68 - handle_bol_radius, 2 * handle_bol_radius, 2 * handle_bol_radius).collidepoint(pos):
                dragging = True  # Begin met slepen van de schuifknop

        # controleren op scrollen
        elif event.type == pygame.MOUSEWHEEL:

            zoom_factor = 0.6 if event.y > 0 else 1.4  # Scroll omhoog = inzoomen, omlaag = uitzoomen

            # Bereken center

            center_lat = (min_lat + max_lat) / 2
            center_lon = (min_lon + max_lon) / 2
            lat_range = (max_lat - min_lat) * zoom_factor
            lon_range = (max_lon - min_lon) * zoom_factor
            min_lat = center_lat - lat_range / 2
            max_lat = center_lat + lat_range / 2
            min_lon = center_lon - lon_range / 2
            max_lon = center_lon + lon_range / 2
            limits = [[min_lat, max_lat], [min_lon, max_lon]]

            update_plane_icon_scale()


        #als er geklikt en gesleept wordt beweegt de achtergrond
        elif event.type == pygame.MOUSEMOTION and pygame.mouse.get_pressed()[2]:
            dx, dy = event.rel  # pixels verschuiving
            lat_range = max_lat - min_lat
            lon_range = max_lon - min_lon

            delta_lat = dy / HEIGHT * lat_range
            delta_lon = -dx / WIDTH * lon_range

            min_lat += delta_lat
            max_lat += delta_lat
            min_lon += delta_lon
            max_lon += delta_lon

            limits = [[min_lat, max_lat], [min_lon, max_lon]]



        # Stop met slepen bij muisklik loslaten
        elif event.type == pygame.MOUSEBUTTONUP:
            dragging = False  # Stop met slepen
            moving = False

        # Verplaats de schuifknop als er wordt gesleept
        elif event.type == pygame.MOUSEMOTION:
            if dragging:
                handle_x = event.pos[0] - handle_bol_radius  # Verplaats de schuifknop horizontaal

                # Beperk de beweging binnen de schuifbalk
                handle_x = max(rect_schuifbar.left, min(handle_x, rect_schuifbar.right ))
                new_freq = int((handle_x - rect_schuifbar.left) / rect_schuifbar.width * 100)
                current_freq = new_freq
                current_freq_text = f"{str(current_freq).zfill(2)}"

    # als de airport of de startknop wordt geshowed wordt het beginscherm afgebeeld
    if show_buttons or show_button:
        screen.blit(background_image, (0, 0))
        screen.blit(text_surface1, ((WIDTH - 546) / 2, 200))
        screen.blit(text_surface2, ((WIDTH - 960) / 2, 300))

    # airport buttons worden getekend
    if show_buttons:
        airports = os.listdir("airports")
        i = 0
        num_airports = len(airports)
        button_width = 160
        button_height = 80
        spacing = 40

        total_width = num_airports * button_width + (num_airports - 1) * spacing
        start_x = (WIDTH - total_width) // 2  # centreer horizontaal

        for idx, airport in enumerate(airports):
            x = start_x + idx * (button_width + spacing)
            rect = pygame.draw.rect(screen, GRAY, (x, HEIGHT-spatie_onder-28, button_width, button_height))

            text_surface = create_surface_with_text(airport, 30, BLUE, "Arial")
            text_width = text_surface.get_width()
            screen.blit(text_surface, (x + button_width // 2 - text_width // 2, HEIGHT-spatie_onder))

            rects.append(rect)
            airport_names.append(airport)

    # Schuifbalk tekenen als de knoppen niet worden weergegeven
    if show_button:
        pygame.draw.rect(screen, GRAY, rect_schuifbar)  # Schuifbalk
        pygame.draw.circle(screen, GRAY, ((WIDTH - 500) / 2 + 500, HEIGHT-spatie_onder-68), 7)  # Linker rand
        pygame.draw.circle(screen, GRAY, ((WIDTH - 500) / 2, HEIGHT-spatie_onder-68), 7)  # Rechter rand
        pygame.draw.rect(screen, GRAY, ((WIDTH - 160) / 2, HEIGHT-spatie_onder-225, 160, 80))
        pygame.draw.rect(screen, BLUE, ((WIDTH - 160) / 2, HEIGHT-spatie_onder-225, 160, 80), width=5)
        rect1 = pygame.draw.rect(screen, GRAY, ((WIDTH - 160) / 2, HEIGHT-spatie_onder-25, 160, 80))
        screen.blit(text_surface4, ((WIDTH - 97) / 2, HEIGHT-spatie_onder))
        rect2 = pygame.draw.rect(screen, GRAY, (100, HEIGHT-spatie_onder-30, 160, 80))
        screen.blit(text_surface6, ((100 + 40), HEIGHT-spatie_onder))

        # Schuifknop tekenen
        pygame.draw.circle(screen, BLUE, (handle_x, HEIGHT-spatie_onder-68), handle_bol_radius)
        screen.blit(create_surface_with_text(current_freq_text, 50, BLUE, "Arial Black"),((WIDTH - 63) / 2, HEIGHT-spatie_onder-205))  # breedte = 144
        screen.blit(text_surface5, ((WIDTH - 245) / 2, HEIGHT-spatie_onder-255))

    # als er op de starknop wordt gedrukt begint het spel
    if not show_buttons and not show_button and game_started:

        #vergrootglas tekenen
        image_path2 = pygame.image.load("assets/img.png").convert_alpha()
        image_path2 = pygame.transform.smoothscale( image_path2, (50, 50))  # Pas grootte aan
        rect3 = screen.blit(image_path2, (WIDTH-90,40))

        # Draw ways (taxiways, runways, etc.)
        for element in osm_data["elements"]:
            if element["type"] == "way" and "nodes" in element:
                points = [latlon_to_screen(all_nodes[n][0], all_nodes[n][1], min_lat, max_lat, min_lon, max_lon, WIDTH, HEIGHT, PADDING)
                          for n in element["nodes"] if n in all_nodes]

                if points:
                    if element["tags"]["aeroway"] == "terminal":
                        pygame.draw.polygon(screen, (200, 200, 200), points)
                    elif element["tags"]["aeroway"] == "apron":
                        continue
                    else:
                        pygame.draw.lines(screen, (200, 200, 200), False, points, 2)

        # Toggle rechthoek
        pygame.draw.rect(screen, (100, 100, 100), menu_toggle_rect)
        screen.blit(create_surface_with_text("RUNWAY", 18, (255, 255, 255), "Arial"),
                    (menu_toggle_rect.x + 10, menu_toggle_rect.y + 10))

        # Teken menu als het open is
        if menu_open:
            pygame.draw.rect(screen, (30, 30, 30), menu_rect)
            pygame.draw.rect(screen, (255, 255, 255), menu_rect, width=2)

            menu_buttons.clear()
            button_height = 50
            for i, key in enumerate(runway_configs):

                btn_rect = pygame.Rect(menu_rect.left + 10, menu_rect.top + 10 + i * (button_height + 10),
                                       menu_rect.width - 20, button_height)
                pygame.draw.rect(screen, (70, 130, 180), btn_rect)
                screen.blit(create_surface_with_text(f"{key} ", 22, (255, 255, 255), "Arial"),
                            (btn_rect.x + 10, btn_rect.y + 12))
                menu_buttons.append(btn_rect)


        # draw all aircraft
        for i in aircraft_list:
            i.blit_aircraft(screen, target, limits, PADDING)

        # de vleigtuigen landen afhankelijk van de gegeven frequentie
        dt = time.time() - last_time_aircraft
        if dt > (-1.2 * current_freq + 240):
            aircraft_list.append(
                generate_flight(schedule, performance, 'arrival', all_nodes, activate_runways, network))
            last_time_aircraft = time.time()

    pygame.display.flip()

pygame.quit()
