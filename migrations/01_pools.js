const { MichelsonMap } = require("@taquito/michelson-encoder");
const { migrate } = require("../scripts/helpers");
const fs = require("fs");

const { stakingFactoryStorage } = require("../storage/stakingFactory");
const { confirmOperation } = require("../scripts/confirmation");

module.exports = async (tezos, network) => {
  const sender = await tezos.signer.publicKeyHash();
  stakingFactoryStorage.administrators.set(sender, 1);
  const addresses = JSON.parse(fs.readFileSync(`compilations/addresses.json`));

  const factoryAddress = addresses[network]["StakingPoolFactory"];
  const factory = await tezos.contract.at(factoryAddress);

  const depositToken = { token_id: 0, token_address: factoryAddress };
  const rewardToken = { token_id: 0, token_address: factoryAddress };
  const isLp = true;
  const maxPeriod = 100;
  const poolAdmins = MichelsonMap.fromLiteral({ [sender]: 1 });
  const pool = await factory.methodsObject
    .deploy_pool({
      deposit_token: depositToken,
      deposit_token_is_v2: isLp,
      reward_token: rewardToken,
      max_release_period: maxPeriod,
      administrators: poolAdmins,
    })
    .send();
  await confirmOperation(tezos, pool.hash);

  const storage = await factory.storage();
  const poolAddress = await storage.staking_pools.get("0");

  console.log(`Pool deployed at: ${poolAddress}`);
};
