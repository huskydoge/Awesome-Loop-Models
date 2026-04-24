
<div align="center">

# Awesome Loop Models

[![Awesome](https://awesome.re/badge.svg)](https://awesome.re)
[![Submit](https://img.shields.io/badge/📄%20Submit-blue?style=flat-square)]({{PUBLIC_SUBMIT_URL}})
[![Website](https://img.shields.io/badge/🌐%20Live%20Website-Link-blue?style=flat-square)]({{PUBLIC_INDEX_URL}})
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<img src="assets/cover.png" alt="Loop architecture concept diagram" width="100%" />

### 🌐 [**Interactive Browser**]({{PUBLIC_INDEX_URL}}) · 🧾 [**PR Submission Guide**]({{PUBLIC_SUBMIT_URL}})

*Search, filter, and explore loop-model papers and selected technical blogs with links to arXiv, code, OpenReview, and more.*

*Use the PR Submission Guide to generate YAML for papers or blogs, then copy the path and YAML into your fork / branch for the final pull request step.*

</div>

A curated list of papers and selected long-form technical blogs on **Loop Models** — architectures where, within a single forward process, a shared learned internal layer, block, module, or operator is reused.

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
