import json
import time
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
    
def map_airport():
    elements = read_json('osm_data.json')
    network = {}

    for element in elements:
        if element['type'] != 'way' or element['tags']['aeroway'] != 'taxiway' or 'ref' not in element['tags']:
            continue

        for i, node in enumerate(element['nodes']):
            parent = element['tags']['ref']
            if not node in network:
                network[node] = {'next_moves': [], 'parents': [parent]}
            if not parent in network[node]['parents']:
                network[node]['parents'].append(parent)

            if i != len(element['nodes'])-1:
                network[node]['next_moves'].append(element['nodes'][i+1])
            if i != 0:
                network[node]['next_moves'].append(element['nodes'][i-1])

    return network

def calculate_distance(all_nodes, node1,node2):
    node1 = node2metric(all_nodes[node1])
    node2 = node2metric(all_nodes[node2])
    return math.dist(node1,node2)



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
    network = map_airport()
    calculate_route(network,(0 ,60753970,{'node': 60753970, 'parent':None}), destination=662320034)