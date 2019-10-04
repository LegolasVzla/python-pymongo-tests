CREATE TABLE public.spots(
    id serial PRIMARY KEY,
    users_id integer NOT NULL,
    status_id integer DEFAULT 5,
    is_privated boolean DEFAULT false,
    name character varying COLLATE pg_catalog."default" NOT NULL DEFAULT ''::character varying,
    place_name character varying COLLATE pg_catalog."default" DEFAULT ''::character varying,
    remarks character varying COLLATE pg_catalog."default" DEFAULT ''::character varying,
    review character varying COLLATE pg_catalog."default" DEFAULT ''::character varying,
    full_address character varying COLLATE pg_catalog."default" DEFAULT ''::character varying,
    country_name character varying COLLATE pg_catalog."default" DEFAULT ''::character varying,
    state_name character varying COLLATE pg_catalog."default" DEFAULT ''::character varying,
    city_name character varying COLLATE pg_catalog."default" DEFAULT ''::character varying,
    street character varying COLLATE pg_catalog."default" DEFAULT ''::character varying,
    lat double precision NOT NULL,
    "long" double precision NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    is_active boolean DEFAULT true,
    is_deleted boolean DEFAULT false,
    CONSTRAINT fk_spots_users FOREIGN KEY (users_id)
        REFERENCES public.users (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
);