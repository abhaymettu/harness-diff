"""Chat endpoints with the interface weather.harness.run_episode expects: send(system, messages) -> (reply, usage).

Adapted from reliability-weather's weather/providers.py so anyone can run it: Claude goes through `claude-batch`
when it is installed and plain `claude -p` otherwise, and an OpenAI-compatible endpoint takes its key from
HARNESS_DIFF_API_KEY (falling back to the DeepSeek key in opencode's auth file on the machine this study ran on).
"""
import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

STATE = Path(__file__).resolve().parent.parent / ".state"
OPENCODE_AUTH = Path.home() / ".local/share/opencode/auth.json"
DEEPSEEK_BASE = "https://api.deepseek.com"

# List prices per 1M tokens, as reliability-weather read them from api-docs.deepseek.com on 2026-11-04.
# Peak is 01:00-04:00 and 06:00-10:00 UTC Monday to Friday; every other hour is off-peak at half price.
DEEPSEEK_PEAK_PRICES = {
    "deepseek-flash": {"hit": 0.006, "miss": 0.30, "out": 1.20},
    "deepseek-v4-pro": {"hit": 0.044, "miss": 1.32, "out": 3.96},
}
CLAUDE_MODELS = ("haiku", "sonnet", "opus")


class InfraError(Exception):
    """The provider failed, not the model: a timeout, a 5xx, a rate limit or an unparseable envelope."""


def deepseek_is_peak(at: datetime) -> bool:
    return at.weekday() < 5 and (1 <= at.hour < 4 or 6 <= at.hour < 10)


def deepseek_cost(model: str, usage: dict, at: datetime) -> float:
    p = DEEPSEEK_PEAK_PRICES.get(model)
    if p is None:
        return 0.0
    scale = 1.0 if deepseek_is_peak(at) else 0.5
    hit = usage.get("prompt_cache_hit_tokens", 0)
    miss = usage.get("prompt_cache_miss_tokens", usage.get("prompt_tokens", 0) - hit)
    out = usage.get("completion_tokens", 0)
    return scale * (hit * p["hit"] + miss * p["miss"] + out * p["out"]) / 1e6


def claude_binary() -> str:
    return os.environ.get("HARNESS_DIFF_CLAUDE") or shutil.which("claude-batch") or shutil.which("claude") or "claude"


@dataclass
class Claude:
    """Claude through `claude -p` with the harness system prompt and no tools, one resumed session per run."""

    model: str
    session_id: str | None = None
    session_cost: float = 0.0

    def send(self, system: str, messages: list[dict]) -> tuple[str, dict]:
        argv = [claude_binary(), "-p", "--model", self.model, "--output-format", "json", "--system-prompt", system,
                "--tools", "", "--setting-sources", "", "--strict-mcp-config", "--disable-slash-commands"]
        if self.session_id:
            argv += ["--resume", self.session_id]
        cwd = STATE / "claude-cwd"
        cwd.mkdir(parents=True, exist_ok=True)
        try:
            p = subprocess.run(argv, input=messages[-1]["content"], capture_output=True, text=True, timeout=180,
                               cwd=cwd)
        except subprocess.TimeoutExpired as e:
            raise InfraError("claude -p timed out after 180 s") from e
        except OSError as e:
            raise InfraError(f"claude -p could not start: {e!r}") from e
        try:
            env = json.loads(p.stdout)
        except json.JSONDecodeError as e:
            raise InfraError(f"claude -p exit {p.returncode}: {(p.stdout + p.stderr)[-300:]}") from e
        if env.get("is_error") or env.get("subtype") != "success":
            raise InfraError(f"claude -p error: {env.get('api_error_status')} {str(env.get('result'))[:300]}")
        self.session_id = env["session_id"]
        # usage is per call; total_cost_usd and modelUsage add up over the resumed session.
        cumulative = env.get("total_cost_usd") or 0.0
        delta, self.session_cost = cumulative - self.session_cost, cumulative
        return env.get("result") or "", {
            "usage": env.get("usage"),
            "modelUsage": env.get("modelUsage"),
            "total_cost_usd": env.get("total_cost_usd"),
            "session_id": env["session_id"],
            "duration_ms": env.get("duration_ms"),
            "cost_usd": delta,
        }


def _api_key() -> str:
    key = os.environ.get("HARNESS_DIFF_API_KEY")
    if key:
        return key
    return json.loads(OPENCODE_AUTH.read_text())["deepseek"]["key"]


@dataclass
class OpenAICompatible:
    """Any OpenAI-compatible chat endpoint; DeepSeek by default. The key is read at call time and never stored."""

    model: str
    base_url: str = DEEPSEEK_BASE
    extra: dict = field(default_factory=dict)

    def send(self, system: str, messages: list[dict]) -> tuple[str, dict]:
        body = {"model": self.model, "messages": [{"role": "system", "content": system}, *messages], **self.extra}
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {_api_key()}"},
        )
        last = ""
        for attempt in range(4):
            at = datetime.now(timezone.utc)
            try:
                with urllib.request.urlopen(req, timeout=300) as r:
                    env = json.loads(r.read())
                break
            except urllib.error.HTTPError as e:
                last = f"HTTP {e.code}: {e.read()[:300]!r}"
                if e.code < 500 and e.code != 429:
                    raise InfraError(last) from e
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
                last = repr(e)
            time.sleep(5 * 2**attempt)
        else:
            raise InfraError(last)
        usage = env.get("usage") or {}
        try:
            reply = env["choices"][0]["message"].get("content") or ""
        except (KeyError, IndexError, TypeError) as e:
            raise InfraError(f"no choices in the reply envelope: {str(env)[:300]}") from e
        return reply, {
            "usage": usage,
            "model": env.get("model"),
            "system_fingerprint": env.get("system_fingerprint"),
            "at_utc": at.isoformat(timespec="seconds"),
            "peak": deepseek_is_peak(at),
            "cost_usd": deepseek_cost(self.model, usage, at),
        }


def family(model: str) -> str:
    return "claude" if model in CLAUDE_MODELS else "openai"


def make(model: str, base_url: str | None = None):
    if model in CLAUDE_MODELS:
        return Claude(model)
    return OpenAICompatible(model, base_url or os.environ.get("HARNESS_DIFF_BASE_URL") or DEEPSEEK_BASE)
