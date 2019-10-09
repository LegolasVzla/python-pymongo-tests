CREATE TABLE public.spot_collections(
    id serial PRIMARY KEY,
    spots_id integer NOT NULL,
    collections_id integer NOT NULL,
    custom_tags text COLLATE pg_catalog."default" DEFAULT ''::text,
    is_custom_collection boolean DEFAULT false,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    is_active boolean DEFAULT true,
    is_deleted boolean DEFAULT false,
    CONSTRAINT fk_spot_collections_spots FOREIGN KEY (spots_id)
        REFERENCES public.spots (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT fk_spots_collections_collections FOREIGN KEY (collections_id)
        REFERENCES public.collections (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT fk_spots_collections_spots FOREIGN KEY (spots_id)
        REFERENCES public.spots (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
);