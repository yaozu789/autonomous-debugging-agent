"""
Autonomous Debugging Agent
---------------------------
A CLI agent that uses Claude's tool-calling API to autonomously debug a
Python script: it reads the file, runs it, interprets any error, edits
the code, and re-runs to confirm the fix — looping until the script
executes cleanly or a max-iteration budget is hit.

This is a genuine multi-turn agent: the MODEL decides which tool to call
and when to stop, based on real tool results fed back into the
conversation. Nothing here is scripted/hardcoded logic that pretends to
be agentic.

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python agent.py --file buggy_script.py

Requires: pip install anthropic
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from anthropic import Anthropic

MODEL = "claude-sonnet-5"
MAX_TURNS = 8

# ---------------------------------------------------------------------------
# Real tool implementations (no mocking / no hardcoded "pretend" results)
# ---------------------------------------------------------------------------

def tool_read_file(path: str) -> str:
    """Read and return the full contents of a file on disk."""
    try:
        return Path(path).read_text()
    except Exception as e:
        return f"ERROR reading {path}: {e}"


def tool_write_file(path: str, content: str) -> str:
    """Overwrite a file on disk with new content."""
    try:
        Path(path).write_text(content)
        return f"OK: wrote {len(content)} characters to {path}"
    except Exception as e:
        return f"ERROR writing {path}: {e}"


def tool_run_python(path: str) -> str:
    """Execute a Python script and capture stdout, stderr, and exit code."""
    try:
        result = subprocess.run(
            [sys.executable, path],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return (
            f"exit_code: {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    except subprocess.TimeoutExpired:
        return "ERROR: script timed out after 15 seconds (possible infinite loop)"
    except Exception as e:
        return f"ERROR running {path}: {e}"


TOOL_IMPL = {
    "read_file": lambda i: tool_read_file(i["path"]),
    "write_file": lambda i: tool_write_file(i["path"], i["content"]),
    "run_python": lambda i: tool_run_python(i["path"]),
}

TOOL_SCHEMAS = [
    {
        "name": "read_file",
        "description": "Read the full contents of a file on disk.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "File path to read"}},
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Overwrite a file on disk with new content. Use this to apply a fix.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to write"},
                "content": {"type": "string", "description": "Full new file content"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "run_python",
        "description": "Execute a Python script and return stdout, stderr, and exit code.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Script path to run"}},
            "required": ["path"],
        },
    },
]


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------

def run_agent(target_file: str) -> None:
    client = Anthropic()

    system_prompt = (
        "You are an autonomous debugging agent. You will be given a Python "
        "script that currently fails or misbehaves. Use your tools to: "
        "(1) read the file, (2) run it to observe the actual error, "
        "(3) diagnose the root cause, (4) write a corrected version of the "
        "file, and (5) re-run it to confirm the fix works. Do not guess at "
        "the bug without running the script first. Do not claim success "
        "without a clean re-run. When the script runs cleanly, summarize "
        "what was wrong and what you changed, then stop."
    )

    messages = [
        {
            "role": "user",
            "content": (
                f"The script at '{target_file}' is not working correctly. "
                f"Please debug and fix it."
            ),
        }
    ]

    print(f"=== Starting agent on {target_file} ===\n")

    for turn in range(1, MAX_TURNS + 1):
        response = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=system_prompt,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        # Print any reasoning/narration text from this turn
        for block in response.content:
            if block.type == "text" and block.text.strip():
                print(f"[turn {turn}] agent says:\n{block.text}\n")

        if response.stop_reason != "tool_use":
            print("=== Agent finished (no further tool calls) ===")
            break

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            print(f"[turn {turn}] calling tool: {block.name}({json.dumps(block.input)})")
            result_text = TOOL_IMPL[block.name](block.input)
            print(f"[turn {turn}] tool result:\n{result_text}\n")
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_text,
                }
            )

        messages.append({"role": "user", "content": tool_results})
    else:
        print("=== Stopped: reached max turn budget ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Autonomous debugging agent")
    parser.add_argument("--file", required=True, help="Path to the buggy Python script")
    args = parser.parse_args()
    run_agent(args.file)
