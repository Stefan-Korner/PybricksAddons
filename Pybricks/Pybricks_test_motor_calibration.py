#******************************************************************************
# Tests the pylib_motor_calibration.                                          *
#******************************************************************************
from pybricks.hubs import ThisHub
from pybricks.parameters import Port
from pybricks.pupdevices import Motor
from pylib_async import EventLoop, WaitForRelativeTime, WaitForTaskCompleted
from pylib_bg_logger import print_bg_log_messages_and_clean
from pylib_console import ConsoleHandler, print_prompt
from pylib_motor_calibration import calibrate_motor_task, decalibrate_motor_task
from pylib_telemetry import enable_telemetry, disable_telemetry

s_event_loop = None
s_running = True
s_command_tokens = None

# Print available commands.
def print_commands():
        print("X | EXIT .................. terminates the program")
        print("? | HELP .................. prints available commands")
        print("C | CALIBRATE <motor> ..... calibrates the motor [1...4]")
        print("D | DECALIBRATE <motor> ... decalibrates the motor [1...4]")
        print("T | TELEMETRY_ENABLE ...... enables telemetry printing")
        print("U | TELEMETRY_DISABLE ..... disables telemetry printing")

# Handle the command line.
def handle(command_line):
    global s_running, s_command_tokens
    s_command_tokens = command_line.split()
    command = "".join(s_command_tokens[0:1]).upper()
    if command == "X" or command == "EXIT":
        s_running = False
    elif command == "?" or command == "HELP":
        print_commands()
    elif command == "C" or command == "CALIBRATE":
        # Processing of the command is done in the console task.
        # Don't show the prompt, this shall be done when the task is finished.
        return False
    elif command == "D" or command == "DECALIBRATE":
        # Processing of the command is done in the console task.
        # Don't show the prompt, this shall be done when the task is finished.
        return False
    elif command == "T" or command == "TELEMETRY_ENABLE":
        enable_telemetry()
    elif command == "U" or command == "TELEMETRY_DISABLE":
        disable_telemetry()
    s_command_tokens = None
    # Show the prompt when True.
    return s_running

# Console task.
def console():
    global s_event_loop, s_running, s_command_tokens
    print("console started")
    motor1 = Motor(Port.A)
    motor2 = Motor(Port.B)
    motor3 = Motor(Port.C)
    motor4 = Motor(Port.D)
    print_commands()
    console_handler = ConsoleHandler(handle)
    while s_running:
        console_handler.poll()
        if s_command_tokens:
            # Command processing shall be done here, because yield must be
            # called here and not in a sub-function.
            command = "".join(s_command_tokens[0:1]).upper()
            arg1 = "".join(s_command_tokens[1:2])
            if command == "C" or command == "CALIBRATE":
                if arg1 == "1":
                    motor = motor1
                elif arg1 == "2":
                    motor = motor2
                elif arg1 == "3":
                    motor = motor3
                elif arg1 == "4":
                    motor = motor4
                else:
                    motor = None
                if motor:
                    # Calibrate the motor and wait until completed.
                    print("CALIBRATE", arg1, "...")
                    s_event_loop.register_task(calibrate_motor_task(motor, "motor_" + arg1), "motor_task")
                    yield WaitForTaskCompleted("motor_task", 30)
            elif command == "D" or command == "DECALIBRATE":
                if arg1 == "1":
                    motor = motor1
                elif arg1 == "2":
                    motor = motor2
                elif arg1 == "3":
                    motor = motor3
                elif arg1 == "4":
                    motor = motor4
                else:
                    motor = None
                if motor:
                    # Decalibrate the motor and wait until completed.
                    print("DECALIBRATE", arg1, "...")
                    s_event_loop.register_task(decalibrate_motor_task(motor, "motor_" + arg1), "motor_task")
                    yield WaitForTaskCompleted("motor_task", 30)
            s_command_tokens = None
            print_bg_log_messages_and_clean()
            print_prompt()
        else:
            # This is the poll cycle for the console.
            yield WaitForRelativeTime(0.1)
    print("console stopped")
    return None

hub = ThisHub()
hub_name = hub.system.name()
print("hub_name =", hub_name)
s_event_loop = EventLoop()
s_event_loop.register_task(console(), "console")
s_event_loop.run(poll_time=0.01)
print("processing finished")