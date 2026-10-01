# Awesome Loop Models Taxonomy

## Core Inclusion Rule

The strict loop-model catalog targets papers where:

> Within one model forward process, a shared learned internal layer, block, module, or operator is reused.

This is the main scope boundary. The qualifying loop must be inside the model's forward computation, not an external optimization, search, planning, or solver routine.

## Scope Scale

The easiest way to understand the boundary is as a scale:

1. Agent loop
2. Autoregressive loop
3. Latent reasoning / multi-pass inference
4. Loop model

Only the fourth category is the main target of this repo. Standard sequence-time recurrence across tokens or timesteps is not enough by itself; the repo's target is iterative depth or latent recurrence inside one forward pass.

### Adjacent-work exception

A rare, curator-approved paper may remain for its conceptual value with `catalog_fit: adjacent`. It must be visibly labeled **Adjacent work**, carry no strict `mechanism_tags`, and have primary-source audit evidence explaining why it falls outside the strict boundary. Omitting `catalog_fit` means strict scope.

## In Scope

- recurrent-depth / weight-tied transformers
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
- sequence recurrence papers that do not add a genuine loop-model architectural argument beyond standard recurrence

## Primary Paper Categories

The public taxonomy uses exactly three flat paper categories. New canonical paper YAML should use one of these `category` values and omit `category_path`.

### Theoretical and Mechanical Analysis (`analysis`)

Use this category when the paper is mainly analytical.

Typical fits:
- formal theory
- expressive-power results
- convergence / stability / fixed-point analysis
- mechanism analysis
- probing, diagnostics, or interpretability
- explanations of why loop models behave as they do

This category is for understanding loop models, not mainly for proposing a new architecture or demonstrating a task result.

### Architecture and Algorithm Designs (`designs`)

Use this category when the paper mainly proposes a loop-model architecture or algorithm.

Typical fits:
- new looped architectures
- recurrent computation-graph designs
- adaptive-depth / routing / halting algorithms
- training or inference algorithms for loop models
- efficiency methods
- memory-compression methods
- domain-specialized loop-model designs when the main contribution is the design itself

This category should absorb papers whose core claim is better performance, efficiency, memory use, training, or inference through a new architecture or algorithm.

### Applications Focused (`applications`)

Use this category when the paper mainly demonstrates loop models on a concrete external domain or task.

Typical fits:
- robotics and VLA
- multimodal tasks
- tabular data
- graph data
- vision, scientific, or domain-specific data where the main point is task/domain performance
- applied evaluations whose main takeaway is that loop models work in that setting

This category is not a catch-all for any empirical result. If the main reusable idea is an architecture or algorithm, use `designs`; if the main contribution is analysis, use `analysis`.

## Foundation Badge

Foundation is not a separate top-level category.

Canonical anchor papers can carry:

- `foundation: true`

Use this badge only for papers that introduced or canonized a major loop-model primitive or formulation that later work treats as a standard reference point. Examples include ACT, Universal Transformers, and DEQ.

## Classification Note

> The paper categories are intentionally coarse: Theoretical and Mechanical Analysis, Architecture and Algorithm Designs, and Applications Focused. Foundation status plus Loop Mechanism / focus / domain tags carry secondary structure without introducing a separate lineage-tag axis.

## Tagging Scheme

See [TAGS.md](TAGS.md) for the current repo-wide tag inventory and preferred spellings.

### Loop Mechanism (`mechanism_tags`)

Use Loop Mechanism (`mechanism_tags`) only for the loop form. This is a closed vocabulary with exactly four values:

- `hierarchical-loop` — nested, recursive, multi-level, or coarse-to-fine loop structure
- `flat-loop` — a single shared block/layer/module repeated in a flat depth/time loop
- `parallel-loop` — parallel, branched, or multi-path loop execution
- `implicit-layer` — fixed-point, equilibrium, or implicit-layer computation

