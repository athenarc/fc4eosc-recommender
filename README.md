# FC4EOSC Recommender Systems

This project, developed by the DARElab team at the ATHENA Research Center, is part of the [FAIRCORE4EOSC European project](https://faircore4eosc.eu). Its aim is to support research discovery within the RDGraph by providing different recommendation services to users.

This repository contains the source code under `darelabdb/` and the wheel file (`fc4eosc_recommenders-0.1.0-py3-none-any.whl`) for the recommender systems integrated into the RDGraph portal.

## Installation

```bash
git clone git@github.com:athenarc/fc4eosc-recommender.git
cd fc4eosc-recommender
pip install fc4eosc_recommenders-0.1.0-py3-none-any.whl
```

After installation, create a `.env` file in the root directory by following the structure in `.env.example`.

## Database Configuration

After importing a new database dump, a few setup steps are required:

1. Add sk_ids as primary keys instead of the string ids in the database for better performance (`./sql/add_sk_ids.sql`)
2. Add trigram-based indexes to string fields (`./sql/build_extra_indexes.sql`)
3. Create the recommender schema (`./sql/build_recommenders_schema.sql`)

You can automate these steps using the provided initialization script:

```bash
cd sql;
chmod +x initialization.sh;
./initialization.sh <host> <port> <user> <password> <database>
```

## Recommenders

There are 3 different recommenders available:

**User-to-Item Recommender**
Recommends research products (e.g., publications) to users based on their ORCID and their citation behavior within research communities. 

[More info](docs/author_based_recommender.md), [API Docs](https://darelab.athenarc.gr/api/faircore/user-to-item-recommender/docs)

**Item-to-Item Recommender**
Recommends similar research products based on metadata and textual similarity.

[More info](docs/similarity_based_recommender.md), [API Docs](https://darelab.athenarc.gr/api/faircore/item-to-item-recommender/docs)

**Category-based Recommender**
Recommends research products based on category associations.

[More info](docs/category_based_recommender.md), [API Docs](https://darelab.athenarc.gr/api/faircore/category-based-recommender/docs)
