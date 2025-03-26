import requests
from bs4 import BeautifulSoup
import json

def fetch_icao_codes():
    """Fetch all ICAO codes from the dropdown menu."""
    url = "https://contentzone.eurocontrol.int/aircraftperformance/details.aspx?ICAO=A388"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Locate the dropdown and extract ICAO codes
        dropdown = soup.find('select', id='wsGroupDropDownList')
        options = dropdown.find_all('option')
        icao_codes = [option['value'] for option in options]
        return icao_codes
    else:
        print("Failed to fetch ICAO codes. HTTP Status Code:", response.status_code)
        return []

def fetch_aircraft_data(icao_code):
    """Fetch data for a single aircraft."""
    url = f"https://contentzone.eurocontrol.int/aircraftperformance/details.aspx?ICAO={icao_code}"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract and return data for this aircraft
        try:
            aircraft_data = {
                'WTC': soup.find('span', id='wsWTCLiteral').text.strip(),
                'dist_TO': int(soup.find('span', id='wsFARTOLiteral').text.strip()),
                'dist_LD': int(soup.find('span', id='wsFARLDLiteral').text.strip()),
                'speed_V2': int(soup.find('span', id='wsV2Literal').text.strip()),
                'speed_climb': int(soup.find('span', id='wsINVCLLiteral').text.strip()),
                'speed_Vat': int(soup.find('span', id='wsVTHLiteral').text.strip()),
                'rate_of_climb': int(soup.find('span', id='wsINROCLiteral').text.strip()),
                'wingspan': float(soup.find('span', id='MainContent_wsLabelWingSpan').text.strip().split(' ')[0]),
                'length': float(soup.find('span', id='MainContent_wsLabelLength').text.strip().split(' ')[0]),
            }
            return aircraft_data
        except Exception as e:
            print(f"Failed to extract data for {icao_code}: {e}")
            return None
    else:
        print(f"Failed to fetch data for {icao_code} (HTTP Status: {response.status_code})")
        return None

def scrape_aircrafts_to_json(icao_codes):
    """Scrape multiple aircraft and save to a single JSON."""
    try:
        with open("all_aircraft_data.json", "r") as file:
            all_aircraft_data = json.load(file)
    except:
        all_aircraft_data = {}

    icao_codes = fetch_icao_codes()
    for code in icao_codes:
        if code in all_aircraft_data:
            continue
        data = fetch_aircraft_data(code)
        if data:
            all_aircraft_data[code] = data
    
    # Write all data to JSON file
    with open('all_aircraft_data.json', 'w') as file:
        json.dump(all_aircraft_data, file, indent=4)
    print("Data successfully written to all_aircraft_data.json")

# List of ICAO codes to scrape
icao_codes = ['A319', 'B738', 'E190', 'A320', 'A388']  # Add ICAO codes here
scrape_aircrafts_to_json(icao_codes)