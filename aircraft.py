from main import network

class Aircraft():
    def __init__(self, position, heading, state, callsign):
        self.position = position
        self.state = state
        self.callsign = callsign
        self.route = []
        self.heading = heading

class Arrival(Aircraft):
    def __init__(self, callsign, runway):
        super().__init__(network[runway]['init'], network[runway]['angle'], 'arrival' , callsign)
        self.runway  = runway
        self.altitude = 3000
        self.speed = 200

class Departure(Aircraft):
    def __init__(self, position, heading, callsign, gate):
        super().__init__(position, heading, 'gate', callsign)
        self.gate = gate