import os
from tornado.gen import engine, coroutine, Task
from handlers.base import BaseHandler
from handlers.api_trello import TrelloApiHandler
from json import dumps
from logging import info
from datetime import datetime
from requests import post
from io import BytesIO
from bson import ObjectId as ObjId
import re
from vmail import sender
from string import Template
from data_models import Activity
from vdecorators import api_authenticated, check_credentials


class ApplicationsHandler(BaseHandler):
    """ Handler to Applications resources """

    SUPPORTED_METHODS = ("GET")

    @coroutine
    @api_authenticated
    def get(self):
        """ Return applications list """

        apps = yield self.Applications.find({}).to_list(None)
        if apps:
            msg = 'Foi encotrado 1 aplicação cadastrada.'
            if len(apps) > 1:
                msg = 'Foram encontrados %s aplicações cadastradas' % len(apps)
            app_names = [{
                'name': app['name'], 'id': app['_id'], 'url': app['info']['url'],
                'manager': (app['info']['manager'] if 'manager' in app['info'] else None) } for app in apps]

            self.response(200, msg, {'apps': app_names}, None, True)
        else:
            self.response(
                404, 'Não foi encontrado nenhuma aplicação cadastrada.', apps)


class OrganizationsHandler(BaseHandler):
    """ Handler to Organizations resources """

    SUPPORTED_METHODS = ("GET")

    @coroutine
    @api_authenticated
    def get(self):
        """ Return organizations list """

        org = self.current_user['organization']
        if org == 'Prox_suporte':
            organizations = yield self.Organizations.find({}).to_list(None)
        else:
            organizations = yield self.Organizations.find(
                {'$or': [
                    {'nickname': 'Prox_suporte'},
                    {'nickname': org}]}).to_list(None)

        if organizations:
            msg = 'Foi encotrado 1 organização cadastrada.'
            if len(organizations) > 1:
                msg = ('Foram encontrados %s organizações cadastradas'
                       % len(organizations))
            orgs = [{
                'name': org['name'],
                'nickname': org['nickname']} for org in organizations]
            self.response(200, msg, {'organizations': orgs}, None, True)
        else:
            self.response(
                404, 'Não foi encontrado nenhuma organização cadastrada.', [])


