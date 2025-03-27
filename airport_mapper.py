import json
import queue
import math
from geopy.distance import geodesic
from geopy import units
from shapely.geometry import LineString, Polygon
import time

def calculate_initial_compass_bearing(pointA, pointB):
    """
    Calculates the bearing between two points.

    The formulae used is the following:
        θ = atan2(sin(Δlong).cos(lat2),
                  cos(lat1).sin(lat2) − sin(lat1).cos(lat2).cos(Δlong))

    :Parameters:
      - `pointA: The tuple representing the latitude/longitude for the
        first point. Latitude and longitude must be in decimal degrees
      - `pointB: The tuple representing the latitude/longitude for the
        second point. Latitude and longitude must be in decimal degrees

    :Returns:
      The bearing in degrees

    :Returns Type:
      float
    """
    if (type(pointA) != tuple) or (type(pointB) != tuple):
        raise TypeError("Only tuples are supported as arguments")

    lat1 = math.radians(pointA[0])
    lat2 = math.radians(pointB[0])

    diffLong = math.radians(pointB[1] - pointA[1])

    x = math.sin(diffLong) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1)
            * math.cos(lat2) * math.cos(diffLong))

    initial_bearing = math.atan2(x, y)

    # Now we have the initial bearing but math.atan2 return values
    # from -180° to + 180° which is not what we want for a compass bearing
    # The solution is to normalize the initial bearing as shown below
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360

    return compass_bearing

#adjust for curvature of the earth, as the lat increases, the circumfrence decreases
R =  6378137.0
def lat2y(lat):
    return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) * R  

def lon2x(lon):
    return math.radians(lon) * R

def node2metric(node):
    return (lon2x(node[0]), lat2y(node[1]))

def read_json(file_name):
    with open(file_name, 'r') as json_file:
        return json.load(json_file)['elements']
    
def calculate_distance(all_nodes, node1,node2):
    node1 = all_nodes[node1]
    node2 = all_nodes[node2]

    distance = geodesic(node1, node2).meters
    return distance
    
def calculate_angle(all_nodes, node1, node2, positive=False):
    node1 = (all_nodes[node1])
    node2 = (all_nodes[node2])

    angle = calculate_initial_compass_bearing(node1, node2)
    if positive and angle < 0:
        angle += 360

    return angle
    
def map_airport(file_name, all_nodes):
    elements = read_json(file_name)
    network = {}
    taxi_nodes = {}
    runways = {}

    thresholds = [e for e in elements if e['type'] == 'way' and 'runway' in e['tags']]

    for element in elements:
        if element['type'] != 'way' or 'ref' not in element['tags']:
            continue
        type = element['tags']['aeroway']

        if type == 'taxiway':
            for i, node in enumerate(element['nodes']):
                parent = element['tags']['ref']
                if not node in taxi_nodes:
                    taxi_nodes[node] = {'next_moves': [], 'parents': [parent]}
                if not parent in taxi_nodes[node]['parents']:
                    taxi_nodes[node]['parents'].append(parent)

                node_osm = next((x for x in elements if x['type'] == 'node' and x['id'] == node), [None])

                if 'tags' in node_osm and 'aeroway' in node_osm['tags'] and node_osm['tags']['aeroway'] == 'holding_position':
                    taxi_nodes[node]['holding_position'] = True

                if i != len(element['nodes'])-1:
                    taxi_nodes[node]['next_moves'].append(element['nodes'][i+1])
                if i != 0:
                    taxi_nodes[node]['next_moves'].append(element['nodes'][i-1])

        if type == 'runway':
            runway_name = element['tags']['ref']
            if runway_name not in runways:
                runways[runway_name] = element

    network['runways'] = process_runways(all_nodes, runways, thresholds, taxi_nodes)
    network['aprons'],apron_polygons = process_aprons(elements, all_nodes)
    network['gates'] = process_gates(elements, all_nodes, apron_polygons)
    network['taxi_nodes'] = taxi_nodes

    with open("osm_data_processed.json", "w") as f:
        json.dump(network, f, indent=2)
    
    return network

