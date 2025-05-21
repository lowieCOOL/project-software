import re
import json
import csv
import difflib

# --- Load airline callsign data by airline name (case-insensitive) ---
callsign_lookup = {}
with open('schedule_generator/airlines.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        name = row['Name'].strip().lower()
        callsign_lookup[name] = {
            'icao': row['Airline'].strip(),
            'callsign': row['Callsign'].strip(),
            'country': row['Country code'].strip()
        }

flights = []
with open('schedule_generator/raw_schedule.txt', encoding='utf-8') as f:
    lines = [line.strip() for line in f if line.strip()]

i = 0
while i < len(lines):
    # Case 1: time and flight number on the same line
    if re.match(r'^\d{1,2}:\d{2} [AP]M\s+\w+', lines[i]):
        block_start = i
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
        flights.append((airline, atype, reg))

    # Move to next block: find the next line that looks like a time
    while i < len(lines) and not re.match(r'^\d{1,2}:\d{2} [AP]M', lines[i]):
        i += 1

schedule = {}
for airline, atype, reg in flights:
    key = airline.lower()
    icao = ''
    callsign = ''
    country = ''
    # Try exact match first
    if key in callsign_lookup:
        icao = callsign_lookup[key]['icao']
        callsign = callsign_lookup[key]['callsign']
        country = callsign_lookup[key]['country']
    else:
        # Fuzzy match: find the closest airline name in the lookup
        close = difflib.get_close_matches(key, callsign_lookup.keys(), n=1, cutoff=0.8)
        if close:
            match_key = close[0]
            icao = callsign_lookup[match_key]['icao']
            callsign = callsign_lookup[match_key]['callsign']
            country = callsign_lookup[match_key]['country']

    if airline not in schedule:
        schedule[airline] = {
            'callsign_ICAO': icao,
            'callsign_SAY': callsign,
            'frequency': 0,
            'aircraft': {}
        }
    if atype not in schedule[airline]['aircraft']:
        schedule[airline]['aircraft'][atype] = {
            'apron': [],
            'frequency': 0,
        }
    schedule[airline]['frequency'] += 1
    schedule[airline]['aircraft'][atype]['frequency'] += 1

print('total flights:', len(flights))

with open("schedule_generator/schedule.json", "w") as f:
    json.dump(schedule, f, indent=2)