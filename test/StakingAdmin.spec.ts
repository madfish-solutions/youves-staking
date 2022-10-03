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

import { ok, rejects, strictEqual } from "assert";

import { BigNumber } from "bignumber.js";

import { alice, bob, carol, dev } from "../scripts/sandbox/accounts";

import { confirmOperation } from "../scripts/confirmation";

import { fa2Storage } from "../storage/test/FA2";
import { stakingStorage } from "../storage/staking";
import { burnerStorage } from "./storage/Burner";
import { bakerRegistryStorage } from "./storage/BakerRegistry";
import { dexCoreStorage } from "storage/test/DexCore";

describe("Staking Admin Tests", async () => {
  var fa2: FA2;
  var qsGov: FA2;
  var utils: Utils;
  var staking: Staking;
  var burner: Burner;
  var bakerRegistry: BakerRegistry;
  var dexCore: DexCore;

  var precision = 10 ** 12;

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
        token_a_in: new BigNumber(10000),
        token_b_in: new BigNumber(10000),
        shares_receiver: alice.pkh,
        candidate: alice.pkh,
        deadline: String((await utils.getLastBlockTimestamp()) / 1000 + 100),
      },
      10000,
    );

    await dexCore.updateStorage({
      token_to_id: [[qsGov.contract.address, 0]],
    });

    burnerStorage.qsgov_lp = dexCore.contract.address;
    burnerStorage.qsgov.token = qsGov.contract.address;
    burnerStorage.qsgov.id = 0;

    stakingStorage.max_release_period = new BigNumber(180 * 60);
    stakingStorage.deposit_token = { id: 0, address: fa2.contract.address };
    stakingStorage.reward_token = { id: 0, address: qsGov.contract.address };
    stakingStorage.administrators.set(alice.pkh, 1);

    burner = await Burner.originate(utils.tezos, burnerStorage);
    staking = await Staking.originate(utils.tezos, stakingStorage);

    const transferOperation: TransactionOperation =
      await utils.tezos.contract.transfer({
        to: carol.pkh,
        amount: 50_000_000,
        mutez: true,
      });

    await confirmOperation(utils.tezos, transferOperation.hash);
  });

  describe("Add new owner", async () => {
    it("Shouldn't add new owner if not admin", async () => {
      await utils.setProvider(bob.sk);
      await rejects(staking.addAdmin(bob.pkh), (err: Error) => {
        ok(err.message === "21");
        return true;
      });
    });
    it("Should add new owner", async () => {
      await utils.setProvider(alice.sk);
      await staking.addAdmin(bob.pkh);
      await staking.updateStorage();

      ok(
        (
          (await staking.storage.administrators.get(bob.pkh)) as BigNumber
        ).toNumber() === 0,
      );
    });
  });
  describe("ConfirmOwner", async () => {
    it("Shouldnt confirm owner if not pending admin", async () => {
      await rejects(staking.confirmAdmin(), (err: Error) => {
        ok(err.message === "405");
        return true;
      });
    });
    it("Should confirm owner", async () => {
      await utils.setProvider(bob.sk);
      await staking.confirmAdmin();
      await staking.updateStorage();

      ok(
        (
          (await staking.storage.administrators.get(bob.pkh)) as BigNumber
        ).toNumber() === 1,
      );
    });
  });
  describe("Remove admin", async () => {
    it("Shouldn't remove admin if not admin", async () => {
      await utils.setProvider(carol.sk);
      await rejects(staking.removeAdmin(alice.pkh), (err: Error) => {
        ok(err.message === "21");
        return true;
      });
    });
    it("Should self-remove admin", async () => {
      await utils.setProvider(bob.sk);
      await staking.removeAdmin(bob.pkh);
      await staking.updateStorage();
      ok((await staking.storage.administrators.get(bob.pkh)) === undefined);
    });
    it("Should remove admin", async () => {
      await utils.setProvider(alice.sk);
      await staking.addAdmin(bob.pkh);
      await utils.setProvider(bob.sk);
      await staking.confirmAdmin();
      await utils.setProvider(alice.sk);
      await staking.removeAdmin(bob.pkh);
      await staking.updateStorage();

      ok((await staking.storage.administrators.get(bob.pkh)) === undefined);
    });
  });
  describe("Update_max_release_period", async () => {
    it("Shouldn't update max release period if not admin", async () => {
      await utils.setProvider(bob.sk);
      await rejects(staking.updateMaxReleasePeriod(100), (err: Error) => {
        ok(err.message === "21");
        return true;
      });
    });
    it("Should update max release period", async () => {
      await utils.setProvider(alice.sk);
      await staking.updateMaxReleasePeriod(100);
      await staking.updateStorage();

      ok(staking.storage.max_release_period.toNumber() === 100);
    });
  });
  describe("Vote", async () => {
    it("Shouldn't vote if not admin", async () => {
      await utils.setProvider(bob.sk);
      await rejects(
        staking.vote({ pair_id: 0, candidate: alice.pkh }),
        (err: Error) => {
          console.log(err.message);
          ok(err.message === "21");
          return true;
        },
      );
    });
    it("Should vote", async () => {
      await utils.setProvider(alice.sk);
      //await staking.vote({ pair_id: 0, candidate: alice.pkh });
      await staking.updateStorage();
    });
  });
  describe("Claim_baker_reward", async () => {
    it("Shouldn't claim baker reward if not admin", async () => {
      await utils.setProvider(bob.sk);
      await rejects(
        staking.claimBakerReward({
          receiver: alice.pkh,
          pair_id: new BigNumber(0),
        }),
        (err: Error) => {
          console.log(err.message);
          ok(err.message === "21");
          return true;
        },
      );
    });
    it("Should claim baker reward", async () => {
      await utils.setProvider(alice.sk);
      await staking.claimBakerReward({
        receiver: alice.pkh,
        pair_id: new BigNumber(0),
      });
      //await staking.updateStorage();
    });
  });
});
