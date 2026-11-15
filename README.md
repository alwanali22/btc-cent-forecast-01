# BTC cent forecast — 4 hours ahead

Entry for make.fun `btc-cent-forecast-01`: forecast Bitcoin's US-dollar
price 240 minutes after each checkpoint, from the 4,320 one-minute closes
of the 72 hours up to the checkpoint.

## Method

The 4-hour-ahead conditional median is estimated by shrinking the
checkpoint close 50% toward the trailing 6–8 hour level:

```
forecast = 0.5 * last close
         + 0.25 * median(last 360 closes)
         + 0.25 * median(last 480 closes)
```

Backtested on the kit's 6 practice cases (264 walk-forward checkpoints):
MAE **43,056 cents** vs persistence **45,117** (−4.57%); on the 5 practice
cases with locally known answers **44,515** vs **47,055** (−5.40%). The
estimator beats persistence on every one of the 6 practice series, in both
halves of the walk-forward. Momentum and linear-trend extrapolation were
tested and rejected (worse than persistence on the same checkpoints). The
weight is fixed: with ~264 correlated checkpoints, an adaptive rule would
add estimation variance without a demonstrable gain.

## Run

```sh
python3 main.py   # reads $MAKEFUN_INPUT_DIR (default /input), writes $MAKEFUN_OUTPUT_DIR (default /output)
```

Stdlib only, no network, no randomness — two runs on the same case produce
byte-identical output. Output per case is exactly
`{"forecasts":[{"case": "<id>", "price": <number>}]}`.

## Files

- `main.py` — the forecaster (Python 3.13, stdlib only)
- `LICENSE` — MIT
