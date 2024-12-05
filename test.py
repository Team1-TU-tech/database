import pandas as pd
parquet_path = "/Users/seon-u/TU-tech/database/2024-12-05T08-01-08.478185.parquet"

df = pd.read_parquet(parquet_path)
print(df)