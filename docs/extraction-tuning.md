# Extraction tuning guide

How to tune the extraction pass when quality or throughput is not where
you want it. Audience: whoever owns the next corpus. Every knob here has
a default that shipped for a reason; change them with data, not vibes.

## Batch size

`GRAPHMIND_EXTRACT_BATCH_SIZE` (default 8) controls how many chunks ride
in one batched completion. Raising it cuts per-call overhead roughly
linearly up to the point where the model starts dropping triples from
the middle of the batch — for the default model that cliff shows up
around 12–16 chunks. Measure yield per batch, not just latency, when
you tune this.

## Confidence floor

`GRAPHMIND_EXTRACT_MIN_CONFIDENCE` (default 0.0 = keep everything)
drops triples below a score at parse time. Model-reported confidence is
calibrated loosely at best; treat the floor as a noise gate, not a
truth filter. Start at 0.3 for noisy corpora and watch
`dropped_low_confidence` in the extraction stats before going higher.

## Citation requirement

`GRAPHMIND_EXTRACT_REQUIRE_SPAN=true` makes the prompt demand a
verbatim source span per triple and drops any triple that lacks one.
This is the single most effective anti-hallucination knob we have (see
the 2026-05-20 incident), at the cost of dropping some legitimate
triples from models that cannot count offsets reliably.

## Model choice

`GRAPHMIND_EXTRACT_MODEL` defaults to a small, cheap model. Extraction
is structured-output work: what matters is JSON reliability and
instruction following, not creativity. A bigger model buys a couple of
points of recall at several times the cost; spend it only after the
prompt itself is no longer the bottleneck (it usually is).

## Chunk sizing interplay

Chunk size and batch size interact: 8 chunks of 1,200 characters is a
very different prompt from 8 chunks of 300. Small chunks raise recall
on dense text but multiply calls; large chunks do the opposite. If you
change one, re-measure the other — the pairs (600/16), (1200/8),
(2400/4) are roughly equivalent in total prompt volume.

## Retry policy

`GRAPHMIND_EXTRACT_MAX_RETRIES` (default 2) covers transient provider
errors with linear backoff. Raising it past 3 usually hides a real
problem (rate limits, an oversized prompt) rather than fixing one —
watch the `retries` counter; a healthy run retries well under 1% of
calls.

## Measuring quality

There is no substitute for a labeled spot-check set: keep ~20 chunks
with hand-verified triples, run the extractor over them after any
prompt or model change, and compare precision/recall against the last
run. The unit tests keep the parser honest; only the spot set keeps
the model honest.

## Cost estimation

`estimate_extraction_cost()` gives a rough dollar figure from corpus
size and config. It underestimates when retries spike and overestimates
when the corpus is mostly short chunks — within 2x either way, which is
enough for budgeting.
