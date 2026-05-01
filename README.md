
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

- [Theoretical and Mechanical Analysis](#theoretical-and-mechanical-analysis) (15)
- [Architecture and Algorithm Designs](#architecture-and-algorithm-designs) (42)
- [Applications Focused](#applications-focused) (3)
- [Blogs](#blogs) (4)

> The paper shelves are intentionally coarse: Theoretical and Mechanical Analysis, Architecture and Algorithm Designs, and Applications Focused. Foundation status plus Loop Mechanism / focus / domain tags carry secondary structure without introducing lineage buckets.
> Blogs are a separate flat section: they can carry tags, but they do not use the paper taxonomy.

---

<!-- AUTO-GENERATED by scripts/build.py on 2026-05-01 03:03 UTC — DO NOT EDIT the lists below manually. Edit papers/*.yaml or blogs/*.yaml and run `python3 scripts/build.py` instead. -->

## Theoretical and Mechanical Analysis

Theoretical and Mechanical Analysis collects papers whose primary contribution is analysis: why loop models work, what formal properties they have, and what mechanisms they exhibit.

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
  <div><strong>Domains:</strong> language-modeling · efficiency</div>
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
  <div><strong>Domains:</strong> language-modeling · reasoning · efficiency</div>
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
  <div><strong>Domains:</strong> language-modeling · reasoning · efficiency</div>
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
