def take_off_speed (self, dt):

    dist_TO = self.performance["dist_TO"]
    speed_V2 = self.performance["speed_V2"]
    rate_of_climb = self.performance["rate_of_climb"]

    acceleration = speed_V2**2 / 2 * dist_TO
    self.speed = self.speed + acceleration * dt

    if self.speed >= speed_V2:
        altitude = rate_of_climb * dt /60
    return self.speed, altitude
