from typing import *
import random

from instabotAI.action_delayer import ActionDelayer
from instauto.helpers.post import *
from instabotAI.AccountInteractions import account_interaction



class AccountLiker(account_interaction.AccountInteraction):
  def _interact(self, min, max):
    count = self._get_like_count(min, max)
    print("liking {0} posts from {1} ...".format(str(count), str(self.acc.username)))
    for post in retrieve_posts_from_user(self.client, count, user_id=self.acc.user_id):
      if(post is not None):
        self._like_one_post(post["caption"]["media_id"])
  
  @ActionDelayer
  def _like_one_post(self, media_id: str):
    like_post(self.client, media_id)

  def _get_like_count(self, min, max):
    return random.randint(min, max)