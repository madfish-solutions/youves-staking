import { MichelsonMap } from "@taquito/michelson-encoder";

import BigNumber from "bignumber.js";

export const stakingFactoryStorage: any = {
  pool_counter: 0,
  staking_pools: MichelsonMap.fromLiteral({}),
  administrators: MichelsonMap.fromLiteral({}),
};
