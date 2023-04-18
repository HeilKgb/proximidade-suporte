# !/usr/bin/env python3

import functools
from tornado.gen import Callback, coroutine, engine, Task
from handlers.base import BaseHandler
from logging import info
from datetime import datetime
import random
from dateutil import parser as dparser

from handlers.data_models import Activity


def check_trello(method):
    """decorator to check if trello is valid
    """

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        trello = self.trello
        if not trello['api'] or not trello['manager'] or not trello['board'] \
                or not trello['card_lists'] or not trello['callbackURL'] \
                or not trello['token'] or not trello['secret']:
            self.response(503, 'Unauthorized for this IP.')
            return
        info('Trello Config verified')
        return method(self, *args, **kwargs)
    return wrapper


class TrelloApiHandler(BaseHandler):
    """A class to collect common api trello handler methods
    """

    @check_trello
    @engine
    def get_client_labels(self, org=None, callback=None):
        """Gets the client label if it exists.
           If it doesn't exist, a new one is created.
        """
        if not self.trello or not org:
            callback(None)
        labels = self.trello['api'].get(
            resource='boards',
            board_id=self.trello['board']['id'],
            nested='labels',
            params={'fields': ['name', 'color']})

        label = next((item for item in labels if item['name'] == org), None)
        if not label:
            colors = list(set(map(lambda d: d['color'], labels)))
            color = random.choice(colors)
            label = self.trello['api'].post(
                resource='labels',
                params={
                    'name': org, 'color': color,
                    'idBoard': self.trello['board']['id']
                }
            )
        callback(label)

    @check_trello
    @engine
    def create_checklist(self, callback=None, **kwargs):
        """ Create a checklist in trello by params """

        params = kwargs.pop('params', None)
        nested = kwargs.pop('nested', None)
        idChecklists = kwargs.pop('idChecklists', None)
        checklist = self.trello['api'].post(
            resource='checklists',
            params=params,
            nested=nested,
            checklist_id=idChecklists
        )
        callback(checklist)

    @check_trello
    @engine
    def get_checklist(self, id=None, callback=None, **kwargs):
        """Gets the checklist/checlist items from checklist.
        """
        params = kwargs.pop('params', None)
        nested = kwargs.pop('nested', None)
        idChecklists = kwargs.pop('idChecklists', None)
        checklist = self.trello['api'].get(
            resource='checklists',
            params=params,
            nested=nested,
            checklist_id=idChecklists
        )
        callback(checklist)

    @check_trello
    @engine
    def update_check_items(self, callback=None, **kwargs):
        """ Update a checklist items in trello by params """

        params = kwargs.pop('params', None)
        nested = kwargs.pop('nested', None)
        idCards = kwargs.pop('idCards', None)
        checklist = self.trello['api'].put(
            resource='cards',
            params=params,
            nested=nested,
            card_id=idCards
        )
        callback(checklist)

    @check_trello
    @coroutine
    def create_webhook(self, params={}):
        """ Create a webhook in trello by params """

        webhook = self.trello['api'].post(
            resource='webhooks',
            params=params
        )
        if (webhook):
            info('Webhook criado com sucesso: %s', webhook)

    @check_trello
    @coroutine
    def schedule_delete_webhook(self, webhook_id=None):
        """ Schedule the delete a webhook in trello by params """

        webhook = self.trello['api'].delete(
            resource='webhooks',
            webhook_id=webhook_id
        )
        if (webhook):
            info('Webhook criado com sucesso: %s', webhook)

    @check_trello
    @engine
    def get_webhook(self, id_model=None, callback=None):
        """ Return webhook from trello """

        webhook = None
        if not id_model:
            info('Um id_model precisa ser fornecido.')
        else:
            webhooks = self.trello['api'].get(
                resource='tokens',
                nested='webhooks'
            )
            if webhooks:
                webhook = [wbhk for wbhk in webhooks if
                           wbhk['idModel'] == id_model]
                if webhook and isinstance(webhook, list) and len(webhook):
                    webhook = webhook[0]
        callback(webhook)

    @check_trello
    @engine
    def delete_webhook(self, webhook_id=None, callback=None):
        """ Delete a webhook from trello """

        if not webhook_id:
            info('Um webhookId precisa ser fornecido.')
            callback(None)
        else:
            resp = self.trello['api'].delete(
                resource='webhooks',
                webhook_id=webhook_id
            )
            callback(resp)

    @check_trello
    @engine
    def get_card(self, callback=None, **kwargs):
        """ Gets the card and nested. """

        params = kwargs.pop('params', None)
        nested = kwargs.pop('nested', None)
        idCards = kwargs.pop('idCards', None)

        card = self.trello['api'].get(
            resource='cards',
            params=params,
            nested=nested,
            card_id=idCards
        )
        callback(card)

    @check_trello
    @engine
    def create_card_in_trello(self, trello_data, callback=None):
        """ Create a Trello Card """

        title = ''
        trello_cardId = None
        org = self.current_user['organization']
        orgs = trello_data['organizations']

        if len(orgs) > 1:
            orgs.remove('PROXIMIDADE_SUPORTE')
        if len(orgs):
            org = orgs[0]
        client_label = yield Task(self.get_client_labels, org)

        lists = [li for li in self.trello['card_lists']
                 if li['name'] == trello_data['activity_type']]
        if not lists:
            info('Board não possui lista %s', trello_data['activity_type'])
            resp = 400, 'Board não possui lista %s', trello_data['activity_type']
            callback(resp)

        """ Card List Correções or Melhorias """
        card_list = lists[0]

        due_date = dparser.parse(trello_data['due_date'])
        params = {
            'idList': card_list['id'],
            'name': trello_data['name'],
            'desc': trello_data['desc'],
            'due': due_date.isoformat(),
            'idMembers': trello_data['idMembers'],
            'pos': 'bottom',  # posição do cartão na lista
            'idLabels': [client_label['id']]
        }

        """ Create a New Card """
        newcard = self.trello['api'].post(
            resource='cards',
            params=params
        )

        if not newcard:
            info('Não foi possível criar o cartão no trello')
            resp = 400, 'Não foi possível criar o cartão no trello'
            callback(resp)

        """ create a checklit """
        title = newcard['id'][:5] + newcard['id'][-5:] + \
            ' - ' + trello_data['name']
        self.trello['api'].put(
            resource='cards',
            card_id=newcard['id'],
            params={'name': title}
        )
        if 'checklist' in trello_data:
            checklist = yield Task(self.create_checklist,
                                   params={
                                       'idCard': newcard['id'],
                                       'name': trello_data['checklist']['name'],
                                       'pos': 'bottom'
                                   })
            if checklist:
                checkitems = []
                for item in trello_data['checklist']['checkitems']:

                    checkitem = yield Task(self.create_checklist,
                                           nested='checkItems',
                                           idChecklists=checklist['id'],
                                           params={
                                               'name': item['name'],
                                               'checked': item['checked'],
                                               'pos': 'bottom'
                                           })
                    checkitems.append(checkitem)

        if 'posts' in trello_data:
            msg_error = ''
            error = False
            for post in trello_data['posts']:
                params = {'text': post}
                info(params)
                action = self.trello['api'].post(
                    resource='cards',
                    card_id=newcard['id'],
                    nested='actions/comments',
                    params=params
                )
                if not action:
                    info('Não foi possível adicionar a mensagem %s', post)
                    msg_error = msg_error + post + '; '
                    error = True
            if error:
                resp = 400, 'Não foi possível adicionar a mensagem: %s', msg_error
                callback(resp)

        if 'attachments' in trello_data:
            """ Add attachment's url as comment in the card """
            client = trello_data['client']
            for attach in trello_data['attachments']:
                msg = "%s adicionou o arquivo: [%s - %s](%s)"
                msg = msg % (
                    client['email'],
                    attach['comment'], attach['name'], attach['url'])
                params = {'text': msg}
                action = self.trello['api'].post(
                    resource='cards', card_id=newcard['id'],
                    nested='actions/comments', params=params)

        """ Create a webhook to monitor card """
        trello_cardId = newcard['id']
        params = {
            'idModel': newcard['id'],
            'callbackURL': self.trello['callbackURL']
        }
        self.scheduler.add_job(
            TrelloApiHandler.create_webhook, args=(self, params), id='process_data')

        resp = 200, {"title": title, "trello_cardId": trello_cardId}
        callback(resp)

    @check_trello
    @engine
    def update_card_in_trello(self, trello_data, callback=None):
        """ Update a trello card """

        card = None
        if 'id' in trello_data:
            if 'attachments' in trello_data:
                """ Add attachment's url as comment in the card """
                for attach in trello_data['attachments']:
                    msg = "O cliente adicionou o arquivo: [%s - %s](%s)"
                    msg = msg % (
                        attach['comment'], attach['name'], attach['url'])
                    params = {'text': msg}
                    action = self.trello['api'].post(
                        resource='cards', card_id=trello_data['id'],
                        nested='actions/comments', params=params)
            elif 'post' in trello_data:
                """ Post new comments """
                params = {'text': trello_data['post']['comment']}
                action = self.trello['api'].post(
                    resource='cards',
                    card_id=trello_data['id'],
                    nested='actions/comments',
                    params=params
                )
            elif 'status' in trello_data:
                """ Change Status """

                data = trello_data['status']
                # user = yield self.TrelloUsers.find_one({'email': data['email']})
                params = {'text': data['comment']}
                action = self.trello['api'].post(
                    resource='cards',
                    card_id=trello_data['id'],
                    nested='actions/comments',
                    params=params
                )

            elif 'phase' in trello_data:
                """ Change phase status """
                data = trello_data['phase']
                """ If phase == em homologacao change list  to Aprovado """
                """ get activities data from mongo and return """

                if 'approve' in trello_data:
                    llist = [l for l in self.trello['card_lists']
                             if l['name'] == 'Aprovados']
                    if len(llist):
                        llist = llist[0]

                        card = self.trello['api'].put(
                            resource='cards',
                            card_id=trello_data['id'],
                            params={'idList': llist['id']}
                        )
                    params = {'text': data['comment']}
                    action = self.trello['api'].post(
                        resource='cards',
                        card_id=trello_data['id'],
                        nested='actions/comments',
                        params=params
                    )
                else:
                    params = {'text': data['comment']}
                    action = self.trello['api'].post(
                        resource='cards',
                        card_id=trello_data['id'],
                        nested='actions/comments',
                        params=params
                    )
            else:
                """ Updating title (card name) and description """
                params = {}
                if 'name' in trello_data:
                    params['name'] = trello_data['name']
                if 'desc' in trello_data:
                    params['desc'] = trello_data['desc']
                card = self.trello['api'].put(
                    resource='cards',
                    card_id=trello_data['id'],
                    params=params
                )
        callback(card)

    @check_trello
    @engine
    def delete_card_from_trello(self, activities, callback=None):
        """ Delete a trello card """

        deleted_cards = []
        for activity in activities:
            card_id = activity['trello_cardId']
            if card_id:
                webhook = yield Task(self.get_webhook, id_model=card_id)
                if webhook and 'id' in webhook:
                    """ remove webhook """
                    webhook = yield Task(
                        self.delete_webhook,
                        webhook_id=webhook['id']
                    )
                """ remove card from trello """
                card = self.trello['api'].delete(
                    resource='cards',
                    card_id=card_id
                )
                deleted_cards.append(card)
        callback(deleted_cards)

    @check_trello
    @engine
    def archive_card_from_trello(self, activities, close='true', callback=None):
        """ Archive a trello card """

        archived_cards = []

        for activity in activities:
            card_id = activity['trello_cardId']

            if card_id:
                webhook = yield Task(self.get_webhook, id_model=card_id)

                if close:
                    if webhook and 'id' in webhook:
                        """ remove webhook """
                        webhook = yield Task(
                            self.delete_webhook,
                            webhook_id=webhook['id']
                        )
                else:
                    if not webhook or (webhook and not 'id' in webhook):
                        """ Create a webhook to monitor card """
                        params = {
                            'idModel': card_id,
                            'callbackURL': self.trello['callbackURL']
                        }
                        self.scheduler.add_job(
                            TrelloApiHandler.create_webhook, args=(self, params), id='process_data')

                """ archive/unarchive card from trello """
                params = {'closed': close}

                card = self.trello['api'].put(
                    resource='cards',
                    card_id=card_id,
                    params=params
                )

                archived_cards.append(card)

        callback(archived_cards)

    def get_updatable_fields(self):
        """ Returns the list of fields to updatable """

        depara = {
            'name': 'title',
            'desc': 'description',
            'closed': 'closed'
        }
        resp = {}
        oldValue = self.input_data['action']['data']['old']
        key = list(oldValue.keys())[0]
        Value = self.input_data['action']['data']['card'][key]
        if key in depara.keys():
            resp[depara[key]] = Value
        return (resp)

    @engine
    def get_trello_user(self, trello_user=None, callback=None):
        """ Return suporte's user equivalent to trello user  """

        user = None
        idMember = trello_user['id']
        user = yield self.TrelloUsers.find_one({'idMember': idMember})
        callback(user)

    @engine
    def get_new_phase(self, activity=None, nlist=None, input_data=None, callback=None):
        """ Return new phase data """

        nphase = dict()
        if not activity or not nlist or not input_data:
            callback(nphase)

        index = len(activity['timeline'])
        trello_user = yield Task(self.get_trello_user,
                                 input_data['action']['memberCreator'])
        nphase = {
            'index': index,
            'phase': nlist['phase'],
            'user': trello_user['email'],
            'date': datetime.now(),
            'posts': [{
                'date': datetime.now(),
                'action_id': [input_data['action']['id']],
                'user': trello_user['email'],
                'comment': nlist['message'],
                'attachment': None
            }]
        }
        callback(nphase)
