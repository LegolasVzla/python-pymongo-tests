CREATE TABLE public.reports_actions(
    id serial PRIMARY KEY,
    users_id integer NOT NULL,
    entity_reported_id integer NOT NULL,
    type_user_reports_id integer NOT NULL,
    report_types_id integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    is_active boolean DEFAULT true,
    is_deleted boolean DEFAULT false,
   CONSTRAINT fk_reports_actions_reports_types FOREIGN KEY (report_types_id)
        REFERENCES public.reports_types (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
);