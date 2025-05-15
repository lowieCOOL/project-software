import re
import json

# --- Load airline callsign data by IATA code ---
callsign_lookup = {}
with open('schedule_generator/airlines.dat', encoding='utf-8') as f:
    for line in f:
        parts = line.strip().split(',')
        if len(parts) > 5:
            iata = parts[3].strip('"').upper()
            icao = parts[4].strip('"')
            name = parts[1].strip('"')
            callsign = parts[5].strip('"')
            if iata:
                callsign_lookup[iata] = {'icao': icao, 'name': name, 'callsign': callsign}

flights = []
with open('schedule_generator/raw_schedule.txt', encoding='utf-8') as f:
    lines = [line.strip() for line in f if line.strip()]

i = 0
while i < len(lines):
    # Case 1: time and flight number on the same line
    if re.match(r'^\d{1,2}:\d{2} [AP]M\s+\w+', lines[i]):
        block_start = i
        # Extract flight number (e.g., BA16)
        flight_match = re.match(r'^\d{1,2}:\d{2} [AP]M\s+(\w+\d+)', lines[i])
        flight_number = flight_match.group(1) if flight_match else ''
        i += 1
    # Case 2: time on one line, flight number on the next
    elif re.match(r'^\d{1,2}:\d{2} [AP]M$', lines[i]) and i + 1 < len(lines) and re.match(r'^\w+\d+$', lines[i+1]):
        block_start = i
        flight_number = lines[i+1]
        i += 2
    else:
        i += 1
        continue

    # Try both offsets for airline/aircraft line
    airline_aircraft_line = None
    for offset in [2, 3]:
        idx = block_start + offset
        if idx < len(lines):
            candidate = lines[idx]
            # Look for a line with a tab and a registration pattern (e.g., (XX-XXX))
            if '\t' in candidate and re.search(r'\([A-Z0-9\-]+\)', candidate):
                airline_aircraft_line = candidate
                break

    if airline_aircraft_line:
        parts = airline_aircraft_line.split('\t')
        if len(parts) >= 2:
            airline = re.sub(r'\s*\(.*?\)', '', parts[0].strip())
            aircraft_info = parts[1].strip()
        else:
            airline = re.sub(r'\s*\(.*?\)', '', airline_aircraft_line.strip())
            aircraft_info = ''
        match = re.match(r'(\w+)\s*\(([^)]+)\)', aircraft_info)
        if match:
            atype = match.group(1)
            reg = match.group(2)
        else:
            atype = aircraft_info
            reg = ''
        # Extract IATA code from flight number (first 2 or 3 uppercase letters)
        iata_match = re.match(r'^([A-Z0-9]{2})', flight_number)
        iata = iata_match.group(1) if iata_match else ''
        flights.append((airline, atype, reg, iata))

    # Move to next block: find the next line that looks like a time
    while i < len(lines) and not re.match(r'^\d{1,2}:\d{2} [AP]M', lines[i]):
        i += 1

schedule = {}
for airline, atype, reg, iata in flights:
    icao = ''
    callsign = ''
    airline_name = iata  # fallback if not found
    if iata in callsign_lookup:
        icao = callsign_lookup[iata]['icao']
        callsign = callsign_lookup[iata]['callsign']
        airline_name = callsign_lookup[iata]['name']

    if airline_name not in schedule:
        schedule[airline_name] = {
            'callsign_ICAO': icao,
            'callsign_SAY': callsign,
            'frequency': 0,
            'aircraft': {}
        }
    if atype not in schedule[airline_name]['aircraft']:
        schedule[airline_name]['aircraft'][atype] = {
            'apron': [],
            'frequency': 0,
        }
    schedule[airline_name]['frequency'] += 1
    schedule[airline_name]['aircraft'][atype]['frequency'] += 1

print('total flights:', len(flights))

with open("schedule_generator/schedule.json", "w") as f:
    json.dump(schedule, f, indent=2)