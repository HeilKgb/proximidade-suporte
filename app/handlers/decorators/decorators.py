#!/usr/bin/env python3

import os
from functools import wraps
from logging import info
from json import loads, dumps
from datetime import datetime
from urllib.parse import unquote
from dateutil.relativedelta import relativedelta
from tornado.web import decode_signed_value

from risk3_utils import token_decode

def https_required(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        using_ssl = (self.request.headers.get('X-Scheme', 'http') == 'https')
        if not using_ssl:
            self.response(403, 'A SSL (https) connection is required.')
            return
        info('HTTPS connection verified.')
        return method(self, *args, **kwargs)
    return wrapper


def vpc_access_only(handler_class):
    ''' Handle Tornado HTTP Basic Auth '''
    def wrap_execute(handler_execute):
        def require_cross(handler, kwargs):
            info('This is a VPC Request')
            # Force to accept requests only in the VPC
            remote_ip = handler.request.headers.get("X-Real-IP") or handler.request.remote_ip
            info('IP requesting VPC connection: ' + remote_ip)
            cross_token = str(handler.request.headers.get('Cross-Key', '123456'))
            info('Cross token: ' + str(cross_token))
            if 'CROSS_KEY' in handler.settings.keys():
                cross_key = handler.settings['CROSS_KEY']
                # Cross token lives for 10 minutes (10 * 0.0006945) considering same TZ
                check = token_decode(cross_token, cross_key)
                check = decode_signed_value(
                    cross_key, 'crosstoken',
                    check, max_age_days=0.006945)
                if check:
                    # Ok, here the key can live for 10 minutes.
                    info('The key was decoded, now check time.')
                    try:
                        if datetime.utcfromtimestamp(float(check)) + relativedelta(minutes=10) >= datetime.utcnow():
                            info('The key is valid.')
                            return True
                    except Exception as e:
                        info('Fail to convert cross token to be evaluated. {}'.format(e))
                info('The key is invalid.')
            else:
                info('Check the configuration for CROSS_KEY variable on settings.py file.')
            handler.set_status(401)
            handler._transforms = []
            handler.set_header('Content-Type', 'application/json; charset=UTF-8')
            handler.write('{"status": "unauthorized", "message": "This resource is available only to logged users."}')
            handler.finish()
            return False

        def _execute(self, transforms, *args, **kwargs):
            if not require_cross(self, kwargs):
                return False
            return handler_execute(self, transforms, *args, **kwargs)

        return _execute

    handler_class._execute = wrap_execute(handler_class._execute)
    return handler_class


def api_authenticated(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.current_user:
            if hasattr(self, 'token_passed_but_invalid'):
                self.response(401, 'Authentication credentials is invalid.')
            else:
                self.response(401, 'Authentication required.')
            return
        return method(self, *args, **kwargs)
    return wrapper

def allowAdmin(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if self.current_user is None:
            self.response(401, 'Acesso querer autenticação.')
            return

        if self.current_user['role'] != 'Administrator':
            self.response(403, 'Acesso permitido somente aos administradores.')
            return

        return method(self, *args, **kwargs)
    return wrapper


def check_credentials(func):
    @wraps(func)
    def wrapper_func(self, *args, **kwargs):
        info('=============================================')
        info(' Authentication Process Started')
        info('---------------------------------------------')
        info(f" user: {self.current_user}")

        self.current_user = None
        self.VAT = None

        # set the AUTHCENTER_LOCAL variable when located on the venidera's network
        url = os.environ.get(
            'AUTHCENTER_LOCAL', self.settings['AUTHCENTER']) + '/auth/crosslogin'

        # Get authentication credentials
        # Precedence:
        # 1 - Token (Header)
        # 2 - Cookie appkey + Cookie VAT (token)
        # 3 - VAT (token)

        token_header = None
        token = self.request.headers.get("Venidera-AuthToken")
        if token:
            token_header = unquote(token)
        info(f"token_header: {token_header}")

        token_cookie = None
        VAT = self.get_cookie("VAT")
        if VAT:
            token_cookie = unquote(VAT)
        info(f"token_cookie: {token_cookie}")

        # Get application key
        app_cookie = None
        app = self.get_secure_cookie('appKey')
        if app:
            app_cookie = loads(app)
        info(f"app_cookie: {app_cookie}")

        # Credentials Loaded
        # Start check
        token_check = None

        if token_header or token_cookie:
            if token_header:
                info(f'Token from Header (Venidera-AuthToken) or cookie VAT')
            elif token_cookie:
                info(f'Token from cookie VAT')
            body = self.json_encode({'token': token_header or token_cookie})
            response = yield self.http_call(url=url, method='POST', body=body)

            # check token validate
            if response.code == 200:
                # Usuário com VAT válido
                token_check = loads(response.body.decode('utf-8'))['data']
            else:
                info('Token not valid... Autentication Failed')

        if token_check:
            # Header token authentication
            if token_header and (not token_cookie and not app_cookie):
                info('Authentication type: TOKEN (header)')
                self.current_user = token_check
                self.VAT = token_header
                info('... API Login OK!')
            # VAT token authentication
            elif token_cookie and not app_cookie:
                info('Authentication type: VAT (cookie) and no appkey')
                self.current_user = token_check
                self.VAT = token_cookie
                self.set_secure_cookie("appKey", dumps(self.current_user))
                info('... Login OK!')
            elif app_cookie and token_cookie:
                # Auth will be ok to this app
                info('Authentication type: COOKIE (appkey)')
                if app_cookie['username'] != token_check['username']:
                    self.current_user = token_check
                    self.set_secure_cookie("appKey", dumps(self.current_user))
                else:
                    self.current_user = app_cookie
                self.VAT = token_cookie
                info('... Login OK and Credentials Updated!')
        else:
            # Sem informação de login
            info('No credentials found.')
        info('---------------------------------------------')
        info(' Authentication Process Finished')
        info('=============================================')
        return func(self, *args, **kwargs)
    return wrapper_func