def process_runways(all_nodes, runways, thresholds, taxi_nodes):
    processed = {}

    # find the thresholds of the runways
    for runway in runways.values():
        runway['thresholds'] = runway['nodes'][::max(len(runway['nodes'])-1,1)]

    # merge the displaced thresholds with the runway nodes
    for threshold in thresholds:
        threshold_nodes = threshold["nodes"]

        # Find a matching runway that shares a start or end node
        for runway in runways.values():
            runway_nodes = runway["nodes"]
            common_nodes = set(threshold_nodes) & set([runway_nodes[0], runway_nodes[-1]])

            if common_nodes:
                common_node = list(common_nodes)[0]  # Get the common node

                # Determine if the threshold needs to be reversed
                if threshold_nodes[0] == common_node:
                    ordered_threshold_nodes = threshold_nodes  # Already in correct order
                else:
                    ordered_threshold_nodes = threshold_nodes[::-1]  # Reverse it

                # Merge at the correct position
                if runway_nodes[0] == common_node:
                    merged_nodes = ordered_threshold_nodes[::-1] + runway_nodes[1:]  # Insert at start
                else:
                    merged_nodes = runway_nodes[:-1] + ordered_threshold_nodes  # Insert at end

                # Update the runway node list
                runway["nodes"] = merged_nodes
                break  # Stop after merging one threshold into a runway

    # split the runways for each runway direction and reformat the data
    for key,value in runways.items():
        heading = calculate_angle(all_nodes, value['nodes'][0], value['nodes'][-1])    
        for runway in key.split('/'):
            direction = int(runway[:2])*10
            processed[runway] = {'direction': direction}
            if abs(direction - heading) < 90:
                processed[runway]['angle'] = heading
                processed[runway]['threshold'] = value['thresholds'][0]
                processed[runway]['nodes'] = value['nodes']
            else:
                processed[runway]['angle'] = (heading + 180) % 360
                processed[runway]['threshold'] = value['thresholds'][1]
                processed[runway]['nodes'] = value['nodes'][::-1]

            initial_height = 3000
            distance_from_threshold = units.m(feet=(initial_height-50)/math.tan(math.radians(3)))
            angle = math.radians((90-processed[runway]['angle']-180)%360)
            processed[runway]['init_offset_from_threshold'] = (distance_from_threshold*math.cos(angle), distance_from_threshold*math.sin(angle))

    # find the exits for each runway and calculate the direction, TORA and LDA
    for key,value in processed.items():
        value['exits'] = {}
        start_node = value['nodes'][0]
        end_node = value['nodes'][-1]

        for node in value['nodes']:
            if node in taxi_nodes:
                exit_name = taxi_nodes[node]['parents'][0]
                if exit_name in value['exits']:
                    continue
                holding_point = find_hold_point(taxi_nodes, all_nodes, node, exit_name)
                if holding_point == None:
                    continue

                LDA = calculate_distance(all_nodes, node, start_node)
                TORA = calculate_distance(all_nodes, node, end_node)
                heading = calculate_angle(all_nodes, node, holding_point, positive=False) - value['angle']
                if heading < -180:
                    heading += 360
                if heading > 180:
                    heading -= 360
                    
                if heading < 0:
                    direction = 'left'
                else:
                    direction = 'right'

                value['exits'][taxi_nodes[node]['parents'][0]] = {'node': node, 'TORA': TORA, 'LDA': LDA, 'direction': direction, 'angle': heading, 'holding_point': holding_point}	
    return processed

def process_aprons(elements, all_nodes):
    aprons = {}
    polygons = {}
    for element in elements:
        if element['type'] == 'way' and 'aeroway' in element['tags'] and element['tags']['aeroway'] == 'apron':
            apron_coords = [all_nodes[n] for n in element['nodes']]
            apron_polygon = Polygon(apron_coords)
            aprons[element['tags']['ref'] if 'ref' in element['tags'] else element['id']] = element['nodes']
            polygons[element['tags']['ref'] if 'ref' in element['tags'] else element['id']] = apron_polygon
    return aprons, polygons

