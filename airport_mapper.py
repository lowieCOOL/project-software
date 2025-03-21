import json
import queue
import math

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
    node1 = node2metric(all_nodes[node1])
    node2 = node2metric(all_nodes[node2])
    return math.dist(node1,node2)
    
def calculate_angle(all_nodes, node1, node2):
    node1 = node2metric(all_nodes[node1])
    node2 = node2metric(all_nodes[node2])

    angle = math.degrees(math.atan2(node2[1] - node1[1], node2[0] - node1[0]))
    if angle < 0:
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

    for key,value in runways.items():
        angle = calculate_angle(all_nodes, value['nodes'][0], value['nodes'][1])    
        for runway in key.split('/'):
            direction = int(runway[:2])*10
            processed[runway] = {'direction': direction}
            if abs(direction - angle) < 90:
                processed[runway]['angle'] = angle
                processed[runway]['nodes'] = value['nodes']
            else:
                processed[runway]['angle'] = (angle + 180) % 360
                processed[runway]['nodes'] = value['nodes'][::-1]

    for key,value in processed.items():
        value['exits'] = {}
        start_node = value['nodes'][0]
        end_node = value['nodes'][-1]

        for node in value['nodes']:
            if node in taxi_nodes:
                LDA = calculate_distance(all_nodes, node, start_node)
                TORA = calculate_distance(all_nodes, node, end_node)
                value['exits'][taxi_nodes[node]['parents'][0]] = {'node': node, 'TORA': TORA, 'LDA': LDA}

    with open("osm_data_processed.json", "w") as f:
        json.dump(processed, f, indent=2)
    return processed

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