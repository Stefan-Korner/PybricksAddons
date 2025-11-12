#******************************************************************************
# Provides helper functions for railroad switch                               *
#******************************************************************************
from pylib_async import WaitForRelativeTime
from pylib_bg_logger import bg_log

class Position:
    A: Position = "A"
    B: Position = "B"

def switch_to_position(motor, target_position):
    if motor:
        if target_position == Position.A:
            motor.run_target(100, 25, wait=False)
        elif target_position == Position.B:
            motor.run_target(100, -25, wait=False)

def switch_position(motor):
    if motor:
        angle = motor.angle()
        if (35 > angle and angle > 15):
            return Position.A
        elif (-15 > angle and angle > -35):
            return Position.B
    return None

def print_position(motor, switch_name):
    position = switch_position(motor)
    print(switch_name, "has position", position)

# Asynchronous task for switching a switch
def switch_task(motor, switch_name, target_position):
    bg_log("try " + switch_name + " to position " + str(target_position))
    if switch_position(motor) == target_position:
        bg_log(switch_name + " already has position " + str(target_position))
        return None
    motor.reset_angle()
    switch_to_position(motor, target_position)
    yield WaitForRelativeTime(1)
    motor.stop()
    return None