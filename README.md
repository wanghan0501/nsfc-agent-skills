# NSFC申请书撰写辅助智能体技能包

这是一个专为 NSFC 申请书撰写设计的 Agent Skills 集合，帮助科研人员提高申请书质量，涵盖写作指导、图表制作、文献管理和政策速查等核心环节。

## 📦 技能包概览

本项目包含 4 个专业技能，每个技能都可以独立使用：

| 技能名称 | 功能简介 | 适用场景 |
|---------|---------|---------|
| **[nsfc-write](./plugins/nsfc/skills/nsfc-write/SKILL.md)** | NSFC 申请书撰写指南 | 选题、摘要、立项依据、研究内容、研究方案、创新性分析等各部分撰写 |
| **[nsfc-figure](./plugins/nsfc/skills/nsfc-figure/SKILL.md)** | NSFC 申请书图表制作指南 | 概念图、技术路线图、研究内容关系图、甘特图等专业图表制作 |
| **[nsfc-literature](./plugins/nsfc/skills/nsfc-literature/SKILL.md)** | NSFC 申请书文献检索与引用 | 使用 OpenAlex API 检索文献，使用 wenxian 生成标准引用格式 |
| **[nsfc-policy](./plugins/nsfc/skills/nsfc-policy/SKILL.md)** | NSFC 2026 年度申报政策速查 | 限项规定、AI 使用规范、申请代码、项目类型、结构改革等政策信息 |

## 🚀 在 OpenClaw 中使用

本项目遵循 [Agent Skills](https://agentskills.io) 规范，这是一个为 AI 智能体设计的结构化知识库格式。每个技能都是一个包含 `SKILL.md` 文件的目录，文件中包含 YAML frontmatter 和 Markdown 格式的指导内容。

可以直接让OpenClaw安装这些技能，如“安装https://github.com/njzjz/nsfc-agent-skills/ 这个skill”。

## 🧩 在 Claude Code 中安装（Plugin 市场）

本仓库同时是一个 Claude Code 插件市场（marketplace），4 个技能打包为名为 `nsfc` 的插件。

### 安装步骤

**第 1 步：添加插件市场**

在 Claude Code 会话中输入：

```
/plugin marketplace add wanghan0501/nsfc-agent-skills
```

> `wanghan0501/nsfc-agent-skills` 是 GitHub 的 `owner/repo` 简写。也可用完整 Git 地址：
> `/plugin marketplace add https://github.com/wanghan0501/nsfc-agent-skills.git`

**第 2 步：安装插件**

```
/plugin install nsfc@nsfc-agent-skills
```

格式为 `插件名@市场名`，即安装 `nsfc-agent-skills` 市场中的 `nsfc` 插件。

**第 3 步：确认生效**

新装插件可能需要重新加载才能在当前会话生效：

```
/reload-plugins
```

也可运行 `/plugin` 打开插件管理界面，查看 `nsfc` 是否已启用。

### 安装后如何使用

安装后**无需手动调用**——撰写 NSFC 申请书时，Claude 会根据任务自动选用对应技能（写作 / 图表 / 文献 / 政策）。直接描述需求即可，例如：

- “帮我写青年基金的立项依据”→ 触发 `nsfc-write`
- “画一张技术路线图”→ 触发 `nsfc-figure`
- “检索这个方向近 5 年的代表文献”→ 触发 `nsfc-literature`

### 卸载

```
/plugin uninstall nsfc@nsfc-agent-skills
```

### 开发者：本地调试与校验

无需发布即可在本地仓库测试，或在发布前校验清单格式：

```bash
# 直接以本地目录加载插件运行
claude --plugin-dir /path/to/nsfc-agent-skills

# 校验 marketplace.json / plugin.json 格式
claude plugin validate /path/to/nsfc-agent-skills
```

## ⚠️ 免责声明

- 本技能包仅供学习和参考，不保证申请成功
- 请务必遵守 NSFC 的科研诚信要求和 AI 使用规范
- 不得使用 AI 直接生成申请书，必须人工核实所有内容
- 政策信息以基金委当年官方指南为准
