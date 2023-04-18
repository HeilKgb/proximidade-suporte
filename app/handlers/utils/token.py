"""
Copyright(C) Risk3 Technology in Credit Analysis, Inc - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
Written by Development Team <suporte@risk3.com.br>
"""

from random import choice
from string import printable, whitespace, digits, ascii_letters
from logging import info
import base64
from uuid import uuid4
import hashlib
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from cryptography.fernet import Fernet
from datetime import datetime, timedelta

safechars = ''.join(sorted(set(printable) - set(whitespace)))


def gen_token(token_size=100):
    token = ''.join(choice(ascii_letters + digits) for x in range(token_size))
    return token


def mksecret(length=50):
    return ''.join(choice(safechars) for i in range(length))


def token_encode(word, secret):
    e = AESCipher(secret)
    enc = e.encrypt(word)
    return enc.decode('utf-8')


def token_decode(word, secret):
    e = AESCipher(secret)
    decval = False
    try:
        decval = e.decrypt(word)
    except Exception as err:
        info(err)
        pass
    return decval


class AESCipher(object):

    def __init__(self, key):
        self.bs = 32
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw):
        raw = pad(raw.encode('utf-8'), AES.block_size)
        iv = get_random_bytes(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        cryptraw = cipher.encrypt(raw)
        codigo = iv + cryptraw
        codigo64 = base64.b64encode(codigo)
        return codigo64

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        decriptado = cipher.decrypt(enc[AES.block_size:])
        unpacado = unpad(decriptado, AES.block_size).decode('utf-8')
        return unpacado


def data_encode(word):
    key = Fernet.generate_key()
    cipher = Fernet(key)
    if isinstance(word, str):
        word = word.encode('utf-8')
    data = cipher.encrypt(word)
    out = data + key
    return out.decode('utf-8')


def data_decode(data):
    if isinstance(data, str):
        data = data.encode('utf-8')
    key = data[-44:]
    word = data[:-44]
    cipher = Fernet(key)
    return cipher.decrypt(word).decode('utf-8')


class AuthToken(object):

    @staticmethod
    def generate_delete_token(authorizetoken, expiresecs=60):
        token = str(uuid4())
        expiresat = (datetime.utcnow() + timedelta(
            seconds=expiresecs)).isoformat() + 'Z'
        authorizetoken.set('authorizetoken-' + token, expiresat, ex=expiresecs)
        return {"token": {"id": token, "expires": expiresat}}

    @staticmethod
    def validate_delete_token(authorizetoken, token):
        if authorizetoken.get('authorizetoken-' + token):
            return True
        else:
            info('Token expired')
            return False
