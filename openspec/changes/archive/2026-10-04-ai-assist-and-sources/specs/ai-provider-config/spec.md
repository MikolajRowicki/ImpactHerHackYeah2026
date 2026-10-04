# Spec Delta

## ADDED Requirements

### Requirement: Groq model comes from the environment
The Groq provider SHALL ask for the model named in `GROQ_MODEL`. When the variable is empty, it SHALL ask for `qwen/qwen3.8-27b`, a model Groq served on 2026-10-04.

#### Scenario: Default model
- **WHEN** `GROQ_MODEL` is unset and a text is generated with Groq
- **THEN** the request names the model `qwen/qwen3.8-27b`

#### Scenario: Chosen model
- **WHEN** `GROQ_MODEL=openai/gpt-oss-120b` and a text is generated with Groq
- **THEN** the request names the model `openai/gpt-oss-120b`

### Requirement: Only the final answer is used
When a model's answer holds a reasoning block between `<think>` and `</think>`, the provider SHALL drop that block and use the rest. An answer that is empty after this SHALL count as an empty answer.

#### Scenario: Think block
- **WHEN** Groq answers "<think>plan</think>\nTekst."
- **THEN** the generated text is "Tekst."

#### Scenario: Only thinking
- **WHEN** Groq answers with nothing but a think block
- **THEN** the feature returns its fallback with `source` `rules`
