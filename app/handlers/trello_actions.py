import logging
import os
from tornado.gen import engine, Task
from handlers.api_trello import TrelloApiHandler
from handlers.vmail import sender
from string import Template
from copy import deepcopy
from dateutil import parser
from json import dumps, loads
from operator import itemgetter
from datetime import datetime
from dateutil.relativedelta import relativedelta
from data_models import Activity


class TrelloActionsHandler(TrelloApiHandler):
    """ Handler to Activities resources """

    @engine
    def trello_actions(self):

        type = self.input_data['action']['type']
        data = self.input_data['action']['data']
        resp = False
        if type == 'updateCard':
            resp, store_msg = yield Task(self.__update_card_action_for_activity)
        elif (type == 'commentCard' and '#client' in data['text']):
            resp, store_msg = yield Task(self.__comment_card_action_for_activity)
        elif (type == 'updateComment' and '#client' in data['action']['text']):
            resp, store_msg = yield Task(self.__update_comment_action_for_activity)
        elif (type == 'deleteComment'):
            resp, store_msg = yield Task(self.__delete_comment_action_for_activity)
        elif (type == 'updateCheckItem'):
            resp, store_msg = yield Task(self.__update_checkitem_action, status=False)
        elif (type == 'updateCheckItemStateOnCard'):
            resp, store_msg = yield Task(self.__update_checkitem_action, status=True)
        """
        elif type == 'deleteCard':
            self.__delete_card_action_for_activity()
        """

        if resp:
            self.trello['store'].submit(store_msg)

    @engine
    def __update_checkitem_action(self, status=False, callback=None):
        """ Update the Checklist Fases Item checks """

        resp = False, {}

        if status:
            checklist = self.input_data['action']['data']['checklist']

            if checklist['name'] == 'Atividades':
                checkItem = self.input_data['action']['data']['checkItem']

                if checkItem['state'] == 'complete':
                    """ check item checked, post message """
                    resp = yield Task(self.__post_automated_messages,
                                      trello_data=self.input_data,
                                      item_name=checkItem['name'])
                else:
                    """ check item unchecked, remove message """
                    card_id = self.input_data['model']['id']
                    resp = yield Task(self.__remove_automated_message,
                                      card_id=card_id)
                    logging.info('Nada a fazer. Check desmarcado.')
            else:
                logging.info('Sem Checklist.')
        else:
            logging.info('status: %s.', status)

        callback(resp)

    @engine
    def __post_automated_messages(self, trello_data=None, item_name=None, callback=None):
        """  """

        resp = False, {}

        if not trello_data or not item_name:
            callback(resp)

        """ Get automated messages from model """
        config = yield self.TrelloConfig.find_one({'version': self.trello['version']})
        if item_name in config['automatic_posts']:
            """ card id """
            card_id = trello_data['model']['id']
            input_data = deepcopy(self.input_data)

            if config['version'] < "1.2":
                if 'action' in config['automatic_posts'][item_name] and\
                        config['automatic_posts'][item_name]['action'] == 'finalizar':
                    store = resp[1]
                    if isinstance(store, str):
                        store = loads(store)
                    resp = yield Task(self.__run_action_to_finish, card_id=card_id,
                                      input_data=input_data, store=store)

                elif 'message' in config['automatic_posts'][item_name]:
                    message_text = config['automatic_posts'][item_name]['message']
                    if 'params' in config['automatic_posts'][item_name]:
                        """ replace %s with data (email/date) """
                        if config['automatic_posts'][item_name]['params'] == 'due_date':
                            due_date = parser.parse(
                                trello_data['model']['due']).strftime('%d/%m/%Y')
                            message_text = message_text % (due_date)
                        elif config['automatic_posts'][item_name]['params'] == 'suporte_email':
                            message_text = message_text % (
                                'suporte_prox@venidera.com')
                    resp = yield Task(self.__publish_message, card_id=card_id,
                                      comment=message_text, input_data=input_data)
                    if not resp[0]:
                        """ Se errro, enviar mensagem para suporte """
                        message = 'modelo: ' + \
                            trello_data['model']['name'] + \
                            '.\n mensagem: ' + message_text
                        template = Template(open(
                            './app/templates/email/system_error.html', 'r').read())
                        user = yield self.Users.find_one({'email': 'vanessa.sena@venidera.com'})
                        emailTo = config['notification_emails'].copy()
                        emailTo.append(
                            {'email': user['email'], 'fullname': user['fullname']})
                        fromaddr = self.settings['PROXIMIDADE_SUPORTE_EMAIL_FROM']

                        # Send Error Message
                        for user in emailTo:
                            body = template.substitute(
                                nome=user['fullname'], message=message)
                            logging.info(body)
                            sender.send_email(
                                toaddr=user['email'], fromaddr=fromaddr,
                                subject='Suporte: Não foi possível avisar o cliente.',
                                message=body, is_html=True)
            else:
                if 'action' in config['automatic_posts'][item_name] and\
                        config['automatic_posts'][item_name]['action'] == 'finalizar':
                    store = resp[1]
                    if isinstance(store, str):
                        store = loads(store)
                    resp, store = yield Task(self.__run_action_to_finish, card_id=card_id,
                                             input_data=input_data, store=store)
                    if resp:
                        self.trello['store'].submit(store)

                if 'message' in config['automatic_posts'][item_name]:
                    message_text = config['automatic_posts'][item_name]['message']
                    if 'params' in config['automatic_posts'][item_name]:
                        """ replace %s with data (email/date) """
                        if config['automatic_posts'][item_name]['params'] == 'due_date':
                            due_date = parser.parse(
                                trello_data['model']['due']).strftime('%d/%m/%Y')
                            message_text = message_text % (due_date)
                        elif config['automatic_posts'][item_name]['params'] == 'suporte_email':
                            message_text = message_text % (
                                'suporte_prox@venidera.com')
                    resp = yield Task(self.__publish_message, card_id=card_id,
                                      comment=message_text, input_data=input_data)
                    if not resp[0]:
                        """ Se errro, enviar mensagem para suporte """
                        message = 'modelo: ' + \
                            trello_data['model']['name'] + \
                            '.\n mensagem: ' + message_text
                        template = Template(open(
                            './app/templates/email/system_error.html', 'r').read())
                        user = yield self.Users.find_one({'email': 'vanessa.sena@venidera.com'})
                        emailTo = config['notification_emails'].copy()
                        emailTo.append(
                            {'email': user['email'], 'fullname': user['fullname']})
                        fromaddr = self.settings['PROXIMIDADE_SUPORTE_EMAIL_FROM']

                        # Send Error Message
                        for user in emailTo:
                            body = template.substitute(
                                nome=user['fullname'], message=message)
                            logging.info(body)
                            sender.send_email(
                                toaddr=user['email'], fromaddr=fromaddr,
                                subject='Suporte: Não foi possível avisar o cliente.',
                                message=body, is_html=True)

                if 'trello_msg' in config['automatic_posts'][item_name]:
                    yield Task(self.update_card_in_trello, {
                        'id': card_id,
                        'post': {'comment': config['automatic_posts'][item_name]['trello_msg']}
                    })
        callback(resp)

    @engine
    def __run_action_to_finish(self, card_id=None, input_data=None,
                               store=None, callback=None):
        """ Updating Activity Status to Finalizado """

        resp = False, store
        if not card_id:
            callback(resp)

        """ find activity by card id """
        activity = yield self.Activities.find_one(
            {'trello_cardId': {'$eq': card_id}})

        if activity:
            """ get the user who commented on trello """
            trello_user = yield Task(self.get_trello_user,
                                     input_data['action']['memberCreator'])

            llist = [l for l in self.trello['card_lists']
                     if l['name'] == 'Finalizados']
            if len(llist):
                llist = llist[0]
                card = self.trello['api'].put(
                    resource='cards',
                    card_id=card_id,
                    params={'idList': llist['id']}
                )

                # scheduling to remove webhook
                # """ Remove a webhook to monitor card """
                logging.info(card_id)
                if card_id:
                    webhook = yield Task(self.get_webhook, id_model=card_id)
                    logging.info(webhook)
                    if webhook and 'id' in webhook:
                        rundate = datetime.now() + relativedelta(minutes=1)
                        # rundate = datetime.now() + relativedelta(seconds=10)
                        logging.info(
                            '%s: programando para excluir at %s %s', datetime.now(), rundate, card_id)
                        # self.scheduler.add_job(
                        #     TrelloApiHandler.schedule_delete_webhook, 'date', run_date=rundate,
                        #     args=(self, webhook['id']), id='process_data')
                        self.scheduler.add_job(
                            TrelloApiHandler.schedule_delete_webhook, 'date', run_date=rundate,
                            args=(self, webhook['id']), id='process_data')

            self.input_data = {
                'activity_status': {
                    'status': 'finalizado',
                    'user': trello_user['email'],
                    'date': input_data['action']['date']
                }
            }

            oid = str(activity['_id'])
            response = yield Task(
                self.update_object, objmodel=Activity, oids=oid)

            activity_status = self.datetime_to_isoformat(
                self.input_data['activity_status'])

            store = {
                'tipo': 'run_action_to_finish',
                'id': oid,
                'data': activity_status
            }

            resp = True, dumps(store)

        callback(resp)

    @engine
    def __publish_message(self, card_id=None, comment=None,
                          input_data=None, callback=None):
        """ Adding Message to Suporte """

        resp = False, {}

        if not card_id or not comment:
            callback(resp)

        """ find activity by card id """
        activity = yield self.Activities.find_one(
            {'trello_cardId': {'$eq': card_id}})

        if activity and 'timeline' in activity:
            oid = str(activity['_id'])

            """ get timeline id """
            timeline = activity['timeline']
            tl = max(timeline, key=itemgetter('index'))
            id = timeline.index(tl)

            # """ get the user who commented on trello """
            trello_user = yield Task(self.get_trello_user,
                                     input_data['action']['memberCreator'])

            """ create a post and append in the timeline"""
            post = {
                'date': input_data['action']['date'],
                'user': trello_user['email'],
                'comment': comment,
                'action_id': [input_data['action']['data']['checkItem']['id']]
            }
            timeline[id]['posts'].append(post)

            """ update activity object with new post """
            self.input_data = {'timeline': timeline}

            response = yield Task(
                self.update_object, objmodel=Activity, oids=oid)

            user = yield self.Users.find_one({'email': trello_user['email']})
            post['user'] = {
                'name': user['fullname'],
                'email': user['email'],
                'organization': user['organization']
            }

            post = self.datetime_to_isoformat(post)

            config = yield self.TrelloConfig.find_one({'version': self.trello['version']})

            """ send email to client """
            # Sending e-mail with notification to the client
            if ((os.environ.get('GITHUB_BRANCH', 'develop') == 'master') or
                (os.environ.get('GITHUB_BRANCH', 'develop') in ['develop', 'release']
                    and '@venidera.com' in activity['created_by'])):
                fromaddr = self.settings['PROXIMIDADE_SUPORTE_EMAIL_FROM']
                template = Template(open(
                    './app/templates/email/customer_notice.html', 'r').read())
                user = yield self.Users.find_one({'email': activity['created_by']})
                emailTo = config['notification_emails'].copy()
                emailTo.append(
                    {'email': user['email'], 'fullname': user['fullname']})
                for user in emailTo:
                    body = template.substitute(
                        fullname=user['fullname'], link_suporte=self.settings['APPURL'],
                        card_title=activity['title'], message=comment)
                    logging.info(body)
                    sender.send_email(toaddr=user['email'], fromaddr=fromaddr,
                                      subject=activity['title'], message=body, is_html=True)
            else:
                logging.info('não enviando email: %s' % activity['created_by'])

            store_dump = {'tipo': 'addComment', 'id': oid,
                          'timeline_id': id, 'data': post}
            resp = True, dumps(store_dump)

        callback(resp)

    @engine
    def __remove_automated_message(self, card_id=None, callback=None):
        """ Remove the message when unckeck a checklist item """

        resp = False, {}

        if not card_id:
            callback(resp)

        """ find activity by card id """
        activity = yield self.Activities.find_one(
            {'trello_cardId': {'$eq': card_id}})

        if activity and 'timeline' in activity:
            oid = str(activity['_id'])

            """ get timeline id """
            timeline = activity['timeline']

            action_id = self.input_data['action']['data']['checkItem']['id']

            ppost = [(id, pid) for (id, tl) in enumerate(timeline) for
                     (pid, post) in enumerate(tl['posts'])
                     if 'action_id' in post and action_id in post['action_id']]

            if ppost:
                """ Exist old action in atividade """

                id = ppost[0][0]
                pid = ppost[0][1]

                del timeline[id]['posts'][pid]

                """ update activity object with new post """
                self.input_data = {'timeline': timeline}

                response = yield Task(
                    self.update_object, objmodel=Activity, oids=oid)

                posts = []
                for post in timeline[id]['posts']:
                    ppost = yield Task(self.update_post, post)
                    posts.append(ppost)

                store_dump = {
                    'tipo': 'deleteComment', 'id': oid,
                    'timeline_id': id, 'data': posts}

                resp = True, dumps(store_dump)

        callback(resp)

    @engine
    def update_post(self, post=None, callback=None):
        """ Update user in timeline post to callback """
        upost = {}
        if post:
            email = post['user']
            ouser = yield self.Users.find_one({'email': email})
            if email:
                post['user'] = {
                    'name': ouser['fullname'],
                    'email': email,
                    'organization': ouser['organization']
                }
                upost = self.datetime_to_isoformat(post)

        callback(upost)

    @engine
    def __delete_comment_action_for_activity(self, callback=None):
        """ Update a activity after webhook actions """

        resp = False, {}

        """ get the trello card id from database """
        card_id = self.input_data['action']['data']['card']['id']

        """ find activity by card id """
        activity = yield self.Activities.find_one(
            {'trello_cardId': {'$eq': card_id}})

        if activity and 'timeline' in activity:
            oid = str(activity['_id'])

            """ get timeline id """
            timeline = activity['timeline']

            """ old action id of comment """
            action_id = self.input_data['action']['data']['action']['id']

            ppost = [(id, pid) for (id, tl) in enumerate(timeline) for
                     (pid, post) in enumerate(tl['posts'])
                     if 'action_id' in post and action_id in post['action_id']]

            if ppost:
                """ Exist old action in atividade """

                id = ppost[0][0]
                pid = ppost[0][1]

                del timeline[id]['posts'][pid]

                """ update activity object with new post """
                self.input_data = {'timeline': timeline}

                response = yield Task(
                    self.update_object, objmodel=Activity, oids=oid)

                posts = []
                for post in timeline[id]['posts']:
                    ppost = yield Task(self.update_post, post)
                    posts.append(ppost)

                store_dump = {
                    'tipo': 'deleteComment', 'id': oid,
                    'timeline_id': id, 'data': posts}

                resp = True, dumps(store_dump)

        callback(resp)

    @engine
    def __update_comment_action_for_activity(self, callback=None):
        """ Update a activity after webhook actions """

        resp = False, {}

        """ get the trello card id from database """
        card_id = self.input_data['action']['data']['card']['id']

        """ get the user who commented on trello """
        trello_user = yield Task(self.get_trello_user,
                                 self.input_data['action']['memberCreator'])

        """ find activity by card id """
        activity = yield self.Activities.find_one(
            {'trello_cardId': {'$eq': card_id}})

        if activity and 'timeline' in activity:
            oid = str(activity['_id'])

            """ get the id of the last timeline and the pid of the last post
                (in case there is no action_id) """
            timeline = activity['timeline']
            tl = max(timeline, key=itemgetter('index'))
            id = timeline.index(tl)
            pid = len(tl['posts']) - 1

            """ get comment message removind #client """
            comment = self.input_data['action']['data']['action']['text']
            comment = comment.replace("#cliente", "")

            """ old action id of comment """
            action_id = self.input_data['action']['data']['action']['id']

            ppost = [(id, pid) for (id, tl) in enumerate(timeline) for
                     (pid, post) in enumerate(tl['posts'])
                     if 'action_id' in post and action_id in post['action_id']]

            store_msg = ''
            if ppost:
                """ Exist old action in atividade """

                id = ppost[0][0]
                pid = ppost[0][1]

                post = {
                    'date': self.input_data['action']['date'],
                    'user': trello_user['email'],
                    'comment': comment,
                    'action_id': [action_id, self.input_data['action']['id']],
                    'edited': True
                }
                timeline[id]['posts'][pid] = post

            else:
                """ Not Exist old action in atividade """
                """ create a new post and append in the timeline"""
                post = {
                    'date': self.input_data['action']['date'],
                    'user': trello_user['email'],
                    'comment': comment,
                    'action_id': [action_id, self.input_data['action']['id']]
                }
                timeline[id]['posts'].append(post)

            """ update activity object with new post """
            self.input_data = {'timeline': timeline}

            response = yield Task(
                self.update_object, objmodel=Activity, oids=oid)

            post = yield Task(self.update_post, post)
            config = yield self.TrelloConfig.find_one({'version': self.trello['version']})
            # Sending e-mail with notification to the client
            # only in production
            if ((os.environ.get('GITHUB_BRANCH', 'develop') == 'master') or
                (os.environ.get('GITHUB_BRANCH', 'develop') in ['develop', 'release']
                    and '@venidera.com' in activity['created_by'])):
                fromaddr = self.settings['PROXIMIDADE_SUPORTE_EMAIL_FROM']
                template = Template(open(
                    './app/templates/email/customer_notice.html', 'r').read())
                user = yield self.Users.find_one({'email': activity['created_by']})
                emailTo = config['notification_emails'].copy()
                emailTo.append(
                    {'email': user['email'], 'fullname': user['fullname']})
                for user in emailTo:
                    body = template.substitute(
                        fullname=user['fullname'], link_suporte=self.settings['APPURL'],
                        card_title=activity['title'], message=comment)
                    logging.info(body)
                    sender.send_email(toaddr=user['email'], fromaddr=fromaddr,
                                      subject=activity['title'], message=body, is_html=True)
            else:
                logging.info('não enviando email: %s' % activity['created_by'])

            store_dump = {
                'tipo': 'updateComment', 'id': oid,
                'timeline_id': id, 'pid': pid, 'data': post}
            resp = True, dumps(store_dump)

        callback(resp)

    @engine
    def __comment_card_action_for_activity(self, callback=None):
        """ Update a activity after webhook actions """

        resp = False, {}

        """ get the trello card id from database """
        card_id = self.input_data['action']['data']['card']['id']

        """ get the user who commented on trello """
        trello_user = yield Task(self.get_trello_user,
                                 self.input_data['action']['memberCreator'])

        """ find activity by card id """
        activity = yield self.Activities.find_one(
            {'trello_cardId': {'$eq': card_id}})

        if activity and 'timeline' in activity:
            oid = str(activity['_id'])

            """ get timeline id """
            timeline = activity['timeline']
            tl = max(timeline, key=itemgetter('index'))
            id = timeline.index(tl)

            """ get comment message removind #client """
            comment = self.input_data['action']['data']['text']
            comment = comment.replace("#cliente", "")

            """ create a post and append in the timeline"""
            post = {
                'date': self.input_data['action']['date'],
                'user': trello_user['email'],
                'comment': comment,
                'action_id': [self.input_data['action']['id']]
            }
            timeline[id]['posts'].append(post)

            """ update activity object with new post """
            self.input_data = {'timeline': timeline}

            response = yield Task(
                self.update_object, objmodel=Activity, oids=oid)

            post = yield Task(self.update_post, post)
            config = yield self.TrelloConfig.find_one({'version': self.trello['version']})
            # Sending e-mail with notification to the client
            if ((os.environ.get('GITHUB_BRANCH', 'develop') == 'master') or
                (os.environ.get('GITHUB_BRANCH', 'develop') in ['develop', 'release']
                    and '@venidera.com' in activity['created_by'])):
                fromaddr = self.settings['PROXIMIDADE_SUPORTE_EMAIL_FROM']
                template = Template(open(
                    './app/templates/email/customer_notice.html', 'r').read())
                user = yield self.Users.find_one({'email': activity['created_by']})
                emailTo = config['notification_emails'].copy()
                emailTo.append(
                    {'email': user['email'], 'fullname': user['fullname']})
                for user in emailTo:
                    body = template.substitute(
                        fullname=user['fullname'], link_suporte=self.settings['APPURL'],
                        card_title=activity['title'], message=comment)
                    logging.info(body)
                    sender.send_email(toaddr=user['email'], fromaddr=fromaddr,
                                      subject=activity['title'], message=body, is_html=True)
            else:
                logging.info('não enviando email: %s' % activity['created_by'])

            store_dump = {'tipo': 'addComment', 'id': oid,
                          'timeline_id': id, 'data': post}
            resp = True, dumps(store_dump)

        callback(resp)

    @engine
    def __update_card_action_for_activity(self, callback=None):
        """ Update a activity after webhook actions """

        resp = False, {}

        """ get trello card id of databse """
        card_id = self.input_data['action']['data']['card']['id']

        """ find activity by card id """
        activity = yield self.Activities.find_one(
            {'trello_cardId': {'$eq': card_id}})

        if activity:
            oid = str(activity['_id'])
            data = self.input_data['action']['data']
            if 'idList' in data['old']:
                """ moving card between lists """

                config = yield self.TrelloConfig.find_one({'version': self.trello['version']})
                activity_type = activity['activity_type']
                trello_list = config['trello'][activity_type]
                activity_status = activity['activity_status']

                newlist = next(
                    (tl for tl in trello_list if
                     tl['lista'] == data['listAfter']['name']), None)

                if newlist:
                    """ new checklist to add """

                    if newlist['lista'] in config['checklist']:
                        lchecklist = config['checklist'][newlist['lista']]

                        """ Get all checlists for a card"""
                        nested = 'checklists'
                        params = {}
                        checklists = yield Task(self.get_card, idCards=card_id,
                                                nested=nested, params=params)

                        checklist = next((
                            cl for cl in checklists if
                            cl['name'] == lchecklist['name']), None)

                        if 'checkItems' in checklist:
                            names = [f['name']
                                     for f in checklist['checkItems']]
                            checkItems = [item for item in
                                          lchecklist['checkitems'] if
                                          item['name'] not in names]

                            for item in checkItems:
                                params = {
                                    'name': item['name'],
                                    'checked': item['checked'],
                                    'pos': 'bottom'
                                }

                                """ Create a checklist in trello by params """
                                nested = 'checkItems'
                                checkitem = yield Task(self.create_checklist,
                                                       idChecklists=checklist['id'],
                                                       nested=nested, params=params)

                    """ Update phase """
                    tl = max(activity['timeline'], key=itemgetter('index'))

                    if newlist['phase'] != tl['phase']:

                        """ Return new phase data """
                        newphase = yield Task(self.get_new_phase, activity,
                                              newlist, self.input_data)
                        activity['timeline'].append(newphase)
                        self.input_data = {'timeline': activity['timeline']}

                        """ If phase == 'finalizado' """
                        if newlist['phase'] == 'finalizado' and activity_status['status'] != 'finalizado':
                            activity_status = {
                                'status': 'finalizado',
                                'user': newphase['user'],
                                'date': newphase['date']
                            }
                            self.input_data['activity_status'] = activity_status
                        else:
                            activity_status = None

                        """ Update Activity with new phase """
                        response = yield Task(
                            self.update_object, objmodel=Activity, oids=oid)

                        """ Replace email by user data """
                        email = newphase['user']
                        user = yield self.Users.find_one({'email': email})
                        newphase['user'] = {
                            'name': user['fullname'], 'email': email,
                            'organization': user['organization']}
                        for post in newphase['posts']:
                            email = post['user']
                            user = yield self.Users.find_one({'email': email})
                            post['user'] = {
                                'name': user['fullname'],
                                'email': email,
                                'organization': user['organization']}

                        newphase = self.datetime_to_isoformat(newphase)

                        # Sending e-mail with notification to the client
                        if ((os.environ.get('GITHUB_BRANCH', 'develop') == 'master') or
                            (os.environ.get('GITHUB_BRANCH', 'develop') in ['develop', 'release']
                                and '@venidera.com' in activity['created_by'])):
                            fromaddr = self.settings['PROXIMIDADE_SUPORTE_EMAIL_FROM']
                            template = Template(open(
                                './app/templates/email/customer_notice.html', 'r').read())
                            user = yield self.Users.find_one({'email': activity['created_by']})
                            emailTo = config['notification_emails'].copy()
                            emailTo.append(
                                {'email': user['email'], 'fullname': user['fullname']})
                            for user in emailTo:
                                body = template.substitute(
                                    fullname=user['fullname'], link_suporte=self.settings['APPURL'],
                                    card_title=activity['title'], message=newlist['message'])
                                logging.info(body)
                                sender.send_email(toaddr=user['email'], fromaddr=fromaddr,
                                                  subject=activity['title'], message=body, is_html=True)
                        else:
                            logging.info('não enviando email: %s' %
                                         activity['created_by'])

                        store_dump = {'tipo': 'updatePhase',
                                      'id': oid, 'data': newphase}
                        if activity_status:
                            store_dump['activity_status'] = self.datetime_to_isoformat(
                                activity_status)
                        resp = True, dumps(store_dump)
            else:
                """ Field updated """
                self.input_data = self.get_updatable_fields()
                updates = [(x, v) for x, v in self.input_data.items()
                           if x in activity and activity[x] != v]

                if self.input_data and any(updates):
                    response = yield Task(
                        self.update_object, objmodel=Activity, oids=oid)
                    updates = self.datetime_to_isoformat(self.input_data)

                    store_dump = {'tipo': 'updateFields',
                                  'id': oid, 'data': updates}
                    resp = True, dumps(store_dump)

        callback(resp)
