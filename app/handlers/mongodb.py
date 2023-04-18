#!/usr/bin/env python3

from tornado.web import asynchronous
from tornado.gen import engine, Task
from schematics.exceptions import ValidationError, DataError
from json.decoder import JSONDecodeError
from logging import info
from datetime import datetime
import pytz
from bson import ObjectId as ObjId
from json import loads, dumps
from handlers.token import AuthToken
import functools
import jsonpatch

# info('Setting timezone to UTC')
# os.environ['TZ'] = 'UTC'
# time.tzset()


class MongoDBCRUD(object):

    def parse_input(self, objmodel, role='insert'):
        if role in 'delete':
            return {'deleted_at': datetime.now()}
        if role == 'undelete':
            return {'deleted_at': None}

        data = self.input_data
        dtype = type(data)
        data = [data] if dtype == dict else data

        resp = []
        for d in data:
            newobj = dict()
            for k, v in d.items():
                if k in objmodel().to_native(role=role).keys():
                    newobj[k] = v
            resp.append(newobj)
        return resp[0] if dtype == dict else resp

    def parse_output(self, obj, objmodel):
        newobj = dict()
        for k, v in obj.items():
            if k in objmodel._fields.keys():
                newobj[k] = v
                if k == 'info':
                    if isinstance(newobj['info'], dict):
                        try:
                            newobj['info'] = dumps(newobj['info'])
                        except Exception as e:
                            pass
        try:
            ret = objmodel(newobj).to_native(role='public')
        except AttributeError:
            # It AttributeError raises, then the date is a string
            ret = objmodel(newobj).to_primitive(role='public')
        except DataError:
            if 'info' in newobj.keys():
                newobj['info'] = loads(newobj['info'])
            ret = objmodel(newobj).to_primitive(role='public')

        if '_id' in obj.keys():
            ret['id'] = obj['_id']

        for k, v in ret.items():
            if 'info' == k:
                if not isinstance(ret['info'], dict):
                    try:
                        ret['info'] = loads(ret['info'])
                    except JSONDecodeError:
                        ret['info'] = loads(
                            ret['info'].replace('\'', ''))
        return ret

    def get_key(self, objmodel):
        # Check if the object model is valid.
        try:
            coll = objmodel.collection()
            if coll not in self.connmodels.keys():
                info('Please inform a valid object model.')
                return False
            return coll
        except Exception as e:
            info('Probably the object does not have a collection')
            return False

    def http_flow(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            # Check if the object model is valid.
            objmodel = kwargs.get('objmodel', None)
            coll = self.get_key(objmodel)
            if not coll:
                self.response(400, 'The object model is not valid.', [])
                return

            # Stablishing connections
            if 'connection' not in kwargs.keys():
                kwargs['connection'] = self.connmodels[coll]
            return method(self, *args, **kwargs)
        return wrapper

    @asynchronous
    @engine
    @http_flow
    def insert_object(self, objmodel, callback=None, **kwargs):
        # Enable callbacks
        callbacks = kwargs.get('callbacks', False)
        # Capturing motor connection
        connection = kwargs.get('connection', None)
        # Creating index for the required object, if it does not exists
        indexes = objmodel.full_index()
        if indexes:
            try:
                indexes = [indexes] if not isinstance(
                    indexes, list) else indexes
                for index in indexes:
                    if 'unique' in index.keys():
                        r = index['unique']
                        del index['unique']
                        index = [(k, v) for k, v in index.items()]
                        connection.create_index(index, unique=r)
                    else:
                        index = [(k, v) for k, v in index.items()]
                        connection.create_index(index)
            except Exception as e:
                pass
        # Parse the recieved data by removing anything but the valid fields.
        objs = self.parse_input(objmodel, role='insert')
        dtype = type(objs)
        objs = [objs] if dtype == dict else objs
        # Outputs
        outputs = list()
        duplicated = 0
        for obj in objs:
            try:
                # Additional operations in data before validation.
                for func in kwargs.get('functions', []):
                    if 'role' in func.keys() and func['role'] == 'after':
                        continue
                    status, message = yield Task(
                        func['instance'], obj, func['arguments'])
                    if status != 200:
                        if callbacks:
                            return callback((status, message, []))
                        self.response(status, message, [])
                        return

                # Adding some required information to the object
                dt = datetime.now(tz=pytz.utc)

                if 'created_at' in objmodel.fields.keys():
                    obj['created_at'] = dt
                if 'updated_at' in objmodel.fields.keys():
                    obj['updated_at'] = dt
                # Creating a new instance of the object.
                newobj = objmodel(obj)
                # Validating the object. This may raise an exception.
                try:
                    newobj.validate()
                except Exception as e:
                    info(e)
                    if callbacks:
                        return callback((
                            400, 'The system could not validate the model.', []))
                    self.response(
                        400, 'The system could not validate the model.', [])
                    return
                # Additional operations in data after validation.
                for func in kwargs.get('functions', []):
                    if 'role' in func.keys() and func['role'] == 'after':
                        status, message = yield Task(
                            func['instance'], obj, func['arguments'])
                        if status != 200:
                            if callbacks:
                                return callback((status, message, []))
                            self.response(status, message, [])
                            return

            except (ValidationError, DataError) as e:
                info(e)
                # The received data is invalid in some way
                if callbacks:
                    return callback((400, 'Invalid input data.', []))
                self.response(400, 'Invalid input data.', [])
                return

        for obj in objs:
            # Creating a new instance of the object.
            newobj = objmodel(obj)
            try:
                # Inserting the valid object into DB. This may raise an exception.
                newsaved = yield connection.insert(newobj.to_native())
                output = newobj.to_native()
                output['_id'] = str(newsaved)
                # The object was inserted.
                outputs.append(output)
            except Exception as e:
                # duplicated index error
                duplicated += 1
                oids = {k: v for k, v in newobj.items() if k in objmodel.index()}
                result = yield Task(
                    self.get_objects, objmodel=objmodel, oids=oids)
                if result:
                    outputs.append(self.parse_output(result[0], objmodel))

        if duplicated > 0:
            if callbacks:
                return callback((
                    409, 'Duplicated entries for an object.', outputs))
            self.response(409, 'Duplicated entries for an object.', outputs)
            return

        callback(outputs[0] if dtype == dict else outputs)

    @asynchronous
    @engine
    @http_flow
    def get_objects(self, objmodel, callback=None, **kwargs):
        # Capturing motor connection
        connection = kwargs.get('connection', None)
        # Capturing object info for specific queries
        oids = kwargs.get('oids', None) or dict()
        if oids and not isinstance(oids, dict):
            index = objmodel.index()
            if index == '' or index == 'id' or isinstance(index, list):
                try:
                    oids = {'_id': ObjId(oids)}
                except Exception as e:
                    self.response(400, 'The informed Id is not valid.')
                    return
            else:
                try:
                    oid = ObjId(oids)
                    oids = {"$or": [{'_id': oid}, {index: oids}]}
                except Exception as e:
                    oids = {index: oids}

        # Capturing all arguments
        arguments = self.request.arguments
        # Setting skip argument
        try:
            skip = int(self.get_argument('skip', None))
        except Exception as e:
            skip = 0
        # Setting limit argument
        try:
            limit = int(self.get_argument('limit', None))
        except Exception as e:
            limit = 100
        # Constraint for deleted objects
        ignore = kwargs.get('ignore', False)
        const = {'deleted_at': None} if not ignore else dict()

        # result = None
        if oids and isinstance(oids, dict):
            # If there is an specific id that was passed
            result = yield connection.find(
                {**oids, **const}).skip(skip).limit(limit).to_list(None)
        elif not arguments:
            # If there is no arguments, get all objects
            result = yield connection.find(
                const).skip(skip).limit(limit).to_list(None)
        else:
            query = dict()
            for arg in arguments:
                if arg in ['token', 'limit', 'skip']:
                    continue
                elif arg == 'query':
                    query = {**query, **arguments[arg]}
                    continue
                value = self.get_argument(arg, None)
                if value:
                    value = value.strip()
                    if value[0] == "\"" and value[-1] == "\"":
                        query[arg] = value[1:-1]
                    else:
                        query[arg] = {
                            '$regex': value,
                            '$options': 'i'
                        }
            result = yield connection.find(
                {**query, **const}).skip(skip).limit(limit).to_list(None)

        callback(result)

    @asynchronous
    @engine
    @http_flow
    def update_object(self, objmodel, callback=None, **kwargs):
        # Capturing motor connection
        connection = kwargs.get('connection', None)
        # Capturing object info for specific queries
        oids = kwargs.get('oids', dict())
        # Capturing role (update, delete, undelete)
        role = kwargs.get('role', 'update')

        # Setting query for enabling visualization of deleted items
        ignore = True if role == 'undelete' else False
        result = yield Task(self.get_objects, objmodel=objmodel,
                            oids=oids, ignore=ignore)
        tres = type(result)
        result = [result] if tres == dict else result
        # If the object was not found
        if not result:
            callback(result)
            return
        # Removing additional fields informed by the user
        updobj = self.parse_input(objmodel, role=role)
        if updobj:
            for out in result:
                valids = objmodel._fields.keys()
                testobj = {k: v for k, v in out.items() if k in valids}

                # Additional operations in data before validation.
                for func in kwargs.get('functions', []):
                    status, message = yield Task(
                        func['instance'], updobj, func['arguments'])
                    if status != 200:
                        self.response(status, message, [])
                        return

                for k, v in updobj.items():
                    if k in testobj.keys():
                        testobj[k] = v

                # Validating the object. This may raise an exception.
                try:
                    testobj = objmodel(testobj)
                    testobj.validate()
                except Exception as e:
                    info(e)
                    self.response(
                        400, 'The system could not validate the model.', [])
                    return

                # Deep update for nested structures
                rep = kwargs.get('replace_existing', False)
                if not rep:
                    updobj = self.deepupdate(out, updobj)
                # Adding some required information to the object.
                dt = datetime.now(tz=pytz.utc)
                updobj['updated_at'] = dt
                try:
                    # Updating the object.
                    newsaved = yield connection.update(
                        {'_id': out['_id']}, {'$set': updobj})
                    info(newsaved)
                except Exception as e:
                    # Duplicated index error
                    self.response(409, 'Duplicated entry for an object.', [])
                    return

                # The object was updated. Preparing the response.
                for k, v in updobj.items():
                    out[k] = v

            # The object/objects was/were updated.
            callback(result)
        else:
            self.response(400, 'No data provided to be updated.', [])
            return

    @asynchronous
    @engine
    @http_flow
    def delete_object(self, objmodel, callback=None, **kwargs):
        # Enable callbacks
        callbacks = kwargs.get('callbacks', False)
        # Capturing motor connection
        connection = kwargs.get('connection', None)
        # Capturing object info for specific queries
        oids = kwargs.get('oids', None) or dict()

        result = yield Task(
            self.get_objects, objmodel=objmodel, oids=oids)
        tres = type(result)
        result = [result] if tres == dict else result
        # If the object was not found
        if not result:
            callback(result)
            return

        # Double step checking for object deletion
        ignore = kwargs.get('ignore', False)
        if not ignore:
            token = self.get_argument('token', None)
            authorizetoken = kwargs.get('authorizetoken', None)
            if authorizetoken is None:
                if callbacks:
                    return callback((
                        500, "Authorization not defined in the system.", {}))
                self.response(
                    500, "Authorization not defined in the system.", {})
                return
            elif token is None:
                resp = AuthToken.generate_delete_token(authorizetoken)
                if callbacks:
                    return callback((
                        401, "Authentication required. Token to execute this" +
                        " request: ?token=<token value>.", resp))
                self.response(
                    401, "Authentication required. Token to execute this" +
                    " request: ?token=<token value>.", resp)
                return
            elif not AuthToken.validate_delete_token(authorizetoken, token):
                if callbacks:
                    return callback((
                        403, 'The informed token is not valid.', {}))
                self.response(403, 'The informed token is not valid.', {})
                return

        for out in result:
            # Additional operations in data before validation.
            for func in kwargs.get('functions', []):
                resp = yield Task(func['instance'], out, func['arguments'])
                if len(resp) >= 2:
                    status, message = resp[0], resp[1]
                data = dict()
                if len(resp) == 3:
                    data = resp[2]
                if status != 200:
                    if callbacks:
                        return callback((status, message, data))
                    return self.response(status, message, data)

            try:
                # Capturing motor connection
                deleted_connection = self.connmodels['deleted_%s' % (
                    self.get_key(objmodel))]
                # Adding some required information to the object.
                dt = datetime.now(tz=pytz.utc)
                out['updated_at'] = dt
                # Copying the object to the deleted collection
                yield deleted_connection.insert(out)
                # Removing the object to the original collection
                yield connection.remove({'_id': out['_id']})
            except Exception as e:
                if callbacks:
                    return callback((status, message, []))
                return self.response(400, 'The deletion has failed', [])

        # The object/objects was/were deleted.
        callback(result)

    @asynchronous
    @engine
    @http_flow
    def recover_object(self, objmodel, callback=None, **kwargs):
        # Capturing motor connection
        try:
            deleted_connection = self.connmodels['deleted_%s' % (
                self.get_key(objmodel))]
        except Exception as e:
            self.response(404, 'There are no objects to be recovered.', {})
            return

        # Capturing object info for specific queries
        oids = kwargs.get('oids', None) or dict()

        result = yield Task(
            self.get_objects, objmodel=objmodel,
            oids=oids, connection=deleted_connection)
        tres = type(result)
        result = [result] if tres == dict else result
        # If the object was not found
        if not result:
            callback(result)
            return

        # Double step checking for object deletion
        token = self.get_argument('token', None)
        authorizetoken = kwargs.get('authorizetoken', None)
        if authorizetoken is None:
            self.response(500, "Authorization not defined in the system.", {})
            return
        elif token is None:
            resp = AuthToken.generate_delete_token(authorizetoken)
            self.response(
                401, "Authentication required. Token to execute this" +
                " request: ?token=<token value>.", resp)
            return
        elif not AuthToken.validate_delete_token(authorizetoken, token):
            self.response(403, 'The informed token is not valid.', {})
            return

        for out in result:
            try:
                # Capturing motor connection
                connection = kwargs.get('connection', None)
                # Adding some required information to the object.
                dt = datetime.now(tz=pytz.utc)
                out['updated_at'] = dt
                # Copying the object to the deleted collection
                yield connection.insert(out)
                # Removing the object to the original collection
                yield deleted_connection.remove({'_id': out['_id']})
            except Exception as e:
                self.response(400, 'The recovery has failed', [])
                return

        # The object/objects was/were recovered.
        callback(result)

    def deepdelete(self, o1):
        info('CASCADE DELETE NOT IMPLEMENTED.')

    def deepupdate(self, o1, o2):
        # Normalizing keys between old and new dicts
        o1 = {k: v for k, v in o1.items() if isinstance(v, dict)
              and k in o2.keys()}
        o1.update({k: v for k, v in o2.items() if k not in o1.keys()})
        # Beginning deep update
        patch = jsonpatch.JsonPatch(
            [p for p in jsonpatch.make_patch(o1, o2) if p["op"] != "remove"])
        for p in patch:
            if p["op"] == "move":
                p["op"] = "copy"
        return patch.apply(o1)

    @asynchronous
    @engine
    def is_valid(self, obj, args=dict(), callback=None):
        try:
            if args['key'] not in obj.keys():
                # Ignore it
                callback((200, ''))
            data = obj[args['key']]
            if not isinstance(data, list):
                data = [data]

            outputs = []
            keys = []
            # Checking for structure validity
            for n, d in enumerate(data):
                index = args['model'].index()
                if index == '' or index == 'id' or isinstance(index, list):
                    try:
                        keys.append(d)
                        oids = {'_id': ObjId(d)}
                    except Exception as e:
                        self.response(400, 'The informed Id is not valid.')
                        return
                else:
                    if isinstance(d, dict):
                        d = d[index]
                    try:
                        keys.append(d)
                        oid = ObjId(d)
                        oids = {"$or": [{'_id': oid}, {index: d}]}
                    except Exception as e:
                        oids = {index: d}

                output = yield Task(
                    self.get_objects, objmodel=args['model'], oids=oids)

                # if index and output and index in output[0].keys():
                #     if isinstance(obj[args['key']], str):
                #         obj[args['key']] = output[0][index]
                #     else:
                #         obj[args['key']][n] = output[0][index]

                outputs.append(output)

            # Checking for repeated ids
            if len(keys) != len(set(keys)):
                callback(
                    (400, 'The field \'%s\' has duplicated ids.' % args['key']))
                return

            if all(outputs):
                callback((200, 'The field %s is valid.' % args['key']))
                return
        except Exception as e:
            pass
        callback((400, 'The field \'%s\' is not valid.' % args['key']))
        return
