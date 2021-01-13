# Strategy for an Automated instagram Bot

<br>
<br>

## 1. Find Accounts who does the same as you
----------
### Input: 
- by hashtags (all left free space)
- by given usernames (randomized, max. 25% of free DB Entries)

### Filter:
- more than 5.000 Followers on hashtags results
- less than 5.000 Followings on hashtags results

### => store Accounts in "Input" DB to fill 200 DB Entries

<br>
<br>

## 2. Categorize Accounts
----------
### Input:
- by your own followings
- by your own follower
- blacklist

### Filter:
- #### Dont Follow you, but you following:
  - #### => store in "Not Interested" DB with blacklist filter
- #### Do Follow you, and you following
  - #### => store in "Mutual" DB with blacklist filter

<br>
<br>

## 3. Unfollow Accounts
----------
### Input:
- "Not Interested" DB
- "Mutual" DB

### Filter:
- Unfollow last 10% in "Not Interested" and remove them from DB
- Unfollow last 5% in "Mutual" and remove them from DB

<br>
<br>

## 4. Rehabilitate Accounts
----------
### Input:
- "Not Interested" DB

### Filter:
- Like random max. 3 posts of last 20% in "Not Interested"

<br>
<br>

## 5. Like and Follow new Accounts
----------
### Input:
- Last "Input" DB entry (pop it)
  - 100 Followers of it
  - 200 Likers of it
  - 200 Commenters of it

### Filter:
- Like max 3 posts with 35% chance
- Follow retrieved accounts with 2% chance

=> with 10-30 sec action delay -> ~3h
