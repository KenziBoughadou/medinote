# MediNote

[![CI](https://github.com/KenziBoughadou/medinote/actions/workflows/ci.yml/badge.svg)](https://github.com/KenziBoughadou/medinote/actions/workflows/ci.yml)

**When summarizing a medical consultation with an LLM, is it better to write
the note directly or to extract the facts first?**

I compare two ways of producing a consultation note from a fictional French
dialogue, using the same language model. I measure what each note keeps, omits
or distorts, and what it costs. A web application lets you compare both notes
and trace every sentence back to its source.

Personal academic project · applied NLP and LLM evaluation · Python, FastAPI,
React, TypeScript · **not for clinical use**

[Live demo](https://medinote.kbcompany.fr) · [Detailed results](docs/HUMAN_REVIEW_RESULTS.md) ·
[Protocol](docs/EXPERIMENT_PROTOCOL.md) · [Français](README.md)

## At a glance

- **Extracting facts first does not make the note more faithful, on this corpus.**
  Direct writing (A) keeps 95.8% of the expected facts, versus 92.5% for structured
  extraction (B). The −3.3 point gap is clear: its 95% confidence interval runs
  from −5.3 to −1.4 points.
- **B costs twice as much and takes twice as long**: 2.3 s versus 5.0 s median
  latency per note.
- **No unsupported information** was found in the 80 reviewed test notes. Errors
  are mostly omissions: 15 missed facts for A, 26 for B, out of 360 each.

![Fictional dialogue and side-by-side comparison of both notes with their sources](docs/assets/readme-comparison.png)

*The demo shows the dialogue, then both notes. Each sentence links to the
passage of the dialogue that supports it. The interface is in French.*

## What I take away

- **Structure does not guarantee faithfulness.** B produces more items than A
  (432 versus 364) but loses more expected facts. By splitting the dialogue into
  isolated facts, extraction drops details: an announced follow-up action,
  an observation without a number.
- **The two methods do not lose the same things.** In the negation test, B keeps
  the patient's scheduling preference in 20 notes out of 20, A in 2 out of 20.
  Structure seems to help keep point details, which direct writing tends to summarize.
- **A strict format can make an error very visible.** B produced "absence of
  medical treatment — negated": the format is valid and the citation points to
  the right passage, but the meaning is reversed.
- **A correct citation does not prove the sentence is right.** You still have to
  read the cited passage; the demo makes that easier but does not replace it.

## Results

40 test consultations, one note per method and per consultation. I reviewed
them one by one, under neutral identifiers that hid the method.

| Measure | A, direct | B, structured | B−A gap [95% CI] |
|---|---:|---:|---|
| Expected facts correctly kept | 95.83% | 92.50% | −3.33 points [−5.28; −1.39] |
| Expected facts omitted | 4.17% | 7.22% | +3.06 points [+1.11; +5.00] |
| Contradictory information in the note | 0.00% | 0.23% | +0.23 points [0.00; +0.71] |
| Unsupported information in the note | 0.00% | 0.00% | 0.00 points |
| Mean cost per note | $0.00079 | $0.00158 | ×2.00 [1.95; 2.05] |
| Median latency | 2.29 s | 4.98 s | ×2.17 [1.94; 2.29] |

Intervals come from a paired bootstrap over the 40 consultations (10,000 samples).
All 132 model calls cost about $0.15 in total.

**Negation test.** Ten pairs of dialogues differ only by one negation ("I report
a fever" / "I do not report a fever"). Both methods keep the flipped fact (10 pairs
out of 10 for A, 9 out of 10 for B). Neither passes the strict criterion, which
also requires every other fact: all 40 notes omit that the origin of the complaint
remains to be clarified. This overly aggregated criterion therefore does not separate
the methods; the [detailed diagnostic](eval/results/stress-diagnostic-v1/) reports
each dimension separately.

The [analysis of nine errors](docs/ERROR_ANALYSIS.md) (in French) shows concrete
cases with the dialogue, the note and the annotation.

## Method

- **A, direct writing**: the model reads the dialogue and writes a note in seven
  sections, with a reference to the source passage for each sentence.
- **B, extraction then rendering**: the model extracts typed facts (subject,
  negation, timing, certainty), then a Python program renders them with fixed
  rules, without a second model call.
- **Model**: `gpt-4.1-mini` through the OpenAI API, JSON outputs constrained by
  a schema, one generation per method and per case.
- **Data**: 80 fictional consultations in French (20 development, 40 test,
  10 negation pairs), with 800 reference facts linked to their source passage.
- **Evaluation**: for each note, I label every piece of information as correct,
  contradictory or unsupported, then list the expected facts that were omitted.

The code, data, prompts and model were
[frozen](https://github.com/KenziBoughadou/medinote/commit/3138ec963c32c6c5acfac93ffddbf0490f5c08ca)
before the test campaign. Since the writing step also differs between A and B,
the observed gap cannot be attributed to the extraction step alone.

[Evaluation rules](docs/EVALUATION.md) · [Annotation guide](eval/annotation-guide.v1.md) ·
[Extractive baselines without an LLM](eval/results/extractive-posthoc-1/report.md)

## Demo

[medinote.kbcompany.fr](https://medinote.kbcompany.fr) presents six fictional
consultations and the twelve notes actually generated for them. You can compare
the notes, open the passage cited by each sentence, export a draft and request a
new generation within a quota. No personal data can be entered.
[Run the demo locally](docs/DEMO.md#lancer-la-démo-en-local)

## Architecture

A React and TypeScript interface displays the dialogues and notes. A Python
backend (FastAPI, Pydantic) prepares requests, validates the model outputs and
builds note B. SQLite tracks the budget and quotas. Docker and GitHub Actions
test and publish each release.

[Detailed architecture](docs/ARCHITECTURE.md) · [System card](docs/MODEL_CARD.md) ·
[Dataset card](docs/DATASET_CARD.md)

## Limitations

- **Synthetic, highly regular corpus.** The dialogues and references were
  generated by an LLM, with 12 turns and 9 expected facts each. Both methods
  therefore come close to the ceiling, and the corpus does not reflect real
  consultations.
- **A single reviewer, myself**, without a second opinion. B's style could reveal
  the method despite the neutral identifiers.
- **An annotation rule changed after seeing the outputs**, to accept five correct
  pieces of information missing from the references. The change is
  [documented](docs/ANNOTATION_AMENDMENT_V1_1.md) and alters neither the dialogues
  nor the generations.
- **One model and one generation per case**: the intervals measure variation
  across consultations, not across generations.
- **No clinical validation**, and no time savings measured in real practice.

## Ideas for a v2

- Evaluate on more realistic dialogues, for example public annotated consultation
  corpora (ACI-Bench, MTS-Dialog).
- Have part of the notes reviewed by a second person from the field and measure
  inter-annotator agreement.
- Compare with an open-weight model running locally, better suited to hosting
  health data.
- Weight errors by clinical severity: missing an allergy matters more than
  missing a scheduling preference.

The [v1 release](https://github.com/KenziBoughadou/medinote/releases/tag/v1)
packages the code, results and analysis. Code under the [MIT](LICENSE) license;
corpus and annotations under [CC BY 4.0](data/LICENSE).
