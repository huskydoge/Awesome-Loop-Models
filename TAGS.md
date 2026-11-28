# Taxonomy vocabulary

Every paper and blog is classified with the controlled vocabulary below, which follows the chapters of the repo's topic map. There are no free-form tags; a value that is not listed here is a taxonomy change and needs the maintainer. See [TAXONOMY.md](TAXONOMY.md) for how to choose values.

This file is auto-generated from `papers/*.yaml` and `blogs/*.yaml` by `scripts/build.py`.

## Taxonomy sections (`survey_section`)

List every section the entry belongs to; the first entry is its primary section. Counts are primary / any.

### Part I. Foundations

**§2 From Recurrent Computation to Iterative Depth**

- `foundations/recurrence` — §2.1 Recurrent networks and weight sharing across computation (2 / 4)
- `foundations/depth-sharing` — §2.2 Weight sharing across network depth (4 / 6)
- `foundations/implicit` — §2.3 Deep equilibrium and implicit models (7 / 12)
- `foundations/algorithmic` — §2.4 Iterative and algorithmic computation (4 / 8)

### Part II. What Looping Buys

**§3 Capabilities, Benefits and Trade-offs**

- `capabilities/efficiency` — §3.1 Parameter, data, and compute efficiency (9 / 65)
- `capabilities/expressivity` — §3.2 Expressivity and reasoning capacity (20 / 24)
- `capabilities/generalization` — §3.3 Length, easy-to-hard, and compositional generalization (14 / 31)

### Part III. Building, Training and Deploying

**§4 Architecture and Design**

- `architecture/topology` — §4.1 Loop topology (15 / 38)
- `architecture/residual-init` — §4.2 Residual manipulation and initialization (14 / 49)
- `architecture/state-memory` — §4.3 Recurrent state and loop-time memory (14 / 33)
- `architecture/sharing` — §4.4 Weight-sharing schemes and iteration-dependent computation (9 / 36)
- `architecture/depth-control` — §4.5 Controlling recurrence depth (30 / 91)
- `architecture/hybrid` — §4.6 Hybrid looped architectures (21 / 36)

**§5 Learning Algorithms**

- `training/supervision-optimization` — §5.1 Supervision, credit assignment, and loop-specific optimization (31 / 85)
- `training/post-training` — §5.2 Post-training and reinforcement learning (12 / 24)
- `training/retrofitting` — §5.3 Retrofitting pretrained models into looped models (22 / 40)

**§6 Scaling Laws**

- `scaling/compute-optimal` — §6.1 Parameter, depth, and compute-optimal scaling (12 / 28)
- `scaling/test-time` — §6.2 Test-time scaling (14 / 60)

**§7 Systems and Infrastructure**

- `systems/quantization-edge` — §7.1 Quantization and edge deployment (12 / 20)
- `systems/kv-memory` — §7.2 KV cache and memory (18 / 36)
- `systems/batching-parallel` — §7.3 Loop-level batching, scheduling, and parallel execution (17 / 23)

### Part IV. Understanding and Applications

**§8 Understanding Why Looped Models Work**

- `understanding/why` — §8.1 Why looped models work (5 / 20)
- `understanding/interpretability` — §8.2 Mechanistic interpretability (25 / 39)
- `understanding/failure-modes` — §8.3 When looping does not help: limits and failure modes (15 / 47)

**§9 Applications**

- `applications/language-speech-multimodal` — §9.1 Language, code, speech, and multimodal tasks (31 / 41)
- `applications/vision` — §9.2 Visual recognition, restoration, and generation (27 / 40)
- `applications/flow-3d` — §9.3 Flow, stereo, and 3D geometry (10 / 11)
- `applications/graphs-science` — §9.4 Graphs, structured data, and scientific modeling (22 / 32)
- `applications/embodied-other` — §9.5 Embodied AI and other domains (29 / 34)

### Part V. Open Problems

**§10 Open Problems**

- `open-problems/diffusion` — §10.1 Unification with diffusion models (4 / 18)
- `open-problems/depth-into-time` — §10.2 Folding depth into time (2 / 11)
- `open-problems/monitorability-safety` — §10.3 Monitorability and safety (1 / 4)

## Loop topology (`loop_topology`)

Where the loop sits in the network (one value, papers only).

- `whole-stack` (177)
- `prelude-core-coda` (88)
- `partial` (49)
- `hierarchical` (43)
- `shifted-parallel` (15)
- `implicit-fixed-point` (40)
- `unspecified` (49)

## Sharing (`sharing`)

How parameters are shared across iterations (one value, papers only).

- `full` (400)
- `partial-adapter` (38)
- `expert-routed` (13)
- `unspecified` (10)

## Depth control (`depth_control`)

How the number of iterations is decided (one value, papers only).

- `fixed` (230)
- `sampled-train` (43)
- `adaptive-halting` (82)
- `convergence` (51)
- `unspecified` (55)

## Claims (`claims`)

What the paper argues looping buys or costs (list, papers only).

- `param-efficiency` (140)
- `compute-efficiency` (158)
- `memory-efficiency` (63)
- `data-efficiency` (23)
- `expressivity` (32)
- `length-generalization` (40)
- `test-time-scaling` (87)
- `stability` (53)
- `failure-mode` (65)

## Looped-vs-untied comparison (`comparison`)

Which quantity is held fixed when the paper compares looped and untied models (list; empty when there is no such comparison).

- `iso-param` (77)
- `iso-flop` (49)
- `iso-depth` (46)
- `unclear` (53)
