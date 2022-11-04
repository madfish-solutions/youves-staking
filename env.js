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
      factoryAdmin: "tz1SiQVaEjEgPwvhq5ACt5YbtLk7i4MtBCsm",
      pools: {
        0: {
          deposit_token: {
            token_type: "FA2",
            token_id: 0,
            token_address: "KT1GPJDTf8GZspCcanaG2KhMvGu3NJRqurat",
          },
          deposit_token_is_v2: true,
          reward_token: {
            token_type: "FA2",
            token_id: 0,
            token_address: "KT19363aZDTjeRyoDkSLZhCk62pS4xfvxo6c",
          },
          max_release_period: 100,
          administrators: MichelsonMap.fromLiteral({ [alice.pkh]: "1" }),
          expected_rewards: 700000000,
        },
        1: {
          deposit_token: {
            token_type: "FA2",
            token_id: 1,
            token_address: "KT1GPJDTf8GZspCcanaG2KhMvGu3NJRqurat",
          },
          deposit_token_is_v2: true,
          reward_token: {
            token_type: "FA2",
            token_id: 0,
            token_address: "KT19363aZDTjeRyoDkSLZhCk62pS4xfvxo6c",
          },
          max_release_period: 100,
          administrators: MichelsonMap.fromLiteral({ [alice.pkh]: "1" }),
          expected_rewards: 300000000,
        },
        2: {
          deposit_token: {
            token_type: "FA2",
            token_id: 2,
            token_address: "KT1GPJDTf8GZspCcanaG2KhMvGu3NJRqurat",
          },
          deposit_token_is_v2: true,
          reward_token: {
            token_type: "FA2",
            token_id: 0,
            token_address: "KT19363aZDTjeRyoDkSLZhCk62pS4xfvxo6c",
          },
          max_release_period: 100,
          administrators: MichelsonMap.fromLiteral({ [alice.pkh]: 1 }),
          expected_rewards: 100000000,
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
      factoryAdmin: "tz1SiQVaEjEgPwvhq5ACt5YbtLk7i4MtBCsm",
      pools: {
        0: {
          deposit_token: {
            token_type: "FA2",
            token_id: 0,
            token_address: "KT1MK1fWszdSA9cASnu7X6b6jCjyhVMRfT8K",
          },
          deposit_token_is_v2: false,
          reward_token: {
            token_type: "FA2",
            token_id: 0,
            token_address: "KT19363aZDTjeRyoDkSLZhCk62pS4xfvxo6c",
          },
          max_release_period: 15552000,
          administrators: MichelsonMap.fromLiteral({
            tz1SiQVaEjEgPwvhq5ACt5YbtLk7i4MtBCsm: 1,
          }),
          expected_rewards: 600000000,
        },
        // 1: {
        //   deposit_token: {
        //     token_type: "FA2",
        //     token_id: 1,
        //     token_address: "KT1GPJDTf8GZspCcanaG2KhMvGu3NJRqurat",
        //   },
        //   deposit_token_is_v2: true,
        //   reward_token: {
        //     token_type: "FA2",
        //     token_id: 0,
        //     token_address: "KT19363aZDTjeRyoDkSLZhCk62pS4xfvxo6c",
        //   },
        //   max_release_period: 7776000,
        //   administrators: MichelsonMap.fromLiteral({
        //     tz1SiQVaEjEgPwvhq5ACt5YbtLk7i4MtBCsm: 1,
        //   }),
        //   expected_rewards: 300000000,
        // },
        // 2: {
        //   deposit_token: {
        //     token_type: "FA2",
        //     token_id: 2,
        //     token_address: "KT1GPJDTf8GZspCcanaG2KhMvGu3NJRqurat",
        //   },
        //   deposit_token_is_v2: true,
        //   reward_token: {
        //     token_type: "FA2",
        //     token_id: 0,
        //     token_address: "KT19363aZDTjeRyoDkSLZhCk62pS4xfvxo6c",
        //   },
        //   max_release_period: 7776000,
        //   administrators: MichelsonMap.fromLiteral({
        //     tz1SiQVaEjEgPwvhq5ACt5YbtLk7i4MtBCsm: 1,
        //   }),
        //   expected_rewards: 100000000,
        // },
      },
    },
    mainnet: {
      rpc: "https://mainnet.smartpy.io",
      port: 443,
      network_id: "*",
      secretKey: mainnetDeployer.sk,
      dexAddress: "KT1M2b4XCUq5zqMNqQAotUar7BSUiNDE4Dgh",
      quipuAddress: "KT1UG6PdaKoJcc3yD6mkFVfxnS1uJeW3cGeX",
      factoryAdmin: "tz1SiQVaEjEgPwvhq5ACt5YbtLk7i4MtBCsm",
      pools: {
        0: {
          deposit_token: {
            token_type: "FA2",
            token_id: 0,
            token_address: "KT1M2b4XCUq5zqMNqQAotUar7BSUiNDE4Dgh",
          },
          deposit_token_is_v2: false,
          reward_token: {
            token_type: "FA2",
            token_id: 0,
            token_address: "KT1UG6PdaKoJcc3yD6mkFVfxnS1uJeW3cGeX",
          },
          max_release_period: 15552000,
          administrators: MichelsonMap.fromLiteral({
            tz1SiQVaEjEgPwvhq5ACt5YbtLk7i4MtBCsm: 1,
          }),
          expected_rewards: 600000000,
        },
        // 1: {
        //   deposit_token: {
        //     token_type: "FA2",
        //     token_id: 1,
        //     token_address: "KT1J8Hr3BP8bpbfmgGpRPoC9nAMSYtStZG43",
        //   },
        //   deposit_token_is_v2: true,
        //   reward_token: {
        //     token_type: "FA2",
        //     token_id: 0,
        //     token_address: "KT193D4vozYnhGJQVtw7CoxxqphqUEEwK6Vb",
        //   },
        //   max_release_period: 7776000,
        //   administrators: MichelsonMap.fromLiteral({
        //     tz1SiQVaEjEgPwvhq5ACt5YbtLk7i4MtBCsm: 1,
        //   }),
        //   expected_rewards: 100000000,
        // },
        // 2: {
        //   deposit_token: {
        //     token_type: "FA2",
        //     token_id: 2,
        //     token_address: "KT1J8Hr3BP8bpbfmgGpRPoC9nAMSYtStZG43",
        //   },
        //   deposit_token_is_v2: true,
        //   reward_token: {
        //     token_type: "FA2",
        //     token_id: 0,
        //     token_address: "KT193D4vozYnhGJQVtw7CoxxqphqUEEwK6Vb",
        //   },
        //   max_release_period: 7776000,
        //   administrators: MichelsonMap.fromLiteral({
        //     tz1SiQVaEjEgPwvhq5ACt5YbtLk7i4MtBCsm: 1,
        //   }),
        //   expected_rewards: 300000000,
        // },
        // 3: {
        //   deposit_token: {
        //     token_type: "FA2",
        //     token_id: 3,
        //     token_address: "KT1J8Hr3BP8bpbfmgGpRPoC9nAMSYtStZG43",
        //   },
        //   deposit_token_is_v2: true,
        //   reward_token: {
        //     token_type: "FA2",
        //     token_id: 0,
        //     token_address: "KT193D4vozYnhGJQVtw7CoxxqphqUEEwK6Vb",
        //   },
        //   max_release_period: 7776000,
        //   administrators: MichelsonMap.fromLiteral({
        //     tz1SiQVaEjEgPwvhq5ACt5YbtLk7i4MtBCsm: 1,
        //   }),
        //   expected_rewards: 700000000,
        // },
      },
    },
  },
};
