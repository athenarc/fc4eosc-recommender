# FC4EOSC Recommender Systems

Includes the src under `darelabdb/` and the wheel file (`fc4eosc_recommenders-0.1.0-py3-none-any.whl`) for the portal recommenders.

## Installation

```bash
git clone git@github.com:athenarc/fc4eosc-recommender.git
cd fc4eosc-recommender
pip install fc4eosc_recommenders-0.1.0-py3-none-any.whl
```

Then you will have to create a `.env` file in the root of the project following the `.env.example` file.

## Database Configuration

The database after a new dump import must be configuredL

1. Add sk_ids as primary keys instead of the string ids in the database for optimization (`./sql/add_sk_ids.sql`)
2. Add extra indexes for string fields using trigrams (`./sql/build_extra_indexes.sql`)
3. Build the recommender schema (`./sql/build_recommenders_schema.sql`)

We have created a script that does all the above steps. You can run it by executing the following command:

```bash
cd sql;
chmod +x initialization.sh;
./initialization.sh <host> <port> <user> <password> <database>
```


## Recommenders

There are 3 different recommenders available:

**Content Based Recommender**

The content based recommender, given a research product (eg. publications) will recommend similar research products based on their textual and metadata attributes.

[More info](docs/similarity_based_recommender.md), [API Docs ](https://darelab.athenarc.gr/api/faircore/item-to-item-recommender/docs)

**Category Based Recommender**
@Antonis

**Author Based Recommender**
@Stavroula

