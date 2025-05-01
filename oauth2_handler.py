
import urllib
import json

REDIRECT_URI = 'https://token-reciever-cheetolord.replit.app'


def UrlEscape(text):
    return urllib.parse.quote(text, safe='~-._')


def FormatUrlParams(params):
    param_fragments = []
    for param in sorted(params.items(), key=lambda x: x[0]):
        param_fragments.append('%s=%s' % (param[0], UrlEscape(param[1])))
    return '&'.join(param_fragments)


def generatePermissionURL(client_id):
    params = {}
    params['client_id'] = client_id
    params['redirect_uri'] = REDIRECT_URI
    params['scope'] = 'https://mail.google.com/'
    params['response_type'] = 'code'
    params['access_type'] = 'offline'
    params['prompt'] = 'consent'
    return '%s?%s' % ("https://accounts.google.com/o/oauth2/auth",
                        FormatUrlParams(params))


def authorize_code(client_id, client_secret, authorization_code):
    params = {}
    params['client_id'] = client_id
    params['client_secret'] = client_secret
    params['code'] = authorization_code
    params['redirect_uri'] = REDIRECT_URI
    params['grant_type'] = 'authorization_code'
    request_url = "https://accounts.google.com/o/oauth2/token"

    response = urllib.request.urlopen(request_url, urllib.parse.urlencode(params).encode('utf-8')).read()
    return json.loads(response)


def getPermissionURL(client_id):
    return generatePermissionURL(client_id)
    

def get_token(client_id, client_secret, code):
    response = authorize_code(client_id, client_secret, code)
    if 'error' in response:
        raise Exception('Error: %s' % response['error'])
    access_token = response['access_token']
    refresh_token = response['refresh_token']
    expires_in = response['expires_in']
    return access_token, refresh_token, expires_in