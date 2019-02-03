# ByeByeBots for Instagram
Unsubscribe Instagram accounts who follows to more than _N_ (e.g. 1500) accounts, because they are not only don't see your posts, but also reduce your stats.

## Long story short
Say goodbye to all Internet-shops, follow4follow, and automatically subscribed to you Instagram accounts.

## Long story long
In 2018, Instagram has changed the algorithm and there’s no question about it, Instagram posts are no longer getting the amount of exposure they used to. Now, it’s estimated that only **10%** of your audience is actually seeing your posts.
This can be extremely frustrating for users who aren’t seeing their friends and family’s posts, businesses hoping to reach new customers, and even worse for influencers whose business model depends on their followers seeing their content.

Since the original shift from a chronological feed, we’ve known the Instagram algorithm is mainly based on engagement. This includes number of likes, comments, video views, saves, shared posts, DM’s and any other type of interactions a post gets. More info in the [original post](https://later.com/blog/how-instagram-algorithm-works/).

Imagine you have 150 followers, and average amount of likes on your photos is 50. Having that, Instagram thinks that your posts are interested to only 33% of your followers. Then imagine that 50 of your 150 followers are not real people - bussines accounts, Internet-shops etc. Those accounts are only interested in you seeing them, they are not insterested in your life or posts - we can easily unsubscribe them from us. Thus, you'll have 100 followers and your 50 likes becomes 50% instead of 33%! This will give the instagram a sign that your posts engage more people in activity, and it will more recommend your account for viewing to other people.

## Logic
The tool combines both BeautifulSoup response parsing and unofficial Instagram API developed by [LevPasha](https://github.com/LevPasha/Instagram-API-python). This hepls to reduce number of [429 HTTP responces](https://stackoverflow.com/questions/49606300/instagram-api-request-limit-max-200-only-2018-april) during processing.

To detect who is bot and who's not is pretty complicated nowaday, often bots put a few random likes or comments, to simulate users activity. We can suppose that if account is subscribed to 1500+ accounts - it's a bot-like. With new Instagram alghoritm, this account will see only the top-rated post, and if your are not super star, your posts most probably won't even shown to them. 

The logic is straighforward:
1. Get accounts subscribed to you
2. Take away accounts to which you are subscribed
3. Unsubscribe from you accounts with more than _N_ subscriptions

## Installation
The tool requires Python 3.7.x. To install the package from PyPi run:
```
pip3 install byebyebots
```

Alternatively, you can install it from source:
```
git clone git@github.com:VikGit/byebyebots-instagram.git
cd byebyebots-instagram
python3 setup.py install
```

## Usage
```
usage: byebyebots [-h] [-u USER] [-p PASSWORD] [-l LIMIT]
                  [--email_sender_user EMAIL_SENDER_USER]
                  [--email_sender_password EMAIL_SENDER_PASSWORD]
                  [--email_recipient EMAIL_RECIPIENT] [--yes] [--dryrun]

Unsubscribe user with unrealistic number of followings

optional arguments:
  -h, --help            show this help message and exit
  -u USER, --user USER  Username fot the Instagram account
  -p PASSWORD, --password PASSWORD
                        Password fot the Instagram account
  -l LIMIT, --limit LIMIT
                        Number of followings which can be considered
                        unrealistic
  --email_sender_user EMAIL_SENDER_USER
                        Email of service user to deliver notifications
  --email_sender_password EMAIL_SENDER_PASSWORD
                        Password of service user to deliver notifications
  --email_recipient EMAIL_RECIPIENT
                        Password of service user to deliver notifications
  --yes                 Proceed without manul approving of unsubscribe action
  --dryrun              Replace unsubscribe action with a safe one, for
                        testing purposes
```

## Examples
Run in interactove dryrun mode to see how many potential bots are going to be unsubscribed. You will be asked to authenticate to Instagram account:
```
byebyebots --dryrun
```

Run in non-interactive mode. Remove `--dryrun` option to proceed with unsubscribing. 
```
goodbyebots -u instagram_login -p instagram_password --yes --dryrun
```
In case you decide to run this tool by schedule, it supports email notifications. First, you'll need to create a mailbox for service user - from who you'll receive notifications. If you select Gmail, you'll probably need to [allow this script](https://support.google.com/accounts/answer/6010255) to use that mailbox. 
When done, pass service-user credentials to the script and specify your own email - to which you'll send notifications. Remove `--dryrun` option to proceed with unsubscribing.
```
goodbyebots --email_sender_user sender_login@gmail.com --email_sender_pass sender_pass --email_recipient myemail@gmail.com -u instagram_login -p instagram_password --yes --dryrun
```
