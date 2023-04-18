#!/usr/bin/env python3

from tornado.web import asynchronous, create_signed_value, decode_signed_value
from tornado.gen import engine, coroutine
from json import dumps, loads
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPError
from tornado.httputil import HTTPHeaders
from datetime import datetime
from dateutil.parser import parse
from logging import info
from handlers.token import token_encode, token_decode
from uuid import uuid4
from urllib.parse import quote as urllib_quote
from functools import partial
import mimetypes
from urllib.parse import quote


@coroutine
def multipart_producer(boundary, filenames, write):
    boundary_bytes = boundary.encode()

    for filename in filenames:
        filename_bytes = filename.encode()
        mtype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        buf = (
            (b'--%s\r\n' % boundary_bytes) +
            (b'Content-Disposition: form-data; name="%s"; filename="%s"\r\n' %
             (filename_bytes, filename_bytes)) +
            (b'Content-Type: %s\r\n' % mtype.encode()) +
            b'\r\n'
        )
        yield write(buf)
        with open(filename, 'rb') as f:
            while True:
                # 16k at a time.
                chunk = f.read(16 * 1024)
                if not chunk:
                    break
                yield write(chunk)

        yield write(b'\r\n')

    yield write(b'--%s--\r\n' % (boundary_bytes,))


class HTTPUtils:
    ''' Set of useful methods related to HTTP comunication '''

    def encoding(self, d):
        if isinstance(d, bytes):
            return d.decode('utf-8')
        elif isinstance(d, datetime):
            return d.isoformat()
        else:
            return str(d)

    def json_encode(self, value):
        return dumps(value, default=self.encoding).replace("</", "<\\/")

    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json; charset=UTF-8')

    def set_json_output(self):
        self.set_header('Content-Type', 'application/json; charset=UTF-8')

    def set_html_output(self):
        self.set_header('Content-Type', 'text/html; charset=UTF-8')

    def sign_and_encrypt(self, data, key, name):
        try:
            singedvalue = create_signed_value(key, name, data)
            return token_encode(singedvalue.decode('utf-8'), key)
        except Exception as e:
            info('Fail to sign and encrypt')
            info('data: {}'.format(data))
            info('key: {}'.format(key))
            info('name: {}'.format(name))
            info('error: {}'.format(e))
            return None

    def unsign_and_decrypt(self, data, key, name, max_age_days=0.006945):
        try:
            signedvalue = token_decode(data, key)
            if signedvalue:
                decoded = decode_signed_value(
                    key, name, signedvalue, max_age_days=max_age_days)
                if decoded:
                    return decoded
        except Exception as e:
            info('Fail to unsign and decrypt')
            info('data: {}'.format(data))
            info('key: {}'.format(key))
            info('name: {}'.format(name))
            info('error: {}'.format(e))
        return None

    def keg_it(self, data):
        assert isinstance(data, str), 'data to be keg it must be str'
        return self.sign_and_encrypt(
            data,
            self.settings['KEG_KEY'],
            'kegtoken')

    def unkeg_it(self, data):
        assert isinstance(data, str), 'data to be unkeg it must be str'
        return self.unsign_and_decrypt(
            data,
            self.settings['KEG_KEY'],
            'kegtoken',
            2)

    def define_keg_url(self, suffix):
        return self.settings['KEG'] + '/api/v0/' + suffix

    @asynchronous
    @engine
    def http_call(self, url, method, body=None, headers=None,
                  curl=True, keg=False, odb=False, raw_response=True, callback=None):
        if curl:
            AsyncHTTPClient.configure(
                "tornado.curl_httpclient.CurlAsyncHTTPClient")
        http_client = AsyncHTTPClient()
        dictheaders = {"content-type": "application/json"}
        # Authentication for Barrel access
        if hasattr(self, 'VAT') and self.VAT:
            dictheaders['Venidera-AuthToken'] = self.VAT
        # Adding token type to dictheaders
        dictheaders['Venidera-TokenType'] = self.tokentype \
            if hasattr(self, 'tokentype') and self.tokentype else 'app'
        # Check cross call
        if 'CROSS_KEY' in self.settings.keys():
            # crosstoken = web.create_signed_value(secret, 'crosstoken', str(datetime.now().timestamp()))
            # crosstoken ; sleep(59);
            # dectoken = web.decode_signed_value(secret, 'crosstoken', crosstoken, max_age_days=0.0006945)
            # print(dectoken)
            # info('Cross token added to the HTTP request.')
            dictheaders['Cross-Key'] = self.sign_and_encrypt(
                str(datetime.utcnow().timestamp()),
                self.settings['CROSS_KEY'],
                'crosstoken')
        else:
            info('\n\nConfigure CROSS_KEY to call the VPC\n')
        if headers:
            for k, v in headers.items():
                dictheaders[k] = v
        if keg and 'KEG_KEY' in self.settings.keys():
            # KEG the headers
            dictheaders['Vat'] = self.keg_it(dictheaders['Venidera-AuthToken'])
            dictheaders['Keg'] = self.keg_it(
                str(datetime.utcnow().timestamp()))
            del dictheaders['Venidera-AuthToken']
            # KEG the body
            if body and not isinstance(body, str):
                body = dumps(body)
            elif body:
                body = self.keg_it(body)
        else:
            if keg:
                info('\n\nConfigure KEG_KEY to call the Barrel\n')
        h = HTTPHeaders(dictheaders)
        params = {
            'headers': h,
            'url': urllib_quote(url, safe='/@"\':?&='),
            'method': method,
            'request_timeout': 720,
            'validate_cert': False}
        if method in ['POST', 'PUT']:
            params['body'] = dumps(body) if not isinstance(body, str) else body
        request = HTTPRequest(**params)
        try:
            response = yield http_client.fetch(request)
        except HTTPError as e:
            # info('========================')
            # info('HTTTP error returned... ')
            # info('Code: ' + str(e.code))
            if e.response:
                # info('URL: ' + str(e.response.effective_url))
                # info('Reason: ' + str(e.response.reason))
                # info('Body: ' + str(e.response.body))
                response = e.response
            else:
                response = e
            # info('========================')
        except Exception as e:
            # info('========================')
            # Other errors are possible, such as IOError.
            # info("Other Errors: " + str(e))
            response = e
            # info('========================')

        if not raw_response:
            retresp = dict()

            if hasattr(response, 'code'):
                retresp['status_code'] = response.code
            if hasattr(response, 'reason'):
                retresp['reason'] = response.reason
            if hasattr(response, 'body'):
                try:
                    retresp['data'] = loads(response.body.decode('utf-8'))
                except Exception as e:
                    # info('========================')
                    # info(e)
                    retresp['data'] = {}
                    # info('========================')
            if hasattr(response, 'message'):
                retresp['message'] = response.message
            else:
                # info('Response: ',response)
                # info('Retresp: ',retresp)
                if 'data' in retresp.keys():
                    retresp['message'] = retresp['data']
                else:
                    retresp['message'] = ''
            callback(retresp)
        else:
            callback(response)

    @asynchronous
    @engine
    def upload_file(self, url, fields=None, files=None, headers=None, keg=False, curl=True, callback=None):
        if curl:
            AsyncHTTPClient.configure(
                "tornado.curl_httpclient.CurlAsyncHTTPClient")
        http_client = AsyncHTTPClient()
        boundary = uuid4().hex
        dictheaders = {
            'Content-Type': 'multipart/form-data; boundary=%s' % boundary}
        producer = partial(multipart_producer, boundary, files)
        if hasattr(self, 'VAT') and self.VAT:
            dictheaders['Venidera-AuthToken'] = self.VAT
        # Check cross call
        if 'CROSS_KEY' in self.settings.keys():
            crosskey = self.settings['CROSS_KEY']
            crosstoken = create_signed_value(
                crosskey, 'crosstoken', str(datetime.utcnow().timestamp()))
            crosstoken = token_encode(crosstoken.decode('utf-8'), crosskey)
            info('Cross token added to the HTTP request.')
            dictheaders['Cross-Key'] = crosstoken
        else:
            info('\n\nConfigure CROSS_KEY for call to the VPC\n')
        dictheaders['Data-Fields'] = quote(dumps(fields))
        # KEG UPLOAD
        if keg and 'KEG_KEY' in self.settings.keys():
            # KEG the headers
            dictheaders['Vat'] = self.keg_it(dictheaders['Venidera-AuthToken'])
            dictheaders['Keg'] = self.keg_it(
                str(datetime.utcnow().timestamp()))
            # Keg-Mode: This will tell to KEG avoid unkeg of the request's body
            dictheaders['Keg-Mode'] = str(uuid4())
            del dictheaders['Venidera-AuthToken']
        else:
            if keg:
                info('\n\nConfigure KEG_KEY to call the Barrel\n')
        h = HTTPHeaders(dictheaders)
        params = {
            'headers': h,
            'url': url,
            'method': 'POST',
            'request_timeout': 720,
            'validate_cert': False,
            'body_producer': producer,
            'allow_nonstandard_methods': True}
        request = HTTPRequest(**params)
        try:
            response = yield http_client.fetch(request)
        except HTTPError as e:
            info('HTTTP error returned... ')
            info('Code: ' + str(e.code))
            if e.response:
                info('URL: ' + str(e.response.effective_url))
                info('Reason: ' + str(e.response.reason))
                info('Body: ' + str(e.response.body))
                response = e.response
            else:
                response = e
        except Exception as e:
            # Other errors are possible, such as IOError.
            info("Other Errors: " + str(e))
            response = e
        callback(response)

    def response(self, code, message="", data=None, headers=None, parse=None):
        output_response = {'status': None, 'message': message}
        if parse:
            data = self.datetime_to_isoformat(data)
        if data != None:
            output_response['data'] = data
        if code < 300:
            output_response['status'] = 'success'
        elif code >= 300 and code < 400:
            output_response['status'] = 'redirect'
        elif code >= 400 and code < 500:
            output_response['status'] = 'error'
        else:
            output_response['status'] = 'fail'
        if headers and isinstance(headers, dict):
            for k, v in headers.items():
                self.add_header(k, v)
        self.set_status(code)
        self.set_json_output()
        self.write(self.json_encode(output_response))
        self.finish()

    def datetime_to_isoformat(self, object):
        try:
            if isinstance(object, list):
                return [self.datetime_to_isoformat(obj) for obj in object]
            elif isinstance(object, dict):
                return {key: self.datetime_to_isoformat(val) for key, val in object.items()}
            else:
                if isinstance(object, datetime):
                    try:
                        return object.isoformat()
                    except Exception as e:
                        return object
                else:
                    return object
        except Exception as e:
            return object

    # Default date is UTC datetime
    def isoformat_to_datetime(self, object):
        try:
            if isinstance(object, list):
                return [self.isoformat_to_datetime(obj) for obj in object]
            elif isinstance(object, dict):
                return {key: self.isoformat_to_datetime(val) for key, val in object.items()}
            else:
                if isinstance(object, str):
                    try:
                        return parse(object)
                    except Exception as e:
                        return object
                else:
                    return object
        except Exception as e:
            return object
