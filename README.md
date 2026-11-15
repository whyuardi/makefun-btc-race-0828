# Crash-Rebound Rider

A long-only cbBTC trading bot for the make.fun BTC 24h race
(btc-race-24h-20261115-0828).

**Idea in one line:** buy only after a deep 120-minute drop, once the price
has bounced off its 120-minute low and broken above its 15-bar high; then
ride the recovery with a trailing stop and no fixed take-profit.

Dev-window net PnL **+$24.68** on this competition's frozen window
(4 round trips, max drawdown 2.65%), and **+$2.09** on the previous race's
dev window (out-of-sample). See `NOTES.md` for the full evidence.

`main.py` is the entrypoint (Python 3, stdlib only); the kit's SDK shim is
in `vendor/makefun_bars.py`.
