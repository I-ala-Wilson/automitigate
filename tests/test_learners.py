import numpy as np

from automitigate.learners import (LEARNERS, ChangeDetectTS, DiscountedTS, DynamicOracle, EpsGreedy,
                                   FixedArm, SlidingWindowTS, StaticOracle, Thompson, UCB1, run_episode)


def constant_table(means, T=300, S=5, noise=0.0, seed=0):
    rng = np.random.default_rng(seed)
    base = np.array(means)[None, :, None]
    return np.clip(base + noise * rng.standard_normal((T, len(means), S)), 0, 1)


def flip_table(T=300, flip=150, S=5, noise=0.03, seed=0):
    rng = np.random.default_rng(seed)
    means = np.zeros((T, 3))
    means[:flip] = [0.6, 0.9, 0.7]
    means[flip:] = [0.6, 0.7, 0.9]
    return np.clip(means[:, :, None] + noise * rng.standard_normal((T, 3, S)), 0, 1)


def test_13_thompson_bernoulli_trick_picks_best():
    out = run_episode(Thompson(3, seed=1), constant_table([0.6, 0.7, 0.9]), np.random.default_rng(0))
    arms = np.array(out["arms"][100:300])
    assert (arms == 2).mean() >= 0.9


def test_ucb1_and_eps_greedy_find_best():
    for L in (UCB1, EpsGreedy):
        out = run_episode(L(3, seed=2), constant_table([0.6, 0.7, 0.9]), np.random.default_rng(1))
        assert (np.array(out["arms"][100:300]) == 2).mean() >= 0.6, L.name


def test_nonstationary_learners_recover_after_flip():
    table = flip_table()
    for L, hp in ((DiscountedTS, {"gamma": 0.9}), (SlidingWindowTS, {"window": 20}),
                  (ChangeDetectTS, {"window": 20, "threshold": 3.0})):
        out = run_episode(L(3, seed=3, **hp), table, np.random.default_rng(2), switches=[150])
        late = np.array(out["arms"][220:300])
        assert (late == 2).mean() >= 0.5, (L.name, (late == 2).mean())
        assert out["switch_lag"][150] is not None and out["switch_lag"][150] < 130, (L.name, out["switch_lag"])
    stale = run_episode(Thompson(3, seed=3), table, np.random.default_rng(2), switches=[150])
    assert (np.array(stale["arms"][220:300]) == 2).mean() < 0.9  # plain Thompson is slower to move


def test_fixed_policies_and_regret():
    table = flip_table(noise=0.0)
    rng = np.random.default_rng(0)
    dyn = run_episode(DynamicOracle(3, best_per_step=[1] * 150 + [2] * 150), table, rng)
    assert dyn["pseudo_regret"][-1] == 0.0
    st = run_episode(StaticOracle(3, arm=1), table, rng)
    assert abs(st["pseudo_regret"][-1] - 150 * 0.2) < 1e-9
    a0 = run_episode(FixedArm(3, arm=0), table, rng)
    assert a0["pseudo_regret"][-1] > st["pseudo_regret"][-1]
    assert len(a0["rewards"]) == 300 and all(r == 0.6 for r in a0["rewards"])


def test_api_and_names():
    for name, L in LEARNERS.items():
        l = L(8, seed=0)
        assert l.name == name
        a = l.select()
        assert 0 <= a < 8
        l.update(a, 0.5)
        l.reset()
    out = run_episode(Thompson(2, seed=0), constant_table([0.5, 0.5], T=10, S=3), np.random.default_rng(0),
                      pulls_per_snapshot=4, seed_cols=[0, 1])
    assert len(out["arms"]) == 40 and len(out["pseudo_regret"]) == 40
