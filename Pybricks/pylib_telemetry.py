#******************************************************************************
# Prints telemetry parameters to the console.                                 *
#******************************************************************************
s_telemetry_enabled = True

# Print telemetry parameters to the console. The printing is always in
# foreground. When the hub is connected to a remote program then the remote
# program must know the pattern for encoded telemetry parameters.
def print_telemetry_parameter(parameter_name, parameter_value):
    global s_telemetry_enabled
    if s_telemetry_enabled:
        print("#" + parameter_name + "{" + parameter_value + "}", end="")

# Enables telemetry printing.
def enable_telemetry():
    global s_telemetry_enabled
    s_telemetry_enabled = True

# Disables telemetry printing.
def disable_telemetry():
    global s_telemetry_enabled
    s_telemetry_enabled = False