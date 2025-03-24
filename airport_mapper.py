import json
import queue
import math
from geopy.distance import geodesic
from geopy import units

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
    
def calculate_angle(all_nodes, node1, node2, positive=True):
    node1 = node2metric(all_nodes[node1])
    node2 = node2metric(all_nodes[node2])

    angle = math.degrees(math.atan2(node2[1] - node1[1], node2[0] - node1[0]))
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
    network['taxi_nodes'] = taxi_nodes
    
    return network

def process_runways(all_nodes, runways, thresholds, taxi_nodes):
    processed = {}

    # find the thresholds of the runways
    for runway in runways.values():
        runway['thresholds'] = runway['nodes'][::len(runway['nodes'])-1]

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
        angle = calculate_angle(all_nodes, value['nodes'][0], value['nodes'][1])    
        for runway in key.split('/'):
            direction = int(runway[:2])*10
            processed[runway] = {'direction': direction}
            if abs(direction - angle) < 90:
                processed[runway]['angle'] = angle
                processed[runway]['threshold'] = value['thresholds'][0]
                processed[runway]['nodes'] = value['nodes']
            else:
                processed[runway]['angle'] = (angle + 180) % 360
                processed[runway]['threshold'] = value['thresholds'][1]
                processed[runway]['nodes'] = value['nodes'][::-1]

            initial_height = 3000
            distance_from_threshold = units.m(feet=(initial_height-50)/math.tan(math.radians(3)))
            processed[runway]['init_offset_from_threshold'] = (distance_from_threshold*math.cos(math.radians(processed[runway]['angle']-180)), distance_from_threshold*math.sin(math.radians(processed[runway]['angle']-45)))
            # todo fix angles

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
                angle = calculate_angle(all_nodes, node, holding_point, positive=False) - value['angle']
                if angle < -180:
                    angle += 360
                    
                if angle < 0:
                    direction = 'left'
                else:
                    direction = 'right'

                value['exits'][taxi_nodes[node]['parents'][0]] = {'node': node, 'TORA': TORA, 'LDA': LDA, 'direction': direction, 'angle': angle, 'holding_point': holding_point}	

    with open("osm_data_processed.json", "w") as f:
        json.dump(processed, f, indent=2)
    return processed

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

def calculate_route (network,all_nodes, begintoestand, destination) :
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
        directions = network[node]['next_moves']

        visited_nodes.append(node)
        
        for new_node in directions:
            if new_node == destination:
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
                #draw path
                return path
            else: 
                distance = state[0] + calculate_distance(all_nodes, new_node, node)
                q.put((distance, new_node, {'node': new_node, 'parent': state[-1]}))
    return None # geen oplossing gevonden


if __name__ == '__main__':
    print('test')