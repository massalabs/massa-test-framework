from abc import ABC, abstractmethod
from typing import Dict

from .crypto import KeyPair, decode_pubkey_to_bytes

import base58
import varint
from blake3 import blake3
import struct


class Serializable(ABC):
    @abstractmethod
    def serialize(self) -> bytes:
        pass


class Typed(ABC):
    @classmethod
    def type_id(cls) -> int:
        TYPE_ID = {
            "Transaction": 0,
            "RollBuy": 1,
            "RollSell": 2,
            "ExecuteSC": 3,
            "CallSC": 4,
        }
        type_id = TYPE_ID.get(cls.__name__, -1)
        if type_id == -1:
            raise Exception(f"Unknown type {cls.__name__}")
        return type_id


class InnerOp(Serializable, Typed):
    pass


class Datastore(Serializable):
    def __init__(self, datastore: Dict[bytes, bytes] = {}):
        self.datastore: Dict[bytes, bytes] = datastore

    def push(self, key: bytes, value: bytes):
        self.datastore[key] = value

    def serialize(self) -> bytes:
        enc_datastore = b""
        # number of key-value pairs
        enc_datastore += varint.encode(len(self.datastore))
        for key, value in self.datastore.items():
            enc_datastore += varint.encode(len(key))
            enc_datastore += key
            enc_datastore += varint.encode(len(value))
            enc_datastore += value
        return bytes(enc_datastore)


class Operation(Serializable):
    def __init__(self, fee: int, expire_period: int, op: InnerOp):
        self.fee = fee
        self.expire_period = expire_period
        self.op = op

    def serialize(self) -> bytes:
        enc_fee = varint.encode(int(self.fee))
        enc_expire_period = varint.encode(self.expire_period)
        enc_type_id = varint.encode(self.op.type_id())
        enc_op = self.op.serialize()
        return bytes(enc_fee + enc_expire_period + enc_type_id + enc_op)

    # massa doc https://docs.massa.net/docs/learn/operation-format-execution
    def sign(self, creator_public_key: str, sender_private_key: str, chainID: int) -> bytes:
        enc_data = self.serialize()
        enc_sender_pub_key = decode_pubkey_to_bytes(creator_public_key) 
        # doc https://docs.massa.net/docs/learn/operation-format-execution
        # > -> big-endian
        # Q -> unsigned long long
        enc_data = struct.pack('>Q', chainID) + enc_sender_pub_key + enc_data

        # Hash
        enc_data = blake3(enc_data).digest()

        # Sign
        keypair = KeyPair.from_secret_massa_encoded(sender_private_key)
        # PyNaCL sign -> return SignedMessage, we want the signature here
        signature = varint.encode(0) + keypair.secret_key.sign(enc_data).signature
        signature_b58 = base58.b58encode_check(signature)
        return signature_b58


class OperationInput:
    def __init__(
        self, creator_public_key: str, content: Operation, sender_private_key: str, chainID: int
    ):
        self.creator_public_key = creator_public_key
        self.signature = content.sign(creator_public_key, sender_private_key, chainID).decode(
            "utf-8"
        )
        self.serialized_content = list(content.serialize())


class RollBuy(InnerOp):
    def __init__(self, roll_count: int):
        self.roll_count = roll_count

    def serialize(self) -> bytes:
        return bytes(varint.encode(self.roll_count))


class RollSell(InnerOp):
    def __init__(self, roll_count: int):
        self.roll_count = roll_count

    def serialize(self) -> bytes:
        return bytes(varint.encode(self.roll_count))


class Transaction(InnerOp):
    def __init__(
        self,
        recipient_address,
        amount,
    ):
        self.recipient_address = recipient_address
        self.amount = amount

    def serialize(self) -> bytes:
        # varint.encode(0) forces user address
        recipient_address = varint.encode(0) + base58.b58decode_check(
            self.recipient_address[2:]
        )
        enc_amount = varint.encode(int(self.amount))
        return bytes(recipient_address + enc_amount)


class ExecuteSC(InnerOp):
    def __init__(self, data: bytes, max_gas: int, max_coins: int, datastore: Datastore):
        self.data = data
        self.max_gas = max_gas
        self.max_coins = max_coins
        self.datastore: Datastore = datastore

    def serialize(self) -> bytes:
        enc_max_gas = varint.encode(int(self.max_gas))
        enc_max_coins = varint.encode(int(self.max_coins))
        enc_data_len = varint.encode(len(self.data))
        enc_data = self.data
        enc_datastore = self.datastore.serialize()
        return bytes(
            enc_max_gas + enc_max_coins + enc_data_len + enc_data + enc_datastore
        )


class CallSC(InnerOp):
    def __init__(
        self,
        target_address: str,
        target_func: str,
        param: bytes,
        max_gas: int,
        coins: int,
    ):
        self.target_address = target_address
        self.target_func = target_func
        self.param = param
        self.max_gas = max_gas
        self.coins = coins

    def serialize(self) -> bytes:
        enc_max_gas = varint.encode(int(self.max_gas))
        enc_coins = varint.encode(int(self.coins))
        # TODO Add an Address class that serialize according to the type of address
        # varint.encode(1) forces smart contract address
        target_address = varint.encode(1) + base58.b58decode_check(
            self.target_address[2:]
        )
        target_func = self.target_func.encode("utf-8")
        target_func_len_enc = varint.encode(len(target_func))
        param_len_enc = varint.encode(len(self.param))
        return bytes(
            enc_max_gas
            + enc_coins
            + target_address
            + target_func_len_enc
            + target_func
            + param_len_enc
            + self.param
        )


def create_roll_buy(
    sender_private_key: str,
    creator_public_key: str,
    fee: int,
    expire_period: int,
    roll_count: int,
    chainID: int,
):
    op = Operation(fee, expire_period, RollBuy(roll_count))
    op_in = OperationInput(creator_public_key, op, sender_private_key, chainID)
    return op_in.__dict__


def create_roll_sell(
    sender_private_key: str,
    creator_public_key: str,
    fee: int,
    expire_period: int,
    roll_count: int,
    chainID: int,
):
    op = Operation(fee, expire_period, RollSell(roll_count))
    op_in = OperationInput(creator_public_key, op, sender_private_key, chainID)
    return op_in.__dict__


def create_transaction(
    sender_private_key: str,
    creator_public_key: str,
    fee: int,
    expire_period: int,
    recipient_address: str,
    amount: int,
    chainID: int,
):
    op = Operation(fee, expire_period, Transaction(recipient_address, amount))
    op_in = OperationInput(creator_public_key, op, sender_private_key, chainID)
    return op_in.__dict__


def create_call_sc(
    sender_private_key: str,
    creator_public_key: str,
    fee: int,
    expire_period: int,
    target_address: str,
    target_func: str,
    param: bytes,
    max_gas: int,
    coins: int,
    chainID: int,
):
    op = Operation(
        fee, expire_period, CallSC(target_address, target_func, param, max_gas, coins)
    )
    op_in = OperationInput(creator_public_key, op, sender_private_key, chainID)
    return op_in.__dict__


def create_execute_sc(
    sender_private_key: str,
    creator_public_key: str,
    fee: int,
    expire_period: int,
    data: bytes,
    max_gas: int,
    max_coins: int,
    datastore: Datastore,
    chainID: int,
):
    op = Operation(fee, expire_period, ExecuteSC(data, max_gas, max_coins, datastore))
    op_in = OperationInput(creator_public_key, op, sender_private_key, chainID)
    return op_in.__dict__
