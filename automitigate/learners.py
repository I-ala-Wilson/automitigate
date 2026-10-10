"""Bandit learners, fixed policies and the replay episode.

Common API: Learner(n_arms, seed, **hp); select() -> arm; update(arm, reward); reset(); name.
Rewards are mirror scores in [0, 1]; the Thompson family uses the Bernoulli trick
(Agrawal & Goyal 2012): draw b ~ Bernoulli(reward) and update a Beta posterior.
Pure Python + numpy so it also runs in the browser sandbox.
"""
from __future__ import annotations

import math
from collections import deque

import numpy as np


class Learner:
    name = "learner"

    def __init__(self, n_arms: int, seed: int = 0, **hp):
        self.k = n_arms
        self.seed = seed
        self.hp = hp
        self.reset()

    def reset(self):
        self.rng = np.random.default_rng(self.seed)
        self.t = 0
        self.n = np.zeros(self.k)
        self.s = np.zeros(self.k)

    def select(self) -> int:
        raise NotImplementedError

    def update(self, arm: int, reward: float):
        self.t += 1
        self.n[arm] += 1
        self.s[arm] += reward

    def _bernoulli(self, reward: float) -> int:
        return int(self.rng.random() < min(max(reward, 0.0), 1.0))


class EpsGreedy(Learner):
    name = "eps-greedy"

    def select(self):
        eps = self.hp.get("eps", 0.1)
        untried = np.flatnonzero(self.n == 0)
        if untried.size:
            return int(self.rng.choice(untried))
        if self.rng.random() < eps:
            return int(self.rng.integers(self.k))
        return int(np.argmax(self.s / self.n))


class UCB1(Learner):
    name = "UCB1"

    def select(self):
        untried = np.flatnonzero(self.n == 0)
        if untried.size:
            return int(untried[0])
        bonus = np.sqrt(2.0 * math.log(self.t + 1) / self.n)
        return int(np.argmax(self.s / self.n + bonus))


class Thompson(Learner):
    name = "Thompson"

    def reset(self):
        super().reset()
        self.alpha = np.ones(self.k)
        self.beta = np.ones(self.k)

    def select(self):
        return int(np.argmax(self.rng.beta(self.alpha, self.beta)))

    def update(self, arm, reward):
        super().update(arm, reward)
        b = self._bernoulli(reward)
        self.alpha[arm] += b
        self.beta[arm] += 1 - b


class DiscountedTS(Thompson):
    """Raj & Kalyani 2017: every posterior is multiplied by gamma each round."""
    name = "Discounted TS"

    def update(self, arm, reward):
        gamma = self.hp.get("gamma", 0.9)
        self.alpha = 1.0 + gamma * (self.alpha - 1.0)
        self.beta = 1.0 + gamma * (self.beta - 1.0)
        Thompson.update(self, arm, reward)


class SlidingWindowTS(Thompson):
    """Trovo et al. 2020: posterior from the last `window` pulls only."""
    name = "Sliding-Window TS"

    def reset(self):
        super().reset()
        self.hist = deque()

    def update(self, arm, reward):
        Learner.update(self, arm, reward)
        b = self._bernoulli(reward)
        self.hist.append((arm, b))
        if len(self.hist) > self.hp.get("window", 20):
            self.hist.popleft()
        self.alpha = np.ones(self.k)
        self.beta = np.ones(self.k)
        for a, bb in self.hist:
            self.alpha[a] += bb
            self.beta[a] += 1 - bb


class ChangeDetectTS(Thompson):
    """Thompson base with the M-UCB change detector (Cao et al. 2019): per arm, keep the
    last `window` Bernoulli draws; if the sums of the two halves differ by more than
    `threshold`, restart every posterior. `explore` forces a round-robin pull with that
    probability so quiet arms keep being monitored."""
    name = "Change-Detection TS"

    def reset(self):
        super().reset()
        self.win = [deque() for _ in range(self.k)]
        self.restarts = []
        self.rr = 0

    def select(self):
        if self.rng.random() < self.hp.get("explore", 0.05):
            self.rr = (self.rr + 1) % self.k
            return self.rr
        return Thompson.select(self)

    def update(self, arm, reward):
        Learner.update(self, arm, reward)
        b = self._bernoulli(reward)
        self.alpha[arm] += b
        self.beta[arm] += 1 - b
        w = self.hp.get("window", 20)
        d = self.win[arm]
        d.append(b)
        if len(d) > w:
            d.popleft()
        if len(d) == w:
            h = w // 2
            if abs(sum(list(d)[:h]) - sum(list(d)[h:])) > self.hp.get("threshold", 3.0):
                self.restarts.append(self.t)
                self.alpha = np.ones(self.k)
                self.beta = np.ones(self.k)
                for q in self.win:
                    q.clear()


