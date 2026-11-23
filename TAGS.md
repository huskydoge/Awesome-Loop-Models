# Taxonomy vocabulary

Every paper and blog is classified with the controlled vocabulary below, which follows the chapters of the repo's topic map. There are no free-form tags; a value that is not listed here is a taxonomy change and needs the maintainer. See [TAXONOMY.md](TAXONOMY.md) for how to choose values.

This file is auto-generated from `papers/*.yaml` and `blogs/*.yaml` by `scripts/build.py`.

## Taxonomy sections (`survey_section`)

List every section the entry belongs to; the first entry is its primary section. Counts are primary / any.

### Part I. Foundations

**§2 From Recurrent Computation to Iterative Depth**

- `foundations/recurrence` — §2.1 Recurrent networks and weight sharing across computation (2 / 4)
- `foundations/depth-sharing` — §2.2 Weight sharing across network depth (4 / 6)
- `foundations/implicit` — §2.3 Deep equilibrium and implicit models (7 / 11)
- `foundations/algorithmic` — §2.4 Iterative and algorithmic computation (4 / 8)

### Part II. What Looping Buys

**§3 Capabilities, Benefits and Trade-offs**

- `capabilities/efficiency` — §3.1 Parameter, data, and compute efficiency (8 / 56)
- `capabilities/expressivity` — §3.2 Expressivity and reasoning capacity (20 / 24)
- `capabilities/generalization` — §3.3 Length, easy-to-hard, and compositional generalization (13 / 30)

### Part III. Building, Training and Deploying

**§4 Architecture and Design**

- `architecture/topology` — §4.1 Loop topology (14 / 36)
- `architecture/residual-init` — §4.2 Residual manipulation and initialization (12 / 44)
- `architecture/state-memory` — §4.3 Recurrent state and loop-time memory (12 / 30)
- `architecture/sharing` — §4.4 Weight-sharing schemes and iteration-dependent computation (7 / 31)
- `architecture/depth-control` — §4.5 Controlling recurrence depth (26 / 81)
- `architecture/hybrid` — §4.6 Hybrid looped architectures (20 / 31)

**§5 Learning Algorithms**

- `training/supervision-optimization` — §5.1 Supervision, credit assignment, and loop-specific optimization (29 / 82)
- `training/post-training` — §5.2 Post-training and reinforcement learning (8 / 19)
- `training/retrofitting` — §5.3 Retrofitting pretrained models into looped models (18 / 32)

**§6 Scaling Laws**

- `scaling/compute-optimal` — §6.1 Parameter, depth, and compute-optimal scaling (11 / 24)
- `scaling/test-time` — §6.2 Test-time scaling (14 / 53)

**§7 Systems and Infrastructure**

- `systems/quantization-edge` — §7.1 Quantization and edge deployment (12 / 20)
- `systems/kv-memory` — §7.2 KV cache and memory (18 / 30)
- `systems/batching-parallel` — §7.3 Loop-level batching, scheduling, and parallel execution (13 / 19)

### Part IV. Understanding and Applications

**§8 Understanding Why Looped Models Work**

- `understanding/why` — §8.1 Why looped models work (5 / 18)
- `understanding/interpretability` — §8.2 Mechanistic interpretability (24 / 38)
- `understanding/failure-modes` — §8.3 When looping does not help: limits and failure modes (13 / 45)

**§9 Applications**

- `applications/language-speech-multimodal` — §9.1 Language, code, speech, and multimodal tasks (31 / 41)
- `applications/vision` — §9.2 Visual recognition, restoration, and generation (24 / 34)
- `applications/flow-3d` — §9.3 Flow, stereo, and 3D geometry (10 / 10)
- `applications/graphs-science` — §9.4 Graphs, structured data, and scientific modeling (22 / 32)
- `applications/embodied-other` — §9.5 Embodied AI and other domains (26 / 30)

### Part V. Open Problems

**§10 Open Problems**

- `open-problems/diffusion` — §10.1 Unification with diffusion models (4 / 14)
- `open-problems/depth-into-time` — §10.2 Folding depth into time (1 / 9)
- `open-problems/monitorability-safety` — §10.3 Monitorability and safety (1 / 4)

## Loop topology (`loop_topology`)

Where the loop sits in the network (one value, papers only).

- `whole-stack` (166)
- `prelude-core-coda` (76)
- `partial` (43)
- `hierarchical` (41)
- `shifted-parallel` (12)
- `implicit-fixed-point` (39)
- `unspecified` (47)

## Sharing (`sharing`)

How parameters are shared across iterations (one value, papers only).

- `full` (372)
- `partial-adapter` (30)
- `expert-routed` (12)
- `unspecified` (10)

## Depth control (`depth_control`)

How the number of iterations is decided (one value, papers only).

- `fixed` (208)
- `sampled-train` (36)
- `adaptive-halting` (76)
- `convergence` (49)
- `unspecified` (55)

## Claims (`claims`)

What the paper argues looping buys or costs (list, papers only).

- `param-efficiency` (124)
- `compute-efficiency` (144)
- `memory-efficiency` (60)
- `data-efficiency` (21)
- `expressivity` (31)
- `length-generalization` (39)
- `test-time-scaling` (79)
- `stability` (48)
- `failure-mode` (62)

## Looped-vs-untied comparison (`comparison`)

Which quantity is held fixed when the paper compares looped and untied models (list; empty when there is no such comparison).

- `iso-param` (65)
- `iso-flop` (40)
- `iso-depth` (40)
- `unclear` (52)
