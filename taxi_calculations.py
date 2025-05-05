

def airplane_taxi_speed (self, distance, taxi_acceleration, v_end, dt):
    WTC = self.performance["WTC"]

    needed_distance = ((self.speed)**2 - (v_end)**2) / 2*taxi_acceleration
    distance = distance - self.speed * dt

    if WTC == 'H' or 'L':
        max_taxispeed = 15
    elif WTC == 'M':
        max_taxispeed = 20

    if distance > needed_distance and self.speed < max_taxispeed:
        self.speed = self.speed + taxi_acceleration * dt

    elif distance > needed_distance and self.speed >= max_taxispeed:
        self.speed = max_taxispeed

    elif distance <= needed_distance:
        self.speed = self.speed -taxi_acceleration * dt

    return self.speed
airplane_taxi_speed(self, distance, 0.6, v_end, 1)