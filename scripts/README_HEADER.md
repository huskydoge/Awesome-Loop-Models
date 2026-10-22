<div align="center">

# Awesome Loop Models

**Models that compute by looping: one learned layer, block, or operator, reused across depth or folded into time.**

[![Awesome](https://awesome.re/badge.svg)](https://awesome.re)
[![Website](https://img.shields.io/badge/🌐%20Live%20Website-Link-blue?style=flat-square)]({{PUBLIC_INDEX_URL}})
[![Submit](https://img.shields.io/badge/📄%20Submit-blue?style=flat-square)]({{PUBLIC_SUBMIT_URL}})
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<img src="assets/cover.png" alt="Loop architecture concept diagram" width="100%" />

### 🌐 [**Interactive Browser**]({{PUBLIC_INDEX_URL}}) · 🧾 [**PR Submission Guide**]({{PUBLIC_SUBMIT_URL}})

<sub>The full catalog lives in the browser: search, browse by chapter, filter by section and loop design, and read TL;DRs, venues, code links, and daily briefings.</sub>

</div>

## News

- **2026-07-17** — The browser gained a **Release Intelligence** view: publication pulse, long-term trends, and dossiers for the latest releases. [Explore stats]({{PUBLIC_INDEX_URL}}#stats)
- **2026-04-24** — Awesome Loop Models is released. [Announcement](https://x.com/huskydogewoof/status/2047655947942744285)

## What is a loop model?

> A shared learned layer, block, module, or operator is reused, either along depth within one forward pass or along time, by feeding a state it computed back through the same layers for the next token or step.

That covers looped, recurrent-depth, and weight-tied Transformers, adaptive halting over a reused block, deep-equilibrium and implicit layers, shared neural algorithmic processors, and models that fold depth into time by feeding high-level states back through the same layers (Feedback Transformers, Latent Recurrent Transformers, shift-1 loops), plus theory and analysis of all of these. It leaves out agent loops, repeated full-model calls, diffusion-style iterative inference, and ordinary sequence recurrence that only carries a memory across steps. [TAXONOMY.md](TAXONOMY.md) has the full rules.

<details>
<summary>Where the scope boundary sits</summary>
<br>
<img src="assets/scope.png" alt="Scope scale from agent loop to loop models" width="100%" />

Only the rightmost end of this scale is in scope. Omitting `catalog_fit` means strict scope; the rare exceptions kept for context set `catalog_fit: adjacent` and are labeled **Adjacent work**.
</details>

<details>
<summary>How the catalog is organized</summary>
<br>

The catalog is organized as a **topic map** of chapters and sections. Each paper lists every section it belongs to, primary first, and the browser files it under that primary section.

| Part | Chapters |
|:--|:--|
| I. Foundations | §2 From recurrent computation to iterative depth |
| II. What looping buys | §3 Capabilities, benefits and trade-offs |
| III. Building, training and deploying | §4 Architecture · §5 Learning algorithms · §6 Scaling laws · §7 Systems |
| IV. Understanding and applications | §8 Why looped models work · §9 Applications |
| V. Open problems | §10 Diffusion · folding depth into time · monitorability and safety |

Every paper also records its design axes (`loop_topology`, `sharing`, `depth_control`) and what it claims looping buys (`claims`, `comparison`). All values are controlled; there are no free-form tags. Blogs sit in one flat section and list only the sections they discuss. [TAXONOMY.md](TAXONOMY.md) explains each value and [TAGS.md](TAGS.md) shows current counts.
</details>
