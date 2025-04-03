# Introduction

Generate category based recommendations using Multi-Armed bandits.

This base wraps the functionality of the mabrecs component, adding features to support category-based recommendations.

View the respective API documentation for the supported operations.

Deployment is simple and hassle-free:

- create the arms if you don't already have the JSON files
- run `docker-compose up`

# Arm Generation Process

## Create the table with the top 100 publications per level 2 tag

```sql
create table recsys_schema.top100_per_level_2_fos_ids as
WITH
citations_count AS (
    SELECT
        rf.fos_id as level_2_id,
        fos.label as level_2_label,
        rf.sk_result_id AS sk_result_id,
        COUNT(rf.sk_result_id) AS citations
    FROM public.result_fos rf
    JOIN public.fos on rf.fos_id = fos.id
    JOIN public.result_citations rc ON rf.sk_result_id = rc.sk_result_id_cited
    JOIN public.result_community rcom ON rcom.sk_result_id = rf.sk_result_id
    WHERE
        rf.fos_id / 100 >= 1 AND rf.fos_id / 100 < 10 -- level 2 fos
    GROUP BY
        rf.fos_id, fos.label, rf.sk_result_id
),
ranked_citations AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY level_2_id ORDER BY citations DESC) AS rank
    FROM citations_count
),
top_publications AS (
SELECT
    *
FROM
    ranked_citations
WHERE
    rank <= 100
ORDER BY
    level_2_id, rank)
SELECT
       top.sk_result_id,
       top.level_2_id,
       top.level_2_label,
       top.citations
from top_publications as top
```

Then, we create a table with the full information about our top publications:

```sql
create table recsys_schema.top100_per_level_2_fos as
WITH
authors as (
    select top.sk_result_id, string_agg(fullname, ',') as authors
    from recsys_schema.top100_per_level_2_fos_ids top
    join public.result_author ra on ra.sk_result_id = top.sk_result_id
    join public.author a on ra.sk_author_id = a.sk_id
    group by top.sk_result_id
)
SELECT
       r.*,
       a.authors,
       c.id as community_id,
       c.acronym as community_acronym,
       fos.id as level_1_id,
       fos.label as level_1_label,
       top.level_2_id,
       top.level_2_label,
       top.citations
from recsys_schema.top100_per_level_2_fos_ids as top
join public.result_community rc on rc.sk_result_id = top.sk_result_id
join public.community c on rc.community_id = c.id
join authors a on a.sk_result_id = top.sk_result_id
join public.result_fos rfos on rfos.sk_result_id = top.sk_result_id
join public.fos on fos.id = rfos.fos_id
join public.result r on top.sk_result_id = r.sk_id
where
 rfos.fos_id < 10
```

The table top100_per_level_2_fos contains the top 100 publications per level 2 tag. However, the same publication may have multiple level 2 and belong to multiple communities. As a result there might be 'week' combinations of communities and level 2 tags. For example, the level 2 tag 'art', resulted in 1 publication in the community 'enermaps'. In order to retrieve only relevant combinations we filter out combinations of communities and level 2 tags that have less than 30 publications. This will also be the minimum number of publications in the pool of any MAB algorithm.

````python
from darelabdb.recs_mab.storage import JsonFile, RedisStorage
from darelabdb.recs_mab.bandits import Ucb, pUcb
import numpy as np
from darelabdb.utils_database_connector.core import Database
from darelabdb.utils_configs.apis.faircore_mabrecs import settings

db = Database("fc4eosc")

query = """
with
t as (
    select distinct community_acronym, level_2_label, id, citations
    from recsys_schema.top100_per_level_2_fos),
t2 as (
    select community_acronym,
   level_2_label,
   count(1) as count_pubs,
   round(avg(citations)) as avg_citations,
   PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY citations) as median_citations,
   string_agg(id,',') as publications
    from t
    group by community_acronym, level_2_label
)
select * from t2
where count_pubs >30
"""

res = db.execute(query, limit = 9999999)

## Create arms for Categories

```python
for community in res['community_acronym'].unique():
    storage = JsonFile(settings.production_dir + community + ".json")
    arms = res[res['community_acronym']==community]['level_2_label'].unique()
    print('MAB:', community, "\nArms: ", arms)
    ucb = pUcb(0.3,0.5, init=True, n_arms= arms.shape[0], bias=np.zeros(arms.shape[0]), storage=storage, arms=list(arms))
````

## Create arms for publications

```python
for index, row in res.iterrows():
    arms = row['publications'].split(',')
    n_arms = len(arms)
    mab_key = row['community_acronym'] + "_" + row['level_2_label']
    print('MAB:', mab_key, "\nArms: ", len(arms), "DOIs")
    storage = JsonFile(settings.production_dir + mab_key + ".json")
    ucb = Ucb(0.5, init=True, n_arms= n_arms, bias=np.zeros(n_arms), storage=storage, arms=arms)
```

This process will create one JSON file per MAB key.
The JSON files are added to the specified directory in the configuration file darelabdb.utils_configs.apis.faircore_mabrecs and are automatically copied inside the docker image.

```python
from darelabdb.utils_configs.apis.faircore_mabrecs import settings
settings.production_dir
```

Once the docker container starts, the arms are automatically loaded into a redis database at startup time. The redis keys/contents will be exactly the same as the JSON filenames/contents. The used redis image is the 'redis-stack' which includes the required JSON module.
