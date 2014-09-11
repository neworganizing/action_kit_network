import datetime
import json
import requests
from requests.auth import HTTPBasicAuth
import time

# Relevant functions are group as static class methods under ActionKit/ActionNetwork
#       because ActionKit.get_signups() is more sensible than get_actionkit_signups()

# You'll need the following constants defined somewhere:

# ActionKit

AK_API_USER = ''
AK_API_PASS = ''

AK_PAGE = ''
AK_PAGE_NAME = ''

AK_LIST = ''
AK_LIST_NAME = ''

# ActionNetwork

AN_MAIN_API_KEY = ''

AN_GROUPS = (
    (''),
)

class ActionKit(object):

    @staticmethod
    def get_signups(page, api_url='https://act.zzz.zzz/rest/v1/', which_signups='action'):

        ' Get all signups from ActionKit '

        def parse_raw_signups(raw_signups=[]):

            subs_web = []
            subs_api = []

            for raw_signup in raw_signups:
                raw_user = raw_signup.get('user', '//').split('/')[-2]

                if raw_user:

                    if raw_signup.get('source') == 'website':
                        source = 'website'
                        subs_web.append(raw_user)
                    elif raw_signup.get('source') == 'restful_api':
                        source = 'restful_api'
                        subs_api.append(raw_user)
                    else:
                        source = 'other'
                        subs_api.append(raw_user)

            return subs_web, subs_api

        web_signups = []
        api_signups = []

        if which_signups == 'action':
            request_url = '{0}surveyaction/?page={1}'.format(api_url, page)
        else:
            request_url = '{0}subscription/?list={1}'.format(api_url, page)

        try:
            time.sleep(1)
            response = requests.get(request_url,
                auth=HTTPBasicAuth(AK_API_USER, AK_API_PASS)).json()
        except:
            print "[ERROR] Failed to get_signups() from ActionKit."
            return ()
        else:
            new_web_subs, new_api_subs = parse_raw_signups(response.get('objects'))
            web_signups.extend(new_web_subs)
            api_signups.extend(new_api_subs)

            while response.get('meta').get('next'):
                try:
                    time.sleep(2)
                    response = requests.get('https://act.zzz.zzz{0}'.format(response.get('meta').get('next')),
                        auth=HTTPBasicAuth(AK_API_USER, AK_API_PASS)).json()
                except:
                    print "[ERROR] Failed to get next page in get_signups() from ActionKit."
                    break
                else:
                    new_web_subs, new_api_subs = parse_raw_signups(response.get('objects'))
                    web_signups.extend(new_web_subs)
                    api_signups.extend(new_api_subs)

        return web_signups, api_signups

    @staticmethod
    def get_info_from_user_id(user_id):

        user_info = {}

        try:
            time.sleep(0.5)
            response = requests.get('https://act.zzz.zzz/rest/v1/user/{0}/'.format(user_id),
                auth=HTTPBasicAuth(AK_API_USER, AK_API_PASS))
            response = response.json()
        except:
            print "[ERROR] Failed to get_info_from_user_id({0})".format(user_id)
        else:
            user_info['email'] = response.get('email')
            user_info['first_name'] = response.get('first_name')
            user_info['last_name'] = response.get('last_name')
            user_info['zipcode'] = response.get('zip')
            user_info['ak_id'] = user_id

            if user_info.get('source') == 'restful_api':
                user_info['source'] = 'restful_api'
            else:
                user_info['source'] = 'website'

        return user_info

    @staticmethod
    def get_or_create_user(email):

        ' Given an email address, returns the AK user if existing or creates and then returns the user. '

        try:
            time.sleep(1)
            response = requests.get('https://act.zzz.zzz/rest/v1/user/?email={0}'.format(email.replace('+', '%2b')),
                auth=HTTPBasicAuth(AK_API_USER, AK_API_PASS)).json()
        except:
            print "[ERROR] Failed to get_or_create_user({0}) from ActionKit.".format(email)
        else:
            try:
                if response['meta']['total_count'] == 0:
                    data = {'email': email}
                    try:
                        time.sleep(1)
                        response = requests.post('https://act.zzz.zzz/rest/v1/user/',
                            auth=HTTPBasicAuth(AK_API_USER, AK_API_PASS), data=data)
                    except:
                        print "[ERROR] Failed to create user: {0}".format(email)
                    else:
                        try:
                            new_id = response.headers.get('location')
                            if new_id:
                                new_id = new_id.split('/')[-2]
                        except:
                            print "[ERROR] Failed to get new_id"
                        else:
                            print "New user #{0} created".format(new_id)
                            zipcode = '12345'
                            if new_id:
                                ActionKit.add_action(AK_PAGE_NAME, new_id, email, zipcode)
                                ActionKit.add_subscription(AK_LIST_NAME, new_id, email, zipcode)
                                return
                elif response['meta']['total_count'] == 1:
                    if response['objects'][0].get('subscription_status'):
                        if response['objects'][0].get('subscription_status') != 'unsubscribed':
                            return response.get('objects', [{}])[0].get('resource_uri', '//').split('/')[-2]
                        else:
                            print "\t[INFO] {0} is unsubscribed.".format(email)
            except KeyError:
                print "[ERROR] Failed to get_or_create_user() from ActionKit."

    @staticmethod
    def check_action(page_id, user_id):

        needle = '/rest/v1/surveypage/{0}/'.format(page_id)

        try:
            time.sleep(1)
            response = requests.get('https://act.zzz.zzz/rest/v1/action/?user={0}'.format(user_id),
                auth=HTTPBasicAuth(AK_API_USER, AK_API_PASS)).json()
        except:
            print "[ERROR] Failed to check_action() from ActionKit."
        else:
            for action in response.get('objects', ()):
                if needle == action['page']:
                    try:
                        time.sleep(1)
                        user_response = requests.get('https://act.zzz.zzz/rest/v1/user/{0}/'.format(user_id),
                            auth=HTTPBasicAuth(AK_API_USER, AK_API_PASS)).json()
                    except:
                        zipcode = '12345'
                    else:
                        zipcode = user_response.get('zip', '12345')
                    return True, zipcode
            while response.get('meta').get('next'):
                try:
                    time.sleep(2)
                    response = requests.get('https://act.zzz.zzz{0}'.format(response.get('meta').get('next')),
                        auth=HTTPBasicAuth(AK_API_USER, AK_API_PASS)).json()
                except:
                    print "[ERROR] Failed to get next page in check_action() from ActionKit."
                    break
                else:
                    for action in response.get('objects', ()):
                        if needle == action['page']:
                            try:
                                time.sleep(1)
                                user_response = requests.get('https://act.zzz.zzz/rest/v1/user/{0}/'.format(user_id),
                                    auth=HTTPBasicAuth(AK_API_USER, AK_API_PASS)).json()
                                
                            except:
                                zipcode = '12345'
                            else:
                                zipcode = user_response.get('zip', '12345')
                            return True, zipcode

        return False, False

    @staticmethod
    def add_action(page_name, user_id, email, zipcode, request_url='https://act.zzz.zzz/rest/v1/action/'):
        
        data = {
            'user': '/rest/v1/user/{0}/'.format(user_id),
            'page': page_name,
            'email': email,
            'zip': zipcode,
        }

        try:
            response = requests.post(request_url,
                    auth=HTTPBasicAuth(AK_API_USER, AK_API_PASS), data=data)
        except:
            print "[ERROR] Failed to add action for #{0}".format(user_id)
        else:
            if 299 >= response.status_code >= 200:
                print "\t [OK: {0}] Added #{1} to {2}".format(response.status_code, user_id, page_name)
            else:
                print "\t [ERROR] Response Code: ", response.status_code
                print "\t", response.headers
                print "\t", response.text

        time.sleep(1)

    @staticmethod
    def check_subscription(list_id, user_id):
        
        needle = '/rest/v1/list/{0}/'.format(list_id)

        try:
            time.sleep(1)
            response = requests.get('https://act.zzz.zzz/rest/v1/subscription/?user={0}'.format(user_id),
                auth=HTTPBasicAuth(AK_API_USER, AK_API_PASS)).json()
        except:
            print "[ERROR] Failed to check_subscription() from ActionKit."
            return False, False
        else:
            for action in response.get('objects', ()):
                if needle == action['list']:
                    try:
                        time.sleep(1)
                        user_response = requests.get('https://act.zzz.zzz/rest/v1/user/{0}/'.format(user_id),
                            auth=HTTPBasicAuth(AK_API_USER, AK_API_PASS)).json()
                    except:
                        zipcode = '12345' # A big fudge
                    else:
                        zipcode = user_response.get('zip', '12345')
                    return True, zipcode
            while response.get('meta').get('next'):
                try:
                    time.sleep(2)
                    response = requests.get('https://act.zzz.zzz{0}'.format(response.get('meta').get('next')),
                        auth=HTTPBasicAuth(AK_API_USER, AK_API_PASS)).json()
                except:
                    print "[ERROR] Failed to get next page in check_subscription() from ActionKit."
                    break
                else:
                    for action in response.get('objects', ()):
                        if needle == action['list']:
                            try:
                                time.sleep(1)
                                user_response = requests.get('https://act.zzz.zzz/rest/v1/user/{0}/'.format(user_id),
                                    auth=HTTPBasicAuth(AK_API_USER, AK_API_PASS)).json()
                            except:
                                zipcode = '12345'
                            else:
                                zipcode = user_response.get('zip', '12345')
                            return True, zipcode

        return False, False

    @staticmethod
    def add_subscription(page_name, user_id, email, zipcode, request_url='https://act.zzz.zzz/rest/v1/action/'):

        ''' Since there isn't a direct way to add a subscription
        and there also isn't a way to have signup pages add supporters
        to more than one list, make a dummy signup page tied to the appropriate list.
        '''
        
        data = {
            'user': '/rest/v1/user/{0}/'.format(user_id),
            'page': page_name,
            'email': email,
            'zip': zipcode,
        }

        try:
            response = requests.post(request_url,
                    auth=HTTPBasicAuth(AK_API_USER, AK_API_PASS), data=data)
        except:
            print "[ERROR] Failed to subscribe {0}".format(user_id)
        else:
            if 299 >= response.status_code >= 200:
                print "\t [OK: {0}] Subscribed #{1} to {2}".format(response.status_code, user_id, page_name)
            else:
                print "\t [ERROR] Response Code: ", response.status_code
                print "\t", response.headers
                print "\t", response.text

        time.sleep(1)

