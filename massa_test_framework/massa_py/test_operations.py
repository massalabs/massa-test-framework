import unittest

from .operations import create_roll_buy, create_roll_sell, create_transaction, RollBuy, RollSell, Transaction

import base58


class TestOperations(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.sender_private_key = "S12m8Je6x2EE6kSrw7CxQ4WWtjSvNvVYq9gB1jrDHPLABFUYoVXM"
        self.creator_public_key = "P1yXufX4ebsXpuCP1Lrf3Tm9ysqYwa27RaJmrueorii44bi9x2k"

    def test_create_roll_buy(self):
        fee = 100
        expire_period = 10
        roll_count = 5
        roll_buy = create_roll_buy(
            self.sender_private_key,
            self.creator_public_key,
            fee,
            expire_period,
            roll_count,
        )
        assert roll_buy["creator_public_key"] == self.creator_public_key
        assert base58.b58decode_check(
            roll_buy["signature"]) == b'\x00\xc3\x15\xf0\x1c\x98\xed\xbdB\xc3\xdc\x91L\x1b\x90\x93\xf6\xa6\xc6\xe4\xa3\x8d%\xd2$\xe4^s\xfc\xcc\xb5\x8f\x8d\xa3+\xdc\xcdA\x9e\x1e\xc8\x1d\xc9\x89\x96\xf2\x910\xa5\xf7>*\x9d`/v\xe3!n\xec1{\x16\xff\x06'
        assert roll_buy["serialized_content"] == [100, 10, 1, 5]

    def test_create_roll_sell(self):
        fee = 100
        expire_period = 10
        roll_count = 5
        roll_sell = create_roll_sell(
            self.sender_private_key,
            self.creator_public_key,
            fee,
            expire_period,
            roll_count,
        )
        assert roll_sell["creator_public_key"] == self.creator_public_key
        assert base58.b58decode_check(
            roll_sell["signature"]) == b'\x00Y\xa7\x12T\x9e\xda\xca\x14\xca\xa0D/\xfcU0!\x90)\xe6je\x0ez\x10c\x1f2p\x80<\xc42y\xee48co\xf19\x1f\xa7\xd6?\x867\r\xb5\x15\x05\x0c\xaa-\xcb\xa8\xb9-\xce+\xbf\xa0W\xc5\r'
        assert roll_sell["serialized_content"] == [100, 10, 2, 5]

    def test_create_transaction(self):
        fee = 100
        expire_period = 10
        recipient_address = "AU1jUbxeXW49QRT6Le5aPuNdcGWQV2kpnDyQkKoka4MmEUW3m8Xm"
        amount = 1000
        transaction = create_transaction(
            self.sender_private_key,
            self.creator_public_key,
            fee,
            expire_period,
            recipient_address,
            amount,
        )
        assert transaction["creator_public_key"] == self.creator_public_key
        assert base58.b58decode_check(
            transaction["signature"]) == b'\x00\x95\xf9&b\xbd\xee\xd4l\n\x08\x1bj\xba\xa6\xeas\x8e\xa8\x94 \xae\x80S\xe7\x0c\x1f\xb3\x1b\xc1x%-g\x9b\xd7Ucs\xb0W\xf7v\x03\x943\xcf3\xf6\x1e\xb2\xcd\xf5l\xb8B\xab:\x06\n\xe2\xb8\x93\x96\x07'
        assert transaction["serialized_content"] == [100, 10, 0, 0, 0, 96, 114, 94, 30, 115, 47, 99, 47, 191, 140,
                                                     83, 1, 241, 139, 206, 40, 105, 236, 27, 21, 29, 180, 129, 27, 137, 66, 234, 212, 59, 126, 129, 219, 232, 7]

    def test_roll_buy_serialize(self):
        roll_count = 5
        roll_buy = RollBuy(roll_count)
        assert roll_buy.serialize() == b'\x05'

    def test_roll_sell_serialize(self):
        roll_count = 5
        roll_sell = RollSell(roll_count)
        assert roll_sell.serialize() == b'\x05'

    def test_transaction_serialize(self):
        recipient_address = "AU1jUbxeXW49QRT6Le5aPuNdcGWQV2kpnDyQkKoka4MmEUW3m8Xm"
        amount = 1000
        transaction = Transaction(recipient_address, amount)
        assert transaction.serialize(
        ) == b'\x00\x00`r^\x1es/c/\xbf\x8cS\x01\xf1\x8b\xce(i\xec\x1b\x15\x1d\xb4\x81\x1b\x89B\xea\xd4;~\x81\xdb\xe8\x07'


if __name__ == '__main__':
    unittest.main()
