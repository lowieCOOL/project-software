'''
These are the aircraft states and actions that can be performed on

Aircraft states:
for departures
- pushback
- pushback_complete
- cleared_takeoff
- takeoff
- gate
    - aircraft.pushback(direction) direction is [north, east, south, west]
- ready_taxi
    - aircraft.taxi(runway, destination, vias=[]) destination is a runway exit name, vias is a list of taxi names to route via
- taxi
    - aircraft.hold_position() hold at the current position, this is used to wait for a crossing aircraft or other reason
    - aircraft.cross_runway() preemptively give clearance to cross runway
    - aircraft.line_up() already give lineup clearance so aircraft doesn't have to stop at the holding point
    - aircraft.takeoff() already give takeoff clearance so aircraft doesn't have to stop at the holding point
- hold_taxi
    - aircraft.continue_taxi() continue taxiing after holding position
- hold_runway
    - aircraft.cross_runway()
- cleared_crossing
    - aircraft.hold_position()
- crossing_runway
- ready_line_up
    - aircraft.line_up()
- line_up
    - aircraft.takeoff()
- ready_takeoff
    - aircraft.takeoff()

for arrivals
- cleared_land
- arrival
    - aircraft.land(exit) land on the runway and vacate at the specified exit
    - aircraft.go_around() go around, abort the landing
- rollout
    - aircraft.taxi(vias=[]) preemtively give taxi to the gate, vias is a list of taxi names to route via
- vacate
    - aircraft.taxi(vias=[]) preemtively give taxi to the gate, vias is a list of taxi names to route via
- vacate_continue
    - aircraft.taxi(vias=[]) continue taxiing after vacating the runway
- ready_taxi_gate
    - aircraft.taxi(vias=[]) taxi to the gate
- taxi
    - aircraft.hold_position() hold at the current position, this is used to wait for a crossing aircraft or other reason
    - aircraft.cross_runway() preemptively give clearance to cross runway
    - aircraft.taxi(vias=[]) vias is a list of taxi names to route via, used to give new route to the aircraft
- hold_taxi
    - aircraft.continue_taxi() continue taxiing after holding position
- hold_runway
    - aircraft.cross_runway()
- cleared_crossing
    - aircraft.hold_position()
- crossing_runway
- park
'''
from airport_mapper import lon2x, lat2y, calculate_angle, angle_difference, calculate_distance
from geopy.distance import distance
import pygame
import math
import time
import queue
from pygame_widgets.button import Button
from pygame_widgets import *
from pygame_widgets.dropdown import Dropdown
from pygame_widgets.textbox import TextBox      
from start_screen import create_surface_with_text

def draw_sidebar(screen):
    # Sidebar dimensions and width
        sidebar_width = screen.get_width() *(1/4) # 1/4 of the screen width
        sidebar_height = screen.get_height()
        pygame.draw.rect(screen, (40,40,40), (0, 0, sidebar_width, sidebar_height)) # 30, 30, 30

# a function to create a dropdown buttons     
def create_dropdown(screen, x, y, WIDTH, HEIGHT, Name, Choices, Colour, Direction, TextHalign, aircraft_list):
    dropdown = Dropdown(
        screen,
        x,
        y,
        WIDTH,
        HEIGHT,
        name=Name,
        choices=Choices,
        colour=Colour,
        direction=Direction,
        textHalign=TextHalign,
        #these are the default values
        font=pygame.font.SysFont('Arial', 20),
        backgroundColour=(255, 255, 255),
        textColour=(0, 0, 0),
        onClick= lambda: dropdown_selection_getter(dropdown.getSelected(), aircraft_list)  
    )

# a setter function to set the selected callsign
def dropdown_selection_getter(selected_callsign, aircraft_list):
    for aircraft in aircraft_list:
        if aircraft.callsign == selected_callsign:
            aircraft.click_handler()
            print('Selected:', aircraft.callsign)
            break
# function to convert latitude and longitude to screen coordinates
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

