#******************************************************************************
# Logger for background tasks.                                                *
#******************************************************************************
s_logger = None


# Convenience helper that delegates to the s_logger instance.
def bg_log(message):
    global s_logger
    s_logger.log(message)

# Convenience helper that delegates to the s_logger instance.
def clean_bg_log_messages():
    global s_logger
    s_logger.clean_log_messages()

# Convenience helper that delegates to the s_logger instance.
def get_bg_log_messages():
    global s_logger
    s_logger.get_log_messages()

# Convenience helper that delegates to the s_logger instance.
def get_bg_log_messages_and_clean():
    global s_logger
    s_logger.get_log_messages_and_clean()

# Convenience helper that delegates to the s_logger instance.
def print_bg_log_messages():
    global s_logger
    s_logger.print_log_messages()

# Convenience helper that delegates to the s_logger instance.
def print_bg_log_messages_and_clean():
    global s_logger
    s_logger.print_log_messages_and_clean()


# The bachgound logger instance.
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


# Logger initializer.
s_logger = Logger()