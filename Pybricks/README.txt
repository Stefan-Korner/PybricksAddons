This folder contains the software for on LEGO Hubs with Pybricks.

Libraries:
==========

pylib_async.py
--------------

Contains the class EventLoop that shall be used for asynchronous processing.
It supports cooperative running tasks (functions) that give control to the
EventLoop via yield calls. In addition this library provides the generic
condition WaitFor and the specific conditions WaitForAbsoluteTime,
WaitForRelativeTime, WaitForTaskCompleted.

pylib_console.py
----------------

Contains the class ConsoleHandler that reads from stdin and interprets
commands. The class can either be derived to support additional custom
commands via the overloaded method handle(self, command) or an external
function handle(command) can be passed to the ctor of the class. The
ConsoleHandler provides a prompt ">>> " to support a synchonization for a
parent application. The class is designed to support a non-blocking reading
from stdin.

Programs:
=========

Pybricks_test_asynv.py
----------------------

Example usage of the EventLoop from the library pylib_async.py. This Example
has 3 cooperative running tasks and it uses the conditions WaitForRelativeTime
and WaitForTaskCompleted for timing and synchronizing.

Pybricks_test_console.py
------------------------

Example usage of the ConsoleHandler from the library pylib_concole.py. The
ConsoleHandler class is derived by the class TestConsoleHandler that provides
a simple poll event loop and an enhanced handle(...) method.
