
<div align="center">

# Awesome Loop Models

[![Awesome](https://awesome.re/badge.svg)](https://awesome.re)
[![Submit](https://img.shields.io/badge/📄%20Submit-blue?style=flat-square)](https://huskydoge.github.io/Awesome-Loop-Models/submit.html)
[![Website](https://img.shields.io/badge/🌐%20Live%20Website-Link-blue?style=flat-square)](https://huskydoge.github.io/Awesome-Loop-Models/index.html)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<img src="assets/cover.png" alt="Loop architecture concept diagram" width="100%" />

### 🌐 [**Interactive Browser**](https://huskydoge.github.io/Awesome-Loop-Models/index.html) · 🧾 [**PR Submission Guide**](https://huskydoge.github.io/Awesome-Loop-Models/submit.html)

*Search, filter, and explore loop-model papers and selected technical blogs with links to arXiv, code, OpenReview, and more.*

*Use the PR Submission Guide to generate YAML for papers or blogs, then copy the path and YAML into your fork / branch for the final pull request step.*

</div>

A curated list of papers and selected long-form technical blogs on **Loop Models** — architectures where, within a single forward process, a shared learned internal layer, block, module, or operator is reused.

---

## News

- **2026-04-24** — Awesome Loop Models is released. [Announcement](https://x.com/huskydogewoof/status/2047655947942744285)

---

## What Counts as a Loop Model?

This repository uses a strict definition:

> By "loop model," we mean that, within a single forward pass of a model, a shared learned internal layer, block, module, or operator is reused.

This repo therefore includes papers that focus on loop models themselves, their mechanisms, applications, and designs. It excludes papers that are primarily about broader-scale iteration patterns that do not directly connect to loop models as defined above, such as agent loops, repeated full-model calls, external solver rounds, energy-based models, or plain sequence-time recurrence.

> Admittedly, loop models are deeply connected to the broader field of architecture and algorithm design (Diffusion, Energy-Based Models, etc.). We also welcome work that explicitly connects adjacent topics to loop models.

<p align="center">
  <img src="assets/scope.png" alt="Scope scale from agent loop to loop models" width="100%" />
</p>

> Only the **rightmost end** of this scale is in scope for the main paper list.

## How the Repository Is Organized

The public browsing layer uses exactly three flat paper categories:
- **Theoretical and Mechanical Analysis** — analytical papers whose main reader takeaway is understanding: theory, mechanism analysis, probing, diagnostics, or formal properties
- **Architecture and Algorithm Designs** — papers that propose loop-model architectures or algorithms, often for better performance, efficiency, training, inference, or memory use
- **Applications Focused** — papers whose main reader takeaway is loop-model performance on concrete external domains or tasks, such as robotics, VLA, multimodal tasks, tabular data, or graph data

In addition, selected long-form technical posts live in a separate flat **Blogs** section. Blogs can carry tags, but they do not use the paper taxonomy.

> The paper categories are intentionally coarse. Foundation status plus Loop Mechanism / focus / domain tags carry secondary structure without introducing a separate lineage-tag axis.

Top-level categories do the minimum amount of work. Finer distinctions are pushed into:
- **Loop Mechanism** (`mechanism_tags`) — loop-form labels only: `hierarchical-loop`, `flat-loop`, `parallel-loop`, or `implicit-layer`
- `focus_tags` — whether the paper mainly studies `objective-loss`, `training-algorithm`, `architecture`, `data`, or `inference-algorithm`
- `domain_tags` — problem/domain labels such as `language-modeling`, `robotics-vla`, `multimodal`, `tabular-data`, or `graph-data`
- `tags` — optional aliases or model identifiers kept in YAML / README metadata, such as `DEQ`, `UT`, `ACT`, or `Ouro`

A paper can also carry `foundation: true` as a secondary badge when it is a canonical anchor such as ACT, Universal Transformers, or DEQ. Foundation is no longer a separate top-level shelf.

In the interactive browser, the visible tag filters are **Loop Mechanism**, `focus_tags`, and `domain_tags`. Alias-style `tags` are not shown as browser filter chips there.

See [TAGS.md](TAGS.md) for the current tag inventory and preferred spellings before proposing a new tag.

See [TAXONOMY.md](TAXONOMY.md) for the full inclusion rule, paper category definitions, tie-break rules, and the flat Blogs-section rule.

---

## Table of Contents

- [Theoretical and Mechanical Analysis](#theoretical-and-mechanical-analysis) (26)
- [Architecture and Algorithm Designs](#architecture-and-algorithm-designs) (67)
- [Applications Focused](#applications-focused) (16)
- [Blogs](#blogs) (7)

> The paper shelves are intentionally coarse: Theoretical and Mechanical Analysis, Architecture and Algorithm Designs, and Applications Focused. Foundation status plus Loop Mechanism / focus / domain tags carry secondary structure without introducing lineage buckets.
> Blogs are a separate flat section: they can carry tags, but they do not use the paper taxonomy.

---

<!-- AUTO-GENERATED by scripts/build.py on 2026-07-01 03:21 UTC — DO NOT EDIT the lists below manually. Edit papers/*.yaml or blogs/*.yaml and run `python3 scripts/build.py` instead. -->

## Theoretical and Mechanical Analysis

Theoretical and Mechanical Analysis collects papers whose primary contribution is analysis: why loop models work, what formal properties they have, and what mechanisms they exhibit.

- <details>
  <summary>[06/29/2026] <strong>Stabilizing Extrapolation in Looped Transformers via Learned Stochastic Stopping</strong> <a href="https://arxiv.org/abs/2606.29983"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2606.29983-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2606.29983"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2606.29983-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Hsun-Yu Kuo, El Mahdi Chayti, Patrik Reizinger, Wieland Brendel, Martin Jaggi · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> training-algorithm · inference-algorithm</div>
  <div><strong>Domains:</strong> algorithmic-reasoning · scaling · adaptive-compute</div>
  <div><strong>TL;DR:</strong> Studies looped Transformers that repeatedly apply a shared Transformer block, showing that stochastic training-time loop counts and learned stochastic stopping can reduce out-of-distribution variance across inference loop counts on algorithmic sequence tasks.</div>
  </details>

- <details>
  <summary>[06/18/2026] <strong>Recurrent neural networks approximate continuous functions</strong> <a href="https://arxiv.org/abs/2606.20325"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2606.20325-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2606.20325"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2606.20325-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Valentin Abadie, Clemens Hutter, Helmut Bölcskei · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> inference-algorithm</div>
  <div><strong>Domains:</strong> theory · algorithmic-reasoning</div>
  <div><strong>TL;DR:</strong> Proves that a single fixed-weight ReLU recurrent neural network with fixed hidden dimension can approximate any continuous function by running its shared recurrent dynamics longer, with runtime becoming the resource that improves accuracy.</div>
  </details>

- <details>
  <summary>[06/16/2026] <strong>On the Residual Scaling of Looped Transformers: Stability and Transferability</strong> <a href="https://arxiv.org/abs/2606.18524"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2606.18524-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2606.18524"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2606.18524-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Shaowen Wang, Bingrui Li, Ge Zhang, Wenhao Huang, Shen Yan, Jian Li · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · theory · scaling</div>
  <div><strong>TL;DR:</strong> Analyzes residual scaling in looped weight-tied Transformers, showing that correlated shared-block updates require stronger 1/N residual scaling across loop count and enable hyperparameter transfer from small to large recurrent depths.</div>
  </details>

- <details>
  <summary>[05/30/2026] <strong>Looped Transformers with Layer Normalization Provably Learn the Power Method</strong> <a href="https://arxiv.org/abs/2606.00605"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2606.00605-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2606.00605"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2606.00605-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Lyumin Wu, Chenyang Zhang, Yuan Cao · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm</div>
  <div><strong>Domains:</strong> theory · algorithmic-reasoning</div>
  <div><strong>TL;DR:</strong> Proves that a looped linear transformer with layer normalization, trained only for principal component prediction, converges to a solution implementing the power method, with each self-attention layer performing one power iteration.</div>
  </details>

- <details>
  <summary>[05/29/2026] <strong>Chain-of-Thought and Compressed Looped Transformers: A Memory-Budget Separation</strong> <a href="https://arxiv.org/abs/2605.30757"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2605.30757-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2605.30757"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2605.30757-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Haozhou Zhang · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning · theory · memory-efficiency</div>
  <div><strong>TL;DR:</strong> Compares chain-of-thought scratchpads with compressed looped Transformers, arguing that looped hidden-state recurrence is bounded by its persistent memory budget even when more recurrent computation is applied.</div>
  </details>

- <details>
  <summary>[05/26/2026] <strong>Stabilizing Recurrent Dynamics for Test-Time Scalable Latent Reasoning in Looped Language Models</strong> <a href="https://arxiv.org/abs/2605.26733"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2605.26733-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2605.26733"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2605.26733-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Xiao-Wen Yang, Ziyu Han, Xi-Hua Zhang, Wen-Da Wei, Jie-Jing Shao, Lan-Zhe Guo, Yu-Feng Li · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> training-algorithm · inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning · theory · scaling</div>
  <div><strong>TL;DR:</strong> Analyzes why Looped Language Models can collapse at larger recurrence depths and proposes STARS, a spectral-radius-regularized training framework that pushes latent dynamics toward stable fixed points for reliable test-time scaling.</div>
  </details>

- <details>
  <summary>[05/20/2026] <strong>Interaction Locality in Hierarchical Recursive Reasoning</strong> <a href="https://arxiv.org/abs/2605.20784"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2605.20784-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2605.20784"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2605.20784-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Yosuke Miyanishi, Tetsuro Morimura · 2026</div>
  <div><strong>Loop Mechanism:</strong> hierarchical-loop · flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> reasoning · algorithmic-reasoning</div>
  <div><strong>TL;DR:</strong> Proposes interaction locality as a mechanistic measurement framework for HRM and TRM, showing how repeated recursive updates accumulate local writes into broader solution structure on grid reasoning benchmarks.</div>
  </details>

- <details>
  <summary>[05/18/2026] <strong>One Model, Two Roles: Emergent Specialization in a Shared Recurrent Transformer</strong> <a href="https://arxiv.org/abs/2605.17811"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2605.17811-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2605.17811"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2605.17811-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Jucheng Shen, Barbara Su, Anastasios Kyrillidis · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop · hierarchical-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> reasoning · algorithmic-reasoning</div>
  <div><strong>TL;DR:</strong> Analyzes Asymmetric Input Recurrence, a two-state shared-weight recurrent Transformer where the same model updates L/H states, showing that state identity and input-injection asymmetry induce distinct proposal-vs-uncertainty roles on Sudoku-Extreme and Maze.</div>
  </details>

- <details>
  <summary>[05/08/2026] <strong>Bifurcation Models: Learning Set-Valued Solution Maps with Weight-Tied Dynamics</strong> <a href="https://arxiv.org/abs/2605.07277"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2605.07277-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2605.07277"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2605.07277-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Caleb Jore, Jialin Liu · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop · implicit-layer</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> theory · algorithmic-reasoning</div>
  <div><strong>TL;DR:</strong> Studies weight-tied dynamics for set-valued solution maps, proving that regular equilibrium dynamics can represent multiple branches while repeated shared-operator iterations discover multiple valid equilibria on Ising and Allen-Cahn tasks.</div>
  </details>

- <details>
  <summary>[05/07/2026] <strong>Is One Layer Enough? Understanding Inference Dynamics in Tabular Foundation Models</strong> <a href="https://arxiv.org/abs/2605.06510"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2605.06510-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2605.06510"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2605.06510-7c3aed.svg"></a> <a href="https://github.com/amirbalef/is_one_layer_enough/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/amirbalef/is_one_layer_enough?style=social"></a></summary>
  <div><strong>Authors:</strong> Amir Rezaei Balef, Mykhailo Koshil, Katharina Eggensperger · ICML 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> tabular-data · reasoning</div>
  <div><strong>TL;DR:</strong> Analyzes layerwise inference dynamics in tabular foundation models and uses the observed depth redundancy to build a looped single-layer model that preserves comparable performance with about 20% of the original parameters.</div>
  </details>

- <details>
  <summary>[05/07/2026] <strong>Transformers Efficiently Perform In-Context Logistic Regression via Normalized Gradient Descent</strong> <a href="https://arxiv.org/abs/2605.06609"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2605.06609-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2605.06609"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2605.06609-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Chenyang Zhang, Yuan Cao · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm · training-algorithm</div>
  <div><strong>Domains:</strong> theory · reasoning</div>
  <div><strong>TL;DR:</strong> Proves that softmax transformers can implement in-context logistic regression by treating layers as normalized-gradient-descent steps, then trains one self-attention layer and applies it recurrently as a looped model with convergence and OOD guarantees.</div>
  </details>

- <details>
  <summary>[04/28/2026] <strong>On Halting vs Converging in Recurrent Graph Neural Networks</strong> <a href="https://arxiv.org/abs/2604.25551"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2604.25551-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2604.25551"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2604.25551-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Jeroen Bollen, Stijn Vansummeren · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> theory · algorithmic-reasoning</div>
  <div><strong>TL;DR:</strong> Analyzes recurrent graph neural networks that repeatedly apply message passing until convergence or halting, proving expressiveness relationships between converging, output-converging, and halting RGNN variants.</div>
  </details>

- <details>
  <summary>[04/23/2026] <strong>Universal Transformers Need Memory: Depth-State Trade-offs in Adaptive Recursive Reasoning</strong> <a href="https://arxiv.org/abs/2604.21999"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2604.21999-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2604.21999"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2604.21999-7c3aed.svg"></a> <a href="https://github.com/che-shr-cat/utm-jax/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/che-shr-cat/utm-jax?style=social"></a></summary>
  <div><strong>Authors:</strong> Grigory Sapunov · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> reasoning · algorithmic-reasoning</div>
  <div><strong>TL;DR:</strong> Studies a single-block Universal Transformer with ACT on Sudoku-Extreme, showing that learned memory tokens are necessary for non-trivial recursive-depth reasoning and that ACT initialization can trap the model in shallow computation.</div>
  </details>

- <details>
  <summary>[04/22/2026] <strong>How Much Is One Recurrence Worth? Iso-Depth Scaling Laws for Looped Language Models</strong> <a href="https://arxiv.org/abs/2604.21106"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2604.21106-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2604.21106"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2604.21106-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Kristian Schwethelm, Daniel Rueckert, Georgios Kaissis · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture</div>
  <div><strong>Domains:</strong> language-modeling · scaling · efficiency</div>
  <div><strong>TL;DR:</strong> Measures the parameter value of recurrence in looped language models with iso-depth scaling laws, estimating how extra recurrent passes trade off against unique depth and training compute.</div>
  </details>

- <details>
  <summary>[04/16/2026] <strong>Stability and Generalization in Looped Transformers</strong> <a href="https://arxiv.org/abs/2604.15259"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2604.15259-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2604.15259"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2604.15259-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Asher Labovich · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop · implicit-layer</div>
  <div><strong>Focus:</strong> inference-algorithm</div>
  <div><strong>Domains:</strong> reasoning · theory</div>
  <div><strong>TL;DR:</strong> Analyzes stability and generalization in looped transformers through a fixed-point framework, characterizing when recall and normalization yield reachable, input-dependent, and trainable loop dynamics.</div>
  </details>

- <details>
  <summary>[04/15/2026] <strong>Hierarchical vs. Flat Iteration in Shared-Weight Transformers</strong> <a href="https://arxiv.org/abs/2604.14442"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2604.14442-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2604.14442"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2604.14442-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Sang-Il Han · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop · hierarchical-loop</div>
  <div><strong>Focus:</strong> architecture</div>
  <div><strong>Domains:</strong> language-modeling · scaling</div>
  <div><strong>TL;DR:</strong> Empirically compares hierarchical shared-weight recurrence against flat shared-weight iteration and independent-layer stacking, revealing a persistent representational gap for the recurrent hierarchy.</div>
  </details>

- <details>
  <summary>[04/13/2026] <strong>A Mechanistic Analysis of Looped Reasoning Language Models</strong> <a href="https://arxiv.org/abs/2604.11791"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2604.11791-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2604.11791"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2604.11791-7c3aed.svg"></a> <a href="https://x.com/HughBlayney/status/2046558050882899995?s=20"><img alt="Twitter" src="https://img.shields.io/badge/Twitter-%40HughBlayney-1d9bf0.svg"></a></summary>
  <div><strong>Authors:</strong> Hugh Blayney, Álvaro Arroyo, Johan Obando-Ceron, Pablo Samuel Castro, Aaron Courville, Michael M. Bronstein, Xiaowen Dong · 2026</div>
  <div><strong>Loop Mechanism:</strong> implicit-layer</div>
  <div><strong>Focus:</strong> inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning</div>
  <div><strong>TL;DR:</strong> Analyzes looped reasoning LLMs mechanistically, showing recurrent cycles converge to layer-specific fixed points and that feedforward-like inference stages repeat across latent recurrences.</div>
  </details>

- <details>
  <summary>[04/10/2026] <strong>Relational Preference Encoding in Looped Transformer Internal States</strong> <a href="https://arxiv.org/abs/2604.09870"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2604.09870-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2604.09870"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2604.09870-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Jan Kirin · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> training-algorithm · architecture</div>
  <div><strong>Domains:</strong> language-modeling · alignment</div>
  <div><strong>TL;DR:</strong> Probes looped transformer hidden states during iterative refinement, showing that human-preference information is encoded primarily in relational differences between loop states rather than independent per-state scores.</div>
  </details>

- <details>
  <summary>[04/09/2026] <strong>Loop, Think, &amp; Generalize: Implicit Reasoning in Recurrent-Depth Transformers</strong> <a href="https://arxiv.org/abs/2604.07822"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2604.07822-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2604.07822"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2604.07822-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Harsh Kohli, Srinivasan Parthasarathy, Huan Sun, Yuekun Yao · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop · implicit-layer</div>
  <div><strong>Focus:</strong> inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning</div>
  <div><strong>TL;DR:</strong> Studies implicit reasoning in recurrent-depth transformers, showing that iterating shared transformer layers can unlock systematic generalization and depth extrapolation while also exposing overthinking limits.</div>
  </details>

- <details>
  <summary>[02/05/2026] <strong>Inverse Depth Scaling From Most Layers Being Similar</strong> <a href="https://arxiv.org/abs/2602.05970"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2602.05970-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2602.05970"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2602.05970-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Yizhou Liu, Sara Kangaslahti, Ziming Liu, Jeff Gore · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture</div>
  <div><strong>Domains:</strong> language-modeling · theory</div>
  <div><strong>Community Comments:</strong> <a href="https://x.com/huskydogewoof/status/2034158020322574556?s=20">X Comment</a></div>
  <div><strong>TL;DR:</strong> Analyzes LLMs and toy residual networks to show loss scales inversely with depth when many layers are functionally similar and primarily reduce error via ensemble averaging.</div>
  </details>

- <details>
  <summary>[09/27/2025] <strong>Two-Scale Latent Dynamics for Recurrent-Depth Transformers</strong> <a href="https://arxiv.org/abs/2509.23314"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2509.23314-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2509.23314"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2509.23314-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Francesco Pappone, Donato Crisostomi, Emanuele Rodolà · 2025</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning</div>
  <div><strong>TL;DR:</strong> Analyzes recurrent-depth transformers through a two-scale latent-dynamics lens, showing shrinking and increasingly orthogonal loop updates and deriving a second-order early-exit criterion that improves latency-quality trade-offs.</div>
  </details>

- <details>
  <summary>[07/02/2025] <strong>Latent Chain-of-Thought? Decoding the Depth-Recurrent Transformer</strong> <a href="https://arxiv.org/abs/2507.02199"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2507.02199-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2507.02199"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2507.02199-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Wenquan Lu, Yuechuan Yang, Kyle Lee, Yanshu Li, Enqi Liu · 2025</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning</div>
  <div><strong>TL;DR:</strong> Probes a depth-recurrent Transformer to test whether latent chain-of-thought structure emerges across recurrence steps, finding limited evidence and recurrence-depth-dependent interpretability effects.</div>
  </details>

- <details>
  <summary>[02/24/2025] <strong>Reasoning with Latent Thoughts: On the Power of Looped Transformers</strong> <a href="https://arxiv.org/abs/2502.17416"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2502.17416-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2502.17416"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2502.17416-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Nikunj Saunshi, Nishanth Dikkala, Zhiyuan Li, Sanjiv Kumar, Sashank J. Reddi · ICLR 2025</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> training-algorithm · inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning</div>
  <div><strong>Community Comments:</strong> <a href="https://x.com/reza_byt/status/2045168844658950392?s=20">Reza Bayat reading list (#7)</a></div>
  <div><strong>TL;DR:</strong> Studies looped transformers as reasoning models, showing effective-depth scaling, latent-thought simulation of chain-of-thought, and a looping-based regularizer that improves the reasoning-versus-memorization trade-off.</div>
  </details>

- <details>
  <summary>[10/02/2024] <strong>On Expressive Power of Looped Transformers: Theoretical Analysis and Enhancement via Timestep Encoding</strong> <a href="https://arxiv.org/abs/2410.01405"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2410.01405-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2410.01405"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2410.01405-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Kevin Xu, Issei Sato · 2024</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture</div>
  <div><strong>Domains:</strong> language-modeling · reasoning · theory</div>
  <div><strong>TL;DR:</strong> Analyzes the expressive power of looped transformers, derives approximation-rate limits, and shows that timestep encoding improves their function-approximation behavior.</div>
  </details>

- <details>
  <summary>[11/21/2023] <strong>Looped Transformers are Better at Learning Learning Algorithms</strong> <a href="https://arxiv.org/abs/2311.12424"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2311.12424-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2311.12424"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2311.12424-7c3aed.svg"></a> <a href="https://github.com/Leiay/looped_transformer/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/Leiay/looped_transformer?style=social"></a> <a href="https://openreview.net/forum?id=HHbRxoDTxE"><img alt="OpenReview" src="https://img.shields.io/badge/OpenReview-Paper-8E44AD.svg"></a></summary>
  <div><strong>Authors:</strong> Liu Yang, Kangwook Lee, Robert Nowak, Dimitris Papailiopoulos · ICLR 2024</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm</div>
  <div><strong>Domains:</strong> algorithmic-reasoning</div>
  <div><strong>Community Comments:</strong> <a href="https://x.com/huskydogewoof/status/2033023167044727049?s=20">Benhao&#x27;s reading note</a> <a href="https://x.com/reza_byt/status/2045168844658950392?s=20">Reza Bayat reading list (#5)</a></div>
  <div><strong>TL;DR:</strong> Proposes looped-transformer training for in-context data-fitting tasks, showing comparable performance to standard transformers with under 10% of the parameters by better matching iterative learning algorithms.</div>
  </details>

- <details>
  <summary>[01/30/2023] <strong>Looped Transformers as Programmable Computers</strong> <a href="https://arxiv.org/abs/2301.13196"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2301.13196-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2301.13196"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2301.13196-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Angeliki Giannou, Shashank Rajput, Jy-yong Sohn, Kangwook Lee, Jason D. Lee, Dimitris Papailiopoulos · 2023</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> algorithmic-reasoning</div>
  <div><strong>Community Comments:</strong> <a href="https://x.com/reza_byt/status/2045168844658950392?s=20">Reza Bayat reading list (#4)</a></div>
  <div><strong>TL;DR:</strong> Shows that a shallow looped transformer can emulate instruction-set computation and iterative algorithms such as SGD or matrix inversion, with the recurrence acting as a reusable program counter.</div>
  </details>

---

## Architecture and Algorithm Designs

Architecture and Algorithm Designs collects the constructive side of the field: new looped architectures, algorithms, recurrent computation graphs, and efficiency or memory-compression methods.

- <details>
  <summary>[06/30/2026] <strong>Bridging the Gap Between Latent and Explicit Reasoning with Looped Transformers</strong> <a href="https://arxiv.org/abs/2606.31779"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2606.31779-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2606.31779"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2606.31779-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Ying Fan, Anej Svete, Kangwook Lee · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop · parallel-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning · efficiency · scaling</div>
  <div><strong>TL;DR:</strong> Introduces LOTUS, a looped padded Transformer that reuses recurrent-depth weights for parallel latent chain-of-thought blocks, matching explicit CoT at 3B scale while reducing thought-phase latency.</div>
  </details>

- <details>
  <summary>[06/30/2026] <strong>CHERRY: Compressed Hierarchical Experts with Recurrent Representational Yield</strong> <a href="https://arxiv.org/abs/2606.31796"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2606.31796-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2606.31796"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2606.31796-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Dohyeon Kwon, Youngjin Park · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · efficiency · scaling · MoE</div>
  <div><strong>TL;DR:</strong> Compresses a 48-layer language Transformer to 6 layers and restores depth through learned recurrent unrolling, then combines compressed recurrent models as efficient experts.</div>
  </details>

- <details>
  <summary>[06/16/2026] <strong>Fixed-Point Reasoners: Stable and Adaptive Deep Looped Transformers</strong> <a href="https://arxiv.org/abs/2606.18206"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2606.18206-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2606.18206"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2606.18206-7c3aed.svg"></a> <a href="https://github.com/nilskiKonjIzDunava/fprm/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/nilskiKonjIzDunava/fprm?style=social"></a></summary>
  <div><strong>Authors:</strong> Sajad Movahedi, Vera Milovanović, Shlomo Libo Feigin, Alexander Theus, Thomas Hofmann, Valentina Boeva, T. Konstantin Rusch, Antonio Orvieto · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop · implicit-layer</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> reasoning · algorithmic-reasoning · adaptive-compute</div>
  <div><strong>TL;DR:</strong> Introduces FPRM, a Transformer-based Fixed-Point Reasoning Model that repeatedly applies a looped reasoning block and uses fixed-point convergence as an end-to-end halting signal, adapting test-time compute to task difficulty on Sudoku, Maze, state-tracking, and ARC-AGI benchmarks.</div>
  </details>

- <details>
  <summary>[06/16/2026] <strong>LoopCoder-v2: Only Loop Once for Efficient Test-Time Computation Scaling</strong> <a href="https://arxiv.org/abs/2606.18023"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2606.18023-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2606.18023"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2606.18023-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Jian Yang, Shawn Guo, Wei Zhang, Tianyu Zheng, Yaxin Du, Haau-Sing Li, Jiajun Wu, Yue Song, Yan Xing, Qingsong Cai, Zelong Huang, Chuan Hao, Ran Tao, Xianglong Liu, Wayne Xin Zhao, Mingjie Tang, Weifeng Lv, Ming Zhou, Bryan Dai · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop · parallel-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning · efficiency · memory-efficiency</div>
  <div><strong>TL;DR:</strong> Studies loop-count selection in Parallel Loop Transformers by training LoopCoder-v2 coder models with shared looped blocks, finding that two loops give the main productive refinement while additional loops regress under cross-loop positional mismatch.</div>
  </details>

- <details>
  <summary>[06/04/2026] <strong>Skip a Layer or Loop It? Learning Program-of-Layers in LLMs</strong> <a href="https://arxiv.org/abs/2606.06574"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2606.06574-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2606.06574"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2606.06574-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Ziyue Li, Yang Li, Tianyi Zhou · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning · efficiency · scaling</div>
  <div><strong>TL;DR:</strong> Learns input-specific programs over pretrained LLM layers, allowing layers to be skipped or repeated so inference can use shorter or looped execution paths than the fixed-depth baseline.</div>
  </details>

- <details>
  <summary>[06/03/2026] <strong>LoopMoE: Unifying Iterative Computation with Mixture-of-Experts for Language Modeling</strong> <a href="https://arxiv.org/abs/2606.04438"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2606.04438-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2606.04438"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2606.04438-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Wenkai Chen, Tianshu Li, Wenyong Huang, Yichun Yin, Lifeng Shang, Chengwei Qin · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · efficiency · scaling</div>
  <div><strong>TL;DR:</strong> Introduces LoopMoE, a looped mixture-of-experts language model that combines sparse routing with iterative weight-shared computation through iteration-conditioned modulation and capacity balancing.</div>
  </details>

- <details>
  <summary>[06/02/2026] <strong>When to Re-Plan: Subgoal Persistence in Hierarchical Latent Reasoning</strong> <a href="https://arxiv.org/abs/2606.03741"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2606.03741-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2606.03741"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2606.03741-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Ayushi Chadha · 2026</div>
  <div><strong>Loop Mechanism:</strong> hierarchical-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm</div>
  <div><strong>Domains:</strong> reasoning · algorithmic-reasoning</div>
  <div><strong>TL;DR:</strong> Extends hierarchical latent reasoning with a slow manager module whose directional subgoal persists across several low-level hidden-state update steps, making subgoal duration a central design knob.</div>
  </details>

- <details>
  <summary>[05/31/2026] <strong>CART: Context-Anchored Recurrent Transformer -- A Parameter-Efficient Architecture with Learned Stability</strong> <a href="https://arxiv.org/abs/2606.01495"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2606.01495-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2606.01495"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2606.01495-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Chad A. Capps · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · efficiency · scaling</div>
  <div><strong>TL;DR:</strong> Introduces a compact language model that reuses a single shared transformer core across depth while anchoring recurrence to precomputed key-value tensors and reports a mostly negative parameter-parity result against dense baselines.</div>
  </details>

- <details>
  <summary>[05/29/2026] <strong>Fixed-Point Masked Generative Modeling</strong> <a href="https://arxiv.org/abs/2605.31215"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2605.31215-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2605.31215"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2605.31215-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Andrea Miele, Yiming Qin, Alba Carballo-Castro, Justin Deschenaux, Pascal Frossard · 2026</div>
  <div><strong>Loop Mechanism:</strong> implicit-layer</div>
  <div><strong>Focus:</strong> architecture · training-algorithm · inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · vision · efficiency</div>
  <div><strong>TL;DR:</strong> Replaces part of a masked generative model denoiser with a fixed-point solver over shared attention layers, using consistency training and solver-state reuse to adapt depth with fewer parameters.</div>
  </details>

- <details>
  <summary>[05/27/2026] <strong>CosmicFish-HRM: Adaptive Reasoning via Hierarchical Recurrent Mechanisms in Compact Language Models</strong> <a href="https://arxiv.org/abs/2605.28919"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2605.28919-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2605.28919"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2605.28919-7c3aed.svg"></a> <a href="https://github.com/MistyozAI/CosmicFish-HRM/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/MistyozAI/CosmicFish-HRM?style=social"></a></summary>
  <div><strong>Authors:</strong> Venkat Akhil Lakkapragada · 2026</div>
  <div><strong>Loop Mechanism:</strong> hierarchical-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning · efficiency</div>
  <div><strong>TL;DR:</strong> Explores a compact autoregressive language model with a Hierarchical Reasoning Module that iterates through high-level and low-level reasoning cycles and learns input-dependent halting behavior for adaptive reasoning depth.</div>
  </details>

- <details>
  <summary>[05/25/2026] <strong>Looped Diffusion Language Models</strong> <a href="https://arxiv.org/abs/2605.26106"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2605.26106-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2605.26106"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2605.26106-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Sanghyun Lee, Chunsan Hong, Seungryong Kim, Jonghyun Lee, Jongho Park, Dongmin Park · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm · inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning · efficiency · scaling</div>
  <div><strong>TL;DR:</strong> Introduces LoopMDM, selectively looping early-middle transformer layers in masked diffusion language models so training gains depth-scaling without extra parameters and inference can vary loop count for compute scaling.</div>
  </details>

- <details>
  <summary>[05/22/2026] <strong>Training-Free Looped Transformers</strong> <a href="https://arxiv.org/abs/2605.23872"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2605.23872-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2605.23872"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2605.23872-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Lizhang Chen, Jonathan Li, Chen Liang, Ni Lao, Qiang Liu · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning · efficiency · scaling</div>
  <div><strong>TL;DR:</strong> Retrofits frozen pretrained transformers with a training-free inference wrapper that repeatedly applies a contiguous mid-stack layer block as damped refinement sub-steps, improving several QA and reasoning benchmarks without fine-tuning.</div>
  </details>

- <details>
  <summary>[05/20/2026] <strong>Equilibrium Reasoners: Learning Attractors Enables Scalable Reasoning</strong> <a href="https://arxiv.org/abs/2605.21488"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2605.21488-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2605.21488"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2605.21488-7c3aed.svg"></a> <a href="https://github.com/locuslab/eqr/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/locuslab/eqr?style=social"></a></summary>
  <div><strong>Authors:</strong> Benhao Huang, Zhengyang Geng, Zico Kolter · ICML 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop · implicit-layer</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> reasoning · algorithmic-reasoning · scaling</div>
  <div><strong>Community Comments:</strong> <a href="https://x.com/huskydogewoof/status/2057641657580064941?s=20">Benhao&#x27;s announcement thread</a></div>
  <div><strong>TL;DR:</strong> Formalizes Equilibrium Reasoners as learned latent dynamical systems whose repeated update rule converges toward task-conditioned attractors, enabling depth and breadth test-time scaling for reasoning.</div>
  </details>

- <details>
  <summary>[05/20/2026] <strong>LT2: Linear-Time Looped Transformers</strong> <a href="https://arxiv.org/abs/2605.20670"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2605.20670-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2605.20670"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2605.20670-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Chunyuan Deng, Yizhe Zhang, Rui-Jie Zhu, Yuanyuan Xu, Jiarui Liu, T. S. Eugene Ng, Hanjie Chen · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning · efficiency · scaling</div>
  <div><strong>TL;DR:</strong> Introduces LT2, a looped-transformer family that replaces quadratic attention with linear or sparse attention so repeated loop steps refine memory and expand receptive field while keeping inference more scalable.</div>
  </details>

- <details>
  <summary>[05/19/2026] <strong>Generative Recursive Reasoning</strong> <a href="https://arxiv.org/abs/2605.19376"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2605.19376-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2605.19376"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2605.19376-7c3aed.svg"></a> <a href="https://ahn-ml.github.io/gram-website/"><img alt="Website" src="https://img.shields.io/badge/Website-Link-blue"></a></summary>
  <div><strong>Authors:</strong> Junyeob Baek, Mingyu Jo, Minsu Kim, Mengye Ren, Yoshua Bengio, Sungjin Ahn · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop · parallel-loop</div>
  <div><strong>Focus:</strong> architecture · objective-loss · training-algorithm · inference-algorithm</div>
  <div><strong>Domains:</strong> reasoning · algorithmic-reasoning</div>
  <div><strong>TL;DR:</strong> Introduces GRAM, a probabilistic recursive-reasoning framework that models reasoning as stochastic latent trajectories, enabling multi-hypothesis computation, variational training, and inference-time scaling through depth and parallel sampling.</div>
  </details>

- <details>
  <summary>[05/19/2026] <strong>Probabilistic Tiny Recursive Model</strong> <a href="https://arxiv.org/abs/2605.19943"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2605.19943-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2605.19943"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2605.19943-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Amin Sghaier, Ali Parviz, Alexia Jolicoeur-Martineau · 2026</div>
  <div><strong>Loop Mechanism:</strong> hierarchical-loop · flat-loop · parallel-loop</div>
  <div><strong>Focus:</strong> inference-algorithm</div>
  <div><strong>Domains:</strong> reasoning · algorithmic-reasoning · efficiency</div>
  <div><strong>TL;DR:</strong> Introduces PTRM, an inference-time scaling framework for Tiny Recursive Models that injects Gaussian noise into recursive latent updates, runs parallel trajectories, and selects the final answer with the model&#x27;s Q head without retraining.</div>
  </details>

- <details>
  <summary>[05/18/2026] <strong>HRM-Text: Efficient Pretraining Beyond Scaling</strong> <a href="https://sapientinc.github.io/HRM-Text/assets/HRM_Text.pdf"><img alt="Paper" src="https://img.shields.io/badge/Paper-sapientinc.github.io-0366d6.svg"></a> <a href="https://github.com/sapientinc/HRM-Text/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/sapientinc/HRM-Text?style=social"></a> <a href="https://huggingface.co/sapientinc/HRM-Text-1B"><img alt="HuggingFace" src="https://img.shields.io/badge/HuggingFace-sapientinc%2FHRM--Text--1B-ffb000.svg"></a> <a href="https://sapientinc.github.io/HRM-Text/"><img alt="Website" src="https://img.shields.io/badge/Website-Link-blue"></a></summary>
  <div><strong>Authors:</strong> Guan Wang, Changling Liu, Chenyu Wang, Cai Zhou, Yuhao Sun, Yifei Wu, Shuai Zhen, Luca Scimeca, Yasin Abbasi Yadkori · Preprint 2026</div>
  <div><strong>Loop Mechanism:</strong> hierarchical-loop · flat-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm · objective-loss · data</div>
  <div><strong>Domains:</strong> language-modeling · reasoning · efficiency</div>
  <div><strong>TL;DR:</strong> Introduces HRM-Text, a 1B Hierarchical Recurrent Model language model that combines dual-timescale recurrent Transformer modules with MagicNorm, warmup deep credit assignment, PrefixLM masking, and task-completion pretraining for efficient training from 40B unique tokens.</div>
  </details>

- <details>
  <summary>[05/15/2026] <strong>Looped SSMs: Depth-Recurrence and Input Reshaping for Time Series Classification</strong> <a href="https://arxiv.org/abs/2605.16048"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2605.16048-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2605.16048"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2605.16048-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Mónika Farsang, Ramin Hasani, Daniela Rus, Radu Grosu · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> sequence-modeling · efficiency · scaling</div>
  <div><strong>TL;DR:</strong> Extends looped-transformer depth recurrence to state-space models by reusing the same SSM block across depth and adding input reshaping, showing tied-depth SSMs match or beat untied SSMs on six time-series benchmarks despite fewer parameters.</div>
  </details>

- <details>
  <summary>[05/12/2026] <strong>Solve the Loop: Attractor Models for Language and Reasoning</strong> <a href="https://arxiv.org/abs/2605.12466"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2605.12466-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2605.12466"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2605.12466-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Jacob Fein-Ashley, Paria Rashidinejad · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop · implicit-layer</div>
  <div><strong>Focus:</strong> architecture · training-algorithm · inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning · scaling · efficiency</div>
  <div><strong>TL;DR:</strong> Introduces Attractor Models, where a backbone proposes output embeddings and an attractor module iteratively solves a fixed point with implicit differentiation, improving looped language modeling and small-model reasoning while allowing adaptive convergence-depth inference.</div>
  </details>

- <details>
  <summary>[05/11/2026] <strong>Simply Stabilizing the Loop via Fully Looped Transformer</strong> <a href="https://arxiv.org/abs/2605.18797"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2605.18797-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2605.18797"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2605.18797-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Rao Fu, Zixuan Yang, Jiankun Zhang, Jing Ma, Hechang Chen, Yu Li, Yi Chang · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm · inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning · scaling · efficiency</div>
  <div><strong>TL;DR:</strong> Stabilizes looped transformers with parameter-free fully looped signal routing and attention injection, enabling stable training at higher loop counts while preserving test-time loop-depth control.</div>
  </details>

- <details>
  <summary>[05/10/2026] <strong>LoopUS: Recasting Pretrained LLMs into Looped Latent Refinement Models</strong> <a href="https://arxiv.org/abs/2605.11011"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2605.11011-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2605.11011"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2605.11011-7c3aed.svg"></a> <a href="https://thrillcrazyer.github.io/LoopUS"><img alt="Website" src="https://img.shields.io/badge/Website-Link-blue"></a></summary>
  <div><strong>Authors:</strong> Taekhyun Park, Yongjae Lee, Dohee Kim, Hyerim Bae · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm · inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning · efficiency · scaling</div>
  <div><strong>TL;DR:</strong> Converts pretrained LLMs into encoder, looped reasoning block, and decoder components, using selective gating, random deep supervision, and adaptive early exiting to stabilize latent looping without training recurrent models from scratch.</div>
  </details>

- <details>
  <summary>[05/09/2026] <strong>Quantum Injection Pathways for Implicit Graph Neural Networks</strong> <a href="https://arxiv.org/abs/2605.09226"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2605.09226-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2605.09226"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2605.09226-7c3aed.svg"></a> <a href="https://github.com/cxMoonGlade/QIP_IGNN/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/cxMoonGlade/QIP_IGNN?style=social"></a></summary>
  <div><strong>Authors:</strong> Pengyuan Xu, Tristan Zaborniak, Luis F. Rivera, Hausi A. Müller · 2026</div>
  <div><strong>Loop Mechanism:</strong> implicit-layer</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> theory · efficiency</div>
  <div><strong>TL;DR:</strong> Formulates quantum-signal injection pathways for graph deep-equilibrium models, comparing fixed, state-dependent, and backbone-dependent coupling inside the fixed-point operator with contraction guarantees and graph-classification experiments.</div>
  </details>

- <details>
  <summary>[05/09/2026] <strong>Sparse Layers are Critical to Scaling Looped Language Models</strong> <a href="https://arxiv.org/abs/2605.09165"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2605.09165-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2605.09165"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2605.09165-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Ryan Lee, Jacob Biloki, Edward J. Hu, Jonathan May · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · scaling · efficiency · MoE</div>
  <div><strong>TL;DR:</strong> Shows that MoE-style sparse layers can make looped language models scale better than dense looped transformers, with routing divergence across repeated shared layers recovering expressivity and loop boundaries serving as effective early-exit points.</div>
  </details>

- <details>
  <summary>[05/08/2026] <strong>Memory-Efficient Looped Transformer: Decoupling Compute from Memory in Looped Language Models</strong> <a href="https://arxiv.org/abs/2605.07721"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2605.07721-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2605.07721"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2605.07721-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Victor Conchello Vendrell, Arnau Padres Masdemont, Niccolò Grillo, Jordi Ros-Giralt, Arash Behboodi, Fabio Valerio Massoli · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning · efficiency · memory-efficiency</div>
  <div><strong>TL;DR:</strong> Memory-Efficient Looped Transformer enables constant‑memory iterative reasoning by sharing a single KV cache across loops, achieving strong performance without the linear memory scaling of prior looped LLMs.</div>
  </details>

- <details>
  <summary>[04/23/2026] <strong>Hyperloop Transformers</strong> <a href="https://arxiv.org/abs/2604.21254"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2604.21254-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2604.21254"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2604.21254-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Abbas Zeitoun, Lucas Torroba-Hennigen, Yoon Kim · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture</div>
  <div><strong>Domains:</strong> language-modeling · efficiency · memory-efficiency</div>
  <div><strong>Community Comments:</strong> <a href="https://x.com/TheTuringPost/status/2047720038342476187?s=20">Turing Posts</a></div>
  <div><strong>TL;DR:</strong> Introduces Hyperloop Transformers, a parameter-efficient looped Transformer that applies only a middle block recurrently and adds hyper-connections between loops to improve memory-efficient language modeling.</div>
  </details>

- <details>
  <summary>[04/20/2026] <strong>One Step Forward and K Steps Back: Better Reasoning with Denoising Recursion Models</strong> <a href="https://arxiv.org/abs/2604.18839"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2604.18839-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2604.18839"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2604.18839-7c3aed.svg"></a> <a href="https://github.com/wwwwwwwwz/DenoisingRecursionModels/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/wwwwwwwwz/DenoisingRecursionModels?style=social"></a></summary>
  <div><strong>Authors:</strong> Chris Cameron, Wangzheng Wang, Nikita Ivanov, Ashmita Bhattacharyya, Didier Chételat, Yingxue Zhang · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> training-algorithm · inference-algorithm · architecture</div>
  <div><strong>Domains:</strong> reasoning · algorithmic-reasoning</div>
  <div><strong>TL;DR:</strong> Introduces Denoising Recursion Models, a looped-transformer training method that corrupts targets and trains recursive refinement over multiple steps, improving ARC-AGI reasoning over TRM.</div>
  </details>

- <details>
  <summary>[04/19/2026] <strong>LASER: Low-Rank Activation SVD for Efficient Recursion</strong> <a href="https://arxiv.org/abs/2604.17224"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2604.17224-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2604.17224"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2604.17224-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Ege Çakar, Ketan Ali Raghu, Lia Zheng · 2026</div>
  <div><strong>Loop Mechanism:</strong> hierarchical-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> efficiency</div>
  <div><strong>TL;DR:</strong> Analyzes Tiny Recursive Model activation geometry during recursive unrolling and introduces LASER, a dynamic low-rank activation compression method that cuts recursive activation memory by ~60% without statistically significant accuracy loss.</div>
  </details>

- <details>
  <summary>[04/14/2026] 🌟 <strong>Parcae: Scaling Laws For Stable Looped Language Models</strong> <a href="https://arxiv.org/abs/2604.12946"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2604.12946-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2604.12946"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2604.12946-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Hayden Prairie, Zachary Novack, Taylor Berg-Kirkpatrick, Daniel Y. Fu · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> objective-loss · architecture</div>
  <div><strong>Domains:</strong> language-modeling · reasoning</div>
  <div><strong>Community Comments:</strong> <a href="https://x.com/huskydogewoof/status/2044609402553115070?s=20">Benhao&#x27;s reading note</a></div>
  <div><strong>TL;DR:</strong> Introduces Parcae, a stable looped language model that constrains injection spectral norms to prevent instability and studies isoFLOPs-style training- and test-time scaling laws for quality gains under fixed-parameter budgets.</div>
  </details>

- <details>
  <summary>[04/10/2026] <strong>ELT: Elastic Looped Transformers for Visual Generation</strong> <a href="https://arxiv.org/abs/2604.09168"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2604.09168-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2604.09168"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2604.09168-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Sahil Goyal, Swayam Agrawal, Gautham Govind Anil, Prateek Jain, Sujoy Paul, Aditya Kusupati · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm · inference-algorithm</div>
  <div><strong>Domains:</strong> vision · efficiency</div>
  <div><strong>Community Comments:</strong> <a href="https://x.com/che_shr_cat/status/2050923533199376595?s=20">Tweet by Grigory Sapunov</a> <a href="https://arxiviq.substack.com/p/elt-elastic-looped-transformers-for">Grigory Sapunov&#x27;s reading notes</a></div>
  <div><strong>TL;DR:</strong> Introduces Elastic Looped Transformers for image and video generation, using weight-shared recurrent transformer blocks plus Intra-Loop Self Distillation to support any-time inference with dynamic quality-compute trade-offs from a single training run.</div>
  </details>

- <details>
  <summary>[03/23/2026] <strong>Thinking Deeper, Not Longer: Depth-Recurrent Transformers for Compositional Generalization</strong> <a href="https://arxiv.org/abs/2603.21676"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2603.21676-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2603.21676"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2603.21676-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Hung-Hsuan Chen · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> reasoning · compositional-reasoning</div>
  <div><strong>TL;DR:</strong> Introduces a depth-recurrent Transformer for compositional generalization, with silent thinking, LayerScale, and identity-biased recurrence enabling stable deep latent iteration.</div>
  </details>

- <details>
  <summary>[03/20/2026] <strong>LoopRPT: Reinforcement Pre-Training for Looped Language Models</strong> <a href="https://arxiv.org/abs/2603.19714"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2603.19714-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2603.19714"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2603.19714-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Guo Tang, Shixin Jiang, Heng Chang, Nuo Chen, Yuhan Li, Huiming Fan, Jia Li, Ming Liu, Bing Qin · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> objective-loss · training-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning · RL</div>
  <div><strong>TL;DR:</strong> Proposes LoopRPT, a reinforcement pre-training method for looped language models that assigns learning signals to latent iterations, improving accuracy-compute trade-offs and strengthening early-stage reasoning on Ouro.</div>
  </details>

- <details>
  <summary>[03/09/2026] <strong>Adaptive Loops and Memory in Transformers: Think Harder or Know More?</strong> <a href="https://arxiv.org/abs/2603.08391"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2603.08391-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2603.08391"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2603.08391-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Markus Frey, Behzad Shomali, Ali Hamza Bashir, David Berghaus, Joachim Koehler, Mehdi Ali · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture</div>
  <div><strong>Domains:</strong> language-modeling · reasoning · efficiency</div>
  <div><strong>TL;DR:</strong> Introduces transformers with adaptive per-layer looping and gated memory banks, showing that combining learned halting with extra storage improves reasoning under matched parameter and FLOP budgets.</div>
  </details>

- <details>
  <summary>[03/09/2026] <strong>Tiny Autoregressive Recursive Models</strong> <a href="https://arxiv.org/abs/2603.08082"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2603.08082-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2603.08082"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2603.08082-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Paulius Rauba, Claudio Fanconi, Mihaela van der Schaar · 2026</div>
  <div><strong>Loop Mechanism:</strong> hierarchical-loop · flat-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm · inference-algorithm</div>
  <div><strong>Domains:</strong> algorithmic-reasoning · language-modeling</div>
  <div><strong>Community Comments:</strong> <a href="https://x.com/huskydogewoof/status/2032232642947494107?s=20">Benhao&#x27;s reading note</a></div>
  <div><strong>TL;DR:</strong> Studies autoregressive Tiny Recursive Models under compute-matched baselines, finding that simple two-step refinement helps on small algorithmic tasks while the full Autoregressive TRM shows no reliable gains.</div>
  </details>

- <details>
  <summary>[03/05/2026] <strong>Mixture of Universal Experts: Scaling Virtual Width via Depth-Width Transformation</strong> <a href="https://arxiv.org/abs/2603.04971"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2603.04971-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2603.04971"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2603.04971-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Yilong Chen, Naibin Gu, Junyuan Shang, Zhenyu Zhang, Yuchen Feng, Jiawei Sheng, Tingwen Liu, Shuohuan Wang, Yu Sun, Hua Wu, Haifeng Wang · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> objective-loss · architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · efficiency · MoE</div>
  <div><strong>Community Comments:</strong> <a href="https://x.com/huskydogewoof/status/2031847931993608673?s=20">Benhao&#x27;s reading note</a></div>
  <div><strong>TL;DR:</strong> Proposes MOUE, which reuses a universal layer-agnostic expert pool across layers to transform depth into virtual width and improve MoE performance under fixed activation budgets.</div>
  </details>

- <details>
  <summary>[03/05/2026] <strong>Recursive Inference Machines for Neural Reasoning</strong> <a href="https://arxiv.org/abs/2603.05234"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2603.05234-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2603.05234"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2603.05234-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Mieszko Komisarczyk, Saurabh Mathur, Maurice Kraus, Sriraam Natarajan, Kristian Kersting · 2026</div>
  <div><strong>Loop Mechanism:</strong> hierarchical-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> reasoning · RL</div>
  <div><strong>Community Comments:</strong> <a href="https://x.com/huskydogewoof/status/2033283214664515642?s=20">Benhao&#x27;s reading note</a></div>
  <div><strong>TL;DR:</strong> Introduces Recursive Inference Machines, a recurrent reasoning framework that casts TRMs as a special case and improves ARC-AGI, Sudoku, and tabular classification by reweighting the history of loop states.</div>
  </details>

- <details>
  <summary>[03/02/2026] <strong>AdaPonderLM: Gated Pondering Language Models with Token-Wise Adaptive Depth</strong> <a href="https://arxiv.org/abs/2603.01914"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2603.01914-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2603.01914"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2603.01914-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Shixiang Song, He Li, Zitong Wang, Boyi Zeng, Feichen Song, Yixuan Wang, Zhiqin John Xu, Ziwei He, Zhouhan Lin · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm · inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning · efficiency</div>
  <div><strong>TL;DR:</strong> Introduces AdaPonderLM, a self-supervised recurrent language model with token-wise halting gates and KV reuse, allocating more loop steps to hard tokens under a fixed compute budget.</div>
  </details>

- <details>
  <summary>[02/12/2026] <strong>SpiralFormer: Looped Transformers Can Learn Hierarchical Dependencies via Multi-Resolution Recursion</strong> <a href="https://arxiv.org/abs/2602.11698"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2602.11698-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2602.11698"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2602.11698-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Chengting Yu, Xiaobo Shu, Yadao Wang, Yizhen Zhang, Haoyi Wu, You Wu, Rujiao Long, Ziheng Chen, Yuchi Xu, Wenbo Su, Bo Zheng · 2026</div>
  <div><strong>Loop Mechanism:</strong> hierarchical-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning</div>
  <div><strong>TL;DR:</strong> Introduces SpiralFormer, a looped transformer that applies shared layers under a multi-resolution recursion schedule to learn hierarchical dependencies more efficiently than fixed-resolution recurrent baselines.</div>
  </details>

- <details>
  <summary>[02/11/2026] <strong>LoopFormer: Elastic-Depth Looped Transformers for Latent Reasoning via Shortcut Modulation</strong> <a href="https://arxiv.org/abs/2602.11451"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2602.11451-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2602.11451"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2602.11451-7c3aed.svg"></a> <a href="https://github.com/armenjeddi/loopformer/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/armenjeddi/loopformer?style=social"></a></summary>
  <div><strong>Authors:</strong> Ahmadreza Jeddi, Marco Ciccone, Babak Taati · ICLR 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm · inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning · efficiency</div>
  <div><strong>TL;DR:</strong> Introduces LoopFormer, trained on variable-length trajectories to enable budget-conditioned reasoning. Uses shortcut-consistency regularization to ensure stable internal trajectories across different loop depths.</div>
  </details>

- <details>
  <summary>[02/11/2026] <strong>Prioritize the Process, Not Just the Outcome: Rewarding Latent Thought Trajectories Improves Reasoning in Looped Language Models</strong> <a href="https://arxiv.org/abs/2602.10520"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2602.10520-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2602.10520"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2602.10520-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Jonathan Williams, Esin Tureci · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> objective-loss · training-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning</div>
  <div><strong>TL;DR:</strong> Introduces RLTT, a reinforcement-learning objective that assigns reward across the full latent thought trajectory of looped language models rather than only the final latent state.</div>
  </details>

- <details>
  <summary>[02/09/2026] <strong>Looping Back to Move Forward: Recursive Transformers for Efficient and Flexible Large Multimodal Models</strong> <a href="https://arxiv.org/abs/2602.09080"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2602.09080-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2602.09080"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2602.09080-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Ruihan Xu, Yuting Gao, Lan Wang, Jianing Li, Weihao Chen, Qingpei Guo, Ming Yang, Shiliang Zhang · 2026</div>
  <div><strong>Loop Mechanism:</strong> hierarchical-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> vision · efficiency</div>
  <div><strong>TL;DR:</strong> Introduces RecursiveVLM, a recursive multimodal transformer with a recursive connector and monotonic recursion loss that enables on-demand extra refinement under varying compute budgets.</div>
  </details>

- <details>
  <summary>[02/09/2026] <strong>Understanding Dynamic Compute Allocation in Recurrent Transformers</strong> <a href="https://arxiv.org/abs/2602.08864"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2602.08864-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2602.08864"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2602.08864-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Ibraheem Muhammad Moosa, Suhas Lohit, Ye Wang, Moitreya Chatterjee, Wenpeng Yin · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · algorithmic-reasoning · efficiency</div>
  <div><strong>Community Comments:</strong> <a href="https://x.com/huskydogewoof/status/2031044736182616081?s=20">Benhao&#x27;s reading note</a></div>
  <div><strong>TL;DR:</strong> Proposes ANIRA, a recurrent Transformer framework for per-token variable-depth computation, and shows adaptive compute can align with token complexity while failing to extrapolate to longer algorithmic inputs.</div>
  </details>

- <details>
  <summary>[01/29/2026] <strong>Depth-Recurrent Attention Mixtures: Giving Latent Reasoning the Attention it Deserves</strong> <a href="https://arxiv.org/abs/2601.21582"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2601.21582-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2601.21582"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2601.21582-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Jonas Knupp, Jan Hendrik Metzen, Jeremias Bohn, Georg Groh, Kristian Kersting · 2026</div>
  <div><strong>Loop Mechanism:</strong> parallel-loop · flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning · efficiency</div>
  <div><strong>Community Comments:</strong> <a href="https://x.com/huskydogewoof/status/2031585611262386670?s=20">Benhao&#x27;s reading note</a></div>
  <div><strong>TL;DR:</strong> Introduces a modular framework combining sequence attention and depth attention for recurrent-depth models, improving FLOP-, parameter-, and memory-efficiency simultaneously.</div>
  </details>

- <details>
  <summary>[01/26/2026] <strong>ChainGPT: Dual-Reasoning Model with Recurrent Depth and Multi-Rank State Updates</strong> <a href="https://openreview.net/pdf?id=kdZbxizwGK"><img alt="OpenReview" src="https://img.shields.io/badge/OpenReview-Paper-8E44AD.svg"></a></summary>
  <div><strong>Authors:</strong> Yunao Zheng, Xiaojie Wang, Lei Ren, Chen Wei · ICLR 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm · inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning</div>
  <div><strong>TL;DR:</strong> Introduces ChainGPT, a dual-reasoning recurrent-depth architecture that combines multi-substep state updates and state-guided sparse attention to move reasoning into latent computation, with adaptive stopping as a supporting mechanism.</div>
  </details>

- <details>
  <summary>[01/26/2026] <strong>MoDr: Mixture-of-Depth-Recurrent Transformers for Test-Time Reasoning</strong> <a href="https://openreview.net/pdf?id=9Pba4rcQbE"><img alt="OpenReview" src="https://img.shields.io/badge/OpenReview-Paper-8E44AD.svg"></a></summary>
  <div><strong>Authors:</strong> Xiaojing Zhang, Haifeng Wu, Gang He, Jiyang Shen, Bochen Lyu, Zhanxing Zhu · ICLR 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm · training-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning · efficiency · MoE</div>
  <div><strong>TL;DR:</strong> Introduces MoDr, which adds multi-branch routing to a depth-recurrent Transformer so looped models can explore solution paths more adaptively at test time.</div>
  </details>

- <details>
  <summary>[12/16/2025] <strong>Universal Reasoning Model</strong> <a href="https://arxiv.org/abs/2512.14693"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2512.14693-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2512.14693"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2512.14693-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Zitian Gao, Lynx Chen, Yihao Xiao, He Xing, Ran Tao, Haoming Luo, Joey Zhou, Bryan Dai · 2025</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm</div>
  <div><strong>Domains:</strong> algorithmic-reasoning · reasoning</div>
  <div><strong>TL;DR:</strong> Proposes URM, a Universal Transformer-based architecture with weight tying that beats standard transformers on reasoning benchmarks through iterative depth computation.</div>
  </details>

- <details>
  <summary>[11/11/2025] <strong>Think-at-Hard: Selective Latent Iterations to Improve Reasoning Language Models</strong> <a href="https://arxiv.org/abs/2511.08577"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2511.08577-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2511.08577"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2511.08577-7c3aed.svg"></a> <a href="https://github.com/thu-nics/TaH/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/thu-nics/TaH?style=social"></a></summary>
  <div><strong>Authors:</strong> Tianyu Fu, Yichen You, Zekai Chen, Guohao Dai, Huazhong Yang, Yu Wang · 2025</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning · efficiency</div>
  <div><strong>TL;DR:</strong> Introduces Think-at-Hard, a dynamic latent-thinking method that uses a learned decider to apply extra recurrent latent iterations only to hard tokens, with LoRA refiners and duo-causal attention across iteration depth.</div>
  </details>

- <details>
  <summary>[11/10/2025] <strong>Teaching Pretrained Language Models to Think Deeper with Retrofitted Recurrence</strong> <a href="https://arxiv.org/abs/2511.07384"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2511.07384-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2511.07384"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2511.07384-7c3aed.svg"></a> <a href="https://github.com/mcleish7/retrofitting-recurrence/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/mcleish7/retrofitting-recurrence?style=social"></a> <a href="https://huggingface.co/collections/tomg-group-umd/retrofitting-recurrence"><img alt="HuggingFace" src="https://img.shields.io/badge/HuggingFace-collections%2Ftomg--group--umd-ffb000.svg"></a></summary>
  <div><strong>Authors:</strong> Sean McLeish, Ang Li, John Kirchenbauer, Dayal Singh Kalra, Brian R. Bartoldson, Bhavya Kailkhura, Avi Schwarzschild, Jonas Geiping, Tom Goldstein, Micah Goldblum · 2025</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm</div>
  <div><strong>Domains:</strong> efficiency · language-modeling · reasoning</div>
  <div><strong>TL;DR:</strong> A framework for retrofitting pretrained feedforward language models with depth recurrence, improving training efficiency for depth-recurrent models and enabling greater FLOP efficiency than comparable feedforward models.</div>
  </details>

- <details>
  <summary>[10/29/2025] 🌟 <strong>Scaling Latent Reasoning via Looped Language Models</strong> <a href="https://arxiv.org/abs/2510.25741"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2510.25741-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2510.25741"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2510.25741-7c3aed.svg"></a> <a href="https://huggingface.co/ByteDance/Ouro-1.4B"><img alt="HuggingFace" src="https://img.shields.io/badge/HuggingFace-ByteDance%2FOuro--1.4B-ffb000.svg"></a> <a href="https://ouro-llm.github.io/"><img alt="Website" src="https://img.shields.io/badge/Website-Link-blue"></a></summary>
  <div><strong>Authors:</strong> Rui-Jie Zhu, Zixuan Wang, Kai Hua, Tianyu Zhang, Ziniu Li, Haoran Que, Boyi Wei, Zixin Wen, Fan Yin, He Xing, Lu Li, Jiajun Shi, Kaijing Ma, Shanda Li, Taylor Kergan, Andrew Smith, Xingwei Qu, Mude Hui, Bohong Wu, Qiyang Min, Hongzhi Huang, Xun Zhou, Wei Ye, Jiaheng Liu, Jian Yang, Yunfeng Shi, Chenghua Lin, Enduo Zhao, Tianle Cai, Ge Zhang, Wenhao Huang, Yoshua Bengio, Jason Eshraghian · 2025</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> objective-loss · architecture · data · training-algorithm · inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning</div>
  <div><strong>Community Comments:</strong> <a href="https://x.com/reza_byt/status/2045168844658950392?s=20">Reza Bayat reading list (#10)</a></div>
  <div><strong>TL;DR:</strong> Introduces Ouro, a family of pre-trained Looped Language Models (1.4B and 2.6B) that match the performance of 12B standard LLMs. Establishes loop depth as a third scaling axis beyond model size and data.</div>
  </details>

- <details>
  <summary>[10/28/2025] <strong>Parallel Loop Transformer for Efficient Test-Time Computation Scaling</strong> <a href="https://arxiv.org/abs/2510.24824"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2510.24824-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2510.24824"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2510.24824-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Bohong Wu, Mengzhao Chen, Xiang Luo, Shen Yan, Qifan Yu, Fan Xia, Tianqi Zhang, Hongrui Zhan, Zheng Zhong, Xun Zhou, Siyuan Qiao, Xingyan Bin · 2025</div>
  <div><strong>Loop Mechanism:</strong> parallel-loop · flat-loop</div>
  <div><strong>Focus:</strong> inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning · efficiency</div>
  <div><strong>TL;DR:</strong> Introduces the Parallel Loop Transformer, which preserves looped-model accuracy while reducing latency and memory through cross-loop parallelism and shared-loop KV representations.</div>
  </details>

- <details>
  <summary>[10/06/2025] <strong>Less is More: Recursive Reasoning with Tiny Networks</strong> <a href="https://arxiv.org/abs/2510.04871"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2510.04871-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2510.04871"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2510.04871-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Alexia Jolicoeur-Martineau · 2025</div>
  <div><strong>Loop Mechanism:</strong> hierarchical-loop · flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm · training-algorithm</div>
  <div><strong>Domains:</strong> reasoning</div>
  <div><strong>TL;DR:</strong> Proposes Tiny Recursive Model (TRM), a single tiny network that recursively refines latent state and answer over multiple improvement steps, outperforming HRM and many larger models on ARC-AGI-style reasoning tasks.</div>
  </details>

- <details>
  <summary>[10/03/2025] <strong>Coevolutionary Continuous Discrete Diffusion: Make Your Diffusion Language Model a Latent Reasoner</strong> <a href="https://arxiv.org/abs/2510.03206"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2510.03206-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2510.03206"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2510.03206-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Cai Zhou, Chenxiao Yang, Yi Hu, Chenyu Wang, Chubin Zhang, Muhan Zhang, Lester Mackey, Tommi Jaakkola, Stephen Bates, Dinghuai Zhang · 2025</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm · inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning</div>
  <div><strong>TL;DR:</strong> Proposes Coevolutionary Continuous Discrete Diffusion, a joint continuous-discrete diffusion language model that repeatedly denoises latent and token states with one time-conditioned model, linking diffusion sampling to latent reasoning and looped-transformer expressivity.</div>
  </details>

- <details>
  <summary>[07/14/2025] <strong>Mixture-of-Recursions: Learning Dynamic Recursive Depths for Adaptive Token-Level Computation</strong> <a href="https://arxiv.org/abs/2507.10524"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2507.10524-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2507.10524"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2507.10524-7c3aed.svg"></a> <a href="https://github.com/raymin0223/mixture_of_recursions/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/raymin0223/mixture_of_recursions?style=social"></a></summary>
  <div><strong>Authors:</strong> Sangmin Bae, Yujin Kim, Reza Bayat, Sungnyun Kim, Jiyoun Ha, Tal Schuster, Adam Fisch, Hrayr Harutyunyan, Ziwei Ji, Aaron Courville, Se-Young Yun · 2025</div>
  <div><strong>Loop Mechanism:</strong> hierarchical-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm · training-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning · efficiency</div>
  <div><strong>Community Comments:</strong> <a href="https://x.com/reza_byt/status/2045168844658950392?s=20">Reza Bayat reading list (#12)</a></div>
  <div><strong>TL;DR:</strong> Introduces Mixture-of-Recursions, a recursive transformer with token-level routing that adapts recursion depth and active-token attention so easy tokens exit early while hard tokens keep thinking.</div>
  </details>

- <details>
  <summary>[07/10/2025] <strong>Skip a Layer or Loop it? Test-Time Depth Adaptation of Pretrained LLMs</strong> <a href="https://arxiv.org/abs/2507.07996"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2507.07996-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2507.07996"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2507.07996-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Ziyue Li, Yang Li, Tianyi Zhou · 2025</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning</div>
  <div><strong>Community Comments:</strong> <a href="https://x.com/huskydogewoof/status/2037024461145215106?s=20">X Comment</a></div>
  <div><strong>TL;DR:</strong> Proposes Chain-of-Layers (CoLa), an inference-time search method that skips or repeats pretrained LLM layers per sample via MCTS to improve efficiency and reasoning accuracy.</div>
  </details>

- <details>
  <summary>[06/26/2025] <strong>Hierarchical Reasoning Model</strong> <a href="https://arxiv.org/abs/2506.21734"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2506.21734-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2506.21734"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2506.21734-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Guan Wang, Jin Li, Yuhao Sun, Xing Chen, Changling Liu, Yue Wu, Meng Lu, Sen Song, Yasin Abbasi Yadkori · 2025</div>
  <div><strong>Loop Mechanism:</strong> hierarchical-loop · flat-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm</div>
  <div><strong>Domains:</strong> reasoning · algorithmic-reasoning</div>
  <div><strong>TL;DR:</strong> Proposes HRM, a brain-inspired recurrent architecture with two coupled modules at different timescales: a high-level module for abstract planning and a low-level module for detailed execution.</div>
  </details>

- <details>
  <summary>[02/10/2025] <strong>Implicit Language Models are RNNs: Balancing Parallelization and Expressivity</strong> <a href="https://arxiv.org/abs/2502.07827"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2502.07827-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2502.07827"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2502.07827-7c3aed.svg"></a> <a href="https://github.com/microsoft/implicit_languagemodels/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/microsoft/implicit_languagemodels?style=social"></a> <a href="https://openreview.net/forum?id=5EbiopWH6e"><img alt="OpenReview" src="https://img.shields.io/badge/OpenReview-Paper-8E44AD.svg"></a></summary>
  <div><strong>Authors:</strong> Mark Schöne, Babak Rahmani, Heiner Kremer, Fabian Falck, Hitesh Ballani, Jannes Gladrow · ICML 2025</div>
  <div><strong>Loop Mechanism:</strong> implicit-layer</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning</div>
  <div><strong>TL;DR:</strong> Introduces implicit state-space language models that iterate a shared transition toward a fixed point, recovering RNN-like expressivity while retaining mostly parallel training.</div>
  </details>

- <details>
  <summary>[02/07/2025] 🌟 <strong>Scaling up Test-Time Compute with Latent Reasoning: A Recurrent Depth Approach</strong> <a href="https://arxiv.org/abs/2502.05171"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2502.05171-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2502.05171"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2502.05171-7c3aed.svg"></a> <a href="https://github.com/seal-rg/recurrent-pretraining/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/seal-rg/recurrent-pretraining?style=social"></a> <a href="https://huggingface.co/tomg-group-umd/huginn-0125"><img alt="HuggingFace" src="https://img.shields.io/badge/HuggingFace-tomg--group--umd%2Fhuginn--0125-ffb000.svg"></a></summary>
  <div><strong>Authors:</strong> Jonas Geiping, Sean McLeish, Neel Jain, John Kirchenbauer, Siddharth Singh, Brian R. Bartoldson, Bhavya Kailkhura, Abhinav Bhatele, Tom Goldstein · NeurIPS 2025</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture</div>
  <div><strong>Domains:</strong> language-modeling · reasoning</div>
  <div><strong>Community Comments:</strong> <a href="https://x.com/reza_byt/status/2045168844658950392?s=20">Reza Bayat reading list (#9)</a></div>
  <div><strong>TL;DR:</strong> Presents Huginn, a recurrent-depth transformer (3.5B params) that iterates a single block up to 64 times per token, achieving strong reasoning performance that scales with additional test-time compute.</div>
  </details>

- <details>
  <summary>[10/28/2024] <strong>Relaxed Recursive Transformers: Effective Parameter Sharing with Layer-wise LoRA</strong> <a href="https://arxiv.org/abs/2410.20672"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2410.20672-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2410.20672"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2410.20672-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Sangmin Bae, Adam Fisch, Hrayr Harutyunyan, Ziwei Ji, Seungyeon Kim, Tal Schuster · 2025</div>
  <div><strong>Loop Mechanism:</strong> hierarchical-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm</div>
  <div><strong>Domains:</strong> language-modeling</div>
  <div><strong>Community Comments:</strong> <a href="https://x.com/reza_byt/status/2045168844658950392?s=20">Reza Bayat reading list (#11)</a></div>
  <div><strong>TL;DR:</strong> Presents Relaxed Recursive Transformers as a parameter-sharing conversion and uptraining recipe that turns pretrained LLMs into compact recursive models using layer tying and layer-wise LoRA while preserving performance and improving deployment efficiency.</div>
  </details>

- <details>
  <summary>[05/25/2024] <strong>MoEUT: Mixture-of-Experts Universal Transformers</strong> <a href="https://arxiv.org/abs/2405.16039"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2405.16039-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2405.16039"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2405.16039-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Róbert Csordás, Kazuki Irie, Jürgen Schmidhuber, Christopher Potts, Christopher D. Manning · 2024</div>
  <div><strong>Loop Mechanism:</strong> flat-loop · hierarchical-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning · efficiency · MoE</div>
  <div><strong>TL;DR:</strong> Introduces MoEUT, a mixture-of-experts Universal Transformer that combines shared recurrent depth with expert routing to improve language modeling while using less compute and memory than comparable baselines.</div>
  </details>

- <details>
  <summary>[02/21/2024] <strong>AlgoFormer: An Efficient Transformer Framework with Algorithmic Structures</strong> <a href="https://arxiv.org/abs/2402.13572"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2402.13572-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2402.13572"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2402.13572-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Yihang Gao, Chuanyang Zheng, Enze Xie, Han Shi, Tianyang Hu, Yu Li, Michael K. Ng, Zhenguo Li, Zhaoqiang Liu · 2024</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · algorithmic-reasoning</div>
  <div><strong>TL;DR:</strong> Splits computation into pre-, loop-, and post-transformer stages, showing that structured recurrent depth can outperform standard and vanilla looped transformers on algorithmic and language tasks.</div>
  </details>

- <details>
  <summary>[10/16/2023] <strong>CoTFormer: A Chain-of-Thought Driven Architecture with Budget-Adaptive Computation Cost at Inference</strong> <a href="https://arxiv.org/abs/2310.10845"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2310.10845-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2310.10845"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2310.10845-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Amirkeivan Mohtashami, Matteo Pagliardini, Martin Jaggi · 2023</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · reasoning</div>
  <div><strong>TL;DR:</strong> Recasts chain-of-thought as recurrent depth inside a token-level transformer, using token-wise adaptive computation to spend extra iterations only where additional reasoning budget helps.</div>
  </details>

- <details>
  <summary>[09/22/2022] <strong>A Generalist Neural Algorithmic Learner</strong> <a href="https://arxiv.org/abs/2209.11142"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2209.11142-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2209.11142"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2209.11142-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Borja Ibarz, Vitaly Kurin, George Papamakarios, Kyriacos Nikiforou, Mehdi Bennani, Róbert Csordás, Andrew Dudzik, Matko Bošnjak, Alex Vitvitskyi, Yulia Rubanova, Andreea Deac, Beatrice Bevilacqua, Yaroslav Ganin, Charles Blundell, Petar Veličković · LoG 2022</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · data</div>
  <div><strong>Domains:</strong> algorithmic-reasoning</div>
  <div><strong>TL;DR:</strong> Presents a single GNN model trained on 30+ algorithms from the CLRS benchmark, demonstrating that a shared recurrent architecture can generalize across diverse algorithmic tasks.</div>
  </details>

- <details>
  <summary>[11/09/2021] <strong>On Training Implicit Models</strong> <a href="https://arxiv.org/abs/2111.05177"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2111.05177-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2111.05177"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2111.05177-7c3aed.svg"></a> <a href="https://proceedings.neurips.cc/paper/2021/hash/b0083e1a03ff2a5b6a0a2c4e0b1c3f0a-Abstract.html"><img alt="Paper" src="https://img.shields.io/badge/Paper-proceedings.neurips.cc-0366d6.svg"></a></summary>
  <div><strong>Authors:</strong> Zhengyang Geng, Xin-Yu Zhang, Shaojie Bai, Yisen Wang, Zhouchen Lin · NeurIPS 2021</div>
  <div><strong>Loop Mechanism:</strong> implicit-layer</div>
  <div><strong>Focus:</strong> training-algorithm</div>
  <div><strong>Domains:</strong> efficiency</div>
  <div><strong>TL;DR:</strong> Proposes phantom gradient, a lightweight backpropagation estimator for implicit (infinite-depth) models that uses damped unrolling and a truncated Neumann series to speed backward passes while matching or surpassing exact-gradient baselines on large-scale tasks.</div>
  </details>

- <details>
  <summary>[06/15/2020] <strong>Multiscale Deep Equilibrium Models</strong> <a href="https://arxiv.org/abs/2006.08656"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2006.08656-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2006.08656"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2006.08656-7c3aed.svg"></a> <a href="https://proceedings.neurips.cc/paper/2020/hash/75ebb3f7b5e8e9d6a7f7e4a4c4f7c2a0-Abstract.html"><img alt="Paper" src="https://img.shields.io/badge/Paper-proceedings.neurips.cc-0366d6.svg"></a></summary>
  <div><strong>Authors:</strong> Shaojie Bai, Vladlen Koltun, J. Zico Kolter · NeurIPS 2020</div>
  <div><strong>Loop Mechanism:</strong> implicit-layer · hierarchical-loop</div>
  <div><strong>Focus:</strong> architecture</div>
  <div><strong>Domains:</strong> vision</div>
  <div><strong>TL;DR:</strong> Extends DEQ to multiscale hierarchical representations, achieving competitive performance on large-scale vision tasks.</div>
  </details>

- <details>
  <summary>[09/03/2019] <strong>Deep Equilibrium Models</strong> <a href="https://proceedings.neurips.cc/paper/2019/hash/01386bd6d8e091c2ab4c7c7de644d37b-Abstract.html"><img alt="Paper" src="https://img.shields.io/badge/Paper-proceedings.neurips.cc-0366d6.svg"></a> <a href="https://github.com/locuslab/deq/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/locuslab/deq?style=social"></a></summary>
  <div><strong>Authors:</strong> Shaojie Bai, J. Zico Kolter, Vladlen Koltun · NeurIPS 2019</div>
  <div><strong>Loop Mechanism:</strong> implicit-layer</div>
  <div><strong>Focus:</strong> architecture · training-algorithm · inference-algorithm</div>
  <div><strong>TL;DR:</strong> Proposes to directly solve for the fixed point of an infinite-depth network, enabling implicit-depth models that are memory-efficient and theoretically equivalent to infinitely deep recurrent networks.</div>
  </details>

- <details>
  <summary>[07/10/2018] <strong>Universal Transformers</strong> <a href="https://arxiv.org/abs/1807.03819"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-1807.03819-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/1807.03819"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-1807.03819-7c3aed.svg"></a> <a href="https://openreview.net/forum?id=HyzdRiR9Y7"><img alt="OpenReview" src="https://img.shields.io/badge/OpenReview-Paper-8E44AD.svg"></a></summary>
  <div><strong>Authors:</strong> Mostafa Dehghani, Stephan Gouws, Oriol Vinyals, Jakob Uszkoreit, Łukasz Kaiser · ICLR 2019</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture</div>
  <div><strong>Domains:</strong> language-modeling · algorithmic-reasoning</div>
  <div><strong>Community Comments:</strong> <a href="https://x.com/reza_byt/status/2045168844658950392?s=20">Reza Bayat reading list (#3)</a></div>
  <div><strong>TL;DR:</strong> Extends the standard Transformer with recurrent computation over depth via weight tying, enabling Turing-complete computation and combining the parallelism of Transformers with the inductive bias of RNNs.</div>
  </details>

- <details>
  <summary>[03/29/2016] <strong>Adaptive Computation Time for Recurrent Neural Networks</strong> <a href="https://arxiv.org/abs/1603.08983"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-1603.08983-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/1603.08983"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-1603.08983-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Alex Graves · 2016</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> sequence-modeling · efficiency</div>
  <div><strong>TL;DR:</strong> Introduces ACT, allowing RNNs to learn how many computational steps to take per input, laying the groundwork for dynamic-depth recurrent computation.</div>
  </details>

- <details>
  <summary>[11/25/2015] <strong>Neural GPUs Learn Algorithms</strong> <a href="https://arxiv.org/abs/1511.08228"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-1511.08228-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/1511.08228"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-1511.08228-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Łukasz Kaiser, Ilya Sutskever · ICLR 2016</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm</div>
  <div><strong>Domains:</strong> algorithmic-reasoning</div>
  <div><strong>TL;DR:</strong> Introduces Neural GPUs, a recurrent convolutional architecture that learns parallel algorithms like addition and multiplication through repeated application of a shared convolutional recurrent block.</div>
  </details>

---

## Applications Focused

Applications Focused collects papers centered on applying loop models to concrete domains or tasks, including robotics, VLA, multimodal settings, tabular data, graph data, and other non-core benchmarks.

- <details>
  <summary>[06/21/2026] <strong>Adaptive Recurrent Message Passing for Test Time Computing on Graphs</strong> <a href="https://arxiv.org/abs/2606.22462"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2606.22462-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2606.22462"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2606.22462-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Junshu Sun, Wanxing Chang, Qingming Huang, Shuhui Wang · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm · training-algorithm</div>
  <div><strong>Domains:</strong> graph-data · efficiency</div>
  <div><strong>TL;DR:</strong> Introduces AdaR, an adaptive recurrent graph model that repeatedly applies learned recurrent message-passing updates with step conditioning, enabling flexible test-time compute on graph tasks without changing model parameters.</div>
  </details>

- <details>
  <summary>[06/16/2026] <strong>Looped World Models</strong> <a href="https://arxiv.org/abs/2606.18208"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2606.18208-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2606.18208"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2606.18208-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Hongyuan Adam Lu, Z. L. Victor Wei, Qun Zhang, Jinrui Zeng, Bowen Cao, Lingwei Meng, Mocheng Li, Zezhong Wang, Haonan Yin, Naifu Xue, Minyu Chen, Cenyuan Zhang, Zefan Zhang, Hao Wei, Jiawei Zhou, Haoran Xu, Hao Yang, Ronglai Zuo, Tongda Xu, Yonghao Li, Jian Chen, Hebin Wang, Zeyu Gao, Yang Li, Wei Zhao, Qimin Zhong, Siqi Liu, Yumeng Zhang, Leyan Cui, Zhangyu Wang, Wai Lam · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> world-modeling · efficiency · scaling</div>
  <div><strong>TL;DR:</strong> Introduces LoopWM, a world-model architecture that iteratively refines latent environment states through a parameter-shared Transformer block, using adaptive computation to scale latent depth per prediction step and reporting up to 100x parameter efficiency over conventional world-modeling approaches.</div>
  </details>

- <details>
  <summary>[06/12/2026] <strong>A Fixed-Point Neural Operator for Size- and Functional-Transferable Hamiltonian Prediction</strong> <a href="https://arxiv.org/abs/2606.14498"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2606.14498-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2606.14498"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2606.14498-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Yunhong Lou, Xihang Yue, Xinran Wei, Tianqi Deng, Linchao Zhu · 2026</div>
  <div><strong>Loop Mechanism:</strong> implicit-layer</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> efficiency</div>
  <div><strong>TL;DR:</strong> Introduces HamEvo, a fixed-point neural operator for Kohn-Sham Hamiltonian prediction that learns a single-step self-consistent update and returns the converged Hamiltonian as the learned operator&#x27;s fixed point, improving electronic-structure prediction accuracy and transfer.</div>
  </details>

- <details>
  <summary>[06/04/2026] <strong>MPCoT: Reward-Guided Multi-Path Latent Reasoning for Test-Time Scalable Vision-Language-Action</strong> <a href="https://arxiv.org/abs/2606.06245"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2606.06245-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2606.06245"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2606.06245-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Boyang Zhang, Lianlei Shan · 2026</div>
  <div><strong>Loop Mechanism:</strong> parallel-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm · inference-algorithm</div>
  <div><strong>Domains:</strong> robotics-vla · reasoning</div>
  <div><strong>TL;DR:</strong> Introduces a VLA latent-reasoning policy that initializes multiple latent hypotheses, refines them for K weight-tied steps, and aggregates them before action decoding.</div>
  </details>

- <details>
  <summary>[06/03/2026] <strong>Test-Time Compute Scaling for ASR with Depth-Conditioned Looped Transformers</strong> <a href="https://arxiv.org/abs/2606.04678"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2606.04678-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2606.04678"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2606.04678-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Yacouba Kaloga, Shashi Kumar, Shakeel A. Sheikh, Driss Khalil, Petr Motlicek, Ina Kodrasi · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> speech-recognition · efficiency · scaling</div>
  <div><strong>TL;DR:</strong> Introduces LARM, a depth-conditioned looped Transformer for automatic speech recognition that reuses a shared acoustic-encoder block recurrently and scales recognition quality by increasing inference-time loop count.</div>
  </details>

- <details>
  <summary>[06/02/2026] <strong>BA-T: An Iterative Transformer for Two-View Bundle Adjustment</strong> <a href="https://arxiv.org/abs/2606.03287"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2606.03287-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2606.03287"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2606.03287-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Ganlin Zhang, Weirong Chen, Daniel Cremers, Xi Wang · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> vision · efficiency</div>
  <div><strong>TL;DR:</strong> Implements bundle-adjustment-style 3D reconstruction updates as a repeatable lightweight Transformer layer in implicit token space, improving pose and reconstruction estimates across iterations.</div>
  </details>

- <details>
  <summary>[05/28/2026] <strong>Déjà View: Looping Transformers for Multi-View 3D Reconstruction</strong> <a href="https://arxiv.org/abs/2605.30215"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2605.30215-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2605.30215"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2605.30215-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Alessandro Burzio, Tobias Fischer, Sven Elflein, Qunjie Zhou, Riccardo de Lutio, Jiawei Ren, Jiahui Huang, Shengyu Huang, Marc Pollefeys, Laura Leal-Taixé, Zan Gojcic, Haithem Turki · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> vision · efficiency</div>
  <div><strong>TL;DR:</strong> Applies a single looped transformer block recurrently to per-view features for a variable number of refinement steps in multi-view 3D reconstruction, exposing loop count as an inference-time compute knob.</div>
  </details>

- <details>
  <summary>[05/27/2026] <strong>Recursive Vision Transformer with Dynamic Depth and Width Adjustment for Resource-Efficient Image Semantic Communication</strong> <a href="https://arxiv.org/abs/2606.00114"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2606.00114-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2606.00114"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2606.00114-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Zhilong Zhang, Xinhui Zhang, Gongyu Jin, Sihua Wang, Danpu Liu, Changchuan Yin · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> vision · efficiency</div>
  <div><strong>TL;DR:</strong> Uses a recursive ViT structure to iteratively refine semantic features for image semantic communication while dynamically adjusting recursive depth and width under image and channel conditions.</div>
  </details>

- <details>
  <summary>[05/19/2026] <strong>i-DEQ: A stable inertial deep equilibrium model for image restoration</strong> <a href="https://arxiv.org/abs/2605.19705"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2605.19705-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2605.19705"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2605.19705-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Antonin Clerc, Marien Renaud, Baudouin Denis De Seneville, Nicolas Papadakis · 2026</div>
  <div><strong>Loop Mechanism:</strong> implicit-layer</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm · training-algorithm</div>
  <div><strong>Domains:</strong> vision · efficiency</div>
  <div><strong>TL;DR:</strong> Introduces i-DEQ, an inertial deep-equilibrium image-restoration model that learns explicit nonconvex regularization and uses momentum in fixed-point iterations, improving stability and robustness while roughly halving DEQ inference time.</div>
  </details>

- <details>
  <summary>[05/19/2026] <strong>Nonlocal operator learning for fMRI encoding and decoding tasks</strong> <a href="https://arxiv.org/abs/2605.20389"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2605.20389-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2605.20389"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2605.20389-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Andreas Kramer, Saugat Acharya, Alice Giola, Emanuele Zappala · 2026</div>
  <div><strong>Loop Mechanism:</strong> implicit-layer</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> sequence-modeling</div>
  <div><strong>TL;DR:</strong> Applies a latent neural integral-operator model to fMRI encoding and decoding, using fixed-point iterations in an auxiliary latent space before downstream classification or stimulus prediction.</div>
  </details>

- <details>
  <summary>[05/18/2026] <strong>PERL: Parameter Efficient Reasoning in CLIP Latent Space</strong> <a href="https://arxiv.org/abs/2605.18464"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2605.18464-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2605.18464"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2605.18464-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Simone Carnemolla, Salvatore Calcagno, Daniela Giordano, Concetto Spampinato, Matteo Pennisi · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm · inference-algorithm</div>
  <div><strong>Domains:</strong> vision · reasoning · efficiency</div>
  <div><strong>TL;DR:</strong> Introduces PERL, a few-shot CLIP adaptation framework that reuses a compact shared reasoning module across latent refinement steps, improving base-to-novel, transfer, and OOD results with about 6K trainable parameters.</div>
  </details>

- <details>
  <summary>[05/12/2026] <strong>Recurrent Transformer-Based Near- and Far-Field THz Wideband Channel Estimation for UM-MIMO</strong> <a href="https://arxiv.org/abs/2605.12578"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2605.12578-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2605.12578"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2605.12578-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Dmitry Artemasov, Alexander Shmatok, Kirill Andreev, Alexey Frolov, Manjesh K. Hanawal, Nikola Zlatanov · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> sequence-modeling · efficiency</div>
  <div><strong>TL;DR:</strong> Applies a block-recurrent transformer to hybrid near/far-field THz UM-MIMO channel estimation, training one state-memory transformer block once and iteratively reusing it to improve narrowband and wideband NMSE.</div>
  </details>

- <details>
  <summary>[04/30/2026] <strong>ITS-Mina: A Harris Hawks Optimization-Based All-MLP Framework with Iterative Refinement and External Attention for Multivariate Time Series Forecasting</strong> <a href="https://arxiv.org/abs/2604.27981"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2604.27981-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2604.27981"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2604.27981-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Pourya Zamanvaziri, Amirhossein Sadr, Aida Pakniyat, Dara Rahmati · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> sequence-modeling · efficiency</div>
  <div><strong>TL;DR:</strong> Applies a shared-parameter iterative refinement module inside an all-MLP multivariate time-series forecasting system, using the loop-model pattern for a concrete forecasting application.</div>
  </details>

- <details>
  <summary>[04/13/2026] <strong>A Deep Equilibrium Network for Hyperspectral Unmixing</strong> <a href="https://arxiv.org/abs/2604.11279"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2604.11279-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2604.11279"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2604.11279-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Chentong Wang, Jincheng Gao, Fei Zhu, Jie Chen · 2026</div>
  <div><strong>Loop Mechanism:</strong> implicit-layer</div>
  <div><strong>Focus:</strong> architecture · training-algorithm</div>
  <div><strong>Domains:</strong> hyperspectral-imaging</div>
  <div><strong>TL;DR:</strong> Recasts hyperspectral unmixing as a deep equilibrium model, replacing the reconstruction-gradient operator with a trainable convolutional update and solving for an implicit fixed point with constant-memory differentiation.</div>
  </details>

- <details>
  <summary>[02/08/2026] <strong>Recurrent-Depth VLA: Implicit Test-Time Compute Scaling of Vision-Language-Action Models via Latent Iterative Reasoning</strong> <a href="https://arxiv.org/abs/2602.07845"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2602.07845-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2602.07845"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2602.07845-7c3aed.svg"></a> <a href="https://github.com/rd-vla/rd-vla/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/rd-vla/rd-vla?style=social"></a> <a href="https://rd-vla.github.io/"><img alt="Website" src="https://img.shields.io/badge/Website-Link-blue"></a></summary>
  <div><strong>Authors:</strong> Yalcin Tur, Jalal Naghiyev, Haoquan Fang, Wei-Chuan Tsai, Jiafei Duan, Dieter Fox, Ranjay Krishna · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm · inference-algorithm</div>
  <div><strong>Domains:</strong> robotics-vla</div>
  <div><strong>TL;DR:</strong> Introduces RD-VLA, a vision-language-action architecture with a weight-tied recurrent action head and adaptive stopping, enabling latent test-time compute scaling for robotics with constant memory footprint.</div>
  </details>

- <details>
  <summary>[02/05/2026] <strong>On the Role of Iterative Computation in Reinforcement Learning</strong> <a href="https://arxiv.org/abs/2602.05999"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2602.05999-b31b1b.svg"></a> <a href="https://www.alphaxiv.org/abs/2602.05999"><img alt="AlphaXiv" src="https://img.shields.io/badge/AlphaXiv-2602.05999-7c3aed.svg"></a></summary>
  <div><strong>Authors:</strong> Raj Ghugare, Michał Bortkiewicz, Alicja Ziarko, Benjamin Eysenbach · 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm · training-algorithm</div>
  <div><strong>Domains:</strong> rl-control</div>
  <div><strong>TL;DR:</strong> Formalizes compute-bounded RL policies and introduces a minimal variable-compute architecture, showing that extra iterative computation improves performance and longer-horizon generalization across 31 online and offline RL tasks.</div>
  </details>

---

## Blogs

Long-form technical posts, essays, and deep-dives about loop models. Blogs can carry Loop Mechanism / focus / domain tags but stay in a single flat section rather than the paper taxonomy.

- <details>
  <summary>[05/23/2026] <strong>Rethinking Hierarchy in Iterative Reasoning Models</strong> <a href="https://x.com/huskydogewoof/status/2058082328744993013?s=20"><img alt="Blog" src="https://img.shields.io/badge/Blog-x.com-0ea5e9.svg"></a></summary>
  <div><strong>Authors:</strong> Benhao Huang · X Article 2026</div>
  <div><strong>Loop Mechanism:</strong> hierarchical-loop · flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> reasoning · algorithmic-reasoning</div>
  <div><strong>TL;DR:</strong> Interprets HRM/TRM-style two-level iteration through value-policy-like coupled dynamics, then reports preliminary evidence that low-level latent states can be better ACT halting inputs than answer-proximal high-level states.</div>
  </details>

- <details>
  <summary>[04/29/2026] <strong>Exact Input Writes Improve Stable Looped Language Models</strong> <a href="https://huskydoge.github.io/husky-blog/posts/recursive_models/improve-parcae/"><img alt="Blog" src="https://img.shields.io/badge/Blog-huskydoge.github.io-0ea5e9.svg"></a> <a href="https://github.com/huskydoge/parcae-zoh-exact/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/huskydoge/parcae-zoh-exact?style=social"></a></summary>
  <div><strong>Authors:</strong> Benhao Huang · Personal Blog 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · theory</div>
  <div><strong>TL;DR:</strong> Proposes replacing Parcae&#x27;s Euler input-write gain with the exact zero-order-hold gain, then reports matched 140M looped-language-model controls where Exact-ZOH lowers validation loss under both short-budget probes and an 11.2B-token paper-style run.</div>
  </details>

- <details>
  <summary>[04/21/2026] <strong>Claude Mythos, Looped LLM, and the Depth Scaling Axis</strong> <a href="https://x.com/RidgerZhu/status/2046736781035618602"><img alt="Blog" src="https://img.shields.io/badge/Blog-x.com-0ea5e9.svg"></a></summary>
  <div><strong>Authors:</strong> Rui-Jie Zhu · X Article 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture</div>
  <div><strong>Domains:</strong> language-modeling · reasoning · scaling</div>
  <div><strong>TL;DR:</strong> Analyzes why Claude Mythos-like gains suggest a depth-scaling axis for looped LLMs and discusses stability, inference efficiency, and iso-FLOPs constraints for scaling loop architectures.</div>
  </details>

- <details>
  <summary>[04/19/2026] <strong>Loop-Model FLOPs and Memory in an Ablation Chain</strong> <a href="https://huskydoge.github.io/husky-blog/posts/recursive_models/loop-cost/"><img alt="Blog" src="https://img.shields.io/badge/Blog-huskydoge.github.io-0ea5e9.svg"></a></summary>
  <div><strong>Authors:</strong> Benhao Huang · Personal Blog 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> training-algorithm</div>
  <div><strong>Domains:</strong> FLOPs-efficiency · memory-efficiency · theory</div>
  <div><strong>TL;DR:</strong> Builds a clean cost-ablation chain for loop-model training, comparing shared versus non-shared weights, per-step losses, detach, instant updates, internal truncation, and gradient checkpointing, then checks the resulting FLOPs and memory trade-offs with a toy benchmark.</div>
  </details>

- <details>
  <summary>[04/19/2026] <strong>On the Looped Transformers Controversy</strong> <a href="https://x.com/ChrisHayduk/status/2045947623572688943?s=20"><img alt="Blog" src="https://img.shields.io/badge/Blog-x.com-0ea5e9.svg"></a></summary>
  <div><strong>Authors:</strong> Chris Hayduk · X Article 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture</div>
  <div><strong>Domains:</strong> language-modeling · reasoning · scaling</div>
  <div><strong>TL;DR:</strong> Argues that benchmark patterns and serving-compute constraints make deterministic weight-tied looping a plausible explanation for Claude Mythos-like gains, while explicitly framing the claim as speculation rather than confirmation.</div>
  </details>

- <details>
  <summary>[01/12/2026] <strong>Looped-GPT: Looping During Pre-training improves Generalization</strong> <a href="https://sanyalsunny111.github.io/posts/2026-01-15-post1-looped-gpt/"><img alt="Blog" src="https://img.shields.io/badge/Blog-sanyalsunny111.github.io-0ea5e9.svg"></a> <a href="https://github.com/sanyalsunny111/Looped-GPT/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/sanyalsunny111/Looped-GPT?style=social"></a></summary>
  <div><strong>Authors:</strong> Sunny Sanyal · Personal Blog 2026</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · training-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · scaling · efficiency</div>
  <div><strong>TL;DR:</strong> Introduces Looped-GPT, a reverse-residual depth-recurrent GPT variant, and reports pre-training experiments where looped models improve generalization under matched parameter, token, and fixed-FLOPs settings.</div>
  </details>

- <details>
  <summary>[01/07/2020] <strong>Adaptive Computation Time (ACT) in Neural Networks [3/3]</strong> <a href="https://moocaholic.medium.com/adaptive-computation-time-act-in-neural-networks-3-3-99452b2eff18"><img alt="Blog" src="https://img.shields.io/badge/Blog-moocaholic.medium.com-0ea5e9.svg"></a></summary>
  <div><strong>Authors:</strong> Grigory Sapunov · Medium 2020</div>
  <div><strong>Loop Mechanism:</strong> flat-loop</div>
  <div><strong>Focus:</strong> architecture · inference-algorithm</div>
  <div><strong>Domains:</strong> language-modeling · algorithmic-reasoning · efficiency</div>
  <div><strong>TL;DR:</strong> Reviews Adaptive Computation Time in transformer-style models, focusing on Universal Transformers with dynamic per-position halting, adaptive attention span, and ALBERT-style cross-layer parameter sharing as related forms of adaptive or repeated computation.</div>
  </details>

---


## Contributing

We welcome additions, corrections, and scope challenges.

The preferred PR Submission Guide workflow is:
1. Open the [PR Submission Guide](https://huskydoge.github.io/Awesome-Loop-Models/submit.html)
2. Reuse the searchable Loop Mechanism (`mechanism_tags`) / `focus_tags` / `domain_tags`, then fill the alias tags manually only if needed
3. Review the generated path and generated YAML locally
4. Fork the repo on GitHub to your own account
5. Create a branch in your fork, create the generated file path, paste the generated YAML, and open a pull request


The guide generates YAML for `papers/` or `blogs/` directly. For blogs, the filename should follow `blogs/YYYY-MM-DD-shortname.yaml`. Blogs here should be substantive long-form technical posts, not short announcements or marketing pages.

See [CONTRIBUTING.md](CONTRIBUTING.md), [TAXONOMY.md](TAXONOMY.md), and [TAGS.md](TAGS.md) for details.

---

<div align="center">
<sub>
  Maintained by <a href="https://github.com/huskydoge">huskydoge</a>.
  README auto-generated from <code>papers/*.yaml</code> and <code>blogs/*.yaml</code> by <a href="scripts/build.py">scripts/build.py</a>.
</sub>
</div>
