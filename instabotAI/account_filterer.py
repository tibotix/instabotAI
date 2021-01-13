from typing import *

from instabotAI import account





class AccountFilterer():
  def __init__(self, min_followers: int, max_followings: int):
      self.min_followers = min_followers
      self.max_followings = max_followings

  def filter_stream(self, accounts_stream: Iterator[account.Account]) -> Iterable[account.Account]:
    for account in filter(self.is_valid_account, accounts_stream):
      yield account

  def is_valid_account(self, acc: account.Account):
    return bool(len(acc.followers_list) >= self.min_followers and len(acc.following_list) <= self.max_followings)
