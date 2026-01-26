from mm_sandbox.strategy import make_quote


def test_bid_less_than_ask():
    q = make_quote(
        mid=100.0,
        vol_est=0.1,
        inventory=0.0,
        base_half_spread_bps=5.0,
        vol_widening_bps=30.0,
        inventory_skew_bps=8.0,
    )
    assert q.bid < q.ask
