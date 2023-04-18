import functools
from tornado.gen import coroutine
from handlers.trello_actions import TrelloActionsHandler
from logging import info

class WebHooks():

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

    def __init__(self, settings):
        self.settings = settings
        self.trello = settings['trello']

        # self.Trello = self.settings['db'].trello
        # self.tz_brazil = pytz.timezone('America/Sao_Paulo')

    @check_trello
    @coroutine
    def create_webhook(self, params={}):
        """ Create a webhook in trello by params """

        info('=========')
        trello_api = self.trello['api']
        webhooks = trello_api.get(
            resource='tokens',
            nested='webhooks'
        )
        trello_board = self.trello['board']
        webhook = next((wbhk for wbhk in webhooks if wbhk['idModel'] ==
                        trello_board['id']), None)
        if not webhook:
            info(' =============== Criando um webhook =============== ')
        #     webhook = trello_api.post(
        #         resource='webhooks',
        #         params={
        #             'idModel': trello_board['id'],
        #             'callbackURL': 'https://suporte.risk3.net.br/trello/webhooks'
        #         }
        #     )
        #     info('WebHook: %s board: %s ', webhook['id'], trello_board['name'])
        else:
            info('Exist WebHook: %s board %s', webhook['id'], trello_board['name'])
        # webhook = trello_api.delete(
        #     resource='webhooks',
        #     webhook_id=webhook['id']
        # )

        card_lists = self.trello['card_lists']
        for list in card_lists:
            webhook = next((wbhk for wbhk in webhooks if wbhk['idModel'] ==
                            list['id']), None)
            if not webhook:
                info(' =============== Criando um webhook =============== ')
            #     params={
            #         'idModel': list['id'],
            #         'callbackURL': self.trello['callbackURL']
            #     }
            #     webhook = trello_api.post(
            #         resource='webhooks',
            #         params=params
            #     )
            #     info('WebHook: %s list %s', webhook['id'], list['name'])
            else:
                info('Exist WebHook: %s list %s', webhook['id'], list['name'])
            # webhook = trello_api.delete(
            #     resource='webhooks',
            #     webhook_id=webhook['id']
            # )