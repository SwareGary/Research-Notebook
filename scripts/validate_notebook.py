#!/usr/bin/env python3
"""只读检查科研 Notebook 的结构、语法和可读性提示。"""

import argparse
import ast
import json
import re
import sys
from pathlib import Path


SECTION_MARKERS = {
    "输入或数据说明": ("输入", "原始数据", "数据清单", "input", "raw data", "dataset"),
    "方法或来源说明": ("研究依据", "方法", "参数来源", "文献", "method", "source", "reference"),
    "质量检查": ("质量检查", "质检", "缺失", "异常", "quality", "validation", "missing"),
    "结果或输出说明": ("结果", "输出", "图表", "result", "output", "figure", "table"),
    "结果索引或运行摘要": ("结果索引", "输出索引", "运行摘要", "result index", "output index", "run summary"),
}

DISPLAY_MARKERS = (
    "display(",
    "plt.show(",
    "Image(",
    ".head(",
    ".plot(",
)

EXPORT_MARKERS = (
    "savefig(",
    ".to_csv(",
    ".to_excel(",
    ".to_parquet(",
    ".to_netcdf(",
)

ENGINEERING_IMPORTS = {
    "argparse",
    "click",
    "dataclasses",
    "dependency_injector",
    "hydra",
    "pydantic",
    "typer",
}


def read_notebook(path, errors):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"文件不存在：{path}")
    except UnicodeDecodeError as exc:
        errors.append(f"文件不是有效的 UTF-8 文本：{exc}")
    except json.JSONDecodeError as exc:
        errors.append(f"Notebook JSON 无法解析：第 {exc.lineno} 行，第 {exc.colno} 列")
    return None


def is_main_guard(node):
    if not isinstance(node, ast.If):
        return False
    test = node.test
    if not isinstance(test, ast.Compare) or len(test.ops) != 1:
        return False
    left = test.left
    right = test.comparators[0]
    return (
        isinstance(test.ops[0], ast.Eq)
        and isinstance(left, ast.Name)
        and left.id == "__name__"
        and isinstance(right, ast.Constant)
        and right.value == "__main__"
    )


def has_annotations(node):
    if getattr(node, "returns", None) is not None:
        return True
    arguments = node.args
    all_args = arguments.posonlyargs + arguments.args + arguments.kwonlyargs
    if arguments.vararg is not None:
        all_args.append(arguments.vararg)
    if arguments.kwarg is not None:
        all_args.append(arguments.kwarg)
    return any(argument.annotation is not None for argument in all_args)


def local_module_exists(module_name, notebook_dir):
    if not module_name:
        return False
    root_name = module_name.split(".")[0]
    return (
        (notebook_dir / f"{root_name}.py").exists()
        or (notebook_dir / root_name / "__init__.py").exists()
    )


