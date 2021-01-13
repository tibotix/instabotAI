from instabotAI.accounts_database import AccountsDatabaseLimitCalculator
from instabotAI import account_filterer, file_adapter
from instabotAI.instabot import InstaBotAI
import instabotAI

from instauto.api.client import ApiClient
from instauto.bot import *

import argparse
import pathlib


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


description = """
This is an intelligent instagram Bot.
It uses 5 different stages to get you the most followers on Instagram.

Stage 1: Find Same Accounts
---------------------------
This stage tries to find accounts that does the same as you do.
So their audience fits the best in your also.
instabotAI currently supports 2 ways to find those accounts:
1. Given hashtags.
2. Given usernames
You can provide both inputs as files.

Stage 2: Categorize Accounts
----------------------------
This stage analyzes your own following / followers insight
and categorize accounts in 2 states:
1. Mutual Friendships: Meaning that you follow each other
2. Not interested Friendship: Meaning that you follow acc, but acc does not follow you
The categorized accounts are finally saved in our Database

Stage 3: Unfollow Accounts
--------------------------
This stage unfollows a particular subgroup of your
1. Mutual Friendships Database
2. Not interested Friendships Database
Unfoll these accounts has the advantage that you are keeping following count small,
which is important for new potential followers looking at your site

Stage 4: Rehabilitate Accounts
------------------------------
This stage tries to reactivate your attention on accounts that had maybe
forgotten you. It likes a specified random amount of posts of accounts in
the
1. Not interested Friendships Database

Stage 5: Follow new Accounts
----------------------------
This stage tries to reach new accounts by following and liking posts of them
hoping that they follow you back. It takes a specified amount of accounts in the
1. Input Database
and retrieving based on this account
1. a given amount of followers following that account
2. a given amount of likers that liked a post of that account
3. a given amount of commenters that commented a post of that account.
Given on that accounts list the bot
1. Likes with a specified possibility a specified random amount of posts 
2. Follows with a specified possibility accounts
\n\n\n
--------------------------------------------
"""

parser = argparse.ArgumentParser(usage="python3 %(prog)s [options]", description=description, formatter_class=argparse.RawDescriptionHelpFormatter)
api_group = parser.add_argument_group("API", "Instagram API relevant Options")
api_group.add_argument("-c", "--client_file", type=pathlib.Path)
api_group.add_argument("-u", "--username", type=str)
api_group.add_argument("-p", "--password", type=str)

general_group = parser.add_argument_group("General", "General instabotAI Options")
general_group.add_argument("-o", "--own_acc_friendships_search_count", type=int, nargs=2, default=[100, 20])
general_group.add_argument("-d", "--delay", type=float, default=45)
general_group.add_argument("-v", "--delay_variance", type=float, default=5)

db_group = parser.add_argument_group("Database", "Database relevant Options")
db_group.add_argument("-a", "--auto_save", action="store_true")
db_group.add_argument("--input_db_size", type=int, default=None)
db_group.add_argument("--mutual_db_size", type=int, default=None)
db_group.add_argument("--not_interested_db_size", type=int, default=None)

find_accounts_group = parser.add_argument_group("Find Accounts Stage", "Options relevant for the Find Same Accounts Stage")
find_accounts_group.add_argument("-f", "--find_accounts", action="store_true")
find_accounts_group.add_argument("-s", "--search_filter", action="append", type=int, nargs=2, )
find_accounts_group.add_argument("--usernames_search_file", type=pathlib.Path)
find_accounts_group.add_argument("--hashtags_search_file", type=pathlib.Path)
find_accounts_group.add_argument("--hashtags_search_percentage", type=float, default=0.75)
find_accounts_group.add_argument("--usernames_search_percentage", type=float, default=0.25)
find_accounts_group.add_argument("--usernames_friendships_search_count", type=int, nargs=2, default=[100, 200])
find_accounts_group.add_argument("--hashtags_friendships_search_count", type=int, nargs=2, default=[500, 1000])

categorize_accounts_group = parser.add_argument_group("Categorize Accounts Stage", "Options relevant for the Categorize Accounts Stage")
categorize_accounts_group.add_argument("-g", "--categorize_accounts", action="store_true")
categorize_accounts_group.add_argument("--unfollow_blacklist_file", type=pathlib.Path)
categorize_accounts_group.add_argument("--reverse_following_count", type=int, default=100)

unfollow_accounts_group = parser.add_argument_group("Unfollow Accounts Stage", "Options relevant for the Unfollow Accounts Stage")
unfollow_accounts_group.add_argument("-w", "--unfollow_accounts", action="store_true")
unfollow_accounts_group.add_argument("--mutual_unfollow_percentage", type=float, default=0.03)
unfollow_accounts_group.add_argument("--not_interested_unfollow_percentage", type=float, default=0.05)

rehabilitate_accounts_group = parser.add_argument_group("Rehabilitate Accounts Stage", "Options relevant for the Rehabilitate Accounts Stage")
rehabilitate_accounts_group.add_argument("-r", "--rehabilitate_accounts", action="store_true")
rehabilitate_accounts_group.add_argument("--min_likes", type=int, default=2)
rehabilitate_accounts_group.add_argument("--max_likes", type=int, default=3)
rehabilitate_accounts_group.add_argument("--rehabilitate_percentage", type=float, default=0.25)

follow_accounts_group = parser.add_argument_group("Follow Accounts Stage", "Options relevant for the Follow Accounts Stage")
follow_accounts_group.add_argument("-n", "--follow_accounts", "--new_accounts", action="store_true")
follow_accounts_group.add_argument("--accounts_to_process", type=int, default=1)
follow_accounts_group.add_argument("--bot_input_followers", type=int, default=100)
follow_accounts_group.add_argument("--bot_input_likers", type=int, default=200)
follow_accounts_group.add_argument("--bot_input_commenters", type=int, default=200)
follow_accounts_group.add_argument("--max_likes_per_user", type=int) #TODO
follow_accounts_group.add_argument("--like_chance", type=int, default=35)
follow_accounts_group.add_argument("--follow_chance", type=int, default=2)


