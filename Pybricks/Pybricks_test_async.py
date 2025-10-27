#------------------------------------------------------------------------------
# Tests the pylib_async.
#------------------------------------------------------------------------------
import pylib_async


# foo1a --> foo1b --> foo1c
def foo1():
    print("foo1a")
    event_time = yield pylib_async.WaitForRelativeTime(3)
    print("foo1b, event_time =", event_time)
    event_time = yield pylib_async.WaitForRelativeTime(3)
    print("foo1c, event_time =", event_time)
    print("task foo1 finished")
    return 123


# foo2a --> foo2b --> foo2c
def foo2():
    print("foo2a")
    event_time = yield pylib_async.WaitForRelativeTime(1)
    print("foo2b, event_time =", event_time)
    try:
        return_value = yield pylib_async.WaitForTaskCompleted("foo1", 4)
        print("foo2c, return_value =", return_value)
    except pylib_async.TimeoutException as ex:
        print("foo2c, exception =", ex)
    print("task foo2 finished")
    return 456


# foo3a --> foo3b --> foo3c
def foo3():
    print("foo3a")
    event_time = yield pylib_async.WaitForRelativeTime(2)
    print("foo3b ,event_time =", event_time)
    try:
        return_value = yield pylib_async.WaitForTaskCompleted("foo2")
        print("foo3c, return_value =", return_value)
    except pylib_async.TimeoutException as ex:
        print("foo3c, exception =", ex)
    print("task foo3 finished")


event_loop = pylib_async.EventLoop()
event_loop.register_task(foo1(), "foo1")
event_loop.register_task(foo2(), "foo2")
event_loop.register_task(foo3(), "foo3")
event_loop.run(poll_time=0.1)
print("processing finished")