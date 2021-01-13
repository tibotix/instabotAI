import collections
from typing import Callable
import pickle_secure
import os

class AccountsDatabase(collections.deque):
  db_size = None

  def __init__(self, iterable=[], maxlen=None, auto_save=False):
    maxlen = (maxlen if(maxlen is not None) else self.db_size)
    super().__init__(iterable=iterable, maxlen=maxlen)
    self.task_creator = AccountsDatabaseTaskCreator(self)
    self.auto_save = auto_save

  def set_client(self, client):
    for item in self:
      item.client = client

  @property
  def free_space(self):
    if(self.maxlen is None):
      return None
    return self.maxlen - len(self)

  def append_from_stream(self, stream):
    for item in stream:
      print("Adding to {0}: {1}".format(str(self.db_name), str(item)))
      self.append(item)
    if(self.auto_save): self.save()

  def save(self, file_name=None):
    file_name = file_name if(file_name is not None) else self.db_path
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    with open(file_name, "wb") as f:
      pickle_secure.dump(self, f, self.encryption_key)
    print("Saved {0} to {1}".format(str(self.db_name), str(self.db_path)))

  @classmethod
  def from_file(cls, client, file_name=None, make_first=True, auto_save=False, maxlen=None):
    if(not os.path.isfile(cls.db_path) and make_first):
      return cls(maxlen=maxlen, auto_save=auto_save)
    print("creating {0} from file".format(str(cls.db_name)))
    file_name = file_name if(file_name is not None) else cls.db_path
    with open(file_name, "rb") as f:
      obj = pickle_secure.load(f, cls.encryption_key)
    obj.set_client(client)
    obj.auto_save = auto_save
    return obj




class InputDatabase(AccountsDatabase):
  db_size = 200
  db_name = "input_db"
  db_path = "db/input.instadb"
  encryption_key = "bf8d90988a95aba5b18d4118a0edba298bdeaee5d5b45f722cf7a22279381fc3"


class NotInterestedDatabase(AccountsDatabase):
  db_name = "not_interested_db"
  db_path = "db/not_interested.instadb"
  encryption_key = "b4df57c967b1417bac947e5c072c2d60390c0c4fe80622f856bd53a0857e4b93"


class MutualFollowingDatabase(AccountsDatabase):
  db_name = "mutual_following_db"
  db_path = "db/mutual_following.instadb"
  encryption_key = "e159972b505d3819347f7fd219a4200ba0e1b29b19a17b9857f976f57598476c"



class AccountsDatabaseLimitCalculator():
  def __init__(self, db: AccountsDatabase):
      self.db = db
      self.relative_count = 0

  def from_free_space(self):
    self.relative_count = self.db.free_space
    return self

  def from_filled_space(self):
    self.relative_count = len(self.db)
    return self

  def from_db_size(self):
    self.relative_count = self.db.maxlen
    return self

  def percentage(self, percentage: float):
    return int(self.relative_count * percentage)

  def number(self, number: int):
    if(number > self.relative_count):
      raise ValueError("Number cannot be greater than relative_count: {0}".format(str(self.relative_count)))
    return int(number)



class AccountsDatabaseTaskCreator():
  def __init__(self, database: AccountsDatabase):
    self.db = database

  def new_task_by_free_space_percentage(self, percentage: float, lifo: bool=True):
    acc_count = int(self.db.free_space * percentage)
    return AccountsDatabaseTaskExecutor(self.db, acc_count, lifo=lifo)

  def new_task_by_count(self, acc_count: int, lifo: bool=True):
    return AccountsDatabaseTaskExecutor(self.db, acc_count, lifo=lifo)

  def new_task_by_filled_space_percentage(self, percentage: float, lifo: bool=True):
    acc_count = int(len(self.db) * percentage)
    return AccountsDatabaseTaskExecutor(self.db, acc_count, lifo=lifo)


class AccountsDatabaseTaskExecutor():
  def __init__(self, database: AccountsDatabase, acc_count: int, lifo: bool=True):
    self.db = database
    self.acc_count = acc_count
    self.lifo = lifo

  def stream_accounts_to_execute(self):
    print("self.acc_count = {0}".format(str(self.acc_count)))
    for i in range(self.acc_count):
      try:
        yield (self.db.popleft() if(self.lifo) else self.db.pop())
      except IndexError as e:
        print("Index error")
        break


  def execute(self, callback: Callable, *args, **kwargs):
    for acc in self.stream_accounts_to_execute():
      print("calling callback...")
      callback(acc, *args, **kwargs)
