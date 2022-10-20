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

  const dexAddress = "KT1GPJDTf8GZspCcanaG2KhMvGu3NJRqurat";
  const depositToken_1 = { token_id: 0, token_address: dexAddress };
  const depositToken_2 = { token_id: 1, token_address: dexAddress };
  const depositToken_3 = { token_id: 2, token_address: dexAddress };
  const rewardToken = {
    token_id: 0,
    token_address: "KT19363aZDTjeRyoDkSLZhCk62pS4xfvxo6c",
  };
  const isLp = true;
  const maxPeriod = 100;
  const poolAdmins = MichelsonMap.fromLiteral({
    [sender]: 1,
  });
  const pool_1 = await factory.methodsObject
    .deploy_pool({
      deposit_token: depositToken_1,
      deposit_token_is_v2: isLp,
      reward_token: rewardToken,
      max_release_period: maxPeriod,
      administrators: poolAdmins,
    })
    .send();
  await confirmOperation(tezos, pool_1.hash);

  const pool_2 = await factory.methodsObject
    .deploy_pool({
      deposit_token: depositToken_2,
      deposit_token_is_v2: isLp,
      reward_token: rewardToken,
      max_release_period: maxPeriod,
      administrators: poolAdmins,
    })
    .send();
  await confirmOperation(tezos, pool_2.hash);

  const pool_3 = await factory.methodsObject
    .deploy_pool({
      deposit_token: depositToken_3,
      deposit_token_is_v2: isLp,
      reward_token: rewardToken,
      max_release_period: maxPeriod,
      administrators: poolAdmins,
    })
    .send();
  await confirmOperation(tezos, pool_3.hash);

  const storage = await factory.storage();
  const poolAddress1 = await storage.staking_pools.get("0");
  const poolAddress2 = await storage.staking_pools.get("1");
  const poolAddress3 = await storage.staking_pools.get("2");
  console.log(
    `Pool1 deployed at: ${poolAddress1}\n Pool2 deployed at: ${poolAddress2}\n Pool3 deployed at: ${poolAddress3}`,
  );
};
