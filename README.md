# Autonomous Debugging Agent

A CLI agent that uses Claude's tool-calling API to autonomously debug a Python
script, with no scripted logic pretending to be "agentic." The model itself
decides which tool to call, when to call it, and when it's done, based on real
tool output fed back into the conversation each turn.

## How it works

1. The agent is told a script isn't working.
2. It calls `read_file` to see the code.
3. It calls `run_python` to see the actual error/output.
4. It reasons about the root cause based on real output (not guessing blind).
5. It calls `write_file` to apply a fix.
6. It calls `run_python` again to confirm the fix actually works.
7. It stops and summarizes what was wrong and what changed.

This loop can take multiple turns if the first fix attempt is wrong: the agent
sees the new error and tries again, up to `MAX_TURNS`.

## Files

- `agent.py` — the agent loop plus three real tools (`read_file`, `write_file`,
  `run_python`)
- `buggy_script_BROKEN.py` — the demo target. A two-heap running-median
  implementation with a genuine bug (a missing negation when rebalancing between
  heaps, which silently corrupts heap ordering rather than crashing outright, a
  realistic bug, not a typo). Point the agent at THIS file.
- `buggy_script.py` — the corrected reference version. Runs clean. Kept for
  comparison so you can see the one-line difference the agent needs to find.

## Running it

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...
python agent.py --file buggy_script_BROKEN.py
```

You'll see turn-by-turn output showing exactly which tool the model called, with
what arguments, and what real result came back, including the final successful
re-run.

## What's verified

- `tool_read_file`, `tool_write_file`, and `tool_run_python` were each
  unit-tested directly and work correctly.
- `buggy_script_BROKEN.py` genuinely fails (exit code 1, AssertionError) before
  the agent touches it. It's a real bug, not a decorative one.
- The agent loop follows Anthropic's documented tool-use message format (tool
  schemas, `tool_use` blocks, `tool_result` blocks fed back in).
- Run end-to-end with a live API key: the model reads the file, runs it to
  observe the real failure, diagnoses the missing negation, writes the fix, and
  re-runs to a clean pass, all within the turn budget.
