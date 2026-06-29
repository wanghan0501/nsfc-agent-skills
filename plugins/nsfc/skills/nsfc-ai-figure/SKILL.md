---
name: nsfc-ai-figure
description: NSFC申请书AI绘图指南。通过Grsai文生图API（nano-banana-pro / gpt-image-2）生成概念示意图、机理插画、材料与器件结构图、应用场景效果图等插画式图表。含提示词工程模板、API调用脚本（同步+异步轮询）与设计原则。适用于nsfc-figure（Mermaid/matplotlib代码绘图）无法覆盖的、以视觉表达为主、文字标签较少的科研插图。
version: 0.1.0
---

# NSFC 申请书 AI 绘图指南

通过 **Grsai 文生图 API**（模型 `nano-banana-pro`、`gpt-image-2`）为申请书生成高质量科研插画。与 [[nsfc-figure]]（代码绘图）分工互补。

---

## 适用边界（先读这一节）

文生图模型对**中文文字、箭头标签、精确节点布局**控制力差——硬把含大量中文标签的逻辑流程图交给 AI，几乎必然乱码、错字、结构错乱。

**✅ 适合 AI 生成（视觉为主、文字少）**：
- 概念示意图 / 研究思路总览图（视觉主体）
- 机理插画：分子/晶体/反应机理、细胞通路、器官结构
- 器件/装置剖面图、能量/物质流示意
- 材料微观结构（3D 渲染、等距视角）
- 应用场景效果图（临床、工程现场、环境场景）
- 研究基础中的可视化背景图

**❌ 不适合，请用 [[nsfc-figure]]（Mermaid / matplotlib）**：
- 研究内容关系图（层层递进/并行支撑/闭环迭代）
- 技术路线流程图（带文字节点和箭头）
- 年度计划甘特图
- 任何依赖精确中文标签排版的逻辑图

**推荐工作流**：AI 生成视觉主体（无文字）→ PowerPoint / Keynote / PS 叠加中文标注与箭头。兼顾美感与可控性。

---

## 与 nsfc-figure 的分工

| 维度 | nsfc-figure（代码绘图） | nsfc-ai-figure（AI 绘图） |
|------|----------------------|------------------------|
| 擅长 | 流程图、关系图、甘特图、逻辑链 | 概念插画、机理图、场景效果图 |
| 文字标签 | 精确可控 | 差，易乱码 |
| 布局精度 | 高（节点/箭头可控） | 低（构图不可精确控制） |
| 美感/视觉冲击 | 一般 | 高 |
| 可复现/可改 | 强（改代码即可） | 弱（每次生成不同） |
| 速度 | 快 | 慢（需生成+挑选） |

**策略**：逻辑结构用代码图，视觉表现用 AI 图，二者风格统一后并存。

---

## 模型选择

| 模型 | 适用 | 比例参数 | 分辨率 | 特性 |
|------|------|---------|--------|------|
| `gpt-image-2`（**默认/推荐**） | 概念图、结构示意、写实场景、图生图编辑 | `aspectRatio`: `1024x1024` `1536x1024` `1024x1536` `1792x1024` `1024x1792` | 像素级 | 稳定可靠、支持 `images` 输入做修改/扩展 |
| `nano-banana-pro` | 风格化插画（**部分账号不可用——若超时或报 `generate failed`，改用 gpt-image-2**） | `aspectRatio`: `1:1` `16:9` `9:16` `4:3` `3:4` | `imageSize`: `1K` | 风格化强；可用时出图快 |

纯文生图与图生图均**默认 `gpt-image-2`**（实测稳定）。图生图编辑时 `images` 参数传图 URL。账号若开通 `nano-banana-pro`，可用其做风格化插画，但部分账号不可用。

---

## API 概要

**基础节点**（二选一）：
- `https://grsaiapi.com`（全球节点）
- `https://grsai.dakka.com.cn`（国内节点，**默认**，国内访问更稳）

**鉴权**：`Authorization: Bearer sk-xxxxxxxxxxx`（申请的 API Key）。

> 🔑 **本技能不内置密钥**。运行前请先申请 Grsai API Key，并通过环境变量 `GRSAI_API_KEY` 提供，或用 `--api-key` 参数传入：
> ```bash
> export GRSAI_API_KEY=sk-xxxxxxxxxxxx
> ```
> ⚠️ 切勿把真实密钥写进脚本或提交到版本库；密钥泄露请立即在 Grsai 后台轮换。

### 1. 生成接口 `POST {base}/v1/api/generate`

**nano-banana-pro 请求体**：
```json
{
    "model": "nano-banana-pro",
    "prompt": "提示词",
    "images": [],
    "aspectRatio": "16:9",
    "imageSize": "1K",
    "replyType": "json"
}
```

**gpt-image-2 请求体**：
```json
{
    "model": "gpt-image-2",
    "prompt": "提示词",
    "images": ["https://example.com/input.png"],
    "aspectRatio": "1536x1024",
    "replyType": "json"
}
```

