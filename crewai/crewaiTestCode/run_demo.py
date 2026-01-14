import argparse
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


def _safe_format(template: str, values: dict[str, Any]) -> str:
    return template.format_map(defaultdict(str, values))


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def offline_pipeline(requirement: str, output_filename: str) -> str:
    _ = offline_generate_spec(requirement)
    code = offline_generate_code(output_filename)
    return offline_review_code(code)


def offline_generate_spec(requirement: str) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return "\n".join(
        [
            f"需求：{requirement}",
            f"时间：{now}",
            "",
            "功能拆分：",
            "- 添加任务",
            "- 删除任务",
            "- 标记完成",
            "- 列表展示",
            "- JSON 保存/加载",
            "",
            "关键设计：",
            "- TodoItem(id:int, text:str, done:bool, created_at:str, done_at:str|None)",
            "- TodoList(storage_path:Path) 负责内存与持久化",
            "- CLI 使用 argparse 子命令 add/list/done/remove",
            "",
            "边界与错误：",
            "- JSON 文件不存在：视为空列表",
            "- JSON 损坏：报错并提示备份/重建",
            "- 删除/完成不存在的 id：提示并返回非 0",
            "- 写入采用临时文件 + 原子替换",
            "",
            "验收标准：",
            "- add 后 list 能看到新增项",
            "- done 后 list 显示已完成且记录完成时间",
            "- remove 后 list 不再出现该项",
            "- save/load 可跨进程保持一致",
        ]
    )


