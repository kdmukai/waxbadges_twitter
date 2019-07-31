![waxbadges](waxbadges_logo_350x72.png)

# waxbadges_twitter
_A simple tool to automate twitter-based WAXBadges achievements ecosystems_

twitter: [@WAXBadges](https://twitter.com/WAXBadges)

#### What is WAXBadges?
see the main repo: [https://github.com/kdmukai/waxbadges](https://github.com/kdmukai/waxbadges)


## Overview
Developers can integrate any game or app into the WAXBadges open achievement system. But WAXBadges can be used for all sorts of interesting use cases beyond gaming. Our first demonstration use case was to run a twitter hype campaign to promote the project itself. Early followers were granted exclusive, limited-quantity achievements. For a twitter campaign obviously we used their screen name (e.g. '@KeithMukai') as their WAXBadges `User.userid` and then grabbed their twitter avatar url.

You can create your basic Achievements ecosystem with the convenient [WAXBadges CREATOR Tool](https://github.com/kdmukai/waxbadges_creator). But even with the tool it takes too much manual labor to add each new twitter user and then manually grant them whatever Achievement they just earned.


## Automation to the rescue
So this python script handles all that for you. Just call:
```
    python grant_twitter_user.py <twitter_user_name> <ecosystem_id> <category_id> <achievement_id>
```

It will create an ecosystem `User` record for their screen name if they haven't already been added. It will then grant the specified achievement which is uniquely identified by the `ecosystem_id` `category_id` `achievement_id` combo.

For example:
```
    python grant_twitter_user.py KeithMukai 2 1 8
```

#### Optional: DM a notification to the user
The script can also DM the user a link to their Proof-of-Achievement on the public [WAXBadges Explorer](https://explorer.waxbadges.com). Just specify the `--send_dm` flag:
```
    python grant_twitter_user.py KeithMukai --send_dm 2 1 8
```
But note that twitter clamped down on the @WAXBadges account when we sent too many automated DMs through it. DMs also won't work unless the twitter user is following the sending account.


# Getting started:
Create a virtualenv

Install the pip dependencies:
```
pip install -r requirements.txt
```

Customize the `local_settings--example.conf` and save it as `local_settings.conf`
```
[TWITTER]
CONSUMER_KEY = 1234
CONSUMER_SECRET = abcd
ACCESS_TOKEN = 5678-efgh
ACCESS_SECRET = ijlk

[WAX]
PRIVATE_KEY = 54321fedcba
ACCOUNT_NAME = abc12.waa
```
Just like the CREATOR Tool, the `PRIVATE_KEY` and the related WAX `ACCOUNT_NAME` are necessary so that your writes to WAXBadges contract can be issued without a manual authorization/signing step.
