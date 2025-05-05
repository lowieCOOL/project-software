'''
Aircraft states:
for departures
- gate
    - aircraft.pushback(direction) direction is [north, east, south, west]
- pushback
- pushback_complete
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
- cleared_takeoff
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
from airport_mapper import lon2x, lat2y, calculate_angle, angle_difference, calculate_distance
from geopy.distance import distance
import pygame
import math
import time
import queue

def latlon_to_screen(pos, limits, width, height, padding, offset_x=0, offset_y=0):
    y, min_y, max_y = lat2y(pos[0]), lat2y(limits[0][0]), lat2y(limits[0][1])
    x, min_x, max_x = lon2x(pos[1]), lon2x(limits[1][0]), lon2x(limits[1][1])

    drawable_width = width - 2 * padding
    drawable_height = height - 2 * padding

    #scales the position to be fit to the screen with some padding on the side, the largest of the 2 is taken and the other is offset so it remains in the center
    x_scale = (max_x - min_x) / drawable_width
    y_scale = (max_y - min_y) / drawable_height
    scale = max(x_scale, y_scale)

    x_offset = (scale - x_scale)* drawable_width / scale / 2  + padding
    y_offset = (scale - y_scale)* drawable_height / scale / 2  + padding

    x = int((x + offset_x - min_x) / scale + x_offset)
    y = int(height - (((y + offset_y - min_y) / scale) + y_offset))
    return x, y

class Aircraft():
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

        if distance > needed_distance and self._speed < max_taxispeed:
            self._speed += taxi_acceleration * self.dt
        elif distance > needed_distance and self._speed >= max_taxispeed:
            self._speed = max_taxispeed
        elif distance <= needed_distance:
            self._speed -= taxi_acceleration * self.dt
        return self._speed
    
    def take_off_speed(self):
        dist_TO = self.performance["dist_TO"]
        speed_V2 = self.performance["speed_V2"]

        acceleration = speed_V2**2 / (2 * dist_TO)
        self._speed = self._speed + acceleration * self.dt

        return self._speed

    @property
    def speed(self):
        match self.state:
            case 'pushback':
                return -5 * 5
            case 'taxi'| 'crossing_runway'| 'cleared_crossing'| 'line_up'| 'cleared_takeoff':
                return self._speed
            case 'takeoff':
                return self.performance['speed_V2']
            case _:
                return 0

    @property
    def angle(self):
        if self.state == 'pushback':
            return (90 - self.heading - 180) % 360
        return 90 - self.heading
    
    @property
    def speed_meters_per_second(self):
        return self.speed * 0.514444  # Convert knots to meters per second
    
    @property
    def movement_direction(self):
        return 1 if self.speed >= 0 else -1
    
    @property
    def dt(self):
        return time.time() - self.last_tick
    
    @property
    def last_tick(self):
        return self._last_tick

    @last_tick.setter
    def last_tick(self, value):
        # Update the speed when last_tick is updated
        if self.state in ['taxi', 'crossing_runway', 'cleared_crossing', 'line_up', 'cleared_takeoff']:
            self.taxi_speed()
        elif self.state == 'takeoff':
            self.take_off_speed()
        
        # Update the internal last_tick value
        self._last_tick = value
    
    @property
    def heading(self):
        return self._heading
    
    @heading.setter
    def heading(self, value):
        if self.state == 'pushback':
            value = (value + 180) % 360
        else:
            value = value % 360
        self._heading = value
    
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

    def next_state(self):
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


    def blit_aircraft(self, screen, png, limits, padding, draw_route=False):
        WIDTH, HEIGHT = screen.get_size()
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
        screen.blit(rotated_image,new_rect.topleft)

    def click_handler(self):
        # when clicked on the aircraft, the info and action of the aircraft will be displayed in the sidepanel, depending on the state of the aircraft
        pass

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

    def calculate_via_route(self, destination, vias):
        taxi_nodes = self.network['taxi_nodes']
        all_nodes = self.network['all_nodes']
        start_node = self.route[0]

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
                continue
                return None
            path, distance = calculated_route
            route.extend(path)
            total_distance += distance
            starting_state = (0, route[-1], {'node': route[-1], 'parent': None, 'distance': 0})
            angle = calculate_angle(all_nodes, route[-1], route[-2])
        
        end_time = time.time()
        print(f"Time taken to run calculate_via_route: {end_time - start_time} seconds")

        self.route = route
        self.distance_to_destination = total_distance
        return route, total_distance

    def hold_position(self):
        if self.state != 'taxi':
            return
        self.state = 'hold_taxi'

    def continue_taxi(self):
        if self.state != 'hold_taxi':
            return

        self.state = 'taxi'

    def cross_runway(self):
        match self.state:
            case 'taxi':
                self.state = 'cleared_crossing'
            case 'hold_runway':
                self.state = 'crossing_runway'               

    def tick(self):
        dt = self.dt
        if dt < 1:
            return False
        self.last_tick = time.time()
        if self.speed == 0 or self.state == 'takeoff':
            return dt
        distance_to_next = calculate_distance(self.network['all_nodes'], self.position, self.route[0])
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
            distance_to_next = calculate_distance(self.network['all_nodes'], self.position, self.route[0])

            if self.speed <= 0:
                continue
            node_information = self.network['taxi_nodes'][node]
            if 'holding_position' in node_information: # and node_information['holding_position']:
                if node == self.runway_exit['holding_point']: 
                    if self.state == 'taxi':
                        self.state = 'ready_line_up'
                    else: continue
                elif self.state == 'cleared_crossing':
                    self.state = 'crossing_runway'
                    continue
                elif self.state == 'crossing_runway':
                    self.state = 'taxi'
                    continue
                else:
                    self.state = 'hold_runway'
                distance_to_move = 0
                print(f'{self.callsign} holding short of runway, state: {self.state}')
                break


        self.heading = calculate_angle(self.network['all_nodes'], self.position, self.route[0])
        new_position = distance(meters=distance_to_move*self.movement_direction).destination(self.position, self.heading)
        self.distance_to_destination -= distance_to_move
        self.position = (new_position.latitude, new_position.longitude)

class Arrival(Aircraft):
    def __init__(self, callsign, performance, runway, network):
        super().__init__(position=network['runways'][runway]['init_offset_from_threshold'], heading=network['runways'][runway]['angle'], state='arrival' , callsign=callsign, performance=performance)
        self.type = 'arrival'
        self.runway  = network['runways'][runway]
        self.exitsAvailable = {key: item for key, item in self.runway['exits'].items() if item['LDA'] > self.performance['LDA']}
        self.altitude = 3000

    def go_around(self):
        pass

    def land(self):
        pass

class Departure(Aircraft):
    def __init__(self, callsign, performance, gate, network, all_nodes):
        gate_nodes = network['gates'][gate]['nodes']
        super().__init__(position=all_nodes[gate_nodes[0]], heading=network['gates'][gate]['heading'], state='gate', callsign=callsign, network=network, performance=performance)
        self.type = 'departure'
        self.gate = gate
        self.route = gate_nodes
        self.all_nodes = all_nodes
        self.takeoff_distance_remaining = performance['dist_TO']
        self.altitude = 0

    def pushback(self, direction):
        # pushback
        self.state = 'pushback'
        options = ['north', 'east', 'south', 'west']
        if direction not in options:
            raise ValueError(f"Pushback direction must be one of {options}")
        self.pushback_direction = options.index(direction) * 90
        print(f'pushing back {self.callsign} to {self.pushback_direction} from {self.gate}')

    def taxi(self, runway, destination, vias=[]):
        #destination is a runway exit name, get the destination node from network['runways']
        print(f'calculation route for {self.callsign} to HP {destination}, runway {runway}')
        self.runway = self.network['runways'][runway]
        self.runway_exit = self.network['runways'][runway]['exits'][destination]
        destination_node = self.runway_exit['node']
        route, distance = self.calculate_via_route(destination_node, vias)
        if route is None:
            raise ValueError(f"Route to {destination} not found")
        self.route = route
        self.state = 'taxi'

    def line_up(self):
        if self.state != 'ready_line_up' and self.state != 'taxi':
            return
        self.state = 'line_up'
        print(f'{self.callsign} lining up on runway ')

    def takeoff(self):
        match self.state:
            case 'ready_takeoff':
                self.state = 'takeoff'
            case 'line_up':
                self.state = 'cleared_takeoff'
            case 'taxi':
                self.state = 'cleared_takeoff'
    
    def tick(self):
        dt = super().tick()
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
            if self.takeoff_distance_remaining <= 0:
                self.altitude += self.performance['rate_of_climb'] * dt / 60

if __name__ == '__main__':
    pass