import subprocess
import yaml
import pandas as pd
import sys
import os
from retrying import retry


def main(start_date="2020-01-01 00:00", end_date="2020-01-01 01:00"):
    """
    Start date and end date should look like: "2020-01-01 00:00"
    """
    if not os.path.isdir("data"):
        Exception("data directory not found")

    # create needed directories
    for path in ["data/raw", "data/intermediate", "data/compressed", "logs"]:
        if not os.path.isdir(path):
            os.mkdir(path)

    with open("pipeline_inputs.yaml") as f:
        pipeline_inputs = yaml.safe_load(f)

    # split into days
    # each day try each hour

    hourly_dates = pd.date_range(start_date, end_date, freq="60min")

    @retry
    def hour_download(i):
        print(f"Starting {hourly_dates[i]}")
        pipeline_inputs["solids"]["download_eumetsat_files"]["inputs"][
            "start_date"
        ] = hourly_dates[i].strftime("%Y-%m-%d %H:%M")
        pipeline_inputs["solids"]["download_eumetsat_files"]["inputs"][
            "end_date"
        ] = hourly_dates[i + 1].strftime("%Y-%m-%d %H:%M")
        subprocess.run(
            "dagster pipeline execute -m satip.mario -c pipeline_inputs.yaml",
            shell=True,
            check=True,
        )

    for i in range(len(hourly_dates) - 1):
        hour_download(i)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
