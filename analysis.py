import pandas as pd
import requests


def main() -> None:
    df = pd.read_csv("explorations_diversity_options.csv")
    print(df.to_string())


if __name__ == "__main__":
    main()
