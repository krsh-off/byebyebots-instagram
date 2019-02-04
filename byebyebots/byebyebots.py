#!/usr/bin/env python3

import re
import time
import multiprocessing
import argparse
import getpass
import smtplib
from urllib import request
from bs4 import BeautifulSoup
from InstagramAPI import InstagramAPI
from copy import deepcopy
from functools import wraps
from random import randint
from itertools import zip_longest
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from .version import __version__

# Initially this planned to be multiprocess program, which can speedup the 
# procedure executing in few streams  simultaneously.  However,  Instagram 
# limits number of connection for both API  and web  endpoints.  Thus, the 
# most efficient way of  run  is  a  single  processes with time.sleen(n), 
# where 'n' is a random number between  specified  interval, which appears
# only in case of 429 HTTP code response. 
#
# In other words, multiprocessing is useless here, but  I spent some  time
# on it, so here it is 
POOL_SIZE = 1
REQ_INTERVAL = (120, 180)

def parse_argumets():
    """Aggregate all arguments passed to the program
    """

    parser = argparse.ArgumentParser(description='Unsubscribe user with unrealistic number of followings')
    parser.add_argument('-u', '--user', 
                        help='Username fot the Instagram account')
    parser.add_argument('-p', '--password', 
                        help='Password fot the Instagram account')
    parser.add_argument('-l', '--limit', 
                        default=1500,
                        type=int,
                        help='Number of followings which can be considered unrealistic')
    parser.add_argument('--email_sender_user', 
                        help='Email of service user to deliver notifications')
    parser.add_argument('--email_sender_password', 
                        help='Password of service user to deliver notifications')
    parser.add_argument('--email_recipient', 
                        help='Password of service user to deliver notifications')
    parser.add_argument('--yes', 
                        action='store_true',
                        help='Proceed without manul approving of unsubscribe action')
    parser.add_argument('--dryrun', 
                        action='store_true',
                        help='Replace unsubscribe action with a safe one, for testing purposes')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {version}'.format(version=__version__))
    return parser.parse_args()

def timeit(func):
    """Calculate time of execution of inner function
    """

    @wraps(func)
    def inner(*args, **kwargs):
        start = time.time()
        res = func(*args, **kwargs)
        end = time.time()
        exec_time = str(round((end-start), 3))
        print('Execution time: {0}'.format(exec_time))
        return res
    return inner

def make_hashable(d):
    """Sort list of dicts without any issues
    """

    return (frozenset(x.items()) for x in d)

def auth():
    """Authenticate to Instagram using user/pass pair
    """

    api = InstagramAPI(args.user, args.password)
    api.login()
    return api

