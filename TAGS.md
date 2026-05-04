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

- `hierarchical-loop` (12)
- `flat-loop` (56)
- `parallel-loop` (2)
- `implicit-layer` (8)

## focus_tags

Controlled vocabulary. The build validates these values, and the interactive browser uses them as filter chips.

- `objective-loss` (5)
- `training-algorithm` (31)
- `architecture` (57)
- `data` (2)
- `inference-algorithm` (39)

## domain_tags

Observed browser-facing domain tags currently used across the repo.

- `language-modeling` (43)
- `reasoning` (37)
- `efficiency` (22)
- `algorithmic-reasoning` (14)
- `theory` (6)
- `scaling` (5)
- `vision` (3)
- `memory-efficiency` (2)
- `RL` (2)
- `sequence-modeling` (2)
- `alignment` (1)
- `compositional-reasoning` (1)
- `FLOPs-efficiency` (1)
- `hyperspectral-imaging` (1)
- `rl-control` (1)
- `robotics-vla` (1)

## tags

Observed alias tags currently used across the repo. These do not appear as browser filter chips, but contributors should still prefer existing spellings.

- `looped-transformer` (10)
- `ACT` (6)
- `TRM` (4)
- `UT` (4)
- `DEQ` (3)
- `Ouro` (3)
- `adaptive-computation-time` (2)
- `depth-recurrent` (2)
- `depth-scaling` (2)
- `looped-llm` (2)
- `LoRA` (2)
- `MoR` (2)
- `mythos` (2)
- `Parcae` (2)
- `recursive-transformer` (2)
- `universal-transformer` (2)
- `activation-compression` (1)
- `AdaPonderLM` (1)
- `adaptive-latent-iteration` (1)
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
- `convergence` (1)
- `CoTFormer` (1)
- `detach` (1)
- `ELT` (1)
- `Exact-ZOH` (1)
- `fixed-point-analysis` (1)
- `generalist-processor` (1)
- `halting` (1)
- `hierarchical-recurrence` (1)
- `HRM` (1)
- `Huginn` (1)
- `hyper-connections` (1)
- `Hyperloop` (1)
- `ILSD` (1)
- `implicit-reasoning` (1)
- `implicit-ssm` (1)
- `iso-depth` (1)
- `isoFLOPs` (1)
- `kv-cache-sharing` (1)
- `latent-cot` (1)
- `latent-thoughts` (1)
- `looped-gpt` (1)
- `LoopFormer` (1)
- `LoopLM` (1)
- `LoopRPT` (1)
- `MDEQ` (1)
- `mechanistic-analysis` (1)
- `memory-banks` (1)
- `memory-tokens` (1)
- `MoDr` (1)
- `MoEUT` (1)
- `MOUE` (1)
- `MoUT` (1)
- `multi-resolution-recursion` (1)
- `multimodal` (1)
- `Neural GPU` (1)
- `phantom-gradient` (1)
- `preference-probing` (1)
- `programmable-computer` (1)
- `RD-VLA` (1)
- `RecursiveVLM` (1)
- `reverse-residual` (1)
- `RGNN` (1)
- `RIM` (1)
- `RLTT` (1)
- `scaling-laws` (1)
- `shared-weight-recurrence` (1)
- `silent-thinking` (1)
- `SpiralFormer` (1)
- `TaH` (1)
- `Think-at-Hard` (1)
- `timestep-encoding` (1)
- `URM` (1)
- `weight-tying` (1)
