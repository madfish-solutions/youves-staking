const { MichelsonMap } = require("@taquito/michelson-encoder");
const { alice, dev, mainnetDeployer } = require("./scripts/sandbox/accounts");

module.exports = {
  confirmationPollingTimeoutSecond: 500000,
  syncInterval: 0, // 0 for tests, 5000 for deploying
  confirmTimeout: 90000, // 90000 for tests, 180000 for deploying
  buildDir: "compilations/out",
  migrationsDir: "migrations",
  contractsDir: "contracts/main",
  ligoVersion: "0.35.0",
  network: "development",
  networks: {
    development: {
      rpc: "http://localhost:8732",
      network_id: "*",
      secretKey: alice.sk,
      dexAddress: "KT1GPJDTf8GZspCcanaG2KhMvGu3NJRqurat",
      quipuAddress: "KT19363aZDTjeRyoDkSLZhCk62pS4xfvxo6c",
      pools: {
        0: {
          deposit_token: {
            token_id: 0,
            token_address: "KT1GPJDTf8GZspCcanaG2KhMvGu3NJRqurat",
          },
          deposit_token_is_v2: true,
          reward_token: {
            token_id: 0,
            token_address: "KT19363aZDTjeRyoDkSLZhCk62pS4xfvxo6c",
          },
          max_release_period: 100,
          administrators: MichelsonMap.fromLiteral({ [alice.pkh]: 1 }),
        },
        1: {
          deposit_token: {
            token_id: 1,
            token_address: "KT1GPJDTf8GZspCcanaG2KhMvGu3NJRqurat",
          },
          deposit_token_is_v2: true,
          reward_token: {
            token_id: 0,
            token_address: "KT19363aZDTjeRyoDkSLZhCk62pS4xfvxo6c",
          },
          max_release_period: 100,
          administrators: MichelsonMap.fromLiteral({ [alice.pkh]: 1 }),
        },
        2: {
          deposit_token: {
            token_id: 2,
            token_address: "KT1GPJDTf8GZspCcanaG2KhMvGu3NJRqurat",
          },
          deposit_token_is_v2: true,
          reward_token: {
            token_id: 0,
            token_address: "KT19363aZDTjeRyoDkSLZhCk62pS4xfvxo6c",
          },
          max_release_period: 100,
          administrators: MichelsonMap.fromLiteral({ [alice.pkh]: 1 }),
        },
      },
    },
    ghostnet: {
      rpc: "https://ghostnet.ecadinfra.com/",
      port: 443,
      network_id: "*",
      secretKey: dev.sk,
      dexAddress: "KT1GPJDTf8GZspCcanaG2KhMvGu3NJRqurat",
      quipuAddress: "KT19363aZDTjeRyoDkSLZhCk62pS4xfvxo6c",
      pools: {
        0: {
          deposit_token: {
            token_id: 0,
            token_address: "KT1GPJDTf8GZspCcanaG2KhMvGu3NJRqurat",
          },
          deposit_token_is_v2: true,
          reward_token: {
            token_id: 0,
            token_address: "KT19363aZDTjeRyoDkSLZhCk62pS4xfvxo6c",
          },
          max_release_period: 100,
          administrators: MichelsonMap.fromLiteral({ [dev.pkh]: 1 }),
        },
        1: {
          deposit_token: {
            token_id: 1,
            token_address: "KT1GPJDTf8GZspCcanaG2KhMvGu3NJRqurat",
          },
          deposit_token_is_v2: true,
          reward_token: {
            token_id: 0,
            token_address: "KT19363aZDTjeRyoDkSLZhCk62pS4xfvxo6c",
          },
          max_release_period: 100,
          administrators: MichelsonMap.fromLiteral({ [dev.pkh]: 1 }),
        },
        2: {
          deposit_token: {
            token_id: 2,
            token_address: "KT1GPJDTf8GZspCcanaG2KhMvGu3NJRqurat",
          },
          deposit_token_is_v2: true,
          reward_token: {
            token_id: 0,
            token_address: "KT19363aZDTjeRyoDkSLZhCk62pS4xfvxo6c",
          },
          max_release_period: 100,
          administrators: MichelsonMap.fromLiteral({ [dev.pkh]: 1 }),
        },
      },
    },
    mainnet: {
      rpc: "https://mainnet.smartpy.io",
      port: 443,
      network_id: "*",
      secretKey: mainnetDeployer.sk,
      dexAddress: "KT1GPJDTf8GZspCcanaG2KhMvGu3NJRqurat",
      quipuAddress: "KT19363aZDTjeRyoDkSLZhCk62pS4xfvxo6c",
      pools: {
        0: {
          deposit_token: {
            token_id: 0,
            token_address: "KT1GPJDTf8GZspCcanaG2KhMvGu3NJRqurat",
          },
          deposit_token_is_v2: true,
          reward_token: {
            token_id: 0,
            token_address: "KT19363aZDTjeRyoDkSLZhCk62pS4xfvxo6c",
          },
          max_release_period: 100,
          administrators: { [dev.pkh]: 1 },
        },
        1: {
          deposit_token: {
            token_id: 1,
            token_address: "KT1GPJDTf8GZspCcanaG2KhMvGu3NJRqurat",
          },
          deposit_token_is_v2: true,
          reward_token: {
            token_id: 0,
            token_address: "KT19363aZDTjeRyoDkSLZhCk62pS4xfvxo6c",
          },
          max_release_period: 100,
          administrators: { [dev.pkh]: 1 },
        },
        2: {
          deposit_token: {
            token_id: 2,
            token_address: "KT1GPJDTf8GZspCcanaG2KhMvGu3NJRqurat",
          },
          deposit_token_is_v2: true,
          reward_token: {
            token_id: 0,
            token_address: "KT19363aZDTjeRyoDkSLZhCk62pS4xfvxo6c",
          },
          max_release_period: 100,
          administrators: { [dev.pkh]: 1 },
        },
      },
    },
  },
};
