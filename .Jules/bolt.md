## 2024-05-22 - Exponential Backoff Overflow Hazard
**Learning:** Calculating backoff using `2 ** count` is extremely dangerous if `count` can accidentally become a large number (e.g. a timestamp due to a bug). This results in an infinite CPU hang trying to compute `2 ** 1.7e9`.
**Action:** Always cap the exponent or validate the input range before performing exponential calculations, even in error handling paths.
