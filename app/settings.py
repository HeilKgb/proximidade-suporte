# !/usr/bin/env python3

import os
import time
import site
import sys
import tornado
import tornado.template
from tornado.options import define, options
from motor import MotorClient as connect
from logging import info, warning
from vutils import gen_token
from apscheduler.schedulers.tornado import TornadoScheduler
from tornado.gen import engine

from vmail import sender
from vsupport.vtrello import VTrello
from lib.webhook_scheduling import WebHooks

info('Setting timezone to UTC')
os.environ['TZ'] = 'UTC'
time.tzset()

appdir = os.path.dirname(os.path.realpath(__file__))
info('Work directory: %s' % str(appdir))

# add local packages directories to Python's site-packages path
paths_list = [appdir, appdir + '/handlers', appdir + '/lib']
for path in paths_list:
    site.addsitedir(path)

sys.path = sys.path + paths_list

define("port", default=10451, type=int, help=("Server port"))
define("config", default=None, help=("Tornado configuration file"))
define('debug', default=True, type=bool,
       help=("Turn on autoreload, log to stderr only"))

tornado.options.parse_command_line()

# Settings
config = {}
config['debug'] = options.debug
config['xsrf_cookies'] = True
config['app_path'] = appdir
config['version'] = 'Proximidade Suporte version v1.0'
config['template_path'] = os.path.join(appdir, "templates")
config['static_path'] = os.path.join(appdir, "static")
config['autoescape'] = None

# MongoDB Connection
mongo_uri = os.environ.get("MONGODB_URI")
dbname = mongo_uri.split("/")[-1]
if '?' in dbname:
    dbname = dbname.split('?')[0]
conn = connect(mongo_uri, tz_aware=True)
db = conn[dbname]
info('MongoDB Database set to: %s' % mongo_uri)
config['db'] = db

# Security settings
config['cookie_secret'] = os.environ.get('COOKIE_SECRET', gen_token(50))
config['max_days_valid'] = 5  # Days to a token or cookie to be valid

# Redis config
config['redisdb_uri'] = os.environ.get('REDISDB_URI', "redis://prox_suporte_redis:6379")

# URL config
config['APP_PROTOCOL'] = os.environ.get('APP_PROTOCOL', 'https')
config['ROOT_DOMAIN'] = os.environ.get('ROOT_DOMAIN', 'suporte.prox.seg.br')
config['AUTHCENTER'] = os.environ.get(
    'AUTHCENTER', config['APP_PROTOCOL'] + '://auth.' + config['ROOT_DOMAIN'])
config['DASHBOARD'] = os.environ.get(
    'DASHBOARD', config['APP_PROTOCOL'] + '://dashboard.' + config['ROOT_DOMAIN'])
config['USMANAGER'] = os.environ.get(
    'USMANAGER', config['APP_PROTOCOL'] + '://usmanager.' + config['ROOT_DOMAIN'])
config['URL_IMAGES'] = os.environ.get('URL_IMAGES', config['AUTHCENTER'])

config['APPURL'] = os.environ.get(
    'APPURL', config['APP_PROTOCOL'] + '://suporte.' + config['ROOT_DOMAIN'])

config['API_URL'] = os.environ.get(
    'API_URL', "%s://api.%s:9090/api/v0" % (
        config['APP_PROTOCOL'], config['ROOT_DOMAIN']))

config['FILEMANAGER_URI'] = os.environ.get(
    'FILEMANAGER_URI', 'prox_suporte_filemanager:18500')

config['FILES'] = 'http://%s' % (config['FILEMANAGER_URI'])

config['SERVICE_NAME'] = 'suporte'

# Support email
config['PROX_SUPORTE_EMAIL_FROM'] = os.environ.get(
    'PROX_SUPORTE_EMAIL_FROM', 'suporte.prox@venidera.com')
config['PROX_SUPORTE_EMAIL_TO'] = os.environ.get(
    'PROX_SUPORTE_EMAIL_TO', 'suporte.prox@venidera.com')

config['login_url'] = (
    config['AUTHCENTER'] + '/#/login?continue=' + config['APPURL'])

# Scheduler
config['scheduler'] = TornadoScheduler()
config['scheduler'].start()

# Trello config
TRELLOAPIKEY = os.environ.get('TRELLOAPIKEY', '')
TRELLOAPITOKEN = os.environ.get('TRELLOAPITOKEN', '')
TRELLOAPISECRET = os.environ.get('TRELLOAPISECRET', '')
info(config['APPURL'])
info(os.environ.get('TRELLOCALLBACK', '/trello/webhooks'))

