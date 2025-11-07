#******************************************************************************
# Tests the pylib_async and pylib_console.                                    *
#******************************************************************************
from pylib_async import EventLoop, WaitFor, WaitForRelativeTime
from pylib_console import ConsoleHandler

ACCU_STATE_MIN = 0
ACCU_STATE_MAX = 100
CHARGE_STATE_CHARGE = 1
CHARGE_STATE_DISCHARGE = 2
s_accu_state1 = None
s_accu_state2 = None
s_accu_state3 = None
s_accu_state4 = None
s_charge_state1 = None
s_charge_state2 = None
s_charge_state3 = None
s_charge_state4 = None
s_running = None

# Task for accu 1.
def accu1():
    global s_accu_state1, s_charge_state1
    print("accu1 started")
    s_accu_state1 = ACCU_STATE_MIN
    s_charge_state1 = CHARGE_STATE_DISCHARGE
    while s_accu_state1 != None:
        if s_charge_state1 == CHARGE_STATE_CHARGE and s_accu_state1 < ACCU_STATE_MAX:
            s_accu_state1 += 1
        elif s_charge_state1 == CHARGE_STATE_DISCHARGE and s_accu_state1 > ACCU_STATE_MIN:
            s_accu_state1 -= 1
        yield WaitForRelativeTime(1)
    print("accu1 stopped")
    return None

# Task for accu 2.
def accu2():
    global s_accu_state2, s_charge_state2
    print("accu2 started")
    s_accu_state2 = ACCU_STATE_MIN
    s_charge_state2 = CHARGE_STATE_DISCHARGE
    while s_accu_state2 != None:
        if s_charge_state2 == CHARGE_STATE_CHARGE and s_accu_state2 < ACCU_STATE_MAX:
            s_accu_state2 += 1
        elif s_charge_state2 == CHARGE_STATE_DISCHARGE and s_accu_state2 > ACCU_STATE_MIN:
            s_accu_state2 -= 1
        yield WaitForRelativeTime(1)
    print("accu2 stopped")
    return None

# Task for accu 3.
def accu3():
    global s_accu_state3, s_charge_state3
    print("accu3 started")
    s_accu_state3 = ACCU_STATE_MIN
    s_charge_state3 = CHARGE_STATE_DISCHARGE
    while s_accu_state3 != None:
        if s_charge_state3 == CHARGE_STATE_CHARGE and s_accu_state3 < ACCU_STATE_MAX:
            s_accu_state3 += 1
        elif s_charge_state3 == CHARGE_STATE_DISCHARGE and s_accu_state3 > ACCU_STATE_MIN:
            s_accu_state3 -= 1
        yield WaitForRelativeTime(1)
    print("accu3 stopped")
    return None

# Task for accu 4.
def accu4():
    global s_accu_state4, s_charge_state4
    print("accu4 started")
    s_accu_state4 = ACCU_STATE_MIN
    s_charge_state4 = CHARGE_STATE_DISCHARGE
    while s_accu_state4 != None:
        if s_charge_state4 == CHARGE_STATE_CHARGE and s_accu_state4 < ACCU_STATE_MAX:
            s_accu_state4 += 1
        elif s_charge_state4 == CHARGE_STATE_DISCHARGE and s_accu_state4 > ACCU_STATE_MIN:
            s_accu_state4 -= 1
        yield WaitForRelativeTime(1)
    print("accu4 stopped")
    return None

# Helper of accu printing.
def accu_bar(accu_state):
    bar_length = int(accu_state / 10)
    return (('#' * bar_length) + (' ' * (10 - bar_length)))

# Prints the state of all accus.
def print_accu_states():
    global s_accu_state1, s_accu_state2, s_accu_state3, s_accu_state4
    print("")
    print("   accu1        accu2        accu3        accu4")
    print("+----------  +----------  +----------  +----------")
    print("|" + accu_bar(s_accu_state1) + "  " +
          "|" + accu_bar(s_accu_state2) + "  " +
          "|" + accu_bar(s_accu_state3) + "  " +
          "|" + accu_bar(s_accu_state4))
    print("+----------  +----------  +----------  +----------")

# Handle the command line.
def handle(command_line):
    global s_running, s_charge_state1, s_charge_state2, s_charge_state3, s_charge_state4
    command_tokens = command_line.split()
    command = "".join(command_tokens[0:1]).upper()
    args = command_tokens[1:]
    arg1 = "".join(command_tokens[1:2])
    if command == "X" or command == "EXIT":
        s_running = False
    elif command == "?" or command == "HELP":
        print("X | EXIT ............... terminates the program")
        print("? | HELP ............... prints available commands")
        print("C | CHARGE <accu> ...... charge an accu 1-4")
        print("D | DISCHARGE <accu> ... discharge an accu 1-4")
        print_accu_states()
    elif command == "C" and arg1 == "1":
        print("charge accu1...")
        s_charge_state1 = CHARGE_STATE_CHARGE
    elif command == "D" and arg1 == "1":
        print("discharge accu1...")
        s_charge_state1 = CHARGE_STATE_DISCHARGE
    elif command == "C" and arg1 == "2":
        print("charge accu2...")
        s_charge_state2 = CHARGE_STATE_CHARGE
    elif command == "D" and arg1 == "2":
        print("discharge accu2...")
        s_charge_state2 = CHARGE_STATE_DISCHARGE
    elif command == "C" and arg1 == "3":
        print("charge accu3...")
        s_charge_state3 = CHARGE_STATE_CHARGE
    elif command == "D" and arg1 == "3":
        print("discharge accu3...")
        s_charge_state3 = CHARGE_STATE_DISCHARGE
    elif command == "C" and arg1 == "4":
        print("charge accu4...")
        s_charge_state4 = CHARGE_STATE_CHARGE
    elif command == "D" and arg1 == "4":
        print("discharge accu4...")
        s_charge_state4 = CHARGE_STATE_DISCHARGE
    # Show the prompt when True.
    return s_running

# Console task.
def console():
    global s_running, s_accu_state1, s_accu_state2, s_accu_state3, s_accu_state4
    print("console started")
    print_accu_states()
    console_handler = ConsoleHandler(handle)
    s_running = True
    while s_running:
        console_handler.poll()
        yield WaitForRelativeTime(0.1)
    s_accu_state1 = None
    s_accu_state2 = None
    s_accu_state3 = None
    s_accu_state4 = None
    print("console stopped")
    return None

event_loop = EventLoop()
event_loop.register_task(accu1(), "accu1")
event_loop.register_task(accu2(), "accu2")
event_loop.register_task(accu3(), "accu3")
event_loop.register_task(accu4(), "accu4")
event_loop.register_task(console(), "console")
event_loop.run(poll_time=0.01)
print("processing finished")