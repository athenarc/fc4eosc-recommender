import json
import os

from redis import Redis


class Readis:
    def __init__(self, redis_url: str):
        self.r = Redis.from_url(redis_url)

    async def initialize(self, dir: str, force: str = ""):

        for f in os.listdir(dir):
            if f.endswith(".json"):
                ff = f.replace(".json", "")
                if self.r.exists(ff) == 0 or force == "42":
                    print("init", dir, ff)
                    with open(f"{dir}{f}", "r", encoding="utf8") as f2:
                        js = json.load(f2)
                    self.r.json().set(ff, "$", js)
