import mechanize
import urlparse
import traceback
import hashlib
import urllib
import urllib2
import json


class Auth(object):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if isinstance(value, (list, tuple)):
                value = value[0]
            setattr(self, key, value)


class VKApi(object):
    URL = 'https://api.vk.com/'

    def __init__(self):
        self.auth = None
        self.api_id = None

    def log_in(self, email, password, api_id, scope):
        self.api_id = api_id

        try:
            browser = mechanize.Browser()
            browser.set_handle_robots(False)

            browser.open(
                'http://oauth.vk.com/oauth/authorize?redirect_uri='
                'http://oauth.vk.com/blank.html&response_type=token'
                '&client_id={}&scope={}&'
                'display=wap&response_type=token'.format(api_id, scope)
            )
            browser.select_form(nr=0)
            browser.form['email'] = email
            browser.form['pass'] = password
            browser.submit()

            if len(list(browser.forms())):
                # We need to confirm app auth.
                browser.select_form(nr=0)
                browser.submit()

            parsed = urlparse.parse_qs(browser.geturl().split('#')[-1])

            self.auth = Auth(**parsed)
            return True
        except:
            traceback.print_exc()
            return False

    def request(self, method, **kwargs):
        assert self.auth

        # sig = str(self.auth.user_id)
        #
        # for key in sorted(kwargs.keys()):
        #     value = kwargs[key]
        #
        #     if isinstance(value, unicode):
        #         value = value.encode('utf-8')
        #         kwargs[key] = value
        #
        #     sig += '='.join((key, value))
        #
        # sig = hashlib.md5(sig).hexdigest()

        data = dict(
            # api_id=self.api_id,
            uid=self.auth.user_id,
            # method=method,
            # sig=sig,
            # format='json',
            access_token=self.auth.access_token
        )

        data.update(kwargs)
        for key, value in data.items():
            if isinstance(value, unicode):
                data[key] = value.encode('utf-8')

        print data
        print urllib.urlencode(data)

        url = VKApi.URL + '/method/{}'.format(method) + '?' + urllib.urlencode(data)
        response = urllib2.urlopen(url)

        return json.loads(response.read())

api = VKApi()