def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks
    """

    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)

def following_count(user, retry=True):
    """Get following of ther users without using API
    """

    username = user['username']
    full_name = user['full_name'] if user['full_name'] else '<no full name>' 
    following = 0
    result = 1
    if not retry:
        result = -2
    try:
        resp = request.urlopen("https://www.instagram.com/{0}/".format(username))
        html = resp.read()
        fancyHTML = BeautifulSoup(html, "html.parser")

        metaContentTags = fancyHTML.select("meta[content]")
        for tags in metaContentTags:
            strContent = tags.get("content").replace(",", "")
            if strContent.find("Follow") != -1:
                _following = int(re.findall(r'[\d.]+', strContent)[1])
        if _following > args.limit:
            following = _following
            print('[{0}] @{1} - {2}'.format(following, username, full_name))
    except Exception as err:
        print('[failed] @{0} - {1}'.format(username, full_name))
        result = -1
        if '429' in str(err):
            wait = randint(REQ_INTERVAL[0], REQ_INTERVAL[1])
            print('--- take a rest, {0} sec ---'.format(wait))
            time.sleep(wait)
        else:
            print('Unhandled error:', err)
        if retry:
            result = following_count(user, False)[1]
    finally:
        return (user, result, following)

def remove_follower(api, user, retry=True):
    """Remove follower by blocking/unblocking their
    """

    uid = user['pk']
    username = user['username']
    full_name = user['full_name'] if user['full_name'] else '<no full name>' 
    result = 1
    if not retry:
        result = -2
    try:
        if args.dryrun:
            api.getUsernameInfo(uid)
            api.getUsernameInfo(uid)
        else:
            api.block(uid)
            api.unblock(uid)
        out = api.LastJson
        if not 'ok' == out['status']:
            if 'wait a few minutes' in out['message']:
                raise Exception(out['message'])
        print('[unsubscribed] @{0} - {1}'.format(username, full_name))
    except Exception as err:
        print('[failed_unsubscribe] @{0} - {1}'.format(username, full_name))
        result = -1
        if 'wait a few minutes' in str(err):
            wait = randint(REQ_INTERVAL[0], REQ_INTERVAL[1])
            print('--- take a rest, {0} sec ---'.format(wait))
            time.sleep(wait)
        else:
            print('Unhandled error:', err)
        if retry:
            result = remove_follower(api, user, False)[1]
    finally:
        return (user, result)

def send_email(unsubscribed, 
               following_map,
               total_scan,
               failed_scan,
               retried_scan,
               didnt_pass,
               planned_unsub,
               failed_unsub,
               retried_unsub
               ):
    """In case you want to automate the process, you can create a service
    account,  from  which  you'll  notify  your  actual email about every 
    successful run. Thus, you  wan't  expose  a  credential for your real
    account
    """

    msgText = '''
    <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
            <style type="text/css">
                .tg  {border-collapse:collapse;border-spacing:0;}
                .tg td{font-family:Arial, sans-serif;font-size:14px;padding:10px 5px;border-style:solid;border-width:1px;overflow:hidden;word-break:normal;border-color:black;}
                .tg th{font-family:Arial, sans-serif;font-size:14px;font-weight:normal;padding:10px 5px;border-style:solid;border-width:1px;overflow:hidden;word-break:normal;border-color:black;}
                .tg .tg-fnn3{font-weight:bold;font-family:Arial, Helvetica, sans-serif !important;;background-color:#d2d0f7;border-color:#d2d0f7;text-align:center;vertical-align:top}
                .tg .tg-rnnb{border-color:#d2d0f7;text-align:center;vertical-align:center}
                .tg .tg-h1t5{border-color:#d2d0f7;text-align:left;vertical-align:center}
            </style>
        </head>
        <body>
    '''

    strFrom = args.email_sender_user
    strTo = args.email_recipient 

    msgRoot = MIMEMultipart('alternative')
    msgRoot['Subject'] = 'Hooray! {0} bot-like users were unsubscribed from @{1}!'.format(len(unsubscribed), args.user)
    msgRoot['From'] = 'ByeByeBots Instagram'
    msgRoot['To'] = strTo

    msgText += '<p>Dear Instagrammer,</p>'
    msgText += '<p>Here is a report of ByeByeBots actions for {0}.<br>'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    msgText += "The goal was to unsubscribe users who follows more than {0} accounts and are not followed by <a href='https://www.instagram.com/{1}/'>@{1}</a>.</p>".format(args.limit, args.user)

    if unsubscribed:
        msgText += "<p>Next Instagram users were unsubscribed from <a href='https://www.instagram.com/{0}/'>@{0}</a> account:</p>".format(args.user)
        msgText += '''
            <table class="tg">
                <tr>
                    <th class="tg-fnn3">Picture</th>
                    <th class="tg-fnn3">Username</th>
                    <th class="tg-fnn3">Full Name</th>
                    <th class="tg-fnn3">Following</th>
                </tr>
        '''
        for user in unsubscribed:
            msgText += "<tr><td class='tg-rnnb'><img src='{0}' height=50 width=50></img></td><td class='tg-h1t5'><a href='https://www.instagram.com/{1}/'>@{1}</a></td><td class='tg-h1t5'>{2}</td><td class='tg-rnnb'>{3}</td></tr>".format(
               user['profile_pic_url'], user['username'], user['full_name'], following_map[user['username']])
        msgText += '</table>'
    else:
        msgText += 'No bot-like users identified in your Instagram account. Congrats!'

    meta = """
        <p><i>Run metadata:</i></p>
        <p style="padding-left: 30px;"><i>
            Total scans: {0}<br>
            Failed scans: {1}<br>
            Retried scans: {2}<br>
            Didn't pass condition: {3}<br>
            Planned to be unsubscribed: {4}<br>
            Failed unsubscribe: {5}<br>
            Retried unsubscribe: {6}<br>
            Successfully unsubscribed: {7}<br>
        </i><p>
    """.format(total_scan,
               failed_scan,
               retried_scan,
               didnt_pass,
               planned_unsub,
               failed_unsub,
               retried_unsub,
               len(unsubscribed))

    msgText += meta
    msgText += '<p>---------------------<br/><i>Sincerely yours,<br>ByeByeBots</i></p>'
    msgText += '</body>'

    msgText = MIMEText(msgText, 'html')
    msgRoot.attach(msgText)

    smtp = smtplib.SMTP('smtp.gmail.com:587')
    smtp.starttls()
    smtp.login(args.email_sender_user, args.email_sender_password)
    smtp.sendmail(strFrom, strTo, msgRoot.as_string())
    smtp.quit()


@timeit
def main():
    """Perform all actions to identify and unsubscribe bot users
    """

    global args
    args = parse_argumets()

    if not args.user:
        in_user = input('Please specify your Instagram username: ')        
        if not in_user:
            raise Exception('[error] Username can\'t be empty string')
        args.user = in_user

    if not args.password:
        in_password = getpass.getpass('Please specify your Instagram password: ')        
        if not in_password:
            raise Exception('[error] Password can\'t be empty string')
        args.password = in_password

    try:
        api = auth()    
        user_id = api.username_id
    except Exception as err:
        print('\n[error] Unable to login, please check you login details\n')
        raise err

    followers = api.getTotalFollowers(user_id)
    following = api.getTotalFollowings(user_id)

    potential_bots = deepcopy(followers)
    for x in followers:
        for y in following:
            if x['pk'] == y['pk']:
                potential_bots.remove(x)
                continue
    
    print('=' * 60)
    print('Account:', args.user)
    print('Number of followers:', len(followers))
    print('Number of followings:', len(following))
    print('-' * 60)
    print('Who has more that {0} followings:'.format(args.limit))

    pool = multiprocessing.Pool(POOL_SIZE)
    results = [pool.apply_async(following_count, args=(user,)) for user in potential_bots]
    pool.close()
    pool.join()

    to_delete = []
    failed_scan = []
    retried_scan = []
    following_map = {}
    for result in results:
        try:
            user, result_code, following = result.get()
            if following > 0:
                to_delete.append(user)
                following_map[user['username']] = following
            if result_code == -1:
                failed_scan.append(user)
            elif result_code == -2:
                retried_scan.append(user)
        except Exception as err:
            print('Exception during receiving data:', result)
            print(err)

    print('-' * 60)
    print('Total scans: {0} user(s)'.format(len(potential_bots)))
    print('Failed to scan: {0} user(s)'.format(len(failed_scan)))
    print('Retried to scan: {0} user(s)'.format(len(retried_scan)))
    print('Didn\'t pass condition: {0} users(s)'.format(len(potential_bots) - len(failed_scan) - len(to_delete)))
    print('To be unsubscribed: {0} user(s) - {1}% of all users'.format(
        len(to_delete), round((len(to_delete)*100)/len(followers))))
    print('-' * 60)

    if not args.yes:
        pres = input('Proceed with removing {0} followers? [yes/No]: '.format(len(to_delete)))
        if pres != 'yes':
            print('Okay, exiting the program...')
            return
    else:
        print('Confirmation is not required for this run, starting with unsubscribing...')

    if args.dryrun:
        print('--- Running in DRYRUN mode ---')

    pool = multiprocessing.Pool(POOL_SIZE)
    results = [pool.apply_async(remove_follower, args=(api, user,)) for user in to_delete]
    pool.close()
    pool.join()

    unsubscribed = []
    failed_unsubscribe = []
    retried_unsubscribe = []
    for result in results:
        try:
            user, unsubscribe_code = result.get()
            if unsubscribe_code == 1:
                unsubscribed.append(user)
            elif unsubscribe_code == -1:
                failed_unsubscribe.append(user)
            elif unsubscribe_code == -2:
                retried_unsubscribe.append(user)
        except Exception as err:
            print('Exception during receiving data:', result)
            print(err)

    print('-' * 60)
    print('Failed to unsubscribe: {0} user(s)'.format(len(failed_unsubscribe)))
    print('Retried to unsubscribe: {0} user(s)'.format(len(retried_unsubscribe)))
    print('Successfully unsubscribed: {0} user(s)'.format(len(unsubscribed)))
    if args.email_sender_user and args.email_sender_password and args.email_recipient:
        print('Notifying via email...')
        try:
            send_email(unsubscribed, 
                       following_map,
                       len(potential_bots),
                       len(failed_scan),
                       len(retried_scan),
                       len(potential_bots) - len(failed_scan) - len(to_delete),
                       '{0} - {1}% of all users'.format(len(to_delete), round((len(to_delete)*100)/len(followers))),
                       len(failed_unsubscribe),
                       len(retried_unsubscribe))
        except Exception as err:
            print('[error] Failure during sending email notification\n')
            raise err
        print('Done')

if __name__ == "__main__":
    main()