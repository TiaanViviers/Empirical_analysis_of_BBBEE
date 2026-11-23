library(arrow)
library(dplyr)

prices <- open_dataset("data/prices_observed.parquet", format = "parquet")
one_instrument <- prices |>
  filter(instrument_id == "SHP:XJSE:EQU",
         date >= as.Date("2017-01-01"),
         date <= as.Date("2017-12-31")) |>
  select(date, instrument_id, close_raw, volume,
         has_valid_price, potential_stale_price) |>
  collect()
instruments <- read_parquet("data/instruments.parquet")
market <- read_parquet("data/market_index.parquet")
with_metadata <- left_join(one_instrument, instruments,
                           by = "instrument_id", relationship = "many-to-one")
