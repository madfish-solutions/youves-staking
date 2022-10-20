from contracts.unified_staking_pool import TokenType
import smartpy as sp

import utils.constants as Constants
import utils.fa2 as fa2
from utils.administrable_mixin import AdministratorState

from contracts.staking_pool_factory import StakingPoolFactory

@sp.add_test(name="Staking Pool Factory")
def test_normal_staking_pool():
    scenario = sp.test_scenario()
    scenario.h1("Staking Pool Factory Test")
    scenario.table_of_contents()

    scenario.h2("Bootstrapping")

    administrator = sp.test_account("Administrator")
    obj = StakingPoolFactory({administrator.address: 1})
    scenario = sp.test_scenario()
    scenario += obj
    param = sp.record(
        deposit_token = TokenType.make(sp.string(Constants.TOKEN_TYPE_FA2), sp.nat(0), Constants.DEFAULT_ADDRESS),
        deposit_token_is_v2 = sp.bool(True),
        reward_token = TokenType.make(sp.string(Constants.TOKEN_TYPE_FA2), sp.nat(0), Constants.DEFAULT_ADDRESS),
        max_release_period = sp.nat(180 * 24 * 60 * 60),
        administrators=sp.big_map({administrator.address: 1}),
    )
    scenario += obj.deploy_pool(param).run(sender = administrator)

    scenario.verify_equal(obj.data.staking_pools[0], obj.data.staking_pools[0])
    scenario.verify_equal(obj.data.pool_counter, 1)

   