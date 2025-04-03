-- Create schema for recommenders
create schema if not exists recsys_schema;


-- Author based recommender initialization

-- Create the ENUM type
CREATE TYPE recsys_schema.interaction_enum AS ENUM ('authorship', 'cited');

-- Create the interactions table in the author-recs schema
CREATE TABLE recsys_schema.interactions (
    id SERIAL PRIMARY KEY,                     -- Auto-incremented unique identifier
    author_id VARCHAR(20) NOT NULL,            -- ORCID identifier of the author
    result_id VARCHAR(200) NOT NULL,           -- Identifier of the cited/result item
    community_acronym VARCHAR(20) NOT NULL,   -- Acronym of the community
    interaction_type recsys_schema.interaction_enum NOT NULL,  -- Use the ENUM type here
    FOREIGN KEY (result_id) REFERENCES public.result(id)
);

-- Populate the interactions table for each distinct community
DO $$ 
BEGIN
    FOR community_acronym IN (SELECT DISTINCT acronym FROM public.community)
    LOOP
        -- Insert authorship interactions
        WITH author_written AS (
            SELECT a.orcid, r.id, c.acronym as community_acronym, 'authorship'::recsys_schema.interaction_enum as interaction_type
            FROM public.author a
            JOIN public.result_author ra ON a.id = ra.author_id
            JOIN public.result r ON ra.result_id = r.id
            JOIN public.result_community rc ON r.id = rc.result_id
            JOIN public.community c ON rc.community_id = c.id
            WHERE a.orcid IS NOT NULL AND a.orcid != '' AND c.acronym = community_acronym
        )
        INSERT INTO recsys_schema.interactions (author_id, result_id, community_acronym, interaction_type)
        SELECT aw.orcid, aw.id, aw.community_acronym, aw.interaction_type
        FROM author_written aw;

        -- Insert cited interactions
        WITH author_cited AS (
            SELECT a.orcid, rcit.result_id_cited, c.acronym as community_acronym, 'cited'::recsys_schema.interaction_enum as interaction_type
            FROM public.author a
            JOIN public.result_author ra ON a.id = ra.author_id
            JOIN public.result_citations rcit ON ra.result_id = rcit.result_id_cites
            JOIN public.result r ON rcit.result_id_cited = r.id
            JOIN public.result_community rc ON r.id = rc.result_id
            JOIN public.community c ON rc.community_id = c.id
            WHERE a.orcid IS NOT NULL AND a.orcid != '' AND c.acronym = community_acronym
        )
        INSERT INTO recsys_schema.interactions (author_id, result_id, community_acronym, interaction_type)
        SELECT ac.orcid, ac.result_id_cited, ac.community_acronym, ac.interaction_type
        FROM author_cited ac;
    END LOOP;
END $$;

CREATE INDEX idx_interactions_author_id ON recsys_schema.interactions(author_id);
CREATE INDEX idx_interactions_community_acronym ON recsys_schema.interactions (community_acronym);
CREATE INDEX idx_interactions_interaction_type ON recsys_schema.interactions(interaction_type);

-- Clean up unuseful interactions
DO $$
BEGIN
    FOR t IN (SELECT DISTINCT interaction_type FROM recsys_schema.interactions)
    LOOP
        -- Step 1: Count the number of results per author in each community
        WITH author_result_counts AS (
            SELECT i.author_id, i.community_acronym, COUNT(DISTINCT i.result_id) AS total_results
            FROM recsys_schema.interactions i
            WHERE i.interaction_type = t
            GROUP BY i.author_id, i.community_acronym
        ),

        -- Step 2: Join with interactions to get the result_ids for those authors
        author_result_details AS (
            SELECT atr.author_id, atr.community_acronym, atr.total_results, i.result_id
            FROM author_result_counts atr
            JOIN recsys_schema.interactions i
            ON atr.author_id = i.author_id
            WHERE atr.community_acronym = i.community_acronym
            AND i.interaction_type = t
        ),

        -- Step 3: Count the number of results that are single authored/cited in each community (solo results)
        solo_author_result_counts AS (
            SELECT i.result_id, i.community_acronym, COUNT(DISTINCT i.result_id) AS solo_results
            FROM recsys_schema.interactions i
            WHERE i.interaction_type = t
            GROUP BY i.result_id, i.community_acronym
            HAVING COUNT(DISTINCT i.author_id) = 1
        )

        -- Step 4: Delete interactions for authors who only authored solo results
        DELETE FROM recsys_schema.interactions
        WHERE (author_id, community_acronym) IN (
            -- Find authors where the number of total results matches the number of solo-authored results
            SELECT ard.author_id, ard.community_acronym
            FROM author_result_details ard
            JOIN solo_author_result_counts sarc
            ON ard.result_id = sarc.result_id
            AND ard.community_acronym = sarc.community_acronym
            WHERE ard.total_results = sarc.solo_results
        )
        AND interaction_type = t;
    END LOOP;