def get_client(args):
  if(args.client_file):
    return ApiClient.initiate_from_file(args.client_file)
  elif(args.username is not None and args.password is not None):
    return ApiClient(args.username, args.password) 
  else:
    parser.error("either client_file or api credentials must be given.\nSee -h for more information.")

def get_instabot(args, client):
  friendships_search_count = instabotAI.account.FriendshipsSearchCount(*args.own_acc_friendships_search_count)
  return InstaBotAI(client, delay_between_actions=args.delay, delay_tolerance=args.delay_variance, friendships_search_count=friendships_search_count)

def get_find_same_accounts_stage(args, client):
  find_same_account_stage = instabotAI.stages.FindSameAccountsStage(input_db)

  if(args.hashtags_search_file):
    hashtags_files_input = file_adapter.FilesInputStream()
    hashtags_files_input.add_file(args.hashtags_search_file)
    hashtags_friendships_search_count = instabotAI.account.FriendshipsSearchCount(*args.hashtags_friendships_search_count)
    hashtags_account_finder = instabotAI.account_finder.HashtagsAccountFinder(hashtags_files_input, client, friendships_search_count=hashtags_friendships_search_count)
    for f in args.search_filterer:
      hashtags_account_finder.add_filterer(account_filterer.AccountFilterer(*f))
    find_same_account_stage.add_account_finder(hashtags_account_finder, AccountsDatabaseLimitCalculator(input_db).from_free_space().percentage(args.hashtags_search_percentage))

  if(args.usernames_search_file):
    usernames_files_input = file_adapter.FilesInputStream()
    usernames_files_input.add_file(args.usernames_search_file)
    usernames_friendships_search_count = instabotAI.account.FriendshipsSearchCount(*args.usernames_friendships_search_count)
    usernames_account_finder = instabotAI.account_finder.ManualUsernamesAccountFinder(usernames_files_input, client, friendships_search_count=usernames_friendships_search_count)
    find_same_account_stage.add_account_finder(usernames_account_finder, AccountsDatabaseLimitCalculator(input_db).from_free_space().percentage(args.usernames_search_percentage))
  
  return find_same_account_stage


def get_categorize_accounts_stage(args, not_interested_db, mutual_db):
  unfollow_blacklist_file_input = file_adapter.FilesInputStream()
  unfollow_blacklist_file_input.add_file(args.unfollow_blacklist_file)
  return instabotAI.stages.CategorizeAccountsStage(not_interested_db, mutual_db, unfollow_blacklist_file_input, reverse_following_count=args.reverse_following_count)

def get_unfollow_accounts_stage(args, not_interested_db, mutual_db):
  return instabotAI.stages.UnfollowAccountsStage(not_interested_db, mutual_db, not_interested_unfollow_percentage=args.not_interested_unfollow_percentage, mutual_unfollow_percentage=args.mutual_unfollow_percentage)

def get_rehabilitate_accounts_stage(args, not_interested_db):
  return instabotAI.stages.RehabilitateAccountsStage(not_interested_db, min_likes=args.min_likes, max_likes=args.max_likes, rehabilitate_percentage=args.rehabilitate_percentage)

def get_follow_accounts_stage(args, input_db):
  max_likes = args.max_likes_per_user if(args.max_likes_per_user is not None) else args.max_likes
  #maybe print value or info when falling back to max_likes
  return instabotAI.stages.LikeFollowNewAccountsStage(input_db, accounts_to_process=args.accounts_to_process, bot_input_followers=args.bot_input_followers, bot_input_likers=args.bot_input_likers, bot_input_commenters=args.bot_input_commenters, max_likes_per_user=max_likes, like_chance=args.like_chance, follow_chance=args.follow_chance)




if(__name__ == "__main__"):
  print(logo)
  args = parser.parse_args()

  if(args.hashtags_search_percentage+args.usernames_search_percentage != 1):
    parser.error("hashtags_search_percentage + usernames_search_percentage has to be 100%!")

  client = get_client(args)
  instabot = get_instabot(args, client)

  input_db = instabotAI.accounts_database.InputDatabase.from_file(client, auto_save=args.auto_save, maxlen=args.input_db_size)
  not_interested_db = instabotAI.accounts_database.NotInterestedDatabase.from_file(client, auto_save=args.auto_save, maxlen=args.not_interested_db_size)
  mutual_db = instabotAI.accounts_database.MutualFollowingDatabase.from_file(client, auto_save=args.auto_save, maxlen=args.mutual_db_size)

  if(args.find_accounts):
    stage = get_find_same_accounts_stage(args)
    instabot.add_stage(stage)
  if(args.categorize_accounts):
    stage = get_categorize_accounts_stage(args, not_interested_db, mutual_db)
    instabot.add_stage(stage)
  if(args.unfollow_accounts):
    stage = get_unfollow_accounts_stage(args, not_interested_db, mutual_db)
    instabot.add_stage(stage)
  if(args.rehabilitate_accounts):
    stage = get_rehabilitate_accounts_stage(args, not_interested_db)
    instabot.add_stage(stage)
  if(args.follow_accounts):
    stage = get_follow_accounts_stage(args, input_db)
    instabot.add_stage(stage)
  
  instabot.start()

  input_db.save()
  not_interested_db.save()
  mutual_db.save()

#client = ApiClient("itsmyvision.de", "d3lph1", testing=True)
#client = ApiClient.initiate_from_file("./.itsmyvision.de.save")
#client.login()

  
