from instabotAI.action_delayer import ActionDelayer
from typing import *
from instauto.helpers.post import retrieve_posts_from_tag
from instauto.api.client import ApiClient
import random

from instabotAI import account
from instabotAI.account_filterer import AccountFilterer


class AccountFinder():
  def __init__(self, client: ApiClient, friendships_search_count: account.FriendshipsSearchCount=None):
    self.client = client
    self.friendships_search_count = friendships_search_count
    self.filters = list()
    self.found_accounts = 0

  def add_filterer(self, account_filterer: AccountFilterer):
    self.filters.append(account_filterer)

  def find_accounts_stream(self, limit: Optional[int]=None, batch_size: int=200) -> Iterable[account.Account]:
    print("Finding {0} new accounts...".format(str(limit)))
    self.found_accounts = 0
    while(limit is None or self.found_accounts < limit):
      print("{0} accounts already found...".format(str(self.found_accounts)))
      results_limit = (limit - self.found_accounts) if(limit is not None) else batch_size
      yield from self._populate_filtered_accounts(results_limit)

  def _populate_filtered_accounts(self, results_limit: int) -> Iterable[account.Account]:
    results_stream = self._populate_accounts_stream(results_limit)
    yield from self._filter_accounts_stream(results_stream)

  def _filter_accounts_stream(self, accounts: Iterator[account.Account]) -> Iterable[account.Account]:
    for acc in accounts:
      if(self._is_valid_account(acc)):
        self.found_accounts += 1
        print("Found valid acc: {0}".format(str(acc)))
        yield acc

  def _is_valid_account(self, acc: account.Account):
    if(len(self.filters) == 0): return True
    for filterer in self.filters:
      if(filterer.is_valid_account(acc)):
        return True
    return False

  def _populate_accounts_stream(self, results_limit: int) -> Iterator[account.Account]:
    raise NotImplementedError()



class ManualUsernamesAccountFinder(AccountFinder):
  def __init__(self, files_input, client, friendships_search_count=None):
    super().__init__(client, friendships_search_count=friendships_search_count)
    self.files_input = files_input

  def _populate_accounts_stream(self, results_limits) -> Iterator[account.Account]:
    for username in self.files_input.get_randomized_lines(limit=results_limits):
      try:
        acc = account.Account.from_username(self.client, username, friendships_search_count=self.friendships_search_count)
        yield acc
      except Exception as e:
        print("Exception : {0}".format(str(e)))


class HashtagsAccountFinder(AccountFinder):
  def __init__(self, files_input, client, friendships_search_count=None):
    super().__init__(client, friendships_search_count=friendships_search_count)
    self.files_input = files_input

  @ActionDelayer
  def _populate_accounts_stream(self, results_limit) -> Iterator[account.Account]:
    random_tag = self.files_input.get_random_line()
    hashtags_count = random.randint(1, results_limit)
    posts = retrieve_posts_from_tag(self.client, random_tag, hashtags_count)
    yield from self._convert_to_accounts_stream(posts)

  def _convert_to_accounts_stream(self, posts):
    for post in posts:
      try:
        yield account.Account.from_hashtag_post(self.client, post, friendships_search_count=self.friendships_search_count)
      except Exception as e:
        print("Exception: {0}".format(str(e)))

