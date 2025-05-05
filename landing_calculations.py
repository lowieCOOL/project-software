import math

def landing_speed(self, dt, exit_speed):

    dist_LD = self.performance ["dist_LD]"]
    speed_Vat = self.perfromance ["speed_Vat"]
    altitude = (distance_from_threshold - self.peed * dt) * math.sin(3) + 50
    deacceleration = (self.speed**2 - exit_speed**2) / dist_LD * 2

    if altitude > 0:
        self.speed = speed_Vat
    elif altitude == 0:
        self.speed = self.speed - deacceleration * dt

    return self.speed, altitude
landing_speed(self, dt,10)