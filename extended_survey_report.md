# LLM 逐层解码概率分布演变调研报告：从“Logit Lens”到“隐式推理”

关于“大语言模型（LLM）每一层解码得到的概率分布是什么样的，是否是一个锐化（Sharpening）的过程”，学术界已经有大量深入的研究。简短的回答是：**是的，LLM 的逐层概率分布演变确实表现为一个“逐步锐化（Sharpening）”和“置信度校准”的过程，但这个过程并非简单的线性递增，而是呈现出明显的分阶段（Stages of Inference）特征，并且在不同架构和任务中表现出高度的复杂性。**

本文在早期观测工具和四阶段推理假说的基础上，进一步扩展了对注意力机制分工、残差流动态、深度效率以及最新隐式推理（Implicit Reasoning）范式的调研，系统性地总结了 LLM 逐层概率分布演变的最新研究进展。

## 1. 核心观测工具：从 Logit Lens 到 Entropy-Lens

要探究 LLM 中间层的概率分布，研究者们通常使用一种称为 **Logit Lens** [1] 的技术。该技术将 Transformer 中间层的隐藏状态（Hidden States）直接乘以最终的 unembedding 矩阵，从而在每一层都“解码”出一个词表上的概率分布。由于直接使用 Logit Lens 可能会因为层间表示空间的差异而产生偏差，后续研究提出了 **Tuned Lens** [2]，通过为每一层训练一个仿射变换探针（Affine Probe），更准确地提取中间层的潜在预测。

近期，研究者在这些工具的基础上引入了信息论视角。**Entropy-Lens** [3] 框架通过计算每一层 Logit Lens 预测分布的熵（Entropy），将高维的词表概率分布压缩为一个低维的“熵轮廓（Entropy Profile）”。研究表明，这种逐层熵的变化能够清晰地揭示模型在预测下一个 Token 时的两种核心策略：**候选扩展（Expansion）**（熵增加，模型考虑更多可能性）和**候选剪枝（Pruning）**（熵减少，模型收敛到特定预测）。这种基于熵的观测方法证明了不同模型家族（如 LLaMA、Gemma）具有其独特的逐层概率演变指纹。

## 2. 逐层概率演变的核心规律：“四阶段推理”与“猜测-精炼”框架

关于概率分布的演变，麻省理工学院（MIT）的研究团队提出了一个极具影响力的“四阶段推理”假说 [4]。他们发现，概率分布的锐化主要发生在最后阶段：

1. **去 Token 化（Detokenization，早期层）**：整合局部上下文，将原始 token 嵌入提升为高级表示。此时的解码概率分布通常是平缓且混乱的。
2. **特征工程（Feature Engineering，中间层）**：迭代地提取和细化特定任务的特征。此时模型在积累信息，但输出概率分布的熵仍然较高。
3. **预测集成（Prediction Ensembling，中后期层）**：隐藏状态开始聚合成合理的下一个 token 预测，正确 token 的概率开始显著上升。
4. **残差锐化（Residual Sharpening，最后几层）**：**这是最关键的锐化阶段**。在最后的几层中，模型会抑制不相关的特征，使得最终的输出分布急剧锐化（Sharpening），正确 token 的概率质量（Probability Mass）高度集中，熵急剧下降。

最新的研究进一步提出了 **“猜测-精炼（Guess-then-Refine）”框架** [5] 来解释这一过程。研究发现，在早期层中，模型倾向于将高频词（High-frequency tokens）推到概率分布的榜首，这相当于在缺乏足够上下文信息时做出的“统计猜测”。随着计算向深层推进，这些初步的猜测会被逐渐精炼和修正为符合上下文的正确 Token。

## 3. 概率锐化与置信度校准（Calibration）

近期的多项研究进一步证实并细化了这种“锐化”现象，特别是在模型对齐和后训练阶段：

