#******************************************************************************
# Console handler for command processing.                                     *
#******************************************************************************
from uselect import poll
from usys import stdin

# Prompt to inform the PC that a new command can be processed.
PROMPT = ">>> "


class ConsoleHandler:

    def __init__(self, command_handler=None):
        self.command_buffer = ""
        if command_handler == None:
            self.command_handler = self
        else:
            self.command_handler = command_handler
        # Register stdin for polling. This allows to wait for incoming data
        # without blocking.
        self.keyboard = poll()
        self.keyboard.register(stdin)
        # Let the remote program know we are ready for a command.
        print(PROMPT, end="")

    # Fetch input from the PC.
    def poll(self):
        if self.keyboard.poll(0):
            # Data have been received from the PC: Read next character.
            next_char = str(stdin.buffer.read(1), "utf-8")
            if next_char == "\r":
                print("")
                if self.command_handler.handle(self.command_buffer):
                    # Let the remote program know we are ready for a command.
                    print(PROMPT, end="")
                self.command_buffer = ""
            else:
                print(next_char, end="")
                self.command_buffer += next_char

    # Handle the command - default implementation.
    def handle(self, command):
        if command != "":
            print("command = " + command)
        # Show the prompt when True.
        return True