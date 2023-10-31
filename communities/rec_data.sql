
CREATE SCHEMA IF NOT EXISTS "author-recs";

-- Create the ENUM type
CREATE TYPE "author-recs".interaction_enum AS ENUM ('authorship', 'cited');

-- Create the interactions table in the author-recs schema
CREATE TABLE "author-recs".interactions (
    id SERIAL PRIMARY KEY,                  -- Auto-incremented unique identifier
    author_id VARCHAR(20) NOT NULL,         -- ORCID identifier of the author
    result_id VARCHAR(200) NOT NULL,        -- Identifier of the cited/result item
    community_name VARCHAR(100) NOT NULL,   -- Name of the community
    interaction_type "author-recs".interaction_enum NOT NULL,  -- Use the ENUM type here
    FOREIGN KEY (result_id) REFERENCES public.result(id)
);

-- Populate the interactions table for each distinct community
DO $$ 
DECLARE 
    community_name VARCHAR(100);
BEGIN
    FOR community_name IN (SELECT DISTINCT name FROM public.community)
    LOOP
        -- Insert authorship interactions
        WITH author_written AS (
            SELECT a.orcid, r.id, c.name as community_name, 'authorship'::"author-recs".interaction_enum as interaction_type
            FROM public.author a
            JOIN public.result_author ra ON a.id = ra.author_id
            JOIN public.result r ON ra.result_id = r.id
            JOIN public.result_community rc ON r.id = rc.result_id
            JOIN public.community c ON rc.community_id = c.id
            WHERE a.orcid IS NOT NULL AND a.orcid != '' AND c.name = community_name
        )
        INSERT INTO "author-recs".interactions (author_id, result_id, community_name, interaction_type)
        SELECT aw.orcid, aw.id, aw.community_name, aw.interaction_type
        FROM author_written aw;

        -- Insert cited interactions
        WITH author_cited AS (
            SELECT a.orcid, rcit.result_id_cited, c.name as community_name, 'cited'::"author-recs".interaction_enum as interaction_type
            FROM public.author a
            JOIN public.result_author ra ON a.id = ra.author_id
            JOIN public.result_citations rcit ON ra.result_id = rcit.result_id_cites
            JOIN public.result r ON rcit.result_id_cited = r.id
            JOIN public.result_community rc ON r.id = rc.result_id
            JOIN public.community c ON rc.community_id = c.id
            WHERE a.orcid IS NOT NULL AND a.orcid != '' AND c.name = community_name
        )
        INSERT INTO "author-recs".interactions (author_id, result_id, community_name, interaction_type)
        SELECT ac.orcid, ac.result_id_cited, ac.community_name, ac.interaction_type
        FROM author_cited ac;
    END LOOP;
END $$;

CREATE INDEX idx_interactions_community_name ON "author-recs".interactions (community_name);

-- -- Create a materialized view
-- CREATE MATERIALIZED VIEW interactions_mview AS
-- SELECT 
--     author_id, 
--     result_id,
--     community_name,
--     interaction_type, 
--     COUNT(*) as interaction_count
-- FROM interactions
-- GROUP BY author_id, result_id, community_name, interaction_type;

-- CREATE INDEX idx_interactions_mview_community ON interactions_mview (community_name);

-- -- Create user to community mapping table
-- CREATE TABLE users_mappings (
--     inner_id INTEGER PRIMARY KEY,               -- Internal ID for the recommender system
--     author_id VARCHAR(20) NOT NULL,             -- ORCID identifier of the author
--     community_name VARCHAR(100) NOT NULL,       -- Name of the community
--     UNIQUE(author_id, community_name),          -- Unique constraint for author within a community
--     FOREIGN KEY (author_id) REFERENCES author(orcid),
--     FOREIGN KEY (community_name) REFERENCES community(name)
-- );

-- -- Create item to community mapping table with optional DOI
-- CREATE TABLE items_mappings (
--     inner_id INTEGER PRIMARY KEY,               -- Internal ID for the recommender system
--     result_id VARCHAR(200) NOT NULL,            -- Result identifier
--     doi VARCHAR(200),                           -- DOI (if available)
--     community_name VARCHAR(100) NOT NULL,       -- Name of the community
--     UNIQUE(result_id, community_name),          -- Unique constraint for item within a community
--     FOREIGN KEY (result_id) REFERENCES result(id),
--     FOREIGN KEY (community_name) REFERENCES community(name)
-- );

-- CREATE INDEX idx_users_mappings_author_community ON users_mappings (author_id, community_name);
-- CREATE INDEX idx_innerid_community ON items_mappings (inner_id, community_name);