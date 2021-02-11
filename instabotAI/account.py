from typing import *
import functools
from instabotAI.action_delayer import ActionDelayer
from instauto.helpers.friendships import get_followers, get_following
from instauto.api.actions.structs.profile import Info
from instauto.api.actions.friendships import Show

from instabotAI.account_friendships import *

class Account():
  def __init__(self, client, account_dict, friendships_search_count=None):
    self.client = client
    self.account_dict = account_dict
    self._check_valid_account_dict()
    self._create_friendship_status()
    self.friendships_search_count = (friendships_search_count if (friendships_search_count is not None) else FriendshipsSearchCount(5000, 5000))
    self.followers_storage = AccountsFollowersStorage(self)
    self.following_storage = AccountsFollowingStorage(self)

  def _create_friendship_status(self):
    if("friendships_status" not in self.account_dict):
      self.account_dict["friendships_status"] = dict()

  def _check_valid_account_dict(self):
    if(not isinstance(self.account_dict, dict)):
      raise TypeError("AccountDict has to be a dict, not {0}".format(str(type(self.account_dict))))

  def _extend_account_dict(self):
    self.account_dict.update(self.client.profile_info(Info(user_id=self.user_id)))

  def __str__(self):
    return "Account: {0}".format(str(self.username))

  def __getstate__(self):
    state = self.__dict__.copy()
    del state["client"]
    return state

  def __setstate__(self, state):
    state["client"] = None
    self.__dict__.update(state)
    self.followers_storage.acc = self
    self.following_storage.acc = self

  @property
  def user_id(self):
    return self.account_dict.get("pk", "")

  @functools.cached_property
  def username(self):
    print("Getting Username for user_id: {0}".format(str(self.user_id)))
    if("username" not in self.account_dict):
      self._extend_account_dict()
    return self.account_dict["username"]

  @functools.cached_property
  def follower_count(self):
    print("getting follower_count for {0}".format(str(self.username)))
    if("follower_count" not in self.account_dict):
      self._extend_account_dict()
    return self.account_dict["follower_count"]

  @functools.cached_property
  def following_count(self):
    print("getting following_count for {0}".format(str(self.username)))
    if("following_count" not in self.account_dict):
      self._extend_account_dict()
    return self.account_dict["following_count"]

  def stream_followers(self, limit=None):
    print("stream followers for {0}".format(str(self.username)))
    limit = limit if(limit is not None) else self.friendships_search_count.max_followers_to_retrieve
    yield from self.followers_storage.stream_friendships(limit)

  def stream_following(self, limit=None):
    print("stream following for {0}".format(str(self.username)))
    limit = limit if(limit is not None) else self.friendships_search_count.max_following_to_retrieve
    yield from self.following_storage.stream_friendships(limit)

  @functools.cached_property
  def is_follwing_you(self):
    if("followed_by" not in self.account_dict["friendship_status"]):
      self._extend_friendship_status()
    if("followed_by" not in self.account_dict["friendship_status"]):
      return self.is_following_acc(self.client.own_acc)
    return self.account_dict["friendship_status"]["followed_by"]

  @functools.cached_property
  def is_followed_by_you(self):
    if("following" not in self.account_dict["friendship_status"]):
      self._extend_friendship_status()
    if("following" not in self.account_dict["friendship_status"]):
      return self.is_followed_by_acc(self.client.own_acc)
    return self.account_dict["friendship_status"]["following"]

  @functools.lru_cache(maxsize=32)
  def is_following_acc(self, account, limit=None):
    for acc in self.stream_following(limit=limit):
      if(acc.user_id == account.user_id):
        return True
    return False
    
  @functools.lru_cache(maxsize=32)
  def is_followed_by_acc(self, account, limit=None):
    for acc in self.stream_followers(limit=limit):
      if(acc.user_id == account.user_id):
        return True
    return False

  @ActionDelayer
  def _extend_friendship_status(self):
    show = self.client.follower_show(Show(user_id=self.user_id))
    self.account_dict["friendship_status"].update(show)

  @ActionDelayer
  def collect_new_followers(self, count: int) -> List["Account"]:
    return [Account(self.client, account_dict, friendships_search_count=self.friendships_search_count) for account_dict in get_followers(self.client, self.user_id, count)]

  @ActionDelayer
  def collect_new_following(self, count: int) -> List["Account"]:
    return [Account(self.client, account_dict, friendships_search_count=self.friendships_search_count) for account_dict in get_following(self.client, self.user_id, count)]


  @classmethod
  @functools.lru_cache(maxsize=128)
  @ActionDelayer
  def from_username(cls, client, username, friendships_search_count=None):
    account_dict = client.profile_info(Info(username=username))
    return cls(client, account_dict, friendships_search_count=friendships_search_count)

  @classmethod
  @functools.lru_cache(maxsize=128)
  @ActionDelayer
  def from_user_id(cls, client, user_id, friendships_search_count=None):
    account_dict = client.profile_info(Info(user_id=user_id))
    return cls(client, account_dict, friendships_search_count=friendships_search_count)

  @classmethod
  @ActionDelayer
  def from_hashtag_post(cls, client, hashtag_post, friendships_search_count=None):
    account_dict = hashtag_post.get("user")
    return cls(client, account_dict, friendships_search_count=friendships_search_count)



class FriendshipsSearchCount():
  def __init__(self, max_followers_to_retrieve, max_following_to_retrieve):
      self.max_followers_to_retrieve = max(max_followers_to_retrieve, 0)
      self.max_following_to_retrieve = max(max_following_to_retrieve, 0)
