# Tasks

Each group is one commit. Before each commit: `ruff check .`, `ruff format --check .`, `pytest tests`; groups that touch the frontend also run `pytest tests_e2e`.

## 1. Groq model and prompts (backend)

- [x] 1.1 Set the default `GROQ_MODEL` to `qwen/qwen3.8-27b` in `config/settings.py` and the `.env.example` comment; verify with tests that the request body names the default model when the variable is unset and the chosen one when it is set.
- [x] 1.2 Remove a `<think>…</think>` block from Groq answers before the empty check; verify with tests for "think block then text" and "only a think block gives the fallback labelled rules".
- [x] 1.3 Reword the guide prompt (no first-person forms that show gender, with examples) and the "say it for me" prompt (do not assume the partner's gender), drop generated guide lines with such forms, and cite nothing when the fixed lines are used; verify with tests that the prompts hold these instructions and for the scenarios of "Opening lines do not show the speaker's gender", and with one manual Groq call per prompt, noted in the worklog.
- [x] 1.4 Add the worklog entry for this group in `docs/worklog/main.md`; verify ruff, format check and `pytest tests` pass, then commit.

## 2. Curated knowledge source (backend)

- [x] 2.1 Write `core/content/knowledge.json`: about a dozen short passages in plain Polish, written from public Polish pages opened and read during this task, each with id, title, https link, text, topics and keywords; verify every link answers, and verify with a data test that ids are unique, links are https, texts have at most 400 characters, keywords exist, topics are known and every topic has a passage.
- [x] 2.2 Add the curated source to `core/ai/knowledge.py` (fold, topic +3, keyword prefix +1, best first, at most three) and make `curated` the default in settings and `.env.example`; verify with tests for topic match, order, word forms and diacritics, no match, the limit of three and the default.
- [x] 2.3 Let `assist.generate` retrieve only when a feature passes a query: the guide passes `"<topic> <brief>"`, while "say it for me" and the narrative pass none. Update the tests that change on purpose (two passages with an explicit query; sources listed only for the guide; default guide sources now come from the file). Verify with tests that "say it for me" and the narrative never ask the knowledge source, and that every topic gets one to three sources.
- [x] 2.4 Add `contracts/examples/ai_conversation_guide.200.sources.json`; verify the contract example tests validate it against the schema.
- [x] 2.5 Describe the knowledge source, the retrieval and the defaults in `docs/architecture.md` (and in the README if it lists AI variables, checking any command there), add the worklog entry, and verify ruff, format check and `pytest tests` pass, then commit.

## 3. "Say it for me" screen (frontend)

- [x] 3.1 Add both AI operations to `js/operations.js` and a `query` option to `api.js`; verify `tests/test_frontend_operations.py` passes and a browser test sees `?topic=` on the live request.
- [x] 3.2 Add `js/mock-ai.js` with sample messages and the crisis subset, and a mock-store handler for `ai_say_it_for_me` (mother only, 1–500 characters, crisis answer); verify with a mock-mode browser test that no request goes to `/api/v1`.
- [x] 3.3 Build `#/say-it` (form, counter, recipient, tone, result with copy and another suggestion, labels, crisis lines, waiting state, error that keeps the text), the card on the mother's start screen, strings and CSS; verify with browser tests for every scenario of "Say it for me screen", "Crisis answer", "Waiting for an answer", the labels, and who can open it, at 375 px and on a laptop width.
- [x] 3.4 Add the worklog entry; verify ruff, format check, `pytest tests` and `pytest tests_e2e` pass, then commit.

## 4. Conversation guide with sources (frontend)

- [x] 4.1 Add a mock-store handler for `ai_conversation_guide` (partner and supporter only, topic check, per-topic content, sample sources); verify with a mock-mode browser test.
- [x] 4.2 Build `#/talk` and `#/talk/:topic` (topic list, three sections, sources with site name opening in a new tab, labels, other opening lines), the card on the loved ones' start screen and the `needs_attention` link in their summary, with strings and CSS; verify with browser tests for every scenario of "Conversation guide screen", "Sources under the guide", "Entry points" and the guide labels, at 375 px and on a laptop width.
- [x] 4.3 Add a live browser test against the seeded backend with the curated source: a supporter opens a topic and sees source links from the file; verify it passes.
- [x] 4.4 Add the worklog entry; verify ruff, format check, `pytest tests` and `pytest tests_e2e` pass, then commit.

## 5. Verification and archive

- [x] 5.1 Run the real app with `AI_PROVIDER=groq` on a throwaway copy of the database, use both screens as the mother and as a supporter, and take screenshots at phone and laptop width; verify the texts come from Groq, the sources open, and record the result in the worklog.
- [x] 5.2 Have a fresh reviewer check the change against the specs (every scenario mapped to a test, real defects with failing scenarios, PASS or FAIL); fix the findings and review again until PASS, recording each round in the worklog.
- [x] 5.3 Archive the change (`openspec archive ai-assist-and-sources`), verify `openspec validate --specs` passes, commit, merge into `main` and push.