# class that represents an aircraft
class Aircraft():
    # set the taxi speed to the aircraft preformance
    def taxi_speed(self, taxi_acceleration=1.0, v_end=0):
        WTC = self.performance["WTC"]

        needed_distance = ((self._speed)**2 - (v_end)**2) / (2 * taxi_acceleration)/4
        distance = self.distance_to_destination - self._speed * self.dt

        match WTC:
            case 'L':
                max_taxispeed = 15
            case 'M':
                max_taxispeed = 30
            case 'H':
                max_taxispeed = 20
        # Adjusts the aircraft's speed based on distance to the target and speed limits.
        if distance > needed_distance and self._speed < max_taxispeed:
            self._speed += taxi_acceleration * self.dt
        elif distance > needed_distance and self._speed >= max_taxispeed:
            self._speed = max_taxispeed
        elif distance <= needed_distance:
            self._speed -= taxi_acceleration * self.dt
        return self._speed

    @property
    def speed(self): # dynamically determines the speed of the aircraft based on its current state
        match self.state:
            case 'pushback':
                return -5
            case 'taxi'| 'crossing_runway'| 'cleared_crossing'| 'line_up'| 'cleared_takeoff' | 'arrival' | 'cleared_land' | 'rollout' | 'rollout_continue':
                return self._speed
            case 'takeoff':
                return self._speed
            case 'vacate'| 'vacate_continue':
                return self._speed
            case 'go_around':
                return self._speed
            case _:
                return 0

    @property  # calculates the aircraft's movement angle relative to its heading
    def angle(self):
        if self.state == 'pushback':
            return (90 - self.heading - 180) % 360
        return 90 - self.heading
    
    @property
    def speed_meters_per_second(self):
        return self.speed * 0.514444  # Convert knots to meters per second
    
    @property
    def movement_direction(self): # determines whether the aircraft is moving forward or backward
        return 1 if self.speed >= 0 else -1
    
    @property
    def distance_to_next(self): #  calculates the distance to the next waypoint in the aircraft's route
        if len(self.route) == 0:
            return 0
        distance_to_next = calculate_distance(self.network['all_nodes'], self.position, self.route[0])
        return distance_to_next
    
    @property
    def dt(self): # calculates the time since the last tick (update)
        return time.time() - self.last_tick
    
    @property
    def last_tick(self): # returns the last tick time
        return self._last_tick

    @last_tick.setter 
    def last_tick(self, value):
        # Update the speed when last_tick is updated
        match self.state:
            case 'taxi' | 'crossing_runway' | 'cleared_crossing' | 'line_up' | 'cleared_takeoff':
                self.taxi_speed()
            case 'takeoff':
                self.take_off_speed()
            case 'arrival' | 'cleared_land':
                self.approach_speed()
            case 'rollout' | 'rollout_continue':
                self.landing_speed()
            case 'vacate' | 'vacate_continue':
                self.vacate_speed()
            case 'go_around':
                self.go_around_speed()
        
        # Update the internal last_tick value
        self._last_tick = value
    
    @property
    def heading(self): # epresents the aircraft's heading in degrees
        return self._heading
    
    @heading.setter # The setter adjusts the heading based on the state
    def heading(self, value):
        if self.state == 'pushback':
            value = (value + 180) % 360
        else:
            value = value % 360
        self._heading = value

    def _add_via(self): # Adds the selected via to the list of selected vias
        via = self.via_dropdown.getSelected()
        if via and via not in self.selected_vias:
            self.selected_vias.append(via)
    def _reset_vias(self):
        self.selected_vias.clear()
    
    def __init__(self, position, heading, state, callsign, network, performance):
        self._speed = 0  # Internal speed variable
        self._last_tick = time.time()
        self.position = position
        self.state = state
        self.heading = heading
        self.callsign = callsign
        self.route = []
        self.distance_to_destination = 0
        self.rect = None
        self.network = network
        self.performance = performance
        self.selected = False # Indicates if the aircraft is selected
        
    def blit_aircraft(self, screen, png, WIDTH, HEIGHT, limits, padding, draw_route=False, draw_rect=False): # function that draws the aircraft on the screen
        coords = latlon_to_screen(self.position, limits, WIDTH, HEIGHT, padding)

        # Convert aviation heading to Pygame's counterclockwise system
        pygame_angle = -self.heading
        angle_rad = math.radians(pygame_angle)

        # Get original image size
        orig_width, orig_height = png.get_size()
        image_offset = (math.sin(angle_rad)*orig_height/2, math.cos(angle_rad)*orig_height/2)

        # Rotate image
        rotated_image = pygame.transform.rotate(png, pygame_angle)
        new_pos = tuple(coords[i] + image_offset[i] for i in range(2))

        # Get new bounding box after rotation
        new_rect = rotated_image.get_rect(center=new_pos)
        self.rect = new_rect

        if draw_route and len(self.route) > 0:
            points = [coords] + [latlon_to_screen(self.network['all_nodes'][n], limits, WIDTH, HEIGHT, padding) for n in self.route if n in self.network['all_nodes']]
            if points:
                pygame.draw.lines(screen, (255, 0, 0), False, points, 2)

        # Blit rotated image
        self.button(screen)
        screen.blit(rotated_image, new_rect.topleft)
        if draw_rect: pygame.draw.rect(screen, (255, 0, 0), new_rect, 2)  # Draw the rectangle around the aircraft

    def button(self, screen): # creates a button for the aircraft to interact with
        # Check if the button already exists
        if not hasattr(self, 'button_instance'):
            # Create and store the button
            self.button_instance = Button(
                screen,
                self.rect.centerx-10,  # Center X position
                self.rect.centery-10,  # Center Y position
                self.rect.width /4,       # Width
                self.rect.height /4,      # Height
                onClick= lambda: self.click_handler(),  # Click event handler
                inactiveColour=(255, 223, 63),  # Yellow color
                pressedColour=(255, 212, 0),   # Darker yellow when pressed
                hoverColour=(212, 212, 0),     # Darker yellow when hovered
                radius=0  # Set radius to 0 for a plain rectangle
            )
        else:
            # Update the button's position if it already exists
            self.button_instance.setX(self.rect.centerx )
            self.button_instance.setY(self.rect.centery )
            
    def click_handler(self):
    # Deselect all other aircraft and clear their buttons
        for aircraft in self.network['aircraft_list']:
            if aircraft.selected:
                aircraft.clear_buttons()  # Clear buttons for the previously selected aircraft
                aircraft.selected = False

        # If this aircraft is already in the first position, just select it
        if self == self.network['aircraft_list'][0]:
            self.selected = True
            return

        # Swap this aircraft with the one in the first position
        idx = self.network['aircraft_list'].index(self)
        self.network['aircraft_list'][idx], self.network['aircraft_list'][0] = (
            self.network['aircraft_list'][0],
            self.network['aircraft_list'][idx],
        )

        # Set this aircraft as selected
        self.network['aircraft_list'][0].selected = True

    def update_via_filter(self): # Updates the via filter and hides or disables related UI elements if they exist.
        self.filtered_vias = [v for v in self.network['taxiways'] if self.via_search_box.getText().lower() in v.lower()]
        if hasattr(self, 'via_dropdown'):
            self.via_dropdown.choices = self.filtered_vias
            print('test', self.via_search_box.getText(), self.filtered_vias, self.via_dropdown.choices)
            for attr in ['via_dropdown', 'add_via_button', 'reset_vias_button', 'give_route_button']:
                if hasattr(self, attr):
                    widget = getattr(self, attr)
                    # If it's a list (like hold_pushback_dropdowns), hide and disable all widgets in it
                    if isinstance(widget, list):
                        for w in widget:
                            try:
                                w.hide()
                                w.disable()
                            except AttributeError:
                                pass
                    else:
                        try:
                            widget.hide()
                            widget.disable()
                        except AttributeError:
                            pass
                    delattr(self, attr)


    def vias_selection_ui(self, screen, y_start=180, on_give_route=None):
        """
        Draws a search box, dropdown, add/reset buttons, selected vias list, and a 'Give new route' button.
        The 'on_give_route' callback is called when the user clicks the button.
        """
        # --- Search box ---
        if not hasattr(self, 'via_search_box'):
            self.filter_text = None
            self.selected_vias = []
            self.last_via_selected = None
            self.via_search_box = TextBox(
                screen, 50, y_start-40, 200, 30, fontSize=18, borderColour=(200,200,200), textColour=(0,0,0), onTextChanged=self.update_via_filter
            )
            self.via_search_box.setText('OUT')
        
        self.filtered_vias = [v for v in self.network['taxiways'] if self.via_search_box.getText().lower() in v.lower()]

        # --- Dropdown and buttons ---
        if not hasattr(self, 'via_dropdown'):
            self.via_dropdown = Dropdown(
                screen,
                50,
                y_start,
                200,
                30,
                name='Via',
                choices=self.filtered_vias,
                colour=(200, 200, 200),
                direction='down',
                textHalign='left',
                font=pygame.font.SysFont('Arial', 20),
                backgroundColour=(255, 255, 255),
                textColour=(0, 0, 0),
                maxChoices=8
            )
            self.add_via_button = Button(
                screen,
                260,
                y_start,
                80,
                30,
                text='Add',
                onClick=lambda: self._add_via(),
                inactiveColour=(180, 180, 255),
                pressedColour=(150, 150, 200),
                hoverColour=(120, 120, 180),
                radius=0
            )
            self.reset_vias_button = Button(
                screen,
                350,
                y_start,
                80,
                30,
                text='Reset',
                onClick=lambda: self._reset_vias(),
                inactiveColour=(255, 180, 180),
                pressedColour=(200, 120, 120),
                hoverColour=(180, 120, 120),
                radius=0
            )
            self.give_route_button = Button(
                screen,
                50,
                y_start + 80,
                200,
                30,
                text='Taxi',
                onClick=lambda: on_give_route(vias=self.selected_vias) if on_give_route else (lambda: None),
                inactiveColour=(255, 223, 63),
                pressedColour=(255, 212, 0),
                hoverColour=(212, 212, 0),
                radius=0
            )
        else:
            # Always update dropdown choices to match filter
            self.via_dropdown.choices = self.filtered_vias

        # Poll for via selection change (but don't add to list automatically)
        current_via = self.via_dropdown.getSelected()
        self.last_via_selected = current_via

        # Draw the selected vias below the dropdown
        try:
            vias_text = ', '.join(self.selected_vias) if self.selected_vias else 'None'
        except:
            vias_text = ''
        screen.blit(create_surface_with_text(f"Selected vias: {vias_text}", 18, (255, 255, 255), 'Arial'), (50, y_start + 40))


    def information(self,screen): # function that displays the aircraft information on the screen
        if self.selected: # standard information
            screen.blit(create_surface_with_text(f"callsign: {self.callsign}", 26, (255, 255, 255), 'Arial'), (50, 50))
            screen.blit(create_surface_with_text(f"state: {self.state}", 20, (255, 255, 255), 'Arial'), (50, 80))  
            screen.blit(create_surface_with_text(f"speed: {round(self.speed)} kts", 20, (255, 255, 255), 'Arial'), (50, 110))
            screen.blit(create_surface_with_text(f"gate: {self.gate}", 20, (255, 255, 255), 'Arial'), (220, 80))
            screen.blit(create_surface_with_text(f"altitude: {round(self.altitude)} ft", 20, (255, 255, 255), 'Arial'), (220, 110))
        
            match self.state: # for each state, display the relevant information and creates the relevant buttons
            
                case 'gate': 
                    screen.blit(create_surface_with_text("pushback direction: north, east, south, west", 20, (255, 255, 255), 'Arial'), (50, 140))
                    if not hasattr(self, 'pushback_buttons'):
                        self.pushback_buttons = [
                        Button(screen, 50, 170, 100, 30, text='north', onClick=lambda: self.pushback('north'), inactiveColour=(255, 223, 63), pressedColour=(255, 212, 0), hoverColour=(212, 212, 0), radius=0),
                        Button(screen, 50, 210, 100, 30, text='east', onClick=lambda: self.pushback('east') , inactiveColour=(255, 223, 63), pressedColour=(255, 212, 0), hoverColour=(212, 212, 0), radius=0),
                        Button(screen, 50, 250, 100, 30, text='south', onClick=lambda: self.pushback('south'), inactiveColour=(255, 223, 63), pressedColour=(255, 212, 0), hoverColour=(212, 212, 0), radius=0),
                        Button(screen, 50, 290, 100, 30, text='west', onClick=lambda: self.pushback('west'), inactiveColour=(255, 223, 63), pressedColour=(255, 212, 0), hoverColour=(212, 212, 0), radius=0)
                        ]        
                    
                            
                case 'hold_pushback':
                    screen.blit(create_surface_with_text("Select runway, exit and vias:", 20, (255, 255, 255), 'Arial'), (50, 170))
                    runway_options = list(self.network['runways'].keys())
                    if not hasattr(self, 'selected_runway'):
                        self.selected_runway = None
                    if not hasattr(self, 'last_runway_selected'):
                        self.last_runway_selected = None
                    if not hasattr(self, 'runway_dropdown'):
                        self.runway_dropdown = Dropdown(
                            screen,
                            50,
                            210,
                            200,
                            30,
                            name='Runway',
                            choices=runway_options,
                            colour=(180, 180, 255),
                            direction='down',
                            textHalign='left',
                            font=pygame.font.SysFont('Arial', 20),
                            backgroundColour=(255, 255, 255),
                            textColour=(0, 0, 0)
                        )
                    # Poll for runway selection change
                    current_runway = self.runway_dropdown.getSelected()
                    if current_runway != self.last_runway_selected:
                        self.selected_runway = current_runway
                        self.last_runway_selected = current_runway
                        # Remove old dropdowns/buttons if present
                        if hasattr(self, 'hold_pushback_dropdowns'):
                            del self.hold_pushback_dropdowns
                        if hasattr(self, 'exit_dropdown'):
                            del self.exit_dropdown
                        if hasattr(self, 'via_dropdown'):
                            del self.via_dropdown
                        if hasattr(self, 'add_via_button'):
                            del self.add_via_button
                        if hasattr(self, 'reset_vias_button'):
                            del self.reset_vias_button
                        if hasattr(self, 'start_taxi_button'):
                            del self.start_taxi_button
                        if hasattr(self, 'selected_exit'):
                            del self.selected_exit
                        if hasattr(self, 'last_exit_selected'):
                            del self.last_exit_selected
                        if hasattr(self, 'selected_vias'):
                            del self.selected_vias
                        if hasattr(self, 'last_via_selected'):
                            del self.last_via_selected

                    # Only show exit/via dropdowns and button if a runway is selected
                    if self.selected_runway:
                        if not hasattr(self, 'exit_dropdown'):
                            exit_options = [key for key, value in self.network['runways'][self.selected_runway]['exits'].items() if value['TORA'] >= self.performance['dist_TO']]
                            self.selected_exit = None
                            self.last_exit_selected = None
                            self.exit_dropdown = Dropdown(
                                screen,
                                50,
                                250,
                                200,
                                30,
                                name='Runway Exit',
                                choices=exit_options,
                                colour=(255, 223, 63),
                                direction='down',
                                textHalign='left',
                                font=pygame.font.SysFont('Arial', 20),
                                backgroundColour=(255, 255, 255),
                                textColour=(0, 0, 0)
                            )
                        # Poll for exit selection change
                        current_exit = self.exit_dropdown.getSelected()
                        if current_exit != self.last_exit_selected:
                            self.selected_exit = current_exit
                            self.last_exit_selected = current_exit

                        # Use the vias_selection_ui for vias selection and route
                        self.vias_selection_ui(
                            screen,
                            y_start=330,
                            on_give_route=lambda vias: self.taxi(self.selected_runway, self.selected_exit, vias=vias)
                        )
                case 'taxi':
                    #screen.blit(create_surface_with_text(f"taxi route: {self.route}", 20, (255, 255, 255), 'Arial'), (50, 140))
                    if not hasattr(self, 'taxi_buttons'):
                        self.taxi_buttons = [
                        Button(screen, 50, 170, 120, 30, text='Cross runway', onClick=lambda: self.cross_runway(), inactiveColour=(255, 223, 63), pressedColour=(255, 212, 0), hoverColour=(212, 212, 0), radius=0),
                        Button(screen, 50, 210, 120, 30, text='Hold Position', onClick=lambda: self.hold_position(), inactiveColour=(255, 223, 63), pressedColour=(255, 212, 0), hoverColour=(212, 212, 0), radius=0), 
                        Button(screen, 50, 250, 120, 30, text='line up', onClick=lambda: self.line_up(), inactiveColour=(255, 223, 63), pressedColour=(255, 212, 0), hoverColour=(212, 212, 0), radius=0),      
                        Button(screen, 50, 290, 120, 30, text='take off', onClick=lambda: self.takeoff(), inactiveColour=(255, 223, 63), pressedColour=(255, 212, 0), hoverColour=(212, 212, 0), radius=0)
                        ]
                    taxi_function = self.set_new_taxi if self.type == "departure" else self.taxi
                    self.vias_selection_ui(screen, y_start=380, on_give_route=taxi_function)
                case 'hold_taxi':
                    screen.blit(create_surface_with_text("hold_taxe", 20, (255, 255, 255), 'Arial'), (50, 140))
                    if not hasattr(self, 'continue_taxi_buttons'):
                        self.continue_taxi_buttons = [Button(screen, 50, 170, 120, 30, text='Continue taxi', onClick=lambda: self.continue_taxi(), inactiveColour=(255, 223, 63), pressedColour=(255, 212, 0), hoverColour=(212, 212, 0), radius=0)
                        ]
                    
                    self.vias_selection_ui(screen, y_start=250, on_give_route=self.set_new_taxi)
                case 'hold_runway':
                    screen.blit(create_surface_with_text("hold runway", 20, (255, 255, 255), 'Arial'), (50, 140)) 
                    if not hasattr(self, 'hold_runway_buttons'):
                        self.hold_runway_buttons = [ 
                        Button(screen, 50, 170, 120, 30, text='Cross runway', onClick=lambda: self.cross_runway(), inactiveColour=(255, 223, 63), pressedColour=(255, 212, 0), hoverColour=(212, 212, 0), radius=0)
                        ]
                case 'cleared_crossing':
                    screen.blit(create_surface_with_text("cleared crossing", 20, (255, 255, 255), 'Arial'), (50, 140))
                    if not hasattr(self, 'cleared_crossing_buttons'):
                        self.cleared_crossing_buttons = [    
                        Button(screen, 50, 170, 120, 30, text='hold position', onClick=lambda: self.hold_position(), inactiveColour=(255, 223, 63), pressedColour=(255, 212, 0), hoverColour=(212, 212, 0), radius=0)
                        ]
                case 'ready_line_up':
                    screen.blit(create_surface_with_text("ready line up", 20, (255, 255, 255), 'Arial'), (50, 140))
                    if not hasattr(self, 'ready_line_up_buttons'):
                        self.ready_line_up_buttons = [
                        Button(screen, 50, 170, 120, 30, text='line up', onClick=lambda: self.line_up(), inactiveColour=(255, 223, 63), pressedColour=(255, 212, 0), hoverColour=(212, 212, 0), radius=0)
                        ]
                case 'line_up':
                    screen.blit(create_surface_with_text("line up", 20, (255, 255, 255), 'Arial'), (50, 140))
                    if not hasattr(self, 'line_up_buttons'):
                        self.line_up_buttons = [
                        Button(screen, 50, 170, 100, 30, text='take off', onClick=lambda: self.takeoff(), inactiveColour=(255, 223, 63), pressedColour=(255, 212, 0), hoverColour=(212, 212, 0), radius=0)
                        ]
                    self.vias_selection_ui(screen, y_start=250, on_give_route=self.set_new_taxi)
                case 'ready_takeoff':
                    screen.blit(create_surface_with_text("ready takeoff", 20, (255, 255, 255), 'Arial'), (50, 140))
                    if not hasattr(self, 'ready_takeoff_buttons'):
                        self.ready_takeoff_buttons = [
                        Button(screen, 50, 170, 100, 30, text='take off', onClick=lambda: self.takeoff(), inactiveColour=(255, 223, 63), pressedColour=(255, 212, 0), hoverColour=(212, 212, 0), radius=0)
                        ]
                    self.vias_selection_ui(screen, y_start=380, on_give_route=self.set_new_taxi)
                case 'arrival':
                    screen.blit(create_surface_with_text("land or abord landing:", 20, (255, 255, 255), 'Arial'), (50, 140))
                    screen.blit(create_surface_with_text(f"runway: {self.runway_name}", 20, (255, 255, 255), 'Arial'), (50, 170))
                    if not hasattr(self, 'arrival_buttons'):
                        self.arrival_buttons = [ 
                        Button(screen, 50, 200, 200, 30, text='go_around', onClick=lambda: self.go_around(), inactiveColour=(255, 223, 63), pressedColour=(255, 212, 0), hoverColour=(212, 212, 0), radius=0)]
                        for i, exit_option in enumerate(self.exitsAvailable.keys()):
                            self.arrival_buttons.append(
                                Button(
                                    screen, 
                                    50, 
                                    240 + i * 40,  # Adjust Y position for each button
                                    200, 
                                    30, 
                                    text=f'Land at {exit_option}', 
                                    onClick=lambda exit_option=exit_option: self.land(exit_option), 
                                    inactiveColour=(255, 223, 63), 
                                    pressedColour=(255, 212, 0), 
                                    hoverColour=(212, 212, 0), 
                                    radius=0
                                )
                            )                      
                case 'rollout':
                    screen.blit(create_surface_with_text("preemtively give taxi to the gate", 20, (255, 255, 255), 'Arial'), (50, 170))
                    self.vias_selection_ui(screen, y_start=250, on_give_route=self.taxi)

                case 'vacate':
                    screen.blit(create_surface_with_text("vacate:", 20, (255, 255, 255), 'Arial'), (50, 170))
                    self.vias_selection_ui(screen, y_start=250, on_give_route=self.taxi)
                case 'vacate_continue':
                    screen.blit(create_surface_with_text("continue taxiing:", 20, (255, 255, 255), 'Arial'), (50, 170))
                    self.vias_selection_ui(screen, y_start=250, on_give_route=self.taxi)
                case 'ready_taxi_gate':
                    screen.blit(create_surface_with_text(" taxi to the gate", 20, (255, 255, 255), 'Arial'), (50, 170))
                    self.vias_selection_ui(screen, y_start=250, on_give_route=self.taxi)
    
    def clear_buttons_aircraft(self): # Clears the buttons for the aircraft, for example when the aircraft is at departure or does a go around
        if hasattr(self, 'button_instance'):
            del self.button_instance
    
    def clear_buttons(self):
        # Remove buttons for the current state
        if hasattr(self, 'pushback_buttons'):
            del self.pushback_buttons
        # Remove all hold_pushback UI elements
        for attr in ['hold_pushback_dropdowns', 'exit_dropdown', 'via_dropdown','add_via_button', 'reset_vias_button', 'start_taxi_button', 'runway_dropdown', 'give_route_button', 'via_search_box']:
            if hasattr(self, attr):
                widget = getattr(self, attr)
                # If it's a list (like hold_pushback_dropdowns), hide and disable all widgets in it
                if isinstance(widget, list):
                    for w in widget:
                        try:
                            w.hide()
                            w.disable()
                        except AttributeError:
                            pass
                else:
                    try:
                        widget.hide()
                        widget.disable()
                    except AttributeError:
                        pass
                delattr(self, attr)
        if hasattr(self, 'runway_dropdown'):
            del self.runway_dropdown
        if hasattr(self, 'hold_pushback_dropdowns'):
            del self.hold_pushback_dropdowns
        if hasattr(self, 'exit_dropdown'):
            del self.exit_dropdown
        if hasattr(self, 'via_dropdown'):
            del self.via_dropdown
        if hasattr(self, 'add_via_button'):
            del self.add_via_button
        if hasattr(self, 'reset_vias_button'):
            del self.reset_vias_button
        if hasattr(self, 'start_taxi_button'):
            del self.start_taxi_button
        if hasattr(self, 'selected_exit'):
            del self.selected_exit
        if hasattr(self, 'last_exit_selected'):
            del self.last_exit_selected
        if hasattr(self, 'selected_vias'):
            del self.selected_vias
        if hasattr(self, 'last_via_selected'):
            del self.last_via_selected

        if hasattr(self, 'taxi_buttons'):
            del self.taxi_buttons
        if hasattr(self, 'continue_taxi_buttons'):
            del self.continue_taxi_buttons
        if hasattr(self, 'hold_runway_buttons'):
            del self.hold_runway_buttons
        if hasattr(self, 'cleared_crossing_buttons'):
            del self.cleared_crossing_buttons
        if hasattr(self, 'ready_line_up_buttons'):
            del self.ready_line_up_buttons
        if hasattr(self, 'line_up_buttons'):
            del self.line_up_buttons
        if hasattr(self, 'ready_takeoff_buttons'):
            del self.ready_takeoff_buttons
        if hasattr(self, 'arrival_buttons'):
            del self.arrival_buttons
        if hasattr(self, 'rollout_buttons'):
            del self.rollout_buttons
        if hasattr(self, 'vacate_buttons'):
            del self.vacate_buttons
        if hasattr(self, 'vacate_continue_buttons'):
            del self.vacate_continue_buttons
        if hasattr(self, 'ready_taxi_gate_buttons'):
            del self.ready_taxi_gate_buttons
    
    # function that calculates the route from the starting point to the destination        
    def calculate_route (self, taxi_nodes,all_nodes, begintoestand, destination, starting_via=None, angle=None):
        q = queue.PriorityQueue()
        q.put(begintoestand)
        visited_nodes = []
        i=0
        while not q.empty():
            i+=1
            state = q.get()
            
            node = state[-1]['node']
            if node in visited_nodes:
                continue
            parent = state[-1]['parent']
            directions = taxi_nodes[node]['next_moves']

            visited_nodes.append(node)
            
            for new_node in directions:
                if state[-1]['parent'] is not None:
                    prev_node = state[-1]['parent']['node']
                    angle = angle_difference(all_nodes, prev_node, node, new_node)
                    if angle < 90:  # Skip if the angle is too acute
                        continue
                else:
                    if starting_via is not None and starting_via not in taxi_nodes[new_node]['parents']:
                        continue
                    if angle is not None:
                        angle = angle_difference(all_nodes, node, new_node, angle=angle)
                        if angle < 90:  # Skip if the angle is too acute
                            continue
                added_distance = calculate_distance(all_nodes, new_node, node)
                real_distance = state[-1]['distance'] + added_distance

                #solution found: get path from parent nodes
                if new_node == destination or destination in taxi_nodes[new_node]['parents']:
                    # Check if the destination is a via and if there is a next node on the same via, otherwise it is not possible to continue from this point onwards and the route is not valid
                    if destination in taxi_nodes[new_node]['parents']:
                        next_nodes = [
                            n for n in taxi_nodes[new_node]['next_moves']
                            if destination in taxi_nodes[n]['parents']
                        ]
                        if not next_nodes:
                            continue
                        else:
                            possible_node = False
                            for next_node in next_nodes:
                                if angle_difference(all_nodes, node, new_node, next_node) >= 90:
                                    possible_node = True
                                    break
                            if not possible_node:
                                continue

                    print("Oplossing gevonden! ")
                    path = [new_node]
                    while True:
                        path.append(node)
                        if parent == None:
                            break
                        state = parent
                        node = state['node']
                        parent = state['parent']
                    print(len(path), i, path)
                    return path[::-1], real_distance
                #no solution found: add node to queue
                else: 
                    if starting_via != None and starting_via in taxi_nodes[new_node]['parents']:
                        added_distance *= 0.01

                    distance = state[0] + added_distance

                    q.put((distance, new_node, {'node': new_node, 'parent': state[-1], 'distance': real_distance}))
        print(f"Geen oplossing gevonden: laatse via: {starting_via}")	
        return None # geen oplossing gevonden
    
    # function that calculates the route from the starting point to the destination via a list of vias
    def calculate_via_route(self, destination, vias=[], starting_node=None, set_route=True):
        taxi_nodes = self.network['taxi_nodes']
        all_nodes = self.network['all_nodes']
        start_node = self.route[0] if starting_node is None else starting_node

        start_time = time.time()
        route = [start_node]
        vias.append(destination)
        starting_state = (0, start_node, {'node': start_node, 'parent': None, 'distance': 0})
        angle = None
        total_distance = 0

        for i, via in enumerate(vias):
            #TODO sometimes it may be better to continue searching for more points on the via to see if another point would give a shorter overal route
            #TODO slightly increase distance(priority) when making turns to prioritize straight routes
            calculated_route = self.calculate_route(taxi_nodes, all_nodes, starting_state, via, starting_via=vias[i-1] if i > 0 else None, angle=angle if angle != None else None)
            if calculated_route == None:
                return None, None
            path, distance = calculated_route
            route.extend(path)
            total_distance += distance
            starting_state = (0, route[-1], {'node': route[-1], 'parent': None, 'distance': 0})
            angle = calculate_angle(all_nodes, route[-1], route[-2])
        
        end_time = time.time()
        print(f"Time taken to run calculate_via_route: {end_time - start_time} seconds")

        if set_route:
            self.route = route
            self.distance_to_destination = total_distance
        return route, total_distance

    def hold_position(self):
        if self.state not in ['taxi', 'cleared_crossing']:
            return
        self.state = 'hold_taxi'
        self.clear_buttons()

    def continue_taxi(self):
        if self.state != 'hold_taxi':
            return

        self.state = 'taxi'
        self.clear_buttons()

    def cross_runway(self):
        match self.state:
            case 'taxi':
                self.state = 'cleared_crossing'
            case 'hold_runway':
                self.state = 'crossing_runway'          
        self.clear_buttons()     

    def check_collision(self, aircraft_list=None):
        if aircraft_list is None:
            return False
        for other_aircraft in aircraft_list:
            if other_aircraft == self or other_aircraft.state == 'pushback' or other_aircraft.state == 'gate':
                continue
            angle = angle_difference(self.network['all_nodes'], self.position, other_aircraft.position, angle=self.angle)
            if abs(angle) > 45:
                continue
            if self.rect.colliderect(other_aircraft.rect):
                return True
        return False

    # Moves the aircraft along its route, updates its state, and handles collisions or transitions.
    def tick(self, aircraft_list=None):
        dt = self.dt
        if dt < 1:
            return False
        self.last_tick = time.time()
        if self.speed == 0 or self.state == 'takeoff' or self.state == 'go_around':
            return dt
        previous_state = {'state': self.state, 'position': self.position, 'heading': self.heading, 'speed': self.speed, 'altitude': self.altitude, 'distance_to_destination': self.distance_to_destination, 'route': self.route}
        distance_to_next = self.distance_to_next
        distance_to_move = abs(self.speed_meters_per_second * dt)
        if distance_to_next < 1 and len(self.route) == 1:
            self.next_state()
            self.position = self.network['all_nodes'][self.route[0]]
            return dt
        while distance_to_next < distance_to_move:
            distance_to_move -= distance_to_next
            self.distance_to_destination -= distance_to_next
            if len(self.route) == 1:
                distance_to_move = 0
                self.position = self.network['all_nodes'][self.route[0]]
                self.next_state()
                return dt
            node = self.route.pop(0)
            self.position = self.network['all_nodes'][node]
            distance_to_next = self.distance_to_next

            if self.speed <= 0:
                continue
            if self.type == 'arrival':
                if node == self.runway['threshold']:
                    self.next_state()
                if node == self.runway_exit['node']:
                    self.next_state()
            if node in self.network['taxi_nodes']:
                node_information = self.network['taxi_nodes'][node]
                if 'holding_position' in node_information: # and node_information['holding_position']:
                    if self.type == 'departure' and node == self.runway_exit['holding_point']: 
                        if self.state == 'taxi':
                            self.state = 'ready_line_up'
                        else: continue
                    elif self.state == 'cleared_crossing':
                        self.state = 'crossing_runway'
                        continue
                    elif self.state == 'crossing_runway':
                        self.state = 'taxi'
                        continue
                    elif self.state == 'vacate':
                        if node_information['holding_direction'] == 'both':
                            self._about_to_cross = True 
                        self.state = 'ready_taxi_gate'
                    elif self.state == 'vacate_continue':
                        if node_information['holding_direction'] == 'both':
                            self.state = 'crossing_runway'
                        else:
                            self.state = 'taxi'
                    else:
                        self.state = 'hold_runway'
                    distance_to_move = 0
                    print(f'{self.callsign} holding short of runway, state: {self.state}')
                    break

        self.heading = calculate_angle(self.network['all_nodes'], self.position, self.route[0])
        new_position = distance(meters=distance_to_move*self.movement_direction).destination(self.position, self.heading)
        self.distance_to_destination -= distance_to_move
        self.position = (new_position.latitude, new_position.longitude)
        self.altitude += self.vspeed * dt / 60
        if self.altitude < 0:
            self.altitude = 0

        if self.state != 'pushback' and self.check_collision(aircraft_list):
            self.position = previous_state['position']
            self.heading = previous_state['heading']
            self._speed = 0
            self.altitude = previous_state['altitude']
            self.distance_to_destination = previous_state['distance_to_destination']
            self.route = previous_state['route']
            print(f'{self.callsign}, {self.state}, collision detected, reverting to previous state')
        else:
            print(self.callsign, self.state, self.speed, self.altitude, self.vspeed, self.distance_to_next)
