# Research Notebook

一个用于生成清晰、线性、可追溯结果的 Notebook 的 Agent Skill。

它面向数据分析、数值计算和科研任务，默认引导 Agent 使用单个 Jupyter Notebook 组织中小型研究项目，使研究者能够从头到尾阅读、运行、修改和核验代码。

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

如果 Agent 支持从 GitHub 安装 Skill，直接提供仓库地址：

```text
https://github.com/SwareGary/Research-Notebook
```

也可以手动克隆仓库：

```powershell
git clone https://github.com/SwareGary/Research-Notebook.git research-notebook
```

将克隆后的 `research-notebook` 文件夹放入 Agent 指定的 Skills 目录，并保留仓库的完整目录结构。安装后如未立即生效，请重新启动 Agent 或新建任务。

如果 Agent 没有 Skill 安装机制，可以直接将下面的文件作为系统提示词或任务前置提示词：

```text
references/universal-prompt.md
```

其中包含完整提示词和简短任务模板。

## 使用

Skill 标识为 `research-notebook`。调用格式由 Agent 平台决定，也可以直接输入：

```text
请使用 research-notebook，根据以下研究方法和数据生成科研 Notebook。
```

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
