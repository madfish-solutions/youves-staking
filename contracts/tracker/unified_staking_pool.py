import smartpy as sp

import utils.error_codes as Errors
import utils.constants as Constants

from utils.administrable_mixin import SingleAdministrableMixin
from utils.contract_utils import Utils
from utils.fa2 import OperatorKey, BalanceOf, FA2ErrorMessage, UpdateOperator, Transfer
from utils.internal_mixin import InternalMixin

class Fa2TokenType:
    def get_type():
        return sp.TRecord(
            id=sp.TNat,
            address=sp.TAddress,
        ).layout(("id", "address"))

    def make(token_id, token_address):
        return sp.set_type_expr(
            sp.record(
                id=token_id,
                address=token_address,
            ),
            Fa2TokenType.get_type(),
        )

class Stake:
    def get_type():
        return sp.TRecord(
            stake=sp.TNat,  # stake
            disc_factor=sp.TNat,  # disc_factor
            age_timestamp=sp.TTimestamp,  # age
        ).layout(("stake", ("disc_factor", "age_timestamp")))

    def make(stake, disc_factor, age_timestamp):
        return sp.set_type_expr(
            sp.record(
                stake=stake,
                disc_factor=disc_factor,
                age_timestamp=age_timestamp,
            ),
            Stake.get_type(),
        )

