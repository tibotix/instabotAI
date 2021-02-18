from typing import *
from instabotAI.account import Account

class AccountInsigths():
  def __init__(self, client, acc: Account):
    self.client = client
    self.acc = acc
    self.dont_follow_back = list()
    self.mutual_friendship = list()

  def analyze_insights(self, reverse_following_count: int=100, limit=None):
    print("analyzing insights for {0}".format(str(self.acc.username)))
    for following in self.acc.stream_following(limit=limit):
      if(self.is_followed_by_acc(following, reverse_following_count)):
        print("adding mutual friendship between {0} - {1}".format(str(following.username), str(self.acc.username)))
        self.mutual_friendship.append(following)
        continue
      print("adding dont follow back friendship between {0} - {1}".format(str(following.username), str(self.acc.username)))
      self.dont_follow_back.append(following)   

  def is_followed_by_acc(self, acc, reverse_following_count):
    return acc.is_following_acc(self.acc, reverse_following_count)

  def filter_dont_follow_back(self) -> List[Account]:
    return self.dont_follow_back

  def filter_mutual_friendship(self) -> List[Account]:
    return self.mutual_friendship

class OwnAccountInsigths(AccountInsigths):
  def is_followed_by_acc(self, acc, reverse_following_count):
    return acc.is_following_you

class AccountInsigthsFactory():
  @staticmethod
  def create_account_insight_class(client, acc):
    if(acc.user_id == client.own_acc.user_id):
      return OwnAccountInsigths(client, acc)
    return AccountInsigths(client, acc)