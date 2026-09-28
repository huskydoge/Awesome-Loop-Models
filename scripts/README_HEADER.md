<div align="center">

# Awesome Loop Models

**Models that compute by looping: one learned layer, block, or operator, reused inside a single forward pass.**

[![Awesome](https://awesome.re/badge.svg)](https://awesome.re)
[![Website](https://img.shields.io/badge/🌐%20Live%20Website-Link-blue?style=flat-square)]({{PUBLIC_INDEX_URL}})
[![Submit](https://img.shields.io/badge/📄%20Submit-blue?style=flat-square)]({{PUBLIC_SUBMIT_URL}})
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<img src="assets/cover.png" alt="Loop architecture concept diagram" width="100%" />

### 🌐 [**Interactive Browser**]({{PUBLIC_INDEX_URL}}) · 🧾 [**PR Submission Guide**]({{PUBLIC_SUBMIT_URL}})

<sub>The full catalog lives in the browser: search, filter by loop mechanism and domain, and read TL;DRs, venues, code links, and daily briefings.</sub>

</div>

## What is a loop model?

> Within a single forward pass, a shared learned layer, block, module, or operator is reused.

That covers looped, recurrent-depth, and weight-tied Transformers, adaptive halting over a reused block, deep-equilibrium and implicit layers, and shared neural algorithmic processors, plus theory and analysis of all of these. It leaves out agent loops, repeated full-model calls, diffusion-style iterative inference, and plain recurrence over time steps. [TAXONOMY.md](TAXONOMY.md) has the full rules.

<details>
<summary>Where the scope boundary sits</summary>
<br>
<img src="assets/scope.png" alt="Scope scale from agent loop to loop models" width="100%" />

Only the rightmost end of this scale is in scope. Omitting `catalog_fit` means strict scope; the rare exceptions kept for context set `catalog_fit: adjacent` and are labeled **Adjacent work**.
</details>

<details>
<summary>How the catalog is organized</summary>
<br>

| Axis | Values |
|:--|:--|
| **Category** | Theoretical and Mechanical Analysis · Architecture and Algorithm Designs · Applications Focused |
| **Loop Mechanism** (`mechanism_tags`) | `flat-loop` · `hierarchical-loop` · `parallel-loop` · `implicit-layer` |
| **Focus** (`focus_tags`) | `architecture` · `training-algorithm` · `inference-algorithm` · `objective-loss` · `data` |
| **Domain** (`domain_tags`) | `language-modeling`, `reasoning`, `vision`, `graph-data`, … |

A paper can also carry a `foundation` badge when it is a canonical anchor such as ACT, Universal Transformers, or DEQ. The browser filters by Loop Mechanism, focus, and domain tags. Blogs sit in one flat section outside the paper categories. [TAGS.md](TAGS.md) lists every tag in use.
</details>
