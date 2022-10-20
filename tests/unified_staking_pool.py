import smartpy as sp

import utils.constants as Constants
import utils.fa2 as fa2
import utils.fa1 as fa1
from utils.administrable_mixin import AdministratorState
from contracts.unified_staking_pool import UnifiedStakingPool, TokenType

class DummyFA2(fa2.AdministrableFA2):
    @sp.entry_point
    def mint(self, recipient_token_amount):
        sp.set_type(recipient_token_amount, fa2.RecipientTokenAmount.get_type())
        with sp.if_(
            self.data.ledger.contains(
                fa2.LedgerKey.make(
                    recipient_token_amount.token_id, recipient_token_amount.owner
                )
            )
        ):
            self.data.ledger[
                fa2.LedgerKey.make(
                    recipient_token_amount.token_id, recipient_token_amount.owner
                )
            ] += recipient_token_amount.token_amount
        with sp.else_():
            self.data.ledger[
                fa2.LedgerKey.make(
                    recipient_token_amount.token_id, recipient_token_amount.owner
                )
            ] = recipient_token_amount.token_amount
    
    @sp.entry_point
    def burn(self, recipient_token_amount):
        sp.set_type(recipient_token_amount, fa2.RecipientTokenAmount.get_type())
        self.data.ledger[
            fa2.LedgerKey.make(
                recipient_token_amount.token_id, recipient_token_amount.owner
            )
        ] = sp.as_nat(
            self.data.ledger[
                fa2.LedgerKey.make(
                    recipient_token_amount.token_id, recipient_token_amount.owner
                )
            ]
            - recipient_token_amount.token_amount
        )

