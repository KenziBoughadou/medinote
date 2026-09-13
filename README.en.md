# MediNote

[![CI](https://github.com/KenziBoughadou/medinote/actions/workflows/ci.yml/badge.svg)](https://github.com/KenziBoughadou/medinote/actions/workflows/ci.yml)

Compare two AI/NLP pipelines on fictional French consultations and inspect the source
of each assertion. **Drafts for review, without clinical validation.**

This is an applied NLP and LLM evaluation project, not a neural-network training project.
The main question concerns the fidelity and cost of two complete pipelines. It does not
isolate the causal effect of extraction alone. There are 132 archived model generations;
final semantic results still require human review.

- **A — direct summary:** one consultation → one LLM call → structured note.
- **B — structured extraction:** one LLM call → typed facts → deterministic Python rendering.

This compares complete pipelines, including different writing methods. B is not assumed
to outperform A. [Français](README.md) · [Experiment protocol](docs/EXPERIMENT_PROTOCOL.md) ·
[Actual acceptance status](docs/ACCEPTANCE.md) · [Three-minute video](docs/assets/demo.webm).

[Open the live demo](https://medinote.kbcompany.fr) — HTTPS and browser workflows verified.
No account is required; live AI generation is available within quotas. The local demo also works
without an API key. Its twelve archived notes are **actual model generations**, with raw responses,
tokens, latency and estimated cost. Semantic performance metrics await annotation.

A separate [AI annotation pilot](docs/ANNOTATION_PILOT.md) examines ten archived notes.
Five forms are complete and five retain unresolved decisions, including partially
covered reference facts. The pilot reports concrete omissions and protocol limitations,
without claiming human review or estimating full-cohort performance.
Screenshots and the video show the earlier illustrative release.

Two additional extractive comparators, lead-5 and TF-IDF centroid-5, now produce 160
archived excerpts without provider calls. This is a separate, post hoc experiment:
[outputs and limitations](eval/results/extractive-posthoc-1/report.md). Selection never
uses gold facts. Length retention is reported, not semantic quality. Offline review packs
and partial annotation checks are described in [the review guide](docs/REFERENCE_REVIEW.md).

## Run locally

Use Python 3.12, uv and Node 22.12 or newer within the Node 22 family.

```bash
uv sync --frozen --group dev --group eval
npm --prefix frontend ci
make demo
```

Open `http://127.0.0.1:5173/?mode=offline`. The bundled consultations, citations, methodology,
results and local Markdown/JSON exports work without the backend. Generation is disabled.
For local API integration, start the following in separate terminals:

```bash
uv run uvicorn medinote.main:create_app --factory --host 127.0.0.1 --port 8000 --no-proxy-headers --no-access-log
npm --prefix frontend run dev
```

Live calls are disabled by default. The public API only accepts an allowed case ID and
method, never free consultation text. Never copy production secrets into the checkout.

## Stack and protocol

React 19, TypeScript 5, Vite 7, Tailwind 4 and bundled Geist; FastAPI, Pydantic 2,
OpenAI Responses and SQLite. Two unprivileged containers: nginx and a single-worker API.
Both methods use `gpt-4.1-mini-2025-04-14`, temperature 0, strict Structured Outputs,
4,000 maximum output tokens, `store=false` and no SDK retries. No semantic repair or
fallback between pipelines is performed. Existing source IDs and valid JSON do not prove
semantic faithfulness.

80 synthetic dialogues: 60 main parents in ten families (20 development, 40 test), plus
ten independent negation stress pairs. Six development cases are public. Source spans
use Unicode code points. Texts and gold references were prepared by AI; **human reference
review and final annotations remain pending; actual generations are archived**. Missing metrics are null.

```bash
uv run medinote corpus validate --root .
uv run medinote plan-status --root .
make check
npm --prefix frontend exec -- playwright install chromium
npm --prefix frontend run test:e2e
```

Frozen manifests capture corpus, gold, prompts, schemas, renderer, code, protocol, prices
and lockfile hashes. Immutable campaigns retain failures and unknown costs. Both final
notes receive semantic claim segmentation, gold alignment and citation assessment.
Metrics use micro aggregation and 10,000 paired bootstrap samples; stress remains separate.
Real calls run inside the active production release and share its budget ledger; see
[deployment commands](docs/DEPLOYMENT.md#campagnes-réelles).

## Delivery and limitations

[Architecture](docs/ARCHITECTURE.md), [dataset card](docs/DATASET_CARD.md),
[model card](docs/MODEL_CARD.md), [evaluation](docs/EVALUATION.md),
[deployment/rollback](docs/DEPLOYMENT.md), [demo script](docs/DEMO_SCRIPT.md).
CI runs offline tests and builds production images on GitHub, including container integration,
image sizes and rollback without restoring the usage database. Releases use full commit SHAs
and image digests. Administrator setup, SSH host verification, Cloudflare and monitoring
must be completed explicitly.

The corpus is synthetic and initially AI-authored. No clinical validation or independent
annotation is claimed. B’s style may reveal its identity during blinded annotation.
The shared ceiling is USD 10 estimated before tax per UTC month. Each attempt reserves
USD 0.025; public limits are six attempts per visitor and thirty total per UTC day, with
one concurrent generation. Unknown usage remains charged conservatively. Versioned prices
do not deduct caching discounts. No fabricated scientific results are included.

Code: [MIT](LICENSE). Original corpus and annotations: [CC BY 4.0](data/LICENSE), with provenance.