def offline_generate_code(output_filename: str) -> str:
    return f'''from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class TodoItem:
    id: int
    text: str
    done: bool
    created_at: str
    done_at: str | None


class TodoList:
    def __init__(self, storage_path: Path) -> None:
        self._storage_path = storage_path
        self._items: list[TodoItem] = []
        self._next_id = 1
        self.load()

    def add(self, text: str) -> TodoItem:
        text = text.strip()
        if not text:
            raise ValueError("任务内容不能为空")
        item = TodoItem(
            id=self._next_id,
            text=text,
            done=False,
            created_at=_now_iso(),
            done_at=None,
        )
        self._items.append(item)
        self._next_id += 1
        self.save()
        return item

    def remove(self, item_id: int) -> bool:
        before = len(self._items)
        self._items = [x for x in self._items if x.id != item_id]
        changed = len(self._items) != before
        if changed:
            self.save()
        return changed

    def mark_done(self, item_id: int) -> bool:
        changed = False
        new_items: list[TodoItem] = []
        for x in self._items:
            if x.id != item_id:
                new_items.append(x)
                continue
            if x.done:
                new_items.append(x)
                continue
            new_items.append(
                TodoItem(
                    id=x.id,
                    text=x.text,
                    done=True,
                    created_at=x.created_at,
                    done_at=_now_iso(),
                )
            )
            changed = True
        self._items = new_items
        if changed:
            self.save()
        return changed

    def list(self, show_all: bool = True) -> list[TodoItem]:
        if show_all:
            return list(self._items)
        return [x for x in self._items if not x.done]

    def load(self) -> None:
        if not self._storage_path.exists():
            self._items = []
            self._next_id = 1
            return
        try:
            raw = json.loads(self._storage_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 文件损坏：{{self._storage_path}}") from e

        items = raw.get("items", [])
        if not isinstance(items, list):
            raise ValueError("JSON 格式不正确：items 必须是数组")

        parsed: list[TodoItem] = []
        max_id = 0
        for obj in items:
            if not isinstance(obj, dict):
                continue
            item_id = int(obj.get("id", 0))
            text = str(obj.get("text", "")).strip()
            done = bool(obj.get("done", False))
            created_at = str(obj.get("created_at", "")).strip() or _now_iso()
            done_at_value = obj.get("done_at", None)
            done_at = str(done_at_value).strip() if done_at_value else None
            if item_id <= 0 or not text:
                continue
            parsed.append(
                TodoItem(
                    id=item_id,
                    text=text,
                    done=done,
                    created_at=created_at,
                    done_at=done_at,
                )
            )
            max_id = max(max_id, item_id)
        self._items = sorted(parsed, key=lambda x: x.id)
        self._next_id = max_id + 1

    def save(self) -> None:
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._storage_path.with_suffix(self._storage_path.suffix + ".tmp")
        payload: dict[str, Any] = {{
            "items": [
                {{
                    "id": x.id,
                    "text": x.text,
                    "done": x.done,
                    "created_at": x.created_at,
                    "done_at": x.done_at,
                }}
                for x in self._items
            ]
        }}
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
        os.replace(tmp_path, self._storage_path)


def _print_items(items: list[TodoItem]) -> None:
    for x in items:
        status = "已完成" if x.done else "未完成"
        done_at = x.done_at or ""
        print(f"{{x.id}}\\t{{status}}\\t{{x.text}}\\t{{x.created_at}}\\t{{done_at}}")


def main() -> int:
    parser = argparse.ArgumentParser(prog="{output_filename}")
    parser.add_argument("--storage", default=str(Path.cwd() / "todo.json"))
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add")
    p_add.add_argument("text")

    p_list = sub.add_parser("list")
    p_list.add_argument("--pending-only", action="store_true")

    p_done = sub.add_parser("done")
    p_done.add_argument("id", type=int)

    p_remove = sub.add_parser("remove")
    p_remove.add_argument("id", type=int)

    args = parser.parse_args()
    todo = TodoList(Path(args.storage))

    try:
        if args.cmd == "add":
            item = todo.add(args.text)
            print(item.id)
            return 0
        if args.cmd == "list":
            items = todo.list(show_all=not args.pending_only)
            _print_items(items)
            return 0
        if args.cmd == "done":
            ok = todo.mark_done(args.id)
            if not ok:
                print("未找到该任务 id")
                return 1
            return 0
        if args.cmd == "remove":
            ok = todo.remove(args.id)
            if not ok:
                print("未找到该任务 id")
                return 1
            return 0
    except Exception as e:
        print(str(e))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def offline_review_code(code: str) -> str:
    return code


def build_agents(agents_config: dict[str, Any], model: str) -> dict[str, Any]:
    from crewai import Agent, LLM

    agents: dict[str, Any] = {}
    llm = LLM(model=model)
    for name, cfg in agents_config.get("agents", {}).items():
        agents[name] = Agent(
            role=cfg["role"],
            goal=cfg["goal"],
            backstory=cfg["backstory"],
            allow_delegation=bool(cfg.get("allow_delegation", False)),
            verbose=bool(cfg.get("verbose", False)),
            llm=llm,
        )
    return agents


def build_tasks(
    tasks_config: dict[str, Any],
    agents_by_name: dict[str, Any],
    inputs: dict[str, Any],
) -> list[Any]:
    from crewai import Task

    tasks: list[Any] = []
    for cfg in tasks_config.get("tasks", []):
        agent_name = cfg["agent"]
        agent = agents_by_name[agent_name]
        tasks.append(
            Task(
                description=_safe_format(cfg["description"], inputs),
                expected_output=_safe_format(cfg["expected_output"], inputs),
                agent=agent,
            )
        )
    return tasks


def kickoff(crew: Any, inputs: dict[str, Any]) -> Any:
    if hasattr(crew, "kickoff"):
        return crew.kickoff(inputs=inputs)
    if hasattr(crew, "run"):
        return crew.run(input=inputs)
    raise RuntimeError("未找到可用的 Crew 启动方法（kickoff/run）。")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "requirement",
        nargs="?",
        default="写一个最小的 TODO 清单管理器，支持添加、完成、删除、列表展示，并能保存/加载到 JSON 文件。",
    )
    parser.add_argument("--output-filename", default="generated_todo.py")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--model",
        default="",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).parent
    crew_home = base_dir / ".crewai_home"
    crew_home.mkdir(parents=True, exist_ok=True)
    os.environ["HOME"] = str(crew_home)

    # 读取 .env 与 runtime.yaml
    env_path = base_dir / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            os.environ.setdefault(k, v)
    runtime_yaml = base_dir / "config" / "runtime.yaml"
    runtime: dict[str, Any] = {}
    if runtime_yaml.exists():
        try:
            runtime = yaml.safe_load(runtime_yaml.read_text(encoding="utf-8")) or {}
        except Exception:
            runtime = {}
    runtime_model = str(runtime.get("model", "")).strip()
    runtime_key = str(runtime.get("OPENAI_API_KEY", "")).strip()
    runtime_base_url = str(runtime.get("OPENAI_BASE_URL", "")).strip()

    if runtime_key:
        os.environ.setdefault("OPENAI_API_KEY", runtime_key)
    if runtime_base_url:
        os.environ.setdefault("OPENAI_BASE_URL", runtime_base_url)

    args.model = (
        args.model
        or os.environ.get("CREWAI_MODEL", "").strip()
        or runtime_model
    )
    if args.model:
        os.environ.setdefault("CREWAI_MODEL", args.model)

    if args.dry_run:
        agents_cfg = load_yaml(base_dir / "config" / "agents.yaml")
        tasks_cfg = load_yaml(base_dir / "config" / "tasks.yaml")
        print("Agents:")
        for name in agents_cfg.get("agents", {}).keys():
            print(f"- {name}")
        print("Tasks:")
        for cfg in tasks_cfg.get("tasks", []):
            print(f'- {cfg.get("name","")}: {cfg.get("agent","")}')
        print("Config:")
        print(f'- model: {args.model or "(未设置)"}')
        print(f'- OPENAI_BASE_URL: {os.environ.get("OPENAI_BASE_URL","") or "(默认)"}')
        print(f'- OPENAI_API_KEY: {"(已设置)" if os.environ.get("OPENAI_API_KEY") else "(未设置)"}')
        return 0

    if args.offline:
        text = offline_pipeline(args.requirement, args.output_filename).strip()
        if args.write:
            out_dir = base_dir / "out"
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / args.output_filename
            out_path.write_text(text + "\n", encoding="utf-8")
            print(str(out_path))
        else:
            print(text)
        return 0

    if not os.environ.get("OPENAI_API_KEY"):
        print("请先设置环境变量 OPENAI_API_KEY，然后再运行该示例。")
        print('示例：export OPENAI_API_KEY="你的key"')
        return 2
    if not args.model:
        print("请指定可用模型名：--model 或设置 CREWAI_MODEL。")
        return 2

    agents_cfg = load_yaml(base_dir / "config" / "agents.yaml")
    tasks_cfg = load_yaml(base_dir / "config" / "tasks.yaml")

    inputs: dict[str, Any] = {
        "user_requirement": args.requirement,
        "output_filename": args.output_filename,
    }

    agents_by_name = build_agents(agents_cfg, args.model)
    tasks = build_tasks(tasks_cfg, agents_by_name, inputs)

    from crewai import Crew, Process

    crew = Crew(
        agents=list(agents_by_name.values()),
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )

    try:
        result = kickoff(crew, inputs)
    except Exception as e:
        print("运行失败：模型不可用或网络/权限异常。")
        print(f"当前 model={args.model}")
        print("可尝试：")
        print('- 通过参数指定可用模型：--model "你的模型名"')
        print('- 或设置环境变量：export CREWAI_MODEL="你的模型名"')
        print(str(e))
        return 3
    text = str(result).strip()

    if args.write:
        out_dir = base_dir / "out"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / args.output_filename
        out_path.write_text(text + "\n", encoding="utf-8")
        print(str(out_path))
    else:
        print(text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
