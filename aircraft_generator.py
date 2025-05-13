'''
This module generates flights for a given airport based on a schedule and performance data.
It includes functions to read the schedule and performance data from JSON files,
generate random callsigns, and create flight objects for arrivals and departures.
'''

from aircraft import Arrival, Departure
import random
import string
import json

#generate a random callsign for the flight form the json file
def generate_callsign(airline_callsign: str, numbers: int, letters: int):
    numbers = ''.join(random.choices(string.digits, k=numbers))
    letters = ''.join(random.choices(string.ascii_uppercase, k=letters))
    callsign = airline_callsign + numbers + letters
    return callsign

def read_schedule(airport: str):
    with open(f"airports/{airport}/schedule.json", "r") as file:
        schedule_json = json.load(file)

    return schedule_json

def read_runways(airport: str):
    with open(f"airports/{airport}/Runway_configuration.json", "r") as file:
        runway_json = json.load(file)

    return runway_json

def read_performance():
    with open("all_aircraft_data.json", "r") as file:
        performance_json = json.load(file)

    return performance_json
# This function generates a flight based on the provided schedule, performance data, and flight type.
def generate_flight(schedule_json: dict, all_performance: dict, type: str, active_runways: list = None, network: dict = None):
    if type not in ['arrival', 'departure']:
        raise ValueError("Type must be 'arrival' or 'departure'")
    if type == 'arrival' and active_runways is None:
        raise ValueError("Runways must be specified for arrival flights")
    if network is None:
        raise ValueError("Network data must be provided")

    airlines = list(schedule_json.keys())
    weights = [value['frequency'] for value in schedule_json.values()]
    airline = random.choices(airlines, weights=weights)[0]
    airline_data = schedule_json[airline]

    aircrafts = list(airline_data['aircraft'].keys())
    weights = [value['frequency'] for value in airline_data['aircraft'].values()]
    aircraft = random.choices(aircrafts, weights=weights)[0]
    aircraft_data = airline_data['aircraft'][aircraft]

    callsign = generate_callsign(airline_data['callsign_ICAO'], 1, 2)
    performance = all_performance[aircraft]
    
    apron = random.choice(aircraft_data['apron'])
    gates = [gate_number for gate_number, gate in network['gates'].items() if gate['apron'] == apron and not gate['occupied']]  # Filter gates by apron
    if not gates:
        print(ValueError(f"No gates available for apron {apron}"))
        return None
    gate = random.choice(gates)
    network['gates'][gate]['occupied'] = True

    if type == 'arrival':
        runway = random.choice(active_runways)
        flight = Arrival(callsign, performance, runway, network, gate, height=2000)
        
    elif type == 'departure':
        flight = Departure(callsign, performance, gate, network)

    return flight

if __name__ == '__main__':
    schedule = read_schedule('EBBR')
    performance = read_performance()
    from main import network

    for i in range(10):
        print(generate_flight(schedule, performance, 'departure', network=network))
