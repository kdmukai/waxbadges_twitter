import argparse
import configparser
import eospy
import datetime as dt
import math
import pytz
import time
import twitter

from eospy.cleos import Cleos


WAX_URL = 'https://chain.wax.io'
WAX_CONTRACT = 'waxbadgesftw'

parser = argparse.ArgumentParser(description='Automates granting WAXBadges achievements to Twitter users')


# Required positional arguments
parser.add_argument('twitter_username')
parser.add_argument('ecosystem_id')
parser.add_argument('category_id')
parser.add_argument('achievement_id')

# Optional switches
parser.add_argument('-d', '--send_dm',
                    action='store_true',
                    default=False,
                    dest="send_dm",
                    help="Optionally send the twitter user a DM with a link to their Proof-of-Achievement")

parser.add_argument('-c', '--settings',
                    default="local_settings.conf",
                    dest="settings_config",
                    help="Override default settings config file location")



if __name__ == '__main__':
    args = parser.parse_args()
    twitter_username = args.twitter_username
    ecosystem_id = int(args.ecosystem_id)
    category_id = int(args.category_id)
    achievement_id = int(args.achievement_id)
    send_dm = args.send_dm

    if twitter_username.startswith('@'):
        twitter_username = twitter_username[1:]
    at_twitter_username = '@' + twitter_username

    # Read settings
    arg_config = configparser.ConfigParser()
    arg_config.read(args.settings_config)

    twitter_consumer_key = arg_config.get('TWITTER', 'CONSUMER_KEY')
    twitter_consumer_secret = arg_config.get('TWITTER', 'CONSUMER_SECRET')
    twitter_access_token = arg_config.get('TWITTER', 'ACCESS_TOKEN')
    twitter_access_secret = arg_config.get('TWITTER', 'ACCESS_SECRET')

    wax_private_key = arg_config.get('WAX', 'PRIVATE_KEY')
    wax_account_name = arg_config.get('WAX', 'ACCOUNT_NAME')


    twitter_api = twitter.Api(  consumer_key=twitter_consumer_key,
                                consumer_secret=twitter_consumer_secret,
                                access_token_key=twitter_access_token,
                                access_token_secret=twitter_access_secret)


    cleos = Cleos(url=WAX_URL)

    def get_ecosystem(key):
        ecosystems = cleos.get_table(
            code=WAX_CONTRACT,
            scope=WAX_CONTRACT,
            table='ecosystems',
            lower_bound=key,
            upper_bound=key,
            limit=1,
            timeout=30
        )
        return ecosystems.get('rows', [])[0]

    ecosystem = get_ecosystem(ecosystem_id)

    # sanity check that the specified ACCOUNT_NAME owns this ecosystem
    if ecosystem.get('account') != wax_account_name:
        raise Exception("Ecosystem.account %s did not match %s" % (ecosystem.get('account'), wax_account_name))

    # Validate the category and achievement ids
    if category_id >= len(ecosystem.get('categories')):
        raise Exception("Invalid category_id")
    if achievement_id >= len(ecosystem.get('categories')[category_id].get('achievements')):
        raise Exception("Invalid achievement_id")

    # Is the specified twitter username already in our User list?
    def get_user_id(ecosystem, userid):
        try:
            return [u.get('userid').lower() for u in ecosystem.get('users')].index(userid.lower())
        except ValueError:
            return -1

    user_id = get_user_id(ecosystem, at_twitter_username)
    if user_id == -1:
        # Have to add this twitter user to Users
        twitter_user = twitter_api.GetUser(screen_name=twitter_username)
        avatarurl = twitter_user.profile_image_url_https

        print(avatarurl)

        # The default '_normal.jpg' is too small. Omit for a larger thumb.
        avatarurl = avatarurl.replace('_normal', '')

        # Add User to ecosystem
        #   void adduser(name ecosystem_owner, uint32_t ecosystem_id, string user_name, string userid, string avatarurl) {
        arguments = {
            "ecosystem_owner": wax_account_name,
            "ecosystem_id": ecosystem_id,
            "user_name": at_twitter_username,
            "userid": at_twitter_username,
            "avatarurl": avatarurl
        }
        payload = {
            "account": WAX_CONTRACT,
            "name": "adduser",
            "authorization": [{
                "actor": wax_account_name,
                "permission": "active",
            }],
        }

        #Converting payload to binary
        data = cleos.abi_json_to_bin(payload['account'],payload['name'],arguments)

        #Inserting payload binary form as "data" field in original payload
        payload['data']=data['binargs']

        #final transaction formed
        trx = {"actions": [payload]}
        trx['expiration'] = str((dt.datetime.utcnow() + dt.timedelta(seconds=60)).replace(tzinfo=pytz.UTC))

        key = eospy.keys.EOSKey(wax_private_key)
        resp = cleos.push_transaction(trx, key, broadcast=True)

        print(resp)

        # Wait a moment for the data to percolate
        time.sleep(1)

        # Now reload the ecosystem
        ecosystem = get_ecosystem(ecosystem_id)
        user_id = get_user_id(ecosystem, at_twitter_username)

        print("User.id: %i" % user_id)

    else:
        print("Existing User: %i" % user_id)


    # void grantach(name ecosystem_owner, uint32_t ecosystem_id, uint32_t user_id, uint32_t category_id, uint32_t achievement_id, uint32_t timestamp)
    arguments = {
        "ecosystem_owner": wax_account_name,
        "ecosystem_id": ecosystem_id,
        "user_id": user_id,
        "category_id": category_id,
        "achievement_id": achievement_id,
        "timestamp": math.trunc(time.time())
    }
    payload = {
        "account": WAX_CONTRACT,
        "name": "grantach",
        "authorization": [{
            "actor": wax_account_name,
            "permission": "active",
        }],
    }

    #Converting payload to binary
    data = cleos.abi_json_to_bin(payload['account'],payload['name'],arguments)

    #Inserting payload binary form as "data" field in original payload
    payload['data']=data['binargs']

    #final transaction formed
    trx = {"actions": [payload]}
    trx['expiration'] = str((dt.datetime.utcnow() + dt.timedelta(seconds=60)).replace(tzinfo=pytz.UTC))

    key = eospy.keys.EOSKey(wax_private_key)
    resp = cleos.push_transaction(trx, key, broadcast=True)

    print(resp)

    if send_dm:
        # DM a notification to the user
        achievement = ecosystem.get('categories')[category_id].get('achievements')[achievement_id]
        msg = f"You've earned the \"{achievement.get('name')}\" achievement from \"{ecosystem.get('name')}\"!"
        msg += "\n\n"
        msg += "It will live forever on the WAX blockchain! Here's your shareable Proof-of-Achievement link."
        msg += "\n\n"
        msg += f"https://explorer.waxbadges.com/poa/{ecosystem.get('key')}/{category_id}/{achievement_id}/{user_id}"
        twitter_api.PostDirectMessage(text=msg, screen_name=twitter_username)


