import argparse
from typing import Dict

import yaml


def read_configs() -> Dict:
    parser = argparse.ArgumentParser(description="DataDazzle API.")
    parser.add_argument(
        "--config_file", default="", help="path to config file", type=str
    )
    args = parser.parse_args()

    conf = None
    with open(args.config_file) as stream:
        try:
            conf = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    return conf


app_config = read_configs()
