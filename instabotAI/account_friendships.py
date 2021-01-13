from typing import *
import collections.abc


class AccountFriendshipsStorage(list):
  def __init__(self, acc):
    super().__init__()
    self.acc = acc

  def __getitem__(self, index):
    return super().__getitem__(index)

  def __getstate__(self):
    state = self.__dict__.copy()
    del state["acc"]
    return state

  def __setstate__(self, state):
    state["acc"] = None
    self.__dict__.update(state)

  def stream_friendships(self, limit: int):
    if(len(self) < limit):
      print("extending friendships to {0}".format(str(limit)))
      yield from self._extend_friendships_and_stream(limit)
    else:
      yield from self[:min(len(self), limit)]
  
  def _extend_friendships_and_stream(self, new_limit: int, batch_size: Optional[int]=200):
    batch_size = batch_size if(batch_size and batch_size<new_limit) else new_limit
    while(len(self) < new_limit):
      print("holding {0} friendships, {1} more to go.".format(str(len(self)), str(new_limit-len(self))))
      print("getting {0} more friendships..".format(str(batch_size)))
      new_friendships = self._collect_new_friendships(batch_size)
      if(len(new_friendships) == 0):
        break
      self.extend(new_friendships)
      yield from new_friendships
    print("extending friendships finished!")


class AccountsFollowingStorage(AccountFriendshipsStorage):
  def _collect_new_friendships(self, batch_size: int):
    return self.acc.collect_new_following(batch_size)

class AccountsFollowersStorage(AccountFriendshipsStorage):
  def _collect_new_friendships(self, batch_size: int):
    return self.acc.collect_new_followers(batch_size)