def inspect_code_cells(cells, notebook_dir, errors, warnings, passes):
    code_cells = []
    execution_counts = []
    class_cells = set()
    decorator_cells = set()
    annotation_cells = set()
    private_function_cells = set()
    main_guard_cells = set()
    engineering_imports = set()
    local_imports = set()

    for cell_number, cell in enumerate(cells, start=1):
        if cell.get("cell_type") != "code":
            continue

        source = "".join(cell.get("source", []))
        code_cells.append((cell_number, source))

        count = cell.get("execution_count")
        if isinstance(count, int):
            execution_counts.append((cell_number, count))

        try:
            tree = ast.parse(source, filename=f"cell-{cell_number}")
        except SyntaxError as exc:
            errors.append(
                f"第 {cell_number} 个单元存在 Python 语法错误："
                f"第 {exc.lineno} 行，{exc.msg}"
            )
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_cells.add(cell_number)
                if node.decorator_list:
                    decorator_cells.add(cell_number)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.decorator_list:
                    decorator_cells.add(cell_number)
                if has_annotations(node):
                    annotation_cells.add(cell_number)
                if node.name.startswith("_") and not node.name.startswith("__"):
                    private_function_cells.add(cell_number)
            elif isinstance(node, ast.AnnAssign):
                annotation_cells.add(cell_number)
            elif is_main_guard(node):
                main_guard_cells.add(cell_number)
            elif isinstance(node, ast.Import):
                for item in node.names:
                    root_name = item.name.split(".")[0]
                    if root_name in ENGINEERING_IMPORTS:
                        engineering_imports.add(root_name)
                    if local_module_exists(item.name, notebook_dir):
                        local_imports.add(item.name)
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""
                root_name = module_name.split(".")[0]
                if node.level > 0 or local_module_exists(module_name, notebook_dir):
                    local_imports.add("." * node.level + module_name)
                if root_name in ENGINEERING_IMPORTS:
                    engineering_imports.add(root_name)

    if not code_cells:
        errors.append("没有找到代码单元。")
        return ""

    passes.append(f"找到 {len(code_cells)} 个代码单元。")

    if len(execution_counts) >= 2:
        counts = [count for _, count in execution_counts]
        if counts != sorted(counts) or len(counts) != len(set(counts)):
            warnings.append("已有执行编号未按单元顺序递增，建议使用新内核从上到下运行。")
        else:
            passes.append("已有执行编号按单元顺序递增。")
    else:
        warnings.append("执行编号较少，尚不能确认 Notebook 已按顺序完整运行。")

    if class_cells:
        warnings.append(f"以下单元定义了类，请确认其确实有助于理解：{sorted(class_cells)}")
    if decorator_cells:
        warnings.append(f"以下单元使用了装饰器，请确认抽象收益：{sorted(decorator_cells)}")
    if annotation_cells:
        warnings.append(f"以下单元包含类型标注，请确认其阅读价值：{sorted(annotation_cells)}")
    if private_function_cells:
        warnings.append(f"以下单元定义了私有风格函数，请确认命名足够直观：{sorted(private_function_cells)}")
    if main_guard_cells:
        warnings.append(f"以下单元使用了脚本入口结构，Notebook 通常可直接线性执行：{sorted(main_guard_cells)}")
    if engineering_imports:
        warnings.append("发现可能增加结构层次的依赖：" + ", ".join(sorted(engineering_imports)))
    if local_imports:
        warnings.append("发现相对或同目录 Python 模块依赖：" + ", ".join(sorted(local_imports)))

    code_text = "\n".join(source for _, source in code_cells)
    if any(marker in code_text for marker in DISPLAY_MARKERS):
        passes.append("代码中包含就地展示操作。")
    else:
        warnings.append("没有识别到数据、表格或图片的就地展示操作。")

    if any(marker in code_text for marker in EXPORT_MARKERS):
        passes.append("代码中包含结果导出操作。")
    else:
        warnings.append("没有识别到常见的表格或图片导出操作。")

    if "plt." in code_text and "savefig(" in code_text:
        has_inline_figure = "plt.show(" in code_text or "display(" in code_text
        if has_inline_figure:
            passes.append("绘图代码同时包含保存和内嵌展示操作。")
        else:
            warnings.append("发现图片保存代码，但没有识别到内嵌展示操作。")

    return code_text


def inspect_markdown(cells, warnings, passes):
    markdown_cells = [
        "".join(cell.get("source", []))
        for cell in cells
        if cell.get("cell_type") == "markdown"
    ]

    if not markdown_cells:
        warnings.append("没有找到 Markdown 说明单元。")
        return ""

    passes.append(f"找到 {len(markdown_cells)} 个 Markdown 说明单元。")
    markdown_text = "\n".join(markdown_cells).lower()

    for section_name, markers in SECTION_MARKERS.items():
        if any(marker.lower() in markdown_text for marker in markers):
            passes.append(f"已识别：{section_name}。")
        else:
            warnings.append(f"没有识别到明确的{section_name}。")

    headings = re.findall(r"(?m)^#{1,6}\s+.+$", markdown_text)
    if len(headings) >= 3:
        passes.append(f"Markdown 中包含 {len(headings)} 个分节标题。")
    else:
        warnings.append("Markdown 分节较少，研究流程可能不易定位。")

    return markdown_text


def validate_notebook(path):
    errors = []
    warnings = []
    passes = []

    notebook = read_notebook(path, errors)
    if notebook is None:
        return errors, warnings, passes

    cells = notebook.get("cells")
    if not isinstance(cells, list):
        errors.append("Notebook 缺少有效的 cells 列表。")
        return errors, warnings, passes

    passes.append("Notebook JSON 可以正常解析。")
    if notebook.get("nbformat") == 4:
        passes.append("Notebook 使用 nbformat 4。")
    else:
        warnings.append("Notebook 未声明常用的 nbformat 4。")

    inspect_markdown(cells, warnings, passes)
    inspect_code_cells(cells, path.parent, errors, warnings, passes)
    return errors, warnings, passes


def print_report(path, errors, warnings, passes):
    print(f"检查文件：{path}")
    print()

    for message in passes:
        print(f"[通过] {message}")
    for message in warnings:
        print(f"[警告] {message}")
    for message in errors:
        print(f"[错误] {message}")

    print()
    print(f"汇总：{len(passes)} 项通过，{len(warnings)} 项警告，{len(errors)} 项错误。")


def main():
    parser = argparse.ArgumentParser(
        description="只读检查科研 Notebook 的结构、语法和可读性提示。"
    )
    parser.add_argument("notebook", help="需要检查的 .ipynb 文件")
    args = parser.parse_args()

    notebook_path = Path(args.notebook).expanduser().resolve()
    errors, warnings, passes = validate_notebook(notebook_path)
    print_report(notebook_path, errors, warnings, passes)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
