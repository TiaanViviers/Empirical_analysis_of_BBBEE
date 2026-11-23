from datetime import date
import pyarrow.dataset as ds
import pyarrow.parquet as pq

prices = ds.dataset("data/prices_observed.parquet", format="parquet")
one_instrument = prices.to_table(
    filter=(ds.field("instrument_id") == "SHP:XJSE:EQU")
    & (ds.field("date") >= date(2017, 1, 1))
    & (ds.field("date") <= date(2017, 12, 31)),
    columns=["date", "instrument_id", "close_raw", "volume",
             "has_valid_price", "potential_stale_price"],
)
instruments = pq.read_table("data/instruments.parquet")
market = pq.read_table("data/market_index.parquet")
print(one_instrument.num_rows, instruments.num_rows, market.num_rows)
