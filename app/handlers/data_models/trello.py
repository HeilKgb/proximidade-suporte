# !/usr/bin/env python3

from schematics.models import Model
from schematics.types import BaseType
from schematics.types import DictType
from schematics.types import ListType
from schematics.types import ModelType
from schematics.types import StringType
from schematics.types import DateTimeType
from schematics.types import EmailType
from schematics.types import IntType
from schematics.types import BooleanType
from schematics.transforms import whitelist
from schematics.transforms import blacklist


class TrelloUser(Model):

    email = EmailType(required=True)
    idMember = StringType(required=True)
    fullName = StringType(required=True)
    username = StringType(required=True)

    # Object controllers
    created_at = DateTimeType(required=True, default=None)
    updated_at = DateTimeType(required=True, default=None)

    @classmethod
    def collection(self, name=None):
        self.__collection__ = name or 'trello_users'
        return self.__collection__

    @classmethod
    def index(self):
        self.__index__ = 'email'
        return self.__index__

    @classmethod
    def full_index(self):
        return {"email": 1, "unique": True}

    class Options:
        roles = {
            'public': blacklist(),
            'delete': whitelist(),
            'insert': blacklist(),
            'update': blacklist()
        }

class Situation(Model):
    id = StringType(required=True, default='executando')
    label = StringType(required=True, default='Executando')
    comment = StringType(required=True,
        default='A solicitação está sendo executada')

class Phase(Model):
    id = StringType(required=True, default='enviado')
    label = StringType(required=True, default='Enviado')
    comment = StringType(required=True,
        default='A solicitação foi enviada.')
    back_comment = StringType(required=False,
        default='')

class ConfigSuporteWeb(Model):
    situations: ListType(ModelType(Situation), required=True, default={})
    triagem: ListType(ModelType(Situation), required=True, default={})
    phases: DictType(BaseType, required=True, default={})

class Level(Model):
    id = StringType(required=True, default='atendimento')
    label = StringType(required=True, default='Atendimento')
    especialista = StringType(required=True, default='')

class Sector(Model):
    id = StringType(required=True, default='sac')
    label = StringType(required=True, default='Atendimento ao Cliente')
    especialista = StringType(required=False)
    status = StringType(required=True, default='sac')

class Status(Model):
    index = IntType(required=True, default=0)
    id = StringType(required=True, default='triagem')
    label = StringType(required=True, default='Triagem')
    phase = StringType(required=True, default='triagem')

class ListStatus(Model):
    sac: ListType(ModelType(Status), required=True)
    padrao: ListType(ModelType(Status), required=True)
    suporte_ti: ListType(ModelType(Status), required=True)

class CleckItem(Model):
    name: StringType(required=True)
    checked: BooleanType(required=True, default=False)

class CheckList(Model):
    name: StringType(required=True)
    position: StringType(required=False, default='bottom')
    checkitems: ModelType(CleckItem, required=True)

class CheckListSAC(Model):
    triagem: ModelType(CheckList, required=True)
    atender: ModelType(CheckList, required=True)
    atendendo: ModelType(CheckList, required=True)
    resolvido: ModelType(CheckList, required=True)
    aprovado: ModelType(CheckList, required=True)

class CheckListPattern(Model):
    atender: ModelType(CheckList, required=True)
    atendendo: ModelType(CheckList, required=True)
    resolvido: ModelType(CheckList, required=True)
    aprovado: ModelType(CheckList, required=True)

class CheckListTI(Model):
    correcoes: ModelType(CheckList, required=True)
    melhorias: ModelType(CheckList, required=True)
    fazer: ModelType(CheckList, required=True)
    fazendo: ModelType(CheckList, required=True)
    homologacao: ModelType(CheckList, required=True)
    pronto_producao: ModelType(CheckList, required=True)
    aprovado: ModelType(CheckList, required=True)

class CheckLists(Model):
    sac: ModelType(CheckListSAC, required=True)
    padrao: ModelType(CheckListPattern, required=True)
    suporte_ti: ModelType(CheckListTI, required=True)

class PostOnMoveBoard(Model):
    move_from: ListType(StringType, required=True, default=list())
    move_to: ListType(StringType, required=True, default=list())
    message: StringType(required=True)

class  ConfigTrelloWeb(Model):
    level = ListType(ModelType(Level), required=True, default=[])
    sector = ListType(ModelType(Sector), required=True, default=[])
    status = ModelType(ListStatus, required=True)
    checklists = ModelType(CheckLists, required=True)
    posts_on_move_board = ListType(ModelType(PostOnMoveBoard), required=True, default=[])
    posts_on_change = DictType(BaseType, required=True, default={})
    action_on_check = DictType(BaseType, required=True, default={})

class Emails(Model):
    fullname = StringType(required=True, default='Equipe da Risk3')
    email = EmailType(required=True, default='suporte@risk3.com.br')

class ConfigEmails(Model):
    notification: ListType(ModelType(Emails), required=True, default=[])
    system_error: ListType(ModelType(Emails), required=True, default=[])

class TrelloConfig(Model):

    version = StringType(required=True)
    description = StringType(required=False)
    suporte = ModelType(ConfigSuporteWeb, required=True)
    trello = ModelType(ConfigTrelloWeb, required=True)
    managers = DictType(BaseType, required=True, default={})
    emails = ModelType(ConfigEmails, required=True)

    # Object controllers
    created_at = DateTimeType(required=True, default=None)
    updated_at = DateTimeType(required=True, default=None)

    @classmethod
    def collection(self, name=None):
        self.__collection__ = name or 'trello_config'
        return self.__collection__

    @classmethod
    def index(self):
        self.__index__ = 'version'
        return self.__index__

    @classmethod
    def full_index(self):
        return {"version": 1, "unique": True}

    class Options:
        roles = {
            'public': blacklist(),
            'delete': whitelist(),
            'insert': blacklist(),
            'update': blacklist()
        }
