import pygame
import json
import math
from scipy.ndimage import gaussian_filter
from airport_mapper import *
from aircraft_generator import generate_flight, read_schedule, read_performance
from sidebar import *
import pygame_widgets

json_file_name = "osm_data.json"
# Load OSM JSON data
with open(json_file_name, "r") as file:
    osm_data = json.load(file)

# Screen settings
PADDING = 50
WIDTH, HEIGHT = 1280, 800
BG_COLOR = (30, 30, 30)  # Dark background

# Function to convert lat/lon to screen coordinates
def latlon_to_screen(lat, lon, min_lat, max_lat, min_lon, max_lon, width, height, padding, offset_x=0, offset_y=0):
    lat, min_lat, max_lat = lat2y(lat), lat2y(min_lat), lat2y(max_lat)
    lon, min_lon, max_lon = lon2x(lon), lon2x(min_lon), lon2x(max_lon)

    drawable_width = width * (3/4) - padding #*2
    drawable_height = height -  padding #*2

    #scales the position to be fit to the screen with some padding on the side, the largest of the 2 is taken and the other is offset so it remains in the center
    x_scale = (max_lon - min_lon) / drawable_width 
    y_scale = (max_lat - min_lat) / drawable_height
    scale = max(x_scale  , y_scale)

    x_offset = (scale - x_scale)* drawable_width / scale / 2  + padding - (width * (1/4) - drawable_width) / 2 
    y_offset = (scale - y_scale)* drawable_height / scale / 2  + padding #*2

    x = int((lon + offset_x - min_lon) / scale + x_offset)
    y = int(height - (((lat + offset_y - min_lat) / scale) + y_offset))
    return x, y 

def smooth_screen(screen, sigma):
    """Apply a gaussian filter to each colour plane"""
    # Get reference pixels for each colour plane and then apply filter
    r = pygame.surfarray.pixels_red(screen)
    gaussian_filter(r, sigma=sigma, mode="nearest", output=r)
    g = pygame.surfarray.pixels_green(screen)
    gaussian_filter(g, sigma=sigma, mode="nearest", output=g)
    b = pygame.surfarray.pixels_blue(screen)
    gaussian_filter(b, sigma=sigma, mode="nearest", output=b)

# Extract bounding box
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

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((0, 0))
pygame.display.set_caption("OSM Airport Map")
target = pygame.transform.smoothscale(pygame.transform.rotate(pygame.image.load('target.png'),45),(20,20))
clock = pygame.time.Clock()

network = map_airport(json_file_name, all_nodes)
path = calculate_via_route(network['taxi_nodes'],all_nodes,5900058194, destination=2425624616, vias=['OUT 2', 'R1', 'OUT 7','W3',  'Y'])
#path = calculate_via_route(network['taxi_nodes'],all_nodes,12435822847, destination=12436227961, vias=['A'])


schedule = read_schedule('EBBR')
performance = read_performance()
activate_runways = ['25R', '25L']
aircraft = generate_flight(schedule, performance, 'departure', activate_runways, network)
print(aircraft.callsign)
print(network['gates'][aircraft.gate])

WIDTH, HEIGHT = screen.get_size()

running = True
while running:
    clock.tick(60)
    screen.fill(BG_COLOR)

    if path != None:
        # Draw ways (taxiways, runways, etc.)
        for element in osm_data["elements"]:
            if element["type"] == "way" and "nodes" in element:
                points = [latlon_to_screen(all_nodes[n][0], all_nodes[n][1], min_lat, max_lat, min_lon, max_lon, WIDTH, HEIGHT, PADDING) for n in element["nodes"] if n in all_nodes]

                if points:
                    if element["tags"]["aeroway"] == "terminal":
                        pygame.draw.polygon(screen, (200, 200, 200), points)
                    else:
                        pygame.draw.lines(screen, (200, 200, 200), False, points, 2)

        points = [latlon_to_screen(all_nodes[n][0], all_nodes[n][1], min_lat, max_lat, min_lon, max_lon, WIDTH, HEIGHT, PADDING) for n in path if n in all_nodes]
        if points:
            pygame.draw.lines(screen, (255, 0, 0), False, points, 2)

    screen.blit(target, (WIDTH/2, HEIGHT/2))

    # Draw sidebar
    sidebar(screen)
    dropdown.draw(screen)
    
    
    # smooth the screen, type of AA
    smooth_screen(screen, 0.6)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
    pygame_widgets.update(pygame.event.get())
    pygame.display.flip()

pygame.quit()
