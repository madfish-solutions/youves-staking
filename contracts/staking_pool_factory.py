from multiprocessing import pool
import smartpy as sp

from contracts.unified_staking_pool import UnifiedStakingPool, Fa2TokenType
from utils.administrable_mixin import SingleAdministrableMixin
import utils.constants as Constants    

class StakingPoolFactory(sp.Contract, SingleAdministrableMixin):

  def get_init_storage(self):
      """Returns the initial storage of the contract used for inheritance of smartpy contracts

      Returns:
            dict: initial storage of the contract
      """
      storage = {}
      storage["pool_counter"] = sp.nat(0)
      storage["staking_pools"] = sp.big_map(tkey=sp.TNat, tvalue=sp.TAddress)
      storage["administrators"] = self.administrators
      return storage

  def __init__(self, administrators):
      self.administrators = administrators
      self.init(**self.get_init_storage())
        
  @sp.entry_point
  def deploy_contract(self, deposit_token, deposit_token_is_v2, reward_token, max_release_period, administrators):
      self.verify_is_admin()

      new_pool = sp.create_contract(contract = UnifiedStakingPool(
            deposit_token,
            deposit_token_is_v2,
            reward_token,
            max_release_period,
            administrators))
      self.data.staking_pools[self.data.pool_counter] = new_pool
      self.data.pool_counter += sp.nat(1) 