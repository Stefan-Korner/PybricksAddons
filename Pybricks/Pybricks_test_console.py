#------------------------------------------------------------------------------
# Tests the pylib_console.
#------------------------------------------------------------------------------
from pybricks.tools import wait
from pylib_console import ConsoleHandler


class TestConsoleHandler(ConsoleHandler):
    
    def __init__(self):
        print("The program was started.")
        super().__init__()
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            self.poll()
            wait(10)

    # Handle the command.
    def handle(self, command):
        upper_command = command.upper()
        if upper_command != "":
            print("command = " + command)
        if upper_command == "X" or upper_command == "EXIT":
            print("The program was stopped (Exit).")
            self.running = False
        elif upper_command == "?" or upper_command == "HELP":
            print("X | EXIT ... terminates the program")
            print("? | HELP ... prints available commands")
        # Show the prompt when True.
        return self.running


console_handler = TestConsoleHandler()
console_handler.run()