# Ticket 001: Route PreLLM through SubLLM

- Status: IN_PROGRESS
- Workflow state: IMPLEMENTATION
- Owner: agent:codex under SESSION_EXECUTION_AUTHORIZATION

## Goal

Make public `subactor-subllm` the default execution boundary for PreLLM so
provider, model, credentials and paid fallback policy are centrally owned.
Direct Z.AI `glm-5.3` is selected by the registered `prellm/preprocess` and
`prellm/execute` routes.

## Acceptance criteria

- [ ] Production completion defaults to `subllm.complete()`.
- [ ] Small and target execution calls use explicit route functions.
- [ ] LiteLLM remains available only through an explicit legacy opt-in.
- [ ] Missing or incompatible SubLLM fails closed.
- [ ] Hermetic tests and the existing suite pass.
