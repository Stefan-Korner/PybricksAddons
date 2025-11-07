#******************************************************************************
# Tests the pylib_console.                                                    *
#******************************************************************************
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

    # Handle the command line.
    def handle(self, command_line):
        command_tokens = command_line.split()
        command = "".join(command_tokens[0:1]).upper()
        args = command_tokens[1:]
        if command != "":
            print("command input =", command, " ".join(args))
        if command == "X" or command == "EXIT":
            print("The program was stopped (Exit).")
            self.running = False
        elif command == "?" or command == "HELP":
            print("X | EXIT ... terminates the program")
            print("? | HELP ... prints available commands")
        # Show the prompt when True.
        return self.running

console_handler = TestConsoleHandler()
console_handler.run()