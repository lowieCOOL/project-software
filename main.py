import pygame
import json
import math
import random as rand
import os
from scipy.ndimage import gaussian_filter
from aircraft import Departure
from airport_mapper import *
from aircraft_generator import generate_flight, read_schedule, read_performance, read_runways
import pygame_widgets
from aircraft import *
# from sidebar_ import *
from geopy.distance import geodesic, distance

json_file_name = "osm_data.json"
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
PADDING = 50 #offset boven en onder
BG_COLOR = (30, 30, 30)  # Dark background
BLUE = (60, 160, 237)
GRAY = (169, 169, 169)

#START SCREEN BACKGROUND
image_path = "assets\\RADAR.jpg"
background_image = pygame.image.load(image_path).convert()
background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

# plane icon sizer als we inzoomen
def update_plane_icon_scale():
    global target  # Zorg dat we de globale `target` variabele aanpassen

    size_plane = 75  # meter
    height_p = HEIGHT - 2 * PADDING
    height_m = geodesic((limits[0][0], limits[1][0]), (limits[0][1], limits[1][0])).meters  # calculate_distance(network['all_nodes'], (limits[0][0], limits[1][0]), (limits[0][1], limits[1][0]))
    x = height_p / height_m * size_plane
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

show_select_aiport_buttons = True
show_start_button = False
rect_startbutton = pygame.Rect(0, 0, 0, 0)
rect_backbutton = pygame.Rect(0, 0, 0, 0)
rect_zoomreset = pygame.Rect(0, 0, 0, 0)

#vergrootglas tekenen
magnifying_glass = pygame.image.load("assets/img.png").convert_alpha()
magnifying_glass = pygame.transform.smoothscale( magnifying_glass, (50, 50))  # Pas grootte aan
rect_zoomreset = screen.blit(magnifying_glass, (WIDTH-90,40))

rects = []
airport_names = []


current_freq = 50  # Startfreq
current_freq_text = f"{str(current_freq).zfill(2)}"
aircraft_list = []
game_started = False
last_time_aircraft = time.time()

# Cache the list of airports before the game loop
airports = os.listdir("airports")

# Define the size and position of the miniature map
MINI_MAP_WIDTH = 300
MINI_MAP_HEIGHT = 200
MINI_MAP_PADDING = 10  # Padding from the bottom-right corner

def calculate_mini_map_limits(network, spawn_height=3000, padding=10):
    distance_to_threshold = (spawn_height - 50) / math.tan(math.radians(3))
    lats = []
    lons = []
    for key, runway in network['runways'].items():
        heading = runway['angle']
        threshold = runway['threshold']
        pos = distance(feet=-distance_to_threshold).destination(network['all_nodes'][threshold], heading)
        lats.append(pos.latitude)
        lons.append(pos.longitude)
    limits = [[min(lats), max(lats)], [min(lons), max(lons)]]
    return limits

# Function to draw the miniature map
def draw_mini_map(screen, all_nodes, osm_data, aircraft_list, limits, padding):
    mini_map_surface = pygame.Surface((MINI_MAP_WIDTH, MINI_MAP_HEIGHT))
    mini_map_surface.fill((50, 50, 50))  # Background color for the mini-map

    # Draw runways on the miniature map
    for element in osm_data["elements"]:
        if element["type"] == "way" and "nodes" in element and element["tags"].get("aeroway") == "runway":
            points = [
                latlon_to_screen(
                    (all_nodes[n][0], all_nodes[n][1]),
                    limits,
                    MINI_MAP_WIDTH,
                    MINI_MAP_HEIGHT,
                    0
                )
                for n in element["nodes"] if n in all_nodes
            ]

            if points:
                pygame.draw.lines(mini_map_surface, (200, 200, 200), False, points, 2)

    # Draw aircraft on the miniature map
    for aircraft in aircraft_list:
        x, y = latlon_to_screen(
            aircraft.position,
            limits,
            MINI_MAP_WIDTH,
            MINI_MAP_HEIGHT,
            0
        )
        pygame.draw.circle(mini_map_surface, (255, 0, 0), (x, y), 2)

    # Blit the miniature map onto the main screen
    screen.blit(
        mini_map_surface,
        (WIDTH - MINI_MAP_WIDTH - MINI_MAP_PADDING, HEIGHT - MINI_MAP_HEIGHT - MINI_MAP_PADDING)
    )

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

# process the osm data
network = map_airport(json_file_name, all_nodes)


# read the schedule and performance data
schedule = read_schedule('EBBR')
performance = read_performance()
runway_configs = read_runways("EBBR")
selected_runway_config = '25R/25L'
active_runways = runway_configs[selected_runway_config]['active_runways']
minimap_limits = calculate_mini_map_limits(network, spawn_height=2000, padding=10)