class ActionNetwork(object):

    @staticmethod
    def get_signups(main_api_key, api_key, request_url):

        headers = {
            'api-key': main_api_key,
        }

        person_ids = []

        try:
            time.sleep(1)
            response = requests.get(request_url, headers=headers)
            response = response.json()
        except:
            print "[ERROR] ActionNetwork: Failed to get {0}".format(request_url)
        else:
            response_items = response.get('_embedded', {}).get('osdi:items', [])
            for response_item in response_items:
                try:
                    person_ids.append({response_item['_links']['osdi:person']['href']: api_key})
                except:
                    print "[INFO] ActionNetwork: KeyError in getting data from {0}".format(request_url)

        return person_ids

    @staticmethod
    def get_emails(api_key, request_url='https://actionnetwork.org/api/v1/people'):

        headers = {
            'api-key': api_key,
        }

        emails = []

        try:
            time.sleep(1)
            response = requests.get(request_url, headers=headers)
            response = response.json()
        except:
            print "[ERROR] ActionNetwork: Failed to get emails for {0}".format(api_key)
        else:

            while response.get('_links', {}).get('next', {}).get('href'):
                nextpage = response.get('_links', {}).get('next', {}).get('href')

                print "\t\tOn page # {0}".format(nextpage.split('page=')[-1])

                response_items = response.get('_embedded', {}).get('osdi:people', [])
                for response_item in response_items:
                    response_email = response_item.get('email_addresses', [{}])[0]

                    if response_email.get('address') and response_email.get('primary'):
                        emails.append(response_email.get('address'))
                    else:
                        print "[INFO] ActionNetwork: Couldn't get email for {0}".format(api_key)

                time.sleep(1)
                response = requests.get(nextpage, headers=headers)
                response = response.json()

        return emails

    @staticmethod
    def signup(api_key, request_url, first_name, last_name, zipcode, email):

        headers = {
            'api-key': api_key,
            'Content-Type': 'application/json'
        }

        data = {
          "originating_system": "actionkit",
          "person" : {
            "family_name" : last_name,
            "given_name" : first_name,
            "postal_addresses" : [ { "postal_code" : zipcode }],
            "email_addresses" : [ { "address" : email }]
          },
          "record_submissions_helper" : {
            "href": request_url
          }
        }

        try:
            time.sleep(1)
            response = requests.post(request_url, headers=headers, data=json.dumps(data))
            response = response.json()
        except:
            print "[ERROR] Failed to sign {0} up for {1}".format(email, api_key[:6])
        else:
            print "[OK] Signed up {0} for {1}".format(email, api_key[:6])
