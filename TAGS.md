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

- `capabilities/efficiency` — §3.1 Parameter, data, and compute efficiency (7 / 39)
- `capabilities/expressivity` — §3.2 Expressivity and reasoning capacity (18 / 22)
- `capabilities/generalization` — §3.3 Length, easy-to-hard, and compositional generalization (11 / 23)

### Part III. Building, Training and Deploying

**§4 Architecture and Design**

- `architecture/topology` — §4.1 Loop topology (11 / 27)
- `architecture/residual-init` — §4.2 Residual manipulation and initialization (10 / 35)
- `architecture/state-memory` — §4.3 Recurrent state and loop-time memory (8 / 18)
- `architecture/sharing` — §4.4 Weight-sharing schemes and iteration-dependent computation (6 / 25)
- `architecture/depth-control` — §4.5 Controlling recurrence depth (20 / 60)
- `architecture/hybrid` — §4.6 Hybrid looped architectures (18 / 24)

**§5 Learning Algorithms**

- `training/supervision-optimization` — §5.1 Supervision, credit assignment, and loop-specific optimization (25 / 70)
- `training/post-training` — §5.2 Post-training and reinforcement learning (7 / 14)
- `training/retrofitting` — §5.3 Retrofitting pretrained models into looped models (12 / 19)

**§6 Scaling Laws**

- `scaling/compute-optimal` — §6.1 Parameter, depth, and compute-optimal scaling (9 / 19)
- `scaling/test-time` — §6.2 Test-time scaling (12 / 47)

**§7 Systems and Infrastructure**

- `systems/quantization-edge` — §7.1 Quantization and edge deployment (10 / 14)
- `systems/kv-memory` — §7.2 KV cache and memory (8 / 18)
- `systems/batching-parallel` — §7.3 Loop-level batching, scheduling, and parallel execution (6 / 9)

### Part IV. Understanding and Applications

**§8 Understanding Why Looped Models Work**

- `understanding/why` — §8.1 Why looped models work (2 / 13)
- `understanding/interpretability` — §8.2 Mechanistic interpretability (21 / 32)
- `understanding/failure-modes` — §8.3 When looping does not help: limits and failure modes (11 / 37)

**§9 Applications**

- `applications/language-speech-multimodal` — §9.1 Language, code, speech, and multimodal tasks (25 / 33)
- `applications/vision` — §9.2 Visual recognition, restoration, and generation (20 / 28)
- `applications/flow-3d` — §9.3 Flow, stereo, and 3D geometry (5 / 5)
- `applications/graphs-science` — §9.4 Graphs, structured data, and scientific modeling (18 / 27)
- `applications/embodied-other` — §9.5 Embodied AI and other domains (20 / 23)

### Part V. Open Problems

**§10 Open Problems**

- `open-problems/diffusion` — §10.1 Unification with diffusion models (2 / 11)
- `open-problems/depth-into-time` — §10.2 Folding depth into time (1 / 6)
- `open-problems/monitorability-safety` — §10.3 Monitorability and safety (1 / 4)

## Loop topology (`loop_topology`)

Where the loop sits in the network (one value, papers only).

- `whole-stack` (137)
- `prelude-core-coda` (42)
- `partial` (33)
- `hierarchical` (35)
- `shifted-parallel` (10)
- `implicit-fixed-point` (36)
- `unspecified` (40)

## Sharing (`sharing`)

How parameters are shared across iterations (one value, papers only).

- `full` (293)
- `partial-adapter` (19)
- `expert-routed` (11)
- `unspecified` (10)

## Depth control (`depth_control`)

How the number of iterations is decided (one value, papers only).

- `fixed` (149)
- `sampled-train` (23)
- `adaptive-halting` (64)
- `convergence` (44)
- `unspecified` (53)

## Claims (`claims`)

What the paper argues looping buys or costs (list, papers only).

- `param-efficiency` (96)
- `compute-efficiency` (111)
- `memory-efficiency` (44)
- `data-efficiency` (18)
- `expressivity` (28)
- `length-generalization` (34)
- `test-time-scaling` (67)
- `stability` (40)
- `failure-mode` (51)

## Looped-vs-untied comparison (`comparison`)

Which quantity is held fixed when the paper compares looped and untied models (list; empty when there is no such comparison).

- `iso-param` (39)
- `iso-flop` (27)
- `iso-depth` (21)
- `unclear` (46)
