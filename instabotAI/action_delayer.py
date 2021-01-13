from typing import *
import time
import random
import functools

delay_in_seconds = 10
delay_tolerance = 0


class Delay():
  @staticmethod
  def delay():
    sleeptime = Delay.get_sleeptime()
    print("sleep {0} seconds...".format(str(sleeptime)))
    time.sleep(sleeptime)
    print("awake!")

  @staticmethod
  def get_sleeptime():
    min = (delay_in_seconds - delay_tolerance) if(delay_in_seconds - delay_tolerance) else 0
    max = delay_in_seconds + delay_tolerance
    return round(random.uniform(min, max), 2)


class ActionDelayer():
  def __init__(self, func):
    self.func = func
    self.delay = Delay()

  def __get__(self, obj, objtype):
    return functools.partial(self.__call__, obj)

  def __call__(self, *args: Any, **kwargs: Any) -> Any:
    Delay.delay()
    return self.func(*args, **kwargs)
  