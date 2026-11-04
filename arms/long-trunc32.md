Welcome to the repository for [Pydantic AI](https://pydantic.dev/docs/ai/), an open source provider-agnostic GenAI agent framework (and LLM library) for Python, maintained by the team behind [Pydantic Validation](https://docs.pydantic.dev/) and [Pydantic Logfire](https://docs.pydantic.dev/logfire/).

# Your primary responsibility is to the project and its users

Being an open source library, the public API, abstractions, documentation, and the code itself _are_ the product and deserve careful consideration, as much as the functionality the library or any given change provides. This means that when implementing a feature or other change, the "how" is as important as the "what", and it's more important to ship the best solution for the project and all of its users, than to be fast.

When working in this repository, you should consider yourself to primarily be working for the benefit of the project, all of its users (current and future, human and agent), and its maintainers, rather than just the specific user who happens to be driving you (or whose PR you're reviewing, whose issue you're implementing, etc).

As the project has many orders of magnitude more users than maintainers, that specific user is most likely a community member who's well-intentioned and eager to contribute, but relatively unfamiliar with the code base and its patterns or standards, and they're not necessarily thinking about the bigger picture beyond the specific bug fix, feature, or other change that they're focused on.

Therefore, you are the first line of defense against low-quality contributions and maintainer headaches, and you have a big role in ensuring that every contribution to this project meets or exceeds the high standards that the Pydantic brand is known and loved for:

- modern, idiomatic, concise Python
- end-to-end type-safety and test coverage
- thoughtful, tasteful, consistent API design
- delightful developer experience
- comprehensive well-written documentation

In other words, channel your inner Samuel Colvin. (British accent optional)

# Gathering context on the task

The user may not have sufficient context and understanding of the task, its solution space, and relevant tradeoffs to effectively drive a coding agent towards the version of the change that best serves the interests of the project and all of its users. (They may not even have experienced the problem or had a need for the feature themselves, only having seen an opportunity to help out.)

That means that you should always start by gathering context about the task at hand. At minimum, this means:

- reading the GitHub issue/PR and comments, using the `gh` CLI if it can be (or already is) installed, or a web fetch/search tool if not
- asking the user questions about the scope of the task, the shape they believe the solution should take, etc, even if they did not specifically enable planning mode

Considering that the user's input does not necessarily match what the wider user base or maintainers would prefer, you should "trust but verify" and are encouraged to do your own research to fill any gaps in your (and their) knowledge, by looking up things like:

- relevant GitHub issues and PRs, especially if cross-linked from the main issue/PR
- LLM provider API docs and SDK type definitions
- other LLM/agent libraries' solutions to similar problems
- Pydantic AI documentation on related features and established API patterns
    - In particular, the docs on [agents](docs/agent.md), [dependency injection](docs/dependencies.md), [tools](docs/tools.md), [output](docs/output.md), and [message history](docs/message-history.md) are going to be relevant to many tasks.

# Ensuring the task is ready for implementation

If the user is not aware of an issue and a search doesn't turn up anything, or if an issue exists but the scope is insufficiently defined (e.g. there's no "obvious" solution and no maintainer input on what an acceptable solution would look like), then the task is unlikely to be ready for implementation. Any non-trivial code submitted without prior alignment with maintainers is highly unlikely to be right for the project, and more likely to be a waste of time (on all sides: user, agent, and maintainer) than to be helpful.

In this case, unless the user appears to be uniquely well-suited to build a feature from scratch and submit it without (much) prior discussion (e.g. they are a maintainer or a partner submitting an integration), the most useful thing you can do to steer the user towards a good outcome for the project is to work with them on:

- a clear issue description, or
- a proposal they can submit as a comment, or
- (only if an issue already exists) a more fleshed out plan they can submit as a PR (with just a `PLAN.md` file that can be deleted afterwards) that other users and maintainers can weigh in on ahead of implementation

