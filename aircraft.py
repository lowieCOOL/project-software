'''
Aircraft states:
for departures
- gate
- pushback
- hold_pushback
- taxi
- hold_taxi
- hold_runway
- line_up
- takeoff

for arrivals
- approach
- go_around
- roll_out
- vacate
- taxi_to_gate
- hold_taxi
- parked

'''
from airport_mapper import lon2x, lat2y
import pygame
import math
from pygame_widgets.button import Button

def latlon_to_screen(pos, limits, width, height, padding, offset_x=0, offset_y=0):
    y, min_y, max_y = lat2y(pos[0]), lat2y(limits[0][0]), lat2y(limits[0][1])
    x, min_x, max_x = lon2x(pos[1]), lon2x(limits[1][0]), lon2x(limits[1][1])

    drawable_width = width*(3/4) -  padding
    drawable_height = height - 2*padding

    
    x_scale = (max_x - min_x) / drawable_width
    y_scale = (max_y - min_y) / drawable_height
    scale = max(x_scale, y_scale)

    x_offset = (scale - x_scale) * drawable_width / scale / 2 + padding + width * (1/4)
    y_offset = (scale - y_scale) * drawable_height / scale / 2 + padding

    x = int((x + offset_x - min_x) / scale + x_offset)
    y = int(height - (((y + offset_y - min_y) / scale) + y_offset))
    return x, y

class Aircraft():
    def __init__(self, position, heading, speed, state, callsign, performance):
        self.position = position
        self.heading = heading
        self.speed = speed
        self.state = state
        self.callsign = callsign
        self.route = []
        self.rect = None
        self.performance = performance
        
    def blit_aircraft(self, screen, png, WIDTH, HEIGHT, limits, padding):
        coords = latlon_to_screen(self.position, limits, WIDTH, HEIGHT, padding)

        # Convert aviation heading to Pygame's counterclockwise system
        pygame_angle = -self.heading
        angle_rad = math.radians(-self.heading)

        # Get original image size
        orig_width, orig_height = png.get_size()
        image_offset = (math.sin(angle_rad)*orig_height/2, math.cos(angle_rad)*orig_height/2)

        # Rotate image
        rotated_image = pygame.transform.rotate(png, pygame_angle)
        new_pos = tuple(coords[i] + image_offset[i] for i in range(2))

        # Get new bounding box after rotation
        new_rect = rotated_image.get_rect(center=new_pos)
        self.rect = new_rect

        # Blit rotated image
        self.button(screen)
        screen.blit(rotated_image, new_rect.topleft)
        

    def button(self, screen):
        # Check if the button already exists
        if not hasattr(self, 'button_instance'):
            # Create and store the button
            self.button_instance = Button(
                screen,
                self.rect.centerx,  # Center X position
                self.rect.centery,  # Center Y position
                self.rect.width /4,       # Width
                self.rect.height /4,      # Height
                onClick=lambda: self.click_handler(),
                inactiveColour=(255, 223, 63),  # Yellow color
                pressedColour=(255, 212, 0),   # Darker yellow when pressed
                hoverColour=(255, 212, 0),     # Darker yellow when hovered
                radius=0  # Set radius to 0 for a plain rectangle
            )
        else:
            # Update the button's position if it already exists
            self.button_instance.setX(self.rect.centerx )
            self.button_instance.setY(self.rect.centery )
            
    def click_handler(self):
        print('clicked on aircraft', self.callsign)

    def calculate_route(self):
        pass

    def calculate_via_route(self):
        pass

    def follow_route(self):
        # code to have an aircraft moving along the nodes in self.route
        pass

    def hold_position(self):
        # code to have an aircraft stop at current position
        pass

    def continue_taxi(self):
        if self.state != 'hold_taxi':
            return

        # code to have an aircraft continue taxiing
        pass

    def tick(self):
        pass

class Arrival(Aircraft):
    def __init__(self, callsign, performance, runway, network):
        super().__init__(position=network['runways'][runway]['init_offset_from_threshold'], heading=network['runways'][runway]['angle'], speed=200, state='arrival' , callsign=callsign, performance=performance)
        self.runway  = network['runways'][runway]
        self.exitsAvailable = {key: item for key, item in self.runway['exits'].items() if item['LDA'] > self.performance['LDA']}
        self.altitude = 3000

    def go_around(self):
        pass

    def land(self):
        pass

class Departure(Aircraft):
    def __init__(self, callsign, performance, gate, network, all_nodes):
        # TODO: add performance parameters or one single parameter for the aircraft and split it in the constructor
        super().__init__(position=all_nodes[network['gates'][gate]['nodes'][0]], heading=network['gates'][gate]['heading'], speed=0, state='gate', callsign=callsign, performance=performance)
        self.gate = gate
        self.all_nodes = all_nodes

    def pushback(self, direction):
        # pushback
        self.state = 'pushback'
        options = ['north', 'east', 'south', 'west']
        if direction not in options:
            raise ValueError(f"Direction must be one of {options}")

        # after pushback, set state to taxi
        self.state = 'hold_pushback'

    def taxi(self, destination, vias=None):
        #destination is a runway exit name, get the destination node from network['runways']
        pass

    def line_up(self):
        # line up on the runway
        pass

    def takeoff(self):
        if self.state == 'taxi':
            self.line_up()
        
        # takeoff
        pass

if __name__ == '__main__':
    pass