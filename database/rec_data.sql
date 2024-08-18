
CREATE SCHEMA IF NOT EXISTS recsys_schema;

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
DECLARE 
    community_acronym VARCHAR(20);
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

CREATE INDEX idx_interactions_community_acronym ON recsys_schema.interactions (community_acronym);

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

-- Function written in PL/pgSQL to populate the recommendations table
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
