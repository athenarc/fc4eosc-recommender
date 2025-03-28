-- Create extra indexes we need for fc4eosc use case
create unique index concurrently result_candidate_id on result (id);
create unique index concurrently author_candidate_id on author (id);
create index concurrently sk_result_id_cited_index on result_citations (sk_result_id_cited);
create index concurrently sk_result_id_cites_index on result_citations (sk_result_id_cites);

-- Create indexes for specific string values to support quick LIKE & ILIKE queries
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX CONCURRENTLY title_trgm_idx
    ON result
    USING GIST (title gist_trgm_ops(siglen=12));

CREATE INDEX CONCURRENTLY description_trgm_idx
    ON result
    USING GIN (description gin_trgm_ops);

CREATE INDEX CONCURRENTLY keywords_trgm_idx
    ON result
    USING GIN (keywords gin_trgm_ops);
