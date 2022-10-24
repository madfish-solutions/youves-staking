const { MichelsonMap } = require("@taquito/michelson-encoder");
const { migrate } = require("../scripts/helpers");
const fs = require("fs");

const { stakingFactoryStorage } = require("../storage/stakingFactory");
const { confirmOperation } = require("../scripts/confirmation");
const { networks } = require("../env");

module.exports = async (tezos, network) => {
  const sender = await tezos.signer.publicKeyHash();
  stakingFactoryStorage.administrators.set(sender, 1);
  const addresses = JSON.parse(fs.readFileSync(`compilations/addresses.json`));

  const factoryAddress = addresses[network]["StakingPoolFactory"];
  const factory = await tezos.contract.at(factoryAddress);
  for (const pool of Object.values(networks[network].pools)) {
    const lastPoolId = await factory
      .storage()
      .then(storage => storage.pool_counter);

    const poolStorage = {
      deposit_token: pool.deposit_token,
      deposit_token_is_v2: pool.deposit_token_is_v2,
      reward_token: pool.reward_token,
      max_release_period: pool.max_release_period,
      administrators: pool.administrators,
    };
    const operation = await factory.methodsObject
      .deploy_pool(poolStorage)
      .send();
    await confirmOperation(tezos, operation.hash);
    const poolAddress = await factory
      .storage()
      .then(storage => storage.staking_pools.get(lastPoolId));
    await confirmOperation(tezos, operation.hash);
    console.log(`New pool deployed at: ${poolAddress}`);
  }
};
