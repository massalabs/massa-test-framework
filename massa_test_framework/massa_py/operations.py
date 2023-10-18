
from abc import ABC, abstractmethod

from .crypto import KeyPair, decode_pubkey_to_bytes

import base58
import varint
from blake3 import blake3

class Serializable(ABC):
    @abstractmethod
    def serialize(self) -> bytes:
        pass


class Typed(ABC):
    @abstractmethod
    def type_id(self) -> int:
        pass


class Operation(Serializable):
    def __init__(self, fee: int, expire_period: int, op: Serializable):
        self.fee = fee
        self.expire_period = expire_period
        self.op = op

    def serialize(self) -> bytes:
        enc_fee = varint.encode(int(self.fee))
        enc_expire_period = varint.encode(self.expire_period)
        enc_type_id = varint.encode(self.op.type_id())
        enc_op = self.op.serialize()
        return enc_fee + enc_expire_period + enc_type_id + enc_op

    def sign(self, creator_public_key, sender_private_key) -> bytes:
        enc_data = self.serialize()
        enc_sender_pub_key = decode_pubkey_to_bytes(creator_public_key)
        enc_data = enc_sender_pub_key + enc_data
        # Hash
        enc_data = blake3(enc_data).digest()

        # Sign
        keypair = KeyPair.from_secret_massa_encoded(sender_private_key)
        signature = varint.encode(0) + keypair.secret_key.sign(enc_data)
        signature_b58 = base58.b58encode_check(signature)
        return signature_b58


class OperationInput():
    def __init__(self, creator_public_key, content: Operation, sender_private_key):
        self.creator_public_key = creator_public_key
        self.signature = content.sign(
            creator_public_key, sender_private_key).decode("utf-8")
        self.serialized_content = list(content.serialize())


class RollBuy(Serializable, Typed):
    def __init__(self, roll_count: int):
        self.roll_count = roll_count

    def serialize(self) -> bytes:
        enc_roll_count = varint.encode(self.roll_count)
        return enc_roll_count

    def type_id(self) -> int:
        return 1


class RollSell(Serializable, Typed):
    def __init__(self, roll_count: int):
        self.roll_count = roll_count

    def serialize(self) -> bytes:
        enc_roll_count = varint.encode(self.roll_count)
        return enc_roll_count

    def type_id(self) -> int:
        return 2


class Transaction(Serializable, Typed):
    def __init__(
        self,
        recipient_address,
        amount,
    ):
        self.recipient_address = recipient_address
        self.amount = amount

    def serialize(self) -> bytes:
        recipient_address = varint.encode(0) + base58.b58decode_check(
            self.recipient_address[2:]
        )
        enc_amount = varint.encode(int(self.amount))
        return recipient_address + enc_amount

    def type_id(self) -> int:
        return 0


def create_roll_buy(
    sender_private_key,
    creator_public_key,
    fee: int,
    expire_period: int,
    roll_count: int,
):
    op = Operation(fee, expire_period, RollBuy(roll_count))
    op_in = OperationInput(creator_public_key, op, sender_private_key)
    return op_in.__dict__


def create_roll_sell(
    sender_private_key,
    creator_public_key,
    fee: int,
    expire_period: int,
    roll_count: int,
):
    op = Operation(fee, expire_period, RollSell(roll_count))
    op_in = OperationInput(creator_public_key, op, sender_private_key)
    return op_in.__dict__


def create_transaction(
    sender_private_key,
    creator_public_key,
    fee: int,
    expire_period: int,
    recipient_address,
    amount: int,
):
    op = Operation(fee, expire_period,
                   Transaction(recipient_address, amount))
    op_in = OperationInput(creator_public_key, op, sender_private_key)
    return op_in.__dict__
