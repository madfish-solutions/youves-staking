import { MichelsonMap } from "@taquito/michelson-encoder";

import { StakingStorageType } from "../test/types/Staking";

import { zeroAddress } from "../test/helpers/Utils";
import BigNumber from "bignumber.js";
import { PRECISION } from "../test/helpers/Constants";
export const stakingStorage: StakingStorageType = {
  total_stake: new BigNumber(0),
  max_release_period: new BigNumber(90 * 24 * 60 * 60),
  last_stake_id: new BigNumber(0),
  stakes: MichelsonMap.fromLiteral({}),
  stakes_owner_lookup: MichelsonMap.fromLiteral({}),
  disc_factor: PRECISION.toNumber(),
  deposit_token: { id: 0, address: zeroAddress },
  deposit_token_is_v2: true,
  reward_token: { id: 0, address: zeroAddress },
  sender: zeroAddress,
  last_rewards: 0,
  current_rewards: 0,
  administrators: MichelsonMap.fromLiteral({}),
  operators: MichelsonMap.fromLiteral({}),
};
