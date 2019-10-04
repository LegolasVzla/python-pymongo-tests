CREATE TABLE public.users(
    id serial PRIMARY KEY,
    email character varying COLLATE pg_catalog."default" NOT NULL DEFAULT ''::character varying,
    first_name character varying COLLATE pg_catalog."default" NOT NULL,
    last_name character varying COLLATE pg_catalog."default" NOT NULL,
    status_account integer DEFAULT 2,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    is_active boolean DEFAULT true,
    is_deleted boolean DEFAULT false,
    full_name character varying COLLATE pg_catalog."default"
);