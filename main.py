"""Crash-Rebound Rider: a long-only cbBTC bot for the make.fun BTC race.

Idea in one line: buy only after a deep 120-minute drop, once the price has
bounced off its 120-minute low and broken above its 15-bar high; then ride
the recovery with a trailing stop and no fixed take-profit.

Entry (on a bar's close, all integer bps math):
  - close at least 125 bps below the highest close of the previous 120 bars
    (the market fell hard and is still in the hole),
  - close at least 20 bps above the lowest close of the previous 120 bars
    (it has bounced off the low),
  - close more than 12 bps above the highest close of the previous 15 bars
    (the bounce is breaking out, not just noise).

Exits (measured from the entry decision close):
  - no fixed take-profit: a trailing stop arms once the close is 50 bps
    above the entry close, then trails 50 bps below the highest close
    since entry, so a real recovery is ridden instead of capped;
  - stop loss 100 bps below the entry close;
  - maximum hold 120 bars;
  - 15-bar cooldown after any exit.

Sizing: full cash on entry, full position on exit, one position at a time.
max_slippage_bps is 100 on every order.

Dev-window evidence (exact replay of the kit engine, validated to the unit
against grade-local on buy-and-hold): this competition's dev window
+$24.68 net PnL (4 round trips, max drawdown 2.65%); the previous race's
dev window +$2.09 (1 round trip) with the same parameters, so the bot
trades on both a crash-recovery day and a slow-grind day. Split-half on
this dev window: +$2.26 / +$22.43. At doubled fees it still makes +$21.49.

Deterministic: no randomness, no wall clock, no environment reads; the only
state is the close history and the open position, both derived from the
batches the harness sends.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
BPS = 10_000
MAX_SLIP = 100

# Entry parameters (bps / bars).
DROP_H = 125   # must be at least this far below the 120-bar high
CONF = 20      # must be at least this far above the 120-bar low
WIN = 15       # breakout window (bars)
BRK = 12       # must break the window high by this much (bps)
# Exit parameters.
STOP = 100     # stop loss, bps below the entry decision close
ARM = 50       # trailing stop arms this far above the entry close (bps)
TRAIL = 50     # trailing distance below the peak close since entry (bps)
HOLD = 120     # maximum hold, bars
COOLDOWN = 15  # bars to wait after an exit before a new entry


class Rider:
    def __init__(self):
        self.closes = []
        self.holding = False
        self.pending = None  # (seq, decision close) of a buy not yet filled
        self.entry_seq = -1
        self.entry_close = 0
        self.peak_close = 0
        self.trailing = False
        self.cooldown_until = -1

    def on_batch(self, state, batch):
        close = state.close(SYMBOL)
        if close is None:
            return []
        self.closes.append(close)
        seq = state.seq
        if state.warming_up:
            return []
        # A buy rejected at this bar's open leaves no position: drop its
        # pending decision so a later fill can never initialise an entry
        # from a decision whose order never executed.
        if self.pending is not None:
            for fill in batch.get("fills", []):
                if (fill.get("status") == "rejected"
                        and fill.get("client_id") == "b%d" % self.pending[0]):
                    self.pending = None
                    break
        # A buy filled since the last batch: initialise the entry from the
        # decision this buy was sent on. A rejected buy leaves us flat.
        if not self.holding and SYMBOL in state.positions:
            self.holding = True
            if self.pending is not None:
                dseq, dclose = self.pending
                self.entry_seq = dseq
                self.entry_close = dclose
                self.peak_close = dclose
                self.trailing = False
                self.pending = None
        if SYMBOL not in state.positions:
            self.holding = False
        if self.holding:
            if close > self.peak_close:
                self.peak_close = close
            if close * BPS >= self.entry_close * (BPS + ARM):
                self.trailing = True
            exit_now = False
            if close * BPS <= self.entry_close * (BPS - STOP):
                exit_now = True
            elif self.trailing and close * BPS <= self.peak_close * (BPS - TRAIL):
                exit_now = True
            elif seq - self.entry_seq >= HOLD:
                exit_now = True
            if exit_now:
                self.cooldown_until = seq + COOLDOWN
                qty = state.positions[SYMBOL].qty
                return [{"side": "sell", "symbol": SYMBOL, "qty": qty,
                         "max_slippage_bps": MAX_SLIP,
                         "client_id": "s%d" % seq}]
            return []
        # Flat: look for an entry.
        if seq < 120 or seq < self.cooldown_until:
            return []
        closes = self.closes
        high120 = max(closes[-121:-1])
        low120 = min(closes[-121:-1])
        high_win = max(closes[-WIN - 1:-1])
        if close * BPS > high120 * (BPS - DROP_H):
            return []
        if close * BPS < low120 * (BPS + CONF):
            return []
        if close * BPS <= high_win * (BPS + BRK):
            return []
        self.pending = (seq, close)
        return [{"side": "buy", "symbol": SYMBOL,
                 "notional_quote_units": state.cash,
                 "max_slippage_bps": MAX_SLIP,
                 "client_id": "b%d" % seq}]


makefun_bars.run(Rider().on_batch)
