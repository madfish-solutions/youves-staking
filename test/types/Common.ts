import { BigNumber } from "bignumber.js";

export type FA12Token = string;

export type FA2Token = {
  id: number;
  token: string;
};

export type Fa2 = { id: number; address: string };
export type Tez = undefined;
export type Token = { fa2: FA2Token } | { fa12: FA12Token } | { tez: Tez };

export type PauseFarmParam = {
  fid: number;
  pause: boolean;
};

export type DepositParams = {
  token_amount: number;
  stake_id: number;
};

export type DexVoteParams = {
  pair_id: number;
  candidate: string;
  referral_code?: number;
};

export type WithdrawParams = {
  fid: number;
  amt: number;
  receiver: string;
  rewards_receiver: string;
  referral_code?: number;
};

export type HarvestParams = {
  fid: number;
  rewards_receiver: string;
};

export type UserInfoType = {
  last_staked: string;
  staked: number;
  earned: number;
  claimed: number;
  prev_earned: number;
  prev_staked: number;
  allowances: string[];
};

export type WithdrawData = {
  actualUserWithdraw: BigNumber;
  wirthdrawCommission: BigNumber;
};

export type WithdrawFarmDepoParams = {
  fid: number;
  amt: number;
};

export type BanBakerParam = {
  baker: string;
  period: number;
};

export type Meta = {
  key: string;
  value: string;
};

export type UpdTokMetaParams = {
  token_id: number;
  token_info: Meta[];
};

export type IsV2LP = {
  fid: number;
  is_v2_lp: boolean;
};