Do not use paper abbreviations such as `DEQ`, `UT`, `HRM`, or `Ouro`, and do not use fine-grained mechanism labels such as `recurrent-depth`, `adaptive-compute`, `algorithmic-loop`, `memory-compression`, or `recursive-loop` as browser-facing Loop Mechanism tags. Keep paper/model aliases in optional `tags` if they are useful metadata.

### `focus_tags`

Use these for contribution emphasis:
- `objective-loss`
- `training-algorithm`
- `architecture`
- `data`
- `inference-algorithm`

These are controlled vocabulary. The build validates them.

### `domain_tags`

Use these for problem/domain labels.

Common examples:
- `language-modeling`
- `reasoning`
- `algorithmic-reasoning`
- `vision`
- `robotics-vla`
- `multimodal`
- `tabular-data`
- `graph-data`

### `tags`

Use `tags` for optional aliases or short identifiers kept in YAML / README metadata. They are useful metadata, but they are not the main browser filter axis.

Examples: `DEQ`, `UT`, `ACT`, `HRM`, `Ouro`, `LoopLM`.

## Survey-Aligned Axes

These fields follow the outline of the Looped Models Survey so that the catalog and the survey share one map of the field. They are optional in the schema while the browser is being migrated, but every catalog paper carries them and new papers should fill all of them. The build validates every value; see [TAGS.md](TAGS.md) for current counts.

### `survey_section` (list, first entry = primary)

Every survey section where the paper belongs, primary contribution first. `analysis` papers usually land in `benefits/expressivity`, `benefits/limits`, or `interpretability`.

| Part | Sections |
| --- | --- |
| Foundations (§2) | `foundations/recurrence`, `foundations/depth-sharing`, `foundations/implicit`, `foundations/algorithmic` — lineage papers, mostly before 2023 |
| What looping buys (§3) | `benefits/efficiency`, `benefits/expressivity`, `benefits/generalization`, `benefits/limits` |
| Architecture (§4) | `design/topology`, `design/residual-injection`, `design/state-memory`, `design/sharing-scheme`, `design/depth-control`, `design/loop-x` |
| Training (§5) | `train/supervision`, `train/gradients`, `train/stability`, `train/post-training`, `train/retrofitting` |
| Scaling (§6) | `scaling/compute-optimal`, `scaling/test-time` |
| Systems (§7) | `systems/quantization-edge`, `systems/kv-memory`, `systems/batching-parallel` |
| Interpretability (§8) | `interpretability` |
| Applications (§9) | `applications/language-speech-multimodal`, `applications/vision`, `applications/flow-3d`, `applications/graphs-science`, `applications/embodied-other` |
| Outlook (§10) | `outlook/diffusion` |

Use an `applications/*` section as primary only when the main takeaway is a specific external domain; a design evaluated on language modeling is a `design/*` paper.

### `loop_topology` (one value)

Where the loop sits: `whole-stack` (the whole block stack repeats), `prelude-core-coda` (a middle core loops between distinct input and output layers), `partial` (only an early block or sub-module loops), `hierarchical` (coupled loops at different rates, e.g. HRM/TRM), `shifted-parallel` (loops pipelined across tokens or run in parallel branches), `implicit-fixed-point` (output solved as a fixed point), or `unspecified`.

### `sharing` (one value)

`full` (all looped parameters tied), `partial-adapter` (shared core plus per-iteration adapters, LoRA, or embeddings), `expert-routed` (per-iteration routing among experts or LoRAs), or `unspecified`.

### `depth_control` (one value)

`fixed`, `sampled-train` (loop count randomized or scheduled in training without a learned halting policy), `adaptive-halting` (learned or confidence-based stopping, depth routers), `convergence` (iterate to a fixed-point tolerance), or `unspecified`.

### `claims` (list)

What the paper argues looping buys or costs: `param-efficiency`, `compute-efficiency`, `memory-efficiency`, `data-efficiency`, `expressivity`, `length-generalization`, `test-time-scaling`, `stability`, `failure-mode`.

### `comparison` (list)

Only for papers that compare looped and non-looped (untied) models: which quantity is held fixed. `iso-param` (same unique parameters), `iso-flop` (same executed compute), `iso-depth` (K loops vs K untied layers), or `unclear` when the paper compares without stating the control. Use `[]` when there is no such comparison.

