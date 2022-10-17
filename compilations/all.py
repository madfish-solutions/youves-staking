import smartpy as sp

import utils.constants as Constants
from utils.fa2 import AdministrableFA2
from utils.viewer import Viewer
from contracts.unified_staking_pool import UnifiedStakingPool, Fa2TokenType
from contracts.staking_pool_factory import StakingPoolFactory

sp.add_compilation_target(
    "UnifiedStakingPool",
    UnifiedStakingPool(
        Fa2TokenType.make(sp.nat(0), Constants.DEFAULT_ADDRESS),
        sp.bool(True),
        Fa2TokenType.make(sp.nat(0), Constants.DEFAULT_ADDRESS),
        sp.nat(180 * 24 * 60 * 60),
        administrators=sp.big_map({}),
    ),
)

sp.add_compilation_target(
    "StakingPoolFactory",
    StakingPoolFactory(administrators=sp.big_map({})),
)