**同步成功响应**：
```json
{
    "id": "14-5f3cf761-a4bb-486a-8016-77f490998f80",
    "status": "succeeded",
    "results": [{"url": "https://file1.aitohumanize.com/file/xxx.png"}]
}
```

若 `status` 非 succeeded（异步任务），用返回的 `id` 轮询下一个接口。

### 2. 异步结果查询 `GET {base}/v1/api/result?id={id}`

```bash
curl --request GET 'https://grsaiapi.com/v1/api/result?id=1-6634fd9a-3086-4d92-9436-69e86fd23bf8' \
  --header 'Authorization: Bearer sk-xxxxxxxxxxx'
```

响应结构与同步一致；`status` 为 `succeeded` 即可取 `results[0].url` 下载。

---

## 使用方法（脚本）

脚本封装了「请求 → 同步/异步处理 → 下载」全流程：

```bash
# 先设置 API Key（环境变量）
export GRSAI_API_KEY=sk-xxxxxxxxxxxx

# 文生图（gpt-image-2，默认模型，国内节点）
uv run scripts/generate_image.py \
  --prompt "perovskite solar cell multilayer cross-section, isometric 3D render, blue-purple tech palette, no text no labels" \
  --aspect-ratio 1536x1024 \
  --output concept.png

# 用 gpt-image-2，像素级比例
uv run scripts/generate_image.py \
  --prompt "..." \
  --model gpt-image-2 \
  --aspect-ratio 1536x1024 \
  --output concept.png

# 图生图编辑（传入参考图）
uv run scripts/generate_image.py \
  --prompt "将器件结构改为三层堆叠，保持风格" \
  --model gpt-image-2 \
  --images ref1.png ref2.png \
  --output edited.png

# 国内节点
uv run scripts/generate_image.py \
  --base https://grsai.dakka.com.cn \
  --prompt "..." --output concept.png

# 一次生成多张供挑选
uv run scripts/generate_image.py --prompt "..." -o c1.png --variants 4
```

脚本说明：
- API Key 通过 `GRSAI_API_KEY` 环境变量或 `--api-key` 提供（脚本不内置密钥）
- `--base` 切换节点（**默认国内 `https://grsai.dakka.com.cn`**，国内延迟低约 15×；海外加 `--base https://grsaiapi.com`）
- 异步任务自动轮询（默认超时 300s，`--timeout` 调整）
- `--images` 接受 http(s) URL；本地路径需先上传至可公网访问地址再传 URL
- `--variants N` 连续生成 N 张供挑选

---

## 提示词工程（核心）

### 核心原则：提示词主体 = 申请书对应段落原文

**绘图提示词的主体，就是该图要说明的那一整段 NSFC 申请书原文**——直接整段照搬，不删减、不自行改写。让模型拿到与正文完全一致的科学语境，画面才会贴着申请书的论述走，而不是 AI 自由发挥、画出「漂亮但不对题」、与正文脱节的图。

**通用结构**：

```
[NSFC 申请书中对应的完整文字段落（原文照搬）]
+ [视角/构图] + [艺术风格] + [配色] + [排除项]
```

**关键原则**：
- **整段原文照搬**：把「立项依据 / 科学问题 / 机理 / 研究内容」中与该图对应的那**一整段**贴进 prompt，完整粘贴，不要只摘几个关键词。
- **关键术语补英文**：段末附上核心术语的英文（perovskite、synapse、turbulent flow），模型对英文术语理解更准、结构更不易画错。
- **原文是给模型「读懂」、不是要它画进图里**：仍必须显式排除文字渲染（`no text, no labels, no Chinese characters`）；中文标注一律后期在 PPT/Keynote 叠加。
- 段末追加**视角**（isometric / cross-section / 3D render…）、**风格关键词**、**配色**（与申请书整体一致，见下）。

### 完整示例（钙钛矿器件机理图）

把申请书「机理」一节对应那段原文整段贴入，再在末尾追加视觉指令：

```
（NSFC 原文段落，示例）本项目拟以钙钛矿吸光层为核心构建叠层太阳能电池，
自下而上依次为透明电极、电子传输层、钙钛矿吸光层、空穴传输层与金属背电极；
光生载流子在钙钛矿层内产生后，经能级匹配的传输层定向分离与输运，
通过界面钝化抑制非辐射复合，从而提升器件开路电压与光电转换效率。

Key terms: perovskite absorber, electron/hole transport layer, tandem solar cell,
interface passivation, charge separation.

Visual directives: isometric 3D cross-section, layered device structure clearly
separated, blue-purple academic palette, scientific journal figure style.
no text, no labels, no watermark, no Chinese characters.
```

模型据此画出分层器件剖面与载流子流向的视觉主体；中文层名、箭头标注后期叠加。

### 视觉指令后缀模板（接在 NSFC 原文段落之后）

