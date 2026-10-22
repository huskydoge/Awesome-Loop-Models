# Awesome Loop Models Taxonomy

## Core Inclusion Rule

The strict loop-model catalog targets papers where:

> A shared learned internal layer, block, module, or operator is reused, either along depth within one forward pass or along time, by feeding a state it computed back through the same layers for the next token or step.

This is the main scope boundary. The qualifying loop must be inside the model's own computation, not an external optimization, search, planning, or solver routine. Both directions of reuse count:

- **Depth recurrence:** the same block is applied repeatedly to the same position within one forward pass (looped, recurrent-depth, weight-tied and implicit models).
- **Depth folded into time:** a high-level or late-layer state computed for one token or step is fed back into the same layers' computation for the next one (Feedback Transformers, Latent Recurrent Transformers, shift-1 and pipelined loops). The topic map files these under §10.2 `open-problems/depth-into-time`.

## Scope Scale

The easiest way to understand the boundary is as a scale:

1. Agent loop
2. Autoregressive loop
3. Latent reasoning / multi-pass inference
4. Loop model

Only the fourth category is the main target of this repo. Recurrence over time counts when it reuses the model's layers on a state they already computed, so that depth is folded into time. Ordinary sequence recurrence, where a recurrent cell or state-space update only carries a memory from one step to the next, does not count by itself.

### Adjacent-work exception

A rare, curator-approved paper may remain for its conceptual value with `catalog_fit: adjacent`. It must be visibly labeled **Adjacent work** and have primary-source audit evidence explaining why it falls outside the strict boundary. Omitting `catalog_fit` means strict scope.

## In Scope

- recurrent-depth / weight-tied transformers
- depth folded into time: high-level states fed back through the same layers for the next token or step
- adaptive halting over a reused recurrent block
- deep equilibrium / fixed-point / implicit-layer models
- shared processors repeatedly executed in neural algorithmic reasoning
- theory or mechanism papers about loop models
- architecture or algorithm papers that improve loop-model performance, efficiency, training, inference, or memory use
- application papers showing loop models on concrete external domains or tasks

## Out of Scope

- agent/tool loops
- plain autoregressive decoding by itself
- latent reasoning via repeated full model calls
- diffusion reasoning papers
- energy-based iterative inference papers
- recursive model calls
- untied depth scaling without explicit reuse of layers
- external search or planning over arbitrary layer orders when the qualifying loop is not a shared internal forward-process recurrence
- ordinary sequence recurrence (RNN, LSTM, state-space or linear-attention updates) that carries a memory across steps without feeding a computed state back through the same layers
- continuous latent chain-of-thought that only feeds the last hidden state back as the next input embedding (COCONUT-style) without cross-token feedback into the layers

## Organization: the topic map

The catalog is organized as a topic map of parts, chapters and sections, so the browser and the README share one map of the field. There are no shelves, categories or free-form tags. [TAGS.md](TAGS.md) lists every value with its current usage count. Every value below is closed: a paper that does not fit is a reason to discuss a taxonomy change with the maintainer, not to invent a value.

Each paper records two things:

1. **Where it belongs in the topic map** — `survey_section` (a historical field name), a list of every taxonomy section the paper contributes to, with its primary section first. The browser files the paper under that primary section.
2. **What its loop looks like and what it claims** — the design axes `loop_topology`, `sharing` and `depth_control` (§4), plus `claims` and `comparison` (§3).

`survey_core: true` (a historical field name) marks core reference papers for loop models. `must_read: true` is a maintainer-only flag.

## Taxonomy sections (`survey_section`)

