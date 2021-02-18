import os
import typing
from instabotAI.accounts_database import AccountsDatabaseLimitCalculator
from instabotAI import account_filterer, file_adapter
from instabotAI.instabot import InstaBotAI
import instabotAI

from instauto.api.client import ApiClient
from instauto.bot import *

import argparse
import pathlib
import colorama
import termcolor
import sys
import configargparse

import logging


logo = """
 __                        __                __                    __       ______   ______ 
/  |                      /  |              /  |                  /  |     /      \ /      |
##/  _______    _______  _## |_     ______  ## |____    ______   _## |_   /######  |######/ 
/  |/       \  /       |/ ##   |   /      \ ##      \  /      \ / ##   |  ## |__## |  ## |  
## |#######  |/#######/ ######/    ######  |#######  |/######  |######/   ##    ## |  ## |  
## |## |  ## |##      \   ## | __  /    ## |## |  ## |## |  ## |  ## | __ ######## |  ## |  
## |## |  ## | ######  |  ## |/  |/####### |## |__## |## \__## |  ## |/  |## |  ## | _## |_ 
## |## |  ## |/     ##/   ##  ##/ ##    ## |##    ##/ ##    ##/   ##  ##/ ## |  ## |/ ##   |
##/ ##/   ##/ #######/     ####/   #######/ #######/   ######/     ####/  ##/   ##/ ######/ 

author: @Tibotix (https://github.com/tibotix)
credits: @stanvanrooy (https://github.com/stanvanrooy)
_______________________________________________________________________________________________
"""


epilog = """
For more information please see manpage \"instabotAI\".
"""