# class Arrival in function of the aircraft that is arriving at the airport
class Arrival(Aircraft):
    def landing_speed(self): # calculate landing speeds
        dist_LDA = self.runway_exit['LDA']
        speed_Vat = self.performance['speed_Vat']
        target_vacate_speed = self.target_vacate_speed
        dist_exit = self.distance_to_next
        self._speed = (target_vacate_speed - speed_Vat) * ((-dist_exit / dist_LDA + 1) ** 2.5) + speed_Vat

        return self._speed
    
    def approach_speed(self): # calculate approach speeds
        speed_Vat = self.performance['speed_Vat']
        descent_angle = math.radians(3)  # Standard 3-degree glide slope
        knots_to_fps = 1.68781  # Conversion factor from knots to feet per second

        if self.altitude > 2000:
            self._speed = 180
        elif self.altitude > 500:
            self._speed = (180 - speed_Vat) / 1500 * (self.altitude - 2000) + 180
        else:
            self._speed = speed_Vat

        # Calculate vertical speed
        horizontal_speed_fps = self._speed * knots_to_fps  # Convert knots to feet per second
        self._vspeed = -descent_angle * horizontal_speed_fps * 60  # Convert to feet per minute

        return self._speed
    
    def go_around_speed(self): # calculate go around speeds
        speed_climb = self.performance['speed_climb']
        acceleration = speed_climb / 10  # Arbitrary acceleration factor for go-around
        self._speed = min(self._speed + acceleration * self.dt, speed_climb)
        return self._speed

    def vacate_speed(self): # calculate vacate speeds
        if self.state != 'vacate':
            return self._speed

        dist_rwy_to_hp = self.dist_rwy_to_hp
        target_vacate_speed = self.target_vacate_speed
        max_taxi_speed = self.speed_max_taxi

        # Find the distance to the next holding point
        dist_hp = calculate_distance(self.network['all_nodes'], self.position, self.route[0])
        for i, node in enumerate(self.route):
            if 'holding_position' in self.network['taxi_nodes'][node]:
                break
            if i < len(self.route) - 1:
                dist_hp += calculate_distance(self.network['all_nodes'], node, self.route[i + 1])
        # Gradually increase speed from target_vacate_speed to max_taxi_speed
        self._speed = (max_taxi_speed - target_vacate_speed) * ((-dist_hp / dist_rwy_to_hp + 1) ** 2.5) + target_vacate_speed
        print(f'{self.callsign} calculating vacate speed, dist to hp: {dist_hp}, speed: {self._speed}')

        return self._speed
        # speeds goes from target_vacate_speed to max_taxi from the runway to the hp

    
    @property # property that returns the vertical speed of the aircraft
    def vspeed(self):
        if self.altitude <= 0:
            return 0  
        match self.state:
            case 'arrival' | 'cleared_land':
                return self._vspeed
            case 'rollout' | 'rollout_continue':
                return -300
            case 'go_around':
                return self.performance['rate_of_climb']
            case _:
                return 0

    def __init__(self, callsign, performance, runway, network, gate, height=3000):
        distance_to_threshold = (height - 50) / math.tan(math.radians(3))
        heading = network['runways'][runway]['angle']
        threshold = network['runways'][runway]['threshold']
        init_pos = distance(feet=-distance_to_threshold).destination(network['all_nodes'][threshold], heading)
        super().__init__(position=(init_pos.latitude, init_pos.longitude), heading=heading, state='arrival' , callsign=callsign, network=network, performance=performance)
        self.type = 'arrival'
        self.route = [threshold]
        self.runway_name = runway
        self.gate = gate
        self.runway  = network['runways'][runway]
        self.exitsAvailable = {key: item for key, item in self.runway['exits'].items() if item['LDA'] > self.performance['dist_LD']}
        self.altitude = height
        self.speed_max_taxi = 20
        self._about_to_cross = False

    def next_state(self): # function that sets the next state of the aircraft
        print('arrival, next_state')
        match self.state:
            case 'arrival':
                self.state = 'go_around'
                print(f'{self.callsign} going around from runway {self.runway_name}')
            case 'cleared_land':
                self.state = 'rollout'
            case 'rollout':
                self.state = 'vacate'
            case 'rollout_continue':
                self.state = 'vacate_continue'
            case 'vacate':
                self.state = 'ready_taxi_gate'
            case 'vacate_continue':
                node_information = self.network['taxi_nodes'][self.route[0]]
                if 'holding_position' in node_information and node_information['direction'] == 'both':
                    self.state = 'crossing_runway'
                else:
                    self.state = 'taxi'
            case 'taxi':
                self.state = 'park'
            case 'hold_taxi':
                self.state = 'taxi'

    def go_around(self): 
        if self.state != 'arrival':
            return
        self.next_state()
        self.clear_buttons()

    def land(self, exit): 
        if self.state != 'arrival':
            return
        self.state = 'cleared_land'

        self.runway_exit = self.runway['exits'][exit]
        start_node = self.runway_exit['node']
        distance_to_exit = calculate_distance(self.network['all_nodes'], self.position, start_node)
        gate_nodes = self.network['gates'][self.gate]['nodes'][::-1]
        route, distance = self.calculate_via_route(gate_nodes[0], starting_node=start_node, set_route=False)
        if route is None:
            print(ValueError(f"Route to {self.gate} not found"))
            return
        dist_rwy_to_hp = 0
        for i, node in enumerate(route):
            if 'holding_position' in self.network['taxi_nodes'][node]:
                break
            if i < len(route) - 1:
                dist_rwy_to_hp += calculate_distance(self.network['all_nodes'], node, route[i + 1])

        self.route += route[1:] + gate_nodes[1:]
        self.dist_rwy_to_hp = dist_rwy_to_hp
        self.distance_to_destination = distance_to_exit + dist_rwy_to_hp + distance
        self.target_vacate_speed = ((180 - abs(self.runway_exit['angle']))/90)**1.5 * self.speed_max_taxi
        print(f'{self.callsign} cleared to land on runway {self.runway_name}, vacate at {exit}, target vacate speed: {self.target_vacate_speed}, dist_rwy_to_hp: {self.dist_rwy_to_hp}')
        self.clear_buttons()

    def taxi(self, vias=None): # function that sets the taxi route for the aircraft
        match self.state:
            case 'ready_taxi_gate' | 'hold_taxi':
                if self._about_to_cross:
                    self.state = 'crossing_runway'
                    self._about_to_cross = False
                else:
                    self.state = 'taxi'
            case 'vacate':
                self.state = 'vacate_continue'
            case 'rollout':
                self.state = 'rollout_continue'
            case 'arrival' | 'cleared_land':
                return
            case _:
                pass
        print(f'{self.callsign} taxiing to gate {self.gate}')
        if vias is None:
            return

        start_node = self.route[0]
        gate_nodes = self.network['gates'][self.gate]['nodes'][::-1]
        route, distance = self.calculate_via_route(gate_nodes[0], starting_node=start_node, set_route=False)
        if route is None:
            print(ValueError(f"Route to {self.gate} not found"))
            return
        self.route = route + gate_nodes[1:]
        self.distance_to_destination = distance + calculate_distance(self.network['all_nodes'], self.position, start_node)
        self.clear_buttons()

    def tick(self, aircraft_list=None): # function that moves the aircraft
        dt = super().tick(aircraft_list=aircraft_list)
        if not dt:
            return
        
        if self.state != 'go_around':
            return
        
        self.heading = self.runway['angle']
        distance_to_move = self.speed_meters_per_second * dt
        new_position = distance(meters=distance_to_move*self.movement_direction).destination(self.position, self.heading)
        self.position = (new_position.latitude, new_position.longitude)
        self.altitude += self.vspeed * dt / 60

