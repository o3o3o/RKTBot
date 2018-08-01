import re
import ssl
import json
import time
import logging
#import certifi
import requests
import settings
import websocket
import getpass
from urlparse import urlsplit, parse_qsl


logging.basicConfig()
#logging.getLogger().setLevel(logging.DEBUG)
#requests_log = logging.getLogger("requests.packages.urllib3")
#requests_log.setLevel(logging.DEBUG)
#requests_log.propagate = True

_session = requests.session()
_session.mount('https://', requests.adapters.HTTPAdapter(pool_connections=4, pool_maxsize=10))

DJ_HOST = 'https://bixin.im'
APP_HOST = 'https://app.bixin.com'

UAS = {
        'android': 'bixin_android/2018020101 (Channel/self; im.bitpocket.bitpocket; Version/1.7.5)',
        'ios': 'bixin-ios/2017122601 (iPod touch; iPhone OS 9.3.5; Scale/2.00; Version/1.0.9)'
        }

class Bot:
    websocket_host = APP_HOST.replace('http', 'ws')
    access_token = settings.ACCESS_TOKEN
    ua = UAS[settings.UA_TYPE]

    def my_request(self, url, data,  method='post'):

        headers = {
            #"Accept-Language": 'zh-Hans',
            'X-Access-Token': self.access_token,
            'User-Agent': self.ua,
        }

        if method == 'post':
            #r = _session.post(url, data=data, headers=headers, verify=certifi.where())
            r = _session.post(url, data=data, headers=headers, verify=False)
        if method == 'get':
            #r = _session.get(url, params=data, headers=headers, verify=certifi.where())
            r = _session.get(url, params=data, headers=headers, verify=False)
        return r

    def phone_set(self, phone):
        data = {
                'phone': phone,
                }
        url = DJ_HOST+'/messenger/api/v2/phone.set'
        resp = self.my_request(url, data, method='post')
        data = json.loads(resp.content)
        if not data.get('ok', False):
            raise Exception(data['error'])
        return data
        
    def phone_verify(self, phone, code):
        data = {
                'phone': phone,
                'code': code,
                }
        url = DJ_HOST+'/messenger/api/v2/phone.verify'
        resp = self.my_request(url, data, method='post')
        data = json.loads(resp.content)
        if not data.get('ok', False):
            raise Exception(data['error'])
        return data

    def login_verify(self, phone, password):
        data = {
                'phone': phone,
                'password': password,
                }
        url = DJ_HOST+'/messenger/api/v2/login.verify'
        resp = self.my_request(url, data, method='post')
        data = json.loads(resp.content)
        if not data.get('ok', False):
            raise exception(data['error'])
        return data

    def get_redpacket_status(self, rkt_id):
        data ={
                'redpacket_id': rkt_id,
                }
        url = DJ_HOST+'/messenger/api/v3/redpacket.status'
        resp = self.my_request(url, data, method='get')
        #print(resp)
        data = json.loads(resp.content)
        return data

    def get_profile_info(self):
        url = DJ_HOST+'/messenger/api/v2/profile.info'
        resp = self.my_request(url, {}, method='get')
        data = json.loads(resp.content)
        return data

    def redpacket_open(self, rkt_id):
        data = {
                'redpacket_id': rkt_id,
                }
        url = DJ_HOST+'/messenger/api/v3/redpacket.open'
        resp = self.my_request(url, data, method='post')
        data = json.loads(resp.content)
        return data

    def login_and_monitor(self):
        #with open('cookie.txt', 'w') as f:
        #    json.dump(requests.utils.dict_from_cookiejar(bot.cookies), f)
        phone = raw_input('Please input your phone with country code(e.g: +8613811111111):')
        self.phone_set(phone)
        code = input('Please input sms code:')
        self.phone_verify(phone, code)
        password = getpass.getpass('Please input login password:')
        data = self.login_verify(phone, password)
        self.access_token = data['data']['token']['access_token']
        self.ws_monitor()

    def ws_monitor(self):
        headers = {
                'X-Access-Token':  self.access_token,
                'User-Agent': self.ua
                }
        #websocket.enableTrace(True)
        websocket_url = "{host}/api/v2/websocket".format(host=self.websocket_host)
        print(websocket_url)
        ws = websocket.WebSocketApp(
            websocket_url,
            header=headers,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close)
        while True:
            try:
               ws.run_forever()
            except KeyboardInterrupt:
                break
            time.sleep(5)

    def on_message(self, ws, message):
        #print(message)
        msg = json.loads(message)
        if msg[0] == 'new_msg' and  msg[1].get('content_type') == 'redpacket':
            action = msg[1]['content']['action'].replace('bixin', 'http')
            res = urlsplit(action)
            target_param = dict(parse_qsl(res.query))
            redpacket_id = target_param.get('redpacket_id')
            #print('opening redpacket_id: %s'%(redpacket_id))

            data = self.get_redpacket_status(redpacket_id)
            data = self.redpacket_open(redpacket_id)
            print('%s open redpacket_id: %s %s'%(msg[1]['created_at'], redpacket_id, data['data'].get('gotted_amount_dict', 'nothing')))


    def on_error(self, ws, error):
        #if str(error) == 'Handshake status 401':
        #    print('Your Access-token is expired')
        #    raise Exception('auth failed')
        print "##on_error in ws: %s"%error

    def on_close(self, ws):
        print "### closed {} ###".format(ws)

def main():
    bot = Bot()
    #print(bot.get_profile_info())
    try:
        if not settings.ACCESS_TOKEN:
            bot.login_and_monitor()
        else:
            bot.ws_monitor()
    except KeyboardInterrupt:
        #TOOD: save cookies
        pass

if __name__ == "__main__":
    main()

