from fastapi import HTTPException
import numpy as np
from darelabdb.recs_mab.bandits import Ucb, pUcb
from darelabdb.recs_mab.storage import RedisStorage

from pydantic import BaseModel, Field
from typing import Literal


class MABRecommend(BaseModel):
    input: str
    top_k_categories: int = Field(
        default=3,
        description="The number of categories to recommend",
    )
    top_k_items: int = Field(
        default=5,
        description="The number of recommendations per category",
    )
    user: str | None = None
    update: bool = Field(
        default=True,
        title="Update MABs",
        description="Use False in case of testing/dev",
    )


def MAB_recommend(settings, recommend: MABRecommend):
    storage = RedisStorage(settings.redis, recommend.input)
    if storage.get("arms") is None:
        raise HTTPException(status_code=404, detail=recommend.input + " not found")

    ucb = pUcb(settings.pucb_alpha, settings.pucb_p, init=False, storage=storage)

    pool = np.arange(ucb.n_arms)
    categories = ucb.recommend(
        pool, recommend.top_k_categories, recommend.user, recommend.update
    )

    ids = []
    cats = {}

    for category in categories:
        storage = RedisStorage(settings.redis, recommend.input + "_" + category)
        ucb = Ucb(alpha=settings.ucb_alpha, init=False, storage=storage)
        pool = np.arange(ucb.n_arms)
        recs = ucb.recommend(pool, recommend.top_k_items, None, recommend.update)
        cats[category] = recs
        ids.extend(recs)

    ids_str = ",".join([f"'{id}'" for id in ids])
    return cats, ids_str


class MABUpdate(BaseModel):
    input: str
    category: str
    item: str | int
    reward: Literal[-1, 1] = 1
    user: str | None = None


def MAB_update(settings, update: MABUpdate):

    # Update the category
    storage2 = RedisStorage(settings.redis, update.input)
    if storage2.get("arms") is None:
        raise HTTPException(status_code=404, detail=update.input + " not found")

    id2 = storage2.find_array_index("arms", update.category)
    if id2 == -1:
        raise HTTPException(status_code=404, detail=update.category + " not found")

    ucb2 = pUcb(settings.pucb_alpha, settings.pucb_p, init=False, storage=storage2)
    try:
        ucb2.update([id2], [update.reward], update.user)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Update the item
    mab_key = update.input + "_" + update.category
    storage = RedisStorage(settings.redis, mab_key)

    id = storage.find_array_index("arms", update.item)
    if id == -1:
        raise HTTPException(
            status_code=404, detail="Item " + str(update.item) + " not found"
        )

    ucb = Ucb(alpha=settings.ucb_alpha, init=False, storage=storage)
    try:
        ucb.update([id], [update.reward], None)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    return ""
