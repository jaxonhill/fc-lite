import pandas as pd
import requests


def main() -> None:
    df = pd.read_csv("explorations_diversity_options.csv")

    # Print
    df = df.drop("class_description", axis=1)
    print(df.to_string())

    # Print
    df = pd.read_csv("cs_elective_options.csv")
    print(df.to_string())

    # Print
    df = pd.read_csv("cs_core_options.csv")
    print(df.to_string())


if __name__ == "__main__":
    main()
