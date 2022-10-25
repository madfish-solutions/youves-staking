const { MichelsonMap } = require("@taquito/michelson-encoder");
const { migrate } = require("../scripts/helpers");

const { stakingFactoryStorage } = require("../storage/stakingFactory");
const { networks } = require("../env");

module.exports = async (tezos, network) => {
  const networkSettings = networks[network];
  const sender = await tezos.signer.publicKeyHash();
  stakingFactoryStorage.administrators.set(sender, 1);
  stakingFactoryStorage.administrators.set(networkSettings.factoryAdmin, 1);
  const factory = await migrate(
    tezos,
    "StakingPoolFactory",
    stakingFactoryStorage,
    network,
  );

  console.log(`Staking pool factory deployed at: ${factory}`);
};
