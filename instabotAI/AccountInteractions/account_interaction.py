from typing import *
from instauto.api.client import ApiClient

from instabotAI.action_delayer import ActionDelayer
from instabotAI.account import Account




class AccountInteraction():
  def __init__(self, client: ApiClient, acc: Account):
    self.client = client
    self.acc = acc

  @ActionDelayer
  def interact(self, *args, **kwargs):
    return self._interact(*args, **kwargs)

  def _interact(self, *args, **kwargs):
    raise NotImplementedError("")