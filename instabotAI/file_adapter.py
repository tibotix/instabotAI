import random
import functools
import os
import termcolor

class FileAdapter():
  def __init__(self, file_name):
    self.file_name = file_name

  @functools.lru_cache(maxsize=1)
  def readlines(self):
    lines = list()
    with open(self.file_name, "r") as f:
      lines = self._save_readlines(f)
    return lines

  def _save_readlines(self, file):
    try:
      return file.readlines()
    except IOError as e:
      print(termcolor.colored(f"Error while reading from {self.file_name}: {str(e)}", "magenta"))
      return list()

class FilesInputStream():
  def __init__(self):
    self.file_adapters = list()

  def add_file(self, file_name):
    if(not os.path.exists(file_name)):
      print(termcolor.colored(f"WARNING: Couldnt open {file_name}. File does not exists!", "magenta")) #TODO:Logging
    self.file_adapters.append(FileAdapter(file_name))

  def get_lines(self, limit=None):
    line_counter = 0
    for file_adapter in self.file_adapters:
      for line in file_adapter.readlines():
        if(limit is not None and line_counter>limit):
          break
        line_counter+=1
        yield line.replace('\n', '').strip()

  def get_randomized_lines(self, limit=None):
    lines = list(self.get_lines(limit=limit))
    random.shuffle(lines)
    for line in lines:
      yield line

  def get_random_line(self):
    lines = list(self.get_lines())
    index = random.randint(0, len(lines)-1)
    return lines[index]

  @functools.cached_property
  def lines_count(self):
    return len(list(self.get_lines()))