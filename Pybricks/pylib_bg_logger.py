#******************************************************************************
# Logger for background tasks.                                                *
#******************************************************************************


class Logger:

    def __init__(self, command_handler=None):
        self.log_buffer = []

    # Enter a log message into the log buffer.
    def log(self, message):
        self.log_buffer.append(message)

    # Cleans all log messages.
    def clean_log_messages(self):
        self.log_buffer = []

    # Retrieves all log messages.
    def get_log_messages(self):
        return self.log_buffer

    # Retrieves all log messages and cleans the log buffer.
    def get_log_messages_and_clean(self):
        messages = self.log_buffer
        self.log_buffer = []
        return messages

    # Prints all log messages.
    def print_log_messages(self):
        for message in messages:
            print(message)

    # Prints all log messages and cleans the log buffer.
    def print_log_messages_and_clean(self):
        for message in self.log_buffer:
            print(message)
        self.log_buffer = []