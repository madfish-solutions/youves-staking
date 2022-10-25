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
  const operation = await factory.methods.remove_administrator(sender).send();
  await confirmOperation(tezos, operation.hash);
  console.log("Deployer removed from administrators");
};
