# The lines under test

Nine rows: six of the most-shared AGENTS.md and CLAUDE.md additions on X, and three rows for Beau Hartshorne's
claim that Codex truncates AGENTS.md at 32 KiB and that cutting 25% of Instant's instructions improved their evals.
Reach is as scraped on 2026-11-04 between 00:15 and 00:27 CT. The exact text of each arm is in `arms/`, pinned by
sha256 in `arms/arms.json`.

| Row | What the post says to add | Source | Reach |
|---|---|---|---|
| `secondary-labels` | "Avoid unnecessary secondary labels and descriptions. Let the layout do the explaining." | [@luinlee](https://x.com/luinlee/status/2113085361836744764) | 7,752 likes, 10,578 bookmarks |
| `ux-dx-ax` | "Cut taglines, helper text and secondary labels. If a screen needs them to make sense, fix the layout." and "Make the best decision that will elevate all three: the user experience (UX), developer experience (DX), and agent experience (AX) always, without breaking anything." | [@Voxyz_ai](https://x.com/Voxyz_ai/status/2113254050170843418) | 7,088 likes, 14,619 bookmarks |
| `marcos-full` | A seven-rule file that opens "Do not preserve backward compatibility" and asks for the simplest implementation, layered growth and established libraries | [@MarcosHernanz](https://x.com/MarcosHernanz/status/2083954734487212511), transcribed from the post's image | 10,789 likes, 20,021 bookmarks |
| `docs-vs-code` | "When a repository's documentation and its existing code disagree, follow the conventions used in the existing code, and in your final reply point out each inconsistency you found between the documentation and the code." | [@ai_database](https://x.com/ai_database/status/2114184481951330365), from arXiv 2610.30571 | 6,313 likes, 9,352 bookmarks |
| `plain-english` | A paragraph asking for plain English in every reply, with 23 banned words ("load-bearing", "footgun", "blast radius" ...) | [@drummatick](https://x.com/drummatick/status/2115102978848022571), transcribed from the post's image | 2,384 likes, 2,833 bookmarks |
| `karpathy` | The 65-line Karpathy-style CLAUDE.md: think before coding, simplicity first, surgical changes, goal-driven execution | [@Saccc_c](https://x.com/Saccc_c/status/2058467100537090544), pointing at github.com/multica-ai/andrej-karpathy-skills | 2,282 likes, 4,018 bookmarks |
| `long-file` | A real 52 KB AGENTS.md pair against no file: "Claude Code reads more, but more is not better" | [@hartshorne](https://x.com/hartshorne/status/2117848891303612427) | 6 likes |
| `cut-25` | The same 52 KB file with a random 25% of its blocks removed, against the full file | [@hartshorne](https://x.com/hartshorne/status/2117848891303612427) | 6 likes |
| `trunc-32k` | The same file cut at 32,768 bytes, which is what Codex passes on, against the full file | [@hartshorne](https://x.com/hartshorne/status/2117848891303612427); `DEFAULT_PROJECT_DOC_MAX_BYTES = 32 * 1024` in openai/codex `codex-rs/config/src/config_toml.rs`, truncation in `codex-rs/core/src/agents_md.rs` | 6 likes |

Hartshorne's post has little reach next to the others; it is here because the brief asks for it and because it is
the only claim in the set that says a change was measured.

## Notes on each source

- **Reach is not a test.** None of the six viral posts reports a measurement. The AIDB post cites a paper whose
  setting is different from this battery: there, instruction files were made stale on purpose, so the docs and the
  code disagreed. Here nothing disagrees, so the row asks only what the sentence costs when it does not apply.
- **The UI lines have no UI to act on.** The battery is Python only. `secondary-labels` and the first half of
  `ux-dx-ax` are expected to do nothing here, which makes them a fair check of whether an instruction that does not
  apply still changes the pass rate. Whether they make interfaces look better needs a validated taste grader and is
  not measured.
- **The long file is a stand-in.** Instant's instructions and their cut are not public (the only AGENTS.md in
  github.com/instantdb/instant is the 14.5 KB create-instant-app template, last changed 2026-06-08). The stand-in is
  pydantic/pydantic-ai's root `AGENTS.md` and `tests/AGENTS.md` at commit 7d1d3f0 (MIT), joined with Codex's own
  separator, 52,497 bytes. The cut removes whole blank-line-separated blocks chosen at random with a fixed seed until
  25% of the bytes are gone; Hartshorne's cut was presumably chosen by hand, so this measures length, not judgment.
- **The probe rule.** The long arms end with one rule an agent can visibly follow: "Every Python file you create or
  modify must begin with this exact first line: # Reviewed under AGENTS.md". It starts at byte 52,392, past the 32 KiB
  cut, so the truncated arm loses it. It is a positive control (see PREREGISTRATION.md section 7), not a line under
  test.
- **The Karpathy file is not committed.** Its repository has no license, so `scripts/build_arms.py` fetches it at
  commit 2c60614 and checks its sha256. The other texts are short quotes with attribution, or MIT.