class UnifiedStakingPool(sp.Contract, InternalMixin, SingleAdministrableMixin):
    """The unified staking pool allows a user to stake their tokens and then get YOU rewards. The rewards are coming from fees of the other parts
    of the platform (farms, mint, etc.). The rewards are in different tokens and they are swapped to YOU tokens during a trading window. The swap
    is using an oracle to predict the expected amount of YOU tokens received and fails if the minimum received is not respecting the oracle.

    Each stake has an age and once it reaches maturity (180 days) the user can withdraw the entire stake, otherwise only a percentage directly proportional
    to the stake age can be withdrawn.

    Args:
        (sp.Contract): this is a smartpy contract
        (InternalMixin): mixin used whenever we need external data and hence have to trigger an internal call (to process after we received said external data)
        (SingleAdministrableMixin): mixin used whenever we have a single administrator.
    """

    def get_init_storage(self):
        """Returns the initial storage of the contract used for inheritance of smartpy contracts

        Returns:
            dict: initial storage of the contract
        """
        storage = {}

        storage["total_stake"] = sp.nat(0)
        storage["max_release_period"] = self.max_release_period

        storage["last_stake_id"] = sp.nat(0)
        storage["stakes"] = sp.big_map(tkey=sp.TNat, tvalue=Stake.get_type())
        storage["stakes_owner_lookup"] = sp.big_map(
            tkey=sp.TAddress, tvalue=sp.TSet(sp.TNat)
        )
        storage["disc_factor"] = sp.nat(Constants.PRECISION_FACTOR)
        storage["deposit_token"] = self.deposit_token
        storage["reward_token"] = self.reward_token
        storage["sender"] = Constants.DEFAULT_ADDRESS
        storage["last_rewards"] = sp.nat(0)
        storage["current_rewards"] = sp.nat(0)
        storage["administrators"] = self.administrators

        storage["operators"] = sp.big_map(tkey=OperatorKey.get_type(), tvalue=sp.TUnit)
        return storage

    def __init__(self, deposit_token, reward_token, max_release_period, administrators):
        """Contract initialization with the token contract (YOU), the maximum age of a stake (if a stake has an age greater than
        max_release_period, the age will be considered max_release_period) and the administrator of the contract.

        Args:
            engine_address (sp.address): engine address
            deposit_token (Fa2TokenType): deposit token
            token_id (sp.nat): token id
            reward_token (Fa2TokenType): reward token
        """
        self.deposit_token = deposit_token
        self.reward_token = reward_token
        self.max_release_period = max_release_period
        self.administrators = administrators
        self.init(**self.get_init_storage())

    @sp.private_lambda(with_storage="read-only", with_operations=True, wrap_call=True)
    def fetch_reward_balance(self, unit):
        """Lambda to trigger a own token balance fetch to be set using the callback on the "set_balance" entrypoint.

        Post: get token balance
        Post: call update on engine
        Args:
            unit (sp.unit): nothing
        """
        Utils.execute_get_own_balance(
            self.data.reward_token.address, self.data.reward_token.id, "set_balance"
        )

    @sp.private_lambda(with_storage="read-write", with_operations=False, wrap_call=True)
    def sub_update_factor(self, unit):
        """sub entrypoint which updates the discount factor based on the received reward.

        Pre: storage.total_stake > 0
        Post: storage.last_token_balance = storage.current_token_balance
        Post: storage.disc_fator += ((storage.current_token_balance - storage.last_token_balance)*10**12)/storage.total_stake

        Args:
            unit (sp.unit): nothing
        """
        with sp.if_(self.data.total_stake > 0):
            reward = sp.as_nat(
                self.data.current_rewards - self.data.last_rewards
            )
            self.data.disc_factor += (
                reward * Constants.PRECISION_FACTOR // self.data.total_stake
            )
            self.data.last_rewards = self.data.current_rewards

    @sp.private_lambda(with_storage="read-write", with_operations=True, wrap_call=True)
    def sub_claim(self, stake_id):
        """sub entrypoint which claims the rewards for the sender stored in "sender". This means this can only be called by "internal_" entrypoints where
        the sender is set correctly. This sub-claim also contains the logic of linear release. Based on the stake age a fraction of the reward is
        released to the sender, the rest is redistributed among the other pool participants.
        Args:
            unit (sp.unit): nothing
        """
        sp.set_type(stake_id, sp.TNat)
        stake = sp.local("stake", self.data.stakes[stake_id])
        stake_age = sp.min(
            sp.as_nat(sp.now - stake.value.age_timestamp),
            self.data.max_release_period,
        )

        reward_token_amount = sp.local(
            "reward_token_amount",
            stake.value.stake
            * sp.as_nat(self.data.disc_factor - stake.value.disc_factor)
            // Constants.PRECISION_FACTOR,
        )
        timed_reward_token_amount = sp.local(
            "timed_reward_token_amount",
            reward_token_amount.value * stake_age // self.data.max_release_period,
        )

        Utils.execute_fa2_token_transfer(
            self.data.reward_token.address,
            sp.self_address,
            sp.self_address,
            self.data.reward_token.id,
            sp.as_nat(reward_token_amount.value - timed_reward_token_amount.value),
        )  # this self-transfer is just for indexing purposes and not required for functionality. It can be removed if gas matters.
        Utils.execute_fa2_token_transfer(
            self.data.reward_token.address,
            sp.self_address,
            self.data.sender,
            self.data.reward_token.id,
            timed_reward_token_amount.value,
        )

        self.data.last_rewards = sp.as_nat(
            self.data.last_rewards - reward_token_amount.value
        )
        self.data.stakes[stake_id].disc_factor = self.data.disc_factor


    @sp.entry_point(check_no_incoming_transfer=True)
    def update_max_release_period(self, max_release_period):
        """Update the max release period for a stake. This entrypoint can only be called by an admin.

        Args:
            max_release_period(sp.nat): new max release period to be set.
        """
        self.verify_is_admin()
        sp.set_type(max_release_period, sp.TNat)
        self.data.max_release_period = max_release_period

    @sp.entry_point(check_no_incoming_transfer=True)
    def set_balance(self, balance_of_response):
        """called by the token contract to set the apropriate balance.

        Args:
            balance_of_response (sp.nat): fa2 balance_of response used to set the current_token_balance
        """
        sp.set_type(balance_of_response, BalanceOf.get_response_type())
        sp.verify(sp.sender == self.data.reward_token.address, message=Errors.INVALID_SENDER)
        with sp.match_cons(balance_of_response) as matched_balance_of_response:
            sp.verify(
                matched_balance_of_response.head.request.owner == sp.self_address,
                message=Errors.INVALID_BALANCE_REQUEST,
            )
            self.data.current_rewards = matched_balance_of_response.head.balance

    @sp.entry_point(check_no_incoming_transfer=True)
    def deposit(self, deposit_paramter):
        """ """
        sp.set_type(
            deposit_paramter, sp.TRecord(token_amount=sp.TNat, stake_id=sp.TNat)
        )

        self.data.sender = sp.sender
        self.fetch_reward_balance(sp.unit)

        sp.transfer(
            deposit_paramter, sp.mutez(0), sp.self_entry_point("internal_deposit")
        )

    @sp.entry_point(check_no_incoming_transfer=True)
    def internal_deposit(self, deposit_paramter):
        """ """
        sp.set_type(
            deposit_paramter, sp.TRecord(token_amount=sp.TNat, stake_id=sp.TNat)
        )

        self.verify_internal(sp.unit)
        self.sub_update_factor(sp.unit)

        token_amount = sp.local("token_amount", deposit_paramter.token_amount)
        Utils.execute_fa2_token_transfer(
            self.data.deposit_token.address,
            self.data.sender,
            sp.self_address,
            self.data.deposit_token.id,
            token_amount.value,
        )

        stake_id = sp.local("stake_id", deposit_paramter.stake_id)

        with sp.if_(stake_id.value > 0):
            sp.verify(
                self.data.stakes_owner_lookup[self.data.sender].contains(
                    stake_id.value
                ),
                message=Errors.NOT_OWNER,
            )
        with sp.else_():
            self.data.last_stake_id += 1
            stake_id.value = self.data.last_stake_id

        with sp.if_(self.data.stakes.contains(stake_id.value)):
            stake = sp.local("stake", self.data.stakes[stake_id.value])
            stake_age = sp.min(
                sp.as_nat(sp.now - stake.value.age_timestamp),
                self.data.max_release_period,
            )
            new_stake = sp.local("new_stake", stake.value.stake + token_amount.value)
            sender_disc_factor = stake.value.disc_factor
            new_age_timestamp = sp.local(
                "new_age_timestamp",
                sp.now.add_seconds(
                    -1 * sp.to_int((stake.value.stake * stake_age // new_stake.value))
                ),
            )  # this is negative addition == substraction because no "remove_seconds" exists in smartpy
            current_reward_token_amount = sp.local(
                "current_reward_token_amount",
                stake.value.stake
                * sp.as_nat(self.data.disc_factor - sender_disc_factor)
                // Constants.PRECISION_FACTOR,
            )
            new_sender_disc_factor = sp.local(
                "new_sender_disc_factor",
                sp.as_nat(
                    self.data.disc_factor
                    - current_reward_token_amount.value
                    * Constants.PRECISION_FACTOR
                    // new_stake.value
                ),
            )
            stake.value.stake = new_stake.value
            stake.value.disc_factor = new_sender_disc_factor.value
            stake.value.age_timestamp = new_age_timestamp.value
            self.data.stakes[stake_id.value] = stake.value
        with sp.else_():
            with sp.if_(~self.data.stakes_owner_lookup.contains(self.data.sender)):
                self.data.stakes_owner_lookup[self.data.sender] = sp.set([])
            self.data.stakes_owner_lookup[self.data.sender].add(stake_id.value)
            self.data.stakes[stake_id.value] = sp.record(
                disc_factor=self.data.disc_factor,
                stake=token_amount.value,
                age_timestamp=sp.now,
            )
        self.data.total_stake += token_amount.value

    @sp.entry_point(check_no_incoming_transfer=True)
    def claim(self, claim_paramter):
        """external entrypoint for a user to claim her/his rewards. The actual logic is in internal_claim.
        Post: storage.sender = sp.sender
        Post: fetch_reward_balance()
        Post: calls self.internal_claim
        """
        sp.set_type(
            claim_paramter, sp.TRecord(stake_id=sp.TNat)
        )
        self.data.sender = sp.sender
        self.fetch_reward_balance(sp.unit)
        sp.transfer(claim_paramter, sp.mutez(0), sp.self_entry_point("internal_claim"))

    @sp.entry_point(check_no_incoming_transfer=True)
    def internal_claim(self, claim_paramter):
        """internal entrypoint to claim a senders rewards.
        Pre: verify_internal()
        Post: sub_distribute()
        Post: sub_claim()
        """
        sp.set_type(
            claim_paramter, sp.TRecord(stake_id=sp.TNat)
        )
        self.verify_internal(sp.unit)
        self.sub_update_factor(sp.unit)
        self.sub_claim(claim_paramter.stake_id)


    @sp.entry_point(check_no_incoming_transfer=True)
    def withdraw(self, withdraw_paramter):
        """ """
        sp.set_type(
            withdraw_paramter,
            sp.TRecord(
                stake_id=sp.TNat
            ),
        )

        self.data.sender = sp.sender
        self.fetch_reward_balance(sp.unit)
        sp.transfer(
            withdraw_paramter, sp.mutez(0), sp.self_entry_point("internal_withdraw")
        )

    @sp.entry_point(check_no_incoming_transfer=True)
    def internal_withdraw(self, withdraw_paramter):
        """ """
        sp.set_type(
            withdraw_paramter,
            sp.TRecord(
                stake_id=sp.TNat
            ),
        )

        self.verify_internal(sp.unit)
        self.sub_update_factor(sp.unit)
        self.sub_claim(withdraw_paramter.stake_id)

        stake = sp.local("stake", self.data.stakes[withdraw_paramter.stake_id])

        sp.verify(
            self.data.stakes_owner_lookup[self.data.sender].contains(
                withdraw_paramter.stake_id
            ),
            message=Errors.NOT_OWNER,
        )

        Utils.execute_fa2_token_transfer(
            self.data.deposit_token.address,
            sp.self_address,
            self.data.sender,
            self.data.deposit_token.id,
            stake.value.stake,
        )

        self.data.total_stake = sp.as_nat(
            self.data.total_stake - stake.value.stake
        )

        del self.data.stakes[withdraw_paramter.stake_id]
        self.data.stakes_owner_lookup[self.data.sender].remove(
            withdraw_paramter.stake_id
        )

    @sp.entry_point(check_no_incoming_transfer=True)
    def update_operators(self, update_operators):
        """ """
        sp.set_type(update_operators, UpdateOperator.get_batch_type())
        with sp.for_("update_operator", update_operators) as update_operator:
            with update_operator.match_cases() as argument:
                with argument.match("add_operator") as update:
                    sp.verify(
                        update.owner == sp.sender, message=FA2ErrorMessage.NOT_OWNER
                    )
                    operator_key = OperatorKey.make(
                        update.token_id, update.owner, update.operator
                    )
                    self.data.operators[operator_key] = sp.unit
                with argument.match("remove_operator") as update:
                    sp.verify(
                        update.owner == sp.sender, message=FA2ErrorMessage.NOT_OWNER
                    )
                    operator_key = OperatorKey.make(
                        update.token_id, update.owner, update.operator
                    )
                    del self.data.operators[operator_key]

    @sp.entry_point(check_no_incoming_transfer=True)
    def transfer(self, transfers):
        sp.set_type(transfers, Transfer.get_batch_type())
        with sp.for_("transfer", transfers) as transfer:
            with sp.for_("tx", transfer.txs) as tx:
                sp.verify(self.data.stakes.contains(tx.token_id), message=FA2ErrorMessage.TOKEN_UNDEFINED)
                stake = sp.local("stake", self.data.stakes[tx.token_id])
                operator_key = OperatorKey.make(tx.token_id, transfer.from_, sp.sender)
                sp.verify(
                    (sp.sender == transfer.from_)
                    | self.data.operators.contains(operator_key),
                    message=FA2ErrorMessage.NOT_OPERATOR,
                )

                with sp.if_((tx.amount == 1) & self.data.stakes_owner_lookup[transfer.from_].contains(tx.token_id)):
                    with sp.if_(~self.data.stakes_owner_lookup.contains(tx.to_)):
                        self.data.stakes_owner_lookup[tx.to_] = sp.set([])
                    self.data.stakes_owner_lookup[transfer.from_].remove(tx.token_id)
                    self.data.stakes_owner_lookup[tx.to_].add(tx.token_id)

    @sp.entry_point(check_no_incoming_transfer=True)
    def balance_of(self, balance_of_request):
        """This entrypoint as per FA2 standard, takes balance_of requests and reponds on the provided callback contract.

        Args:
            balance_of_request (BalanceOf): the request
        """
        sp.set_type(balance_of_request, BalanceOf.get_type())

        responses = sp.local(
            "responses", sp.set_type_expr(sp.list([]), BalanceOf.get_response_type())
        )
        with sp.for_("request", balance_of_request.requests) as request:
            sp.verify(
                self.data.stakes.contains(request.token_id),
                message=FA2ErrorMessage.TOKEN_UNDEFINED,
            )
            stake = sp.local("stake", self.data.stakes[request.token_id])
            with sp.if_(self.data.stakes_owner_lookup.contains(request.owner)):
                with sp.if_(
                    self.data.stakes_owner_lookup[request.owner].contains(
                        request.token_id
                    )
                ):
                    responses.value.push(sp.record(request=request, balance=1))
            with sp.else_():
                responses.value.push(sp.record(request=request, balance=0))

        sp.transfer(responses.value, sp.mutez(0), balance_of_request.callback)


    @sp.onchain_view()
    def view_balance(self, parameter):
        sp.set_type(parameter, sp.TRecord(address=sp.TAddress, token_id=sp.TNat))
        sp.verify(
            self.data.stakes.contains(parameter.token_id),
            message=FA2ErrorMessage.TOKEN_UNDEFINED,
        )

        with sp.if_(
            (
                self.data.stakes_owner_lookup.contains(parameter.address)
                & self.data.stakes_owner_lookup[parameter.address].contains(
                    parameter.token_id
                )
            )
        ):
            sp.result(1)
        with sp.else_():
            sp.result(0)

    @sp.onchain_view()
    def view_is_operator(self, parameter):
        sp.set_type(parameter, OperatorKey.get_type())
        operator_key = OperatorKey.make(
            parameter.token_id, parameter.owner, parameter.operator
        )
        sp.result(self.data.operators.contains(operator_key))

    @sp.onchain_view()
    def view_owner_stakes(self, owner):
        sp.set_type(owner, sp.TAddress)
        with sp.if_(~self.data.stakes_owner_lookup.contains(owner)):
            sp.result(sp.set([]))
        with sp.else_():
            sp.result(self.data.stakes_owner_lookup[owner])

    @sp.onchain_view()
    def view_stake(self, stake_id):
        sp.set_type(stake_id, sp.TNat)
        with sp.if_(~self.data.stakes.contains(stake_id)):
            sp.result(
                Stake.make(
                    disc_factor=sp.nat(0),
                    stake=sp.nat(0),
                    age_timestamp=sp.timestamp(0),
                )
            )
        with sp.else_():
            sp.result(self.data.stakes[stake_id])

    @sp.onchain_view()
    def view_max_release_period(self):
        sp.result(self.data.max_release_period)

    @sp.onchain_view()
    def view_administrator_state(self, address):
        with sp.if_(self.data.administrators.contains(address)):
            sp.result(self.data.administrators[address])
        with sp.else_():
            sp.result(-1)

    @sp.onchain_view()
    def view_last_stake_id(self):
        sp.result(self.data.last_stake_id)

    @sp.onchain_view()
    def view_disc_factor(self):
        sp.result(self.data.disc_factor)

    @sp.onchain_view()
    def view_total_stake(self):
        sp.result(self.data.total_stake)
