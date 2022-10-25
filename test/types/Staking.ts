import { MichelsonMap, MichelsonMapKey } from "@taquito/michelson-encoder";

import { BigNumber } from "bignumber.js";

import { Fa2, Token } from "./Common";

export type Stake = {
  stake: number;
  disc_factor: number;
  age_timestamp: number;
};

export type StakingStorageType = {
  total_stake: BigNumber;
  max_release_period: BigNumber;
  last_stake_id: BigNumber;
  stakes: MichelsonMap<MichelsonMapKey, unknown>;
  stakes_owner_lookup: MichelsonMap<MichelsonMapKey, unknown>;
  disc_factor: number;
  deposit_token: Fa2;
  deposit_token_is_v2: boolean;
  reward_token: Fa2;
  sender: string;
  last_rewards: number;
  current_rewards: number;
  administrators: MichelsonMap<MichelsonMapKey, unknown>;
  operators: MichelsonMap<MichelsonMapKey, unknown>;
};