def process_gates(elements, all_nodes, aprons):
    gates = {}
    
    for element in elements:
        if element['type'] == 'way' and 'aeroway' in element['tags'] and 'ref' in element['tags'] and element['tags']['aeroway'] == 'parking_position':
            ref = element['tags']['ref']
            gate_coords = [all_nodes[n] for n in element['nodes'] if n in all_nodes]
            gate_polygon = LineString(gate_coords)
            for apron_name, apron in aprons.items():
                if ref not in gates and gate_polygon.intersects(apron):
                    gates[ref] = {'nodes': element['nodes'], 'apron': apron_name}
                    break

    return gates

def find_hold_point(taxi_nodes, all_nodes, node, ref):
    q = queue.Queue()
    q.put(node)
    visited_nodes = []
    while not q.empty():
        node = q.get()
        if node in visited_nodes or ref not in taxi_nodes[node]['parents']:
            continue
        visited_nodes.append(node)

        if 'holding_position' in taxi_nodes[node] and taxi_nodes[node]['holding_position']:
            return node
        for new_node in taxi_nodes[node]['next_moves']:
            q.put(new_node)

    return None

def angle_difference(angle1, angle2):
    diff = abs(angle1 - angle2) % 360
    return min(diff, 360 - diff)

def calculate_route (taxi_nodes,all_nodes, begintoestand, destination, starting_via=None, angle=None):
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
                angle = angle_difference(
                    calculate_angle(all_nodes, prev_node, node),
                    calculate_angle(all_nodes, new_node, node)
                )
                if angle < 90:  # Skip if the angle is too acute
                    continue
            else:
                if starting_via is not None and starting_via not in taxi_nodes[new_node]['parents']:
                    continue
                if angle is not None:
                    angle = angle_difference(
                        calculate_angle(all_nodes, node, new_node),
                        angle
                    )
                    if angle < 90:  # Skip if the angle is too acute
                        continue

            #solution found: get path from parent nodes
            if new_node == destination or destination in taxi_nodes[new_node]['parents']:
                print("Oplossing gevonden! ")
                path = [new_node]
                while True:
                    path.append(node)
                    if parent == None:
                        break
                    state = parent
                    node = state['node']
                    parent = state['parent']
                print(len(path),i, path)
                return path[::-1]
            #no solution found: add node to queue
            else: 
                added_distance = calculate_distance(all_nodes, new_node, node)
                if starting_via != None and starting_via in taxi_nodes[new_node]['parents']:
                    added_distance *= 0.01

                distance = state[0] + added_distance
                q.put((distance, new_node, {'node': new_node, 'parent': state[-1]}))
    print(f"Geen oplossing gevonden: laatse via: {starting_via}")	
    return None # geen oplossing gevonden

def calculate_via_route(taxi_nodes, all_nodes, start_node, destination, vias):
    start_time = time.time()
    route = [start_node]
    vias.append(destination)
    starting_state = (0, start_node, {'node': start_node, 'parent': None})
    angle = None

    for i, via in enumerate(vias):
        #TODO it should not go back to the previous node after a via
        #TODO it should pass the last angle so it can't go back on intself
        path = calculate_route(taxi_nodes, all_nodes, starting_state, via, starting_via=vias[i-1] if i > 0 else None, angle=angle if angle != None else None)
        if path == None:
            continue
            return None
        route.extend(path)
        starting_state = (0, route[-1], {'node': route[-1], 'parent': None})
        angle = calculate_angle(all_nodes, route[-1], route[-2])
    
    end_time = time.time()
    print(f"Time taken to run calculate_via_route: {end_time - start_time} seconds")
    return route


if __name__ == '__main__':
    print('test')