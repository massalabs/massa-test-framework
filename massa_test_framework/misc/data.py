from dataclasses import dataclass


@dataclass
class NodeKeys:
    address: str
    public_key: str
    secret_key: str
    node_id: str


node_keys_list = [
    NodeKeys(
        address="AU1jUbxeXW49QRT6Le5aPuNdcGWQV2kpnDyQkKoka4MmEUW3m8Xm",
        public_key="P1ewWxz2kLqaU8q1ru4R3fBM6yCEbSrCuxFqMofsvBeRrtirtct",
        secret_key="S12J1PSAFXP3C1UnVbhgtPKezpsHtxfdArSUq5fo6Yhqh1Vg8YFL",
        node_id="N1ewWxz2kLqaU8q1ru4R3fBM6yCEbSrCuxFqMofsvBeRrtirtct",
    ),
    NodeKeys(
        address="AU12nfJdBNotWffSEDDCS9mMXAxDbHbAVM9GW7pvVJoLxdCeeroX8",
        public_key="P18aAC3zsisfensJ3ZHbA2u3L2nK3HWaYtPVkT3puu2LTuc3VpR",
        secret_key="S1Fp5FU2upkcngrEfXYzprDuDsL2E72wpJE4KjiJUAYKLFZ6v7u",
        node_id="N18aAC3zsisfensJ3ZHbA2u3L2nK3HWaYtPVkT3puu2LTuc3VpR",
    )
    # {
    #     "address": "AU1jUbxeXW49QRT6Le5aPuNdcGWQV2kpnDyQkKoka4MmEUW3m8Xm",
    #     "public_key": "P1ewWxz2kLqaU8q1ru4R3fBM6yCEbSrCuxFqMofsvBeRrtirtct",
    #     "secret_key": "S12J1PSAFXP3C1UnVbhgtPKezpsHtxfdArSUq5fo6Yhqh1Vg8YFL",
    #     "node_id": "N1ewWxz2kLqaU8q1ru4R3fBM6yCEbSrCuxFqMofsvBeRrtirtct",
    # },
    # {
    #     "address": "AU12nfJdBNotWffSEDDCS9mMXAxDbHbAVM9GW7pvVJoLxdCeeroX8",
    #     "public_key": "P18aAC3zsisfensJ3ZHbA2u3L2nK3HWaYtPVkT3puu2LTuc3VpR",
    #     "secret_key": "S1Fp5FU2upkcngrEfXYzprDuDsL2E72wpJE4KjiJUAYKLFZ6v7u",
    #     "node_id": "N18aAC3zsisfensJ3ZHbA2u3L2nK3HWaYtPVkT3puu2LTuc3VpR",
    # },
]

# wallets = [
#     {
#         "address": "AU1YxNkYDeC5GuEnVfoPsFtjfgtAJuxUoHKeZinzieaaRXQzcD4d",
#         "public_key": "P1VgjRuPn2VtsUEHsv5HmGG3SMhPVHSDnPKu1kg8aJUjHMXfNZj",
#         "secret_key": "S1WaSs8LGVoJck2hcz1kb5FN1Fwsfhp7cQkMmWxp5ceNPLDuLCT",
#         "node_id": "N1VgjRuPn2VtsUEHsv5HmGG3SMhPVHSDnPKu1kg8aJUjHMXfNZj",
#     },
#     {
#         "address": "AU12VAQtMCrgJNxXjscgHLn7Mr98Ky5DsCfom3HBB4ZENhAyzfpJQ",
#         "public_key": "P12XCs4CRuZCqbs7EM5weJ6wD3ybsho6q1yjQLAg91fXBSLsMLK9",
#         "secret_key": "S1V6ZLTTEifCwNbWpwMcCsoZwTiB3k1bdfT2U7FxBQKtcbLqdRk",
#         "node_id": "N12XCs4CRuZCqbs7EM5weJ6wD3ybsho6q1yjQLAg91fXBSLsMLK9",
#     },
# ]
