# !/usr/bin/env python3

from schematics.models import Model
from schematics.types import BaseType
from schematics.types import DictType
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


class Attachment(Model):
    filename = StringType(required=True, default='filename')
    file_checksum = StringType(required=True)
    thumb_checksum = StringType(required=False)
    image_type = StringType(required=True, default='image')

    class Options:
        roles = {
            'public': blacklist(''), 'delete': whitelist(''),
            'insert': blacklist(''), 'update': blacklist('')
        }

class Post(Model):
    date = DateTimeType(required=True, default=datetime.now())
    action_id = ListType(StringType, required=True, default=[])
    user = EmailType(required=True, default='suporte@risk3.com.br')
    comment = StringType(required=True, default='mudança de fase')
    attachment = ModelType(Attachment, required=False, default=None)
    edited = BooleanType(required=False, default=False)

    class Options:
        roles = {
            'public': blacklist(''), 'delete': whitelist(''),
            'insert': blacklist(''), 'update': blacklist('')
        }

class Atendimento(Model):

    index = IntType(required=True, default=0)
    level = StringType(required=True, default="sac")
    sector = StringType(required=True, default="atendimento")
    phase = DictType(BaseType, required=True, default={
        "index": 0, "id": "enviado", "label": "Enviado",
        "comment": "A solicitação foi enviada."
    })
    posts = ListType(ModelType(Post), required=True)
    user = EmailType(required=True, default='suporte@risk3.com.br')
    date = DateTimeType(required=True, default=datetime.now())

    class Options:
        roles = {
            'public': blacklist(''), 'delete': whitelist(''),
            'insert': blacklist(''), 'update': blacklist('')
        }

class SuporteTicket(Model):

    """Title"""
    title = StringType(required=True, default='')
    """Created By"""
    created_by = StringType(required=True, default='suporte@risk3.com.br')
    """NickName of Organizations allowed to view ticket"""
    organizations = ListType(StringType, required=True, default=['Risk3'])
    """The ticket description"""
    description = StringType(required=False)
    """Trello Card Id"""
    trello_cardId = StringType(required=False)

    """ Situação do cartão """
    # """ Condição/Situação do atendimento """
    situation = StringType(required=True, choices=[
        'executando', 'pausado', 'cancelado', 'finalizado'],
        default='executando')

    """ Nível de atendimento no Trello: 0 = 'SAC', 1 = 'Especializado' """
    level = DictType(BaseType, required=True, default={
        "id": "sac", "label": "Atendimento ao Cliente"})

    """ Setor de atendimento no Trello """
    sector = DictType(BaseType, required=True, default={
        "id": 'atendimento', "label": 'Atendimento',
        "specialist": 'Emanuelle Souza',
        'status': 'sac'})

    """ Estado do atendimento no Trello """
    status = DictType(BaseType, required=True, default = {
        "index": 0, "id": "triagem", "label": "Triagem", "phase": "recebido"
    })

    """ Histórico de atividades do suporte"""
    atendimento = ListType(ModelType(Atendimento), required=True, default=[])

    # ticket closed (trello)
    closed = BooleanType(required=True, default=False)

    # Object controllers
    created_at = DateTimeType(required=True, default=None)
    updated_at = DateTimeType(required=True, default=None)

    @classmethod
    def collection(self, name=None):
        self.__collection__ = name or 'suporte_tickets'
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