CREATE TABLE public.collections(
    id serial PRIMARY KEY,
    name character varying COLLATE pg_catalog."default" NOT NULL DEFAULT ''::character varying,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    is_active boolean DEFAULT true,
    is_deleted boolean DEFAULT false
);