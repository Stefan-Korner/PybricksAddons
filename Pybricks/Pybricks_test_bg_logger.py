#******************************************************************************
# Tests the pylib_bg_logger.                                                  *
#******************************************************************************
from pylib_async import EventLoop, WaitFor, WaitForRelativeTime
from pylib_console import ConsoleHandler
from pylib_bg_logger import bg_log, print_bg_log_messages_and_clean

s_running = True

# Task 1.
def task1():
    global s_running
    print("task1 started")
    counter = 0
    while s_running:
        bg_log(f"task1: {counter}")
        counter += 1
        yield WaitForRelativeTime(1)
    print("task1 stopped")
    return None

# Task 2.
def task2():
    global s_running
    print("task2 started")
    counter = 0
    while s_running:
        bg_log(f"task2: {counter}")
        counter += 1
        yield WaitForRelativeTime(2)
    print("task2 stopped")
    return None

# Handle the command line.
def handle(command_line):
    global s_running
    command_tokens = command_line.split()
    command = "".join(command_tokens[0:1]).upper()
    if command == "X" or command == "EXIT":
        s_running = False
    elif command == "?" or command == "HELP":
        print("X | EXIT .... terminates the program")
        print("? | HELP .... prints available commands")
        print("P | PRINT ... print the background log and clean")
    elif command == "P" or command == "PRINT":
        print("log messages:")
        print_bg_log_messages_and_clean()
    # Show the prompt when True.
    return s_running

# Console task.
def console():
    global s_running
    print("console started")
    console_handler = ConsoleHandler(handle)
    while s_running:
        console_handler.poll()
        yield WaitForRelativeTime(0.1)
    print("console stopped")
    return None

event_loop = EventLoop()
event_loop.register_task(task1(), "task1")
event_loop.register_task(task2(), "task2")
event_loop.register_task(console(), "console")
event_loop.run(poll_time=0.01)
print("processing finished")