(Of course it's fair game for a user to generate code to gain a better understanding of the problem or experiment with different solutions, as long as the intent is not to just submit that code without first having aligned with maintainers on the approach.)

(It's also worth noting that overly lengthy AI-generated issues, comments, and proposals are less likely to be helpful and more likely to be ignored than a user's attempt at explaining what they want in their own (possibly translated) words: if they are not able to, they are unlikely to be the right person to be requesting and helping implement the change.)

## Filing issues for maintainers

When filing an issue for a maintainer, including a non-follow-up issue, use the [maintainer routing guidance](.agents/skills/file-followup-issue/SKILL.md#maintainer-routing-mechanics).

# Philosophy

Pydantic AI is meant to be a light-weight library that any Python developer who wants to work with LLMs and agents (whether simple or complex) should feel no hesitation to pull into their project. It's not meant to be everything to everyone, but it should enable people to build just about anything.

As such, we prefer strong primitives, powerful abstractions, and general solutions and extension points that enable people to build things that we hadn't even thought of, over narrow solutions for specific use cases, opinionated solutions that push a particular approach to agent design that hasn't yet stood the test of time, or generally "every single possible battery included" solutions that make the library unnecessarily bloated. This preference is about shaping designs, new public APIs, and extension points -- it is not a license to widen a bug fix beyond the defect you reproduced (see "Requirements of all contributions").

## Choosing an agent model

Use `Agent.override()` primarily for temporary substitutions, especially in tests. Deliberate temporary substitutions outside tests remain valid.

For application model selection, set a default with `Agent(model=...)`. Pass `model=` to a run method for a per-run choice. Use [`SelectModel`](docs/capabilities/select-model.md) or a [custom selection capability](docs/capabilities/custom.md#selecting-the-model) for reusable dynamic selection.

When designing an agent operation or capability, integrate model selection into its API and lifecycle. Do not use `Agent.override(model=...)` to patch a missing model parameter, capability integration, or lifecycle design. Do not use `Agent.override(model=...)` for application routing. An active `Agent.override(model=...)` supersedes an explicit run model and skips capability selection.

# Requirements of all contributions

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

PR titles feed directly into the release changelog. Write one as an imperative sentence naming the change — no `fix:` / `docs:` / `chore:` prefix, which belongs on the commit subject and not on the title — and wrap every code identifier (class names, keyword arguments, module paths, CLI flags, env vars, file paths) in backticks. Check the convention against merged PRs rather than commit subjects, which follow a different one: `gh pr list --state merged --limit 20`.

Never add yourself (Claude) as a co-author on commits. Commits should be authored as the user only, with no `Co-Authored-By` trailer referencing Claude.

## Pushing changes

Before every push, and until the PR lifecycle is complete, follow the
`pushing-commits-to-the-repo` skill. Do not idle after pushing.

Branch state that has to outlive one session -- the issue brief, the decisions log, session
handoffs -- lives in the `branch-context` skill, which `pushing-commits-to-the-repo` reads. Bootstrap
it with `initialize-worktree` on new work or `adopt-pr` on an existing PR, and read it at the start
of every session on that branch.

**A restriction is a conclusion you earn from a real failure, not a field you read.** Never report an
operation as blocked, unavailable, or not-permitted based on a metadata flag, a config field, or a
docs claim — attempt it and quote the actual error. (`maintainerCanModify: false` on a PR does *not*
mean you cannot push: it governs the upstream-maintainer auto-grant, not your own access to the
fork.) If you genuinely cannot attempt it, say "not attempted", never "we can't".

**Do not leave work uncommitted.** Don't end a turn with unstaged or uncommitted local changes
unless the user's own instructions say otherwise.

## Repository structure

The repo contains a `uv` workspace defining multiple Python packages:

- `pydantic-ai-slim` in `pydantic_ai_slim/`: the [agent framework](docs/agent.md), including the `Agent` class and `Model` classes for each model provider/API
    - This is a slim package with minimal dependencies and optional dependency groups for each model provider (e.g. `openai`, `anthropic`, `google`) or integration (e.g. `logfire`, `mcp`, `temporal`).
- `pydantic-graph` in `pydantic_graph/`: the type-hint based [graph library](docs/graph.md) that powers the agent loop
- `pydantic-evals` in `pydantic_evals/`: the [evaluation framework](docs/evals.md) for evaluating the arbitrary stochastic functions including LLMs and agents
- `clai` in `clai/`: a [CLI](docs/cli.md) (with an optional [web UI](docs/web.md)) to chat with Pydantic AI agents
- `pydantic-ai-harness` in `src/pydantic_ai_harness/`: the [capability library](docs/harness/index.md) built on the packages above, with tests in `tests/harness/` and a contributor guide in `src/pydantic_ai_harness/AGENTS.md`. Released as `0.X.Y` alongside pydantic-ai `2.X.Y`.
- `pydantic-clai2` in `src/pydantic_clai2/`: a capability-aware terminal client built on the harness, with tests in `tests/clai2/` and a guide in `src/pydantic_clai2/AGENTS.md`. Released with the harness.
- `pydantic-ai` defined in `pyproject.toml` at the root, bringing in the packages above as well as the optional dependency groups for all model providers and select integrations.

## Development workflow

The project uses:

- [`uv`](https://docs.astral.sh/uv/getting-started/installation/), supporting Python 3.11 through 3.15
    - Install all dependencies with `make install`
- `pre-commit`, installed and set up by `make install` (if it isn't available, `make install` installs it with `uv`)
- `ruff` via `make lint` and `make format`
- `pyright` via `make typecheck`
- `pytest` in `tests/`, via `make test`, with:
    - `inline-snapshot` for inline assertions
    - `cassetter` for recording and playing back requests to model APIs
- Documentation is published by [pydantic/unified-docs](https://github.com/pydantic/unified-docs).
  `docs/navigation.yml` owns the Pydantic AI sidebar, routes, and redirects; `tests/test_examples.py`
  tests all code examples in the docs (including docstrings).
- [`logfire`](docs/logfire.md) for OTel instrumentation of Pydantic AI and `httpx`
    - If you have access to the Logfire MCP server, you can use it to inspect agent runs, tool calls, and model requests

## Test process isolation

Do not use subprocesses to test logic that can run in-process. Starting another interpreter and importing the project again makes the full test suite materially slower. Reserve subprocesses for behavior that depends on the process boundary, such as interpreter startup, import isolation, or signal handling; call a CLI's entry point in-process. `tests/cost_guards.py` fails a test that launches a Python interpreter unless it is marked `@pytest.mark.subprocess(reason=...)`; see "Test cost" in [tests/AGENTS.md](tests/AGENTS.md).

## When to verify

Pre-commit runs `make lint`, `make format` and the [cognitive complexity check](agent_docs/complexity.md) automatically on every commit. CI runs the repository-wide type check, test, and coverage gates. Do not run repository-wide Pyright, pytest, or coverage locally. While iterating, only run targeted checks on the files/tests you have a specific reason to suspect:

- typecheck a single file: `PYRIGHT_PYTHON_IGNORE_WARNINGS=1 uv run pyright path/to/file.py`
- run a single test: `uv run pytest path/to/test.py::test_name`

Avoid `make typecheck` and `make test` — both are slow and CI covers them at the right time.

# Coding Guidelines

When generating or reviewing code anywhere in this repo, always read [agent_docs/index.md](agent_docs/index.md) and follow/enforce those guidelines. Don't forget to read the linked "topic guides" when appropriate.

Additionally, always read the directory-specific instructions when working in those directories:

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

--- project-doc ---

# Testing Guidelines

## Testing philosophy

Every `async def` test runs via the anyio pytest plugin automatically (`anyio_mode = "auto"` in
`pyproject.toml`); don't add `@pytest.mark.anyio`. The async backend defaults to asyncio. Use
`uv run pytest <test-path> --anyio-backend=trio --record-mode=none` to run selected portable tests on Trio without duplicating the default suite. During the Trio migration,
run affected concurrency tests once per backend. Keep broad Trio runs manual or periodic; do not add a
second backend to every ordinary CI matrix. The selector does not imply that every test or integration
already supports Trio. `tests/harness` and `tests/clai2` pin `anyio_backend` to asyncio in their `conftest.py`;
don't re-override it per file.

VCR + public-API tests are the default. We test through the public API the way a user would (`Agent(...)`, `agent.run(...)`) against real provider responses recorded as cassettes — provider APIs are the ultimate judge of whether the code is correct when run as intended, and that user-facing correctness is what we care about, not behavior in isolated units.

Unit tests still earn their place — for internal behavior that is definitory and worth pinning against drift. That includes behavior you can't reach or reliably trigger through the public API (pre-request guards, defensive branches no real model produces), but also behavior a VCR test wouldn't actually protect: our cassette matchers aren't always sensitive to the request body, so a changed internal payload can still match an existing recording and pass green — a unit test asserting the internal shape directly is what catches that regression. Each unit test should still say why it isn't (or can't be) a VCR test.

Recording cassettes needs provider API keys and isn't trivial, so contributors routinely under-test the real behavior — writing the VCR test a contributor couldn't is core maintainer work.

Recorded cassettes also double as a suite-wide prompt-cache prefix regression net. The cache-prefix invariant checks that consecutive requests extend the same serialized provider-cache prefix; tests that deliberately move it through compaction, dynamic tool disclosure, or history rewriting must use `@pytest.mark.moves_cache_prefix(reason=...)` on the test.

`tests/test_history_append_only.py` (core) and `tests/harness/test_history_append_only.py` (Harness) check the same invariant without cassettes, over every capability the packages ship. A new capability is picked up automatically; if it can't be built with its defaults, give it a `FIXTURES` entry (or an `EXEMPT` entry saying why it can't run offline), and, in the Harness file, a `SCENARIOS` entry if it keeps state the conversation should change. A prefix move that is a bug goes in `KNOWN`, linked to the issue or PR that fixes it; a move that is documented behavior (compaction, a request-only tail) goes in `ALLOWED`, which pins how far it may move.

Tests without a cassette get the same check from `fail_function_model_prefix_violations` in `tests/conftest.py`: every request a `FunctionModel` or `TestModel` receives is rendered offline as the body `AnthropicModel` would send, and compared with the previous request of its run, or, for a run's first request, with the latest shorter request that starts with the same message. A test whose conversation moves the prefix on purpose (it changes the tools or instructions between steps, compacts or rewrites history, drops a request-scoped prompt, rewinds a fallback continuation) uses `@pytest.mark.moves_cache_prefix(reason=...)`, preferably with one of the shared reasons in `tests/function_model_prefix.py`. A move the framework shouldn't make is a bug, the counterpart of a `KNOWN` entry above: fix it rather than mark the test, or, when the fix belongs in its own PR, mark it with a reason that links the issue tracking the fix.

## Test File Structure

```python
from __future__ import annotations

import pytest
from inline_snapshot import snapshot

from pydantic_ai import Agent
from pydantic_ai.models import Model
# ... other imports

pytestmark = pytest.mark.vcr


# fixtures/helpers immediately before their test
@pytest.fixture
def my_helper():
    ...


@pytest.mark.parametrize('model', ['openai', 'anthropic', 'google'], indirect=True)
@pytest.mark.parametrize('stream', [False, True])
async def test_feature(model: Model, stream: bool):
    ...
```

## Parametrization with Expectations

For cartesian product tests, use a dict to map parameter combinations to expected results:

```python
from cassetter import Cassette

from pydantic_ai.models import Model

# expectation can be a dataclass, for more complex cases
EXPECTATIONS: dict[tuple[str, bool], str] = {
    ('openai', False): 'expected output for openai non-streaming',
    ('openai', True): 'expected output for openai streaming',
    ('anthropic', False): 'expected output for anthropic non-streaming',
    ('anthropic', True): 'expected output for anthropic streaming',
}


@pytest.mark.parametrize('model', ['openai', 'anthropic'], indirect=True)
@pytest.mark.parametrize('stream', [False, True])
async def test_feature(model: Model, stream: bool, request: pytest.FixtureRequest, vcr: Cassette):
    """What the test is asserting.

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

Use the `EXPECTATIONS` dict only for a pure cartesian output lookup keyed by `(model, stream)`. For feature-centric files where cases are heterogeneous — different inputs, expectations, and xfails per case, all run through one minimal comprehensive test — use a `@dataclass Case` with sensible defaults plus per-case overrides:

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


@pytest.mark.parametrize('case', [pytest.param(c, id=c.id, marks=c.marks) for c in CASES])
async def test_feature(case: Case):
    agent = Agent(case.model, instructions=case.instructions)
    result = await agent.run(case.prompt)
    assert result.all_messages() == case.expected_messages
```

Each case carries its own snapshot (not the central test body), so a reviewer can read the cases top to bottom and check that every expectation is realistic.

## VCR Workflow

Record cassettes with `--record-mode=rewrite`, verify playback without the flag, and review diffs.
For detailed workflows see `.claude/skills/testing-skill/SKILL.md`.

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

Default for a test that asserts an outbound field: take the capture fixture and assert on what it recorded, snapshotting a projection when the whole payload is worth reviewing. Fall back to snapshotting the cassette 