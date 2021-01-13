from typing import *
from instauto.api.actions import friendships as fs

from instabotAI.AccountInteractions import account_interaction


class AccountUnfollower(account_interaction.AccountInteraction):
  def _interact(self, *args, **kwargs):
    print("unfollowing {0} ...".format(str(self.acc.username)))
    f = fs.Destroy(user_id=self.acc.user_id)
    self.client.user_unfollow(f)