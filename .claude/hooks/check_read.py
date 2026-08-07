#!/usr/bin/env python3
"""PreToolUse hook (Read matcher): block reading background-task output sinks.

CLAUDE.md forbids Read on files under
  .../AppData/Local/Temp/claude/<project>/<session>/tasks/<id>.output
These are the raw streamed stdout/stderr sinks of background Bash / agent tasks.
Reading them directly is banned (for local_agent tasks the .output is a symlink
to the full subagent transcript JSONL -- a Read overflows the context window),
and CLAUDE.md mandates the TaskOutput tool instead.

This hook denies such reads with a clear reason + actionable remediation so no
permission prompt is ever shown for them. Hook deny takes precedence over the
broad `Read(.../Temp/claude/...)` allow rule in settings.local.json.

To extend: add more path predicates to _is_forbidden(). The driver reads
`tool_input.file_path` from stdin (same JSON contract as check_bash.py).
"""
import json
import re
import sys

_TASK_OUTPUT_TAIL = re.compile(r"/tasks/[^/]+\.output$")


def _norm(file_path: str) -> str:
    return file_path.replace("\\", "/").lower()


def _is_forbidden(file_path: str):
    """Return (reason, task_id) if the Read is on a task-output sink, else None."""
    norm = _norm(file_path)
    if "local/temp/claude/" not in norm:
        return None
    m = _TASK_OUTPUT_TAIL.search(norm)
    if not m:
        return None
    fname = norm.rsplit("/", 1)[-1]
    task_id = fname[: -len(".output")] if fname.endswith(".output") else fname
    reason = (
        "原因：这是后台任务的输出文件 (.../AppData/Local/Temp/claude/<project>/<session>/tasks/"
        f"{fname})，是后台 Bash/agent 任务的原始流式 stdout/stderr。CLAUDE.md 禁止用 Read "
        "工具直接读这些文件（local_agent 任务的 .output 是完整 transcript JSONL 的符号链接，"
        "Read 会撑爆上下文窗口）。修改方式：用 TaskOutput 工具读取，传 task_id="
        f"\"{task_id}\"（block=true 等待完成、block=false 非阻塞查当前状态）；"
        "bash 任务的 .output 可 Read，但本地 agent 任务必须用 TaskOutput。不要用 Read 直接读 .output。"
    )
    return reason, task_id


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    file_path = data.get("tool_input", {}).get("file_path", "")
    if not file_path:
        return
    hit = _is_forbidden(file_path)
    if not hit:
        return
    reason, _ = hit
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