@sp.add_test(name="Normal Staking Pool")
def test_normal_staking_pool():
    scenario = sp.test_scenario()
    scenario.h1("Staking Pool Unit Test")
    scenario.table_of_contents()

    scenario.h2("Bootstrapping")
    token_id = sp.nat(0)

    administrator = sp.test_account("Administrator")
    alice = sp.test_account("Alice")
    bob = sp.test_account("Robert")
    charlie = sp.test_account("Charlie")
    dan = sp.test_account("Dan")

    reward_token = DummyFA2({fa2.LedgerKey.make(0, administrator.address): sp.unit})
    staking_token = DummyFA2({fa2.LedgerKey.make(0, administrator.address): sp.unit})

    scenario += reward_token
    scenario += staking_token

    scenario += reward_token.set_token_metadata(
        sp.record(token_id=token_id, token_info=sp.map())
    ).run(sender=administrator)

    scenario += staking_token.set_token_metadata(
        sp.record(token_id=token_id, token_info=sp.map())
    ).run(sender=administrator)

    scenario.h1("Long Staking with release of 0")
    staking_pool = UnifiedStakingPool(sp.record(token_type=Constants.TOKEN_TYPE_FA2, token_id=token_id, token_address=staking_token.address), True, sp.record(token_type=Constants.TOKEN_TYPE_FA2, token_id=0, token_address=reward_token.address), 180 * 24 * 60 * 60, {administrator.address: 1})

    scenario += staking_pool

    scenario += staking_token.mint(
        owner=alice.address,
        token_id=token_id,
        token_amount=10 * Constants.PRECISION_FACTOR,
    )
    scenario += staking_token.mint(
        owner=bob.address,
        token_id=token_id,
        token_amount=10 * Constants.PRECISION_FACTOR,
    )
    scenario += staking_token.mint(
        owner=charlie.address,
        token_id=token_id,
        token_amount=10 * Constants.PRECISION_FACTOR,
    )
    scenario += staking_token.mint(
        owner=dan.address,
        token_id=token_id,
        token_amount=10 * Constants.PRECISION_FACTOR,
    )
    scenario += staking_token.update_operators(
        [
            sp.variant(
                "add_operator",
                sp.record(
                    owner=alice.address,
                    operator=staking_pool.address,
                    token_id=token_id,
                ),
            )
        ]
    ).run(sender=alice.address)
    scenario += staking_token.update_operators(
        [
            sp.variant(
                "add_operator",
                sp.record(
                    owner=dan.address, operator=staking_pool.address, token_id=token_id
                ),
            )
        ]
    ).run(sender=dan.address)
    scenario += staking_token.update_operators(
        [
            sp.variant(
                "add_operator",
                sp.record(
                    owner=charlie.address,
                    operator=staking_pool.address,
                    token_id=token_id,
                ),
            )
        ]
    ).run(sender=charlie.address)
    scenario += staking_token.update_operators(
        [
            sp.variant(
                "add_operator",
                sp.record(
                    owner=bob.address, operator=staking_pool.address, token_id=token_id
                ),
            )
        ]
    ).run(sender=bob.address)
    alice_ledger_key = fa2.LedgerKey.make(0, alice.address)
    bob_ledger_key = fa2.LedgerKey.make(0, bob.address)
    charlie_ledger_key = fa2.LedgerKey.make(0, charlie.address)
    dan_ledger_key = fa2.LedgerKey.make(0, dan.address)

    scenario.h2("Start staking")
    now = sp.timestamp(0)
    scenario += staking_pool.deposit(sp.record(token_amount=1 * Constants.PRECISION_FACTOR, stake_id=0)).run(
        sender=alice, now=now
    )

    scenario.h2("Claim after a reward has been paid ")
    now = now.add_seconds(sp.to_int(staking_pool.data.max_release_period))
    reward_amount = 1 * Constants.PRECISION_FACTOR
    alice_reward = reward_amount
    bob_reward = 0
    scenario.p("pay reward")
    scenario += reward_token.mint(
        owner=staking_pool.address, token_id=token_id, token_amount=reward_amount
    )
    scenario.p("alice claims as only user -> gets full reward")
    scenario += staking_pool.claim(sp.record(stake_id=1)).run(sender=alice, now=now)
    scenario.verify_equal(reward_token.data.ledger[alice_ledger_key], alice_reward)
    scenario.p("Multiclaim yields nothing")
    scenario += staking_pool.claim(sp.record(stake_id=1)).run(sender=alice, now=now)
    scenario.verify_equal(reward_token.data.ledger[alice_ledger_key], alice_reward)

    scenario.h2("Bob joins before a reward payout")
    scenario += staking_pool.deposit(sp.record(token_amount=1 * Constants.PRECISION_FACTOR, stake_id=0)).run(
        sender=bob, now=now
    )
    now = now.add_seconds(sp.to_int(staking_pool.data.max_release_period))
    scenario.p("pay reward")
    alice_reward += reward_amount // 2
    bob_reward += reward_amount // 2
    scenario += reward_token.mint(
        owner=staking_pool.address, token_id=token_id, token_amount=reward_amount
    )
    scenario.p("both claim, both get same reward")
    scenario += staking_pool.claim(sp.record(stake_id=1)).run(sender=alice, now=now)
    scenario += staking_pool.claim(sp.record(stake_id=2)).run(sender=bob, now=now)
    scenario.verify_equal(reward_token.data.ledger[alice_ledger_key], alice_reward)
    scenario.verify_equal(reward_token.data.ledger[bob_ledger_key], bob_reward)

    scenario.h2("Alice Increases Stake")
    scenario += staking_pool.deposit(sp.record(token_amount=1 * Constants.PRECISION_FACTOR, stake_id=1)).run(
        sender=alice, now=now
    )
    now = now.add_seconds(sp.to_int(staking_pool.data.max_release_period))
    scenario.p("pay reward")
    alice_reward += reward_amount * 2 // 3
    bob_reward += reward_amount // 3
    scenario += reward_token.mint(
        owner=staking_pool.address, token_id=token_id, token_amount=reward_amount
    )
    scenario.p("both claim, alice gets 2/3 and bob 1/3")
    scenario += staking_pool.claim(sp.record(stake_id=1)).run(sender=alice, now=now)
    scenario += staking_pool.claim(sp.record(stake_id=2)).run(sender=bob, now=now)
    scenario.verify_equal(reward_token.data.ledger[alice_ledger_key], alice_reward)
    scenario.verify_equal(reward_token.data.ledger[bob_ledger_key], bob_reward)

    scenario.h2("Fixed rewards randomly flies in")
    scenario += reward_token.mint(
        owner=staking_pool.address, token_id=token_id, token_amount=reward_amount
    ).run(now=now)
    alice_reward += reward_amount * 2 // 3
    bob_reward += reward_amount // 3
    dan_reward = 0

    scenario.p("Dan joins late (not ellegible for fixed reward")
    now = now.add_seconds(sp.to_int(staking_pool.data.max_release_period))
    scenario += staking_pool.deposit(sp.record(token_amount=1 * Constants.PRECISION_FACTOR, stake_id=0)).run(
        sender=dan, now=now
    )

    scenario += staking_pool.claim(sp.record(stake_id=1)).run(sender=alice, now=now)
    scenario += staking_pool.claim(sp.record(stake_id=2)).run(sender=bob, now=now)
    scenario += staking_pool.claim(sp.record(stake_id=3)).run(sender=dan, now=now)

    scenario.verify_equal(reward_token.data.ledger[alice_ledger_key], alice_reward)
    scenario.verify_equal(reward_token.data.ledger[bob_ledger_key], bob_reward)

    scenario.h2("Dan leaves after reward")
    scenario += reward_token.mint(
        owner=staking_pool.address, token_id=token_id, token_amount=reward_amount
    ).run(now=now)

    alice_reward += reward_amount * 2 // 4
    bob_reward += reward_amount // 4
    dan_reward += reward_amount // 4

    now = now.add_seconds(sp.to_int(staking_pool.data.max_release_period))
    scenario += staking_pool.withdraw(sp.record(stake_id=3)).run(sender=dan, now=now)

    scenario.p("Dan Rejoins (after a new reward)")
    scenario += reward_token.mint(
        owner=staking_pool.address, token_id=token_id, token_amount=reward_amount
    ).run(now=now)
    now = now.add_seconds(sp.to_int(staking_pool.data.max_release_period))

    alice_reward += reward_amount * 2 // 3
    bob_reward += reward_amount // 3

    scenario += staking_pool.deposit(sp.record(token_amount=1 * Constants.PRECISION_FACTOR, stake_id=0)).run(
        sender=dan, now=now
    )
    scenario += staking_pool.claim(sp.record(stake_id=1)).run(sender=alice, now=now)
    scenario += staking_pool.claim(sp.record(stake_id=2)).run(sender=bob, now=now)
    scenario += staking_pool.claim(sp.record(stake_id=4)).run(sender=dan, now=now)

    scenario.verify_equal(reward_token.data.ledger[alice_ledger_key], alice_reward)
    scenario.verify_equal(reward_token.data.ledger[bob_ledger_key], bob_reward)
    scenario.verify_equal(reward_token.data.ledger[dan_ledger_key], dan_reward)


