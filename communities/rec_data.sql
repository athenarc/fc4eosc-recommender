
-- Create the interactions table
CREATE TABLE interactions (
    orcid VARCHAR(255) NOT NULL,         -- ORCID identifier of the author
    result_id INTEGER NOT NULL,          -- Identifier of the cited/result item
    community_id INTEGER NOT NULL,       -- ID of the community
    interaction_type ENUM('authorship', 'cited') NOT NULL, -- Type of interaction
    PRIMARY KEY (orcid, result_id, community_id),
    FOREIGN KEY (orcid) REFERENCES authors(orcid),
    FOREIGN KEY (result_id) REFERENCES results(id),
    FOREIGN KEY (community_id) REFERENCES communities(id)
);

-- Populate the interactions table for each distinct community
DO $$ 
DECLARE 
    community integer;
BEGIN
    FOR community IN (SELECT DISTINCT id FROM communities)
    LOOP
        INSERT INTO interactions (orcid, result_id, community_id, interaction_type)
        WITH author_written AS (
            SELECT a.orcid, r.id, c.id as community_id, 'authorship' as interaction_type
            FROM authors a
            JOIN result_author ra ON a.id = ra.author_id
            JOIN result r ON ra.result_id = r.id
            JOIN result_community rc ON r.id = rc.result_id
            JOIN community c ON rc.community_id = c.id
            WHERE a.orcid IS NOT NULL AND a.orcid != '' AND c.id = community
        ),
        author_cited AS (
            SELECT a.orcid, rcit.result_id_cited, c.id as community_id, 'cited' as interaction_type
            FROM authors a
            JOIN result_author ra ON a.id = ra.author_id
            JOIN result_citations rcit ON ra.result_id = rcit.result_id_cites
            JOIN result r ON rcit.result_id_cited = r.id
            JOIN result_community rc ON r.id = rc.result_id
            JOIN community c ON rc.community_id = c.id
            WHERE a.orcid IS NOT NULL AND a.orcid != '' AND c.id = community
        )
        SELECT orcid, result_id, community_id, interaction_type FROM author_written
        UNION ALL
        SELECT orcid, result_id, community_id, interaction_type FROM author_cited;
    END LOOP;
END $$;

-- Create an index on community id for faster queries
CREATE INDEX idx_interactions_community_id ON interactions(community_id);

-- Create materialized views for counts
CREATE MATERIALIZED VIEW author_interactions_count AS
SELECT orcid, COUNT(*) AS interaction_count
FROM interactions
GROUP BY orcid;

CREATE MATERIALIZED VIEW result_interactions_count AS
SELECT result_id, COUNT(*) AS interaction_count
FROM interactions
GROUP BY result_id;

-- Create mapping tables
CREATE TABLE users_mappings (
    inner_id SERIAL PRIMARY KEY,  -- ID used internally by the recommender system
    raw_id VARCHAR(255),          -- ORCID
    community_id INTEGER,         -- Community ID
    UNIQUE(raw_id, community_id),
    FOREIGN KEY (raw_id) REFERENCES authors(orcid),
    FOREIGN KEY (community_id) REFERENCES communities(id)
);

CREATE TABLE items_mappings (
    inner_id SERIAL PRIMARY KEY,  -- ID used internally by the recommender system
    raw_id INTEGER,               -- Result id
    community_id INTEGER,         -- Community ID
    UNIQUE(raw_id, community_id),
    FOREIGN KEY (raw_id) REFERENCES results(id),
    FOREIGN KEY (community_id) REFERENCES communities(id)
);

-- Create an index on community id and raw id for faster queries
CREATE INDEX idx_users_mappings_community_raw ON users_mappings (community_id, raw_id);
CREATE INDEX idx_items_mappings_community_raw ON items_mappings (community_id, raw_id);