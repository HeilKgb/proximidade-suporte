# !/usr/bin/env python3

import os
from tornado.web import asynchronous
from tornado.gen import coroutine
from tornado.gen import engine, Task
from handlers.base import BaseHandler
from json import loads
from handlers.decorators.decorators import api_authenticated
from logging import info


class UserInfoHandler(BaseHandler):
    SUPPORTED_METHODS = ("GET")

    @coroutine
    @api_authenticated
    def get(self):

        url = os.environ.get(
            'AUTHCENTER_LOCAL', self.settings['AUTHCENTER']) + '/auth/crossuserinfo'

        username = self.current_user['username']
        response = yield Task(
            self.http_call, url=url, method='GET', body='{}', headers={})
        if response and response.code == 200:
            ouser = loads(response.body)['data']
            info(ouser['role'])
            if ouser['organization'] == 'Proximidade_suporte' and ouser['role'] == 'Administrator':
                ouser['is_admin'] = True
            else:
                ouser['is_admin'] = False
            if any(app['url'] == self.settings['APPURL'] for app in ouser['apps']):
                self.response(200, 'Informações do usuário ' + username, ouser)
            else:
                self.response(401, 'Usuário não tem permissão.')
        elif response and response.code == 404:
            self.response(404, 'User not found.')
        else:
            message = loads(response.body)['message']
            self.response(response.code, message)


class UserRole(BaseHandler):
    SUPPORTED_METHODS = ("GET")

    @coroutine
    @api_authenticated
    def get(self):

        url = os.environ.get('AUTHCENTER_LOCAL',
                             self.settings['AUTHCENTER']) + '/auth/user/role'

        response = yield Task(
            self.http_call, url=url, method='GET', body='{}', headers={})
        if response and response.code == 200:
            data = loads(response.body)['data']
            if ('role' in data.keys()):
                self.write({'role': data['role']})
                self.finish()
            else:
                self.finish('User')
        elif response and response.code == 404:
            self.response(404, 'User not found.')
        else:
            message = loads(response.body)['message']
            self.response(response.code, message)


class LogoutHandler(BaseHandler):
    SUPPORTED_METHODS = ("POST")

    @asynchronous
    @engine
    @api_authenticated
    def post(self):

        url = os.environ.get('AUTHCENTER_LOCAL',
                             self.settings['AUTHCENTER']) + '/auth/crosslogout'

        response = yield Task(
            self.http_call, url=url, method='POST', body='{}', headers={})
        if response and response.code == 200:
            self.clear_cookie('VAT', domain=self.settings['ROOT_DOMAIN'])
            self.clear_cookie('appKey')
            self.response(200, 'Logout ok.')
        else:
            self.response(500, 'Fail to logout.')
