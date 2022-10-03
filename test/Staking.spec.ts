import { FA12 } from "./helpers/FA12";
import { FA2 } from "./helpers/FA2";
import { Utils, zeroAddress } from "./helpers/Utils";
import { Staking } from "./helpers/Staking";
import { Burner } from "./helpers/Burner";
import { BakerRegistry } from "./helpers/BakerRegistry";
import { DexCore } from "./helpers/DexCore";

import {
  UpdateOperatorParam,
  TransferParam,
  UserFA2LPInfo,
  UserFA2Info,
} from "./types/FA2";
import {} from "./types/Staking";
import {} from "./types/Common";
import { UserFA12Info } from "./types/FA12";

import { MichelsonMap } from "@taquito/michelson-encoder";
import { TransactionOperation } from "@taquito/taquito";

import { equal, ok, rejects, strictEqual } from "assert";
import { BigNumber } from "bignumber.js";

import { alice, bob, carol, dev } from "../scripts/sandbox/accounts";

import { confirmOperation } from "../scripts/confirmation";

import { fa2Storage } from "../storage/test/FA2";
import { stakingStorage } from "../storage/staking";
import { burnerStorage } from "./storage/Burner";
import { bakerRegistryStorage } from "./storage/BakerRegistry";
import { dexCoreStorage } from "storage/test/DexCore";

