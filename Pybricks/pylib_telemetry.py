#******************************************************************************
# Prints telemetry parameters to the console.                                 *
#******************************************************************************

# Print telemetry parameters to the console. The printing is always in
# foreground. When the hub is connected to a remote program then the remote
# program must know the pattern for encoded telemetry parameters.
def print_telemetry_parameter(parameter_name, parameter_value):
    print("#" + parameter_name + "{" + parameter_value + "}", end="")