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

- `capabilities/efficiency` — §3.1 Parameter, data, and compute efficiency (7 / 49)
- `capabilities/expressivity` — §3.2 Expressivity and reasoning capacity (19 / 23)
- `capabilities/generalization` — §3.3 Length, easy-to-hard, and compositional generalization (13 / 25)

### Part III. Building, Training and Deploying

**§4 Architecture and Design**

- `architecture/topology` — §4.1 Loop topology (14 / 33)
- `architecture/residual-init` — §4.2 Residual manipulation and initialization (10 / 40)
- `architecture/state-memory` — §4.3 Recurrent state and loop-time memory (10 / 26)
- `architecture/sharing` — §4.4 Weight-sharing schemes and iteration-dependent computation (6 / 29)
- `architecture/depth-control` — §4.5 Controlling recurrence depth (23 / 71)
- `architecture/hybrid` — §4.6 Hybrid looped architectures (19 / 28)

**§5 Learning Algorithms**

- `training/supervision-optimization` — §5.1 Supervision, credit assignment, and loop-specific optimization (27 / 78)
- `training/post-training` — §5.2 Post-training and reinforcement learning (8 / 16)
- `training/retrofitting` — §5.3 Retrofitting pretrained models into looped models (14 / 25)

**§6 Scaling Laws**

- `scaling/compute-optimal` — §6.1 Parameter, depth, and compute-optimal scaling (11 / 22)
- `scaling/test-time` — §6.2 Test-time scaling (13 / 50)

**§7 Systems and Infrastructure**

- `systems/quantization-edge` — §7.1 Quantization and edge deployment (10 / 15)
- `systems/kv-memory` — §7.2 KV cache and memory (11 / 21)
- `systems/batching-parallel` — §7.3 Loop-level batching, scheduling, and parallel execution (8 / 13)

### Part IV. Understanding and Applications

**§8 Understanding Why Looped Models Work**

- `understanding/why` — §8.1 Why looped models work (4 / 17)
- `understanding/interpretability` — §8.2 Mechanistic interpretability (24 / 37)
- `understanding/failure-modes` — §8.3 When looping does not help: limits and failure modes (12 / 39)

**§9 Applications**

- `applications/language-speech-multimodal` — §9.1 Language, code, speech, and multimodal tasks (29 / 37)
- `applications/vision` — §9.2 Visual recognition, restoration, and generation (23 / 31)
- `applications/flow-3d` — §9.3 Flow, stereo, and 3D geometry (7 / 7)
- `applications/graphs-science` — §9.4 Graphs, structured data, and scientific modeling (20 / 30)
- `applications/embodied-other` — §9.5 Embodied AI and other domains (24 / 27)

### Part V. Open Problems

**§10 Open Problems**

- `open-problems/diffusion` — §10.1 Unification with diffusion models (3 / 12)
- `open-problems/depth-into-time` — §10.2 Folding depth into time (1 / 7)
- `open-problems/monitorability-safety` — §10.3 Monitorability and safety (1 / 4)

## Loop topology (`loop_topology`)

Where the loop sits in the network (one value, papers only).

- `whole-stack` (151)
- `prelude-core-coda` (62)
- `partial` (37)
- `hierarchical` (39)
- `shifted-parallel` (10)
- `implicit-fixed-point` (38)
- `unspecified` (43)

## Sharing (`sharing`)

How parameters are shared across iterations (one value, papers only).

- `full` (332)
- `partial-adapter` (27)
- `expert-routed` (11)
- `unspecified` (10)

## Depth control (`depth_control`)

How the number of iterations is decided (one value, papers only).

- `fixed` (176)
- `sampled-train` (29)
- `adaptive-halting` (73)
- `convergence` (47)
- `unspecified` (55)

## Claims (`claims`)

What the paper argues looping buys or costs (list, papers only).

- `param-efficiency` (112)
- `compute-efficiency` (124)
- `memory-efficiency` (48)
- `data-efficiency` (19)
- `expressivity` (29)
- `length-generalization` (36)
- `test-time-scaling` (74)
- `stability` (42)
- `failure-mode` (56)

## Looped-vs-untied comparison (`comparison`)

Which quantity is held fixed when the paper compares looped and untied models (list; empty when there is no such comparison).

- `iso-param` (51)
- `iso-flop` (35)
- `iso-depth` (31)
- `unclear` (51)
