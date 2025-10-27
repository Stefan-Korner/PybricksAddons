#******************************************************************************
# Event loop and criterieas for asynchronous processing.                      *
#******************************************************************************
from pybricks.tools import StopWatch, wait

s_stop_watch = None


def time_sleep(sleep_time_sec):
    wait(sleep_time_sec * 1000)

def time_time():
    global s_stop_watch
    if s_stop_watch is None:
        s_stop_watch = StopWatch()
    return s_stop_watch.time() / 1000


class TimeoutException(Exception):

    def __init__(self, value):
        self.value = value


class WaitFor:

    def __init__(self):
        pass

    def test_event(self, event_loop):
        # (condition reached, return value)
        return (True, None)


class EventLoop:

    def __init__(self):
        self.tasks = []
        self.task_names = set()
        self.next_default_task_name = 0
        self.last_task_return_value = None

    def run(self, poll_time):
        while len(self.tasks) > 0:
            self.process_next_events()
            time_sleep(poll_time)

    def process_next_events(self):
        tasks_copy = self.tasks
        self.tasks = []
        for task_entry in tasks_copy:
            event_criteria, task, task_name = task_entry
            try:
                is_event, event_value = event_criteria.test_event(self)
                if is_event:
                    try:
                        # activate the task and obtain the next criteria
                        task_next_criteria = task.send(event_value)
                        self.register_task(task, task_name, task_next_criteria)
                    except StopIteration as ex:
                        # task finished, store the return value
                        self.save_task_return_value(task_name, ex.value)
                        # forget name and don't register it again
                        self.task_names.remove(task_name)
                else:
                    # task not activated, must be registered again
                    self.register_task(task, task_name, event_criteria)
            except Exception as criteria_exception:
                # there is an exception when checking the criteria
                try:
                    # send exception to the task and obtain the next criteria
                    task_next_criteria = task.throw(criteria_exception)
                    self.register_task(task, task_name, task_next_criteria)
                except StopIteration as ex:
                    # task finished, store the return value
                    self.save_task_return_value(task_name, ex.value)
                    # forget name and don't register it again
                    self.task_names.remove(task_name)

    def register_task(self, task, task_name=None, event_criteria=WaitFor()):
        if task_name == None:
            task_name = str(self.next_default_task_name)
            self.next_default_task_name += 1
        self.tasks.append((event_criteria, task, task_name))
        self.task_names.add(task_name)
        return task_name

    def task_exists(self, task_name):
        return (task_name in self.task_names)

    def save_task_return_value(self, task_name, task_return_value):
        self.last_task_return_value = task_return_value

    def task_return_value(self, task_name):
        return self.last_task_return_value


class WaitForAbsoluteTime(WaitFor):

    def __init__(self, absolute_time):
        super().__init__()
        self.absolute_time = absolute_time

    def test_event(self, event_loop):
        time_now = time_time()
        return (self.absolute_time <= time_now, time_now)


class WaitForRelativeTime(WaitForAbsoluteTime):

    def __init__(self, relative_time):
        super().__init__(time_time() + relative_time)


class WaitForTaskCompleted(WaitFor):

    def __init__(self, task_name, timeout=None):
        super().__init__()
        self.task_name = task_name
        self.timeout = timeout
        self.start_time = time_time()

    def test_event(self, event_loop):
        if event_loop.task_exists(self.task_name):
            # task is still running, check the timeout
            if self.timeout is not None:
                wait_time = time_time() - self.start_time
                if wait_time >= self.timeout:
                    raise TimeoutException(wait_time)
            # still have to wait
            return (False, None)
        # task has finished (or was never running)
        return (True, event_loop.task_return_value(self.task_name))