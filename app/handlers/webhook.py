# !/usr/bin/env python3

import functools
# from tornado.gen import coroutine, Task
from tornado.gen import coroutine
# from handlers.base import BaseHandler
from handlers.trello_actions import TrelloActionsHandler
from logging import info
import hashlib
import hmac
import base64


def wh_authorized(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        remote_ips = self.request.headers.get("X-Forwarded-For").split(',')
        remote_ip = remote_ips.pop(0)
        while '192.168' in remote_ip and len(remote_ip) > 1:
            remote_ip = remote_ips.pop(0)
        ips = set()
        authorized_ips = self.settings['trello_authorized_ips']
        for x in authorized_ips.strip().split("\n"):
            ip = x.split('#')[0].strip()
            if '/' not in ip:
                ips.add(ip)
            else:
                sub_ips = self.parse_ips_from_subnets(ip_base=ip)
                for y in sub_ips:
                    ips.add(y)
        if remote_ip not in ips:
            self.response(403, 'Unauthorized for this IP.')
            return
        info('Trello Webhook request IP verified')
        return method(self, *args, **kwargs)
    return wrapper


def check_wb_requests(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        signature = self.request.headers.get("x-trello-webhook", "")
        if not signature:
            self.response(403, 'Unauthorized for this IP.')
            return
        else:
            signature = signature.encode('utf-8')
            content = self.request.body + self.trello[
                'callbackURL'].encode('utf-8')
            doubleHash = self.base64Digest(content)
            if not hmac.compare_digest(signature, doubleHash):
                self.response(
                    403, 'Unauthorized: Invalid request signature.')
                return
        info('Trello Webhook Request Signature verified')
        return method(self, *args, **kwargs)
    return wrapper


class WebHooksCallbackHandler(TrelloActionsHandler):
    SUPPORTED_METHODS = ("HEAD", "POST")

    # @wh_authorized
    def head(self, id=None):
        self.finish()

    def check_xsrf_cookie(self):
        pass

    def parse_ips_from_subnets(self, ip_base=None):
        ips = list()
        try:
            ip, mask = ip_base.split('/')
            nsub = pow(2, 32-int(mask))
            sub_ip, sub = ip.rsplit('.', 1)
            ips = [sub_ip + '.' + str(ip) for ip in [
                   i for i in range(int(sub), int(sub) + nsub)]]
        except Exception as e:
            info(e)
        return ips


    def base64Digest(self, signature):
        mac = hmac.new(
            key=self.trello['secret'].encode('utf-8'),
            msg=signature,
            digestmod=hashlib.sha1)
        return base64.b64encode(mac.digest())


    @wh_authorized
    @check_wb_requests
    @coroutine
    def post(self):
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        # Parser and update Risk3-Suporte data
        yield self.trello_actions()

        self.response(200, 'WebHook CallBack URL active.')
