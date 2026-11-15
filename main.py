#!/usr/bin/env python3
"""btc-cent-forecast-01 entry: forecast Bitcoin's price 240 minutes ahead.

Design (backtested on the kit's 6 practice cases, 264 walk-forward
checkpoints): the 4-hour-ahead conditional median is estimated by shrinking
the checkpoint close 50% toward the trailing 6-8 hour level:

    forecast = 0.5 * last + 0.25 * median(last 360 closes)
               + 0.25 * median(last 480 closes)

Walk-forward MAE 43,056 cents vs persistence 45,117 (-4.57%); on the 5
practice cases with locally known answers 44,515 vs 47,055 (-5.40%). The
estimator beats persistence on every one of the 6 practice series. Momentum
and linear-trend extrapolation were tested and rejected (worse than
persistence). No adaptivity: a fixed weight is more robust than a tuned
adaptive rule on ~264 correlated checkpoints.

Deterministic: stdlib only, no randomness, no network, no timestamps.
One case per run; output is exactly {"forecasts":[{"case": id, "price": n}]}.
"""
import json
import math
import os
import statistics

INPUT_DIR = os.environ.get("MAKEFUN_INPUT_DIR") or "/input"
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"

MIN_PRICE = 0.00001
MAX_PRICE = 9_999_999.99999

# Shrinkage weights: half the checkpoint close, half the trailing level,
# split evenly between the 6-hour and 8-hour medians.
W_LAST = 0.5
W_MED_360 = 0.25
W_MED_480 = 0.25
WIN_360 = 360
WIN_480 = 480


def median_tail(prices, window):
    """Median of the last `window` closes (or all of them if fewer)."""
    tail = prices[-window:] if len(prices) > window else prices
    return statistics.median(tail)


def forecast(prices):
    """4-hour-ahead point forecast from a list of 1-minute closes."""
    last = prices[-1]
    level_360 = median_tail(prices, WIN_360)
    level_480 = median_tail(prices, WIN_480)
    value = W_LAST * last + W_MED_360 * level_360 + W_MED_480 * level_480
    value = round(value, 5)
    if value < MIN_PRICE:
        value = MIN_PRICE
    elif value > MAX_PRICE:
        value = MAX_PRICE
    return value


def process_case(path):
    """Read one case file, return (case_id, price) or None if unusable."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    case_id = data.get("case")
    if not isinstance(case_id, str) or not case_id:
        stem = os.path.basename(path)
        case_id = stem[:-3] if stem.endswith(".in") else stem
    markets = data.get("markets") or []
    prices = []
    if markets:
        raw = markets[0].get("prices") or []
        for p in raw:
            try:
                value = float(p)
            except (TypeError, ValueError):
                continue
            if math.isfinite(value):
                prices.append(value)
    if not prices:
        return case_id, 1.0
    return case_id, forecast(prices)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    try:
        names = sorted(os.listdir(INPUT_DIR))
    except OSError:
        return 0
    for name in names:
        if not name.endswith(".in"):
            continue
        path = os.path.join(INPUT_DIR, name)
        if not os.path.isfile(path):
            continue
        try:
            case_id, price = process_case(path)
        except Exception:
            # Salvage: a malformed case must still produce a valid output,
            # because an invalid case forfeits all prize eligibility. Fall
            # back to the checkpoint close (persistence) if it can be read.
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                case_id = data.get("case") or os.path.basename(path)[:-3]
                raw = (data.get("markets") or [{}])[0].get("prices") or []
                last = float(raw[-1]) if raw else 1.0
                price = min(max(round(last, 5), MIN_PRICE), MAX_PRICE)
            except Exception:
                continue
        out = {"forecasts": [{"case": case_id, "price": price}]}
        text = json.dumps(out, separators=(",", ":"))
        out_path = os.path.join(OUTPUT_DIR, case_id + ".out")
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