class FixedArm(Learner):
    def __init__(self, n_arms, seed=0, arm=0, **hp):
        self.arm = arm
        self.name = f"arm {arm}"
        super().__init__(n_arms, seed, **hp)

    def select(self):
        return self.arm


class StaticOracle(FixedArm):
    """The best fixed arm in hindsight (arm index supplied by the analysis)."""

    def __init__(self, n_arms, seed=0, arm=0, **hp):
        super().__init__(n_arms, seed, arm, **hp)
        self.name = "static oracle"


class DynamicOracle(Learner):
    """The best arm per snapshot (list supplied by the analysis); advances one step per update."""
    name = "dynamic oracle"

    def __init__(self, n_arms, seed=0, best_per_step=(), **hp):
        self.best = list(best_per_step)
        super().__init__(n_arms, seed, **hp)

    def select(self):
        return int(self.best[min(self.t, len(self.best) - 1)])


LEARNERS = {
    "eps-greedy": EpsGreedy, "UCB1": UCB1, "Thompson": Thompson, "Discounted TS": DiscountedTS,
    "Sliding-Window TS": SlidingWindowTS, "Change-Detection TS": ChangeDetectTS,
}


def smooth_means(means: np.ndarray, window: int) -> np.ndarray:
    """Centred moving average along the snapshot axis (edge-padded); window <= 1 is a no-op."""
    if window <= 1:
        return means
    k = np.ones(window) / window
    pad = window // 2
    return np.vstack([np.convolve(np.pad(means[:, a], (pad, pad), mode="edge"), k, mode="valid")[:len(means)]
                      for a in range(means.shape[1])]).T


def run_episode(learner: Learner, samples: np.ndarray, rng: np.random.Generator,
                horizon: int | None = None, pulls_per_snapshot: int = 1,
                switches: list[int] | None = None, seed_cols: list[int] | None = None,
                smooth: int = 0) -> dict:
    """Replay one episode on stored rewards.

    samples: array [T, K, S] of stored rewards (NaN where missing); the learner observes one
    stored sample per pull drawn at random from the chosen snapshot's seeds (seed_cols
    restricts which). Pseudo-regret is cumulative versus the seed-mean best arm per snapshot.
    switch_lag: for each snapshot index in `switches`, pulls until the learner's choice equals
    the new best arm for 10 consecutive pulls (None if never). smooth > 1 replaces the per-snapshot
    seed means by a centred moving average of that many snapshots before taking the oracle (used
    for the IonQ-like tables, which have 5 seeds per step)."""
    T, K, S = samples.shape
    cols = list(range(S)) if seed_cols is None else list(seed_cols)
    means = smooth_means(np.nanmean(samples[:, :, cols], axis=2), smooth)
    best = np.nanargmax(means, axis=1)
    horizon = T if horizon is None else min(horizon, T)
    learner.reset()
    rewards, arms, regret = [], [], []
    cum = 0.0
    for t in range(horizon):
        for _ in range(pulls_per_snapshot):
            a = learner.select()
            pool = samples[t, a, cols]
            pool = pool[~np.isnan(pool)]
            r = float(rng.choice(pool)) if pool.size else float(means[t, a])
            learner.update(a, r)
            rewards.append(r)
            arms.append(a)
            cum += float(means[t, best[t]] - means[t, a])
            regret.append(cum)
    lag = {}
    for s in switches or []:
        target = int(best[min(s, horizon - 1)])
        start = s * pulls_per_snapshot
        run_len, lag[s] = 0, None
        for i in range(start, len(arms)):
            run_len = run_len + 1 if arms[i] == target else 0
            if run_len >= 10:
                lag[s] = i - start + 1 - 10
                break
    return {"rewards": rewards, "arms": arms, "pseudo_regret": regret, "switch_lag": lag,
            "best": best.tolist(), "name": learner.name}