END $$;

-- Create a materialized view
CREATE MATERIALIZED VIEW recsys_schema.interactions_mview AS
SELECT 
    author_id, 
    result_id,
    community_acronym,
    interaction_type, 
    COUNT(*) as interaction_count
FROM recsys_schema.interactions
GROUP BY author_id, result_id, community_acronym, interaction_type;

CREATE INDEX idx_interactions_mview_community ON recsys_schema.interactions_mview (community_acronym);

CREATE TABLE recsys_schema.recommendations (
    author_id VARCHAR(20) NOT NULL,                        -- ORCID identifier of the author
    result_id VARCHAR(200) NOT NULL,                       -- Result identifier
    result_title TEXT,                                     -- Title of the result
    result_type VARCHAR(50),                               -- Type of the result
    result_publication_date DATE,                          -- Publication date of the result
    result_publisher TEXT,                                 -- Publisher of the result
    rank INTEGER NOT NULL,                                 -- Rank of the recommendation
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,         -- Timestamp when the recommendation was generated
    community_acronym VARCHAR(20) NOT NULL,                -- Acronym of the community
    PRIMARY KEY (author_id, result_id, community_acronym), -- Ensuring unique recommendations per author per community
    FOREIGN KEY (result_id) REFERENCES public.result(id)
);

CREATE INDEX idx_author_community ON recsys_schema.recommendations (author_id, community_acronym);
CREATE INDEX idx_author_community_rank ON recsys_schema.recommendations (author_id, community_acronym, rank);

-- Function written in PL/pgSQL to populate the recommendations table with metadata
CREATE OR REPLACE FUNCTION recsys_schema.populate_recommendations()
RETURNS TRIGGER AS $$
BEGIN
    SELECT r.title, r.type, r.publication_date, r.publisher INTO NEW.result_title, NEW.result_type, NEW.result_publication_date, NEW.result_publisher
    FROM public.result r
    WHERE r.id = NEW.result_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create a trigger to populate the recommendations table
CREATE TRIGGER populate_recommendation_details_trigger
BEFORE INSERT ON recsys_schema.recommendations
FOR EACH ROW
EXECUTE FUNCTION recsys_schema.populate_recommendations();

-- Create table to return top 20 cited results per community
CREATE TABLE recsys_schema.top20_cited_results (
    community_acronym VARCHAR(20) NOT NULL,
    result_id VARCHAR(200) NOT NULL,
    author_id VARCHAR(20),
    result_title TEXT,
    result_type VARCHAR(50),
    result_publication_date DATE,
    result_publisher TEXT,
    rank INTEGER NOT NULL,
    PRIMARY KEY (community_acronym, result_id, rank)
);

-- Function written in PL/pgSQL to populate the top20_cited_results table with metadata
CREATE OR REPLACE FUNCTION recsys_schema.populate_top20_cited_details()
RETURNS TRIGGER AS $$
BEGIN
    -- Fetch metadata for the result being inserted
    SELECT r.title, r.type, r.publication_date, r.publisher
    INTO NEW.result_title, NEW.result_type, NEW.result_publication_date, NEW.result_publisher
    FROM public.result r
    WHERE r.id = NEW.result_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create a trigger to populate the top20_cited_results table
CREATE TRIGGER populate_top20_cited_details_trigger
BEFORE INSERT ON recsys_schema.top20_cited_results
FOR EACH ROW
EXECUTE FUNCTION recsys_schema.populate_top20_cited_details();

-- Function to populate the top 20 cited results per community
DO $$
DECLARE
    community RECORD;
BEGIN
    -- Loop through each distinct community
    FOR community IN (SELECT DISTINCT community_acronym FROM recsys_schema.interactions_mview)
    LOOP
        -- Insert top 20 cited results for the current community
        INSERT INTO recsys_schema.top20_cited_results (
            community_acronym,
            result_id,
            author_id,
            rank
        )
        SELECT
            community.community_acronym,
            mv.result_id,
            mv.author_id,
            ROW_NUMBER() OVER (ORDER BY mv.interaction_count DESC) AS rank
        FROM
            recsys_schema.interactions_mview mv
        WHERE
            mv.community_acronym = community.community_acronym
            AND mv.interaction_type = 'cited'
        ORDER BY
            mv.interaction_count DESC
        LIMIT 20;
    END LOOP;
END $$;


-- Category based recommender initialization

-- 1) create a table with the top 100 publication ids per level 2 tag
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
from top_publications as top;


-- 2) create a table with the full information about top publications
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
 rfos.fos_id < 10;
