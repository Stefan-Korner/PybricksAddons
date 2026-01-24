#******************************************************************************
# Provides actions for de-calibrating and calibration a motor.                *
#******************************************************************************
from pylib_async import WaitFor, WaitForRelativeTime
from pylib_bg_logger import bg_log
from pylib_telemetry import print_telemetry_parameter

class WaitForMotorCalibrated(WaitFor):

    def __init__(self, motor):
        super().__init__()
        self.motor = motor

    def test_event(self, event_loop):
        angle = self.motor.angle()
        speed = self.motor.speed()
        # (condition reached, return value)
        return ((angle < 5 and angle > -5 and speed == 0), angle)

# Asynchronous task for calibrating a motor.
def calibrate_motor_task(motor, motor_id="default"):
    angle = motor.angle()
    bg_log(f"calibrate motor {motor_id} angle = {angle}")
    print_telemetry_parameter(motor_id, str(angle))
    # Set the motor back zu zero position and wait until it is reached
    motor.reset_angle()
    angle = motor.angle()
    bg_log(f"motor absolute angle = {angle}")
    print_telemetry_parameter(motor_id, str(angle))
    motor.run_target(20, 0, wait=False)
    angle = yield WaitForMotorCalibrated(motor)
    # Stop the motor to stop controlling the position
    motor.stop()
    bg_log(f"calibration of motor {motor_id} done, angle = {angle}")
    print_telemetry_parameter(motor_id, str(angle))
    return None

# Asynchronous task for decalibrating a motor.
def decalibrate_motor_task(motor, motor_id="default"):
    bg_log(f"decalibrate motor {motor_id} (for test purpose)...")
    # Run the motor for some time to force a decalibration
    motor.run(200)
    yield WaitForRelativeTime(2)
    motor.stop()
    angle = motor.angle()
    bg_log(f"decalibration of motor {motor_id} done, angle = {angle}")
    print_telemetry_parameter(motor_id, str(angle))
    return None