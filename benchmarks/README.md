# Selected historical comparisons

<!-- PLACEHOLDER: owner-selected introduction, chart and interpretation. -->

These recorded results compare the listed implementations of one exact matching
task. They do not establish the fastest possible implementation in either vendor
library. No other optimized search implementation is distributed here.

Each time is the median in microseconds for an entire batch of 128 ascending
queries, 256 peaks, harmonic orders 1–32, and strict 2 Hz eligibility. Queries span
either 100–400 Hz or 30–60 Hz. Matching includes validation, required conversion,
strict rejection, ties and output construction. Allocation and cache loading are
outside this timing. These are recorded SDK/adapter measurements, not timings of
the new protected ABI wrappers or of complete audio processing.

| Implementation | 100–400 Hz, µs | 30–60 Hz, µs | Persistent bytes | Relative time, 30–60 Hz |
|---|---:|---:|---:|---:|
| DM-MHM Standard | 9.889 | 11.040 | 2,392 | 1.00× |
| DM-MHM Automatic | 10.187 | 20.002 | 2,392 | 1.81× |
| Intel IPP 2026.1.0 exact matching adapter | 255.387 | 275.761 | 8,632 | 24.98× |
| KFR 7.2.0 integer matching adapter | 549.990 | 593.153 | 4,536 | 53.73× |

Relative time is implementation time divided by Standard time; lower is better.
Automatic selection is a dispatch policy, not a claim of fastest measured mode.
Persistent bytes exclude returned outputs and temporary stack space. The recorded
benchmark additionally used 32,928 output bytes per case, including its result
metadata; the new ABI has its own explicitly documented output shape.

The 100–400 Hz workload places 1,073/4,096 harmonic targets within the 2 kHz peak
range (26.2%). The 30–60 Hz workload places 4,096/4,096 there (100%). This is target
range coverage, not the percentage of matched peaks or a task accuracy score.

Environment: AMD Ryzen 7 260; Linux under Windows; GCC 13.3.0; logical CPU 15;
five serial processes with 50 samples per point, 250 samples total; sanitizers
disabled. The comparison is selected, host-specific evidence, not a global
optimality claim. Stronger private reference comparisons remain outside this
repository and are not characterized as vendor baselines.

Numerical authority: *Matching Through 32 Harmonics*, pages 2–3, PDF SHA-256
`cfd1a02895ba30e3cdd1aa8f28b53508ab2e704d04750496a682aa2fb1231eb1`.
The source PDF contains additional unselected material and is not included.
Values above retain its printed precision. New wrappers require new measurements.

<!-- PLACEHOLDER: owner-selected raw artifacts, public receipt IDs and charts. -->
