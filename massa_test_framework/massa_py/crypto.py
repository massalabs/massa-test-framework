# import numpy as np
# import hashlib
import base58

# import random
from blake3 import blake3
import varint
from nacl.signing import SigningKey, VerifyKey

class KeyPair:
    def __init__(self, secret_key: SigningKey, public_key: VerifyKey):
        self.secret_key = secret_key
        self.public_key = public_key

    @staticmethod
    def random():
        sk = SigningKey.generate()
        vk = sk.verify_key
        return KeyPair(secret_key=sk, public_key=vk)

    @staticmethod
    def from_secret_massa_encoded(private: str):
        # Strip identifier
        private = private[1:]
        # Decode base58
        private = base58.b58decode_check(private)
        # Decode varint
        # version = varint.decode_bytes(private)
        # Get rest (for the moment versions are little)
        secret_key_ = private[1:]
        # decode privkey
        # PyNaCL can only init SigningKey object from seed
        # From https://github.com/pyca/pynacl/issues/639 and crypto_sign_ed25519_sk_to_seed function code
        # the seed is in fact the private key
        seed = secret_key_
        secret_key = SigningKey(seed)
        public_key = secret_key.verify_key
        return KeyPair(secret_key=secret_key, public_key=public_key)

    def get_public_massa_encoded(self):
        return "P" + base58.b58encode_check(
            varint.encode(0) + self.public_key.to_bytes()
        ).decode("utf-8")

    def get_secret_massa_encoded(self):
        return "S" + base58.b58encode_check(
            varint.encode(0) + self.secret_key.to_seed()
        ).decode("utf-8")


def decode_pubkey_to_bytes(pubkey):
    return base58.b58decode_check(pubkey[1:])


def deduce_address(pubkey):
    return "AU" + base58.b58encode_check(
        varint.encode(0) + blake3(varint.encode(0) + pubkey.to_bytes()).digest()
    ).decode("utf-8")


# def get_address_thread(address):
#     address_bytes = base58.b58decode_check(address[2:])[1:]
#     return np.frombuffer(address_bytes, dtype=np.uint8)[0] / 8
