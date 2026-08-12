# Research Notebook

一个用于生成清晰、线性、可追溯科研 Notebook 的 Agent Skill。

它面向数据分析、数值计算和科研复现任务，默认引导 Agent 使用单个 Jupyter Notebook 组织中小型研究项目，使研究者能够从头到尾阅读、运行、修改和核验代码。

## 主要特点

- 按研究过程从上到下组织 Notebook；
- 优先采用直观、容易理解的代码表达；
- 使用中文 Markdown 和注释解释研究含义；
- 记录数据处理、研究方法、参数和结果来源；
- 在当前步骤就地展示质检、表格和图片；
- 根据任务规模决定是否使用函数、类或多文件结构；
- 提供跨模型提示词和 Notebook 检查工具。

## 目录结构

```text
Research-Notebook/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── notebook-guidelines.md
│   └── universal-prompt.md
└── scripts/
    └── validate_notebook.py
```

## 安装

### Codex 用户级安装

安装后，该 Skill 可以在当前用户的不同项目中使用。

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.agents\skills"
git clone https://github.com/SwareGary/Research-Notebook.git "$env:USERPROFILE\.agents\skills\research-notebook"
```

如果 Codex 没有立即显示新 Skill，请重新启动 Codex 或新建一个任务。

### Codex 项目级安装

在项目根目录运行：

```powershell
New-Item -ItemType Directory -Force ".agents\skills"
git clone https://github.com/SwareGary/Research-Notebook.git ".agents\skills\research-notebook"
```

该 Skill 将随项目保存，并应用于从这个项目目录启动的 Codex 任务。

### 其他 Agent

如果 Agent 支持 Skills 或类似扩展机制，将整个仓库复制到该平台规定的 Skill 目录。

如果平台没有 Skill 安装机制，可以直接使用：

```text
references/universal-prompt.md
```

其中包含完整提示词和简短任务模板。

## 使用

在支持显式 Skill 调用的 Agent 中输入：

```text
使用 $research-notebook，根据以下研究方法和数据生成科研 Notebook。
```

仓库名称使用 `Research-Notebook`，Skill 内部名称遵循小写命名规则，调用名称为 `$research-notebook`。

## 检查 Notebook

仓库提供一个只读检查脚本：

```powershell
python scripts/validate_notebook.py path\to\notebook.ipynb
```

检查内容包括：

- Notebook JSON 和 Python 语法；
- Markdown 说明和研究流程结构；
- 单元执行顺序；
- 结果展示和导出；
- 可能增加阅读负担的代码形式。

检查脚本只输出通过项、警告和错误，不会修改 Notebook。

## 更新

进入安装目录后运行：

```powershell
git pull
```

## 许可证

本项目采用 [MIT License](LICENSE)。
