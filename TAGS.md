# TAGS

Prefer existing tags from this file when adding a paper or blog. Only propose a new tag when no current option fits.

This file is auto-generated from `papers/*.yaml` and `blogs/*.yaml` by `scripts/build.py`.

## Selection Policy

- Reuse an existing tag whenever possible.
- Reuse the existing spelling and case exactly.
- Loop Mechanism (`mechanism_tags`) describes the loop form and must be one of `hierarchical-loop`, `flat-loop`, `parallel-loop`, or `implicit-layer`; do not use paper acronyms or lineage labels such as `DEQ` as browser-facing tags.
- `focus_tags` are controlled vocabulary and must come from the allowlist below.
- `domain_tags` are browser-facing domain labels; prefer an existing one before proposing a new domain tag.
- `tags` are optional alias metadata for short model or paper identifiers; prefer existing spellings before proposing a new alias tag.

## Loop Mechanism (`mechanism_tags`)

Loop Mechanism is a controlled loop-form tag set. Use only `hierarchical-loop`, `flat-loop`, `parallel-loop`, or `implicit-layer`.

- `hierarchical-loop` (19)
- `flat-loop` (89)
- `parallel-loop` (5)
- `implicit-layer` (17)

## focus_tags

Controlled vocabulary. The build validates these values, and the interactive browser uses them as filter chips.

- `objective-loss` (7)
- `training-algorithm` (48)
- `architecture` (96)
- `data` (3)
- `inference-algorithm` (74)

## domain_tags

Observed browser-facing domain tags currently used across the repo.

- `reasoning` (61)
- `language-modeling` (59)
- `efficiency` (48)
- `algorithmic-reasoning` (24)
- `scaling` (20)
- `theory` (12)
- `vision` (9)
- `sequence-modeling` (5)
- `memory-efficiency` (4)
- `MoE` (4)
- `RL` (2)
- `robotics-vla` (2)
- `adaptive-compute` (1)
- `alignment` (1)
- `compositional-reasoning` (1)
- `FLOPs-efficiency` (1)
- `hyperspectral-imaging` (1)
- `rl-control` (1)
- `speech-recognition` (1)
- `tabular-data` (1)
- `world-modeling` (1)

## tags

Observed alias tags currently used across the repo. These do not appear as browser filter chips, but contributors should still prefer existing spellings.

- `looped-transformer` (24)
- `ACT` (7)
- `DEQ` (7)
- `TRM` (7)
- `HRM` (6)
- `looped-llm` (6)
- `recursive-transformer` (5)
- `shared-weight-recurrence` (5)
- `Ouro` (4)
- `UT` (4)
- `convergence` (3)
- `depth-recurrent` (3)
- `depth-scaling` (3)
- `mechanistic-analysis` (3)
- `weight-tying` (3)
- `adaptive-computation-time` (2)
- `adaptive-latent-iteration` (2)
- `halting` (2)
- `hyper-connections` (2)
- `LoopLM` (2)
- `LoRA` (2)
- `MoR` (2)
- `mythos` (2)
- `Parcae` (2)
- `test-time-compute` (2)
- `universal-transformer` (2)
- `activation-compression` (1)
- `AdaPonderLM` (1)
- `AlgoFormer` (1)
- `ANIRA` (1)
- `attention-mixture` (1)
- `BPTD` (1)
- `BPTT` (1)
- `ChainGPT` (1)
- `checkpointing` (1)
- `CoLa` (1)
- `compositional-generalization` (1)
- `compute-bounded-policy` (1)
- `CoTFormer` (1)
- `detach` (1)
- `ELT` (1)
- `Exact-ZOH` (1)
- `fixed-point-analysis` (1)
- `fully-looped-transformer` (1)
- `generalist-processor` (1)
- `GRAM` (1)
- `hierarchical-recurrence` (1)
- `HRM-Text` (1)
- `Huginn` (1)
- `Hyperloop` (1)
- `ILSD` (1)
- `implicit-reasoning` (1)
- `implicit-ssm` (1)
- `iso-depth` (1)
- `isoFLOPs` (1)
- `kv-cache-sharing` (1)
- `latent-cot` (1)
- `latent-refinement` (1)
- `latent-thoughts` (1)
- `latent-trajectories` (1)
- `looped-depth-up-scaling` (1)
- `looped-gpt` (1)
- `LoopFormer` (1)
- `LoopMDM` (1)
- `LoopRPT` (1)
- `LoopUS` (1)
- `masked-diffusion-language-model` (1)
- `MDEQ` (1)
- `MELT` (1)
- `memory-banks` (1)
- `memory-tokens` (1)
- `MoDr` (1)
- `MoE` (1)
- `MoEUT` (1)
- `MOUE` (1)
- `MoUT` (1)
- `multi-resolution-recursion` (1)
- `multimodal` (1)
- `Neural GPU` (1)
- `phantom-gradient` (1)
- `preference-probing` (1)
- `PrefixLM` (1)
- `programmable-computer` (1)
- `PTRM` (1)
- `RD-VLA` (1)
- `recurrent-scaling` (1)
- `recursive-reasoning` (1)
- `RecursiveVLM` (1)
- `reverse-residual` (1)
- `RGNN` (1)
- `RIM` (1)
- `RLTT` (1)
- `scaling-laws` (1)
- `silent-thinking` (1)
- `SpiralFormer` (1)
- `stability-analysis` (1)
- `STARS` (1)
- `stochastic-rollouts` (1)
- `TaH` (1)
- `Think-at-Hard` (1)
- `timestep-encoding` (1)
- `training-free-looping` (1)
- `URM` (1)
