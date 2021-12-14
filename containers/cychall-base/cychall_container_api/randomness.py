import os
import random
import string
import hashlib

class Random:

    _registered = {}

    def __init_subclass__(cls, code, **kwargs):
        super().__init_subclass__(**kwargs)
        Random._registered[code] = cls
        cls._code = code

    @classmethod
    def get(cls, code):
        return cls._registered.get(code, RandomDefault)

    @classmethod
    @property
    def registered_codes(cls):
        return cls._registered.keys()
    
    @classmethod
    def generate(cls, code, *args, **kwargs):
        RandomClass = cls.get(code)
        return RandomClass.generate(*args, **kwargs)


class RandomString(Random, code='string'):

    _default_charset = string.digits+string.ascii_letters+string.punctuation

    @classmethod
    def generate(cls, length=16, charset=_default_charset, **kwargs):  
        return ''.join(random.choice(charset) for i in range(length))


class RandomInteger(Random, code='integer'):

    @classmethod
    def generate(cls, low=0, high=10, **kwargs):
        return random.randint(low, high)


class RandomBytes(Random, code='bytes'):

    @classmethod
    def generate(cls, length=16, **kwargs):
        return os.urandom(length)


class RandomHash(Random, code='hash'):

    @classmethod
    def generate(cls, hash_name='sha256', length=16, **kwargs):
        randomness = os.urandom(length)
        h = hashlib.new(hash_name)
        h.update(randomness)
        return h.hexdigest()

class RandomBit(Random, code='bit'):

    @classmethod
    def generate(cls, **kwargs):
        return random.getrandbits(1)

class RandomDefault(Random, code='default'):

    @classmethod
    def generate(cls, **kwargs):
        return 0