describe("Staking Tests", async () => {
  var fa2: FA2;
  var qsGov: FA2;
  var utils: Utils;
  var staking: Staking;
  var burner: Burner;
  var bakerRegistry: BakerRegistry;
  var dexCore: DexCore;

  var precision = 10 ** 12;

  const aliseStakesTime = [];

  before("setup", async () => {
    utils = new Utils();

    await utils.init(alice.sk, true);

    fa2 = await FA2.originate(utils.tezos, fa2Storage);
    qsGov = await FA2.originate(utils.tezos, fa2Storage);

    bakerRegistry = await BakerRegistry.originate(
      utils.tezos,
      bakerRegistryStorage,
    );

    dexCoreStorage.storage.baker_registry = bakerRegistry.contract.address;
    dexCoreStorage.storage.admin = alice.pkh;
    dexCoreStorage.storage.collecting_period = new BigNumber(12);
    dexCore = await DexCore.originate(utils.tezos, dexCoreStorage);

    await dexCore.setLambdas();

    const updateOperatorParam: UpdateOperatorParam = {
      add_operator: {
        owner: alice.pkh,
        operator: dexCore.contract.address,
        token_id: 0,
      },
    };

    await qsGov.updateOperators([updateOperatorParam]);
    await dexCore.launchExchange(
      {
        pair: {
          token_a: {
            fa2: { token: qsGov.contract.address, id: 0 },
          },
          token_b: { tez: undefined },
        },
        token_a_in: new BigNumber(50000),
        token_b_in: new BigNumber(50000),
        shares_receiver: alice.pkh,
        candidate: alice.pkh,
        deadline: String((await utils.getLastBlockTimestamp()) / 1000 + 100),
      },
      50000,
    );

    await dexCore.updateStorage({
      token_to_id: [[qsGov.contract.address, 0]],
    });

    const transferParams: any = [
      {
        from_: alice.pkh,
        txs: [
          {
            to_: bob.pkh,
            token_id: 0,
            amount: 5000,
          },
        ],
      },
    ];

    await dexCore.transfer(transferParams);

    burnerStorage.qsgov_lp = dexCore.contract.address;
    burnerStorage.qsgov.token = qsGov.contract.address;
    burnerStorage.qsgov.id = 0;

    stakingStorage.max_release_period = new BigNumber(15);
    stakingStorage.deposit_token = { id: 0, address: dexCore.contract.address };
    stakingStorage.reward_token = { id: 0, address: qsGov.contract.address };
    stakingStorage.administrators.set(alice.pkh, 1);

    burner = await Burner.originate(utils.tezos, burnerStorage);
    staking = await Staking.originate(utils.tezos, stakingStorage);

    const transferOperation: TransactionOperation =
      await utils.tezos.contract.transfer({
        to: carol.pkh,
        amount: 1_000_000,
        mutez: true,
      });

    await confirmOperation(utils.tezos, transferOperation.hash);
    await qsGov.transfer([
      {
        from_: alice.pkh,
        txs: [{ to_: staking.contract.address, token_id: 0, amount: 10000 }],
      },
    ]);
  });

  describe("Deposit", async () => {
    it("Should deposit", async () => {
      const prevAliceBalance = await dexCore.getBalance(alice.pkh);
      console.log("aliceStartDeposit at:", await utils.getLastBlockTimestamp());
      await dexCore.updateOperators([
        {
          add_operator: {
            owner: alice.pkh,
            operator: staking.contract.address,
            token_id: 0,
          },
        },
      ]);
      await staking.deposit({ token_amount: 1000, stake_id: 0 });
      await staking.updateStorage();
      const aliceBalance = await dexCore.getBalance(alice.pkh);
      const aliceStakes = await staking.storage.stakes_owner_lookup.get(
        alice.pkh,
      );
      const stake: any = await staking.storage.stakes.get("1");
      console.log(stake);
      console.log("GlobalDiscFactor:", staking.storage.disc_factor);
      strictEqual(stake.stake.toNumber(), 1000);
      strictEqual(aliceStakes[0].toNumber(), 1);
      strictEqual(
        aliceBalance.toNumber(),
        prevAliceBalance.minus(1000).toNumber(),
      );
      strictEqual(staking.storage.total_stake.toNumber(), 1000);
      strictEqual(staking.storage.last_stake_id.toNumber(), 1);
    });
    it("Should deposit in new stake", async () => {
      const prevAliceBalance = await dexCore.getBalance(alice.pkh);
      const prevTotalStake = staking.storage.total_stake.toNumber();
      await dexCore.updateOperators([
        {
          add_operator: {
            owner: alice.pkh,
            operator: staking.contract.address,
            token_id: 0,
          },
        },
      ]);
      await staking.deposit({ token_amount: 1000, stake_id: 0 });
      await staking.updateStorage();
      console.log("GlobalDiscFactor:", staking.storage.disc_factor);
      const aliceBalance = await dexCore.getBalance(alice.pkh);
      const totalStake = staking.storage.total_stake.toNumber();
      const aliceStakes = await staking.storage.stakes_owner_lookup.get(
        alice.pkh,
      );
      const stake: any = await staking.storage.stakes.get("2");
      console.log(stake);

      strictEqual(stake.stake.toNumber(), 1000);
      strictEqual(aliceStakes[0].toNumber(), 1);
      strictEqual(aliceStakes[1].toNumber(), 2);
      strictEqual(
        aliceBalance.toNumber(),
        prevAliceBalance.minus(1000).toNumber(),
      );
      strictEqual(staking.storage.last_stake_id.toNumber(), 2);

      strictEqual(totalStake, prevTotalStake + 1000);
    });
    it("Should deposit in exist stake", async () => {
      const prevAliceBalance = await dexCore.getBalance(alice.pkh);
      const prevTotalStake = staking.storage.total_stake.toNumber();

      await staking.deposit({ token_amount: 1000, stake_id: 1 });
      await staking.updateStorage();
      const aliceBalance = await dexCore.getBalance(alice.pkh);
      const totalStake = staking.storage.total_stake.toNumber();

      const stake: any = await staking.storage.stakes.get("1");
      console.log("AliceStake :", stake);
      console.log("GlobalDiscFactor :", staking.storage.disc_factor);
      strictEqual(stake.stake.toNumber(), 2000);
      strictEqual(
        aliceBalance.toNumber(),
        prevAliceBalance.minus(1000).toNumber(),
      );
      strictEqual(staking.storage.last_stake_id.toNumber(), 2);

      strictEqual(totalStake, prevTotalStake + 1000);
    });
    it("Should new deposit Bob", async () => {
      // await qsGov.transfer([
      //   {
      //     from_: alice.pkh,
      //     txs: [{ to_: staking.contract.address, token_id: 0, amount: 10000 }],
      //   },
      // ]);
      await utils.setProvider(bob.sk);
      const prevBobBalance = await dexCore.getBalance(bob.pkh);
      const prevTotalStake = staking.storage.total_stake.toNumber();
      await dexCore.updateOperators([
        {
          add_operator: {
            owner: bob.pkh,
            operator: staking.contract.address,
            token_id: 0,
          },
        },
      ]);
      await staking.deposit({ token_amount: 1000, stake_id: 0 });
      await staking.updateStorage();
      const bobBalance = await dexCore.getBalance(bob.pkh);
      const totalStake = staking.storage.total_stake.toNumber();
      const bobStakes = await staking.storage.stakes_owner_lookup.get(bob.pkh);
      const stake: any = await staking.storage.stakes.get("3");
      console.log(stake);
      strictEqual(stake.stake.toNumber(), 1000);
      strictEqual(bobStakes[0].toNumber(), 3);

      strictEqual(bobBalance.toNumber(), prevBobBalance.minus(1000).toNumber());
      strictEqual(staking.storage.last_stake_id.toNumber(), 3);

      strictEqual(totalStake, prevTotalStake + 1000);
    });
    it("Shouldn't deposit in exists stake if a user not owner", async () => {
      await utils.setProvider(bob.sk);
      await dexCore.updateOperators([
        {
          add_operator: {
            owner: bob.pkh,
            operator: staking.contract.address,
            token_id: 0,
          },
        },
      ]);
      await rejects(
        staking.deposit({ token_amount: 1000, stake_id: 1 }),
        (err: Error) => {
          ok(err.message === "404"); // must be 404
          return true;
        },
      );
    });
  });
  describe("Withdraw", async () => {
    it("Should withdraw stake_id 3 Bob", async () => {
      await utils.setProvider(bob.sk);
      const prevBobBalance = await dexCore.getBalance(bob.pkh);
      const prevTotalStake = staking.storage.total_stake.toNumber();
      const prevRewardBalance = await qsGov.getBalance(bob.pkh);
      const prevStake = await staking.storage.stakes.get("3");
      console.log("GlobalDiscFactor :", staking.storage.disc_factor);
      console.log("BobPrevStake :", prevStake);
      console.log("TotalStake: ", staking.storage.total_stake.toNumber());
      await utils.bakeBlocks(5);
      await staking.withdraw(3);
      await staking.updateStorage();
      const rewardBalance = await qsGov.getBalance(bob.pkh);
      const bobBalance = await dexCore.getBalance(bob.pkh);
      const totalStake = staking.storage.total_stake.toNumber();

      const stake: any = await staking.storage.stakes.get("3");
      console.log(rewardBalance.minus(prevRewardBalance));
      strictEqual(stake, undefined);
      strictEqual(bobBalance.toNumber(), prevBobBalance.plus(1000).toNumber());
      strictEqual(staking.storage.last_stake_id.toNumber(), 3);

      strictEqual(totalStake, prevTotalStake - 1000);
    });
    it("Should withdraw stake_id 1 Alice", async () => {
      await utils.setProvider(alice.sk);
      const prevAliceBalance = await dexCore.getBalance(alice.pkh);
      const prevTotalStake = staking.storage.total_stake.toNumber();
      const prevRewardBalance = await qsGov.getBalance(alice.pkh);

      console.log("aliceWithdraw at:", await utils.getLastBlockTimestamp());
      console.log("GlobalDiscFactor :", staking.storage.disc_factor);
      console.log("TotalStake: ", staking.storage.total_stake.toNumber());
      const prevStake = await staking.storage.stakes.get("1");
      console.log("AlicePrevStake :", prevStake);
      await utils.bakeBlocks(10);
      await staking.withdraw(1);
      await staking.updateStorage();
      const rewardBalance = await qsGov.getBalance(alice.pkh);
      const aliceBalance = await dexCore.getBalance(alice.pkh);
      const totalStake = staking.storage.total_stake.toNumber();
      const aliceStakes = await staking.storage.stakes_owner_lookup.get(
        alice.pkh,
      );
      const stake: any = await staking.storage.stakes.get("1");
      console.log(rewardBalance.minus(prevRewardBalance));
      strictEqual(stake, undefined);
      strictEqual(aliceStakes[0].toNumber(), 2);
      strictEqual(
        aliceBalance.toNumber(),
        prevAliceBalance.plus(2000).toNumber(),
      );
      strictEqual(staking.storage.last_stake_id.toNumber(), 3);

      strictEqual(totalStake, prevTotalStake - 2000);
    });
  });
});
