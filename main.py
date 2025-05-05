import pygame
import json
from scipy.ndimage import gaussian_filter
from airport_mapper import *
from aircraft_generator import generate_flight, read_schedule, read_performance
from sidebar_ import *
import pygame_widgets
from aircraft import *

json_file_name = "osm_data.json"
json_file_name = "osm_data.json"
# Load OSM JSON data
with open(json_file_name, "r") as file:
    osm_data = json.load(file)

# Screen settings
PADDING = 50
WIDTH, HEIGHT = 1280, 800
BG_COLOR = (30, 30, 30)  # Dark background



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
path = calculate_via_route(network['taxi_nodes'],all_nodes,5900058194, destination=2425624616, vias=['OUT 2', 'R1', 'OUT 7','W3' , 'Y', 'E3'])
#path = calculate_via_route(network['taxi_nodes'],all_nodes,12435822847, destination=12436227961, vias=['A'])


# read the schedule and performance data and generate 20 departure aircraft, not yet continuous
schedule = read_schedule('EBBR')
performance = read_performance()
activate_runways = ['25R', '25L']
aircraft = [generate_flight(schedule, performance, 'departure', all_nodes, activate_runways, network) for i in range(20)]

aircraft_list = [i.callsign for i in aircraft if i.state == 'arrival']
# gameloop
running = True
while running:
    clock.tick(60)
    screen.fill(BG_COLOR)

    if path != None:
        # Draw ways (taxiways, runways, etc.)
        for element in osm_data["elements"]:
            if element["type"] == "way" and "nodes" in element:
                points = [latlon_to_screen(all_nodes[n], limits, WIDTH, HEIGHT, PADDING) for n in element["nodes"] if n in all_nodes]

                if points:
                    if element["tags"]["aeroway"] == "terminal":
                        pygame.draw.polygon(screen, (200, 200, 200), points)
                    else:
                        pygame.draw.lines(screen, (200, 200, 200), False, points, 2)

        # draw exemple pathfinding route
        points = [latlon_to_screen(all_nodes[n], limits, WIDTH, HEIGHT, PADDING) for n in path if n in all_nodes]
        if points:
            pygame.draw.lines(screen, (255, 0, 0), False, points, 2)

    # draw all aircraft
    for i in aircraft:
        i.blit_aircraft(screen, target, WIDTH, HEIGHT, limits, PADDING)

    # Draw sidebar
    draw_sidebar(screen)
    DropdownMenu(screen, aircraft_list).create_dropdown()
    
    # smooth the screen, type of AA
    smooth_screen(screen, 0.6)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
    pygame_widgets.update(pygame.event.get())
    pygame.display.flip()

pygame.quit()
