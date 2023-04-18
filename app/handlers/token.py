#!/usr/bin/env python3

from random import choice
from string import printable, whitespace, digits, ascii_letters
from logging import info
import base64
from uuid import uuid4
import hashlib
from Crypto import Random
from Crypto.Cipher import AES
from cryptography.fernet import Fernet
from datetime import datetime, timedelta


# Stupid XOR demo
# from itertools import cycle

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
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s) - 1:])]


# def encrypt(key, plaintext):
#     cipher = XOR.new(key)
#     return base64.b64encode(cipher.encrypt(plaintext))


# def decrypt(key, ciphertext):
#     cipher = XOR.new(key)
#     return cipher.decrypt(base64.b64decode(ciphertext))


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
