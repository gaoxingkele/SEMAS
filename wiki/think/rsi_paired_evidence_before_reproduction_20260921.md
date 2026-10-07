---
date: 2026-09-21
tags: [thinking, rsi, paired-evidence, selection]
related: [../factor_rsi_phase2_paired_selection_20260921.md]
---

# Reproduction needs paired evidence, not a better isolated score

A child policy and its parent generate different factor-search trajectories.
Comparing runs that also use different random seeds confounds the policy edit
with search noise. Pairing on the seed does not remove all variance, but it
turns each comparison into a controlled difference with a shared stochastic
starting point.

[source: arXiv:2505.22954]

The archive needs two notions of validity. Single-run validity proves that an
execution receipt is authentic and respects the examiner. Paired validity asks
whether the mutation is repeatably better than its actual parent. A node may be
valid evidence without yet being a valid reproductive parent.

[source: china_a_share_alpha/loop/recursive_self_improve.py]

Three pairs are a cost-aware minimum, not a claim of strong statistical power.
Mean, median, win rate, and worst-case gates deliberately examine different
failure modes. If a mutation is borderline, the correct recovery is to add
matched seeds to the same campaign rather than relax the evaluator.

[source: china_a_share_alpha/loop/paired_policy_evaluation.py]