# class Departure in function of the aircraft that is departing from the airport
class Departure(Aircraft):
    def take_off_speed(self): # calculate take off speeds
        dist_TO = self.performance["dist_TO"]
        speed_V2 = self.performance["speed_V2"]

        acceleration = speed_V2**2 / (2 * dist_TO)
        self._speed = self._speed + acceleration * self.dt

        return self._speed
    
    @property # property that returns the vertical speed of the aircraft
    def vspeed(self):
        if self.takeoff_distance_remaining <= 0:
            return self.performance['rate_of_climb']
        return 0

    def __init__(self, callsign, performance, gate, network):
        gate_nodes = network['gates'][gate]['nodes']
        super().__init__(position=network['all_nodes'][gate_nodes[0]], heading=network['gates'][gate]['heading'], state='gate', callsign=callsign, network=network, performance=performance)
        self.type = 'departure'
        self.gate = gate
        self.route = gate_nodes
        self.takeoff_distance_remaining = performance['dist_TO']
        self.altitude = 0
        self.runway_name = '25R'

    def next_state(self): # function that sets the next state of the aircraft
        match self.state:
            case 'gate':
                self.state = 'pushback'
            case 'pushback':
                self.state = 'pushback_complete'
            case 'pushback_complete':
                print(f'{self.callsign}, gate: {self.gate}, ready for taxi')
                self.state = 'hold_pushback'
            case 'hold_pushback':
                print(f'{self.callsign}, gate: {self.gate}, speed: {self.speed}, starting taxi')
                self.state = 'taxi'
            case 'taxi':
                self.state = 'hold_runway'
            case 'hold_taxi':
                self.state = 'taxi'
            case 'hold_runway':
                self.state = 'line_up'
            case 'line_up':
                self.state = 'ready_takeoff'
                self.heading = self.runway['angle']
            case 'cleared_takeoff':
                self.takeoff()

    def pushback(self, direction):        # Change state to pushback
        self.state = 'pushback'
        options = ['north', 'east', 'south', 'west']
        if direction not in options:
            raise ValueError(f"Pushback direction must be one of {options}")
        self.pushback_direction = options.index(direction) * 90
        print(f'pushing back {self.callsign} to {self.pushback_direction} from {self.gate}')
        self.clear_buttons()

    def taxi(self, runway, destination, vias=[]):
        #destination is a runway exit name, get the destination node from network['runways']
        print(f'calculation route for {self.callsign} to HP {destination}, runway {runway}')
        if runway == None or destination == None:
            return
        self.runway = self.network['runways'][runway]
        self.runway_name = runway
        self.runway_exit = self.network['runways'][runway]['exits'][destination]
        destination_node = self.runway_exit['node']
        self.runway_exit_name = destination
        route, distance = self.calculate_via_route(destination_node, vias)
        if route is None:
            print(ValueError(f"Route to {destination} not found"))
            return
        self.route = route
        self.state = 'taxi'
        self.clear_buttons()

    def set_new_taxi(self, vias=[]):
        self.taxi(runway=self.runway_name, destination=self.runway_exit_name, vias=vias)

    def line_up(self):
        if self.state != 'ready_line_up' and self.state != 'taxi':
            return
        self.state = 'line_up'
        print(f'{self.callsign} lining up on runway ')
        self.clear_buttons()

    def takeoff(self): # function that sets the take off state of the aircraft
        match self.state:
            case 'ready_takeoff' | 'cleared_takeoff':
                self.state = 'takeoff'
            case 'line_up':
                self.state = 'cleared_takeoff'
            case 'taxi':
                self.state = 'cleared_takeoff'
            case _:
                return
        self.clear_buttons()
    
    def tick(self, aircraft_list=None): 
        dt = super().tick(aircraft_list=aircraft_list)
        if not dt:
            return

        if self.state == 'pushback_complete':
            self.state = 'hold_pushback'

            closest_node = None
            min_angle_diff = float('inf')
            self.network['gates'][self.gate]['occupied'] = False
            for next_node in self.network['taxi_nodes'][self.route[0]]['next_moves']:
                angle_diff = abs(angle_difference(self.network['all_nodes'], self.route[0], next_node, angle=self.pushback_direction))
                if angle_diff < min_angle_diff:
                    min_angle_diff = angle_diff
                    closest_node = next_node
            if closest_node:
                self.heading = calculate_angle(self.network['all_nodes'], self.position, self.network['all_nodes'][closest_node])

        elif self.state == 'takeoff':
            self.heading = self.runway['angle']
            distance_to_move = self.speed_meters_per_second * dt
            self.takeoff_distance_remaining -= distance_to_move
            new_position = distance(meters=distance_to_move*self.movement_direction).destination(self.position, self.heading)
            self.position = (new_position.latitude, new_position.longitude)
            self.altitude += self.vspeed * dt / 60




if __name__ == '__main__':
    pass