### `survey_core` (bool)

`true` for the survey's core set of roughly 30-50 anchor papers. It does not change repo inclusion; peer-review or citation thresholds of the survey do not apply to the catalog.

## Browser Behavior

The interactive browser exposes only these visible tag-filter groups:
- Loop Mechanism (`mechanism_tags`)
- `focus_tags`
- `domain_tags`

Alias-style `tags` are kept in metadata but are not shown as browser filter chips.

## Blogs Section

Blogs are intentionally separate from the paper taxonomy.

They live in one flat `Blogs` section and can carry `mechanism_tags`, `focus_tags`, `domain_tags`, and optional `tags`, but they do not use `category`, `category_path`, or `foundation`.

A blog belongs here only if it is a substantive public long-form technical post about loop models or closely related loop-model questions.

Good fits:
- technical deep-dives
- lab blog posts
- long-form essays
- tutorials with real technical content
- long X articles / Substack posts / personal blog posts with substantial analysis

Usually out of scope:
- short tweets or announcement-only posts
- marketing pages
- bare link roundups with little or no analysis
- generic news reposts
- project pages without meaningful technical writing

## Classification Procedure

When a paper is ambiguous, use this order:

1. First ask whether a shared learned internal layer, block, module, or operator is reused inside one model forward process.
2. If the paper's iteration is really repeated full-model calls, agent steps, recursive self-calls, external search/planning, or latent reasoning via multiple complete forwards, drop it.
3. If the paper is in scope, ask what readers should take away first.
   - analysis, theory, mechanism, probing, explanation -> `analysis`
   - architecture, algorithm, efficiency, memory compression, training/inference method -> `designs`
   - domain/task demonstration such as robotics, VLA, multimodal, tabular, or graph data -> `applications`
4. Then use `foundation`, Loop Mechanism (`mechanism_tags`), `focus_tags`, and `domain_tags` for the secondary story.
5. Fill the survey-aligned axes: `survey_section` (primary first), `loop_topology`, `sharing`, `depth_control`, `claims`, `comparison`, and `survey_core`.

## Tie-Break Rules

### Applications Focused vs Architecture and Algorithm Designs

- Use `designs` when the main reusable artifact is the architecture or algorithm.
- Use `applications` when the main reusable artifact is evidence about a concrete task/domain.
- If a paper introduces a named model variant and the paper is mostly selling that variant as a design, prefer `designs`.
- If a paper mainly uses loop models to demonstrate performance in robotics, VLA, multimodal, tabular, graph, or another external domain, prefer `applications`.

### Applications Focused vs Theoretical and Mechanical Analysis

- Use `analysis` when the main artifact is explanation or understanding.
- Use `applications` when the main artifact is task/domain behavior in use.
- If empirical evidence mainly exists to support a mechanism claim, use `analysis`.
- If analysis mainly exists to support a task/domain result, use `applications`.

### Architecture and Algorithm Designs vs Theoretical and Mechanical Analysis

- Use `designs` when the main artifact is a new architecture, algorithm, or efficiency method.
- Use `analysis` when the main artifact is understanding an existing loop mechanism.

## Legacy Metadata Policy

Legacy taxonomy shapes are no longer read or remapped by the build. New or edited `papers/*.yaml` entries must use only the strict flat schema:

- `category` must be exactly one of `analysis`, `designs`, or `applications`.
- use `foundation: true` for anchor papers instead of `category: foundation`.
- omit `category_path` and `subcategory`; nested category paths are rejected.
- put loop-form labels only in `mechanism_tags`, using one or more of `hierarchical-loop`, `flat-loop`, `parallel-loop`, or `implicit-layer`.
- keep paper acronyms, family names, and fine-grained mechanism words in `tags`, `domain_tags`, or prose; the build does not map them into `mechanism_tags`.

For non-paper long-form resources, use `blogs/*.yaml` instead. Blog entries stay flat and are not part of the paper taxonomy.