class ActivitiesHandler(TrelloApiHandler):
    """ Handler to Activities resources """

    SUPPORTED_METHODS = ("POST", "GET", "PUT", "DELETE")

    @coroutine
    @api_authenticated
    def post(self):
        """ Create a activity """

        """ adjust input data """
        self.input_data, trello_data = yield Task(self.adjust_input_data, self.input_data)
        """ create a trello card with activity """
        code, input_data = yield Task(self.create_card_in_trello, trello_data)

        ouser = yield self.TrelloUsers.find_one({'email': 'suporte.prox@venidera.com'})
        config = yield self.TrelloConfig.find_one({'version': self.trello['version']})
        timeline = self.input_data['timeline'][-1]
        index = timeline['index'] + 1
        activity_type = self.input_data['activity_type']
        activity_phase = config['phases'][activity_type][index]
        self.input_data['trello_config_version'] = self.trello['version']

        # Sending e-mail with notification to the client
        current_user = yield self.Users.find_one(
            {'email': self.current_user['username']})

        # send email from production or develop to risk3
        send_email = True if (
            (os.environ.get('GITHUB_BRANCH', 'develop') == 'master') or
            (os.environ.get('GITHUB_BRANCH', 'develop') in ['develop', 'release']
                and '@venidera.com' in current_user['email'])) else False

        # email sender
        fromaddr=self.settings['PROX_SUPORTE_EMAIL_FROM']
        if code == 200:
            self.input_data = dict(self.input_data , **input_data)

            message_text = "Muito obrigado por entrar em contato conosco.\n" +\
                "A sua solicitação de suporte já foi designada ao nosso gerente.\n" +\
                "Ele entrará em contato com você nas próximas 24h para definir um prazo para a sua solicitação.\n\n";
            posts = [{
                'date': datetime.now(),
                'user': ouser['email'],
                'comment': message_text
            }]

            tm = {
                'index': index,
                'phase': activity_phase['name'],
                'user': ouser['email'],
                'date': datetime.now(),
                'posts': posts
            }

            self.input_data['timeline'].append(tm)

            if send_email:
                # Capturing template
                template = Template(open(
                    './app/templates/email/customer_notice.html', 'r').read())
                emailTo = config['notification_emails'].copy()
                emailTo.append(
                    {'email': current_user['email'], 'fullname': current_user['fullname']})
                for user in emailTo:
                    msg_body = template.substitute(
                        fullname=user['fullname'], link_suporte=self.settings['APPURL'],
                        card_title=self.input_data['title'], message=message_text)
                    info(msg_body)
                    sender.send_email(toaddr=user['email'], fromaddr=fromaddr,
                        subject=input_data['title'], message=msg_body, is_html=True)
            else:
                info('não enviando email: %s' % current_user['email'])
        else:
            message_text = """
                Infelizmente houve um erro interno e não conseguimos seguir por aqui.\n
                Favor enviar um email para %s
                """
            message_text = message_text % (ouser['email'])
            post = {
                'date': datetime.now(),
                'user': ouser['email'],
                'comment': message_text
            }
            self.input_data['timeline'][-1]['posts'].append(post)

            """ Se errro, enviar mensagem para suporte """
            templ = Template(open(
                './app/templates/email/system_error.html', 'r').read())
            user = yield self.Users.find_one({'email': 'vanessa.sena@venidera.com'})
            emailTo = config['notification_emails'].copy()
            emailTo.append({'email': user['email'], 'fullname': user['fullname']})

            # Send Error Message
            for user in emailTo:
                body = templ.substitute(nome=user['fullname'], message=message_text)
                info(body)
                sender.send_email(
                    toaddr=user['email'], fromaddr=fromaddr,
                    subject='Suporte: Não foi possível criar a solicitação de suporte.',
                    message=body, is_html=True)

            if send_email:
                # Capturing template
                template = Template(open(
                    './app/templates/email/system_error.html', 'r').read())
                emailTo = config['notification_emails']
                emailTo.append(
                    {'email': current_user['email'], 'fullname': current_user['fullname']})
                for user in emailTo:
                    msg_body = template.substitute(nome=user['fullname'], message=message_text)
                    info(msg_body)
                    sender.send_email(toaddr=user['email'], fromaddr=fromaddr,
                        subject=input_data['title'], message=msg_body, is_html=True)
            else:
                info('não enviando email: %s' % current_user['email'])

        """ adding a activity to the mongo db """
        response = yield Task(self.insert_object, objmodel=Activity)

        """ adjusts in the response data """
        self.throw_message(response, 'POST', Activity)

    @coroutine
    @api_authenticated
    def get(self, oid=None):
        """ Return activities list """

        """ get activities data from mongo and return """
        response = yield Task(self.get_objects, objmodel=Activity, oids=oid)
        """ adjusts in the response data """

        self.throw_message(response, 'GET', Activity)

    @coroutine
    @api_authenticated
    def put(self, oid=None):
        """ Update a activity """

        """ adjust input data """
        self.input_data, trello_data = yield Task(self.adjust_input_data, self.input_data)
        resp, data = yield Task(self.validate_inputs, oid)
        if resp:
            """ adjust input date data """
            self.input_data = self.isoformat_to_datetime(self.input_data)

            """ update activity in mongo database """
            response = yield Task(
                self.update_object, objmodel=Activity, oids=oid)

            """ update activity data in trello """
            yield Task(self.update_card_in_trello, trello_data)

            """ adjusts in the response data """
            self.throw_message(response, 'PUT', Activity)
        else:
            config = yield self.TrelloConfig.find_one({'version': self.trello['version']})
            activities = yield Task(self.get_objects, objmodel=Activity, oids=oid)
            output = {
                'config': config,
                'activities': activities
            }
            self.response(200, 'Nothing to change.', output)

    @coroutine
    @api_authenticated
    def delete(self, oid=None):
        """ Delete a activity from database """

        token = self.get_argument('token', None)
        if token:
            """ if token, get all images to remove """
            attachments = yield Task(self.get_attachments, {'_id': ObjId(oid)})
            attachment_list = yield Task(
                self.get_attachments, {'_id': {'$ne': ObjId(oid)}})
            delete_list = [d for d in attachments if d not in attachment_list]
            for d in delete_list:
                """ remove all attachments of from filemanager before remove activity """
                response = yield Task(self.deleteFile, checksum=d)
                if (response['status'] and 'data' in response and
                    'token' in response['data']):
                    response = yield Task(
                        self.deleteFile, checksum=d,
                        token=response['data']['token'])
        """ remove activity (return token in first delete) """
        response = yield Task(
            self.delete_object, objmodel=Activity,
            oids=oid, authorizetoken=self.redis)

        if token and response:
            """ if token, remove trello card """
            # yield Task(self.delete_card_from_trello, response)
            yield Task(self.archive_card_from_trello, response, 'true')

        self.throw_message(response, 'DELETE', Activity)


class FilesUploadHandler(BaseHandler):
    """ Handler to upload files """

    SUPPORTED_METHODS = ("POST")

    @coroutine
    @check_credentials
    def prepare(self):
        info('Prepare Upload Phase completed!')

    @coroutine
    @api_authenticated
    def post(self):
        """ Upload files """
        if self.request.files:
            api_url = self.settings['FILES'] + '/files'
            resp = yield Task(self.send_file, api_url)
            if resp.status_code == 200 or resp.status_code == 409:
                self.response(
                    resp.status_code,
                    resp.json()['message'],
                    resp.json()['data'])
            else:
                self.response(resp.status_code, resp.json()['message'])
        else:
            self.response(400, 'Invalid request.')

    @engine
    def send_file(self, url, callback=None):
        fileobj = self.request.files['file'][0]
        dictheaders = {'File-Service': self.settings['SERVICE_NAME']}
        pfile = (
            fileobj['filename'],
            BytesIO(fileobj['body']),
            fileobj['content_type'])
        resp = post(
            url=url,
            files={'file': pfile},
            headers=dictheaders,
            auth=self.rewrite_request(fileobj['filename']))
        callback(resp)

    def rewrite_request(self, filename):
        def prep(obj, filename):
            filename = filename.encode('utf-8')
            pattern = r'filename\*=.*'.encode('utf-8')
            replacer = 'filename='.encode('utf-8') + filename
            obj.body = re.sub(pattern, replacer, obj.body)
            return obj
        return lambda obj: prep(obj, filename)

    def dumps(self, x):
        return dumps(x, default=self.encoding)

    def encoding(self, d):
        if isinstance(d, bytes):
            return d.decode('utf-8')
        elif isinstance(d, datetime):
            return d.isoformat()
        else:
            return str(d)


class CrossActivitiesHandler(ActivitiesHandler):
    """ Handler to Activities resources from cross handlers """

    SUPPORTED_METHODS = ('POST')

    def check_xsrf_cookie(self):
        pass