class CustomFormatter(argparse.RawTextHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
  def __init__(self, prog: typing.Text, indent_increment: int=2, max_help_position: int=24, width: typing.Optional[int]=None) -> None:
    super().__init__(prog, indent_increment=indent_increment, max_help_position=50, width=width)

parser = configargparse.ArgParser(usage="python3 %(prog)s [options]", epilog=epilog, formatter_class=CustomFormatter, default_config_files=["~/.instabotAI/config/config", "./config/config"])
api_group = parser.add_argument_group("API", "Instagram API relevant Options.")
api_group.add_argument("-c", "--config-file", is_config_file=True, help="Optional Configuration File.", env_var="IAI_CONFIG_FILE")
api_group.add_argument("--client-file", type=pathlib.Path, help="Instauto ApiClient file. It usually starts with a \".\"\nUsed to avoid relogin", env_var="IAI_CLIENT_FILE")
api_group.add_argument("-u", "--username", type=str, help="Username used when logging in to Instagram.")
api_group.add_argument("-p", "--password", type=str, help="Password used when logging in to Instagram.")
api_group.add_argument("--force-login", action="store_true", help="Force login with username and password.")

general_group = parser.add_argument_group("General", "General instabotAI Options")
general_group.add_argument("--delay", type=float, default=45, help="Delay in seconds between calls to instagram.", env_var="IAI_DELAY")
general_group.add_argument("--delay-variance", type=float, default=5, help="Variance in seconds to randomize delay. Delay will be between (delay-delay_variance) and (delay+delay_variance).", env_var="IAI_DELAY_VARIANCE")
general_group.add_argument("-v", action="count", default=0, help="Verbosity level: specify more flags to get more verbosity.")
#TODO: LOGGING

db_group = parser.add_argument_group("Database", "Database relevant Options")
db_group.add_argument("-a", "--auto-save", action="store_true", help="Automatically save databases on each new input.", env_var="IAI_AUTO_SAVE")
db_group.add_argument("--input-db-size", type=int, default=None, help="Maximum size of input_db.", env_var="IAI_INPUTDB_SIZE")
db_group.add_argument("--mutual-db-size", type=int, default=None, help="Maximum size of mutual_db.", env_var="IAI_MUTUALDB_SIZE")
db_group.add_argument("--not-interested-db-size", type=int, default=None, help="Maximum size of not_interested_db.", env_var="IAI_NOTINTERESTEDDB_SIZE")

find_accounts_group = parser.add_argument_group("Find Accounts Stage", "Options relevant for the Find Same Accounts Stage.")
find_accounts_group.add_argument("-f", "--find", action="store_true", help="Enable this stage.")
find_accounts_group.add_argument("-s", "--search-filter", action="append", type=int, nargs=2, help="Mark only accounts with [more followers than, less followings than] as valid accounts.")
find_accounts_group.add_argument("--usernames-search-file", type=pathlib.Path, default="config/usernames.txt", help="File with accounts that will be scanned during this stage.", env_var="IAI_USERNAMES_FILE")
find_accounts_group.add_argument("--hashtags-search-file", type=pathlib.Path, default="config/hashtags.txt", help="File with hashtags that will be scanned during this stage.", env_var="IAI_HASHTAGS_FILE")
find_accounts_group.add_argument("--no-usernames-search", action="store_true", help="Exclude usernames search.")
find_accounts_group.add_argument("--no-hashtags-search", action="store_true", help="Exclude hashtags search.")
find_accounts_group.add_argument("--usernames-search-percentage", type=float, default=0.25, help="Amount of Accounts to add from the username search to the input_db based on percentage of free space in input_db.", env_var="IAI_USERNAMES_SEARCH_PERCENTAGE")
find_accounts_group.add_argument("--hashtags-search-percentage", type=float, default=0.75, help="Amount of Accounts to add from the hashtags search to the input_db based on percentage of free space in imput_db.", env_var="IAI_HASHTAGS_SEARCH_PERCENTAGE")

categorize_accounts_group = parser.add_argument_group("Categorize Accounts Stage", "Options relevant for the Categorize Accounts Stage.")
categorize_accounts_group.add_argument("-g", "--categorize", action="store_true", help="Enable this stage.")
categorize_accounts_group.add_argument("--scan-limit", type=int, default=None, help="How many own followings to scan maximum. Defaulting to ALL.", env_var="IAI_SCAN_LIMIT")
categorize_accounts_group.add_argument("--unfollow-blacklist-file", type=pathlib.Path, default="config/unfollow_blacklist.txt", help="Optional File with accounts excluded from unfollowing.", env_var="IAI_UNFOLLOW_BLACKLIST_FILE")
categorize_accounts_group.add_argument("--reverse-following-count", type=int, default=100, help="How many followings to trace back before deciding wether account is following back or not.", env_var="IAI_REVERSE_FOLLOWING_COUNT")

unfollow_accounts_group = parser.add_argument_group("Unfollow Accounts Stage", "Options relevant for the Unfollow Accounts Stage.")
unfollow_accounts_group.add_argument("-w", "--unfollow", action="store_true", help="Enable this stage.")
unfollow_accounts_group.add_argument("--mutual-unfollow-percentage", type=float, default=0.03, help="Percentage of current accounts in mutual_db that will be unfollowed.", env_var="IAI_MUTUAL_UNFOLLOW")
unfollow_accounts_group.add_argument("--not-interested-unfollow-percentage", type=float, default=0.05, help="Percentage of current accounts in not_interested_db that will be unfollowed.",env_var="IAI_NOTINTERESTED_UNFOLLOW")

rehabilitate_accounts_group = parser.add_argument_group("Rehabilitate Accounts Stage", "Options relevant for the Rehabilitate Accounts Stage.")
rehabilitate_accounts_group.add_argument("-r", "--rehabilitate", action="store_true", help="Enable this stage.")
rehabilitate_accounts_group.add_argument("--min-likes", type=int, default=2, help="Minimum posts that are liked per acount.", env_var="IAI_REHAB_MIN_LIKES")
rehabilitate_accounts_group.add_argument("--max-likes", type=int, default=3, help="Maximum posts that are liked per account.", env_var="IAI_REHAB_MAX_LIKES")
rehabilitate_accounts_group.add_argument("--rehabilitate-percentage", type=float, default=0.25, help="Percentage of current accounts in not_interested_db that will be rehabilitated.",env_var="IAI_REHAB_PERCENTAGE")

follow_accounts_group = parser.add_argument_group("Follow Accounts Stage", "Options relevant for the Follow Accounts Stage.")
follow_accounts_group.add_argument("-n", "--follow", action="store_true", help="Enable this stage.")
follow_accounts_group.add_argument("--scan-count", type=int, default=1, help="Number of scanned accounts in the input_db.", env_var="IAI_FOLLOW_SCAN_COUNT")
follow_accounts_group.add_argument("--bot-input-followers", type=int, default=100, help="Number of Followers of the scanned accounts that are processed.", env_var="IAI_FOLLOW_FOLLOWERS")
follow_accounts_group.add_argument("--bot-input-likers", type=int, default=200, help="Number of Likers of the scanned accounts that are processed.", env_var="IAI_FOLLOW_LIKERS")
follow_accounts_group.add_argument("--bot-input-commenters", type=int, default=200, help="Number of Commenters of the scanned accounts that are processed.",env_var="IAI_FOLLOW_COMMENTERS")
follow_accounts_group.add_argument("--max-likes-per-user", type=int, help="Maximum likes an account can get.", env_var="IAI_FOLLOW_MAX_LIKES")
follow_accounts_group.add_argument("--like-chance", type=float, default=0.35, help="Chance in percentage to like posts of a new account.", env_var="IAI_FOLLOW_LIKE_CHANCE")
follow_accounts_group.add_argument("--follow-chance", type=float, default=0.02, help="Chance in percentage to follow a new account to following.", env_var="IAI_FOLLOW_FOLLOW_CHANCE")


def get_client(args):
  if(args.force_login):
    if(args.username is not None and args.password is not None):
      return ApiClient(args.username, args.password)
    parser.error("--username and --password have to be specified when using --force_login!")
  if(args.client_file):
    return initiate_client_from_file(args.client_file)
  elif(args.username is not None):
    client_file = "./.{0}.instauto.save".format(str(args.username))
    if(os.path.exists(client_file)):
      return initiate_client_from_file(client_file, exit_on_error=False)
  elif(args.username is not None and args.password is not None):
    return ApiClient(args.username, args.password) 
  else:
    parser.error("either client_file or api credentials must be given.\nSee -h for more information.")

def initiate_client_from_file(filename, exit_on_error=True):
  try:
    return ApiClient.initiate_from_file(filename)
  except Exception as e:
    print(termcolor.colored("[!] Could not initiating ApiClient from file {0} : {1}".format(str(filename), str(e)), "magenta"))
    if(exit_on_error):
      sys.exit(2)
 
def get_instabot(args, client):
  return InstaBotAI(client, delay_between_actions=args.delay, delay_tolerance=args.delay_variance)

def get_find_same_accounts_stage(args, client, input_db):
  find_same_account_stage = instabotAI.stages.FindSameAccountsStage(input_db)

  if(not args.no_hashtags_search):
    hashtags_files_input = file_adapter.FilesInputStream()
    hashtags_files_input.add_file(args.hashtags_search_file)
    hashtags_account_finder = instabotAI.account_finder.HashtagsAccountFinder(hashtags_files_input, client)
    for f in args.search_filter:
      hashtags_account_finder.add_filterer(account_filterer.AccountFilterer(*f))
    find_same_account_stage.add_account_finder(hashtags_account_finder, AccountsDatabaseLimitCalculator(input_db).from_free_space().percentage(args.hashtags_search_percentage))

  if(not args.no_usernames_search):
    usernames_files_input = file_adapter.FilesInputStream()
    usernames_files_input.add_file(args.usernames_search_file)
    usernames_account_finder = instabotAI.account_finder.ManualUsernamesAccountFinder(usernames_files_input, client)
    find_same_account_stage.add_account_finder(usernames_account_finder, AccountsDatabaseLimitCalculator(input_db).from_free_space().percentage(args.usernames_search_percentage))
  
  return find_same_account_stage


def get_categorize_accounts_stage(args, not_interested_db, mutual_db):
  unfollow_blacklist_file_input = file_adapter.FilesInputStream()
  unfollow_blacklist_file_input.add_file(args.unfollow_blacklist_file)
  return instabotAI.stages.CategorizeAccountsStage(not_interested_db, mutual_db, unfollow_blacklist_file_input, reverse_following_count=args.reverse_following_count, scan_limit=args.scan_limit)

def get_unfollow_accounts_stage(args, not_interested_db, mutual_db):
  return instabotAI.stages.UnfollowAccountsStage(not_interested_db, mutual_db, not_interested_unfollow_percentage=args.not_interested_unfollow_percentage, mutual_unfollow_percentage=args.mutual_unfollow_percentage)

def get_rehabilitate_accounts_stage(args, not_interested_db):
  return instabotAI.stages.RehabilitateAccountsStage(not_interested_db, min_likes=args.min_likes, max_likes=args.max_likes, rehabilitate_percentage=args.rehabilitate_percentage)

def get_follow_accounts_stage(args, input_db):
  def get_max_likes():
    if(args.max_likes_per_user is not None):
      return args.max_likes_per_user
    print(termcolor.colored("[!] Max likes per user is not specified! Falling back to {0} likes".format(str(args.max_likes)), "magenta"))
    return args.max_likes
  max_likes = get_max_likes()
  return instabotAI.stages.LikeFollowNewAccountsStage(input_db, accounts_to_process=args.scan_count, bot_input_followers=args.bot_input_followers, bot_input_likers=args.bot_input_likers, bot_input_commenters=args.bot_input_commenters, max_likes_per_user=max_likes, like_chance=args.like_chance*100, follow_chance=args.follow_chance*100)


def main(args):
  if(args.hashtags_search_percentage+args.usernames_search_percentage > 1):
    parser.error("hashtags_search_percentage + usernames_search_percentage cannot be greater than 100%!")

  client = get_client(args)
  print(termcolor.colored("[*] Got ApiClient", "blue"))
  instabot = get_instabot(args, client)

  input_db = instabotAI.accounts_database.InputDatabase.from_file(client, auto_save=args.auto_save, maxlen=args.input_db_size)
  not_interested_db = instabotAI.accounts_database.NotInterestedDatabase.from_file(client, auto_save=args.auto_save, maxlen=args.not_interested_db_size)
  mutual_db = instabotAI.accounts_database.MutualFollowingDatabase.from_file(client, auto_save=args.auto_save, maxlen=args.mutual_db_size)
  print(termcolor.colored("[*] Got all DB", "blue"))

  if(args.find):
    stage = get_find_same_accounts_stage(args, client, input_db)
    instabot.add_stage(stage)
  if(args.categorize):
    stage = get_categorize_accounts_stage(args, not_interested_db, mutual_db)
    instabot.add_stage(stage)
  if(args.unfollow):
    stage = get_unfollow_accounts_stage(args, not_interested_db, mutual_db)
    instabot.add_stage(stage)
  if(args.rehabilitate):
    stage = get_rehabilitate_accounts_stage(args, not_interested_db)
    instabot.add_stage(stage)
  if(args.follow):
    stage = get_follow_accounts_stage(args, input_db)
    instabot.add_stage(stage)

  instabot.start()

  input_db.save()
  not_interested_db.save()
  mutual_db.save()


#client = ApiClient.initiate_from_file("./.itsmyvision.de.save")
#client.login()



if(__name__ == "__main__"):

#  loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
#  print(str(loggers))

  logger = logging.getLogger("instauto")
  logger.setLevel(logging.NOTSET)

  colorama.init()
  print(termcolor.colored(logo, "cyan"))
  
  args = parser.parse_args()

  try:
    main(args)
  except Exception as e:
    print(termcolor.colored("[-] {0}".format(str(e)), "red"))