* **置信度修正阶段**：研究发现 LLM 在较深层存在一个明显的“置信度修正阶段” [6]。在这个阶段，模型在已经确定了决策（即 Top-1 token 已经稳定）之后，会主动重新校准（Recalibrate）其置信度，表现为概率分布的进一步锐化或平滑，以匹配其真实的准确率。
* **对齐（Alignment）加剧了锐化**：经过 RLHF 等对齐微调后的模型，其输出分布会比基础模型（Base Model）更加锐化 [7]。对齐过程极大地降低了分布的“分支因子（Branching Factor）”，使得概率高度集中在少数几个 token 上。
* **后训练导致的探索坍塌**：对于经过强化学习后训练的推理模型（如 DeepSeek-R1 类的模型），其最后一层的后验概率分布表现出急剧降低的熵（极度锐化），而中间层的熵仍然相对较高 [8]。这种极度的锐化甚至可能导致温度采样（Temperature Sampling）失效。

## 4. 注意力头与 MLP 层的分工机制

概率分布的逐层演变并非由单一机制驱动，而是注意力头（Attention Heads）和多层感知机（MLP）层协同作用的结果。

| 组件 | 核心功能与对概率分布的贡献 |
| :--- | :--- |
| **注意力头 (Attention Heads)** | 主要负责**信息路由与过滤**。特定类型的注意力头（如 Induction Heads）通过复制上文信息，直接增加目标 Token 的概率。此外，研究发现了“复制抑制（Copy Suppression）”机制 [9]，即某些注意力头会主动降低已出现 Token 的概率，以避免重复生成，从而动态调整概率分布。 |
| **MLP 层 (Feed-Forward Networks)** | 被广泛认为是模型的**知识存储库（Knowledge Store）** [10]。MLP 层通过将输入映射到高维空间，提取并注入事实性知识。在逐层解码中，MLP 层的激活往往对应着特定概念或事实的浮现，直接推动相关 Token 概率的上升。 |

## 5. 残差流视角与中间层“冻结”现象

从残差流（Residual Stream）的视角来看，概率分布的演变揭示了 LLM 内部信息处理的非均匀性。

一项名为 *Frozen in the Middle* 的最新研究 [11] 揭示了一个反直觉的现象：在处理关系抽取等任务时，主语 Token 的隐藏状态在跨越数十个中间层时**保持基本不变（Frozen）**。这意味着，尽管中间层已经包含了生成最终预测所需的所有事实信息，但模型会刻意“忽略”这些信息，直到到达特定的深层网络时，才突然进行信息交换并迅速完成概率分布的锐化。这种“中间层停滞”现象表明，概率分布的演变在某些任务中呈现出阶跃式的特征，而非平滑的渐进过程。

## 6. 复杂任务中的非线性演变与隐式推理

对于复杂的推理任务，概率的演变并非总是单调的锐化，而是呈现出高度的动态性。

* **内部思维链（Internal Chain-of-Thought）**：研究表明，LLM 在处理复合任务时，会在不同的网络深度依次分解并执行子任务 [12]。这种层级的子任务调度导致了概率分布在中间层的反复震荡。
* **隐式推理（Implicit Reasoning）的崛起**：最新的推理模型研究（如 Meta 的 COCONUT [13] 和 Soft Thinking [14]）探索了在连续的潜在空间（Latent Space）中进行推理。在这些范式中，模型不再依赖离散的 Token 输出，而是利用最后一个隐藏状态作为“连续思维”。在这种模式下，中间层的概率分布失去了传统的语义对应关系，演变为一种纯粹的内部计算状态，直到推理结束时才映射回高度锐化的离散 Token 概率分布。

## 7. 深度效率与早退出（Early-Exit）的困境

基于“中间层已经能预测出正确 token”的观察，许多研究提出了 Early-Exit（早退出）机制：如果中间层的概率分布已经足够锐化，就提前终止计算以节省算力。

