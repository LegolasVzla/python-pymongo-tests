CREATE TABLE public.spot_tags(
    id serial PRIMARY KEY,
    user_actions_id integer NOT NULL,
    users_id integer NOT NULL,
    tags_id integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    is_active boolean DEFAULT true,
    is_deleted boolean DEFAULT false,
    CONSTRAINT fk_spot_tags_tags FOREIGN KEY (tags_id)
        REFERENCES public.tags (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT fk_spots_tags_user_actions FOREIGN KEY (user_actions_id)
        REFERENCES public.user_actions (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
);