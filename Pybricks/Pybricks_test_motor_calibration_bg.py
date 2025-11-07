#******************************************************************************
# Tests the pylib_motor_calibration with non-blocking background tasks.       *
#******************************************************************************
from pybricks.hubs import ThisHub
from pybricks.parameters import Port
from pybricks.pupdevices import Motor
from pylib_async import EventLoop, WaitForRelativeTime, WaitForTaskCompleted
from pylib_bg_logger import print_bg_log_messages_and_clean
from pylib_console import ConsoleHandler, print_prompt
from pylib_motor_calibration import calibrate_motor_task, decalibrate_motor_task

s_event_loop = None
s_running = True
s_command_tokens = None

# Print available commands.
def print_commands():
        print("X | EXIT .................. terminates the program")
        print("? | HELP .................. prints available commands")
        print("C | CALIBRATE <motor> ..... calibrates the motor [1...4]")
        print("D | DECALIBRATE <motor> ... decalibrates the motor [1...4]")
        print("L | BACKGROUND_LOG ........ prints the background log")

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
    elif command == "L" or command == "BACKGROUND_LOG":
        print_bg_log_messages_and_clean()
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
            # Command processing shall be done here, bacause yield must be
            # called here and not in a sub-function.
            command = "".join(s_command_tokens[0:1]).upper()
            arg1 = "".join(s_command_tokens[1:2])
            if command == "C" or command == "CALIBRATE":
                if arg1 == "1":
                    motor = motor1
                    task_name = "motor_task_1"
                elif arg1 == "2":
                    motor = motor2
                    task_name = "motor_task_2"
                elif arg1 == "3":
                    motor = motor3
                    task_name = "motor_task_3"
                elif arg1 == "4":
                    motor = motor4
                    task_name = "motor_task_4"
                else:
                    motor = None
                if motor and not s_event_loop.task_exists(task_name):
                    # Calibrate the motor and wait until completed.
                    print("CALIBRATE", arg1, "...")
                    s_event_loop.register_task(calibrate_motor_task(motor), task_name)
            elif command == "D" or command == "DECALIBRATE":
                if arg1 == "1":
                    motor = motor1
                    task_name = "motor_task_1"
                elif arg1 == "2":
                    motor = motor2
                    task_name = "motor_task_2"
                elif arg1 == "3":
                    motor = motor3
                    task_name = "motor_task_3"
                elif arg1 == "4":
                    motor = motor4
                    task_name = "motor_task_4"
                else:
                    motor = None
                if motor and not s_event_loop.task_exists(task_name):
                    # Decalibrate the motor and wait until completed.
                    print("DECALIBRATE", arg1, "...")
                    s_event_loop.register_task(decalibrate_motor_task(motor), task_name)
            s_command_tokens = None
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