然而，最新的深度效率（Depth Efficiency）研究对这一机制提出了挑战。斯坦福大学的研究 [15] 表明，现代 LLM 并没有完全高效地利用其深度。通过分析层间的余弦相似度，研究者发现模型往往只是将相似的计算“拉长”分布在多个层中。尽管如此，由于真正的“残差锐化”和置信度校准往往发生在最后几层，Early-Exit 的收益正在递减 [16]。跳过最后几层不仅会降低准确率，还会严重破坏模型输出的校准度，因为模型越来越依赖最后几层的锐化过程来确保输出的可靠性。

## 8. 总结

LLM 每一层的解码概率确实是一个**从高熵（平缓、混乱）到低熵（锐化、集中）的演变过程**。综合最新研究，这一过程具有以下核心特征：

1. **非线性与阶段性**：演变过程遵循“猜测-精炼”框架，早期层进行基于频率的统计猜测，中间层进行特征提取和知识注入（有时伴随状态冻结），最后几层执行关键的残差锐化。
2. **组件协同**：注意力头负责上下文信息的路由与抑制，MLP 层负责事实知识的提取，两者共同塑造了概率分布的动态变化。
3. **任务依赖性**：在简单任务中，概率分布可能较早收敛；而在复杂推理或隐式推理任务中，概率分布会在中间层经历剧烈的震荡或转化为连续的潜在状态，直到最后阶段才完成锐化。

这种逐层锐化的机制，既是 LLM 强大表现的基础，也是目前模型可解释性（Interpretability）、推理加速（Inference Acceleration）以及下一代隐式推理模型研究的核心焦点。

---
### 参考文献

[1] nostalgebraist, "interpreting GPT: the logit lens," LessWrong, 2020. [Online]. Available: https://www.lesswrong.com/posts/AcKRB8wDpdaN6v6ru/interpreting-gpt-the-logit-lens  
[2] N. Belrose et al., "Eliciting Latent Predictions from Transformers with the Tuned Lens," arXiv:2303.08112, 2023.  
[3] R. Ali et al., "Entropy-Lens: Uncovering Decision Strategies in LLMs," arXiv:2502.16570, 2026.  
[4] V. Lad et al., "The Remarkable Robustness of LLMs: Stages of Inference?," arXiv:2406.19384, 2024.  
[5] A. Gupta et al., "How Do LLMs Use Their Depth?," arXiv:2510.18871, 2025.  
[6] A. Joshi, A. Ahmad, and A. Modi, "Calibration Across Layers: Understanding Calibration Evolution in LLMs," arXiv:2511.00280, 2025.  
[7] C. Yang, S. Li, and A. Holtzman, "LLM Probability Concentration: How Alignment Shrinks the Generative Horizon," arXiv:2506.17871, 2025.  
[8] W. Tan et al., "Restoring Exploration after Post-Training: Latent Exploration Decoding for Large Reasoning Models," arXiv:2602.01698, 2026.  
[9] C. McDougall et al., "Copy Suppression: Comprehensively Understanding an Attention Head," arXiv:2310.04625, 2023.  
[10] D. Dai et al., "Knowledge Neurons in Pretrained Transformers," ACL, 2022.  
[11] P. Tikhonov and D. Ilvovsky, "Frozen in the Middle: Hidden States Remain Unchanged Across Intermediate Layers of Language Models," ACM, 2025.  
[12] Z. Yang et al., "Internal Chain-of-Thought: Empirical Evidence for Layer-wise Subtask Scheduling in LLMs," EMNLP, 2025.  
[13] S. Hao et al., "Training Large Language Models to Reason in a Continuous Latent Space," arXiv:2412.06769, 2024.  
[14] Y. Xu et al., "Soft Thinking: Unlocking the Reasoning Potential of LLMs in Continuous Space," arXiv:2505.15778, 2025.  
[15] R. Csordás, C. D. Manning, and C. Potts, "Do Language Models Use Their Depth Efficiently?," arXiv:2505.13898, 2025.  
[16] R. Wei et al., "The Diminishing Returns of Early-Exit Decoding in Modern LLMs," arXiv:2603.23701, 2026.
