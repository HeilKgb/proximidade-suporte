"""
Copyright(C) Venidera Research & Development, Inc - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
Written by Maakoto Kadowaki <makoto@venidera.com>
"""

import locale
from datetime import datetime
import logging
from json import loads
import pytz
import requests


class VTrello:
    """ Class for interfacing with Trello """

    def __init__(self, api_key=None, api_token=None, callbackURL=None):
        """ sets class basic data """
        self.api = {
            'url': 'https://api.trello.com/1/',
            'token': api_token,
            'key': api_key,
            'callbackURL': callbackURL
        }
        self.tz_brazil = pytz.timezone('America/Sao_Paulo')
        self.cur_dtime = (datetime.today()).astimezone(self.tz_brazil).date()
        self.lc_date_format = locale.nl_langinfo(locale.D_FMT)
        self.lc_dtime_format = locale.nl_langinfo(locale.D_T_FMT)
        self.check_connection()

    def check_connection(self):
        """ Check if the connection to the API is enabled """

        url = self.api['url'] + 'tokens/' + self.api['token']
        headers = {'Accept': 'application/json'}
        params = {
            'key': self.api['key'],
            'token': self.api['token']
        }
        try:
            req = requests.get(
                url=url,
                headers=headers,
                params=params
            )
            if req and req.status_code in [200, 201]:
                self.authenticated = True
                logging.info('Connected to %s.', self.api['url'])
                return True
            else:
                logging.info('Could not connect, error: %s', req.text)
                return False

        except requests.exceptions.RequestException as err:
            logging.info('Could not connect, error: %s', str(err))
        return False

    def search(self, **kwargs):
        """
            By default, Trello searches for each word in your query against
            exactly matching words within Member content. Specifying partial
            to be true means that we will look for content that starts with any
            of the words in your query. If you are looking for a Card titled
            "My Development Status Report", by default you would need to search
            for "Development". If you have partial enabled, you will be able to
            search for "dev" but not "velopment"
        """
        query = kwargs.pop('query', None)
        if not 'query':
            raise Exception('Uma query precisa ser fornecido.')

        url = self.api['url'] + 'search'

        nested = kwargs.pop('nested', None)
        if nested:
            url += '/' + kwargs['nested']
        headers = {'Accept': 'application/json'}
        query = {
            'key': self.api['key'],
            'token': self.api['token'],
            'query': query,
        }

        params = kwargs.pop('params', {})
        if params:
            query = {**query, **params}
        try:
            req = requests.get(
                url=url,
                headers=headers,
                params=query
            )
            if req and req.status_code in [200, 201]:
                data = loads(req.text)
                return data
        except requests.exceptions.RequestException as err:
            logging.info('Could not connect to %s: error: %s', url, str(err))
        return None

    def __tokens(self, method='GET', **kwargs):
        """ Return a webhook
        field: string. Field to retrieve.
            One of: active, callbackURL, description, idModel
            Valid values: active, callbackURL, description, idModel,
            consecutiveFailures, firstConsecutiveFailDate
        """

        token = kwargs.pop('token', None)
        if not token and not self.api['token']:
            raise Exception('Um token precisa ser fornecido.')
        if not token:
            token = self.api['token']

        url = self.api['url'] + 'tokens/' + token

        nested = kwargs.pop('nested', None)
        if nested:
            url += '/' + nested

        headers = {'Accept': 'application/json'}
        query = {
            'key': self.api['key'],
            'token': self.api['token']
        }

        params = kwargs.pop('params', {})
        if params:
            query = {**query, **params}
        try:
            req = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=query
            )
            if req and req.status_code in [200, 201]:
                data = loads(req.text)
                return data
            return None
        except requests.exceptions.RequestException as err:
            logging.info('Could not connect to %s: error: %s', url, str(err))
        return None

    def get_field_id(self, resource, **kwargs):
        """ Returns the id of resource from **kwargs """

        ids = {'organizations': 'org_id', 'members': 'member_id',
               'boards': 'board_id', 'lists': 'list_id', 'cards': 'card_id',
               'labels': 'label_id', 'webhooks': 'webhook_id',
               'checklists': 'checklist_id'
               }
        id = ids[resource]
        resp = kwargs.pop(id, None)
        return (resp)

    def __resources(self, method='GET', resource='organizations', **kwargs):
        """ Return information about a resource.
            resources: organizations, boards, lists, cards, labels, webhooks
            all or a comma-separated list of fields.
        """

        url = self.api['url'] + resource + '/'
        id = self.get_field_id(resource=resource, **kwargs)
        if id:
            url += id
        elif resource == 'members' or method != 'POST':
            raise Exception('Um recource id precisa ser fornecido.')

        nested = kwargs.pop('nested', None)
        if nested:
            url += '/' + nested

        if nested == 'checkItem' and 'idCheckItem' in kwargs:
            idCheckItem = kwargs.pop('idCheckItem', None)
            url += '/' + idCheckItem
        elif nested == 'checkItems' and 'idCheckItem' in kwargs:
            idCheckItem = kwargs.pop('idCheckItem', None)
            url += '/' + idCheckItem

        headers = {'Accept': 'application/json'}
        query = {
            'key': self.api['key'],
            'token': self.api['token']
        }

        params = kwargs.pop('params', {})
        if params:
            query = {**query, **params}

        try:
            req = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=query
            )
            if req and req.status_code in [200, 201]:
                data = loads(req.text)
                return data
            else:
                logging.info(req.text)
        except requests.exceptions.RequestException as err:
            logging.info('Could not connect to %s: error: %s', url, str(err))
        return None

    def get(self, resource=None, **kwargs):
        """ GET
            resource: organizations,
        """

        if not resource:
            raise Exception('Um resource precisa ser fornecido.')

        if resource in ['organizations', 'members', 'boards', 'lists',
                        'cards', 'labels', 'webhooks', 'checklists']:
            resp = self.__resources(
                method='GET', resource=resource, **kwargs)
        elif resource == 'tokens':
            resp = self.__tokens(method='GET', **kwargs)
        else:
            resp = None
        return resp

    def post(self, resource=None, **kwargs):
        """ POST
            resource: ,
        """
        if not resource:
            raise Exception('Um resource precisa ser fornecido.')

        if resource in ['organizations', 'members', 'boards', 'lists',
                        'cards', 'labels', 'webhooks', 'checklists']:
            resp = self.__resources(
                method='POST', resource=resource, **kwargs)
        elif resource == 'tokens':
            resp = self.__tokens(method='POST', **kwargs)
        else:
            resp = None
        return resp

    def put(self, resource=None, **kwargs):
        """ PUT
            resource: ,
        """

        if not resource:
            raise Exception('Um resource precisa ser fornecido.')

        if resource in ['organizations', 'members', 'boards', 'lists',
                        'cards', 'labels', 'webhooks', 'checklists']:
            resp = self.__resources(
                method='PUT', resource=resource, **kwargs)
        elif resource == 'tokens':
            resp = self.__tokens(method='PUT', **kwargs)
        else:
            resp = None
        return resp

    def delete(self, resource=None, **kwargs):
        """ DELETE
            resource: ,
        """

        if not resource:
            raise Exception('Um resource precisa ser fornecido.')

        if resource in ['organizations', 'members', 'boards', 'lists',
                        'cards', 'labels', 'webhooks', 'checklists']:
            resp = self.__resources(
                method='DELETE', resource=resource, **kwargs)
        if resource == 'tokens':
            resp = self.__tokens(method='DELETE', **kwargs)
        else:
            resp = None
        return resp
