ALTER TABLE result
ADD COLUMN sk_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY;

ALTER TABLE author
ADD COLUMN sk_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY;

ALTER TABLE datasource
ADD COLUMN sk_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY;

ALTER TABLE community
ADD COLUMN sk_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY;

ALTER TABLE fos
ADD COLUMN sk_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY;

-- result_author
ALTER TABLE result_author
ADD sk_author_id int;

ALTER TABLE result_author
ADD sk_result_id int;

UPDATE
    result_author ra
SET
    sk_result_id = r.sk_id
FROM result r
WHERE
    ra.result_id = r.id;

UPDATE
    result_author ra
SET
    sk_author_id = a.sk_id
FROM author a
WHERE
    ra.author_id = a.id;


-- result_citations
ALTER TABLE result_citations
ADD sk_result_id_cited int;

ALTER TABLE result_citations
ADD sk_result_id_cites int;

UPDATE
    result_citations rc
SET
    sk_result_id_cited = r.sk_id
FROM result r
WHERE
    rc.result_id_cited = r.id;

UPDATE
    result_citations rc
SET
    sk_result_id_cites = r.sk_id
FROM result r
WHERE
    rc.result_id_cites = r.id;

-- result_community
ALTER TABLE result_community
ADD sk_community_id int;

ALTER TABLE result_community
ADD sk_result_id int;

UPDATE
    result_community rc
SET
    sk_result_id = r.sk_id
FROM result r
WHERE
    rc.result_id = r.id;

UPDATE
    result_community rc
SET
    sk_community_id = c.sk_id
FROM community c
WHERE
    rc.community_id = c.id;

-- result_hostedby
ALTER TABLE result_hostedby
ADD sk_datasource_id int;

ALTER TABLE result_hostedby
ADD sk_result_id int;

UPDATE
    result_hostedby rh
SET
    sk_result_id = r.sk_id
FROM result r
WHERE
    rh.result_id = r.id;

UPDATE
    result_hostedby rh
SET
    sk_datasource_id = d.sk_id
FROM datasource d
WHERE
    rh.datasource_id = d.id;

--result_pid
ALTER TABLE result_pid
ADD sk_result_id int;

UPDATE
    result_pid rp
SET
    sk_result_id = r.sk_id
FROM result r
WHERE
    rp.result_id = r.id;

-- result_fos
ALTER TABLE result_fos
ADD sk_result_id int;

UPDATE
    result_fos rf
SET
    sk_result_id = r.sk_id
FROM result r
WHERE
    rf.result_id = r.id;

ALTER TABLE result_fos
ADD sk_fos_id int;

UPDATE
    result_fos rf
SET
    sk_fos_id = f.sk_id
FROM fos f
WHERE
    rf.fos_id = f.id;

-- result_collectedfrom
ALTER TABLE result_collectedfrom
ADD sk_result_id int;

UPDATE
    result_collectedfrom rc
SET
    sk_result_id = r.sk_id
FROM result r
WHERE
    rc.result_id = r.id;

ALTER TABLE result_collectedfrom
ADD sk_datasource_id int;

UPDATE
    result_collectedfrom rc
SET
    sk_datasource_id = d.sk_id
FROM datasource d
WHERE
    rc.datasource_id = d.id;

-- define new foreign key relationships
alter table public.result_author
    add constraint result_author_author_sk_id_fk
        foreign key (sk_author_id) references public.author;

alter table public.result_author
    add constraint result_author_result_sk_id_fk
        foreign key (sk_result_id) references public.result;

alter table public.result_citations
    add constraint result_citations_result_sk_id_fk
        foreign key (sk_result_id_cites) references public.result;

alter table public.result_citations
    add constraint result_citations_result_sk_id_fk_2
        foreign key (sk_result_id_cited) references public.result;

alter table public.result_collectedfrom
    add constraint result_collectedfrom_result_sk_id_fk
        foreign key (sk_result_id) references public.result;

alter table public.result_collectedfrom
    add constraint result_collectedfrom_datasource_sk_id_fk
        foreign key (sk_datasource_id) references public.datasource;

alter table public.result_community
    add constraint result_community_result_sk_id_fk
        foreign key (sk_result_id) references public.result;

alter table public.result_community
    add constraint result_community_community_sk_id_fk
        foreign key (sk_community_id) references public.community;

alter table public.result_fos
    add constraint result_fos_result_sk_id_fk
        foreign key (sk_result_id) references public.result;

alter table public.result_fos
    add constraint result_fos_fos_sk_id_fk
        foreign key (sk_fos_id) references public.fos;

alter table public.result_hostedby
    add constraint result_hostedby_result_sk_id_fk
        foreign key (sk_result_id) references public.result;

alter table public.result_hostedby
    add constraint result_hostedby_datasource_sk_id_fk
        foreign key (sk_datasource_id) references public.datasource;

alter table public.result_pid
    add constraint result_pid_result_sk_id_fk
        foreign key (sk_result_id) references public.result;