下列**不是完整 prompt**，而是贴在申请书原文段落末尾的「视角 + 风格 + 配色 + 负面词」后缀；主体内容来自原文，无需在此重复学科主体词。

**材料 / 化学**：
```
isometric 3D render, atomic-level detail, clean white background,
blue and teal academic color scheme, scientific journal figure style,
no text, no labels, no Chinese characters
```

**生命科学 / 医学**：
```
semi-realistic 3D illustration, soft cellular color palette (green/purple/blue),
cell membrane cross-section view, biomedical publication style,
no text, no labels, no Chinese characters
```

**工程 / 器件**：
```
cross-section or exploded view, layered structure clearly separated,
engineering blueprint style with clean lines, blue-grey industrial palette,
no text, no labels, no Chinese characters
```

**地学 / 环境**：
```
isometric 3D terrain with subtle scientific overlays,
earth-tone palette with blue water accents, clean composition,
no text, minimal labels, no Chinese characters
```

**信息 / AI（机理示意，非架构图）**：
```
abstract 3D network, glowing nodes and connections, dark blue tech background,
minimalist data-art style, no text, no code, no Chinese characters
```

### 风格关键词库

- 视角：isometric / cross-section / exploded view / top-down / bird's-eye / macro
- 渲染：3D render / flat illustration / line art / semi-realistic / clay style
- 氛围：scientific journal figure / academic / minimalist / clean / professional
- 配色词：blue tech / earth tones / pastel / monochrome blue / vivid scientific

### 负面提示（务必加）

```
no text, no words, no letters, no labels, no watermark, no signature,
no random characters, no UI elements, no borders
```

中文文字乱码是 NSFC 申请书 AI 配图**最常见**的扣分项，务必在提示词中排除，并在出图后人工复核擦除残留字符。

---

## 设计原则

### 配色（与全书统一）
- 调用前先确定申请书主色（参考 [[nsfc-figure]] 配色建议）
- 蓝：工程/物理/化学/信息　·　绿：生命/环境　·　暖色：能源/材料
- 在 prompt 中指定同一套配色，多张图才能统一
- 推荐：https://colorbrewer2.org

### 分辨率
- `imageSize: 1K` 起步；最终插入 Word 前确认打印效果
- 出图后可 upscale 到 300 DPI 等效
- 矢量优先不适用（AI 出的是位图）——大图宁可生成大尺寸再缩

### 构图与留白
- 主体居中、四周留白（方便后期加标注）
- 避免信息过载，一张图一个核心概念
- 风格统一：同一申请书的 AI 图用同一套风格关键词

### 科学准确性（重要）
- **AI 会画错结构**（化学键、解剖关系、装置原理都可能错）
- 生成后必须由领域专家核对，不可直接采用
- 复杂精确结构优先手绘或代码生成，AI 仅作示意性背景

---

## 推荐工作流

1. **明确科学信息**：这张图要传达什么？哪些是必须准确的？
2. **拆解视觉元素**：把文字标签剥离，只留视觉主体
3. **写提示词**：以申请书对应段落原文为主体整段照搬，段末补核心术语英文，再加视角+风格+配色+负面词
4. **生成 3-4 张**：同提示词多跑几次，挑最准、最美的一张
5. **科学核对**：结构/机理是否正确？错则改 prompt 重生成或手绘修
6. **叠加标注**：PowerPoint/Keynote 加中文标签、箭头、编号
7. **统一风格**：全书 AI 图用同一套风格与配色关键词

---

## 常见错误

- ❌ 把带中文标签的流程图/关系图交给 AI → 文字乱码、结构错乱（用 [[nsfc-figure]]）
- ❌ 提示词太笼统（「画一张科研图」）或只摘几个关键词 → 出图平庸、与正文脱节；应整段照搬申请书对应原文做主体
- ❌ 不加负面词 → 图里满是乱码字母、水印
- ❌ 不核对科学准确性 → 化学键/解剖/原理画错，评审直接扣分
- ❌ 一张图塞多个概念 → 信息过载
- ❌ 多张 AI 图风格/配色不统一 → 全书割裂
- ❌ 分辨率不足直接插入 → 打印模糊
- ❌ 全书所有图都用 AI → 该精确的逻辑图也错乱；应代码图与 AI 图混用

---

## 各类项目的 AI 配图建议

| 项目类型 | AI 图数量 | 重点 AI 图类型 |
|---------|----------|--------------|
| 青年C（30万/3年） | 1-2 张 | 概念图（视觉主体） |
| 面上（50万/4年） | 2-4 张 | 概念图、机理插画、应用效果图 |
| 重点（260万+/4年） | 3-5 张 | 概念图、结构示意、场景效果、研究基础背景图 |
| 重大研究计划 | 3-5 张 | 概念图、与计划总目标关系示意 |

> AI 图为**补充**，逻辑性图表仍以 [[nsfc-figure]] 的代码图为主。
