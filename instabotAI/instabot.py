from instabotAI.account import Account
from instabotAI import action_delayer
from typing import *
from instauto.api.client import ApiClient
from instauto.api.exceptions import StateExpired

from instabotAI import stages
import termcolor




class InstaBotAI():
  def __init__(self, client: ApiClient, delay_between_actions: float=20.0, delay_tolerance: float=10.0, friendships_search_count=None):
    self._set_delay_time(delay_between_actions, delay_tolerance)
    self.client = client
    self._check_client_state()
    self.friendships_search_count = friendships_search_count
    self.stages = list()

  def _set_delay_time(self, delay_between_actions: float, delay_tolerance: float):
    action_delayer.delay_in_seconds = delay_between_actions
    action_delayer.delay_tolerance = delay_tolerance #TODO: maybe better solution

  def _check_client_state(self):
    if(not hasattr(self.client, "state") or not self.client.state.valid):
      raise StateExpired("Client is not valid anymore. Please relogin!")

  def add_stage(self, stage: stages.Stage):
    self.stages.append(stage)

  def start(self):
    print(termcolor.colored("[+] Starting instabotAI", "green"))
    if(not self.stages):
      print(termcolor.colored("[!] No stages to process. Exiting...", "magenta"))
      return
    self._start()

  def _start(self):
    self.client.own_acc = Account.from_user_id(self.client, self.client.state.user_id, friendships_search_count=self.friendships_search_count)
    for stage in self.stages:
      stage.set_client(self.client)
      stage.start()
      stage.finish()
      self._save_client()

  def _save_client(self):
    self.client.save_to_disk("./.{0}.instauto.save".format(str(self.client.own_acc.username)), over_write=True)