from __future__ import annotations

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
            raise ValueError(f"JSON 文件损坏：{self._storage_path}") from e

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
        payload: dict[str, Any] = {
            "items": [
                {
                    "id": x.id,
                    "text": x.text,
                    "done": x.done,
                    "created_at": x.created_at,
                    "done_at": x.done_at,
                }
                for x in self._items
            ]
        }
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp_path, self._storage_path)


def _print_items(items: list[TodoItem]) -> None:
    for x in items:
        status = "已完成" if x.done else "未完成"
        done_at = x.done_at or ""
        print(f"{x.id}\t{status}\t{x.text}\t{x.created_at}\t{done_at}")


def main() -> int:
    parser = argparse.ArgumentParser(prog="generated_todo.py")
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
