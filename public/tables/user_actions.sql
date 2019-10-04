CREATE TABLE public.user_actions(
    id serial PRIMARY KEY,
    spots_id integer NOT NULL,
    type_user_actions_id integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    is_active boolean DEFAULT true,
    is_deleted boolean DEFAULT false,
    CONSTRAINT fk_user_actions_spots FOREIGN KEY (spots_id)
        REFERENCES public.spots (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
);