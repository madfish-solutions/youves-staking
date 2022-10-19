const fs = require("fs");

const { execSync } = require("child_process");

const { TezosToolkit } = require("@taquito/taquito");
const { InMemorySigner } = require("@taquito/signer");

const { confirmOperation } = require("./confirmation");

const env = require("../env");

const getLigo = (isDockerizedLigo, ligoVersion = env.ligoVersion) => {
  let path = "ligo";

  if (isDockerizedLigo) {
    path = `docker run -v $PWD:$PWD --rm -i ligolang/ligo:${ligoVersion}`;

    try {
      execSync(`${path}  --help`);
    } catch (err) {
      path = "ligo";

      execSync(`${path}  --help`);
    }
  } else {
    try {
      execSync(`${path}  --help`);
    } catch (err) {
      path = `docker run -v $PWD:$PWD --rm -i ligolang/ligo:${ligoVersion}`;

      execSync(`${path}  --help`);
    }
  }

  return path;
};

const getMigrationsList = () => {
  return fs
    .readdirSync(env.migrationsDir)
    .filter(file => file.endsWith(".js"))
    .map(file => file.slice(0, file.length - 3));
};

const migrate = async (tezos, contract, storage, network) => {
  try {
    const artifacts = JSON.parse(
      fs.readFileSync(
        `${env.buildDir}/${contract}/step_000_cont_0_contract.json`,
      ),
    );
    const operation = await tezos.contract
      .originate({
        code: artifacts,
        storage: storage,
        fee: 1000000,
        gasLimit: 1040000,
        storageLimit: 20000,
      })
      .catch(e => {
        console.error(e);

        return { contractAddress: null };
      });

    await confirmOperation(tezos, operation.hash);

    const addresses = JSON.parse(
      fs.readFileSync(`compilations/addresses.json`),
    );
    addresses[network][contract] = operation.contractAddress;
    fs.writeFileSync(`compilations/addresses.json`, JSON.stringify(addresses));

    return operation.contractAddress;
  } catch (e) {
    console.error(e);
  }
};

const getDeployedAddress = (contract, network) => {
  try {
    const artifacts = JSON.parse(
      fs.readFileSync(`${env.buildDir}/${contract}.json`),
    );

    return artifacts.networks[network][contract];
  } catch (e) {
    console.error(e);
  }
};

const runMigrations = async options => {
  try {
    const migrations = getMigrationsList();

    options.network = options.network || "development";
    options.optionFrom = options.from || 0;
    options.optionTo = options.to || migrations.length;

    const networkConfig = env.networks[options.network];
    const tezos = new TezosToolkit(networkConfig.rpc);

    tezos.setProvider({
      config: {
        confirmationPollingTimeoutSecond: env.confirmationPollingTimeoutSecond,
      },
      rpc: networkConfig.rpc,
      signer: await InMemorySigner.fromSecretKey(networkConfig.secretKey),
    });

    for (const migration of migrations) {
      const execMigration = require(`../${env.migrationsDir}/${migration}.js`);

      await execMigration(tezos, options.network);
    }
  } catch (e) {
    console.error(e);
  }
};

module.exports = {
  getLigo,
  getMigrationsList,
  getDeployedAddress,
  migrate,
  runMigrations,
  env,
};
