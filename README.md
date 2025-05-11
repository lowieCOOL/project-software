# Project: ATC Simulator

Step into the shoes of an Air Traffic Controller in this realistic simulation game. Featuring physics based on real-world aircraft behavior, the game lets you guide planes safely across complex airports — and even allows you to add custom aircraft.

One of the standout features is the ability to import airports directly from OpenStreetMap. The game includes Brussels Airport by default to get you started.


## How to Play

Use a variety of commands to manage aircraft as they progress through different phases of flight. Each aircraft enters specific states, and your role is to issue the appropriate instructions to ensure safe and efficient operation.

Refer to the attached document for a detailed map of the airport, including all runway names and important notes.
[EBBR_GMC01_v64.pdf](https://github.com/user-attachments/files/20151469/EBBR_GMC01_v64.pdf)

### **Departure Workflow**

**Aircraft States & Commands:**

for departures
- pushback
- pushback_complete
- cleared_takeoff
- takeoff
- gate
    - pushback(direction) direction is [north, east, south, west]
- ready_taxi
    - taxi(runway, destination, vias=[]) destination is a runway exit name, vias is a list of taxi names to route via
- taxi
    - hold_position() hold at the current position, this is used to wait for a crossing aircraft or other reason
    - cross_runway() preemptively give clearance to cross runway
    - line_up() already give lineup clearance so aircraft doesn't have to stop at the holding point
    - takeoff() already give takeoff clearance so aircraft doesn't have to stop at the holding point
- hold_taxi
    - continue_taxi() continue taxiing after holding position
- hold_runway
    - cross_runway()
- cleared_crossing
    - hold_position()
- crossing_runway
- ready_line_up
    - line_up()
- line_up
    - takeoff()
- ready_takeoff
    - takeoff()

for arrivals
- cleared_land
- arrival
    - land(exit) land on the runway and vacate at the specified exit
    - go_around() go around, abort the landing
- rollout
    - taxi(vias=[]) preemtively give taxi to the gate, vias is a list of taxi names to route via
- vacate
    - taxi(vias=[]) preemtively give taxi to the gate, vias is a list of taxi names to route via
- vacate_continue
    - taxi(vias=[]) continue taxiing after vacating the runway
- ready_taxi_gate
    - taxi(vias=[]) taxi to the gate
- taxi
    - hold_position() hold at the current position, this is used to wait for a crossing aircraft or other reason
    - cross_runway() preemptively give clearance to cross runway
    - taxi(vias=[]) vias is a list of taxi names to route via, used to give new route to the aircraft
- hold_taxi
    - continue_taxi() continue taxiing after holding position
- hold_runway
    - cross_runway()
- cleared_crossing
    - hold_position()
- crossing_runway
- park

### Can you handle the skies?

Take control, keep the airspace safe, and prove you’ve got what it takes to be a top air traffic controller.


