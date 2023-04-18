# !/usr/bin/env python3

from schematics.models import Model
from schematics.types import ListType
from schematics.types import ModelType
from schematics.types import StringType
from schematics.types import BooleanType
from schematics.types import DateTimeType
from schematics.types import EmailType
from schematics.types import IntType
from schematics.transforms import whitelist
from schematics.transforms import blacklist
from datetime import datetime
from data_models.risk3.suporte import Post


class ActivityStatus(Model):
    status = StringType(required=True, choices=[
        'executando',
        'pausado',
        'cancelado',
        'finalizado'
    ], default='executando')
    user = EmailType(required=True, default='suporte@risk3.com.br')
    date = DateTimeType(required=True, default=datetime.now())

    class Options:
        roles = {
            'public': blacklist(''), 'delete': whitelist(''),
            'insert': blacklist(''), 'update': blacklist('')
        }


class TimelinePhase(Model):
    index = IntType(required=True, default=0)
    phase = StringType(required=True, default='enviado')
    user = EmailType(required=True, default='suporte@risk3.com.br')
    date = DateTimeType(required=True, default=datetime.now())
    posts = ListType(ModelType(Post), required=True)

    class Options:
        roles = {
            'public': blacklist(''), 'delete': whitelist(''),
            'insert': blacklist(''), 'update': blacklist('')
        }


class Activity(Model):
    """Title"""
    title = StringType(required=True, default='')
    """Created By"""
    created_by = StringType(required=True, default='suporte@risk3.com.br')
    """NickName of Organizations allowed to view activity"""
    organizations = ListType(StringType, required=True, default=['Risk3'])
    """The activity description"""
    description = StringType(required=False)
    """Trello Card Id"""
    trello_cardId = StringType(required=False)
    """Trello Config Version"""
    trello_config_version = StringType(required=True, default="1.0")
    """Show in mobile"""
    mobile = BooleanType(required=True, default=False)
    """The activity option (0-"Correções"; 1-"Melhorias")"""
    activity_type = StringType(required=True, default='correcoes', choices=[
        'correcoes',
        'melhorias'
    ])
    """Module id for fault corection or new features"""
    module = StringType(required=True)
    """Activity state"""
    activity_status = ModelType(ActivityStatus, required=True)
    '"" Timeline data ""'
    timeline = ListType(ModelType(TimelinePhase), required=True, default=[])

    # Activity closed (trello)
    closed = BooleanType(required=True, default=False)

    # Object controllers
    created_at = DateTimeType(required=True, default=None)
    updated_at = DateTimeType(required=True, default=None)

    @classmethod
    def collection(self, name=None):
        self.__collection__ = name or 'activities'
        return self.__collection__

    @classmethod
    def index(self):
        self.__index__ = 'id'
        return 'id'

    @classmethod
    def full_index(self):
        return {}

    class Options:
        roles = {
            'public': blacklist(),
            'delete': whitelist(),
            'insert': blacklist('created_at', 'updated_at'),
            'update': blacklist('created_at', 'updated_at')
        }
