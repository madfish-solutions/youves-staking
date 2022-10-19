const { MichelsonMap } = require("@taquito/michelson-encoder");
const { migrate } = require("../scripts/helpers");

const { stakingFactoryStorage } = require("../storage/stakingFactory");

module.exports = async (tezos, network) => {
  const sender = await tezos.signer.publicKeyHash();
  stakingFactoryStorage.administrators.set(sender, 1);
  const factory = await migrate(
    tezos,
    "StakingPoolFactory",
    stakingFactoryStorage,
    network,
  );

  console.log(`Staking pool factory deployed at: ${factory}`);
};
