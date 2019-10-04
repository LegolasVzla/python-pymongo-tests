CREATE TABLE public.friendships(
    id serial PRIMARY KEY,
    friendable_type character varying COLLATE pg_catalog."default",
    friendable_id integer,
    friend_id integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    blocker_id integer,
    status integer,
    CONSTRAINT fk_friendships_users1 FOREIGN KEY (friendable_id)
        REFERENCES public.users (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT fk_friendships_users2 FOREIGN KEY (friend_id)
        REFERENCES public.users (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
);