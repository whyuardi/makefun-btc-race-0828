# Crash-Rebound Rider — btc-race-24h-20261115-0828

## Idea
Buy only after a deep 120-minute drop, once the price has bounced off its
120-minute low and broken above its 15-bar high; then ride the recovery
with a trailing stop and no fixed take-profit.

Entry (on a bar's close, integer bps math):
- close at least 125 bps below the highest close of the previous 120 bars,
- close at least 20 bps above the lowest close of the previous 120 bars,
- close more than 12 bps above the highest close of the previous 15 bars.

Exits (from the entry decision close):
- no fixed take-profit; trailing stop arms at +50 bps, trails 50 bps below
  the highest close since entry,
- stop loss -100 bps,
- maximum hold 120 bars,
- 15-bar cooldown after any exit.

Sizing: full cash on entry, full position on exit, one position at a time,
max_slippage_bps 100.

## Evidence (exact replay of the kit engine, validated to the unit against
grade-local on buy-and-hold: PnL -44.009846, fees 0.782550, 1 trade)
- This competition's dev window: **+$24.682736** net (4 round trips,
  8 trades, fees $3.19399, max drawdown 2.65%).
- Previous race's dev window (out-of-sample, slow grind down -491 bps):
  **+$2.094018** (1 round trip, max drawdown 0.73%).
- Split-half on this dev window: +$2.26 / +$22.43.
- At doubled fees (8 bps + 4 bps): +$21.49.
- Entry plateau: 240/240 nearby entry parameterisations positive on this
  dev window; best +$39.62. The submitted parameters sit in the plateau
  centre (drop 125, conf 20, breakout 12, trailing arm 50 / trail 50).
- The entry fires on both regimes (crash-recovery and slow grind), so the
  >=1-trade race-day guardrail is not at risk from a 0-trade day.

## Why this shape
- Round-trip cost on this window is ~43 bps (depth ~$642k), so a trade
  must catch a move larger than that. Fixed take-profits capped the big
  recovery; trailing-only exits rode it (+$33.33 on the largest round trip).
- Breakouts of 5-8 bps sit inside the 12 bps 1-min noise and lose;
  12 bps breakout + a 125 bps hole filter the noise out.
- The 20 bps bounce-off-the-low confirmation keeps the bot from catching
  a still-falling knife.

## Files
- `main.py` — the entry (stdlib only, kit shim in `vendor/`).
- `vendor/makefun_bars.py` — byte-identical copy of the kit's SDK shim.
- `NOTES.md`, `README.md` — this note and the entry summary.
