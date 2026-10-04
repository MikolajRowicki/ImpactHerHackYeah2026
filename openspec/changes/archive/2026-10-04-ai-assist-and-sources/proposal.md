# Proposal

## Why

The backend has had both AI helpers ("say it for me" and the conversation guide) since `full-backend`, but no screen uses them, so the demo shows no AI at all. Cited Polish sources were planned from the start and the backend already has a slot for them, but it is always empty. A check against Groq on 2026-10-04 also showed that the default model `llama-3.3-70b-versatile` no longer exists (`model_not_found`), so turning Groq on today would silently give only the fixed fallback texts.

## What Changes

**Frontend**
- **"Powiedz to za mnie"** for the mother: a screen reached from a card on her start screen. She writes what she wants to say (up to 500 characters) and picks who it is for (partner or close people) and a tone (gentle or direct). She gets a suggested message she can copy, or ask for another one. A crisis answer shows the crisis lines instead of a message. Her text is not kept in the browser.
- **"Jak z nią rozmawiać"** for a partner or supporter: a screen reached from a card on their start screen, and from the summary when it needs attention (opens the topic on suggesting professional help). It has five topics, and each shows opening lines, things to avoid, follow-up questions and the **sources** behind the text as links.
- Generated text is labelled by where it came from (AI, sample, or nothing for the fixed texts).
- Mock mode mirrors both operations.
- No new navigation items. On phones the bottom bar already holds six.

**Backend**
- A **curated knowledge source** (light retrieval, no embeddings). About a dozen short passages live in a JSON file in the repository. Each one is a summary in our own words of a public Polish page, with its title and link. Retrieval matches the topic and keywords and returns at most three passages, best first. `KNOWLEDGE_SOURCE` defaults to `curated`, and `none` switches it off.
- Only the conversation guide asks the knowledge source. "Say it for me" and the summary narrative never do. Her words are never a search query, and a personal message carries no citations.
- The default Groq model changes to one Groq serves today (`qwen/qwen3.8-27b`). `GROQ_MODEL` still overrides it. A `<think>` block that a model may put in its answer is removed.
- The prompts ask for wording that does not reveal the gender of the person who speaks (guide) and does not assume the partner's gender (say it for me).
- Contract: no operation or schema changes. One new example shows a guide with sources.

## Non-goals

- Free-text questions to the knowledge base (a "ask about postpartum depression" chat), embeddings, vector search, or fetching pages at runtime.
- Sources under "say it for me".
- UI for `get_preferences`, `update_preferences` and `list_reminders`.
- Deployment and slides (other team members own them).
- Any change to an existing operation, schema or error code.

## Capabilities

### New Capabilities
- `frontend-ai-assist`: the mother's "say it for me" screen and the loved ones' conversation guide with its sources, their entry points, labels, crisis answer and mock mode.

### Modified Capabilities
- `ai-assist`: the knowledge-source requirement now covers the curated source and its default, and says which features cite.
- `ai-provider-config`: the Groq model comes from the environment with a default Groq serves, and only the final answer of a model is used.

## Impact

- Backend: `core/ai/knowledge.py` (curated source), `core/ai/assist.py` (retrieval only on request), `core/services/assist_guide.py` and `assist_say_it.py` (query and prompts), `core/ai/groq.py` (think block), `config/settings.py` (defaults), new `core/content/knowledge.json`. Tests are in `tests/`. Two existing tests change on purpose: the default knowledge source, and sources for "say it for me".
- Contract: new example `contracts/examples/ai_conversation_guide.200.sources.json` only.
- Frontend: two new screens, routes, start-screen cards, a summary link for loved ones, `api.js` query parameters, `operations.js`, mock store, strings, CSS. Browser tests in `tests_e2e/`.
- Configuration: `.env.example` (`KNOWLEDGE_SOURCE=curated`, model comment). Local `.env` files that say `KNOWLEDGE_SOURCE=none` must change it to see sources.
- Docs: `docs/architecture.md` (knowledge source), worklog.

## Assumptions to confirm at review

1. **Placement:** both screens are opened from cards on the start screens (mother: "Powiedz to za mnie"; partner and supporter: "Jak z nią rozmawiać"), not from new navigation items. A loved one whose summary needs attention also gets a link to the professional-help topic.
2. **Labels:** text from Groq says "Przygotowane z pomocą AI". When sources were used, it adds "na podstawie źródeł poniżej". Mock text says "Tekst przykładowy". Fixed rule texts get no label.
3. **Default knowledge source is `curated`**, so the deployed app cites sources without extra settings. Your local `.env` has `KNOWLEDGE_SOURCE=none`; change it to `curated` (or delete the line).
4. **Model:** `qwen/qwen3.8-27b` wrote the most natural Polish in a short test against `openai/gpt-oss-120b`, and answered in 0.2–0.5 s. Both have the same free limits for this key (1000 requests a day, 8000 tokens a minute). `openai/gpt-oss-120b` is the alternative via `GROQ_MODEL`. With `AI_PROVIDER=groq`, every summary also calls Groq for its narrative and shows it (this is existing behaviour).
5. **Passages:** I write them as short summaries in plain Polish from public pages I open and check (for example pacjent.gov.pl, Fundacja Rodzić po Ludzku, 116 123, Centrum Wsparcia). They are general, not medical advice, and need a specialist's read before real use.
6. **Who and when:** "Say it for me" is open to the mother of an active or closed group (like the check-in). The guide is open to a partner or supporter of an active or closed group (like tasks).
7. **Copy:** the copy button uses the clipboard. When the browser refuses, the text is selected so it can be copied by hand.
8. "Inna propozycja" asks the same question again. No history of suggestions is kept.
