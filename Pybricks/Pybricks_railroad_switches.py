#******************************************************************************
# Controls 4 railroad switches.                                               *
#******************************************************************************
from pybricks.hubs import ThisHub
from pybricks.parameters import Port
from pybricks.pupdevices import Motor
from pylib_async import EventLoop, WaitForRelativeTime, WaitForTaskCompleted
from pylib_bg_logger import print_bg_log_messages_and_clean
from pylib_console import ConsoleHandler, print_prompt
from pylib_motor import calibrate_motor_task, decalibrate_motor_task
from pylib_railroad_switch import Position, print_position, switch_task
from pylib_telemetry import enable_telemetry, disable_telemetry

s_event_loop = None
s_running = True
s_command_tokens = None
s_motor1 = None
s_motor2 = None
s_motor3 = None
s_motor4 = None

# Print available commands.
def print_commands():
        print("X | EXIT .................. terminates the program")
        print("? | HELP .................. prints available commands")
        print("A | SWITCH_TO_A <motor> ... switch motor [1...4] to position A")
        print("B | SWITCH_TO_B <motor> ... switch motor [1...4] to position A")
        print("C | CALIBRATE <motor> ..... calibrates the motor [1...4]")
        print("D | DECALIBRATE <motor> ... decalibrates the motor [1...4]")
        print("T | TELEMETRY_ENABLE ...... enables telemetry printing")
        print("U | TELEMETRY_DISABLE ..... disables telemetry printing")

def print_switch_positions():
    global s_motor1, s_motor2, s_motor3, s_motor4
    print_position(s_motor1, "motor 1")
    print_position(s_motor2, "motor 2")
    print_position(s_motor3, "motor 3")
    print_position(s_motor4, "motor 4")

# Handle the command line.
def handle(command_line):
    global s_running, s_command_tokens
    s_command_tokens = command_line.split()
    command = "".join(s_command_tokens[0:1]).upper()
    if command == "X" or command == "EXIT":
        s_running = False
    elif command == "?" or command == "HELP":
        print_commands()
        print_switch_positions()
    elif command == "A" or command == "SWITCH_TO_A":
        # Processing of the command is done in the console task.
        # Don't show the prompt, this shall be done when the task is finished.
        return False
    elif command == "B" or command == "SWITCH_TO_B":
        # Processing of the command is done in the console task.
        # Don't show the prompt, this shall be done when the task is finished.
        return False
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
    global s_event_loop, s_running, s_command_tokens, s_motor1, s_motor2, s_motor3, s_motor4
    print("console started")
    s_motor1 = Motor(Port.A)
    s_motor2 = Motor(Port.B)
    s_motor3 = Motor(Port.C)
    s_motor4 = Motor(Port.D)
    print_commands()
    print_switch_positions()
    console_handler = ConsoleHandler(handle)
    while s_running:
        console_handler.poll()
        if s_command_tokens:
            # Command processing shall be done here, because yield must be
            # called here and not in a sub-function.
            command = "".join(s_command_tokens[0:1]).upper()
            arg1 = "".join(s_command_tokens[1:2])
            if command == "A" or command == "SWITCH_TO_A":
                if arg1 == "1":
                    motor = s_motor1
                elif arg1 == "2":
                    motor = s_motor2
                elif arg1 == "3":
                    motor = s_motor3
                elif arg1 == "4":
                    motor = s_motor4
                else:
                    motor = None
                if motor:
                    # Switch to position A and wait until completed.
                    print("SWITCH_TO_A", arg1, "...")
                    s_event_loop.register_task(switch_task(motor, "motor_" + arg1, Position.A), "switch_task")
                    yield WaitForTaskCompleted("switch_task", 10)
            elif command == "B" or command == "SWITCH_TO_B":
                if arg1 == "1":
                    motor = s_motor1
                elif arg1 == "2":
                    motor = s_motor2
                elif arg1 == "3":
                    motor = s_motor3
                elif arg1 == "4":
                    motor = s_motor4
                else:
                    motor = None
                if motor:
                    # Switch to position B and wait until completed.
                    print("SWITCH_TO_B", arg1, "...")
                    s_event_loop.register_task(switch_task(motor, "motor_" + arg1, Position.B), "switch_task")
                    yield WaitForTaskCompleted("switch_task", 10)
            elif command == "C" or command == "CALIBRATE":
                if arg1 == "1":
                    motor = s_motor1
                elif arg1 == "2":
                    motor = s_motor2
                elif arg1 == "3":
                    motor = s_motor3
                elif arg1 == "4":
                    motor = s_motor4
                else:
                    motor = None
                if motor:
                    # Calibrate the motor and wait until completed.
                    print("CALIBRATE", arg1, "...")
                    s_event_loop.register_task(calibrate_motor_task(motor, "motor_" + arg1), "motor_task")
                    yield WaitForTaskCompleted("motor_task", 30)
            elif command == "D" or command == "DECALIBRATE":
                if arg1 == "1":
                    motor = s_motor1
                elif arg1 == "2":
                    motor = s_motor2
                elif arg1 == "3":
                    motor = s_motor3
                elif arg1 == "4":
                    motor = s_motor4
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