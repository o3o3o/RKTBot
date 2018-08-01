# -*- encoding: utf-8 -*-

#When access_token is empty, we login with phone&passwd
#ACCESS_TOKEN = '96900c19f8704993a552b386aa701623'
ACCESS_TOKEN = ''

UA_TYPE = 'ios' #ios or  android

try:
    from local_settings import *
except ImportError:
    pass