| § | `survey_section` | Covers |
|:--|:--|:--|
| 2.1 | `foundations/recurrence` | **Recurrent networks and weight sharing across computation.** RNNs, ACT and PonderNet, and other early weight sharing across computation steps. |
| 2.2 | `foundations/depth-sharing` | **Weight sharing across network depth.** Early weight-tied depth: recursive CNNs, Universal Transformers, ALBERT-style sharing. |
| 2.3 | `foundations/implicit` | **Deep equilibrium and implicit models.** DEQs, implicit layers, Neural ODE-style fixed points, implicit GNNs. |
| 2.4 | `foundations/algorithmic` | **Iterative and algorithmic computation.** Neural GPU, deep thinking networks, neural algorithmic processors. |
| 3.1 | `capabilities/efficiency` | **Parameter, data, and compute efficiency.** What looping saves in parameters, data or compute, and what it does not. |
| 3.2 | `capabilities/expressivity` | **Expressivity and reasoning capacity.** Theory and evidence on what looped models can compute and reason about. |
| 3.3 | `capabilities/generalization` | **Length, easy-to-hard, and compositional generalization.** Length, easy-to-hard and compositional generalization from extra iterations. |
| 4.1 | `architecture/topology` | **Loop topology.** Where the recurrence sits: whole stack, prelude-core-coda, partial, hierarchical, shifted. |
| 4.2 | `architecture/residual-init` | **Residual manipulation and initialization.** Input injection, residual scaling and gating, initialization of the looped state. |
| 4.3 | `architecture/state-memory` | **Recurrent state and loop-time memory.** What state and history are carried across iterations. |
| 4.4 | `architecture/sharing` | **Weight-sharing schemes and iteration-dependent computation.** Full vs partial sharing, iteration embeddings, per-loop adapters, loop-dependent modulation. |
| 4.5 | `architecture/depth-control` | **Controlling recurrence depth.** Training-time depth distributions and adaptive, elastic or halting-based depth at inference. |
| 4.6 | `architecture/hybrid` | **Hybrid looped architectures.** Loop x MoE, loops with linear/state-space/convolutional mixers, loops inside other generators. |
| 5.1 | `training/supervision-optimization` | **Supervision, credit assignment, and loop-specific optimization.** Per-step or final supervision, BPTT/truncated/implicit gradients, loop-specific stability. |
| 5.2 | `training/post-training` | **Post-training and reinforcement learning.** SFT, distillation and RL after pretraining a looped model. |
| 5.3 | `training/retrofitting` | **Retrofitting pretrained models into looped models.** Turning a pretrained untied model into a looped one. |
| 6.1 | `scaling/compute-optimal` | **Parameter, depth, and compute-optimal scaling.** Scaling laws over parameters, depth and loops; iso-param/iso-FLOP comparisons. |
| 6.2 | `scaling/test-time` | **Test-time scaling.** Spending more iterations at inference. |
| 7.1 | `systems/quantization-edge` | **Quantization and edge deployment.** Quantization, compression and on-device deployment of looped models. |
| 7.2 | `systems/kv-memory` | **KV cache and memory.** KV caches and memory across loops. |
| 7.3 | `systems/batching-parallel` | **Loop-level batching, scheduling, and parallel execution.** Batching, scheduling and parallel execution of loop iterations. |
| 8.1 | `understanding/why` | **Why looped models work.** Analyses of why and when looping helps. |
| 8.2 | `understanding/interpretability` | **Mechanistic interpretability.** Mechanistic interpretability of looped models. |
| 8.3 | `understanding/failure-modes` | **When looping does not help: limits and failure modes.** Limits, negative results and failure modes of looping. |
| 9.1 | `applications/language-speech-multimodal` | **Language, code, speech, and multimodal tasks.** Language, code, speech and multimodal tasks. |
| 9.2 | `applications/vision` | **Visual recognition, restoration, and generation.** Visual recognition, restoration and generation. |
| 9.3 | `applications/flow-3d` | **Flow, stereo, and 3D geometry.** Optical flow, stereo and 3D geometry. |
| 9.4 | `applications/graphs-science` | **Graphs, structured data, and scientific modeling.** Graphs, tabular and structured data, scientific modeling. |
| 9.5 | `applications/embodied-other` | **Embodied AI and other domains.** Robotics, VLA, RL, and other domains. |
| 10.1 | `open-problems/diffusion` | **Unification with diffusion models.** Combining looping with diffusion or denoising. |
| 10.2 | `open-problems/depth-into-time` | **Folding depth into time.** Looping across positions (shift-1 recurrence, pipelined loops) that folds depth into the sequence dimension. |
| 10.3 | `open-problems/monitorability-safety` | **Monitorability and safety.** Monitoring, oversight and safety of latent looped computation. |