TRELLOCALLBACK = config['APPURL'] + os.environ.get('TRELLOCALLBACK', '/trello/webhooks')
TRELLOORGANIZATION= os.environ.get('TRELLOORGANIZATION', 'proxsuportedesenvolvimento')
TRELLOMANAGER = os.environ.get('TRELLOMANAGER', '')
TRELLOSUPORTBOARD = os.environ.get('TRELLOSUPORTBOARD',
    'Suporte Desenvolvimento' if os.environ.get('GITHUB_BRANCH', '') == 'develop' else (
        'Suporte Release' if os.environ.get('GITHUB_BRANCH', '') == 'release' else 'Suporte')
)

info('==========================================================================')
info('TRELLOAPIKEY: %s', TRELLOAPIKEY)
info('TRELLOAPITOKEN: %s', TRELLOAPITOKEN)
info('TRELLOAPISECRET: %s', TRELLOAPISECRET)
info('TRELLOCALLBACK: %s', TRELLOCALLBACK)
info('TRELLOORGANIZATION: %s', TRELLOORGANIZATION)
info('TRELLOMANAGER: %s', TRELLOMANAGER)
info('TRELLOSUPORTBOARD: %s', TRELLOSUPORTBOARD)
info('==========================================================================')

# Trello
trello_api = manager = trello_board = card_lists = None
if (TRELLOAPIKEY and TRELLOAPITOKEN and TRELLOAPISECRET and
    TRELLOMANAGER and TRELLOCALLBACK):
    trello_api = VTrello(api_key=TRELLOAPIKEY, api_token=TRELLOAPITOKEN)
    if not trello_api.check_connection():
        warning('Conexão com a API do Trello falhou')
        message = 'Conexão com a API do Trello falhou'
        subject = 'Erro no Trello Api.'
        sender.send_email(toaddr='vanessa.sena@venidera.com',
            fromaddr='prox@venidera.com', subject=subject,
            message=message, is_html=True)
    else:
        # Trello Manager Member
        manager = trello_api.get(
            resource='members',
            member_id=TRELLOMANAGER,
            params={'fields': 'fullName'}
        )
        if not manager:
            warning('Trello Manager não encontrado.')
            """ Se errro, enviar mensagem para suporte """
            message = 'Trello Manager não encontrado'
            subject = 'Erro no Trello Api.'
            sender.send_email(toaddr='vanessa.sena@venidera.com',
                fromaddr='suporte.prox@venidera.com', subject=subject,
                message=message, is_html=True)

        else:
            # Get Organization Id
            orgName = TRELLOORGANIZATION
            # if orgName:
            orgList = trello_api.get(
                resource='members',
                member_id = manager['id'],
                nested="organizations",
                params={"fields": ["name" , "displayName"]}
            )
            orgId = next((x['id'] for x in orgList if orgName in x['name']), None)
            if not orgId:
                warning('Trello Organization id não encontrado.')
                message = 'Trello Organization id não encontrado'
                subject = 'Erro no Trello Api.'
                sender.send_email(toaddr='vanessa.sena@venidera.com',
                    fromaddr='suporte.prox@venidera.com', subject=subject,
                    message=message, is_html=True)
            else:
                # Get Suporte Board of organization
                boards = trello_api.get(
                    resource='organizations',
                    org_id=orgId,
                    nested='boards',
                    params={'fields': 'name'}
                )
                boards = [b for b in boards if b['name'] == TRELLOSUPORTBOARD]
                if not boards:
                    info('Board Suporte não encontrado.')
                    message = 'Board Suporte não encontrado'
                    subject = 'Erro no Trello Api.'
                    sender.send_email(toaddr='vanessa.sena@venidera.com',
                        fromaddr='suporte.prox@venidera.com', subject=subject,
                        message=message, is_html=True)
                else:
                    trello_board = boards[0]
                    # Get Card List
                    card_lists = trello_api.get(
                        resource='boards',
                        board_id = trello_board['id'],
                        nested='lists',
                        params={'fields': 'name'}
                    )

config['trello'] = {
    'api': trello_api,
    'manager':  manager,
    'board': trello_board,
    'card_lists': card_lists,
    'callbackURL': TRELLOCALLBACK,
    'token': TRELLOAPITOKEN,
    'secret': TRELLOAPISECRET,
    'version': '1.2'
}

config['trello_authorized_ips'] = """
    107.23.104.115
    107.23.149.70
    54.152.166.250
    54.156.199.20
    54.209.149.230
    18.234.32.224/28
    189.19.114.172
    177.170.15.190
    """


info('DOMAIN: ' + config['ROOT_DOMAIN'])

MB = 1024 * 1024
GB = 1024 * MB
TB = 1024 * GB
MAX_BODY_SIZE = 1 * GB
MAX_BUFFER_SIZE = 1 * GB

config['CROSS_KEY'] = os.environ.get('CROSS_KEY', '---')

# sched_config = {}
# sched_config['trello'] = config['trello']

# @engine
# def check_webhook(sched_config):
#     job_trello = WebHooks(sched_config)
#     job_trello.create_webhook()

# config['scheduler'].add_job(check_webhook, args=[sched_config], id='process_data')
