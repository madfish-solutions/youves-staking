import {
  TransactionOperation,
  OriginationOperation,
  TezosToolkit,
  MichelsonMap,
  Contract,
} from "@taquito/taquito";

import { BigNumber } from "bignumber.js";

import fs from "fs";

import env from "../../env";

import { confirmOperation } from "../../scripts/confirmation";

import { DepositParams, DexVoteParams } from "../types/Common";
import { StakingStorageType } from "../types/Staking";
import { TransferParam, UpdateOperatorParam } from "test/types/FA2";

import { Utils, zeroAddress } from "./Utils";
import { WithdrawProfit } from "test/types/DexCore";

export class Staking {
  contract: Contract;
  storage: StakingStorageType;
  tezos: TezosToolkit;

  constructor(contract: Contract, tezos: TezosToolkit) {
    this.contract = contract;
    this.tezos = tezos;
  }

  static async init(
    tFarmAddress: string,
    tezos: TezosToolkit,
  ): Promise<Staking> {
    return new Staking(await tezos.contract.at(tFarmAddress), tezos);
  }

  static async originate(
    tezos: TezosToolkit,
    storage: StakingStorageType,
  ): Promise<Staking> {
    const artifacts: any = JSON.parse(
      fs.readFileSync(`./test/contracts/staking.json`).toString(),
    );
    const operation: OriginationOperation = await tezos.contract
      .originate({
        code: artifacts.michelson,
        storage: storage,
      })
      .catch(e => {
        console.error(e);

        return null;
      });
    await confirmOperation(tezos, operation.hash);

    return new Staking(
      await tezos.contract.at(operation.contractAddress),
      tezos,
    );
  }

  async updateStorage() {
    const storage: StakingStorageType = await this.contract.storage();

    this.storage = storage;

    return storage;
  }

  async default(mutezAmount: number): Promise<TransactionOperation> {
    const operation: TransactionOperation = await this.contract.methods
      .default([])
      .send({ amount: mutezAmount, mutez: true });

    await confirmOperation(this.tezos, operation.hash);

    return operation;
  }

  async addAdmin(newAdmin: string): Promise<TransactionOperation> {
    const operation: TransactionOperation = await this.contract.methods
      .propose_administrator(newAdmin)
      .send();

    await confirmOperation(this.tezos, operation.hash);

    return operation;
  }

  async confirmAdmin(): Promise<TransactionOperation> {
    const operation: TransactionOperation = await this.contract.methods
      .set_administrator([])
      .send();

    await confirmOperation(this.tezos, operation.hash);

    return operation;
  }

  async removeAdmin(admin: string): Promise<TransactionOperation> {
    const operation: TransactionOperation = await this.contract.methods
      .remove_administrator(admin)
      .send();

    await confirmOperation(this.tezos, operation.hash);

    return operation;
  }

  async updateMaxReleasePeriod(
    maxReleasePeriod: number,
  ): Promise<TransactionOperation> {
    const operation: TransactionOperation = await this.contract.methods
      .update_max_release_period(maxReleasePeriod)
      .send();

    await confirmOperation(this.tezos, operation.hash);

    return operation;
  }

  async deposit(
    params: DepositParams,
    mutezAmount: number = 0,
  ): Promise<TransactionOperation> {
    const operation: TransactionOperation = await this.contract.methodsObject
      .deposit(params)
      .send({ amount: mutezAmount, mutez: true });

    await confirmOperation(this.tezos, operation.hash);

    return operation;
  }

  async claim(stakeId: number): Promise<TransactionOperation> {
    const operation: TransactionOperation = await this.contract.methods
      .claim(stakeId)
      .send();

    await confirmOperation(this.tezos, operation.hash);

    return operation;
  }

  async withdraw(stakeId: number): Promise<TransactionOperation> {
    const operation: TransactionOperation = await this.contract.methods
      .withdraw(stakeId)
      .send({ storageLimit: 10000 });

    await confirmOperation(this.tezos, operation.hash);

    return operation;
  }
  async vote(voteParams: DexVoteParams): Promise<TransactionOperation> {
    const operation: TransactionOperation = await this.contract.methodsObject
      .vote(voteParams)
      .send();

    await confirmOperation(this.tezos, operation.hash);

    return operation;
  }
  async claimBakerReward(
    params: WithdrawProfit,
  ): Promise<TransactionOperation> {
    const operation: TransactionOperation = await this.contract.methodsObject
      .claim_baker_reward(params)
      .send();

    await confirmOperation(this.tezos, operation.hash);

    return operation;
  }

  async transfer(params: TransferParam[]): Promise<TransactionOperation> {
    const operation: TransactionOperation = await this.contract.methods
      .transfer(params)
      .send();

    await confirmOperation(this.tezos, operation.hash);

    return operation;
  }

  async updateOperators(
    updateOperatorsParams: UpdateOperatorParam[],
  ): Promise<TransactionOperation> {
    const operation: TransactionOperation = await this.contract.methods
      .update_operators(updateOperatorsParams)
      .send();

    await confirmOperation(this.tezos, operation.hash);

    return operation;
  }
}
