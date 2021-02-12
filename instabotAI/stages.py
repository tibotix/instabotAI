from typing import *
from instauto.api.client import ApiClient
from instauto.bot import Bot
from instabotAI import action_delayer


from instabotAI.AccountInteractions.account_unfollower import AccountUnfollower
from instabotAI.AccountInteractions.account_liker import AccountLiker
from instabotAI.account import Account
from instabotAI.account_insigths import AccountInsigths
from instabotAI import file_adapter
from instabotAI import account_finder
from instabotAI.accounts_database import AccountsDatabase
from instabotAI.action_delayer import Delay


class Stage():
  def __init__(self):
    self.client = None

  def set_client(self, client: ApiClient):
    self.client = client

  def start(self):
    if(self.client is None):
      raise ValueError("ApiClient has to be initialized to start the stage")
    self._start()

  def finish(self):
    pass


class FindSameAccountsStage(Stage):
  def __init__(self, input_db: AccountsDatabase):
    super().__init__()
    self.input_db = input_db
    self.account_finders = list()

  def add_account_finder(self, account_finder: account_finder.AccountFinder, limit: int, raise_on_limit_overflow: bool=True):
    self._check_limits_with_limit(limit, raise_on_limit_overflow)
    self.account_finders.append((account_finder, limit))

  def _check_limits_with_limit(self, limit, raise_on_limit_overflow):
    limits_sum = sum([l for a,l in self.account_finders])
    if(limits_sum + limit > self.input_db.free_space):
      if(raise_on_limit_overflow):
        raise ValueError("Limit overflows free db space")
      print("WARNING: Limits will overflow free space on db resulting in rotating entries!") # TODO: Logging

  def _start(self):
    for account_finder, limit in self.account_finders:
      self.input_db.append_from_stream(account_finder.find_accounts_stream(limit=limit))


class CategorizeAccountsStage(Stage):
  def __init__(self, not_interested_db: AccountsDatabase, mutual_db: AccountsDatabase, unfollow_blacklist_file_input: file_adapter.FilesInputStream, reverse_following_count: Optional[int]=None, scan_limit: Optional[int]=None):
    super().__init__()
    self.not_interested_db = not_interested_db
    self.mutual_db = mutual_db
    self.unfollow_blacklist_file_input = unfollow_blacklist_file_input
    self.reverse_following_count = reverse_following_count
    self.scan_limit = scan_limit

  def _start(self):
    account_insigth = AccountInsigths(self.client, self.client.own_acc)
    account_insigth.analyze_insights(self.reverse_following_count, limit=self.scan_limit)
    not_interested_accounts = account_insigth.filter_dont_follow_back()
    mutual_friendships_accounts = account_insigth.filter_mutual_friendship()
    self.not_interested_db.append_from_stream(self._filter_blacklisted_accounts_stream(not_interested_accounts))
    self.mutual_db.append_from_stream(self._filter_blacklisted_accounts_stream(mutual_friendships_accounts))

  def _filter_blacklisted_accounts_stream(self, accounts: Iterable[Account]) -> Iterable[Account]:
    return filter(lambda acc:acc.username not in list(self.unfollow_blacklist_file_input.get_lines()), accounts)


class UnfollowAccountsStage(Stage):
  def __init__(self, not_interested_db: AccountsDatabase, mutual_db: AccountsDatabase, not_interested_unfollow_percentage: float=0.1, mutual_unfollow_percentage: float=0.05):
    super().__init__()
    self.not_interested_db = not_interested_db
    self.mutual_db = mutual_db
    self.mutual_unfollow_percentage = mutual_unfollow_percentage
    self.not_interested_unfollow_percentage = not_interested_unfollow_percentage

  def _start(self):
    unfollow_not_interested_task = self.not_interested_db.task_creator.new_task_by_filled_space_percentage(self.not_interested_unfollow_percentage)
    unfollow_mutual_task = self.mutual_db.task_creator.new_task_by_filled_space_percentage(self.mutual_unfollow_percentage)
    unfollow_not_interested_task.execute(self._unfollow_account)
    unfollow_mutual_task.execute(self._unfollow_account)

  def _unfollow_account(self, acc):
    AccountUnfollower(self.client, acc).interact()


class RehabilitateAccountsStage(Stage):
  def __init__(self, not_interested_db: AccountsDatabase, min_likes: int=2, max_likes: int=3, rehabilitate_percentage: float=0.2):
    super().__init__()
    self.min_likes = min_likes
    self.max_likes = max_likes
    self.not_interested_db = not_interested_db
    self.rehabilitate_percentage = rehabilitate_percentage

  def _start(self):
    rehabilitate_task = self.not_interested_db.task_creator.new_task_by_filled_space_percentage(self.rehabilitate_percentage)
    rehabilitate_task.execute(self._rehabilitate_account)

  def _rehabilitate_account(self, acc):
    AccountLiker(self.client, acc).interact(self.min_likes, self.max_likes)



class LikeFollowNewAccountsStage(Stage):
  def __init__(self, input_db: AccountsDatabase, accounts_to_process: int=1, bot_input_followers: int=100, bot_input_likers: int=200, bot_input_commenters: int=200, max_likes_per_user: int=3, like_chance: int=35, follow_chance: int=2):
    super().__init__()
    self.bot_input_followers = bot_input_followers
    self.bot_input_likers = bot_input_likers
    self.bot_input_commenters = bot_input_commenters
    self.max_likes_per_user = max_likes_per_user
    self.like_chance = like_chance
    self.follow_chance = follow_chance
    self.input_db = input_db
    self.accounts_to_process = accounts_to_process
    self._initialize_bot()

  def _initialize_bot(self):
    self.bot = Bot.from_client(self.client, delay_between_action=action_delayer.delay_in_seconds, delay_variance=action_delayer.delay_tolerance)

  def _start(self):
    set_bot_input_task = self.input_db.task_creator.new_task_by_count(self.accounts_to_process)
    set_bot_input_task.execute(self._set_bot_input)
    self._configure_bot()
    self.bot.start()

  def _set_bot_input(self, acc):
    print("configure bot input based on acc: {0}".format(str(acc.username)))
    self.bot.input.from_followers_of(acc.username, self.bot_input_followers)
    self.bot.input.from_likers_of(acc.username, self.bot_input_likers)
    self.bot.input.from_commenters_of(acc.username, self.bot_input_commenters)

  def _configure_bot(self):
    self.bot.like(self.like_chance, self.max_likes_per_user)
    self.bot.follow(self.follow_chance)