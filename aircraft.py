from main import network

'''
Aircraft states:
for departures
- gate
- pushback
- hold_pushback
- taxi
- hold_taxi
- hold_runway
- line_up
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

class Aircraft():
    def __init__(self, position, heading, speed, state, callsign):
        self.position = position
        self.heading = heading
        self.speed = speed
        self.state = state
        self.callsign = callsign
        self.route = []

    def click_handler(self):
        # when clicked on the aircraft, the info and action of the aircraft will be displayed in the sidepanel, depending on the state of the aircraft
        pass

    def calculate_route(self):
        pass

    def calculate_via_route(self):
        pass

    def follow_route(self):
        # code to have an aircraft moving along the nodes in self.route
        pass

    def hold_position(self):
        # code to have an aircraft stop at current position
        pass

    def continue_taxi(self):
        if self.state != 'hold_taxi':
            return

        # code to have an aircraft continue taxiing
        pass

    def tick(self):
        pass

class Arrival(Aircraft):
    def __init__(self, callsign, runway, LDA, Vat):
        super().__init__(position=network['runways'][runway]['init'], heading=network['runways'][runway]['angle'], speed=200, state='arrival' , callsign=callsign)
        self.runway  = network['runways'][runway]
        self.exitsAvailable = {key: item for key, item in self.runway['exits'].items() if item['LDA'] > self.LDA}
        self.altitude = 3000
        self.LDA = LDA
        self.Vat = Vat

    def go_around(self):
        pass

    def land(self):
        pass

class Departure(Aircraft):
    def __init__(self, callsign, gate):
        # TODO: don't use the gate but apron and select a gate from the apron here
        # TODO: add performance parameters or one single parameter for the aircraft and split it in the constructor
        super().__init__(position=gate['init'], heading=gate['angle'], speed=0, state='gate', callsign=callsign)
        self.gate = gate

    def pushback(self, direction):
        # pushback
        self.state = 'pushback'

        # after pushback, set state to taxi
        self.state = 'hold_pushback'

    def taxi(self, destination, vias=None):
        #destination is a runway exit name, get the destination node from network['runways']
        pass

    def line_up(self):
        # line up on the runway
        pass

    def takeoff(self):
        if self.state == 'taxi':
            self.line_up()
        
        # takeoff
        pass

if __name__ == '__main__':
    pass