# active runways menu
menu_open = False
menu_toggle_rect = pygame.Rect(WIDTH - 130, 100, 100, 50)  # Rechtsboven
menu_rect = pygame.Rect(WIDTH - 230, 170, 200, 310)  # Menu aan rechterkant
menu_buttons = []

# Create airport buttons before the game loop
airport_buttons = []
rects = []
airport_names = []
button_width = 160
button_height = 80
spacing = 40
num_airports = len(airports)
total_width = num_airports * button_width + (num_airports - 1) * spacing
start_x = (WIDTH - total_width) // 2  # centreer horizontaal

for idx, airport in enumerate(airports):
    x = start_x + idx * (button_width + spacing)
    rect = pygame.Rect(x, HEIGHT - spatie_onder - 28, button_width, button_height)
    text_surface = create_surface_with_text(airport, 30, BLUE, "Arial")
    airport_buttons.append((rect, text_surface))
    rects.append(rect)  # Add the rect to the list
    airport_names.append(airport)  # Add the airport name to the list

# gameloop
running = True
while running:
    clock.tick(60)
    screen.fill(BG_COLOR)
    # als de airport of de startknop wordt geshowed wordt het beginscherm afgebeeld
    if show_select_aiport_buttons or show_start_button:
        screen.blit(background_image, (0, 0))
        screen.blit(text_surface1, ((WIDTH - 546) / 2, 200))
        screen.blit(text_surface2, ((WIDTH - 960) / 2, 300))

    # airport buttons worden getekend
    if show_select_aiport_buttons:
        for rect, text_surface in airport_buttons:
            pygame.draw.rect(screen, GRAY, rect)
            text_width = text_surface.get_width()
            screen.blit(text_surface, (rect.x + button_width // 2 - text_width // 2, HEIGHT - spatie_onder))

        # Event handling
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
                        show_start_button = True
                        show_select_aiport_buttons = False
                        print(selected_airport)

    # Schuifbalk tekenen als de knoppen niet worden weergegeven
    if show_start_button:
        pygame.draw.rect(screen, GRAY, rect_schuifbar)  # Schuifbalk
        pygame.draw.circle(screen, GRAY, ((WIDTH - 500) / 2 + 500, HEIGHT-spatie_onder-68), 7)  # Linker rand
        pygame.draw.circle(screen, GRAY, ((WIDTH - 500) / 2, HEIGHT-spatie_onder-68), 7)  # Rechter rand
        pygame.draw.rect(screen, GRAY, ((WIDTH - 160) / 2, HEIGHT-spatie_onder-225, 160, 80))
        pygame.draw.rect(screen, BLUE, ((WIDTH - 160) / 2, HEIGHT-spatie_onder-225, 160, 80), width=5)
        rect_startbutton = pygame.draw.rect(screen, GRAY, ((WIDTH - 160) / 2, HEIGHT-spatie_onder-25, 160, 80))
        screen.blit(text_surface4, ((WIDTH - 97) / 2, HEIGHT-spatie_onder))
        rect_backbutton = pygame.draw.rect(screen, GRAY, (100, HEIGHT-spatie_onder-30, 160, 80))
        screen.blit(text_surface6, ((100 + 40), HEIGHT-spatie_onder))

        # Schuifknop tekenen
        pygame.draw.circle(screen, BLUE, (handle_x, HEIGHT-spatie_onder-68), handle_bol_radius)
        screen.blit(create_surface_with_text(current_freq_text, 50, BLUE, "Arial Black"),((WIDTH - 63) / 2, HEIGHT-spatie_onder-205))  # breedte = 144
        screen.blit(text_surface5, ((WIDTH - 245) / 2, HEIGHT-spatie_onder-255))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Controleer of de schuifknop wordt ingedrukt
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                
                # Controleer of de startknop is aangeklikt
                if rect_startbutton.collidepoint(pos):
                    show_start_button = False
                    show_select_aiport_buttons = False
                    game_started = True
                    aircraft_list = [
                        generate_flight(schedule, performance, 'departure', active_runways, network)
                        for i in range(int(45 * current_freq / 100))
                    ]
                    last_time_aircraft = time.time()
                    for aircraft in aircraft_list:
                        aircraft.blit_aircraft(screen, target, WIDTH, HEIGHT, limits, PADDING, draw_route=True)

                    for aircraft in aircraft_list:
                        aircraft.network['aircraft_list'] = aircraft_list
                        
                    create_dropdown(screen, screen.get_width()/4, screen.get_height() / 20, screen.get_width()/4,screen.get_height() / 20, 'Arrival', [aircraft.callsign for aircraft in aircraft_list if aircraft.type == 'arrival'],(150, 150, 150), 'down', 'left',aircraft_list)

                #controleer of de back button wordt ingedrukt                
                if rect_backbutton.collidepoint(pos):
                    show_select_aiport_buttons = True
                    show_start_button = False

                # Controleer of de schuifknop wordt aangeklikt
                if pygame.Rect(handle_x - handle_bol_radius, HEIGHT-spatie_onder-68 - handle_bol_radius, 2 * handle_bol_radius, 2 * handle_bol_radius).collidepoint(pos):
                    dragging = True  # Begin met slepen van de schuifknop

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

    # als er op de starknop wordt gedrukt begint het spel
    if not show_select_aiport_buttons and not show_start_button and game_started:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()

                if menu_toggle_rect.collidepoint(pos):
                    menu_open = not menu_open

                if menu_open:
                    for idx, (btn_rect, key) in enumerate(menu_buttons):
                        if btn_rect.collidepoint(pos):
                            active_runways = runway_configs[key]['active_runways']
                            selected_runway_config = key  # sla op wat geselecteerd is
                            print(key)

                # controleren of de zoom standaard knop is ingedrukt
                if rect_zoomreset.collidepoint(pos):
                    min_lat, max_lat = limits_begin[0]
                    min_lon, max_lon = limits_begin[1]
                    limits = [[min_lat, max_lat], [min_lon, max_lon]]
                    update_plane_icon_scale()

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

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    selected = aircraft_list[rand.randint(0, len(aircraft_list)-1)]
                    print(selected.callsign, selected.state)
                    if selected.state == 'gate':
                        selected.pushback('east')
                    elif selected.state == 'hold_pushback':
                        selected.taxi(runway='25R', destination='B1')
                    elif selected.state == 'hold_runway':
                        selected.cross_runway()
                    elif selected.state == 'ready_line_up':
                        selected.line_up()
                    elif selected.state == 'ready_takeoff':
                        selected.takeoff()
                    elif selected.state == 'arrival':
                        selected.land(list(selected.exitsAvailable)[0])
                    elif selected.state == 'ready_taxi_gate':
                        selected.taxi()

        # Draw ways (taxiways, runways, etc.)
        for element in osm_data["elements"]:
            if element["type"] == "way" and "nodes" in element:
                points = [latlon_to_screen(all_nodes[n], limits, WIDTH, HEIGHT, PADDING)
                          for n in element["nodes"] if n in all_nodes]

                if points:
                    if element["tags"]["aeroway"] == "terminal":
                        pygame.draw.polygon(screen, (200, 200, 200), points)
                    elif element["tags"]["aeroway"] == "apron":
                        continue
                    else:
                        pygame.draw.lines(screen, (200, 200, 200), False, points, 2)

        # Draw sidebar
        draw_sidebar(screen)
        

        # draw all aircraft
        for i, aircraft in enumerate(aircraft_list):
            aircraft.tick(aircraft_list)
            if aircraft.state == 'parked':
                aircraft_list[i] = Departure(aircraft.callsign, aircraft.performance, aircraft.gate, network)
            elif aircraft.state == 'go_around' and aircraft.altitude > 3000:
                aircraft.clear_buttons_aircraft()
                aircraft.clear_buttons()                
                aircraft_list.pop(i)
                
            aircraft.blit_aircraft(screen, target, WIDTH, HEIGHT, limits, PADDING, draw_route=aircraft.selected)
            aircraft.information(screen)  
            aircraft.selected = (i==0) 
            if not aircraft.selected:   
                aircraft.clear_buttons()

 # Move selected aircraft to the first position
        # Draw the miniature map
        draw_mini_map(screen, all_nodes, osm_data, aircraft_list, minimap_limits, PADDING)

        # smooth the screen, type of AA
        # smooth_screen(screen, 0.6)

        screen.blit(magnifying_glass, (WIDTH-90,40))
        # Toggle rechthoek
        pygame.draw.rect(screen, (100, 100, 100), menu_toggle_rect)
        screen.blit(create_surface_with_text("RUNWAY", 18, (255, 255, 255), "Arial"), (menu_toggle_rect.x + 10, menu_toggle_rect.y + 10))

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

                #als de knop wordt ingedrukt wordt er een kader rond getekend
                if key == selected_runway_config:
                    pygame.draw.rect(screen, (255, 255, 0), btn_rect, width=3)  # geel kader

                screen.blit(create_surface_with_text(f"{key} ", 22, (255, 255, 255), "Arial"), (btn_rect.x + 10, btn_rect.y + 12))

                menu_buttons.append((btn_rect, key))

        # de vleigtuigen landen afhankelijk van de gegeven frequentie
        dt = time.time() - last_time_aircraft
        if dt > (-1.2 * current_freq + 240):
            aircraft_list.append(
                generate_flight(schedule, performance, 'arrival', active_runways, network))
        last_time_aircraft = time.time()

    #draw the fps in the topright
    fps = clock.get_fps()
    fps_surface = create_surface_with_text(f"FPS: {int(fps)}", 20, (255, 255, 255), "Arial")
    screen.blit(fps_surface, (WIDTH - fps_surface.get_width() - 10, 10))
    pygame_widgets.update(pygame.event.get())
    pygame.display.flip()

pygame.quit()

