# !/usr/bin/env python3

from json import loads, dumps
from tornado.web import RequestHandler, asynchronous
from tornado.gen import coroutine, engine, Task
from bson import ObjectId as ObjId
from logging import info
import string
from vdecorators import prepare_json
from vdecorators import check_credentials
from handlers.mongoDBCRUD import MongoDBCRUD
from handlers.http import HTTPUtils

from vdecorators import api_authenticated
from data_models import Activity
import redis


class BaseHandler(RequestHandler, HTTPUtils, MongoDBCRUD):
    """A class to collect common handler methods - all other handlers should
    inherit this one.
    """

    def initialize(self):
        # Connecting to a local redis
        self.redis = redis.StrictRedis.from_url(
            "%s/%d" % (self.settings['redisdb_uri'], 0))

        # Allows dynamic connections using object models

        self.Applications = self.settings['db'].applications
        self.Organizations = self.settings['db'].organizations
        self.Users = self.settings['db'].users
        self.Activities = self.settings['db'].activities
        self.Deleted_Activities = self.settings['db'].deleted_activities
        self.TrelloUsers = self.settings['db'].trello_users
        self.TrelloConfig = self.settings['db'].trello_config

        models = [Activity]

        self.connmodels = dict()
        for model in models:
            conn1 = self.settings['db'][model.collection()]
            self.connmodels[model.collection()] = conn1
            conn2 = self.settings['db']['deleted_%s' % model.collection()]
            self.connmodels['deleted_%s' % model.collection()] = conn2

        self.trello = self.settings['trello']
        self.scheduler = self.settings['scheduler']

    @coroutine
    @prepare_json
    @check_credentials
    def prepare(self):
        info('Prepare phase completed!')

    def get_current_user(self):
        return self.current_user

    def sanitizestr(self, strs):
        txt = "%s%s" % (string.ascii_letters, string.digits)
        return ''.join(c for c in strs if c in txt)

    def json_encode(self, value):
        return dumps(value, default=str).replace("</", "<\\/")

    def set_default_headers(self):
        self.set_header('Content-Type', 'text/html; charset=UTF-8')

    def set_json_output(self):
        self.set_header('Content-Type', 'application/json; charset=UTF-8')

    def write_error(self, status_code, **kwargs):
        if status_code == 404:
            self.response(status_code, 'Resource not found. Check the URL.')
        elif status_code == 405:
            self.response(
                status_code,
                'Method not allowed in this resource. Check your verb '
                '(GET, POST, PUT and DELETE)')
        else:
            self.response(status_code, 'Internal server error.')

    @engine
    def read_cache(self, key, callback=None):
        key = 'cache:' + str(key)
        cache = self.redis.get(key)
        if cache:
            cache = loads(cache)
        callback(cache)

    @engine
    def write_cache(self, key='', data='', expiration_s=120, callback=None):
        key = 'cache:' + str(key)
        rresult = self.redis.set(
            name=key, value=dumps(data, default=str), ex=expiration_s)
        callback(rresult)

    @engine
    def clear_cache(self, callback=None):
        lkeys = self.redis.keys('cache:*' + self.settings['APPURL'] + '*')
        for k in lkeys:
            self.redis.delete(k)
        callback(True)

    @asynchronous
    @engine
    def throw_message(self, result, verb, objmodel):
        dc = {
            'POST': ['added', 'added'],
            'GET': ['found', 'returned'],
            'PUT': ['updated', 'updated'],
            'DELETE': ['deleted', 'deleted'],
            'PATCH': ['recovered', 'recovered']
        }

        coll = self.get_key(objmodel)
        if result:
            if isinstance(result, dict):
                result = [result]
            if verb == 'GET':
                config = yield self.TrelloConfig.find_one(
                    {'version': self.trello['version']})
                org = self.current_user['organization']
                if org != 'Prox_suporte':
                    result = [d for d in result if
                              (org in d['organizations'] and d['closed'] == False)]

                outputs = [self.parse_output(obj, objmodel) for obj in result]
                config['admin'], activities = yield Task(
                    self.adjusts_output_activities, outputs)
                output = {
                    'config': config,
                    'activities': activities
                }
                llen = len(output['activities'])
            elif verb == 'DELETE':
                outputs = [self.parse_output(obj, objmodel) for obj in result]
                admin, output = yield Task(
                    self.adjusts_output_activities, outputs)
                llen = len(output)
                if llen == 1:
                    output = output[0]
            else:
                config = yield self.TrelloConfig.find_one({'version': self.trello['version']})
                outputs = [self.parse_output(obj, objmodel) for obj in result]
                admin, activities = yield Task(
                    self.adjusts_output_activities, outputs)
                llen = len(activities)
                if llen == 1:
                    activities = activities[0]
                output = {
                    'config': config,
                    'activities': activities
                }
            self.response(200, 'Your operation %s %d %s.' % (
                dc[verb][1], llen, coll if llen > 1 else coll[:-1]),
                output, None, True)
            return
        else:
            output = dict()
            if verb == 'GET':
                config = yield self.TrelloConfig.find_one({'version': self.trello['version']})
                output = {
                    'config': config,
                    'activities': []
                }
            self.response(
                200, 'No %s %s.' % (coll, dc[verb][0]), output, None, True)
            return

    @engine
    def adjusts_output_activities(self, activities, callback=None):
        """ Adjusts response activities """

        org = self.current_user['organization']
        for activity in activities:
            activity_status = activity['activity_status']
            email = activity_status['user']
            user = yield self.Users.find_one({'email': email}, {'avatar': 0})
            activity_status['user'] = {
                'name': user['fullname'],
                'email': email,
                'organization': user['organization']}
            app_id = activity['module']
            application = yield self.Applications.find_one(
                {'_id': ObjId(app_id)})
            activity['module'] = {
                'id': application['_id'],
                'name': application['name']
            }
            timeline = activity['timeline']
            for item in timeline:
                email = item['user']
                user = yield self.Users.find_one({'email': email})
                item['user'] = {
                    'name': user['fullname'], 'email': email,
                    'organization': user['organization']}
                for post in item['posts']:
                    email = post['user']
                    user = yield self.Users.find_one({'email': email})
                    post['user'] = {
                        'name': user['fullname'],
                        'email': email,
                        'organization': user['organization']}
                    if 'attachment' in post and post['attachment']:
                        file_checksum = post['attachment']['file_checksum']
                        pfile = yield Task(self.getFile, file_checksum)
                        if pfile:
                            post['attachment']['file'] = {
                                'url': pfile['url'],
                                'checksum': pfile['checksum']}
                        else:
                            post['attachment']['file'] = {
                                'url': '', 'checksum': ''}
                        del post['attachment']['file_checksum']
                        if ('thumb_checksum' in post['attachment']
                                and post['attachment']['thumb_checksum']):
                            thumb_checksum = (
                                post['attachment']['thumb_checksum'])
                            thumbnail = yield Task(
                                self.getFile, thumb_checksum)
                            if thumbnail:
                                post['attachment']['thumbnail'] = {
                                    'url': thumbnail['url'],
                                    'checksum': thumbnail['checksum']}
                            else:
                                post['attachment']['thumbnail'] = {
                                    'url': '', 'checksum': ''}
                            del post['attachment']['thumb_checksum']

            if org != 'Prox_suporte':
                del activity['created_by']
                del activity['organizations']
        # resp = (org == 'Prox_suporte' and user['role'] == 'Administrator'), activities
        resp = (
            org == 'Prox_suporte' and self.current_user['role'] == 'Administrator'), activities
        callback(resp)

    @engine
    def getFile(self, checksum, callback=None):
        """ Get file from file manager """

        api_url = self.settings['FILES'] + '/files/' + checksum
        headers = {'Content-type': 'application/json'}
        response = yield Task(
            self.http_call,
            url=api_url,
            method='GET',
            headers=headers)
        data = dict()
        if response.code == 200:
            resp = loads(response.body.decode('utf-8'))
            data = resp['data'][0]
        callback(data)

    @engine
    def deleteFile(self, checksum=None, token=None, callback=None):
        """ Delete file from filemanager """

        resp = dict()
        if checksum:
            api_url = self.settings['FILES'] + '/files/' + checksum
            if token:
                api_url += '?token=' + token['id']
            response = yield Task(
                self.http_call,
                url=api_url,
                method='DELETE',
                headers={
                    'Content-type': 'application/json',
                    'File-Service': self.settings['SERVICE_NAME'],
                })
            resp = loads(response.body.decode('utf-8'))
            resp['status'] = response.code
        callback(resp)

    @engine
    def validate_inputs(self, id, callback=None):
        """ Validate input data before save on databse """

        org = self.current_user['organization']
        resp = True
        input_data = self.input_data
        if org != 'Prox_suporte' and ('activity_phase' not in self.input_data or
                                      ('activity_phase' in self.input_data and
                                       self.input_data['activity_phase'] != 'aprovado')):
            resp = False
            input_data = {}
            activity = yield self.Activities.find_one({'_id': ObjId(id)})
            if 'timeline' in self.input_data.keys():
                timeline = self.input_data['timeline']
                if len(timeline) == len(activity['timeline']):
                    resp = True
                    input_data['timeline'] = timeline
            if 'activity_status' in self.input_data.keys():
                activity_status = self.input_data['activity_status']
                if 'status' in activity_status and \
                        activity_status['status'] == 'finalizado':
                    resp = True
                    input_data['activity_status'] = activity_status
        response = resp, input_data
        callback(response)

    @engine
    def adjust_input_data(self, input_data, callback=None):
        """ Adjusts input data before save on database """

        trello_data = input_data['trello_data'] if 'trello_data' in input_data else {
        }
        data = input_data['data']
        if ('module' in data.keys()
                and 'id' in data['module'].keys()):
            data['module'] = data['module']['id']
        if 'timeline' in data.keys():
            timeline = data['timeline']
            for item in timeline:
                for post in item['posts']:
                    if 'attachment' in post and post['attachment']:
                        if 'file' in post['attachment']:
                            post['attachment']['file_checksum'] = (
                                post['attachment']['file']['checksum'])
                            del post['attachment']['file']
                        if 'thumbnail' in post['attachment']:
                            post['attachment']['thumb_checksum'] = (
                                post['attachment']['thumbnail']['checksum'])
                            del post['attachment']['thumbnail']
        resp = (data, trello_data)
        callback(resp)

    @engine
    def get_attachments(self, query=None, callback=None):
        """ Get attachments from activities """

        attachments = list()
        if query:
            activities = yield self.Activities.find(query).to_list(None)
            for activity in activities:
                for timeline in activity['timeline']:
                    for post in timeline['posts']:
                        if 'attachment' in post and post['attachment']:
                            if ('file_checksum' in post['attachment'] and
                                    post['attachment']['file_checksum']):
                                attachments.append(
                                    post['attachment']['file_checksum'])
                            if ('thumb_checksum' in post['attachment'] and
                                    post['attachment']['thumb_checksum']):
                                attachments.append(
                                    post['attachment']['thumb_checksum'])
        callback(attachments)


class VersionHandler(BaseHandler):
    SUPPORTED_METHODS = ("GET")

    @api_authenticated
    def get(self):
        self.response(200, message=self.settings['version'])
