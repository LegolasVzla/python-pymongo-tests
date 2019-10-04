CREATE TABLE public.site_images(
    id serial PRIMARY KEY,
    spots_id integer NOT NULL,
    uri character varying COLLATE pg_catalog."default",
    extension character varying COLLATE pg_catalog."default",
    original character varying COLLATE pg_catalog."default",
    principalimage boolean DEFAULT true,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    is_active boolean DEFAULT true,
    is_deleted boolean DEFAULT false,
    CONSTRAINT fk_site_images_spots FOREIGN KEY (spots_id)
        REFERENCES public.spots (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
);