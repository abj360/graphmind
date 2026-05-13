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