Chapters: §2 From Recurrent Computation to Iterative Depth; §3 Capabilities, Benefits and Trade-offs; §4 Architecture and Design; §5 Learning Algorithms; §6 Scaling Laws; §7 Systems and Infrastructure; §8 Understanding Why Looped Models Work; §9 Applications; §10 Open Problems.

### Choosing sections

1. First check scope: is a shared learned layer, block, module or operator reused, either within one forward pass or by feeding a computed state back through the same layers for the next token or step? If not, drop the paper.
2. Pick the **primary** section by the paper's main contribution, i.e. the section where a reader would look for it first.
   - A design evaluated on language modeling is an `architecture/*`, `training/*`, `scaling/*` or `systems/*` paper, not `applications/language-speech-multimodal`. Use an `applications/*` section as primary only when the main takeaway is about that external domain.
   - Theory of what loops can compute goes to `capabilities/expressivity`; an analysis of why a trained looped model works goes to `understanding/why`; probing and circuits go to `understanding/interpretability`; negative results go to `understanding/failure-modes`.
   - `foundations/*` is for lineage papers, mostly before 2023.
3. Add every other section the paper substantively contributes to. Do not add a section for a passing mention.

## Design axes

### `loop_topology` (one value)

`whole-stack` (the whole block stack repeats), `prelude-core-coda` (a middle core loops between distinct input and output layers), `partial` (only an early block or sub-module loops), `hierarchical` (coupled loops at different rates, e.g. HRM/TRM), `shifted-parallel` (loops pipelined across tokens or run in parallel branches), `implicit-fixed-point` (output solved as a fixed point), or `unspecified`.

### `sharing` (one value)

`full` (all looped parameters tied), `partial-adapter` (shared core plus per-iteration adapters, LoRA, or embeddings), `expert-routed` (per-iteration routing among experts or LoRAs), or `unspecified`.

### `depth_control` (one value)

`fixed`, `sampled-train` (loop count randomized or scheduled in training without a learned halting policy), `adaptive-halting` (learned or confidence-based stopping, depth routers), `convergence` (iterate to a fixed-point tolerance), or `unspecified`.

### `claims` (list)

What the paper argues looping buys or costs: `param-efficiency`, `compute-efficiency`, `memory-efficiency`, `data-efficiency`, `expressivity`, `length-generalization`, `test-time-scaling`, `stability`, `failure-mode`.

### `comparison` (list)

Only for papers that compare looped and untied models: which quantity is held fixed. `iso-param` (same unique parameters), `iso-flop` (same executed compute), `iso-depth` (K loops vs K untied layers), or `unclear` when the paper compares without stating the control. Use `[]` when there is no such comparison.

### `survey_core` (bool)

`true` for the core set of reference papers on loop models (the field name is historical). It does not change repo inclusion.

## No free-form tags

Model names, acronyms and method names (Huginn, Ouro, TRM, ELR, …) belong in the title and `desc`, which the browser searches. Do not add `tags`, `mechanism_tags`, `focus_tags`, `domain_tags`, `category` or `foundation`: the build rejects them.

## Blogs

Blogs are intentionally separate from the paper catalog. They live in one flat `Blogs` section and list only the `survey_section` values they discuss; they do not use the design axes.

A blog belongs here only if it is a substantive public long-form technical post about loop models or closely related loop-model questions: technical deep-dives, lab blog posts, long-form essays, tutorials with real technical content, long X articles, Substack or personal posts with substantial analysis. Short announcement posts, marketing pages, bare link roundups and news reposts are out of scope.
