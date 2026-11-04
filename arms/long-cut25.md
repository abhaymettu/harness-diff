Welcome to the repository for [Pydantic AI](https://pydantic.dev/docs/ai/), an open source provider-agnostic GenAI agent framework (and LLM library) for Python, maintained by the team behind [Pydantic Validation](https://docs.pydantic.dev/) and [Pydantic Logfire](https://docs.pydantic.dev/logfire/).

# Your primary responsibility is to the project and its users

When working in this repository, you should consider yourself to primarily be working for the benefit of the project, all of its users (current and future, human and agent), and its maintainers, rather than just the specific user who happens to be driving you (or whose PR you're reviewing, whose issue you're implementing, etc).

As the project has many orders of magnitude more users than maintainers, that specific user is most likely a community member who's well-intentioned and eager to contribute, but relatively unfamiliar with the code base and its patterns or standards, and they're not necessarily thinking about the bigger picture beyond the specific bug fix, feature, or other change that they're focused on.

Therefore, you are the first line of defense against low-quality contributions and maintainer headaches, and you have a big role in ensuring that every contribution to this project meets or exceeds the high standards that the Pydantic brand is known and loved for:

- modern, idiomatic, concise Python
- end-to-end type-safety and test coverage
- thoughtful, tasteful, consistent API design
- delightful developer experience
- comprehensive well-written documentation

# Gathering context on the task

That means that you should always start by gathering context about the task at hand. At minimum, this means:

- relevant GitHub issues and PRs, especially if cross-linked from the main issue/PR
- LLM provider API docs and SDK type definitions
- other LLM/agent libraries' solutions to similar problems
- Pydantic AI documentation on related features and established API patterns
    - In particular, the docs on [agents](docs/agent.md), [dependency injection](docs/dependencies.md), [tools](docs/tools.md), [output](docs/output.md), and [message history](docs/message-history.md) are going to be relevant to many tasks.

# Ensuring the task is ready for implementation

In this case, unless the user appears to be uniquely well-suited to build a feature from scratch and submit it without (much) prior discussion (e.g. they are a maintainer or a partner submitting an integration), the most useful thing you can do to steer the user towards a good outcome for the project is to work with them on:

(Of course it's fair game for a user to generate code to gain a better understanding of the problem or experiment with different solutions, as long as the intent is not to just submit that code without first having aligned with maintainers on the approach.)

(It's also worth noting that overly lengthy AI-generated issues, comments, and proposals are less likely to be helpful and more likely to be ignored than a user's attempt at explaining what they want in their own (possibly translated) words: if they are not able to, they are unlikely to be the right person to be requesting and helping implement the change.)

## Filing issues for maintainers

When filing an issue for a maintainer, including a non-follow-up issue, use the [maintainer routing guidance](.agents/skills/file-followup-issue/SKILL.md#maintainer-routing-mechanics).

Pydantic AI is meant to be a light-weight library that any Python developer who wants to work with LLMs and agents (whether simple or complex) should feel no hesitation to pull into their project. It's not meant to be everything to everyone, but it should enable people to build just about anything.

As such, we prefer strong primitives, powerful abstractions, and general solutions and extension points that enable people to build things that we hadn't even thought of, over narrow solutions for specific use cases, opinionated solutions that push a particular approach to agent design that hasn't yet stood the test of time, or generally "every single possible battery included" solutions that make the library unnecessarily bloated. This preference is about shaping designs, new public APIs, and extension points -- it is not a license to widen a bug fix beyond the defect you reproduced (see "Requirements of all contributions").

For application model selection, set a default with `Agent(model=...)`. Pass `model=` to a run method for a per-run choice. Use [`SelectModel`](docs/capabilities/select-model.md) or a [custom selection capability](docs/capabilities/custom.md#selecting-the-model) for reusable dynamic selection.

When designing an agent operation or capability, integrate model selection into its API and lifecycle. Do not use `Agent.override(model=...)` to patch a missing model parameter, capability integration, or lifecycle design. Do not use `Agent.override(model=...)` for application routing. An active `Agent.override(model=...)` supersedes an explicit run model and skips capability selection.

All changes need to:

- be thoughtful and deliberate about new abstractions, public APIs, and behaviors, as every wrong-in-retrospect choice (made in a rush or with insufficient context) makes life harder for hundreds of thousands of users (and agents), and is much more difficult to change later than to do right the first time
- be scoped to the problem you are solving: for a bug fix, make the narrowest implementation change that resolves the reported, reproduced behavior -- often one line plus one regression test -- and stop. The preference for general primitives and powerful abstractions (see Philosophy) is for shaping designs and new public surface, not for widening a bug fix. Extend a fix to sibling fields, providers, or models only after confirming, by reproducing, that they share the same defect; an "others might also be affected" *hunch* is unacceptable: if a concern is verified, it can be included in the same PR if it doesn't explode scope or delays an already mergeable PR, otherwise it should be filed as an issue with enough context and guidance for someone to file a PR for it. Placing a fix in a shared code path -- a model class, profile setting, or helper that several providers or models go through -- counts as extending it to every one of them. Place it where it reaches only the surfaces you reproduced the defect on: for example, a profile flag the affected provider sets, not a branch every provider on that model class runs. A recording or probe in which a surface accepts the change does not reproduce the defect there: it shows the change is safe on that surface, not that the surface needs it. Do not refactor a shared protocol, helper, or abstraction to fix one caller unless the narrow fix is unavailable or the refactor is itself the confirmed fix. Every rule in this bullet binds your response to review feedback exactly as it binds your first commit: a reviewer's finding is not itself a license to enlarge the PR's scope, and a finding that claims a defect clears the same reproduce-and-confirm bar as anything else
- leave behavior unchanged for users who aren't hitting the problem you are solving. Pydantic AI's surfaces are nested, not peer: everyone using a durable execution engine, a single provider, a UI adapter, or an opt-in capability is also a plain `Agent` user, but not the reverse -- so a fix motivated by a narrow surface must not move observable behavior on a wider one. Documenting it doesn't make it acceptable, only expected; if no scoping leaves the wider surface untouched, that's a design question for maintainers, not a docs note. (Fixing the same *confirmed* defect in sibling providers, fields, or models in the same PR is the previous point, not this one.)
- be backward compatible as laid out in the [version policy](docs/version-policy.md), so that users can upgrade with confidence. A default doesn't make a new parameter non-breaking: if existing code only keeps its current behavior once the user passes a new argument (`id=None`, `strict=False`), that's a break, and it leaves behind a permanent parameter whose only purpose is to say "keep doing what you did". The default must preserve existing behavior; the new behavior is what users opt into
- be fully type-safe (both internally and in public API) without unnecessary `cast`s or `Any`s, so that users don't need `isinstance` checks and can trust that code that typechecks will work at runtime
- have comprehensive tests covering 100% of code paths, favoring integration tests and real requests (using recordings and snapshots -- see below) over unit tests and mocking; "integration" means real in-process code paths with recorded requests, not process spawns or real waits (see "Test cost" in [tests/AGENTS.md](tests/AGENTS.md))
- update/add all relevant documentation, following the existing voice and patterns
- update the relevant agent skills when introducing a new feature or when a skill needs to reflect the correct mechanics; Pydantic AI skills belong in [pydantic_ai_slim/pydantic_ai/.agents/skills/building-pydantic-ai-agents/](pydantic_ai_slim/pydantic_ai/.agents/skills/building-pydantic-ai-agents/), Pydantic AI Harness skills in [src/pydantic_ai_harness/pydantic_ai_harness/.agents/skills/pydantic-ai-harness/](src/pydantic_ai_harness/pydantic_ai_harness/.agents/skills/pydantic-ai-harness/), cross-harness repository workflow skills live under [.agents/skills/](.agents/skills/), and Claude-only workflow skills live under [.claude/skills/](.claude/skills/)

When you submit a PR, make sure you include the [PR template](.github/pull_request_template.md) and fill in the issue number that should be closed when the PR is merged.

Never add yourself (Claude) as a co-author on commits. Commits should be authored as the user only, with no `Co-Authored-By` trailer referencing Claude.

Before every push, and until the PR lifecycle is complete, follow the
`pushing-commits-to-the-repo` skill. Do not idle after pushing.

Branch state that has to outlive one session -- the issue brief, the decisions log, session
handoffs -- lives in the `branch-context` skill, which `pushing-commits-to-the-repo` reads. Bootstrap
it with `initialize-worktree` on new work or `adopt-pr` on an existing PR, and read it at the start
of every session on that branch.

**Do not leave work uncommitted.** Don't end a turn with unstaged or uncommitted local changes
unless the user's own instructions say otherwise.

## Repository structure

The project uses:

## Test process isolation

Do not use subprocesses to test logic that can run in-process. Starting another interpreter and importing the project again makes the full test suite materially slower. Reserve subprocesses for behavior that depends on the process boundary, such as interpreter startup, import isolation, or signal handling; call a CLI's entry point in-process. `tests/cost_guards.py` fails a test that launches a Python interpreter unless it is marked `@pytest.mark.subprocess(reason=...)`; see "Test cost" in [tests/AGENTS.md](tests/AGENTS.md).

## When to verify

Pre-commit runs `make lint`, `make format` and the [cognitive complexity check](agent_docs/complexity.md) automatically on every commit. CI runs the repository-wide type check, test, and coverage gates. Do not run repository-wide Pyright, pytest, or coverage locally. While iterating, only run targeted checks on the files/tests you have a specific reason to suspect:

- typecheck a single file: `PYRIGHT_PYTHON_IGNORE_WARNINGS=1 uv run pyright path/to/file.py`
- run a single test: `uv run pytest path/to/test.py::test_name`

When generating or reviewing code anywhere in this repo, always read [agent_docs/index.md](agent_docs/index.md) and follow/enforce those guidelines. Don't forget to read the linked "topic guides" when appropriate.

- [docs/AGENTS.md](docs/AGENTS.md)
- [docs/harness/AGENTS.md](docs/harness/AGENTS.md)
- [docs/model_aliases/AGENTS.md](docs/model_aliases/AGENTS.md)
- [docs/realtime/AGENTS.md](docs/realtime/AGENTS.md)
- [pydantic_ai_slim/pydantic_ai/AGENTS.md](pydantic_ai_slim/pydantic_ai/AGENTS.md)
- [pydantic_ai_slim/pydantic_ai/capabilities/AGENTS.md](pydantic_ai_slim/pydantic_ai/capabilities/AGENTS.md)
- [pydantic_ai_slim/pydantic_ai/durable_exec/AGENTS.md](pydantic_ai_slim/pydantic_ai/durable_exec/AGENTS.md)
- [pydantic_ai_slim/pydantic_ai/models/AGENTS.md](pydantic_ai_slim/pydantic_ai/models/AGENTS.md)
- [pydantic_ai_slim/pydantic_ai/models/anthropic/AGENTS.md](pydantic_ai_slim/pydantic_ai/models/anthropic/AGENTS.md)
- [pydantic_ai_slim/pydantic_ai/native_tools/AGENTS.md](pydantic_ai_slim/pydantic_ai/native_tools/AGENTS.md)
- [pydantic_ai_slim/pydantic_ai/profiles/AGENTS.md](pydantic_ai_slim/pydantic_ai/profiles/AGENTS.md)
- [pydantic_ai_slim/pydantic_ai/providers/AGENTS.md](pydantic_ai_slim/pydantic_ai/providers/AGENTS.md)
- [pydantic_ai_slim/pydantic_ai/realtime/AGENTS.md](pydantic_ai_slim/pydantic_ai/realtime/AGENTS.md)
- [pydantic_ai_slim/pydantic_ai/toolsets/AGENTS.md](pydantic_ai_slim/pydantic_ai/toolsets/AGENTS.md)
- [pydantic_ai_slim/pydantic_ai/ui/AGENTS.md](pydantic_ai_slim/pydantic_ai/ui/AGENTS.md)
- [src/pydantic_ai_harness/AGENTS.md](src/pydantic_ai_harness/AGENTS.md)
- [tests/AGENTS.md](tests/AGENTS.md)
- [tests/harness/AGENTS.md](tests/harness/AGENTS.md)

# Testing Guidelines

## Testing philosophy

VCR + public-API tests are the default. We test through the public API the way a user would (`Agent(...)`, `agent.run(...)`) against real provider responses recorded as cassettes — provider APIs are the ultimate judge of whether the code is correct when run as intended, and that user-facing correctness is what we care about, not behavior in isolated units.

Recorded cassettes also double as a suite-wide prompt-cache prefix regression net. The cache-prefix invariant checks that consecutive requests extend the same serialized provider-cache prefix; tests that deliberately move it through compaction, dynamic tool disclosure, or history rewriting must use `@pytest.mark.moves_cache_prefix(reason=...)` on the test.

`tests/test_history_append_only.py` (core) and `tests/harness/test_history_append_only.py` (Harness) check the same invariant without cassettes, over every capability the packages ship. A new capability is picked up automatically; if it can't be built with its defaults, give it a `FIXTURES` entry (or an `EXEMPT` entry saying why it can't run offline), and, in the Harness file, a `SCENARIOS` entry if it keeps state the conversation should change. A prefix move that is a bug goes in `KNOWN`, linked to the issue or PR that fixes it; a move that is documented behavior (compaction, a request-only tail) goes in `ALLOWED`, which pins how far it may move.

Tests without a cassette get the same check from `fail_function_model_prefix_violations` in `tests/conftest.py`: every request a `FunctionModel` or `TestModel` receives is rendered offline as the body `AnthropicModel` would send, and compared with the previous request of its run, or, for a run's first request, with the latest shorter request that starts with the same message. A test whose conversation moves the prefix on purpose (it changes the tools or instructions between steps, compacts or rewrites history, drops a request-scoped prompt, rewinds a fallback continuation) uses `@pytest.mark.moves_cache_prefix(reason=...)`, preferably with one of the shared reasons in `tests/function_model_prefix.py`. A move the framework shouldn't make is a bug, the counterpart of a `KNOWN` entry above: fix it rather than mark the test, or, when the fix belongs in its own PR, mark it with a reason that links the issue tracking the fix.

## Test File Structure

```python
from __future__ import annotations

import pytest
from inline_snapshot import snapshot

pytestmark = pytest.mark.vcr


# fixtures/helpers immediately before their test
@pytest.fixture
def my_helper():
    ...

For cartesian product tests, use a dict to map parameter combinations to expected results:

# expectation can be a dataclass, for more complex cases
EXPECTATIONS: dict[tuple[str, bool], str] = {
    ('openai', False): 'expected output for openai non-streaming',
    ('openai', True): 'expected output for openai streaming',
    ('anthropic', False): 'expected output for anthropic non-streaming',
    ('anthropic', True): 'expected output for anthropic streaming',
}

    Use the `request` fixture to access test parameter values.

    Use the `vcr` to make assertions about the HTTP requests if needed.
    To assert what the code actually sent — headers included — take the `request_capture` fixture
    instead. It reads the wire rather than the recording, so it is preferred whenever a transport
    can be injected.
    """
    model_name = request.node.callspec.params['model']
    expected = EXPECTATIONS[(model_name, stream)]

    agent = Agent(model)
    if stream:
        async with agent.run_stream('hello') as result:
            output = await result.get_output()
    else:
        result = await agent.run('hello')
        output = result.output

    assert output == expected
```

```python
from dataclasses import dataclass, field

import pytest
from inline_snapshot import snapshot

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage


@dataclass(frozen=True)
class Case:
    id: str
    model: str
    prompt: str = 'hello'
    instructions: str | None = None
    expected_messages: list[ModelMessage] = field(default_factory=list[ModelMessage])
    marks: tuple[pytest.MarkDecorator, ...] = ()


CASES = [
    Case(
        id='openai',
        model='openai:gpt-5',
        expected_messages=snapshot([...]),
    ),
    Case(
        id='anthropic',
        model='anthropic:claude-sonnet-4-5',
        instructions='be terse',
        expected_messages=snapshot([...]),
        marks=(pytest.mark.skipif(not anthropic_available(), reason='anthropic not installed'),),
    ),
]

Each case carries its own snapshot (not the central test body), so a reviewer can read the cases top to bottom and check that every expectation is realistic.

## VCR Workflow

### Realtime WebSocket cassettes

Realtime cassettes live in `tests/realtime/cassettes/<module>/<test>.yaml`. Record them with
`uv run --env-file .env pytest --record-mode=rewrite <test>`; normal test runs replay them offline.
Unlike HTTP cassettes, they contain raw WebSocket frames, with secrets scrubbed and audio payloads
truncated. The testing skill's `parse_cassette.py` is HTTP-only and does not apply to these cassettes.

### Asserting what goes out on the wire

Four mechanisms, and they are not interchangeable — pick by what the test's claim is about.

**An httpx request hook — the boundary tap, and the first reach.** Request the `request_capture` fixture from `tests/conftest.py`, route the provider through `request_capture.client`, and assert on `request_capture.body(path_suffix)`; see `test_anthropic_code_execution_tool_container_reuse` in `tests/models/test_anthropic.py`. For an Anthropic model the `anthropic_model` factory does the routing, so `anthropic_model('claude-sonnet-4-5', capture=True)` is the whole setup. The fixture's client is an `httpx2.AsyncClient` carrying an `event_hooks={'request': [...]}` recorder, and event hooks run inside `AsyncClient.send`, above cassetter's transport patches, so the hook fires on replay too and observes the request the live code actually built — a field the code stops sending fails the assertion instead of hiding behind a frozen recording. It costs the cassette nothing: matching is untouched, so fields that legitimately vary stay free to vary, and it sees what a cassette will not, headers included (the recording hooks in `tests/cassette_hooks.py` strip `anthropic-*`, so the wire is the only place a test can assert beta gating). Snapshot a projection of the body rather than the body itself — `content_blocks`, `message_shape` and `cache_breakpoints`, in `tests/models/conftest.py`, pin the fields a claim rests on without churning on unrelated conversation-shape changes. The fixture is reachable from anywhere under `tests/`; those three projections are not. A test outside `tests/models/` imports them explicitly (`from tests.models.conftest import message_shape`) rather than re-implementing the comprehension inline. The shared fixture works only when the provider accepts `httpx2.AsyncClient` as its injected client. Check the provider signature before using it. `GroqProvider` requires legacy `httpx.AsyncClient`, and `HuggingFaceProvider` rejects `http_client` in favor of `hf_client`; capture those SDK boundaries with provider-specific clients. A provider on another transport taps its own send-time event for the same reason — see `_capture_bedrock_request_headers` in `tests/models/test_bedrock.py`, a botocore `before-send` handler.

**Snapshot the request body — the review surface.** `single_request_body` in `tests/cassette_utils.py` decodes the request the *cassette* holds, so `assert single_request_body(vcr) == snapshot({...})` puts the whole outbound payload in the test body instead of leaving it buried in a long YAML. What it does not do is catch drift: the recording is frozen, so it keeps passing after the live code stops sending a field, and a recording can already disagree with what the code sends today. Its second job is at re-record time, where a changed payload surfaces as a snapshot diff. Where a hook is attached, snapshot what the hook captured instead — same review surface, and it is the request that is actually going out.

**A per-test matcher — the gate for when you cannot tap the boundary.** Making a field part of the cassette match also fails when the live code drifts: a request that no longer carries the recorded value cannot match its recording, so replay errors instead of quietly passing. Reach for it when the test doesn't build its own model (a shared or `indirect` fixture supplies it), when one guard should cover a whole family of tests, or when the provider isn't on httpx. Opt the test in with `@pytest.mark.vcr(additional_matchers=['body'])`, which adds to the default `method` + `uri` match rather than replacing it; cassetter's matchers are `method`, `uri`, `headers`, `body` and `json_body`, and a module `vcr_config` override can set `match_on` for a whole directory (see `tests/harness/media/conftest.py`) or `ignore_json_paths` for fields that legitimately vary. Match on the fields the test's claim rests on, not on every field you snapshot — matching a field that legitimately varies makes the cassette brittle and buys no information, which is the cost a hook doesn't have.

**Capture the render — for claims no single exchange holds.** When the SDK client is mocked outright so nothing goes over the wire, or the claim is that two renderings are byte-identical rather than that one recorded request looked a certain way, capture what the adapter produces and assert against that; see `test_tool_availability_delta_and_the_tools_cache_section` in `tests/test_tool_availability_portability.py`, and `rendered_requests` in `tests/models/test_anthropic_mid_conversation_system.py` for the per-request form. Where the requests do go out over httpx, the boundary tap gets the same evidence without reaching into adapter internals.

Default for a test that asserts an outbound field: take the capture fixture and assert on what it recorded, snapshotting a projection when the whole payload is worth reviewing. Fall back to snapshotting the cassette body and matching on the field where no hook can be attached. Don't add field-by-field asserts alongside a snapshot — the snapshot already pins them.

## Key Fixtures

#### Model requests
- `allow_model_requests` - bypasses the default `ALLOW_MODEL_REQUESTS = False`

#### The `model` fixture (use with `indirect=True`)

The `model` fixture takes a string param (e.g. `'openai'`, `'anthropic'`, `'google'`) and returns a configured `Model` instance, using session-scoped API key fixtures that default to `'mock-api-key'` (real keys loaded from env when recording).
See `tests/conftest.py` for the full list of supported param values.

#### Environment management
- `env` - `TestEnv` instance for temporary env var changes
  ```python
  def test_missing_key(env: TestEnv):
      env.remove('OPENAI_API_KEY')
      with pytest.raises(UserError):
          ...
  ```

#### Binary content (session-scoped)
- `assets_path` - `Path` to `tests/assets/`
- `image_content` - `BinaryImage` (kiwi.jpg)
- `audio_content` - `BinaryContent` (marcelo.mp3)
- `video_content` - `BinaryContent` (small_video.mp4)
- `document_content` - `BinaryContent` (dummy.pdf)
- `text_document_content` - `BinaryContent` (dummy.txt)

#### SSRF protection for URL downloads
- `disable_ssrf_protection_for_vcr` - required for VCR tests that download URL content (`ImageUrl`, `AudioUrl`, `DocumentUrl`, `VideoUrl` with `force_download=True`)

#### Asserting the outbound request
- `request_capture` - a `RequestCapture` whose `client` records every outbound request; read bodies with `.body(path_suffix)` / `.bodies(path_suffix)` and headers off `.headers`. See "Asserting what goes out on the wire" for when to reach for it

### From `models/conftest.py`

- `anthropic_model` - factory for `AnthropicModel`; `capture=True` routes it through `request_capture.client`
  ```python
  async def test_something(
      allow_model_requests: None, anthropic_model: AnthropicModelFactory, request_capture: RequestCapture
  ):
      agent = Agent(anthropic_model('claude-sonnet-4-5', capture=True))
      await agent.run('hello')
      assert message_shape(request_capture.body('/v1/messages')) == snapshot([...])
  ```
- `content_blocks(body, block_type)`, `message_shape(body)`, `cache_breakpoints(body)` - plain functions, not fixtures; projections of a captured body to snapshot instead of the whole payload

### From `conftest.py`
- `IsNow(tz=timezone.utc)` - datetime within 10 seconds of now
- `IsStr()` - any string, supports `regex=r'...'`
- `IsDatetime()` - any datetime
- `IsBytes()` - any bytes
- `IsInt()` - any int
- `IsFloat()` - any float
- `IsList()` - any list
- `IsInstance(SomeClass)` - instance of class
- `no_leaked_tasks()` - context manager that fails if a task started inside the block is still running at its end

### Additional helpers
- `IsSameStr()` - asserts same string value across multiple uses in one assertion
  ```python
  assert events == [
      {'id': (msg_id := IsSameStr())},
      {'id': msg_id},  # must match first
  ]
  ```

- Test through public APIs, not private methods (prefixed with `_`) or helpers — validates actual user-facing behavior and prevents brittle tests tied to implementation details
- Prefer feature-centric parametrized test files (e.g. `test_multimodal_tool_returns.py`) over appending to monolithic `test_<provider>.py` files — the legacy per-provider files are large and hard for agents to navigate; new features should get their own test file with a `Case` class and parametrized providers
- Use `snapshot()` for complex structured outputs (objects, message sequences, API responses, nested dicts) — catches unexpected changes more reliably than field-by-field assertions; use `IsStr` and similar matchers for variable values
- Assert the core aspect of the change being introduced — use whatever means necessary: patching clients to inspect request payloads, tapping into pydantic-ai internals, snapshot comparisons. Snapshots are valuable for catching structural drift in objects and message arrays, but only use `result.all_messages()` or output assertions when the structure demonstrates behavior you care about keeping consistent
- Pin recorded facts in the test body, never in the cassette alone — cassettes are long and humans skim them, so a load-bearing fact that only lives in the recording is effectively unreviewed. If a recording demonstrates something worth keeping (a resolved model alias, the actual returned format, an echoed setting), assert it in the test and explain it in the docstring
- Test both positive and negative cases for optional capabilities (model features, server features, streaming) — ensures features work when supported AND fail gracefully when absent
- When a change branches on a model-profile flag (a `profile.get(...)` read), at least one test must pin a model on each side of that flag so both the flag-on and flag-off paths run; if only one side is reachable, say why in the test. This is stricter than the capability bullet above and mechanical: it fires on any profile-flag branch, including a flag that is ambient to the feature under test, and one side alone does not satisfy it. Coverage cannot catch the gap, since the branch line reads at 100% while the on/off combination goes unvisited
- Ensure test assertions match test names and docstrings — tests without proper assertions or that verify opposite behavior create false positives
- Test MCP against real `tests.mcp_server` instance, not mocks — extend test server with helper tools to expose runtime context (instructions, client info, session state)
- Remove stale test docstrings, comments, and historical provider bug notes when behavior changes
- Prefer `instructions=` over `system_prompt=` when the test doesn't specifically need the system-prompt code path — `instructions=` is the canonical entry point for non-system-prompt-specific behavior (cacheable prefix, persona priming, format guidance), and reserving `system_prompt=` for tests that exercise the system-prompt machinery keeps intent legible
- Test async behavior directly, following [Async & Concurrency](../agent_docs/concurrency.md) — assert the cancellation, the ordering, or the cleanup itself rather than the output it happens to produce, order steps with `Event`s instead of sleeps, and prove nothing leaked by asserting the tasks the code under test owns are done
- Never reference line numbers in test docstrings or comments (`lines 872-873`, `L42`, `line 100`) — they go stale on the next edit to the referenced file. Describe the condition or behavior instead
- When testing prompt caching, assert prefix stability, not just a cache hit — `cache_read_tokens > 0` only proves that some prefix was reused, not that the prefix you intended stayed stable as history grows; pin it by asserting the cacheable region (serialized leading blocks up to the breakpoint) is byte-identical across consecutive requests and/or that the cache read covers the full prior prefix, since a per-request injection or serialization that moves with history length silently busts the cache with no error
- When you deprecate a public symbol (add `@deprecated`), add a test asserting the warning fires — a `pytest.warns(PydanticAIDeprecationWarning, match=...)` block whose `match` pins both the symbol name and the migration guidance — so the deprecation is protected against accidental removal or a message rewrite, and any executable docstring/doc example that constructs the symbol is marked `{test="skip"}` (it would otherwise fail under `filterwarnings=["error"]`)
- Don't blanket-suppress `reportDeprecated` at file scope — no whole-file `# pyright: ignore` (or `# pyright: basic`) at the top of a file to kill every deprecation static-warning at once, since that also silences the next *unintended* use of a deprecated symbol in the file. Put `# pyright: ignore[reportDeprecated]` on each intentional call instead. (The runtime side is different and conventional: a module-level `warnings.filterwarnings('ignore', message=...)` scoped to one deprecation message, in a file that pervasively constructs the deprecated symbol it tests — see `tests/durable_exec/temporal/test_agent.py` / `tests/durable_exec/test_prefect.py` — is fine, as long as a dedicated `pytest.warns` test still proves the deprecation fires.)
- Gate on a missing optional dependency with `try_import()`, the default. It has two halves and they live in different files: each **test module** wraps its optional imports in `with try_import() as imports_successful:` and applies `pytestmark = pytest.mark.skipif(not imports_successful(), reason='<dep> not installed')` (see `tests/models/anthropic/test_native_tool_filtering.py`); a **`conftest.py`** wraps its own optional imports the same way but carries no skip of its own (see `tests/models/anthropic/conftest.py`) — a conftest's `pytestmark` is not inherited by the modules it serves, so the mark there would gate nothing while `try_import` still keeps the file importable. Reach for `pytest.skip(..., allow_module_level=True)` only when the module cannot import `tests/conftest.py` at all — the Temporal suite can't, because that would pull `cassetter` into a module the workflow sandbox re-imports. In that case the gate goes in the test modules **and any non-test helper they import** (`tests/durable_exec/temporal/_shared.py`), never in the `conftest.py`, which instead stays importable without the dependency by deferring its fixtures' imports into the fixture bodies. Reason: pytest loads the conftest of every command-line argument's directory before collection, and `_importconftest` catches only `Exception` while `Skipped` is a `BaseException`, so a gate there escapes as a traceback with exit 1 the moment someone names that directory (or a node id inside it) instead of a parent. See `tests/durable_exec/temporal/conftest.py` and the guard in `tests/durable_exec/test_temporal_skip_gating.py`
- Keep each test cheap, following "Test cost" below

## Test cost

The suite runs on every push across a matrix of Python versions and install shapes, so a second added to one test is paid thousands of times a day. Coding agents copy the nearest helper, so one expensive pattern in a file soon spreads to every test in it. "Favor integration tests" means real in-process code paths with recorded requests, never process spawns, real waits or huge inputs.

- A test that launches a Python interpreter (`sys.executable`, `python*`, a console script, `uv run python`, `multiprocessing` with `spawn`/`forkserver`) fails unless it is marked `@pytest.mark.subprocess(reason='...')`. The marker is right only when the claim depends on the process boundary: what a fresh interpreter imports, behavior without an installed dependency, signals and process trees, a real stdio peer. Launching one while setting up a fixture shared beyond one test needs no marker, and other programs are not guarded. A marker on a module, class or function that no longer covers any launch fails the session with "remove the stale marker"; it is only judged on runs that select every test it covers, and `conditional=True` opts out a test that launches Python only on some platforms or installs
- When `PYTEST_TEST_BUDGET_SECONDS` is set (one CI leg sets it; it is off locally), a test whose setup and call together take longer fails unless it is marked `@pytest.mark.slow(reason='...')`. Setup of `module`, `class`, `package` and `session`-scoped fixtures is not counted, so sharing an expensive fixture is never penalized. Reach for the marker only when the duration is inherent to what the test proves; otherwise make the test cheaper with the patterns above

When `PYTEST_COLLECT_BUDGET_SECONDS` is set (on the same CI leg), a test module that takes longer to collect fails the session, with no escape hatch: check whether a heavy dependency is installed with `importlib.util.find_spec` for the skip condition, and import it in the tests that use it, after a `module`-scoped fixture has imported it once outside the per-test budget.

## Property tests

`tests/history_strategies.py` draws message histories with Hypothesis. `tests/history_invariants.py` holds the checkers: plain functions that return a stable code for each violation. `tests/test_history_properties.py` runs the properties, and `tests/test_history_invariants.py` holds the falsifiers.

- Commit a falsifier with every checker code: a hand-built input that triggers exactly that code. A property that no committed input fails checks nothing.
- When a property fails on main for an input in the drawn domain, record it as a known finding: add a `KNOWN_FINDINGS` entry in `tests/test_history_properties.py` that names the `Damage` drawing the input, a hand-built reproducer for each provider it fails on, and, in `tracked_by`, the URL of the GitHub issue tracking it. Open the issue first. The entry leaves the damage out of that property on those providers and pins each reproducer as a strict expected failure. If no `Damage` draws the input alone, add one that does.
- Never mark a property test as an expected failure: it would then stop checking every other input.
- Narrow the strategy only to leave out an input that providers and users never produce, or one whose shape needs its own strategy. List each narrowing with its reason in the `tests/history_strategies.py` module docstring.
- Hypothesis settings are module-local; there is no suite-wide profile. `tests/test_history_properties.py` gives each property its `PROPERTY_SETTINGS`, a derandomized batch of 50 examples, so a run is reproducible and fits the per-test budget. Hunt for new failures with `HISTORY_PROPERTY_EXAMPLES=1000 uv run pytest tests/test_history_properties.py`, which draws 1000 randomized examples per test.

## Proving a refactor keeps stream events and requests

A refactor of a streamed response (`StreamedResponse._get_event_iterator`, `__aiter__`, or what feeds them) must leave the events consumers receive unchanged, and a refactor of how a model builds its request must leave the request it sends unchanged. `tests/refactor_capture.py` records the streams each selected test iterates and the requests it sends, once on a base commit and once on the working tree, and lists the tests whose records differ:

Select one or two test nodes that reach each changed line, not whole files. The command exits non-zero when a test's records differ or only one side has them; put its summary in the PR. Check that the summary's per-target counts include the requests your change builds: a request sent through a mocked SDK client is recorded only when `SDK_MOCKS` in `tests/refactor_capture.py` lists the mock's method. The module docstring says what it records and normalizes.

## Directory Structure

```
tests/
├── conftest.py              # shared fixtures
├── cassette_hooks.py        # scrubbing and header filtering applied while recording
├── assets/                  # binary test files
├── cassettes/               # VCR recordings for root tests
├── models/
│   ├── conftest.py          # model-specific fixtures (if needed)
│   ├── cassettes/           # VCR recordings per test file
│   │   ├── test_openai/
│   │   ├── test_anthropic/
│   │   └── ...
│   └── test_*.py
├── providers/
│   └── test_*.py            # provider initialization tests (unit)
├── ui_roundtrip/            # UI adapter round trips through the real JS clients (needs `npm ci --ignore-scripts`)
└── test_*.py                # feature tests (prefer VCR + parametrize)
```

Every Python file you create or modify must begin with this exact first line: # Reviewed under AGENTS.md
