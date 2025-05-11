import pygame
import json
import math
import random as rand
import os
from scipy.ndimage import gaussian_filter
from aircraft import Departure
from airport_mapper import *
from aircraft_generator import generate_flight, read_schedule, read_performance
import pygame_widgets
from aircraft import *
# from sidebar_ import *
from geopy.distance import distance

json_file_name = "osm_data.json"
json_file_name = "osm_data.json"
# Load OSM JSON data
with open(json_file_name, "r") as file:
    osm_data = json.load(file)

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((0, 0))
pygame.display.set_caption("OSM Airport Map")
target = pygame.transform.smoothscale(pygame.transform.rotate(pygame.image.load('target.png'),45),(20,20))
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

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((0, 0))
pygame.display.set_caption("OSM Airport Map")
target = pygame.transform.smoothscale(pygame.transform.rotate(pygame.image.load('target.png'),45),(20,20))
clock = pygame.time.Clock()

# process the osm data, generate a route via a few taxiways to show pathfinding
network = map_airport(json_file_name, all_nodes)
path = None
#path = calculate_via_route(network['taxi_nodes'],all_nodes,5900058194, destination=2425624616, vias=['OUT 2', 'R1', 'OUT 7','W3' , 'Y', 'E3'])
#path = calculate_via_route(network['taxi_nodes'],all_nodes,12435822847, destination=12436227961, vias=['A'])


# read the schedule and performance data and generate 20 departure aircraft, not yet continuous
schedule = read_schedule('EBBR')
performance = read_performance()
active_runways = ['25R', '25L']
aircraft_list = [generate_flight(schedule, performance, 'arrival', active_runways, network)] + [generate_flight(schedule, performance, 'departure', active_runways, network) for i in range(2)]
minimap_limits = calculate_mini_map_limits(network, spawn_height=2000, padding=10)

for aircraft in aircraft_list:
    aircraft.network['aircraft_list'] = aircraft_list
    
create_dropdown(screen, screen.get_width()/4, screen.get_height() / 20, screen.get_width()/4,screen.get_height() / 20, 'Arrival', [aircraft.callsign for aircraft in aircraft_list if aircraft.type == 'arrival'],(150, 150, 150), 'down', 'left',aircraft_list)
# gameloop
running = True
while running:
    clock.tick(60)
    screen.fill(BG_COLOR)

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
                    show_buttons = False
                    show_button = True
                    print(selected_airport)
                    break

            # Controleer of de startknop is aangeklikt
            if rect1.collidepoint(pos):
                show_button = False
                for aircraft in aircraft_list:
                    aircraft.blit_aircraft(screen, target, WIDTH, HEIGHT, limits, PADDING, draw_route=True)

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
    if show_button:
        pygame.draw.rect(screen, GRAY, rect_schuifbar)  # Schuifbalk
        pygame.draw.circle(screen, GRAY, ((WIDTH - 500) / 2 + 500, 807), 7)  # Linker rand
        pygame.draw.circle(screen, GRAY, ((WIDTH - 500) / 2, 807), 7)  # Rechter rand
        pygame.draw.rect(screen, GRAY, ((WIDTH - 160) / 2, 650, 160, 80))
        pygame.draw.rect(screen, BLUE, ((WIDTH - 160) / 2, 650, 160, 80), width=5)
        rect1 = pygame.draw.rect(screen, GRAY, ((WIDTH - 160) / 2, 850, 160, 80))
        screen.blit(text_surface4, ((WIDTH - 97) / 2, 875))
        rect2 = pygame.draw.rect(screen, GRAY, (100, 845, 160, 80))
        screen.blit(text_surface6, ((100 + 40), 875))

        # Schuifknop tekenen
        pygame.draw.circle(screen, BLUE, (handle_x, 807), handle_bol_radius)
        screen.blit(create_surface_with_text(current_freq_text, 50, BLUE, "Arial Black"),((WIDTH - 63) / 2, 670))  # breedte = 144
        screen.blit(text_surface5, ((WIDTH - 245) / 2, 620))

    if not show_buttons and not show_button:
        # Draw ways (taxiways, runways, etc.)
        for element in osm_data["elements"]:
            if element["type"] == "way" and "nodes" in element:
                points = [latlon_to_screen(all_nodes[n], limits, WIDTH,
                                           HEIGHT, PADDING)
                          for n in element["nodes"] if n in all_nodes]

                if points:
                    if element["tags"]["aeroway"] == "terminal":
                        pygame.draw.polygon(screen, (200, 200, 200), points)
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
        smooth_screen(screen, 0.6)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
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
                
        pygame_widgets.update(pygame.event.get())
    pygame.display.flip()

pygame.quit()