@sp.add_test(name="Vesting Staking Pool")
def test_vesting_incentive():
    scenario = sp.test_scenario()
    scenario.h1("Staking Pool Unit Test")
    scenario.table_of_contents()

    scenario.h2("Bootstrapping")
    token_id = sp.nat(0)

    administrator = sp.test_account("Administrator")
    alice = sp.test_account("Alice")
    bob = sp.test_account("Robert")
    dan = sp.test_account("Dan")

    scenario.show([administrator, alice, bob, dan])

    reward_token = DummyFA2({fa2.LedgerKey.make(0, administrator.address): sp.unit})
    staking_token = DummyFA2({fa2.LedgerKey.make(0, administrator.address): sp.unit})

    scenario += reward_token
    scenario += staking_token

    scenario += reward_token.set_token_metadata(
        sp.record(token_id=token_id, token_info=sp.map())
    ).run(sender=administrator)

    scenario += staking_token.set_token_metadata(
        sp.record(token_id=token_id, token_info=sp.map())
    ).run(sender=administrator)

    scenario.h1("Long Staking with release of 0")
    staking_pool = staking_pool = UnifiedStakingPool(sp.record(token_type=Constants.TOKEN_TYPE_FA2, token_id=token_id, token_address=staking_token.address), True, sp.record(token_type=Constants.TOKEN_TYPE_FA2, token_id=0, token_address=reward_token.address), 180 * 24 * 60 * 60, {administrator.address: 1})

    scenario += staking_pool

    scenario += staking_token.mint(
        owner=alice.address,
        token_id=token_id,
        token_amount=10 * Constants.PRECISION_FACTOR,
    )
    scenario += staking_token.mint(
        owner=bob.address,
        token_id=token_id,
        token_amount=10 * Constants.PRECISION_FACTOR,
    )
    scenario += staking_token.mint(
        owner=dan.address,
        token_id=token_id,
        token_amount=10 * Constants.PRECISION_FACTOR,
    )
    scenario += staking_token.update_operators(
        [
            sp.variant(
                "add_operator",
                sp.record(
                    owner=alice.address,
                    operator=staking_pool.address,
                    token_id=token_id,
                ),
            )
        ]
    ).run(sender=alice.address)
    scenario += staking_token.update_operators(
        [
            sp.variant(
                "add_operator",
                sp.record(
                    owner=dan.address, operator=staking_pool.address, token_id=token_id
                ),
            )
        ]
    ).run(sender=dan.address)
    scenario += staking_token.update_operators(
        [
            sp.variant(
                "add_operator",
                sp.record(
                    owner=bob.address, operator=staking_pool.address, token_id=token_id
                ),
            )
        ]
    ).run(sender=bob.address)
    alice_ledger_key = fa2.LedgerKey.make(0, alice.address)
    bob_ledger_key = fa2.LedgerKey.make(0, bob.address)
    dan_ledger_key = fa2.LedgerKey.make(0, dan.address)

    scenario.h2("Start staking")
    now = sp.timestamp(0)
    scenario += staking_pool.deposit(sp.record(token_amount=1 * Constants.PRECISION_FACTOR, stake_id=0)).run(
        sender=alice, now=now
    )

    scenario.h2("Claim after a reward has been paid ")
    now = now.add_seconds(sp.to_int(staking_pool.data.max_release_period // 2))
    reward_amount = 1 * Constants.PRECISION_FACTOR
    alice_reward = reward_amount // 2
    bob_reward = 0
    scenario.p("pay reward")
    scenario += reward_token.mint(
        owner=staking_pool.address, token_id=token_id, token_amount=reward_amount
    )
    scenario.p("alice claims as only user -> gets full reward")
    scenario += staking_pool.claim(sp.record(stake_id=1)).run(sender=alice, now=now)
    scenario.verify_equal(reward_token.data.ledger[alice_ledger_key], alice_reward)
    scenario.p("Multiclaim yields the re-distributed rewards")
    alice_reward += (reward_amount - alice_reward) // 2
    scenario += staking_pool.claim(sp.record(stake_id=1)).run(sender=alice, now=now)
    scenario.verify_equal(reward_token.data.ledger[alice_ledger_key], alice_reward)

    scenario.h2("Bob joins before a reward payout")
    scenario += staking_pool.deposit(sp.record(token_amount=1 * Constants.PRECISION_FACTOR, stake_id=0)).run(
        sender=bob, now=now
    )
    now = now.add_seconds(sp.to_int(staking_pool.data.max_release_period // 2))
    scenario.p("pay reward")
    alice_reward += reward_amount // 2 + reward_amount // 4
    bob_reward += reward_amount // 4
    scenario += reward_token.mint(
        owner=staking_pool.address, token_id=token_id, token_amount=reward_amount
    )
    scenario.p("both claim, both get same reward")
    scenario += staking_pool.claim(sp.record(stake_id=1)).run(sender=alice, now=now)
    scenario += staking_pool.claim(sp.record(stake_id=2)).run(sender=bob, now=now)
    scenario.verify_equal(reward_token.data.ledger[alice_ledger_key], alice_reward)
    scenario.verify_equal(reward_token.data.ledger[bob_ledger_key], bob_reward)

    scenario.h2("Alice Increases Stake")
    scenario += staking_pool.deposit(sp.record(token_amount=1 * Constants.PRECISION_FACTOR, stake_id=1)).run(
        sender=alice, now=now
    )
    now = now.add_seconds(sp.to_int(staking_pool.data.max_release_period // 2))
    scenario.p("pay reward")
    alice_reward += (
        reward_amount * 2 // 3 + reward_amount // 4 // 2
    )  # time weighted own + bob's redistribution
    bob_reward += reward_amount // 3 + reward_amount // 4 // 2
    scenario += reward_token.mint(
        owner=staking_pool.address, token_id=token_id, token_amount=reward_amount
    )
    scenario.p("both claim, alice gets 2/3 and bob 1/3")
    scenario += staking_pool.claim(sp.record(stake_id=1)).run(sender=alice, now=now)
    scenario += staking_pool.claim(sp.record(stake_id=2)).run(sender=bob, now=now)
    scenario.verify_equal(reward_token.data.ledger[alice_ledger_key], alice_reward)
    scenario.verify_equal(reward_token.data.ledger[bob_ledger_key], bob_reward)

    scenario.h2("Fixed rewards randomly flies in")
    scenario += reward_token.mint(
        owner=staking_pool.address, token_id=token_id, token_amount=reward_amount
    ).run(now=now)
    alice_reward += reward_amount * 2 // 3
    bob_reward += reward_amount // 3
    dan_reward = 0

    scenario.p("Dan joins late (not ellegible for fixed reward")
    now = now.add_seconds(sp.to_int(staking_pool.data.max_release_period // 2))
    scenario += staking_pool.deposit(sp.record(token_amount=1 * Constants.PRECISION_FACTOR, stake_id=0)).run(
        sender=dan, now=now
    )

    scenario += staking_pool.claim(sp.record(stake_id=1)).run(sender=alice, now=now)
    scenario += staking_pool.claim(sp.record(stake_id=2)).run(sender=bob, now=now)
    scenario += staking_pool.claim(sp.record(stake_id=3)).run(sender=dan, now=now)

    scenario.verify_equal(reward_token.data.ledger[alice_ledger_key], alice_reward)
    scenario.verify_equal(reward_token.data.ledger[bob_ledger_key], bob_reward)

    scenario.h2("Dan leaves after reward")
    scenario += reward_token.mint(
        owner=staking_pool.address, token_id=token_id, token_amount=reward_amount
    ).run(now=now)

    alice_reward += reward_amount * 2 // 4
    bob_reward += reward_amount // 4
    dan_reward += reward_amount // 4 // 2

    now = now.add_seconds(sp.to_int(staking_pool.data.max_release_period // 2))
    scenario += staking_pool.withdraw(sp.record(stake_id=3)).run(sender=dan, now=now)

    scenario.p("Dan Rejoins (after a new reward)")
    scenario += reward_token.mint(
        owner=staking_pool.address, token_id=token_id, token_amount=reward_amount
    ).run(now=now)
    now = now.add_seconds(sp.to_int(staking_pool.data.max_release_period // 2))

    alice_reward += reward_amount * 2 // 3 + reward_amount * 2 // 4 // 2 // 3 + 1
    bob_reward += (
        reward_amount // 3 + reward_amount // 4 // 2 // 3 + 1
    )  # the +1 is because we have double truncated division

    scenario += staking_pool.deposit(sp.record(token_amount=1 * Constants.PRECISION_FACTOR, stake_id=0)).run(
        sender=dan, now=now
    )
    scenario += staking_pool.claim(sp.record(stake_id=1)).run(sender=alice, now=now)
    scenario += staking_pool.claim(sp.record(stake_id=2)).run(sender=bob, now=now)
    scenario += staking_pool.claim(sp.record(stake_id=4)).run(sender=dan, now=now)

    scenario.verify_equal(reward_token.data.ledger[alice_ledger_key], alice_reward)
    scenario.verify_equal(reward_token.data.ledger[bob_ledger_key], bob_reward)
    scenario.verify_equal(reward_token.data.ledger[dan_ledger_key], dan_reward)
    now = now.add_seconds(sp.to_int(staking_pool.data.max_release_period // 2))
    scenario += staking_pool.claim(sp.record(stake_id=1)).run(sender=alice, now=now)
    scenario += staking_pool.claim(sp.record(stake_id=2)).run(sender=bob, now=now)

    # Admin tests
    scenario += staking_pool.propose_administrator(alice.address).run(
        sender=alice, now=now, valid=False
    )
    scenario += staking_pool.propose_administrator(alice.address).run(
        sender=administrator, now=now, valid=True
    )
    scenario.verify(staking_pool.data.administrators.contains(alice.address) == True)
    scenario.verify_equal(
        staking_pool.data.administrators[alice.address], AdministratorState.PROPOSED
    )

    scenario += staking_pool.set_administrator(sp.unit).run(
        sender=bob, now=now, valid=False
    )
    scenario += staking_pool.set_administrator(sp.unit).run(
        sender=alice, now=now, valid=True
    )
    scenario.verify(staking_pool.data.administrators.contains(alice.address) == True)
    scenario.verify_equal(
        staking_pool.data.administrators[alice.address], AdministratorState.SET
    )

    scenario += staking_pool.remove_administrator(alice.address).run(
        sender=bob, now=now, valid=False
    )
    scenario += staking_pool.remove_administrator(alice.address).run(
        sender=administrator, now=now, valid=True
    )
    scenario.verify(staking_pool.data.administrators.contains(alice.address) == False)

    scenario += staking_pool.update_max_release_period(360 * 24 * 60 * 60).run(
        sender=alice, now=now, valid=False
    )
    scenario += staking_pool.update_max_release_period(360 * 24 * 60 * 60).run(
        sender=administrator, now=now, valid=True
    )
    scenario.verify(staking_pool.data.max_release_period == 360 * 24 * 60 * 60)

@sp.add_test(name="Vesting Staking Pool multistakes solo")
def test_multi_stakes_solo():
    scenario = sp.test_scenario()
    scenario.h1("Unified Staking Pool Test")
    scenario.table_of_contents()

    scenario.h2("Bootstrapping")

    administrator = sp.test_account("Administrator")
    alice = sp.test_account("Alice")
    bob = sp.test_account("Robert")
    dan = sp.test_account("Dan")

    scenario.show([administrator, alice, bob, dan])

    token_id = sp.nat(0)
    staking_token = DummyFA2({fa2.LedgerKey.make(token_id, administrator.address): sp.unit})
    reward_token = DummyFA2({fa2.LedgerKey.make(token_id, administrator.address): sp.unit})
    scenario += staking_token
    scenario += reward_token
    scenario += reward_token.set_token_metadata(
        token_id=token_id, token_info=sp.map()
    ).run(sender=administrator)

    scenario += staking_token.set_token_metadata(
        token_id=token_id, token_info=sp.map()
    ).run(sender=administrator)

    staking_token_key = fa2.LedgerKey.make(0, staking_token.address)
                    
    unified_staking_pool = UnifiedStakingPool(
        sp.record(token_type=Constants.TOKEN_TYPE_FA2, token_id=token_id, token_address=staking_token.address), True, sp.record(token_type=Constants.TOKEN_TYPE_FA2, token_id=token_id, token_address=reward_token.address), 100, {administrator.address: 1}
    )
    scenario += unified_staking_pool

    initial_balance = 1000 * Constants.PRECISION_FACTOR

    scenario += staking_token.mint(
        owner=alice.address, token_id=token_id, token_amount=initial_balance
    )
    scenario += staking_token.mint(
        owner=bob.address, token_id=token_id, token_amount=initial_balance
    )
    scenario += staking_token.mint(
        owner=dan.address, token_id=token_id, token_amount=initial_balance
    )
    scenario += staking_token.update_operators(
        [
            sp.variant(
                "add_operator",
                sp.record(
                    owner=alice.address,
                    operator=unified_staking_pool.address,
                    token_id=token_id,
                ),
            )
        ]
    ).run(sender=alice.address)
    scenario += staking_token.update_operators(
        [
            sp.variant(
                "add_operator",
                sp.record(
                    owner=dan.address,
                    operator=unified_staking_pool.address,
                    token_id=token_id,
                ),
            )
        ]
    ).run(sender=dan.address)
    scenario += staking_token.update_operators(
        [
            sp.variant(
                "add_operator",
                sp.record(
                    owner=bob.address,
                    operator=unified_staking_pool.address,
                    token_id=token_id,
                ),
            )
        ]
    ).run(sender=bob.address)

    alice_ledger_key = fa2.LedgerKey.make(0, alice.address)
    bob_ledger_key = fa2.LedgerKey.make(0, bob.address)
    dan_ledger_key = fa2.LedgerKey.make(0, dan.address)
    unified_staking_pool_key = fa2.LedgerKey.make(0, unified_staking_pool.address)

    scenario.h2("Single User Flows")
    now = sp.timestamp(0)
    scenario.p("Alice stakes 1 token")
    alices_stake = 1 * Constants.PRECISION_FACTOR
    alices_balance = initial_balance
    alices_reward = 0

    scenario += unified_staking_pool.deposit(
        sp.record(token_amount=alices_stake, stake_id=0)
    ).run(sender=alice.address, now=now)
    scenario.p("Alice withdraws what she put in")
    scenario += unified_staking_pool.withdraw(
        sp.record(stake_id=1)
    ).run(sender=alice.address, now=now)
    scenario.verify_equal(staking_token.data.ledger[alice_ledger_key], alices_balance)

    scenario.p("Alice stakes 1 token")

    reward_payout = 1 * Constants.PRECISION_FACTOR
    total_reward = reward_payout
    scenario += unified_staking_pool.deposit(
        sp.record(token_amount=alices_stake, stake_id=0)
    ).run(sender=alice.address, now=now)
    scenario += reward_token.mint(
        owner=unified_staking_pool.address,
        token_id=token_id,
        token_amount=reward_payout,
    )

    scenario.p("Alice withdraws what she put in after reward")
    scenario += unified_staking_pool.withdraw(
        sp.record(stake_id=2)
    ).run(sender=alice.address, now=now)
    scenario.verify_equal(staking_token.data.ledger[alice_ledger_key], alices_balance)
    scenario.verify_equal(
        reward_token.data.ledger[unified_staking_pool_key], reward_payout
    )

    scenario.p("Alice stakes 1 token")
    scenario += unified_staking_pool.deposit(
        sp.record(token_amount=alices_stake, stake_id=0)
    ).run(sender=alice.address, now=now)
    scenario += reward_token.mint(
        owner=unified_staking_pool.address,
        token_id=token_id,
        token_amount=reward_payout,
    )

    scenario.p("Alice withdraws what she put in after reward after 1/10 of the time")
    now = now.add_seconds(10)
    total_reward += reward_payout
    alices_reward += total_reward // 10
  
    scenario += unified_staking_pool.withdraw(
        sp.record(stake_id=3)
    ).run(sender=alice.address, now=now)
    scenario.verify_equal(staking_token.data.ledger[alice_ledger_key], alices_balance)
    scenario.verify_equal(reward_token.data.ledger[alice_ledger_key], alices_reward)
    scenario.verify_equal(
        reward_token.data.ledger[unified_staking_pool_key], total_reward * 9 // 10
    )

    scenario.p("Alice stakes 1 token")
    scenario += unified_staking_pool.deposit(
        sp.record(token_amount=alices_stake, stake_id=0)
    ).run(sender=alice.address, now=now)
    scenario += reward_token.mint(
        owner=unified_staking_pool.address,
        token_id=token_id,
        token_amount=reward_payout,
    )

    scenario.p(
        "Alice withdraws what she put in after reward after 10/10 of the time, get full rewards"
    )
    now = now.add_seconds(100)
    total_reward = total_reward * 9 // 10 + reward_payout
    alices_reward += total_reward
   
    scenario += unified_staking_pool.withdraw(
        sp.record(stake_id=4)
    ).run(sender=alice.address, now=now)

    scenario.verify_equal(reward_token.data.ledger[alice_ledger_key], alices_reward)

    scenario.p("Alice stakes 1 token")
    scenario += unified_staking_pool.deposit(
        sp.record(token_amount=alices_stake, stake_id=0)
    ).run(sender=alice.address, now=now)
    scenario += reward_token.mint(
        owner=unified_staking_pool.address,
        token_id=token_id,
        token_amount=reward_payout,
    )

    scenario.p("Alice withdraws half-time half of her stake")
    now = now.add_seconds(50)
    total_reward = reward_payout

    alices_reward += total_reward // 2
    remaining_reward = total_reward // 2

    scenario += unified_staking_pool.withdraw(
        sp.record(stake_id=5)
    ).run(sender=alice.address, now=now)

    scenario.verify_equal(reward_token.data.ledger[alice_ledger_key], alices_reward)
    scenario.verify_equal(staking_token.data.ledger[alice_ledger_key], alices_balance)
    scenario.verify_equal(
        reward_token.data.ledger[unified_staking_pool_key], remaining_reward
    )

    scenario += reward_token.burn(
        owner=unified_staking_pool.address,
        token_id=token_id,
        token_amount=reward_token.data.ledger[unified_staking_pool_key],
    )
    scenario.p("Alice stakes 1 token")
    scenario += unified_staking_pool.deposit(
        sp.record(token_amount=alices_stake, stake_id=0)
    ).run(sender=alice.address, now=now)
    scenario += reward_token.mint(
        owner=unified_staking_pool.address,
        token_id=token_id,
        token_amount=reward_payout,
    )

    scenario.p(
        "Alice adds 1 token to stake after half time, after reward her stake is currently 2:1"
    )
    now = now.add_seconds(50)
    scenario += unified_staking_pool.deposit(
        sp.record(token_amount=alices_stake, stake_id=6)
    ).run(sender=alice.address, now=now)
    scenario += reward_token.mint(
        owner=unified_staking_pool.address,
        token_id=token_id,
        token_amount=reward_payout,
    )
    scenario += reward_token.burn(
        owner=alice.address,
        token_id=token_id,
        token_amount=reward_token.data.ledger[alice_ledger_key],
    )

    scenario.p("Alice withdraws full after half time of the second deposit")
    now = now.add_seconds(50)
    total_reward = 2 * reward_payout
    # when alice deposits the second time, her stake has grown to 2x, this means we have 1x age of 0 and 2x age of 50 == an age of 33 days. Add the 50 days to that we end up at the 83 days used below.
    alices_reward = total_reward * 3 // 4
    remaining_reward = total_reward - alices_reward
    scenario += unified_staking_pool.withdraw(
        sp.record(stake_id=6)
    ).run(sender=alice.address, now=now)
    
    scenario.verify_equal(reward_token.data.ledger[alice_ledger_key], alices_reward)
    scenario.verify_equal(
        reward_token.data.ledger[unified_staking_pool_key], remaining_reward
    )

@sp.add_test(name="Vesting Staking Pool multistakes multi")
def test_multi_stakes():
    scenario = sp.test_scenario()
    scenario.h1("Staking Pool Unit Test")
    scenario.table_of_contents()

    scenario.h2("Bootstrapping")
    token_id = sp.nat(0)

    administrator = sp.test_account("Administrator")
    alice = sp.test_account("Alice")
    bob = sp.test_account("Robert")
    dan = sp.test_account("Dan")

    scenario.show([administrator, alice, bob, dan])

    reward_token = DummyFA2({fa2.LedgerKey.make(0, administrator.address): sp.unit})
    staking_token = DummyFA2({fa2.LedgerKey.make(0, administrator.address): sp.unit})

    scenario += reward_token
    scenario += staking_token

    scenario += reward_token.set_token_metadata(
        sp.record(token_id=token_id, token_info=sp.map())
    ).run(sender=administrator)

    scenario += staking_token.set_token_metadata(
        sp.record(token_id=token_id, token_info=sp.map())
    ).run(sender=administrator)

    scenario.h1("Long Staking with release of 0")
    staking_pool = staking_pool = UnifiedStakingPool(sp.record(token_type=Constants.TOKEN_TYPE_FA2, token_id=token_id, token_address=staking_token.address), True, sp.record(token_type=Constants.TOKEN_TYPE_FA2, token_id=0, token_address=reward_token.address), 180 * 24 * 60 * 60, {administrator.address: 1})

    scenario += staking_pool

    scenario += staking_token.mint(
        owner=alice.address,
        token_id=token_id,
        token_amount=10 * Constants.PRECISION_FACTOR,
    )
    scenario += staking_token.mint(
        owner=bob.address,
        token_id=token_id,
        token_amount=10 * Constants.PRECISION_FACTOR,
    )
    scenario += staking_token.mint(
        owner=dan.address,
        token_id=token_id,
        token_amount=10 * Constants.PRECISION_FACTOR,
    )
    scenario += staking_token.update_operators(
        [
            sp.variant(
                "add_operator",
                sp.record(
                    owner=alice.address,
                    operator=staking_pool.address,
                    token_id=token_id,
                ),
            )
        ]
    ).run(sender=alice.address)
    scenario += staking_token.update_operators(
        [
            sp.variant(
                "add_operator",
                sp.record(
                    owner=dan.address, operator=staking_pool.address, token_id=token_id
                ),
            )
        ]
    ).run(sender=dan.address)
    scenario += staking_token.update_operators(
        [
            sp.variant(
                "add_operator",
                sp.record(
                    owner=bob.address, operator=staking_pool.address, token_id=token_id
                ),
            )
        ]
    ).run(sender=bob.address)
    alice_ledger_key = fa2.LedgerKey.make(0, alice.address)
    bob_ledger_key = fa2.LedgerKey.make(0, bob.address)
    dan_ledger_key = fa2.LedgerKey.make(0, dan.address)
    reward_amount = 1 * Constants.PRECISION_FACTOR

    scenario.h2("Start staking")
    now = sp.timestamp(0)
    scenario += staking_pool.deposit(sp.record(token_amount=1 * Constants.PRECISION_FACTOR, stake_id=0)).run(
        sender=alice, now=now
    )
    scenario.p("Alice stake and pay reward")
    scenario += reward_token.mint(
        owner=staking_pool.address, token_id=token_id, token_amount=reward_amount
    )

    scenario.p("Bob stake and pay reward")
    scenario += staking_pool.deposit(sp.record(token_amount=1 * Constants.PRECISION_FACTOR, stake_id=0)).run(
        sender=bob, now=now
    )
    scenario += reward_token.mint(
        owner=staking_pool.address, token_id=token_id, token_amount=reward_amount
    )

    scenario.h2("Alice claim after half-period. Alice has a weight 3/4, and loses 50% of the remaining reward ")
    now = now.add_seconds(sp.to_int(staking_pool.data.max_release_period // 2))
    scenario += staking_pool.claim(sp.record(stake_id=1)).run(sender=alice, now=now)
  
    alice_reward = reward_amount // 4 * 3
  
    scenario.verify_equal(reward_token.data.ledger[alice_ledger_key], alice_reward)
 
    scenario.p("Bob exits after half time. Bob have weitgh 1/4 and 50% of those lost by Alice.")
    scenario += staking_pool.withdraw(
        sp.record(stake_id=2)
    ).run(sender=bob.address, now=now)

    bobs_reward = (reward_amount // 4) + (reward_amount // 16 * 3)
    scenario.show(reward_token.data.ledger[bob_ledger_key])
    scenario.verify_equal(reward_token.data.ledger[bob_ledger_key], bobs_reward)

    scenario.h2("Alice withdraw after end stake. Alice has a 0.25% unrelized profit + 50% from losses Bob ")
    now = now.add_seconds(sp.to_int(staking_pool.data.max_release_period // 2))
    scenario += staking_pool.withdraw(sp.record(stake_id=1)).run(sender=alice, now=now)
    alice_reward = reward_amount * 2 - bobs_reward

    scenario.verify_equal(reward_token.data.ledger[alice_ledger_key], alice_reward)

    
    scenario += reward_token.burn(
        owner=alice.address,
        token_id=token_id,
        token_amount=reward_token.data.ledger[alice_ledger_key],
    )
    scenario += reward_token.burn(
        owner=bob.address,
        token_id=token_id,
        token_amount=reward_token.data.ledger[bob_ledger_key],
    )
    
    scenario.h2("Start staking")
    scenario.p("Alice and Bob stake and pay reward")
    now = sp.timestamp(0)
    scenario += staking_pool.deposit(sp.record(token_amount=1 * Constants.PRECISION_FACTOR, stake_id=0)).run(
        sender=alice, now=now
    )
    scenario += staking_pool.deposit(sp.record(token_amount=1 * Constants.PRECISION_FACTOR, stake_id=0)).run(
        sender=bob, now=now
    )

    scenario += reward_token.mint(
        owner=staking_pool.address, token_id=token_id, token_amount=reward_amount * 2
    )

    now = now.add_seconds(sp.to_int(staking_pool.data.max_release_period // 2))
 
    #now = now.add_seconds(sp.to_int(staking_pool.data.max_release_period // 2))
    scenario.p("Bob enter in new stake after half-time")
    scenario.p("Bob stake and pay reward")
    scenario += staking_pool.deposit(sp.record(token_amount=1 * Constants.PRECISION_FACTOR, stake_id=0)).run(
        sender=bob, now=now
    )
    # scenario += staking_pool.deposit(sp.record(token_amount=1 * Constants.PRECISION_FACTOR, stake_id=0)).run(
    #     sender=alice, now=now
    # )
    scenario += reward_token.mint(
        owner=staking_pool.address, token_id=token_id, token_amount=reward_amount * 1
    )

    now = now.add_seconds(sp.to_int(staking_pool.data.max_release_period // 2))
    scenario.p("Alice withdraw after end period")
    scenario.p("Alice should get 50% of the first reward and + 1 reward // 3 because Bob increased the stake weight.")
    scenario.p("stake * (reward / totalDeposit)")
    #scenario.show(reward_token.data.ledger[alice_ledger_key])
    scenario += staking_pool.withdraw(
        sp.record(stake_id=3)
    ).run(sender=alice.address, now=now)
    alice_reward = reward_amount + int((reward_amount / (3 * Constants.PRECISION_FACTOR)) * 1 * Constants.PRECISION_FACTOR)

    scenario.verify_equal(reward_token.data.ledger[alice_ledger_key], alice_reward)

    scenario.p("Bob withdraw after end period 1st stake, and receives 100% of 1st reward + 50%  of second reward")
    scenario += staking_pool.withdraw(
        sp.record(stake_id=4)
    ).run(sender=bob.address, now=now)
    bobs_reward = reward_amount + int((reward_amount / (3 * Constants.PRECISION_FACTOR)) * 1 * Constants.PRECISION_FACTOR)
    scenario.show(reward_token.data.ledger[bob_ledger_key])
    scenario.verify_equal(reward_token.data.ledger[bob_ledger_key], bobs_reward)

    scenario.p("Bob withdraw after end period")
    now = now.add_seconds(sp.to_int(staking_pool.data.max_release_period // 2))
    scenario += staking_pool.withdraw(
        sp.record(stake_id=5)
    ).run(sender=bob.address, now=now)
    bobs_reward += int((reward_amount / (3 * Constants.PRECISION_FACTOR)) * 1 * Constants.PRECISION_FACTOR)
    scenario.verify_equal(reward_token.data.ledger[bob_ledger_key], bobs_reward)

@sp.add_test(name="Normal Staking Pool fa12 full")
def test_normal_staking_pool():
    scenario = sp.test_scenario()
    scenario.h1("Staking Pool Unit Test")
    scenario.table_of_contents()

    scenario.h2("Bootstrapping")
    token_id = sp.nat(0)

    administrator = sp.test_account("Administrator")
    alice = sp.test_account("Alice")
    bob = sp.test_account("Robert")
    charlie = sp.test_account("Charlie")
    dan = sp.test_account("Dan")

    reward_token = fa1.FA12(administrator.address)
    staking_token = fa1.FA12(administrator.address)

    scenario += reward_token
    scenario += staking_token

    scenario.h1("Long Staking with release of 0")
    staking_pool = UnifiedStakingPool(sp.record(token_type=Constants.TOKEN_TYPE_FA1, token_id=token_id, token_address=staking_token.address), False, sp.record(token_type=Constants.TOKEN_TYPE_FA1, token_id=0, token_address=reward_token.address), 180 * 24 * 60 * 60, {administrator.address: 1})

    scenario += staking_pool

    scenario += staking_token.mint(
        address=alice.address,
        value=10 * Constants.PRECISION_FACTOR,
    ).run(sender = administrator)
    scenario += staking_token.mint(
        address=bob.address,
        value=10 * Constants.PRECISION_FACTOR,
    ).run(sender = administrator)

    scenario += staking_token.approve(spender = staking_pool.address, value = 10 * Constants.PRECISION_FACTOR).run(sender = alice)
    scenario += staking_token.approve(spender = staking_pool.address, value = 10 * Constants.PRECISION_FACTOR).run(sender = bob)
   
    scenario.h2("Start staking")
    now = sp.timestamp(0)
    scenario += staking_pool.deposit(sp.record(token_amount=1 * Constants.PRECISION_FACTOR, stake_id=0)).run(
        sender=alice, now=now
    )

    scenario.h2("Claim after a reward has been paid ")
    now = now.add_seconds(sp.to_int(staking_pool.data.max_release_period))
    reward_amount = 1 * Constants.PRECISION_FACTOR
    alice_reward = reward_amount
    bob_reward = 0
    scenario.p("pay reward")
    scenario += reward_token.mint(
        address=staking_pool.address, value=reward_amount
    ).run(sender=administrator)
    scenario.p("alice claims as only user -> gets full reward")
    scenario += staking_pool.claim(sp.record(stake_id=1)).run(sender=alice, now=now)
    scenario.verify_equal(reward_token.data.balances[alice.address].balance, alice_reward)
    scenario.p("Multiclaim yields nothing")
    scenario += staking_pool.claim(sp.record(stake_id=1)).run(sender=alice, now=now)
    scenario.verify_equal(reward_token.data.balances[alice.address].balance, alice_reward)

    scenario.h2("Bob joins before a reward payout")
    scenario += staking_pool.deposit(sp.record(token_amount=1 * Constants.PRECISION_FACTOR, stake_id=0)).run(
        sender=bob, now=now
    )
    now = now.add_seconds(sp.to_int(staking_pool.data.max_release_period))
    scenario.p("pay reward")
    alice_reward += reward_amount // 2
    bob_reward += reward_amount // 2
    scenario += reward_token.mint(
        address=staking_pool.address, value=reward_amount
    ).run(sender=administrator)
    scenario.p("both withdraw, both get same reward")
    scenario += staking_pool.withdraw(sp.record(stake_id=1)).run(sender=alice, now=now)
    scenario += staking_pool.withdraw(sp.record(stake_id=2)).run(sender=bob, now=now)
    scenario.verify_equal(reward_token.data.balances[alice.address].balance, alice_reward)
    scenario.verify_equal(reward_token.data.balances[bob.address].balance, bob_reward)
