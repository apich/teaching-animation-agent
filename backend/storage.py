"""In-memory + file storage for generated teaching HTML."""
import os
import json
from datetime import datetime, timezone
from typing import Optional


class Storage:
    def __init__(self, base_dir: str = "storage"):
        self.base_dir = base_dir
        self._tasks: dict[str, dict] = {}  # in-memory task metadata
        os.makedirs(base_dir, exist_ok=True)
        os.makedirs(os.path.join(base_dir, "html"), exist_ok=True)
        os.makedirs(os.path.join(base_dir, "previews"), exist_ok=True)
        os.makedirs(os.path.join(base_dir, "metadata"), exist_ok=True)
        self._load_from_disk()  # 启动时恢复已有任务

    def _load_from_disk(self):
        """扫描磁盘，恢复已有任务的元数据"""
        # 优先从 metadata JSON 恢复
        meta_path = os.path.join(self.base_dir, "metadata", "tasks.json")
        if os.path.exists(meta_path):
            try:
                import json
                with open(meta_path, "r", encoding="utf-8") as f:
                    self._tasks = json.load(f)
                # 验证 html 文件是否存在
                html_dir = os.path.join(self.base_dir, "html")
                for tid in list(self._tasks.keys()):
                    if not os.path.exists(os.path.join(html_dir, f"{tid}.html")):
                        del self._tasks[tid]
                print(f"[storage] Loaded {len(self._tasks)} tasks from metadata", flush=True)
                return
            except Exception as e:
                print(f"[storage] Failed to load metadata: {e}", flush=True)

        # 兜底：从 html 文件重建（没有标签）
        html_dir = os.path.join(self.base_dir, "html")
        preview_dir = os.path.join(self.base_dir, "previews")
        if not os.path.isdir(html_dir):
            return
        for fname in os.listdir(html_dir):
            if not fname.endswith(".html"):
                continue
            task_id = fname.replace(".html", "")
            html_path = os.path.join(html_dir, fname)
            title = task_id[:8]
            try:
                with open(html_path, "r", encoding="utf-8") as f:
                    content = f.read(2000)
                import re
                m = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE)
                if m:
                    title = m.group(1).strip()
            except Exception:
                pass
            preview_type = None
            for ext in ["svg", "webp", "png"]:
                if os.path.exists(os.path.join(preview_dir, f"{task_id}.{ext}")):
                    preview_type = ext
                    break
            mtime = os.path.getmtime(html_path)
            from datetime import datetime, timezone
            self._tasks[task_id] = {
                "task_id": task_id,
                "prompt": title,
                "status": "completed",
                "progress": 100,
                "title": title,
                "tags": None,
                "preview_type": preview_type,
                "created_at": datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat(),
                "updated_at": datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat(),
            }
        print(f"[storage] Loaded {len(self._tasks)} tasks from disk", flush=True)

    def create_task(self, task_id: str, prompt: str) -> dict:
        task = {
            "task_id": task_id,
            "prompt": prompt,
            "status": "pending",
            "progress": 0,
            "title": None,
            "preview_type": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._tasks[task_id] = task
        return task

    def update_task(self, task_id: str, **kwargs) -> Optional[dict]:
        if task_id not in self._tasks:
            return None
        self._tasks[task_id].update(kwargs)
        self._tasks[task_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save_metadata()
        return self._tasks[task_id]

    def _save_metadata(self):
        """把所有任务元数据存到 JSON 文件"""
        import json
        meta_path = os.path.join(self.base_dir, "metadata", "tasks.json")
        try:
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(self._tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[storage] Failed to save metadata: {e}", flush=True)

    def get_task(self, task_id: str) -> Optional[dict]:
        return self._tasks.get(task_id)

    def save_html(self, task_id: str, html_content: str):
        path = os.path.join(self.base_dir, "html", f"{task_id}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_content)

    def get_html(self, task_id: str) -> Optional[str]:
        path = os.path.join(self.base_dir, "html", f"{task_id}.html")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return None

    def save_preview(self, task_id: str, content, preview_type: str = "svg"):
        """保存封面：svg存文本，webp/png存二进制"""
        ext = "svg" if preview_type == "svg" else preview_type
        path = os.path.join(self.base_dir, "previews", f"{task_id}.{ext}")
        if preview_type == "svg":
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        else:
            with open(path, "wb") as f:
                f.write(content)
        # 记录类型
        self.update_task(task_id, preview_type=preview_type)

    def get_preview(self, task_id: str) -> Optional[tuple]:
        """返回 (content, content_type) 或 None"""
        # 先找 webp/png
        for ext, ct in [("webp", "image/webp"), ("png", "image/png")]:
            path = os.path.join(self.base_dir, "previews", f"{task_id}.{ext}")
            if os.path.exists(path):
                with open(path, "rb") as f:
                    return (f.read(), ct)
        # 再找 svg
        path = os.path.join(self.base_dir, "previews", f"{task_id}.svg")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return (f.read().encode("utf-8"), "image/svg+xml")
        return None

    def list_tasks(self) -> list[dict]:
        return sorted(
            self._tasks.values(),
            key=lambda t: t["created_at"],
            reverse=True,
        )


# Global singleton
storage = Storage(
    base_dir=os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage")
)
