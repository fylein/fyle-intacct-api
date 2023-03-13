--
-- PostgreSQL database dump
--

-- Dumped from database version 14.6 (Homebrew)
-- Dumped by pg_dump version 14.6 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ap_payment_lineitems; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ap_payment_lineitems (
    id integer NOT NULL,
    amount double precision NOT NULL,
    record_key character varying(255) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    ap_payment_id integer NOT NULL
);


ALTER TABLE public.ap_payment_lineitems OWNER TO postgres;

--
-- Name: ap_payment_lineitems_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ap_payment_lineitems_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ap_payment_lineitems_id_seq OWNER TO postgres;

--
-- Name: ap_payment_lineitems_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ap_payment_lineitems_id_seq OWNED BY public.ap_payment_lineitems.id;


--
-- Name: ap_payments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ap_payments (
    id integer NOT NULL,
    payment_account_id character varying(255) NOT NULL,
    vendor_id character varying(255) NOT NULL,
    description text NOT NULL,
    currency character varying(255) NOT NULL,
    created_at date NOT NULL,
    updated_at date NOT NULL,
    expense_group_id integer NOT NULL
);


ALTER TABLE public.ap_payments OWNER TO postgres;

--
-- Name: ap_payments_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ap_payments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ap_payments_id_seq OWNER TO postgres;

--
-- Name: ap_payments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ap_payments_id_seq OWNED BY public.ap_payments.id;


--
-- Name: auth_cache; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_cache (
    cache_key character varying(255) NOT NULL,
    value text NOT NULL,
    expires timestamp with time zone NOT NULL
);


ALTER TABLE public.auth_cache OWNER TO postgres;

--
-- Name: auth_group; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_group (
    id integer NOT NULL,
    name character varying(150) NOT NULL
);


ALTER TABLE public.auth_group OWNER TO postgres;

--
-- Name: auth_group_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.auth_group_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.auth_group_id_seq OWNER TO postgres;

--
-- Name: auth_group_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.auth_group_id_seq OWNED BY public.auth_group.id;


--
-- Name: auth_group_permissions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_group_permissions (
    id integer NOT NULL,
    group_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.auth_group_permissions OWNER TO postgres;

--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.auth_group_permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.auth_group_permissions_id_seq OWNER TO postgres;

--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.auth_group_permissions_id_seq OWNED BY public.auth_group_permissions.id;


--
-- Name: auth_permission; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_permission (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    content_type_id integer NOT NULL,
    codename character varying(100) NOT NULL
);


ALTER TABLE public.auth_permission OWNER TO postgres;

--
-- Name: auth_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.auth_permission_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.auth_permission_id_seq OWNER TO postgres;

--
-- Name: auth_permission_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.auth_permission_id_seq OWNED BY public.auth_permission.id;


--
-- Name: auth_tokens; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_tokens (
    id integer NOT NULL,
    refresh_token text NOT NULL,
    user_id integer NOT NULL
);


ALTER TABLE public.auth_tokens OWNER TO postgres;

--
-- Name: bill_lineitems; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bill_lineitems (
    id integer NOT NULL,
    expense_type_id character varying(255),
    gl_account_number character varying(255),
    project_id character varying(255),
    location_id character varying(255),
    department_id character varying(255),
    memo text,
    amount double precision NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    bill_id integer NOT NULL,
    expense_id integer NOT NULL,
    billable boolean,
    customer_id character varying(255),
    item_id character varying(255),
    user_defined_dimensions jsonb,
    class_id character varying(255),
    tax_amount double precision,
    tax_code character varying(255),
    cost_type_id character varying(255),
    task_id character varying(255)
);


ALTER TABLE public.bill_lineitems OWNER TO postgres;

--
-- Name: bills; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bills (
    id integer NOT NULL,
    vendor_id character varying(255) NOT NULL,
    description text NOT NULL,
    supdoc_id character varying(255),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    expense_group_id integer NOT NULL,
    memo text,
    transaction_date timestamp with time zone,
    paid_on_sage_intacct boolean NOT NULL,
    payment_synced boolean NOT NULL,
    currency character varying(5) NOT NULL
);


ALTER TABLE public.bills OWNER TO postgres;

--
-- Name: category_mappings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.category_mappings (
    id integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    destination_account_id integer,
    destination_expense_head_id integer,
    source_category_id integer NOT NULL,
    workspace_id integer NOT NULL
);


ALTER TABLE public.category_mappings OWNER TO postgres;

--
-- Name: category_mappings_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.category_mappings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.category_mappings_id_seq OWNER TO postgres;

--
-- Name: category_mappings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.category_mappings_id_seq OWNED BY public.category_mappings.id;


--
-- Name: charge_card_transaction_lineitems; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.charge_card_transaction_lineitems (
    id integer NOT NULL,
    gl_account_number character varying(255),
    project_id character varying(255),
    location_id character varying(255),
    department_id character varying(255),
    amount double precision NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    charge_card_transaction_id integer NOT NULL,
    expense_id integer NOT NULL,
    memo text,
    customer_id character varying(255),
    item_id character varying(255),
    class_id character varying(255),
    tax_amount double precision,
    tax_code character varying(255),
    cost_type_id character varying(255),
    task_id character varying(255)
);


ALTER TABLE public.charge_card_transaction_lineitems OWNER TO postgres;

--
-- Name: charge_card_transactions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.charge_card_transactions (
    id integer NOT NULL,
    charge_card_id character varying(255) NOT NULL,
    description text NOT NULL,
    supdoc_id character varying(255),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    expense_group_id integer NOT NULL,
    memo text,
    transaction_date timestamp with time zone,
    currency character varying(5) NOT NULL,
    reference_no character varying(255) NOT NULL,
    vendor_id character varying(255) NOT NULL,
    payee character varying(255)
);


ALTER TABLE public.charge_card_transactions OWNER TO postgres;

--
-- Name: configurations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.configurations (
    id integer NOT NULL,
    reimbursable_expenses_object character varying(50) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL,
    corporate_credit_card_expenses_object character varying(50),
    import_projects boolean NOT NULL,
    sync_fyle_to_sage_intacct_payments boolean NOT NULL,
    sync_sage_intacct_to_fyle_payments boolean NOT NULL,
    auto_map_employees character varying(50),
    import_categories boolean NOT NULL,
    auto_create_destination_entity boolean NOT NULL,
    memo_structure character varying(100)[] NOT NULL,
    import_tax_codes boolean,
    change_accounting_period boolean NOT NULL,
    import_vendors_as_merchants boolean NOT NULL,
    employee_field_mapping character varying(50),
    is_simplify_report_closure_enabled boolean NOT NULL
);


ALTER TABLE public.configurations OWNER TO postgres;

--
-- Name: destination_attributes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.destination_attributes (
    id integer NOT NULL,
    attribute_type character varying(255) NOT NULL,
    display_name character varying(255) NOT NULL,
    value character varying(255) NOT NULL,
    destination_id character varying(255) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL,
    active boolean,
    detail jsonb,
    auto_created boolean NOT NULL
);


ALTER TABLE public.destination_attributes OWNER TO postgres;

--
-- Name: django_admin_log; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_admin_log (
    id integer NOT NULL,
    action_time timestamp with time zone NOT NULL,
    object_id text,
    object_repr character varying(200) NOT NULL,
    action_flag smallint NOT NULL,
    change_message text NOT NULL,
    content_type_id integer,
    user_id integer NOT NULL,
    CONSTRAINT django_admin_log_action_flag_check CHECK ((action_flag >= 0))
);


ALTER TABLE public.django_admin_log OWNER TO postgres;

--
-- Name: django_admin_log_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.django_admin_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_admin_log_id_seq OWNER TO postgres;

--
-- Name: django_admin_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.django_admin_log_id_seq OWNED BY public.django_admin_log.id;


--
-- Name: django_content_type; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_content_type (
    id integer NOT NULL,
    app_label character varying(100) NOT NULL,
    model character varying(100) NOT NULL
);


ALTER TABLE public.django_content_type OWNER TO postgres;

--
-- Name: django_content_type_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.django_content_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_content_type_id_seq OWNER TO postgres;

--
-- Name: django_content_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.django_content_type_id_seq OWNED BY public.django_content_type.id;


--
-- Name: django_migrations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_migrations (
    id integer NOT NULL,
    app character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    applied timestamp with time zone NOT NULL
);


ALTER TABLE public.django_migrations OWNER TO postgres;

--
-- Name: django_migrations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.django_migrations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_migrations_id_seq OWNER TO postgres;

--
-- Name: django_migrations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.django_migrations_id_seq OWNED BY public.django_migrations.id;


--
-- Name: django_q_ormq; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_q_ormq (
    id integer NOT NULL,
    key character varying(100) NOT NULL,
    payload text NOT NULL,
    lock timestamp with time zone
);


ALTER TABLE public.django_q_ormq OWNER TO postgres;

--
-- Name: django_q_ormq_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.django_q_ormq_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_q_ormq_id_seq OWNER TO postgres;

--
-- Name: django_q_ormq_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.django_q_ormq_id_seq OWNED BY public.django_q_ormq.id;


--
-- Name: django_q_schedule; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_q_schedule (
    id integer NOT NULL,
    func character varying(256) NOT NULL,
    hook character varying(256),
    args text,
    kwargs text,
    schedule_type character varying(1) NOT NULL,
    repeats integer NOT NULL,
    next_run timestamp with time zone,
    task character varying(100),
    name character varying(100),
    minutes smallint,
    cron character varying(100),
    CONSTRAINT django_q_schedule_minutes_check CHECK ((minutes >= 0))
);


ALTER TABLE public.django_q_schedule OWNER TO postgres;

--
-- Name: django_q_schedule_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.django_q_schedule_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_q_schedule_id_seq OWNER TO postgres;

--
-- Name: django_q_schedule_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.django_q_schedule_id_seq OWNED BY public.django_q_schedule.id;


--
-- Name: django_q_task; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_q_task (
    name character varying(100) NOT NULL,
    func character varying(256) NOT NULL,
    hook character varying(256),
    args text,
    kwargs text,
    result text,
    started timestamp with time zone NOT NULL,
    stopped timestamp with time zone NOT NULL,
    success boolean NOT NULL,
    id character varying(32) NOT NULL,
    "group" character varying(100),
    attempt_count integer NOT NULL
);


ALTER TABLE public.django_q_task OWNER TO postgres;

--
-- Name: django_session; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_session (
    session_key character varying(40) NOT NULL,
    session_data text NOT NULL,
    expire_date timestamp with time zone NOT NULL
);


ALTER TABLE public.django_session OWNER TO postgres;

--
-- Name: employee_mappings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.employee_mappings (
    id integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    destination_card_account_id integer,
    destination_employee_id integer,
    destination_vendor_id integer,
    source_employee_id integer NOT NULL,
    workspace_id integer NOT NULL
);


ALTER TABLE public.employee_mappings OWNER TO postgres;

--
-- Name: employee_mappings_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.employee_mappings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.employee_mappings_id_seq OWNER TO postgres;

--
-- Name: employee_mappings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.employee_mappings_id_seq OWNED BY public.employee_mappings.id;


--
-- Name: expense_attributes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.expense_attributes (
    id integer NOT NULL,
    attribute_type character varying(255) NOT NULL,
    display_name character varying(255) NOT NULL,
    value character varying(1000) NOT NULL,
    source_id character varying(255) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL,
    active boolean,
    detail jsonb,
    auto_mapped boolean NOT NULL,
    auto_created boolean NOT NULL
);


ALTER TABLE public.expense_attributes OWNER TO postgres;

--
-- Name: expense_fields; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.expense_fields (
    id integer NOT NULL,
    attribute_type character varying(255) NOT NULL,
    source_field_id integer NOT NULL,
    is_enabled boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL
);


ALTER TABLE public.expense_fields OWNER TO postgres;

--
-- Name: expense_fields_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.expense_fields_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.expense_fields_id_seq OWNER TO postgres;

--
-- Name: expense_fields_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.expense_fields_id_seq OWNED BY public.expense_fields.id;


--
-- Name: expense_group_settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.expense_group_settings (
    id integer NOT NULL,
    reimbursable_expense_group_fields character varying(100)[] NOT NULL,
    corporate_credit_card_expense_group_fields character varying(100)[] NOT NULL,
    expense_state character varying(100) NOT NULL,
    reimbursable_export_date_type character varying(100) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL,
    ccc_export_date_type character varying(100) NOT NULL,
    import_card_credits boolean NOT NULL,
    ccc_expense_state character varying(100)
);


ALTER TABLE public.expense_group_settings OWNER TO postgres;

--
-- Name: expense_group_settings_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.expense_group_settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.expense_group_settings_id_seq OWNER TO postgres;

--
-- Name: expense_group_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.expense_group_settings_id_seq OWNED BY public.expense_group_settings.id;


--
-- Name: expense_groups; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.expense_groups (
    id integer NOT NULL,
    description jsonb,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL,
    fund_source character varying(255) NOT NULL,
    exported_at timestamp with time zone,
    export_type character varying(50)
);


ALTER TABLE public.expense_groups OWNER TO postgres;

--
-- Name: expense_groups_expenses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.expense_groups_expenses (
    id integer NOT NULL,
    expensegroup_id integer NOT NULL,
    expense_id integer NOT NULL
);


ALTER TABLE public.expense_groups_expenses OWNER TO postgres;

--
-- Name: expense_report_lineitems; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.expense_report_lineitems (
    id integer NOT NULL,
    expense_type_id character varying(255),
    gl_account_number character varying(255),
    project_id character varying(255),
    location_id character varying(255),
    department_id character varying(255),
    memo text,
    amount double precision NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    expense_report_id integer NOT NULL,
    expense_id integer NOT NULL,
    transaction_date timestamp with time zone,
    billable boolean,
    customer_id character varying(255),
    item_id character varying(255),
    user_defined_dimensions jsonb,
    expense_payment_type character varying(255),
    class_id character varying(255),
    tax_amount double precision,
    tax_code character varying(255),
    cost_type_id character varying(255),
    task_id character varying(255)
);


ALTER TABLE public.expense_report_lineitems OWNER TO postgres;

--
-- Name: expense_reports; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.expense_reports (
    id integer NOT NULL,
    employee_id character varying(255) NOT NULL,
    description text NOT NULL,
    supdoc_id character varying(255),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    expense_group_id integer NOT NULL,
    memo text,
    transaction_date timestamp with time zone,
    paid_on_sage_intacct boolean NOT NULL,
    payment_synced boolean NOT NULL,
    currency character varying(5) NOT NULL
);


ALTER TABLE public.expense_reports OWNER TO postgres;

--
-- Name: expenses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.expenses (
    id integer NOT NULL,
    employee_email character varying(255) NOT NULL,
    category character varying(255),
    sub_category character varying(255),
    project character varying(255),
    expense_id character varying(255) NOT NULL,
    expense_number character varying(255) NOT NULL,
    claim_number character varying(255),
    amount double precision NOT NULL,
    currency character varying(5) NOT NULL,
    foreign_amount double precision,
    foreign_currency character varying(5),
    settlement_id character varying(255),
    reimbursable boolean NOT NULL,
    state character varying(255) NOT NULL,
    vendor character varying(255),
    cost_center character varying(255),
    purpose text,
    report_id character varying(255) NOT NULL,
    spent_at timestamp with time zone,
    approved_at timestamp with time zone,
    expense_created_at timestamp with time zone NOT NULL,
    expense_updated_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    fund_source character varying(255) NOT NULL,
    custom_properties jsonb,
    verified_at timestamp with time zone,
    billable boolean,
    paid_on_sage_intacct boolean NOT NULL,
    org_id character varying(255),
    tax_amount double precision,
    tax_group_id character varying(255),
    file_ids character varying(255)[],
    payment_number character varying(55)
);


ALTER TABLE public.expenses OWNER TO postgres;

--
-- Name: fyle_accounting_mappings_destinationattribute_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fyle_accounting_mappings_destinationattribute_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.fyle_accounting_mappings_destinationattribute_id_seq OWNER TO postgres;

--
-- Name: fyle_accounting_mappings_destinationattribute_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fyle_accounting_mappings_destinationattribute_id_seq OWNED BY public.destination_attributes.id;


--
-- Name: fyle_accounting_mappings_expenseattribute_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fyle_accounting_mappings_expenseattribute_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.fyle_accounting_mappings_expenseattribute_id_seq OWNER TO postgres;

--
-- Name: fyle_accounting_mappings_expenseattribute_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fyle_accounting_mappings_expenseattribute_id_seq OWNED BY public.expense_attributes.id;


--
-- Name: mappings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.mappings (
    id integer NOT NULL,
    source_type character varying(255) NOT NULL,
    destination_type character varying(255) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    destination_id integer NOT NULL,
    source_id integer NOT NULL,
    workspace_id integer NOT NULL
);


ALTER TABLE public.mappings OWNER TO postgres;

--
-- Name: fyle_accounting_mappings_mapping_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fyle_accounting_mappings_mapping_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.fyle_accounting_mappings_mapping_id_seq OWNER TO postgres;

--
-- Name: fyle_accounting_mappings_mapping_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fyle_accounting_mappings_mapping_id_seq OWNED BY public.mappings.id;


--
-- Name: mapping_settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.mapping_settings (
    id integer NOT NULL,
    source_field character varying(255) NOT NULL,
    destination_field character varying(255) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL,
    import_to_fyle boolean NOT NULL,
    is_custom boolean NOT NULL,
    source_placeholder text,
    expense_field_id integer
);


ALTER TABLE public.mapping_settings OWNER TO postgres;

--
-- Name: fyle_accounting_mappings_mappingsetting_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fyle_accounting_mappings_mappingsetting_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.fyle_accounting_mappings_mappingsetting_id_seq OWNER TO postgres;

--
-- Name: fyle_accounting_mappings_mappingsetting_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fyle_accounting_mappings_mappingsetting_id_seq OWNED BY public.mapping_settings.id;


--
-- Name: fyle_credentials; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fyle_credentials (
    id integer NOT NULL,
    refresh_token text NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL,
    cluster_domain text
);


ALTER TABLE public.fyle_credentials OWNER TO postgres;

--
-- Name: fyle_expense_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fyle_expense_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.fyle_expense_id_seq OWNER TO postgres;

--
-- Name: fyle_expense_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fyle_expense_id_seq OWNED BY public.expenses.id;


--
-- Name: fyle_expensegroup_expenses_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fyle_expensegroup_expenses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.fyle_expensegroup_expenses_id_seq OWNER TO postgres;

--
-- Name: fyle_expensegroup_expenses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fyle_expensegroup_expenses_id_seq OWNED BY public.expense_groups_expenses.id;


--
-- Name: fyle_expensegroup_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fyle_expensegroup_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.fyle_expensegroup_id_seq OWNER TO postgres;

--
-- Name: fyle_expensegroup_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fyle_expensegroup_id_seq OWNED BY public.expense_groups.id;


--
-- Name: fyle_rest_auth_authtokens_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fyle_rest_auth_authtokens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.fyle_rest_auth_authtokens_id_seq OWNER TO postgres;

--
-- Name: fyle_rest_auth_authtokens_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fyle_rest_auth_authtokens_id_seq OWNED BY public.auth_tokens.id;


--
-- Name: general_mappings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.general_mappings (
    id integer NOT NULL,
    default_location_name character varying(255),
    default_location_id character varying(255),
    default_department_name character varying(255),
    default_department_id character varying(255),
    default_project_name character varying(255),
    default_project_id character varying(255),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL,
    default_charge_card_name character varying(255),
    default_charge_card_id character varying(255),
    default_ccc_vendor_name character varying(255),
    default_ccc_vendor_id character varying(255),
    default_item_id character varying(255),
    default_item_name character varying(255),
    payment_account_id character varying(255),
    payment_account_name character varying(255),
    default_ccc_expense_payment_type_id character varying(255),
    default_ccc_expense_payment_type_name character varying(255),
    default_reimbursable_expense_payment_type_id character varying(255),
    default_reimbursable_expense_payment_type_name character varying(255),
    use_intacct_employee_departments boolean NOT NULL,
    use_intacct_employee_locations boolean NOT NULL,
    location_entity_id character varying(255),
    location_entity_name character varying(255),
    default_class_id character varying(255),
    default_class_name character varying(255),
    default_tax_code_id character varying(255),
    default_tax_code_name character varying(255),
    default_credit_card_id character varying(255),
    default_credit_card_name character varying(255)
);


ALTER TABLE public.general_mappings OWNER TO postgres;

--
-- Name: journal_entries; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.journal_entries (
    id integer NOT NULL,
    description text NOT NULL,
    memo text,
    currency character varying(5) NOT NULL,
    supdoc_id character varying(255),
    transaction_date timestamp with time zone,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    expense_group_id integer NOT NULL
);


ALTER TABLE public.journal_entries OWNER TO postgres;

--
-- Name: journal_entries_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.journal_entries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.journal_entries_id_seq OWNER TO postgres;

--
-- Name: journal_entries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.journal_entries_id_seq OWNED BY public.journal_entries.id;


--
-- Name: journal_entry_lineitems; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.journal_entry_lineitems (
    id integer NOT NULL,
    gl_account_number character varying(255),
    project_id character varying(255),
    location_id character varying(255),
    class_id character varying(255),
    department_id character varying(255),
    customer_id character varying(255),
    item_id character varying(255),
    memo text,
    user_defined_dimensions jsonb,
    amount double precision NOT NULL,
    billable boolean,
    transaction_date timestamp with time zone,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    expense_id integer NOT NULL,
    journal_entry_id integer NOT NULL,
    employee_id character varying(255),
    vendor_id character varying(255),
    tax_amount double precision,
    tax_code character varying(255),
    cost_type_id character varying(255),
    task_id character varying(255)
);


ALTER TABLE public.journal_entry_lineitems OWNER TO postgres;

--
-- Name: journal_entry_lineitems_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.journal_entry_lineitems_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.journal_entry_lineitems_id_seq OWNER TO postgres;

--
-- Name: journal_entry_lineitems_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.journal_entry_lineitems_id_seq OWNED BY public.journal_entry_lineitems.id;


--
-- Name: location_entity_mappings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.location_entity_mappings (
    id integer NOT NULL,
    location_entity_name character varying(255) NOT NULL,
    country_name character varying(255),
    destination_id character varying(255),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL
);


ALTER TABLE public.location_entity_mappings OWNER TO postgres;

--
-- Name: location_entity_mappings_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.location_entity_mappings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.location_entity_mappings_id_seq OWNER TO postgres;

--
-- Name: location_entity_mappings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.location_entity_mappings_id_seq OWNED BY public.location_entity_mappings.id;


--
-- Name: mappings_generalmapping_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.mappings_generalmapping_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.mappings_generalmapping_id_seq OWNER TO postgres;

--
-- Name: mappings_generalmapping_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.mappings_generalmapping_id_seq OWNED BY public.general_mappings.id;


--
-- Name: reimbursements; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.reimbursements (
    id integer NOT NULL,
    settlement_id character varying(255) NOT NULL,
    reimbursement_id character varying(255) NOT NULL,
    state character varying(255) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL,
    payment_number character varying(255)
);


ALTER TABLE public.reimbursements OWNER TO postgres;

--
-- Name: reimbursements_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.reimbursements_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.reimbursements_id_seq OWNER TO postgres;

--
-- Name: reimbursements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.reimbursements_id_seq OWNED BY public.reimbursements.id;


--
-- Name: sage_intacct_bill_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sage_intacct_bill_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sage_intacct_bill_id_seq OWNER TO postgres;

--
-- Name: sage_intacct_bill_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sage_intacct_bill_id_seq OWNED BY public.bills.id;


--
-- Name: sage_intacct_billlineitem_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sage_intacct_billlineitem_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sage_intacct_billlineitem_id_seq OWNER TO postgres;

--
-- Name: sage_intacct_billlineitem_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sage_intacct_billlineitem_id_seq OWNED BY public.bill_lineitems.id;


--
-- Name: sage_intacct_chargecardtransaction_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sage_intacct_chargecardtransaction_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sage_intacct_chargecardtransaction_id_seq OWNER TO postgres;

--
-- Name: sage_intacct_chargecardtransaction_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sage_intacct_chargecardtransaction_id_seq OWNED BY public.charge_card_transactions.id;


--
-- Name: sage_intacct_chargecardtransactionlineitem_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sage_intacct_chargecardtransactionlineitem_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sage_intacct_chargecardtransactionlineitem_id_seq OWNER TO postgres;

--
-- Name: sage_intacct_chargecardtransactionlineitem_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sage_intacct_chargecardtransactionlineitem_id_seq OWNED BY public.charge_card_transaction_lineitems.id;


--
-- Name: sage_intacct_credentials; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sage_intacct_credentials (
    id integer NOT NULL,
    si_user_id text NOT NULL,
    si_company_id text NOT NULL,
    si_company_name text NOT NULL,
    si_user_password text NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL
);


ALTER TABLE public.sage_intacct_credentials OWNER TO postgres;

--
-- Name: sage_intacct_expensereport_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sage_intacct_expensereport_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sage_intacct_expensereport_id_seq OWNER TO postgres;

--
-- Name: sage_intacct_expensereport_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sage_intacct_expensereport_id_seq OWNED BY public.expense_reports.id;


--
-- Name: sage_intacct_expensereportlineitem_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sage_intacct_expensereportlineitem_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sage_intacct_expensereportlineitem_id_seq OWNER TO postgres;

--
-- Name: sage_intacct_expensereportlineitem_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sage_intacct_expensereportlineitem_id_seq OWNED BY public.expense_report_lineitems.id;


--
-- Name: sage_intacct_reimbursement_lineitems; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sage_intacct_reimbursement_lineitems (
    id integer NOT NULL,
    amount double precision NOT NULL,
    record_key character varying(255) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    sage_intacct_reimbursement_id integer NOT NULL
);


ALTER TABLE public.sage_intacct_reimbursement_lineitems OWNER TO postgres;

--
-- Name: sage_intacct_reimbursement_lineitems_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sage_intacct_reimbursement_lineitems_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sage_intacct_reimbursement_lineitems_id_seq OWNER TO postgres;

--
-- Name: sage_intacct_reimbursement_lineitems_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sage_intacct_reimbursement_lineitems_id_seq OWNED BY public.sage_intacct_reimbursement_lineitems.id;


--
-- Name: sage_intacct_reimbursements; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sage_intacct_reimbursements (
    id integer NOT NULL,
    account_id character varying(255) NOT NULL,
    employee_id character varying(255) NOT NULL,
    memo text NOT NULL,
    payment_description text NOT NULL,
    created_at date NOT NULL,
    updated_at date NOT NULL,
    expense_group_id integer NOT NULL
);


ALTER TABLE public.sage_intacct_reimbursements OWNER TO postgres;

--
-- Name: sage_intacct_reimbursements_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sage_intacct_reimbursements_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sage_intacct_reimbursements_id_seq OWNER TO postgres;

--
-- Name: sage_intacct_reimbursements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sage_intacct_reimbursements_id_seq OWNED BY public.sage_intacct_reimbursements.id;


--
-- Name: task_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.task_logs (
    id integer NOT NULL,
    type character varying(50) NOT NULL,
    task_id character varying(255),
    status character varying(255) NOT NULL,
    detail jsonb,
    sage_intacct_errors jsonb,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    bill_id integer,
    expense_report_id integer,
    expense_group_id integer,
    workspace_id integer NOT NULL,
    charge_card_transaction_id integer,
    ap_payment_id integer,
    sage_intacct_reimbursement_id integer,
    journal_entry_id integer
);


ALTER TABLE public.task_logs OWNER TO postgres;

--
-- Name: tasks_tasklog_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tasks_tasklog_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tasks_tasklog_id_seq OWNER TO postgres;

--
-- Name: tasks_tasklog_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tasks_tasklog_id_seq OWNED BY public.task_logs.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    password character varying(128) NOT NULL,
    last_login timestamp with time zone,
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    user_id character varying(255) NOT NULL,
    full_name character varying(255) NOT NULL,
    active boolean NOT NULL,
    staff boolean NOT NULL,
    admin boolean NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_user_id_seq OWNER TO postgres;

--
-- Name: users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_user_id_seq OWNED BY public.users.id;


--
-- Name: workspace_schedules; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.workspace_schedules (
    id integer NOT NULL,
    enabled boolean NOT NULL,
    start_datetime timestamp with time zone,
    interval_hours integer,
    schedule_id integer,
    workspace_id integer NOT NULL,
    additional_email_options jsonb,
    emails_selected character varying(255)[],
    error_count integer
);


ALTER TABLE public.workspace_schedules OWNER TO postgres;

--
-- Name: workspace_schedules_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.workspace_schedules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workspace_schedules_id_seq OWNER TO postgres;

--
-- Name: workspace_schedules_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.workspace_schedules_id_seq OWNED BY public.workspace_schedules.id;


--
-- Name: workspaces; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.workspaces (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    fyle_org_id character varying(255) NOT NULL,
    last_synced_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    destination_synced_at timestamp with time zone,
    source_synced_at timestamp with time zone,
    cluster_domain character varying(255),
    ccc_last_synced_at timestamp with time zone
);


ALTER TABLE public.workspaces OWNER TO postgres;

--
-- Name: workspaces_fylecredential_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.workspaces_fylecredential_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workspaces_fylecredential_id_seq OWNER TO postgres;

--
-- Name: workspaces_fylecredential_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.workspaces_fylecredential_id_seq OWNED BY public.fyle_credentials.id;


--
-- Name: workspaces_sageintacctcredential_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.workspaces_sageintacctcredential_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workspaces_sageintacctcredential_id_seq OWNER TO postgres;

--
-- Name: workspaces_sageintacctcredential_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.workspaces_sageintacctcredential_id_seq OWNED BY public.sage_intacct_credentials.id;


--
-- Name: workspaces_user; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.workspaces_user (
    id integer NOT NULL,
    workspace_id integer NOT NULL,
    user_id integer NOT NULL
);


ALTER TABLE public.workspaces_user OWNER TO postgres;

--
-- Name: workspaces_workspace_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.workspaces_workspace_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workspaces_workspace_id_seq OWNER TO postgres;

--
-- Name: workspaces_workspace_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.workspaces_workspace_id_seq OWNED BY public.workspaces.id;


--
-- Name: workspaces_workspace_user_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.workspaces_workspace_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workspaces_workspace_user_id_seq OWNER TO postgres;

--
-- Name: workspaces_workspace_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.workspaces_workspace_user_id_seq OWNED BY public.workspaces_user.id;


--
-- Name: workspaces_workspacegeneralsettings_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.workspaces_workspacegeneralsettings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workspaces_workspacegeneralsettings_id_seq OWNER TO postgres;

--
-- Name: workspaces_workspacegeneralsettings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.workspaces_workspacegeneralsettings_id_seq OWNED BY public.configurations.id;


--
-- Name: ap_payment_lineitems id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ap_payment_lineitems ALTER COLUMN id SET DEFAULT nextval('public.ap_payment_lineitems_id_seq'::regclass);


--
-- Name: ap_payments id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ap_payments ALTER COLUMN id SET DEFAULT nextval('public.ap_payments_id_seq'::regclass);


--
-- Name: auth_group id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group ALTER COLUMN id SET DEFAULT nextval('public.auth_group_id_seq'::regclass);


--
-- Name: auth_group_permissions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions ALTER COLUMN id SET DEFAULT nextval('public.auth_group_permissions_id_seq'::regclass);


--
-- Name: auth_permission id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_permission ALTER COLUMN id SET DEFAULT nextval('public.auth_permission_id_seq'::regclass);


--
-- Name: auth_tokens id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_tokens ALTER COLUMN id SET DEFAULT nextval('public.fyle_rest_auth_authtokens_id_seq'::regclass);


--
-- Name: bill_lineitems id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bill_lineitems ALTER COLUMN id SET DEFAULT nextval('public.sage_intacct_billlineitem_id_seq'::regclass);


--
-- Name: bills id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bills ALTER COLUMN id SET DEFAULT nextval('public.sage_intacct_bill_id_seq'::regclass);


--
-- Name: category_mappings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.category_mappings ALTER COLUMN id SET DEFAULT nextval('public.category_mappings_id_seq'::regclass);


--
-- Name: charge_card_transaction_lineitems id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.charge_card_transaction_lineitems ALTER COLUMN id SET DEFAULT nextval('public.sage_intacct_chargecardtransactionlineitem_id_seq'::regclass);


--
-- Name: charge_card_transactions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.charge_card_transactions ALTER COLUMN id SET DEFAULT nextval('public.sage_intacct_chargecardtransaction_id_seq'::regclass);


--
-- Name: configurations id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.configurations ALTER COLUMN id SET DEFAULT nextval('public.workspaces_workspacegeneralsettings_id_seq'::regclass);


--
-- Name: destination_attributes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.destination_attributes ALTER COLUMN id SET DEFAULT nextval('public.fyle_accounting_mappings_destinationattribute_id_seq'::regclass);


--
-- Name: django_admin_log id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_admin_log ALTER COLUMN id SET DEFAULT nextval('public.django_admin_log_id_seq'::regclass);


--
-- Name: django_content_type id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_content_type ALTER COLUMN id SET DEFAULT nextval('public.django_content_type_id_seq'::regclass);


--
-- Name: django_migrations id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_migrations ALTER COLUMN id SET DEFAULT nextval('public.django_migrations_id_seq'::regclass);


--
-- Name: django_q_ormq id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_q_ormq ALTER COLUMN id SET DEFAULT nextval('public.django_q_ormq_id_seq'::regclass);


--
-- Name: django_q_schedule id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_q_schedule ALTER COLUMN id SET DEFAULT nextval('public.django_q_schedule_id_seq'::regclass);


--
-- Name: employee_mappings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee_mappings ALTER COLUMN id SET DEFAULT nextval('public.employee_mappings_id_seq'::regclass);


--
-- Name: expense_attributes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_attributes ALTER COLUMN id SET DEFAULT nextval('public.fyle_accounting_mappings_expenseattribute_id_seq'::regclass);


--
-- Name: expense_fields id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_fields ALTER COLUMN id SET DEFAULT nextval('public.expense_fields_id_seq'::regclass);


--
-- Name: expense_group_settings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_group_settings ALTER COLUMN id SET DEFAULT nextval('public.expense_group_settings_id_seq'::regclass);


--
-- Name: expense_groups id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_groups ALTER COLUMN id SET DEFAULT nextval('public.fyle_expensegroup_id_seq'::regclass);


--
-- Name: expense_groups_expenses id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_groups_expenses ALTER COLUMN id SET DEFAULT nextval('public.fyle_expensegroup_expenses_id_seq'::regclass);


--
-- Name: expense_report_lineitems id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_report_lineitems ALTER COLUMN id SET DEFAULT nextval('public.sage_intacct_expensereportlineitem_id_seq'::regclass);


--
-- Name: expense_reports id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_reports ALTER COLUMN id SET DEFAULT nextval('public.sage_intacct_expensereport_id_seq'::regclass);


--
-- Name: expenses id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expenses ALTER COLUMN id SET DEFAULT nextval('public.fyle_expense_id_seq'::regclass);


--
-- Name: fyle_credentials id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fyle_credentials ALTER COLUMN id SET DEFAULT nextval('public.workspaces_fylecredential_id_seq'::regclass);


--
-- Name: general_mappings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.general_mappings ALTER COLUMN id SET DEFAULT nextval('public.mappings_generalmapping_id_seq'::regclass);


--
-- Name: journal_entries id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.journal_entries ALTER COLUMN id SET DEFAULT nextval('public.journal_entries_id_seq'::regclass);


--
-- Name: journal_entry_lineitems id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.journal_entry_lineitems ALTER COLUMN id SET DEFAULT nextval('public.journal_entry_lineitems_id_seq'::regclass);


--
-- Name: location_entity_mappings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.location_entity_mappings ALTER COLUMN id SET DEFAULT nextval('public.location_entity_mappings_id_seq'::regclass);


--
-- Name: mapping_settings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mapping_settings ALTER COLUMN id SET DEFAULT nextval('public.fyle_accounting_mappings_mappingsetting_id_seq'::regclass);


--
-- Name: mappings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mappings ALTER COLUMN id SET DEFAULT nextval('public.fyle_accounting_mappings_mapping_id_seq'::regclass);


--
-- Name: reimbursements id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reimbursements ALTER COLUMN id SET DEFAULT nextval('public.reimbursements_id_seq'::regclass);


--
-- Name: sage_intacct_credentials id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sage_intacct_credentials ALTER COLUMN id SET DEFAULT nextval('public.workspaces_sageintacctcredential_id_seq'::regclass);


--
-- Name: sage_intacct_reimbursement_lineitems id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sage_intacct_reimbursement_lineitems ALTER COLUMN id SET DEFAULT nextval('public.sage_intacct_reimbursement_lineitems_id_seq'::regclass);


--
-- Name: sage_intacct_reimbursements id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sage_intacct_reimbursements ALTER COLUMN id SET DEFAULT nextval('public.sage_intacct_reimbursements_id_seq'::regclass);


--
-- Name: task_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_logs ALTER COLUMN id SET DEFAULT nextval('public.tasks_tasklog_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_user_id_seq'::regclass);


--
-- Name: workspace_schedules id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workspace_schedules ALTER COLUMN id SET DEFAULT nextval('public.workspace_schedules_id_seq'::regclass);


--
-- Name: workspaces id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workspaces ALTER COLUMN id SET DEFAULT nextval('public.workspaces_workspace_id_seq'::regclass);


--
-- Name: workspaces_user id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workspaces_user ALTER COLUMN id SET DEFAULT nextval('public.workspaces_workspace_user_id_seq'::regclass);


--
-- Data for Name: ap_payment_lineitems; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.ap_payment_lineitems (id, amount, record_key, created_at, updated_at, ap_payment_id) FROM stdin;
\.


--
-- Data for Name: ap_payments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.ap_payments (id, payment_account_id, vendor_id, description, currency, created_at, updated_at, expense_group_id) FROM stdin;
\.


--
-- Data for Name: auth_cache; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_cache (cache_key, value, expires) FROM stdin;
\.


--
-- Data for Name: auth_group; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_group (id, name) FROM stdin;
\.


--
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_group_permissions (id, group_id, permission_id) FROM stdin;
\.


--
-- Data for Name: auth_permission; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_permission (id, name, content_type_id, codename) FROM stdin;
1	Can add log entry	1	add_logentry
2	Can change log entry	1	change_logentry
3	Can delete log entry	1	delete_logentry
4	Can view log entry	1	view_logentry
5	Can add permission	2	add_permission
6	Can change permission	2	change_permission
7	Can delete permission	2	delete_permission
8	Can view permission	2	view_permission
9	Can add group	3	add_group
10	Can change group	3	change_group
11	Can delete group	3	delete_group
12	Can view group	3	view_group
13	Can add content type	4	add_contenttype
14	Can change content type	4	change_contenttype
15	Can delete content type	4	delete_contenttype
16	Can view content type	4	view_contenttype
17	Can add session	5	add_session
18	Can change session	5	change_session
19	Can delete session	5	delete_session
20	Can view session	5	view_session
21	Can add Scheduled task	6	add_schedule
22	Can change Scheduled task	6	change_schedule
23	Can delete Scheduled task	6	delete_schedule
24	Can view Scheduled task	6	view_schedule
25	Can add task	7	add_task
26	Can change task	7	change_task
27	Can delete task	7	delete_task
28	Can view task	7	view_task
29	Can add Failed task	8	add_failure
30	Can change Failed task	8	change_failure
31	Can delete Failed task	8	delete_failure
32	Can view Failed task	8	view_failure
33	Can add Successful task	9	add_success
34	Can change Successful task	9	change_success
35	Can delete Successful task	9	delete_success
36	Can view Successful task	9	view_success
37	Can add Queued task	10	add_ormq
38	Can change Queued task	10	change_ormq
39	Can delete Queued task	10	delete_ormq
40	Can view Queued task	10	view_ormq
41	Can add auth token	11	add_authtoken
42	Can change auth token	11	change_authtoken
43	Can delete auth token	11	delete_authtoken
44	Can view auth token	11	view_authtoken
45	Can add destination attribute	12	add_destinationattribute
46	Can change destination attribute	12	change_destinationattribute
47	Can delete destination attribute	12	delete_destinationattribute
48	Can view destination attribute	12	view_destinationattribute
49	Can add expense attribute	13	add_expenseattribute
50	Can change expense attribute	13	change_expenseattribute
51	Can delete expense attribute	13	delete_expenseattribute
52	Can view expense attribute	13	view_expenseattribute
53	Can add mapping setting	14	add_mappingsetting
54	Can change mapping setting	14	change_mappingsetting
55	Can delete mapping setting	14	delete_mappingsetting
56	Can view mapping setting	14	view_mappingsetting
57	Can add mapping	15	add_mapping
58	Can change mapping	15	change_mapping
59	Can delete mapping	15	delete_mapping
60	Can view mapping	15	view_mapping
61	Can add employee mapping	16	add_employeemapping
62	Can change employee mapping	16	change_employeemapping
63	Can delete employee mapping	16	delete_employeemapping
64	Can view employee mapping	16	view_employeemapping
65	Can add category mapping	17	add_categorymapping
66	Can change category mapping	17	change_categorymapping
67	Can delete category mapping	17	delete_categorymapping
68	Can view category mapping	17	view_categorymapping
69	Can add user	18	add_user
70	Can change user	18	change_user
71	Can delete user	18	delete_user
72	Can view user	18	view_user
73	Can add workspace	19	add_workspace
74	Can change workspace	19	change_workspace
75	Can delete workspace	19	delete_workspace
76	Can view workspace	19	view_workspace
77	Can add sage intacct credential	20	add_sageintacctcredential
78	Can change sage intacct credential	20	change_sageintacctcredential
79	Can delete sage intacct credential	20	delete_sageintacctcredential
80	Can view sage intacct credential	20	view_sageintacctcredential
81	Can add fyle credential	21	add_fylecredential
82	Can change fyle credential	21	change_fylecredential
83	Can delete fyle credential	21	delete_fylecredential
84	Can view fyle credential	21	view_fylecredential
85	Can add workspace schedule	22	add_workspaceschedule
86	Can change workspace schedule	22	change_workspaceschedule
87	Can delete workspace schedule	22	delete_workspaceschedule
88	Can view workspace schedule	22	view_workspaceschedule
89	Can add configuration	23	add_configuration
90	Can change configuration	23	change_configuration
91	Can delete configuration	23	delete_configuration
92	Can view configuration	23	view_configuration
93	Can add expense	24	add_expense
94	Can change expense	24	change_expense
95	Can delete expense	24	delete_expense
96	Can view expense	24	view_expense
97	Can add expense group	25	add_expensegroup
98	Can change expense group	25	change_expensegroup
99	Can delete expense group	25	delete_expensegroup
100	Can view expense group	25	view_expensegroup
101	Can add expense group settings	26	add_expensegroupsettings
102	Can change expense group settings	26	change_expensegroupsettings
103	Can delete expense group settings	26	delete_expensegroupsettings
104	Can view expense group settings	26	view_expensegroupsettings
105	Can add reimbursement	27	add_reimbursement
106	Can change reimbursement	27	change_reimbursement
107	Can delete reimbursement	27	delete_reimbursement
108	Can view reimbursement	27	view_reimbursement
109	Can add bill	28	add_bill
110	Can change bill	28	change_bill
111	Can delete bill	28	delete_bill
112	Can view bill	28	view_bill
113	Can add bill lineitem	29	add_billlineitem
114	Can change bill lineitem	29	change_billlineitem
115	Can delete bill lineitem	29	delete_billlineitem
116	Can view bill lineitem	29	view_billlineitem
117	Can add expense report	30	add_expensereport
118	Can change expense report	30	change_expensereport
119	Can delete expense report	30	delete_expensereport
120	Can view expense report	30	view_expensereport
121	Can add expense report lineitem	31	add_expensereportlineitem
122	Can change expense report lineitem	31	change_expensereportlineitem
123	Can delete expense report lineitem	31	delete_expensereportlineitem
124	Can view expense report lineitem	31	view_expensereportlineitem
125	Can add charge card transaction	32	add_chargecardtransaction
126	Can change charge card transaction	32	change_chargecardtransaction
127	Can delete charge card transaction	32	delete_chargecardtransaction
128	Can view charge card transaction	32	view_chargecardtransaction
129	Can add charge card transaction lineitem	33	add_chargecardtransactionlineitem
130	Can change charge card transaction lineitem	33	change_chargecardtransactionlineitem
131	Can delete charge card transaction lineitem	33	delete_chargecardtransactionlineitem
132	Can view charge card transaction lineitem	33	view_chargecardtransactionlineitem
133	Can add ap payment	34	add_appayment
134	Can change ap payment	34	change_appayment
135	Can delete ap payment	34	delete_appayment
136	Can view ap payment	34	view_appayment
137	Can add sage intacct reimbursement	35	add_sageintacctreimbursement
138	Can change sage intacct reimbursement	35	change_sageintacctreimbursement
139	Can delete sage intacct reimbursement	35	delete_sageintacctreimbursement
140	Can view sage intacct reimbursement	35	view_sageintacctreimbursement
141	Can add sage intacct reimbursement lineitem	36	add_sageintacctreimbursementlineitem
142	Can change sage intacct reimbursement lineitem	36	change_sageintacctreimbursementlineitem
143	Can delete sage intacct reimbursement lineitem	36	delete_sageintacctreimbursementlineitem
144	Can view sage intacct reimbursement lineitem	36	view_sageintacctreimbursementlineitem
145	Can add ap payment lineitem	37	add_appaymentlineitem
146	Can change ap payment lineitem	37	change_appaymentlineitem
147	Can delete ap payment lineitem	37	delete_appaymentlineitem
148	Can view ap payment lineitem	37	view_appaymentlineitem
149	Can add journal entry	38	add_journalentry
150	Can change journal entry	38	change_journalentry
151	Can delete journal entry	38	delete_journalentry
152	Can view journal entry	38	view_journalentry
153	Can add journal entry lineitem	39	add_journalentrylineitem
154	Can change journal entry lineitem	39	change_journalentrylineitem
155	Can delete journal entry lineitem	39	delete_journalentrylineitem
156	Can view journal entry lineitem	39	view_journalentrylineitem
157	Can add task log	40	add_tasklog
158	Can change task log	40	change_tasklog
159	Can delete task log	40	delete_tasklog
160	Can view task log	40	view_tasklog
161	Can add general mapping	41	add_generalmapping
162	Can change general mapping	41	change_generalmapping
163	Can delete general mapping	41	delete_generalmapping
164	Can view general mapping	41	view_generalmapping
165	Can add location entity mapping	42	add_locationentitymapping
166	Can change location entity mapping	42	change_locationentitymapping
167	Can delete location entity mapping	42	delete_locationentitymapping
168	Can view location entity mapping	42	view_locationentitymapping
169	Can add expense field	43	add_expensefield
170	Can change expense field	43	change_expensefield
171	Can delete expense field	43	delete_expensefield
172	Can view expense field	43	view_expensefield
\.


--
-- Data for Name: auth_tokens; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_tokens (id, refresh_token, user_id) FROM stdin;
1	eyJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2NjM2NjMwNzIsImlzcyI6IkZ5bGVBcHAiLCJvcmdfdXNlcl9pZCI6Ilwib3VWTE9ZUDhsZWxOXCIiLCJ0cGFfaWQiOiJcInRwYXlmalBQSFREZ3ZcIiIsInRwYV9uYW1lIjoiXCJGeWxlIDw-IFNhZ2UgSW4uLlwiIiwiY2x1c3Rlcl9kb21haW4iOiJcImh0dHBzOi8vc3RhZ2luZy5meWxlLnRlY2hcIiIsImV4cCI6MTk3OTAyMzA3Mn0.NGRySUzDx7ycSD_6LaRy_wTGMD7Yl-u3I1FmOo9BWhk	1
\.


--
-- Data for Name: bill_lineitems; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.bill_lineitems (id, expense_type_id, gl_account_number, project_id, location_id, department_id, memo, amount, created_at, updated_at, bill_id, expense_id, billable, customer_id, item_id, user_defined_dimensions, class_id, tax_amount, tax_code, cost_type_id, task_id) FROM stdin;
\.


--
-- Data for Name: bills; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.bills (id, vendor_id, description, supdoc_id, created_at, updated_at, expense_group_id, memo, transaction_date, paid_on_sage_intacct, payment_synced, currency) FROM stdin;
\.


--
-- Data for Name: category_mappings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.category_mappings (id, created_at, updated_at, destination_account_id, destination_expense_head_id, source_category_id, workspace_id) FROM stdin;
1	2022-09-20 14:10:38.707759+05:30	2022-09-20 14:10:38.70782+05:30	792	927	26	1
2	2022-09-20 14:10:38.707876+05:30	2022-09-20 14:10:38.707906+05:30	792	931	20	1
3	2022-09-20 14:10:38.707955+05:30	2022-09-20 14:10:38.707984+05:30	792	928	27	1
4	2022-09-20 14:10:38.708033+05:30	2022-09-20 14:10:38.708062+05:30	807	930	23	1
5	2022-09-20 14:10:38.708112+05:30	2022-09-20 14:10:38.708149+05:30	807	932	21	1
6	2022-09-20 14:10:38.70843+05:30	2022-09-20 14:10:38.708473+05:30	796	929	22	1
7	2022-09-20 14:10:38.708547+05:30	2022-09-20 14:10:38.708578+05:30	796	926	25	1
8	2022-09-20 14:10:38.70874+05:30	2022-09-20 14:10:38.708764+05:30	792	925	24	1
9	2022-09-20 14:19:07.95636+05:30	2022-09-20 14:19:07.956416+05:30	896	\N	325	1
10	2022-09-28 17:26:20.729414+05:30	2022-09-28 17:26:20.729471+05:30	756	\N	327	1
\.


--
-- Data for Name: charge_card_transaction_lineitems; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.charge_card_transaction_lineitems (id, gl_account_number, project_id, location_id, department_id, amount, created_at, updated_at, charge_card_transaction_id, expense_id, memo, customer_id, item_id, class_id, tax_amount, tax_code, cost_type_id, task_id) FROM stdin;
\.


--
-- Data for Name: charge_card_transactions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.charge_card_transactions (id, charge_card_id, description, supdoc_id, created_at, updated_at, expense_group_id, memo, transaction_date, currency, reference_no, vendor_id, payee) FROM stdin;
\.


--
-- Data for Name: configurations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.configurations (id, reimbursable_expenses_object, created_at, updated_at, workspace_id, corporate_credit_card_expenses_object, import_projects, sync_fyle_to_sage_intacct_payments, sync_sage_intacct_to_fyle_payments, auto_map_employees, import_categories, auto_create_destination_entity, memo_structure, import_tax_codes, change_accounting_period, import_vendors_as_merchants, employee_field_mapping, is_simplify_report_closure_enabled) FROM stdin;
1	BILL	2022-09-20 14:09:32.015647+05:30	2022-09-20 14:16:24.926422+05:30	1	BILL	t	t	f	EMAIL	f	t	{employee_email,category,spent_on,report_number,purpose,expense_link}	t	t	t	VENDOR	f
\.


--
-- Data for Name: destination_attributes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.destination_attributes (id, attribute_type, display_name, value, destination_id, created_at, updated_at, workspace_id, active, detail, auto_created) FROM stdin;
1	LOCATION_ENTITY	location entity	USA 1	100	2022-09-20 14:08:53.467623+05:30	2022-09-20 14:08:53.467654+05:30	1	\N	{"country": "United States"}	f
2	LOCATION_ENTITY	location entity	USA 2	200	2022-09-20 14:08:53.467725+05:30	2022-09-20 14:08:53.467767+05:30	1	\N	{"country": "United States"}	f
3	LOCATION_ENTITY	location entity	Holding Company	300	2022-09-20 14:08:53.467858+05:30	2022-09-20 14:08:53.467892+05:30	1	\N	{"country": "United States"}	f
4	LOCATION_ENTITY	location entity	Canada	400	2022-09-20 14:08:53.467952+05:30	2022-09-20 14:08:53.467974+05:30	1	\N	{"country": "Canada"}	f
5	LOCATION_ENTITY	location entity	United Kingdom	500	2022-09-20 14:08:53.468564+05:30	2022-09-20 14:08:53.468612+05:30	1	\N	{"country": "United Kingdom"}	f
6	LOCATION_ENTITY	location entity	Australia	600	2022-09-20 14:08:53.468695+05:30	2022-09-20 14:08:53.468719+05:30	1	\N	{"country": "Australia"}	f
7	LOCATION_ENTITY	location entity	South Africa	700	2022-09-20 14:08:53.468885+05:30	2022-09-20 14:08:53.468927+05:30	1	\N	{"country": "South Africa"}	f
8	LOCATION_ENTITY	location entity	Elimination - NA	900	2022-09-20 14:08:53.469363+05:30	2022-09-20 14:08:53.469389+05:30	1	\N	{"country": null}	f
9	LOCATION_ENTITY	location entity	Elimination - Global	910	2022-09-20 14:08:53.469468+05:30	2022-09-20 14:08:53.469498+05:30	1	\N	{"country": null}	f
10	LOCATION_ENTITY	location entity	Elimination - Sub	920	2022-09-20 14:08:53.46957+05:30	2022-09-20 14:08:53.46959+05:30	1	\N	{"country": null}	f
11	LOCATION	location	Australia	600	2022-09-20 14:09:08.709874+05:30	2022-09-20 14:09:08.709918+05:30	1	\N	\N	f
12	LOCATION	location	New South Wales	700-New South Wales	2022-09-20 14:09:08.709971+05:30	2022-09-20 14:09:08.709999+05:30	1	\N	\N	f
13	CUSTOMER	customer	AB SQUARE	10001	2022-09-20 14:09:16.581594+05:30	2022-09-20 14:09:16.581644+05:30	1	\N	\N	f
14	CUSTOMER	customer	EZ Services	10002	2022-09-20 14:09:16.581716+05:30	2022-09-20 14:09:16.581749+05:30	1	\N	\N	f
15	CUSTOMER	customer	Uplift Services	10003	2022-09-20 14:09:16.581815+05:30	2022-09-20 14:09:16.581847+05:30	1	\N	\N	f
16	CUSTOMER	customer	Sagacent Finance	10004	2022-09-20 14:09:16.581966+05:30	2022-09-20 14:09:16.582022+05:30	1	\N	\N	f
17	CUSTOMER	customer	Nirvana	10005	2022-09-20 14:09:16.582145+05:30	2022-09-20 14:09:16.582199+05:30	1	\N	\N	f
18	CUSTOMER	customer	AG Insurance	10006	2022-09-20 14:09:16.582471+05:30	2022-09-20 14:09:16.58252+05:30	1	\N	\N	f
19	CUSTOMER	customer	RedFin Insurance	10007	2022-09-20 14:09:16.582626+05:30	2022-09-20 14:09:16.582657+05:30	1	\N	\N	f
20	CUSTOMER	customer	Cvibe Insurance	10008	2022-09-20 14:09:16.582715+05:30	2022-09-20 14:09:16.582745+05:30	1	\N	\N	f
21	CUSTOMER	customer	CostLess Insurance	10009	2022-09-20 14:09:16.582802+05:30	2022-09-20 14:09:16.582831+05:30	1	\N	\N	f
22	CUSTOMER	customer	Community Agency Services	10010	2022-09-20 14:09:16.582888+05:30	2022-09-20 14:09:16.582918+05:30	1	\N	\N	f
23	CUSTOMER	customer	GBD Inc	10011	2022-09-20 14:09:16.582975+05:30	2022-09-20 14:09:16.583004+05:30	1	\N	\N	f
24	CUSTOMER	customer	MK Manufacturing	10012	2022-09-20 14:09:16.583061+05:30	2022-09-20 14:09:16.5831+05:30	1	\N	\N	f
25	CUSTOMER	customer	Gemini Manufacturing Services	10013	2022-09-20 14:09:16.583168+05:30	2022-09-20 14:09:16.583197+05:30	1	\N	\N	f
26	CUSTOMER	customer	Fab Seven	10014	2022-09-20 14:09:16.583263+05:30	2022-09-20 14:09:16.583302+05:30	1	\N	\N	f
27	CUSTOMER	customer	GS Industries	10015	2022-09-20 14:09:16.583537+05:30	2022-09-20 14:09:16.583577+05:30	1	\N	\N	f
28	CUSTOMER	customer	BioClear	10016	2022-09-20 14:09:16.583663+05:30	2022-09-20 14:09:16.583693+05:30	1	\N	\N	f
29	CUSTOMER	customer	Applied Biomics	10017	2022-09-20 14:09:16.583752+05:30	2022-09-20 14:09:16.583781+05:30	1	\N	\N	f
30	CUSTOMER	customer	Proton Centric	10018	2022-09-20 14:09:16.583839+05:30	2022-09-20 14:09:16.583868+05:30	1	\N	\N	f
31	CUSTOMER	customer	BioMed Labs	10019	2022-09-20 14:09:16.583925+05:30	2022-09-20 14:09:16.583956+05:30	1	\N	\N	f
32	CUSTOMER	customer	Nanocell	10020	2022-09-20 14:09:16.584035+05:30	2022-09-20 14:09:16.584066+05:30	1	\N	\N	f
33	CUSTOMER	customer	Genentech, Inc.	10021	2022-09-20 14:09:16.584123+05:30	2022-09-20 14:09:16.584153+05:30	1	\N	\N	f
34	CUSTOMER	customer	Matrox Electronic Systems Ltd.	10022	2022-09-20 14:09:16.58421+05:30	2022-09-20 14:09:16.584239+05:30	1	\N	\N	f
35	CUSTOMER	customer	Pacificorp	10023	2022-09-20 14:09:16.58442+05:30	2022-09-20 14:09:16.584461+05:30	1	\N	\N	f
36	CUSTOMER	customer	Virtela Communications	10024	2022-09-20 14:09:16.584515+05:30	2022-09-20 14:09:16.584543+05:30	1	\N	\N	f
37	CUSTOMER	customer	Sonicwall, Inc.	10025	2022-09-20 14:09:16.584607+05:30	2022-09-20 14:09:16.584845+05:30	1	\N	\N	f
38	CUSTOMER	customer	Spencer, Scott and Dwyer	10026	2022-09-20 14:09:16.584926+05:30	2022-09-20 14:09:16.584955+05:30	1	\N	\N	f
39	CUSTOMER	customer	Klondike Gold Corporation	10027	2022-09-20 14:09:16.585011+05:30	2022-09-20 14:09:16.585038+05:30	1	\N	\N	f
40	CUSTOMER	customer	Davis and Young LPA	10028	2022-09-20 14:09:16.585092+05:30	2022-09-20 14:09:16.585235+05:30	1	\N	\N	f
41	CUSTOMER	customer	Bayer Corporation	10029	2022-09-20 14:09:16.585328+05:30	2022-09-20 14:09:16.585376+05:30	1	\N	\N	f
42	CUSTOMER	customer	Rand Corporation	10030	2022-09-20 14:09:16.5855+05:30	2022-09-20 14:09:16.585671+05:30	1	\N	\N	f
43	CUSTOMER	customer	Cleco Corporation	10031	2022-09-20 14:09:16.585737+05:30	2022-09-20 14:09:16.585766+05:30	1	\N	\N	f
44	CUSTOMER	customer	Leo A. Daly Company	10032	2022-09-20 14:09:16.585986+05:30	2022-09-20 14:09:16.586041+05:30	1	\N	\N	f
45	CUSTOMER	customer	United Security Bank	10033	2022-09-20 14:09:16.586148+05:30	2022-09-20 14:09:16.586191+05:30	1	\N	\N	f
46	CUSTOMER	customer	Novamed	10034	2022-09-20 14:09:16.586298+05:30	2022-09-20 14:09:16.586346+05:30	1	\N	\N	f
47	CUSTOMER	customer	Render	10041	2022-09-20 14:09:16.586447+05:30	2022-09-20 14:09:16.586611+05:30	1	\N	\N	f
48	CUSTOMER	customer	Projo	10042	2022-09-20 14:09:16.586725+05:30	2022-09-20 14:09:16.58679+05:30	1	\N	\N	f
49	CUSTOMER	customer	Finscent	10043	2022-09-20 14:09:16.587077+05:30	2022-09-20 14:09:16.587276+05:30	1	\N	\N	f
50	CUSTOMER	customer	Innovation Arch	10044	2022-09-20 14:09:16.587528+05:30	2022-09-20 14:09:16.587573+05:30	1	\N	\N	f
51	CUSTOMER	customer	Admire Arts	10051	2022-09-20 14:09:16.587676+05:30	2022-09-20 14:09:16.587715+05:30	1	\N	\N	f
52	CUSTOMER	customer	Candor Corp	10052	2022-09-20 14:09:16.587949+05:30	2022-09-20 14:09:16.588073+05:30	1	\N	\N	f
53	CUSTOMER	customer	Clerby	10053	2022-09-20 14:09:16.588218+05:30	2022-09-20 14:09:16.588306+05:30	1	\N	\N	f
54	CUSTOMER	customer	Neoveo	10054	2022-09-20 14:09:16.58861+05:30	2022-09-20 14:09:16.588641+05:30	1	\N	\N	f
55	CUSTOMER	customer	Avu	10061	2022-09-20 14:09:16.588699+05:30	2022-09-20 14:09:16.588726+05:30	1	\N	\N	f
56	CUSTOMER	customer	Vertous	10062	2022-09-20 14:09:16.58878+05:30	2022-09-20 14:09:16.588818+05:30	1	\N	\N	f
57	CUSTOMER	customer	Portore	10063	2022-09-20 14:09:16.588884+05:30	2022-09-20 14:09:16.588912+05:30	1	\N	\N	f
58	CUSTOMER	customer	Med dot	10064	2022-09-20 14:09:16.588965+05:30	2022-09-20 14:09:16.588992+05:30	1	\N	\N	f
59	CUSTOMER	customer	Proweb	10071	2022-09-20 14:09:16.589045+05:30	2022-09-20 14:09:16.589072+05:30	1	\N	\N	f
60	CUSTOMER	customer	Focus Med	10072	2022-09-20 14:09:16.589127+05:30	2022-09-20 14:09:16.589154+05:30	1	\N	\N	f
61	CUSTOMER	customer	Global Manufacturing	10073	2022-09-20 14:09:16.589206+05:30	2022-09-20 14:09:16.589234+05:30	1	\N	\N	f
62	CUSTOMER	customer	Digital Bio	10074	2022-09-20 14:09:16.589287+05:30	2022-09-20 14:09:16.589313+05:30	1	\N	\N	f
63	CUSTOMER	customer	new customer	10075	2022-09-20 14:09:16.595177+05:30	2022-09-20 14:09:16.595221+05:30	1	\N	\N	f
64	CUSTOMER	customer	Entity 100	10100	2022-09-20 14:09:16.595287+05:30	2022-09-20 14:09:16.595464+05:30	1	\N	\N	f
65	CUSTOMER	customer	Entity 200	10200	2022-09-20 14:09:16.595539+05:30	2022-09-20 14:09:16.595568+05:30	1	\N	\N	f
66	CUSTOMER	customer	Entity 300	10300	2022-09-20 14:09:16.595624+05:30	2022-09-20 14:09:16.595652+05:30	1	\N	\N	f
67	CUSTOMER	customer	Entity 400	10400	2022-09-20 14:09:16.595707+05:30	2022-09-20 14:09:16.595736+05:30	1	\N	\N	f
68	CUSTOMER	customer	Entity 500	10500	2022-09-20 14:09:16.595791+05:30	2022-09-20 14:09:16.595818+05:30	1	\N	\N	f
69	CUSTOMER	customer	Entity 600	10600	2022-09-20 14:09:16.595872+05:30	2022-09-20 14:09:16.5959+05:30	1	\N	\N	f
70	CUSTOMER	customer	Entity 700	10700	2022-09-20 14:09:16.595955+05:30	2022-09-20 14:09:16.595982+05:30	1	\N	\N	f
71	CUSTOMER	customer	Corley Energy	11001	2022-09-20 14:09:16.596036+05:30	2022-09-20 14:09:16.596064+05:30	1	\N	\N	f
72	CUSTOMER	customer	National Clean Energy	11002	2022-09-20 14:09:16.596117+05:30	2022-09-20 14:09:16.596145+05:30	1	\N	\N	f
73	CUSTOMER	customer	Porter Technologies	11003	2022-09-20 14:09:16.596199+05:30	2022-09-20 14:09:16.596227+05:30	1	\N	\N	f
74	CUSTOMER	customer	Powell Clean Tech	11004	2022-09-20 14:09:16.59628+05:30	2022-09-20 14:09:16.596308+05:30	1	\N	\N	f
75	CUSTOMER	customer	Vaillante	11005	2022-09-20 14:09:16.596372+05:30	2022-09-20 14:09:16.596512+05:30	1	\N	\N	f
76	CUSTOMER	customer	Vapid Battery	11006	2022-09-20 14:09:16.596578+05:30	2022-09-20 14:09:16.596606+05:30	1	\N	\N	f
77	CUSTOMER	customer	Acme	11007	2022-09-20 14:09:16.59666+05:30	2022-09-20 14:09:16.596687+05:30	1	\N	\N	f
78	CUSTOMER	customer	ARCAM Corporation	11008	2022-09-20 14:09:16.596741+05:30	2022-09-20 14:09:16.596768+05:30	1	\N	\N	f
79	CUSTOMER	customer	Biffco	11009	2022-09-20 14:09:16.596821+05:30	2022-09-20 14:09:16.596849+05:30	1	\N	\N	f
80	CUSTOMER	customer	Binford	11010	2022-09-20 14:09:16.596902+05:30	2022-09-20 14:09:16.596929+05:30	1	\N	\N	f
81	CUSTOMER	customer	Blue Sun Corporation	11011	2022-09-20 14:09:16.596982+05:30	2022-09-20 14:09:16.59701+05:30	1	\N	\N	f
82	CUSTOMER	customer	Buynlarge Corporation	11012	2022-09-20 14:09:16.597063+05:30	2022-09-20 14:09:16.59709+05:30	1	\N	\N	f
83	CUSTOMER	customer	Gadgetron	11013	2022-09-20 14:09:16.597143+05:30	2022-09-20 14:09:16.597182+05:30	1	\N	\N	f
84	CUSTOMER	customer	Itex	11014	2022-09-20 14:09:16.597238+05:30	2022-09-20 14:09:16.597267+05:30	1	\N	\N	f
85	CUSTOMER	customer	Matsumura Fishworks	11015	2022-09-20 14:09:16.597324+05:30	2022-09-20 14:09:16.597353+05:30	1	\N	\N	f
86	CUSTOMER	customer	Omni Consumer Products	11016	2022-09-20 14:09:16.597522+05:30	2022-09-20 14:09:16.597553+05:30	1	\N	\N	f
87	CUSTOMER	customer	Upton-Webber	11017	2022-09-20 14:09:16.597617+05:30	2022-09-20 14:09:16.597645+05:30	1	\N	\N	f
88	CUSTOMER	customer	Grand Trunk Semaphore	11018	2022-09-20 14:09:16.597698+05:30	2022-09-20 14:09:16.597725+05:30	1	\N	\N	f
89	CUSTOMER	customer	Ace Tomato	11019	2022-09-20 14:09:16.597778+05:30	2022-09-20 14:09:16.597806+05:30	1	\N	\N	f
90	CUSTOMER	customer	Primatech Paper	11020	2022-09-20 14:09:16.597859+05:30	2022-09-20 14:09:16.597886+05:30	1	\N	\N	f
91	CUSTOMER	customer	Universal Exports	11021	2022-09-20 14:09:16.597939+05:30	2022-09-20 14:09:16.597966+05:30	1	\N	\N	f
92	CUSTOMER	customer	Duff	11022	2022-09-20 14:09:16.598019+05:30	2022-09-20 14:09:16.598046+05:30	1	\N	\N	f
93	CUSTOMER	customer	Sunshine Desserts	11023	2022-09-20 14:09:16.598099+05:30	2022-09-20 14:09:16.598126+05:30	1	\N	\N	f
94	CUSTOMER	customer	Paper Street Soap Co.	11024	2022-09-20 14:09:16.598179+05:30	2022-09-20 14:09:16.598206+05:30	1	\N	\N	f
95	CUSTOMER	customer	Dunder Mifflin	11025	2022-09-20 14:09:16.598259+05:30	2022-09-20 14:09:16.598286+05:30	1	\N	\N	f
96	CUSTOMER	customer	Wernham Hogg	11026	2022-09-20 14:09:16.59835+05:30	2022-09-20 14:09:16.598493+05:30	1	\N	\N	f
97	CUSTOMER	customer	United Liberty Paper	11027	2022-09-20 14:09:16.598559+05:30	2022-09-20 14:09:16.598587+05:30	1	\N	\N	f
98	CUSTOMER	customer	Union Aerospace Corporation	11028	2022-09-20 14:09:16.598642+05:30	2022-09-20 14:09:16.59867+05:30	1	\N	\N	f
99	CUSTOMER	customer	Abstergo Industries	11029	2022-09-20 14:09:16.598723+05:30	2022-09-20 14:09:16.59875+05:30	1	\N	\N	f
100	CUSTOMER	customer	Conglomerated Amalgamated	11030	2022-09-20 14:09:16.598803+05:30	2022-09-20 14:09:16.59883+05:30	1	\N	\N	f
101	CUSTOMER	customer	CHOAM	11031	2022-09-20 14:09:16.598882+05:30	2022-09-20 14:09:16.59892+05:30	1	\N	\N	f
102	CUSTOMER	customer	Cyberdyne Systems	11032	2022-09-20 14:09:16.598977+05:30	2022-09-20 14:09:16.599006+05:30	1	\N	\N	f
103	CUSTOMER	customer	Digivation Industries	11033	2022-09-20 14:09:16.599062+05:30	2022-09-20 14:09:16.599102+05:30	1	\N	\N	f
104	CUSTOMER	customer	Hishii Industries	11034	2022-09-20 14:09:16.599155+05:30	2022-09-20 14:09:16.599182+05:30	1	\N	\N	f
105	CUSTOMER	customer	Nordyne Defense	11035	2022-09-20 14:09:16.599235+05:30	2022-09-20 14:09:16.599262+05:30	1	\N	\N	f
106	CUSTOMER	customer	Ewing Oil	11036	2022-09-20 14:09:16.599315+05:30	2022-09-20 14:09:16.599342+05:30	1	\N	\N	f
107	CUSTOMER	customer	Strickland Propane	11037	2022-09-20 14:09:16.599511+05:30	2022-09-20 14:09:16.599541+05:30	1	\N	\N	f
108	CUSTOMER	customer	Benthic Petroleum	11038	2022-09-20 14:09:16.59959+05:30	2022-09-20 14:09:16.599611+05:30	1	\N	\N	f
109	CUSTOMER	customer	Liandri Mining	11039	2022-09-20 14:09:16.599659+05:30	2022-09-20 14:09:16.599679+05:30	1	\N	\N	f
110	CUSTOMER	customer	ENCOM	11040	2022-09-20 14:09:16.599734+05:30	2022-09-20 14:09:16.599753+05:30	1	\N	\N	f
111	CUSTOMER	customer	Nakatomi Corporation	11041	2022-09-20 14:09:16.599791+05:30	2022-09-20 14:09:16.599811+05:30	1	\N	\N	f
112	CUSTOMER	customer	Weyland-Yutani	11042	2022-09-20 14:09:16.599868+05:30	2022-09-20 14:09:16.599897+05:30	1	\N	\N	f
113	CUSTOMER	customer	Bluth Company	11043	2022-09-20 14:09:16.61139+05:30	2022-09-20 14:09:16.611433+05:30	1	\N	\N	f
114	CUSTOMER	customer	Devlin MacGregor	11044	2022-09-20 14:09:16.611493+05:30	2022-09-20 14:09:16.611523+05:30	1	\N	\N	f
115	CUSTOMER	customer	Dharma Initiative	11045	2022-09-20 14:09:16.611581+05:30	2022-09-20 14:09:16.61161+05:30	1	\N	\N	f
116	CUSTOMER	customer	Ecumena	11046	2022-09-20 14:09:16.611667+05:30	2022-09-20 14:09:16.611697+05:30	1	\N	\N	f
117	CUSTOMER	customer	Hanso Foundation	11047	2022-09-20 14:09:16.611754+05:30	2022-09-20 14:09:16.611784+05:30	1	\N	\N	f
118	CUSTOMER	customer	InGen	11048	2022-09-20 14:09:16.611844+05:30	2022-09-20 14:09:16.611874+05:30	1	\N	\N	f
119	CUSTOMER	customer	Khumalo	11049	2022-09-20 14:09:16.611934+05:30	2022-09-20 14:09:16.611965+05:30	1	\N	\N	f
120	CUSTOMER	customer	Medical Mechanica	11050	2022-09-20 14:09:16.612046+05:30	2022-09-20 14:09:16.612077+05:30	1	\N	\N	f
121	CUSTOMER	customer	N.E.R.D.	11051	2022-09-20 14:09:16.612134+05:30	2022-09-20 14:09:16.612164+05:30	1	\N	\N	f
122	CUSTOMER	customer	North Central Positronics	11052	2022-09-20 14:09:16.61222+05:30	2022-09-20 14:09:16.61225+05:30	1	\N	\N	f
123	CUSTOMER	customer	Prescott Pharmaceuticals	11053	2022-09-20 14:09:16.612306+05:30	2022-09-20 14:09:16.612335+05:30	1	\N	\N	f
124	CUSTOMER	customer	Tricell	11054	2022-09-20 14:09:16.612391+05:30	2022-09-20 14:09:16.612421+05:30	1	\N	\N	f
125	CUSTOMER	customer	Umbrella Corporation	11055	2022-09-20 14:09:16.612478+05:30	2022-09-20 14:09:16.612508+05:30	1	\N	\N	f
126	CUSTOMER	customer	VersaLife Corporation	11056	2022-09-20 14:09:16.612565+05:30	2022-09-20 14:09:16.612595+05:30	1	\N	\N	f
127	CUSTOMER	customer	Optican	11057	2022-09-20 14:09:16.612651+05:30	2022-09-20 14:09:16.61268+05:30	1	\N	\N	f
128	CUSTOMER	customer	Rossum Corporation	11058	2022-09-20 14:09:16.612736+05:30	2022-09-20 14:09:16.612765+05:30	1	\N	\N	f
129	CUSTOMER	customer	Simeon	11059	2022-09-20 14:09:16.612821+05:30	2022-09-20 14:09:16.61285+05:30	1	\N	\N	f
130	CUSTOMER	customer	Ziodex Industries	11060	2022-09-20 14:09:16.612906+05:30	2022-09-20 14:09:16.612935+05:30	1	\N	\N	f
131	CUSTOMER	customer	Metacortex	11061	2022-09-20 14:09:16.612991+05:30	2022-09-20 14:09:16.61302+05:30	1	\N	\N	f
132	CUSTOMER	customer	Delos	11062	2022-09-20 14:09:16.613076+05:30	2022-09-20 14:09:16.613105+05:30	1	\N	\N	f
133	CUSTOMER	customer	Deon International	11063	2022-09-20 14:09:16.613162+05:30	2022-09-20 14:09:16.613191+05:30	1	\N	\N	f
134	CUSTOMER	customer	Edgars	11064	2022-09-20 14:09:16.61327+05:30	2022-09-20 14:09:16.613301+05:30	1	\N	\N	f
135	CUSTOMER	customer	Global Dynamics	11065	2022-09-20 14:09:16.613362+05:30	2022-09-20 14:09:16.613374+05:30	1	\N	\N	f
136	CUSTOMER	customer	LexCorp	11066	2022-09-20 14:09:16.613421+05:30	2022-09-20 14:09:16.61345+05:30	1	\N	\N	f
137	CUSTOMER	customer	Mishima Zaibatsu	11067	2022-09-20 14:09:16.613701+05:30	2022-09-20 14:09:16.613758+05:30	1	\N	\N	f
138	CUSTOMER	customer	OsCorp	11068	2022-09-20 14:09:16.61399+05:30	2022-09-20 14:09:16.61404+05:30	1	\N	\N	f
139	CUSTOMER	customer	Universal Terraforming	11069	2022-09-20 14:09:16.614137+05:30	2022-09-20 14:09:16.61433+05:30	1	\N	\N	f
140	CUSTOMER	customer	Wayne Enterprises	11070	2022-09-20 14:09:16.614431+05:30	2022-09-20 14:09:16.614473+05:30	1	\N	\N	f
141	CUSTOMER	customer	McCandless Communications	11071	2022-09-20 14:09:16.614569+05:30	2022-09-20 14:09:16.614611+05:30	1	\N	\N	f
142	CUSTOMER	customer	Parrish Communications	11072	2022-09-20 14:09:16.614703+05:30	2022-09-20 14:09:16.614743+05:30	1	\N	\N	f
143	CUSTOMER	customer	Network23	11073	2022-09-20 14:09:16.614829+05:30	2022-09-20 14:09:16.61487+05:30	1	\N	\N	f
144	CUSTOMER	customer	Astromech	11074	2022-09-20 14:09:16.614955+05:30	2022-09-20 14:09:16.614994+05:30	1	\N	\N	f
145	CUSTOMER	customer	Capsule	11075	2022-09-20 14:09:16.615077+05:30	2022-09-20 14:09:16.615117+05:30	1	\N	\N	f
146	CUSTOMER	customer	Tyrell Corp.	11076	2022-09-20 14:09:16.6152+05:30	2022-09-20 14:09:16.615239+05:30	1	\N	\N	f
147	CUSTOMER	customer	United Robotronics	11077	2022-09-20 14:09:16.615303+05:30	2022-09-20 14:09:16.615332+05:30	1	\N	\N	f
148	CUSTOMER	customer	NorthAm Robotics	11078	2022-09-20 14:09:16.615389+05:30	2022-09-20 14:09:16.615418+05:30	1	\N	\N	f
149	CUSTOMER	customer	Serrano Genomics	11079	2022-09-20 14:09:16.615475+05:30	2022-09-20 14:09:16.615504+05:30	1	\N	\N	f
150	CUSTOMER	customer	Ajax	11080	2022-09-20 14:09:16.615561+05:30	2022-09-20 14:09:16.61559+05:30	1	\N	\N	f
151	CUSTOMER	customer	Cym Labs	11081	2022-09-20 14:09:16.615646+05:30	2022-09-20 14:09:16.615675+05:30	1	\N	\N	f
152	CUSTOMER	customer	Ovi	11082	2022-09-20 14:09:16.61573+05:30	2022-09-20 14:09:16.615759+05:30	1	\N	\N	f
153	CUSTOMER	customer	Aperture Science	11083	2022-09-20 14:09:16.615816+05:30	2022-09-20 14:09:16.615845+05:30	1	\N	\N	f
154	CUSTOMER	customer	DataDyne	11084	2022-09-20 14:09:16.615901+05:30	2022-09-20 14:09:16.61593+05:30	1	\N	\N	f
155	CUSTOMER	customer	Dynatechnics	11085	2022-09-20 14:09:16.615985+05:30	2022-09-20 14:09:16.616014+05:30	1	\N	\N	f
156	CUSTOMER	customer	Izon	11086	2022-09-20 14:09:16.616071+05:30	2022-09-20 14:09:16.6161+05:30	1	\N	\N	f
157	CUSTOMER	customer	Seburo	11087	2022-09-20 14:09:16.616156+05:30	2022-09-20 14:09:16.616185+05:30	1	\N	\N	f
158	CUSTOMER	customer	Stark Industries	11088	2022-09-20 14:09:16.616242+05:30	2022-09-20 14:09:16.616271+05:30	1	\N	\N	f
159	CUSTOMER	customer	X-Com	11089	2022-09-20 14:09:16.616328+05:30	2022-09-20 14:09:16.616357+05:30	1	\N	\N	f
160	CUSTOMER	customer	Cathedral Software	11090	2022-09-20 14:09:16.616415+05:30	2022-09-20 14:09:16.616445+05:30	1	\N	\N	f
161	CUSTOMER	customer	ComTron	11091	2022-09-20 14:09:16.616501+05:30	2022-09-20 14:09:16.61653+05:30	1	\N	\N	f
162	CUSTOMER	customer	Uplink	11092	2022-09-20 14:09:16.616586+05:30	2022-09-20 14:09:16.616615+05:30	1	\N	\N	f
163	CUSTOMER	customer	Globochem	11093	2022-09-20 14:09:16.649016+05:30	2022-09-20 14:09:16.649065+05:30	1	\N	\N	f
164	CUSTOMER	customer	Grayson Sky Domes	11094	2022-09-20 14:09:16.649139+05:30	2022-09-20 14:09:16.649171+05:30	1	\N	\N	f
165	CUSTOMER	customer	Monsters, Inc.	11095	2022-09-20 14:09:16.649239+05:30	2022-09-20 14:09:16.649503+05:30	1	\N	\N	f
166	CUSTOMER	customer	Stay Puft	11096	2022-09-20 14:09:16.649605+05:30	2022-09-20 14:09:16.649637+05:30	1	\N	\N	f
167	CUSTOMER	customer	Soylent Corporation	11097	2022-09-20 14:09:16.649702+05:30	2022-09-20 14:09:16.649731+05:30	1	\N	\N	f
168	CUSTOMER	customer	Allied British Plastics	11098	2022-09-20 14:09:16.649793+05:30	2022-09-20 14:09:16.649822+05:30	1	\N	\N	f
169	CUSTOMER	customer	Vandelay Industries	11099	2022-09-20 14:09:16.64988+05:30	2022-09-20 14:09:16.649909+05:30	1	\N	\N	f
170	CUSTOMER	customer	The android's Dungeon	11100	2022-09-20 14:09:16.649965+05:30	2022-09-20 14:09:16.649994+05:30	1	\N	\N	f
171	CUSTOMER	customer	Kwik-E-Mart	11101	2022-09-20 14:09:16.65005+05:30	2022-09-20 14:09:16.650079+05:30	1	\N	\N	f
172	CUSTOMER	customer	Mega Lo Mart	11102	2022-09-20 14:09:16.650136+05:30	2022-09-20 14:09:16.650165+05:30	1	\N	\N	f
173	CUSTOMER	customer	Zimms	11103	2022-09-20 14:09:16.650221+05:30	2022-09-20 14:09:16.65025+05:30	1	\N	\N	f
174	CUSTOMER	customer	Treadstone	11104	2022-09-20 14:09:16.650306+05:30	2022-09-20 14:09:16.650335+05:30	1	\N	\N	f
175	CUSTOMER	customer	Interplanetary Expeditions	11105	2022-09-20 14:09:16.650656+05:30	2022-09-20 14:09:16.65069+05:30	1	\N	\N	f
176	CUSTOMER	customer	Trade Federation	11106	2022-09-20 14:09:16.650751+05:30	2022-09-20 14:09:16.65078+05:30	1	\N	\N	f
177	CUSTOMER	customer	Veridian Dynamics	11107	2022-09-20 14:09:16.650839+05:30	2022-09-20 14:09:16.650869+05:30	1	\N	\N	f
178	CUSTOMER	customer	Yoyodyne Propulsion	11108	2022-09-20 14:09:16.650927+05:30	2022-09-20 14:09:16.650956+05:30	1	\N	\N	f
179	CUSTOMER	customer	IPS	11109	2022-09-20 14:09:16.651014+05:30	2022-09-20 14:09:16.651043+05:30	1	\N	\N	f
180	CUSTOMER	customer	Fuji Air	11110	2022-09-20 14:09:16.6511+05:30	2022-09-20 14:09:16.651129+05:30	1	\N	\N	f
181	CUSTOMER	customer	Ajira Airways	11111	2022-09-20 14:09:16.651186+05:30	2022-09-20 14:09:16.651215+05:30	1	\N	\N	f
182	CUSTOMER	customer	Roxxon	11112	2022-09-20 14:09:16.651273+05:30	2022-09-20 14:09:16.651302+05:30	1	\N	\N	f
183	CUSTOMER	customer	Shinra Electric	11113	2022-09-20 14:09:16.651631+05:30	2022-09-20 14:09:16.651744+05:30	1	\N	\N	f
184	CUSTOMER	customer	TriOptimum	11114	2022-09-20 14:09:16.651996+05:30	2022-09-20 14:09:16.652098+05:30	1	\N	\N	f
185	CUSTOMER	customer	TetraCorp	11115	2022-09-20 14:09:16.653406+05:30	2022-09-20 14:09:16.654714+05:30	1	\N	\N	f
186	CUSTOMER	customer	Ultor	11116	2022-09-20 14:09:16.654879+05:30	2022-09-20 14:09:16.654917+05:30	1	\N	\N	f
187	CUSTOMER	customer	U-North	11117	2022-09-20 14:09:16.654991+05:30	2022-09-20 14:09:16.655023+05:30	1	\N	\N	f
188	CUSTOMER	customer	Intelligent Audit	11118	2022-09-20 14:09:16.655089+05:30	2022-09-20 14:09:16.655119+05:30	1	\N	\N	f
189	CUSTOMER	customer	Been Verified	11119	2022-09-20 14:09:16.655181+05:30	2022-09-20 14:09:16.655211+05:30	1	\N	\N	f
190	CUSTOMER	customer	Sailthru	11120	2022-09-20 14:09:16.655503+05:30	2022-09-20 14:09:16.655545+05:30	1	\N	\N	f
191	CUSTOMER	customer	YellowHammer	11121	2022-09-20 14:09:16.655621+05:30	2022-09-20 14:09:16.655652+05:30	1	\N	\N	f
192	CUSTOMER	customer	Conductor	11122	2022-09-20 14:09:16.655716+05:30	2022-09-20 14:09:16.655745+05:30	1	\N	\N	f
193	CUSTOMER	customer	Cinium Financial Services	11123	2022-09-20 14:09:16.655807+05:30	2022-09-20 14:09:16.655836+05:30	1	\N	\N	f
194	CUSTOMER	customer	33Across	11124	2022-09-20 14:09:16.655896+05:30	2022-09-20 14:09:16.655925+05:30	1	\N	\N	f
195	CUSTOMER	customer	Live With Intention	11125	2022-09-20 14:09:16.655984+05:30	2022-09-20 14:09:16.656014+05:30	1	\N	\N	f
196	CUSTOMER	customer	Quantum Networks	11126	2022-09-20 14:09:16.656071+05:30	2022-09-20 14:09:16.656101+05:30	1	\N	\N	f
197	CUSTOMER	customer	Renegade Furniture Group	11127	2022-09-20 14:09:16.656158+05:30	2022-09-20 14:09:16.657675+05:30	1	\N	\N	f
198	CUSTOMER	customer	Gilead Sciences	11128	2022-09-20 14:09:16.657872+05:30	2022-09-20 14:09:16.657918+05:30	1	\N	\N	f
199	CUSTOMER	customer	Cymer	11129	2022-09-20 14:09:16.657999+05:30	2022-09-20 14:09:16.658118+05:30	1	\N	\N	f
200	CUSTOMER	customer	BuddyTV	11130	2022-09-20 14:09:16.658203+05:30	2022-09-20 14:09:16.658231+05:30	1	\N	\N	f
201	CUSTOMER	customer	The HCI Group	11131	2022-09-20 14:09:16.658285+05:30	2022-09-20 14:09:16.658325+05:30	1	\N	\N	f
202	CUSTOMER	customer	KENTECH Consulting	11132	2022-09-20 14:09:16.658513+05:30	2022-09-20 14:09:16.658541+05:30	1	\N	\N	f
203	CUSTOMER	customer	Column Five	11133	2022-09-20 14:09:16.658594+05:30	2022-09-20 14:09:16.658622+05:30	1	\N	\N	f
204	CUSTOMER	customer	GSATi	11134	2022-09-20 14:09:16.658674+05:30	2022-09-20 14:09:16.658702+05:30	1	\N	\N	f
205	CUSTOMER	customer	ThinkLite	11135	2022-09-20 14:09:16.658755+05:30	2022-09-20 14:09:16.658782+05:30	1	\N	\N	f
206	CUSTOMER	customer	Bottle Rocket Apps	11136	2022-09-20 14:09:16.658835+05:30	2022-09-20 14:09:16.658863+05:30	1	\N	\N	f
207	CUSTOMER	customer	Dhaliwal Labs	11137	2022-09-20 14:09:16.658916+05:30	2022-09-20 14:09:16.658944+05:30	1	\N	\N	f
208	CUSTOMER	customer	Brant, Agron, Meiselman	11138	2022-09-20 14:09:16.658997+05:30	2022-09-20 14:09:16.659025+05:30	1	\N	\N	f
209	CUSTOMER	customer	Insurance Megacorp	11139	2022-09-20 14:09:16.659077+05:30	2022-09-20 14:09:16.659105+05:30	1	\N	\N	f
210	CUSTOMER	customer	Bledsoe Cathcart Diestel and Pedersen LLP	11140	2022-09-20 14:09:16.659158+05:30	2022-09-20 14:09:16.659186+05:30	1	\N	\N	f
211	CUSTOMER	customer	Cuna Mutual Insurance Society	11141	2022-09-20 14:09:16.659239+05:30	2022-09-20 14:09:16.659266+05:30	1	\N	\N	f
212	CUSTOMER	customer	Augusta Medical Associates	11142	2022-09-20 14:09:16.659541+05:30	2022-09-20 14:09:16.65957+05:30	1	\N	\N	f
213	CUSTOMER	customer	Cardiovascular Disease Special	11143	2022-09-20 14:09:16.676865+05:30	2022-09-20 14:09:16.676919+05:30	1	\N	\N	f
214	CUSTOMER	customer	Pediatric Subspecialty Faculty	11144	2022-09-20 14:09:16.676992+05:30	2022-09-20 14:09:16.677016+05:30	1	\N	\N	f
215	CUSTOMER	customer	Mensa, Ltd.	11145	2022-09-20 14:09:16.677072+05:30	2022-09-20 14:09:16.677106+05:30	1	\N	\N	f
216	CUSTOMER	customer	South Bay Medical Center	11146	2022-09-20 14:09:16.677613+05:30	2022-09-20 14:09:16.677645+05:30	1	\N	\N	f
217	CUSTOMER	customer	United Methodist Communications	11147	2022-09-20 14:09:16.677695+05:30	2022-09-20 14:09:16.677748+05:30	1	\N	\N	f
218	CUSTOMER	customer	Oakland County Community Mental Health	11148	2022-09-20 14:09:16.677898+05:30	2022-09-20 14:09:16.677928+05:30	1	\N	\N	f
219	CUSTOMER	customer	Arkansas Blue Cross and Blue Shield	11149	2022-09-20 14:09:16.677973+05:30	2022-09-20 14:09:16.677986+05:30	1	\N	\N	f
220	CUSTOMER	customer	Piggly Wiggly Carolina Co.	11150	2022-09-20 14:09:16.678032+05:30	2022-09-20 14:09:16.678177+05:30	1	\N	\N	f
221	CUSTOMER	customer	Woodlands Medical Group	11151	2022-09-20 14:09:16.67823+05:30	2022-09-20 14:09:16.678251+05:30	1	\N	\N	f
222	CUSTOMER	customer	Arbitration Association	11152	2022-09-20 14:09:16.678309+05:30	2022-09-20 14:09:16.678338+05:30	1	\N	\N	f
223	CUSTOMER	customer	Talcomp Management Services	11153	2022-09-20 14:09:16.678785+05:30	2022-09-20 14:09:16.678807+05:30	1	\N	\N	f
224	CUSTOMER	customer	Denticare Of Oklahoma	11154	2022-09-20 14:09:16.678862+05:30	2022-09-20 14:09:16.678896+05:30	1	\N	\N	f
225	CUSTOMER	customer	Gulf States Paper Corporation	11155	2022-09-20 14:09:16.67899+05:30	2022-09-20 14:09:16.679016+05:30	1	\N	\N	f
226	CUSTOMER	customer	Oncolytics Biotech Inc.	11156	2022-09-20 14:09:16.679066+05:30	2022-09-20 14:09:16.679099+05:30	1	\N	\N	f
227	CUSTOMER	customer	Pacificare Health Systems Az	11157	2022-09-20 14:09:16.679153+05:30	2022-09-20 14:09:16.679174+05:30	1	\N	\N	f
228	CUSTOMER	customer	Southern Orthopedics	11158	2022-09-20 14:09:16.679344+05:30	2022-09-20 14:09:16.679434+05:30	1	\N	\N	f
229	CUSTOMER	customer	News Day	11159	2022-09-20 14:09:16.679517+05:30	2022-09-20 14:09:16.679548+05:30	1	\N	\N	f
230	CUSTOMER	customer	Quallaby Corporation	11160	2022-09-20 14:09:16.679599+05:30	2022-09-20 14:09:16.67962+05:30	1	\N	\N	f
231	CUSTOMER	customer	Computer Sciences Corporation	11161	2022-09-20 14:09:16.679703+05:30	2022-09-20 14:09:16.679794+05:30	1	\N	\N	f
232	CUSTOMER	customer	Premier Inc	11162	2022-09-20 14:09:16.679845+05:30	2022-09-20 14:09:16.679877+05:30	1	\N	\N	f
233	CUSTOMER	customer	Innova Solutions	11163	2022-09-20 14:09:16.679935+05:30	2022-09-20 14:09:16.67997+05:30	1	\N	\N	f
234	CUSTOMER	customer	Medical Research Technologies	11164	2022-09-20 14:09:16.680013+05:30	2022-09-20 14:09:16.680102+05:30	1	\N	\N	f
235	CUSTOMER	customer	Spine Rehab Center	11165	2022-09-20 14:09:16.680168+05:30	2022-09-20 14:09:16.680302+05:30	1	\N	\N	f
236	CUSTOMER	customer	CGH Medical Center	11166	2022-09-20 14:09:16.680361+05:30	2022-09-20 14:09:16.680397+05:30	1	\N	\N	f
237	CUSTOMER	customer	Olin Corporation	11167	2022-09-20 14:09:16.680457+05:30	2022-09-20 14:09:16.680514+05:30	1	\N	\N	f
238	CUSTOMER	customer	Sempra Energy	11168	2022-09-20 14:09:16.680572+05:30	2022-09-20 14:09:16.68061+05:30	1	\N	\N	f
239	CUSTOMER	customer	PA Neurosurgery and Neuroscience	11169	2022-09-20 14:09:16.680692+05:30	2022-09-20 14:09:16.680899+05:30	1	\N	\N	f
240	CUSTOMER	customer	West Oak Capital Group Inc	11170	2022-09-20 14:09:16.680957+05:30	2022-09-20 14:09:16.680979+05:30	1	\N	\N	f
241	CUSTOMER	customer	Titanium Corporation Inc.	11171	2022-09-20 14:09:16.681034+05:30	2022-09-20 14:09:16.681053+05:30	1	\N	\N	f
242	CUSTOMER	customer	Creative Healthcare	11172	2022-09-20 14:09:16.681098+05:30	2022-09-20 14:09:16.681128+05:30	1	\N	\N	f
243	CUSTOMER	customer	Georgia Power Company	11173	2022-09-20 14:09:16.681182+05:30	2022-09-20 14:09:16.681319+05:30	1	\N	\N	f
244	CUSTOMER	customer	Atlanta Integrative Medicine	11174	2022-09-20 14:09:16.681377+05:30	2022-09-20 14:09:16.681404+05:30	1	\N	\N	f
245	CUSTOMER	customer	Heart and Vascular Clinic	11175	2022-09-20 14:09:16.681504+05:30	2022-09-20 14:09:16.68153+05:30	1	\N	\N	f
246	CUSTOMER	customer	Compass Investment Partners	11176	2022-09-20 14:09:16.681579+05:30	2022-09-20 14:09:16.681608+05:30	1	\N	\N	f
247	CUSTOMER	customer	CDC Ixis North America Inc.	11177	2022-09-20 14:09:16.682389+05:30	2022-09-20 14:09:16.682427+05:30	1	\N	\N	f
248	CUSTOMER	customer	James Mintz Group, Inc.	11178	2022-09-20 14:09:16.68249+05:30	2022-09-20 14:09:16.682521+05:30	1	\N	\N	f
249	CUSTOMER	customer	Stoxnetwork Corporation	11179	2022-09-20 14:09:16.68258+05:30	2022-09-20 14:09:16.682603+05:30	1	\N	\N	f
250	CUSTOMER	customer	Kansas City Power and Light Co.	11180	2022-09-20 14:09:16.682666+05:30	2022-09-20 14:09:16.682689+05:30	1	\N	\N	f
251	CUSTOMER	customer	Bella Technologies	11181	2022-09-20 14:09:16.682752+05:30	2022-09-20 14:09:16.682772+05:30	1	\N	\N	f
252	CUSTOMER	customer	Naples Pediatrics	11182	2022-09-20 14:09:16.682814+05:30	2022-09-20 14:09:16.682843+05:30	1	\N	\N	f
253	CUSTOMER	customer	Intrepid Minerals Corporation	11183	2022-09-20 14:09:16.682909+05:30	2022-09-20 14:09:16.682932+05:30	1	\N	\N	f
254	CUSTOMER	customer	Wauwatosa Medical Group	11184	2022-09-20 14:09:16.682996+05:30	2022-09-20 14:09:16.683019+05:30	1	\N	\N	f
255	CUSTOMER	customer	Carolina Health Centers, Inc.	11185	2022-09-20 14:09:16.683331+05:30	2022-09-20 14:09:16.683386+05:30	1	\N	\N	f
256	CUSTOMER	customer	Chevron Texaco	11186	2022-09-20 14:09:16.683457+05:30	2022-09-20 14:09:16.683512+05:30	1	\N	\N	f
257	CUSTOMER	customer	Orchard Group	11187	2022-09-20 14:09:16.683878+05:30	2022-09-20 14:09:16.683938+05:30	1	\N	\N	f
258	CUSTOMER	customer	Copper Ab	11188	2022-09-20 14:09:16.684012+05:30	2022-09-20 14:09:16.684034+05:30	1	\N	\N	f
259	CUSTOMER	customer	The Vanguard Group, Inc.	11189	2022-09-20 14:09:16.684127+05:30	2022-09-20 14:09:16.684151+05:30	1	\N	\N	f
260	CUSTOMER	customer	Citizens Communications	11190	2022-09-20 14:09:16.6842+05:30	2022-09-20 14:09:16.684418+05:30	1	\N	\N	f
261	CUSTOMER	customer	Transnet	14001	2022-09-20 14:09:16.684477+05:30	2022-09-20 14:09:16.6845+05:30	1	\N	\N	f
262	CUSTOMER	customer	3Way International Logistics	14002	2022-09-20 14:09:16.684556+05:30	2022-09-20 14:09:16.684588+05:30	1	\N	\N	f
263	CUSTOMER	customer	Ache Records	14003	2022-09-20 14:09:16.726438+05:30	2022-09-20 14:09:16.726499+05:30	1	\N	\N	f
264	CUSTOMER	customer	Advanced Cyclotron Systems	14004	2022-09-20 14:09:16.726583+05:30	2022-09-20 14:09:16.726632+05:30	1	\N	\N	f
265	CUSTOMER	customer	Aldo Group	14005	2022-09-20 14:09:16.726709+05:30	2022-09-20 14:09:16.726744+05:30	1	\N	\N	f
266	CUSTOMER	customer	Algonquin Power and Utilities	14006	2022-09-20 14:09:16.726834+05:30	2022-09-20 14:09:16.727678+05:30	1	\N	\N	f
267	CUSTOMER	customer	Angoss	14007	2022-09-20 14:09:16.728438+05:30	2022-09-20 14:09:16.72851+05:30	1	\N	\N	f
268	CUSTOMER	customer	Appnovation	14008	2022-09-20 14:09:16.728598+05:30	2022-09-20 14:09:16.728622+05:30	1	\N	\N	f
269	CUSTOMER	customer	Army and Navy Stores	14009	2022-09-20 14:09:16.728695+05:30	2022-09-20 14:09:16.728727+05:30	1	\N	\N	f
270	CUSTOMER	customer	ATB Financial	14010	2022-09-20 14:09:16.728786+05:30	2022-09-20 14:09:16.728816+05:30	1	\N	\N	f
271	CUSTOMER	customer	Banff Lodging Co	14011	2022-09-20 14:09:16.728869+05:30	2022-09-20 14:09:16.72889+05:30	1	\N	\N	f
272	CUSTOMER	customer	Bard Ventures	14012	2022-09-20 14:09:16.728928+05:30	2022-09-20 14:09:16.728948+05:30	1	\N	\N	f
273	CUSTOMER	customer	BC Research	14013	2022-09-20 14:09:16.729058+05:30	2022-09-20 14:09:16.729104+05:30	1	\N	\N	f
274	CUSTOMER	customer	Bell Canada	14014	2022-09-20 14:09:16.729845+05:30	2022-09-20 14:09:16.729929+05:30	1	\N	\N	f
275	CUSTOMER	customer	Big Blue Bubble	14015	2022-09-20 14:09:16.730081+05:30	2022-09-20 14:09:16.730123+05:30	1	\N	\N	f
276	CUSTOMER	customer	Biovail	14016	2022-09-20 14:09:16.730391+05:30	2022-09-20 14:09:16.730444+05:30	1	\N	\N	f
277	CUSTOMER	customer	Black Hen Music	14017	2022-09-20 14:09:16.730517+05:30	2022-09-20 14:09:16.730746+05:30	1	\N	\N	f
278	CUSTOMER	customer	BlackBerry Limited	14018	2022-09-20 14:09:16.73083+05:30	2022-09-20 14:09:16.730857+05:30	1	\N	\N	f
279	CUSTOMER	customer	Blenz Coffee	14019	2022-09-20 14:09:16.730907+05:30	2022-09-20 14:09:16.730937+05:30	1	\N	\N	f
280	CUSTOMER	customer	Boeing Canada	14020	2022-09-20 14:09:16.731002+05:30	2022-09-20 14:09:16.73103+05:30	1	\N	\N	f
281	CUSTOMER	customer	Boston Pizza	14021	2022-09-20 14:09:16.731093+05:30	2022-09-20 14:09:16.731126+05:30	1	\N	\N	f
282	CUSTOMER	customer	Bowring Brothers	14022	2022-09-20 14:09:16.731788+05:30	2022-09-20 14:09:16.731829+05:30	1	\N	\N	f
283	CUSTOMER	customer	BrightSide Technologies	14023	2022-09-20 14:09:16.73189+05:30	2022-09-20 14:09:16.73192+05:30	1	\N	\N	f
284	CUSTOMER	customer	Bruce Power	14024	2022-09-20 14:09:16.731977+05:30	2022-09-20 14:09:16.732006+05:30	1	\N	\N	f
285	CUSTOMER	customer	Bullfrog Power	14025	2022-09-20 14:09:16.732062+05:30	2022-09-20 14:09:16.732092+05:30	1	\N	\N	f
286	CUSTOMER	customer	Cadillac Fairview	14026	2022-09-20 14:09:16.732148+05:30	2022-09-20 14:09:16.732178+05:30	1	\N	\N	f
287	CUSTOMER	customer	Canada Deposit Insurance Corporation	14027	2022-09-20 14:09:16.732381+05:30	2022-09-20 14:09:16.732422+05:30	1	\N	\N	f
288	CUSTOMER	customer	Canadian Bank Note Company	14028	2022-09-20 14:09:16.732495+05:30	2022-09-20 14:09:16.732534+05:30	1	\N	\N	f
289	CUSTOMER	customer	Canadian Light Source	14029	2022-09-20 14:09:16.732612+05:30	2022-09-20 14:09:16.732653+05:30	1	\N	\N	f
290	CUSTOMER	customer	Canadian Natural Resources	14030	2022-09-20 14:09:16.732741+05:30	2022-09-20 14:09:16.732773+05:30	1	\N	\N	f
291	CUSTOMER	customer	Canadian Steamship Lines	14031	2022-09-20 14:09:16.73283+05:30	2022-09-20 14:09:16.73286+05:30	1	\N	\N	f
292	CUSTOMER	customer	Canadian Tire Bank	14032	2022-09-20 14:09:16.732916+05:30	2022-09-20 14:09:16.732945+05:30	1	\N	\N	f
293	CUSTOMER	customer	Candente Copper	14033	2022-09-20 14:09:16.733+05:30	2022-09-20 14:09:16.73304+05:30	1	\N	\N	f
294	CUSTOMER	customer	CanJet	14034	2022-09-20 14:09:16.733122+05:30	2022-09-20 14:09:16.733163+05:30	1	\N	\N	f
295	CUSTOMER	customer	Capcom Vancouver	14035	2022-09-20 14:09:16.733364+05:30	2022-09-20 14:09:16.733397+05:30	1	\N	\N	f
296	CUSTOMER	customer	Casavant Frares	14036	2022-09-20 14:09:16.733456+05:30	2022-09-20 14:09:16.733485+05:30	1	\N	\N	f
297	CUSTOMER	customer	Cellcom Communications	14037	2022-09-20 14:09:16.733541+05:30	2022-09-20 14:09:16.733571+05:30	1	\N	\N	f
298	CUSTOMER	customer	Centra Gas Manitoba Inc.	14038	2022-09-20 14:09:16.733627+05:30	2022-09-20 14:09:16.733656+05:30	1	\N	\N	f
299	CUSTOMER	customer	Chapters	14039	2022-09-20 14:09:16.733712+05:30	2022-09-20 14:09:16.733741+05:30	1	\N	\N	f
300	CUSTOMER	customer	Choices Market	14040	2022-09-20 14:09:16.733798+05:30	2022-09-20 14:09:16.733838+05:30	1	\N	\N	f
301	CUSTOMER	customer	Cirque du Soleil	14041	2022-09-20 14:09:16.73391+05:30	2022-09-20 14:09:16.733945+05:30	1	\N	\N	f
302	CUSTOMER	customer	Coachman Insurance Company	14042	2022-09-20 14:09:16.734004+05:30	2022-09-20 14:09:16.734033+05:30	1	\N	\N	f
303	CUSTOMER	customer	Comm100	14043	2022-09-20 14:09:16.73409+05:30	2022-09-20 14:09:16.734119+05:30	1	\N	\N	f
304	CUSTOMER	customer	Conestoga-Rovers and Associates	14044	2022-09-20 14:09:16.734175+05:30	2022-09-20 14:09:16.734204+05:30	1	\N	\N	f
305	CUSTOMER	customer	Cordiant Capital Inc.	14045	2022-09-20 14:09:16.734259+05:30	2022-09-20 14:09:16.734288+05:30	1	\N	\N	f
306	CUSTOMER	customer	Corus Entertainment	14046	2022-09-20 14:09:16.734344+05:30	2022-09-20 14:09:16.734373+05:30	1	\N	\N	f
307	CUSTOMER	customer	Country Style	14047	2022-09-20 14:09:16.734545+05:30	2022-09-20 14:09:16.734576+05:30	1	\N	\N	f
308	CUSTOMER	customer	Crestline Coach	14048	2022-09-20 14:09:16.734625+05:30	2022-09-20 14:09:16.734646+05:30	1	\N	\N	f
309	CUSTOMER	customer	CTV Television Network	14049	2022-09-20 14:09:16.734703+05:30	2022-09-20 14:09:16.734749+05:30	1	\N	\N	f
310	CUSTOMER	customer	Cymax Stores	14050	2022-09-20 14:09:16.735675+05:30	2022-09-20 14:09:16.735735+05:30	1	\N	\N	f
311	CUSTOMER	customer	Dare Foods	14051	2022-09-20 14:09:16.738506+05:30	2022-09-20 14:09:16.738616+05:30	1	\N	\N	f
312	CUSTOMER	customer	Delta Hotels	14052	2022-09-20 14:09:16.738945+05:30	2022-09-20 14:09:16.739017+05:30	1	\N	\N	f
313	CUSTOMER	customer	Digital Extremes	14053	2022-09-20 14:09:16.755505+05:30	2022-09-20 14:09:16.755553+05:30	1	\N	\N	f
314	CUSTOMER	customer	Discovery Air Defence	14054	2022-09-20 14:09:16.755653+05:30	2022-09-20 14:09:16.755783+05:30	1	\N	\N	f
315	CUSTOMER	customer	Dominion Voting Systems	14055	2022-09-20 14:09:16.755916+05:30	2022-09-20 14:09:16.755963+05:30	1	\N	\N	f
316	CUSTOMER	customer	Donner Metals	14056	2022-09-20 14:09:16.756291+05:30	2022-09-20 14:09:16.756329+05:30	1	\N	\N	f
317	CUSTOMER	customer	Dynamsoft	14057	2022-09-20 14:09:16.756399+05:30	2022-09-20 14:09:16.756422+05:30	1	\N	\N	f
318	CUSTOMER	customer	EA Black Box	14058	2022-09-20 14:09:16.756805+05:30	2022-09-20 14:09:16.756846+05:30	1	\N	\N	f
319	CUSTOMER	customer	Electrohome	14059	2022-09-20 14:09:16.756918+05:30	2022-09-20 14:09:16.756954+05:30	1	\N	\N	f
320	CUSTOMER	customer	Emera	14060	2022-09-20 14:09:16.757661+05:30	2022-09-20 14:09:16.757873+05:30	1	\N	\N	f
321	CUSTOMER	customer	Enwave	14061	2022-09-20 14:09:16.758023+05:30	2022-09-20 14:09:16.75806+05:30	1	\N	\N	f
322	CUSTOMER	customer	FandP Manufacturing Inc.	14062	2022-09-20 14:09:16.758129+05:30	2022-09-20 14:09:16.75816+05:30	1	\N	\N	f
323	CUSTOMER	customer	Fairmont Hotels and Resorts	14063	2022-09-20 14:09:16.758222+05:30	2022-09-20 14:09:16.758252+05:30	1	\N	\N	f
324	CUSTOMER	customer	Farmers of North America	14064	2022-09-20 14:09:16.758313+05:30	2022-09-20 14:09:16.758343+05:30	1	\N	\N	f
325	CUSTOMER	customer	Fido Solutions	14065	2022-09-20 14:09:16.758402+05:30	2022-09-20 14:09:16.758431+05:30	1	\N	\N	f
326	CUSTOMER	customer	First Air	14066	2022-09-20 14:09:16.758489+05:30	2022-09-20 14:09:16.758518+05:30	1	\N	\N	f
327	CUSTOMER	customer	Flickr	14067	2022-09-20 14:09:16.758575+05:30	2022-09-20 14:09:16.758604+05:30	1	\N	\N	f
328	CUSTOMER	customer	Ford Motor Company of Canada	14068	2022-09-20 14:09:16.758661+05:30	2022-09-20 14:09:16.75869+05:30	1	\N	\N	f
329	CUSTOMER	customer	Four Seasons Hotels and Resorts	14069	2022-09-20 14:09:16.758747+05:30	2022-09-20 14:09:16.758776+05:30	1	\N	\N	f
330	CUSTOMER	customer	Freedom Mobile	14070	2022-09-20 14:09:16.758833+05:30	2022-09-20 14:09:16.758862+05:30	1	\N	\N	f
331	CUSTOMER	customer	Riffwire	15001	2022-09-20 14:09:16.758918+05:30	2022-09-20 14:09:16.758947+05:30	1	\N	\N	f
332	CUSTOMER	customer	Zoozzy	15002	2022-09-20 14:09:16.759003+05:30	2022-09-20 14:09:16.759032+05:30	1	\N	\N	f
333	CUSTOMER	customer	Linkbuzz	15003	2022-09-20 14:09:16.759166+05:30	2022-09-20 14:09:16.759642+05:30	1	\N	\N	f
334	CUSTOMER	customer	Brainlounge	15004	2022-09-20 14:09:16.759806+05:30	2022-09-20 14:09:16.759914+05:30	1	\N	\N	f
335	CUSTOMER	customer	Pixonyx	15005	2022-09-20 14:09:16.760043+05:30	2022-09-20 14:09:16.760769+05:30	1	\N	\N	f
336	CUSTOMER	customer	Bubblebox	15006	2022-09-20 14:09:16.761107+05:30	2022-09-20 14:09:16.761461+05:30	1	\N	\N	f
337	CUSTOMER	customer	Yodel	15007	2022-09-20 14:09:16.763119+05:30	2022-09-20 14:09:16.763608+05:30	1	\N	\N	f
338	CUSTOMER	customer	Trunyx	15008	2022-09-20 14:09:16.763818+05:30	2022-09-20 14:09:16.763887+05:30	1	\N	\N	f
339	CUSTOMER	customer	Aimbu	15009	2022-09-20 14:09:16.764021+05:30	2022-09-20 14:09:16.764074+05:30	1	\N	\N	f
340	CUSTOMER	customer	Yata	15010	2022-09-20 14:09:16.764203+05:30	2022-09-20 14:09:16.76437+05:30	1	\N	\N	f
341	CUSTOMER	customer	Voonix	15011	2022-09-20 14:09:16.764496+05:30	2022-09-20 14:09:16.764544+05:30	1	\N	\N	f
342	CUSTOMER	customer	Leexo	15012	2022-09-20 14:09:16.764653+05:30	2022-09-20 14:09:16.765674+05:30	1	\N	\N	f
343	CUSTOMER	customer	Bubblemix	15013	2022-09-20 14:09:16.765758+05:30	2022-09-20 14:09:16.765792+05:30	1	\N	\N	f
344	CUSTOMER	customer	Devbug	15014	2022-09-20 14:09:16.765856+05:30	2022-09-20 14:09:16.765879+05:30	1	\N	\N	f
345	CUSTOMER	customer	Jazzy	15015	2022-09-20 14:09:16.765943+05:30	2022-09-20 14:09:16.765972+05:30	1	\N	\N	f
346	CUSTOMER	customer	Voolith	15016	2022-09-20 14:09:16.766033+05:30	2022-09-20 14:09:16.766063+05:30	1	\N	\N	f
347	CUSTOMER	customer	Skinte	15017	2022-09-20 14:09:16.766123+05:30	2022-09-20 14:09:16.766152+05:30	1	\N	\N	f
348	CUSTOMER	customer	Izio	15018	2022-09-20 14:09:16.766211+05:30	2022-09-20 14:09:16.76624+05:30	1	\N	\N	f
349	CUSTOMER	customer	Trudeo	15019	2022-09-20 14:09:16.766299+05:30	2022-09-20 14:09:16.766328+05:30	1	\N	\N	f
350	CUSTOMER	customer	Jabberstorm	15020	2022-09-20 14:09:16.766386+05:30	2022-09-20 14:09:16.766415+05:30	1	\N	\N	f
351	CUSTOMER	customer	Topicstorm	15021	2022-09-20 14:09:16.766473+05:30	2022-09-20 14:09:16.766502+05:30	1	\N	\N	f
352	CUSTOMER	customer	Npath	15022	2022-09-20 14:09:16.766559+05:30	2022-09-20 14:09:16.766588+05:30	1	\N	\N	f
353	CUSTOMER	customer	Photojam	15023	2022-09-20 14:09:16.766645+05:30	2022-09-20 14:09:16.766674+05:30	1	\N	\N	f
354	CUSTOMER	customer	Twitterbeat	15024	2022-09-20 14:09:16.766731+05:30	2022-09-20 14:09:16.766761+05:30	1	\N	\N	f
355	CUSTOMER	customer	Feednation	15025	2022-09-20 14:09:16.766817+05:30	2022-09-20 14:09:16.766846+05:30	1	\N	\N	f
356	CUSTOMER	customer	Eadel	15026	2022-09-20 14:09:16.766904+05:30	2022-09-20 14:09:16.766933+05:30	1	\N	\N	f
357	CUSTOMER	customer	Zoombeat	15027	2022-09-20 14:09:16.766989+05:30	2022-09-20 14:09:16.767018+05:30	1	\N	\N	f
358	CUSTOMER	customer	Wikibox	15028	2022-09-20 14:09:16.767075+05:30	2022-09-20 14:09:16.767104+05:30	1	\N	\N	f
359	CUSTOMER	customer	Edgeblab	15029	2022-09-20 14:09:16.767161+05:30	2022-09-20 14:09:16.76719+05:30	1	\N	\N	f
360	CUSTOMER	customer	Kwilith	15030	2022-09-20 14:09:16.767247+05:30	2022-09-20 14:09:16.767276+05:30	1	\N	\N	f
361	CUSTOMER	customer	Feedspan	15031	2022-09-20 14:09:16.767333+05:30	2022-09-20 14:09:16.767362+05:30	1	\N	\N	f
362	CUSTOMER	customer	Flashdog	15032	2022-09-20 14:09:16.767418+05:30	2022-09-20 14:09:16.767447+05:30	1	\N	\N	f
363	CUSTOMER	customer	Myworks	15033	2022-09-20 14:09:16.803897+05:30	2022-09-20 14:09:16.803977+05:30	1	\N	\N	f
364	CUSTOMER	customer	Dynabox	15034	2022-09-20 14:09:16.804225+05:30	2022-09-20 14:09:16.804593+05:30	1	\N	\N	f
365	CUSTOMER	customer	Browsebug	15035	2022-09-20 14:09:16.807804+05:30	2022-09-20 14:09:16.808172+05:30	1	\N	\N	f
366	CUSTOMER	customer	Topiczoom	15036	2022-09-20 14:09:16.808769+05:30	2022-09-20 14:09:16.808811+05:30	1	\N	\N	f
367	CUSTOMER	customer	Yombu	15037	2022-09-20 14:09:16.808886+05:30	2022-09-20 14:09:16.808913+05:30	1	\N	\N	f
368	CUSTOMER	customer	Twitterbeat	15038	2022-09-20 14:09:16.80897+05:30	2022-09-20 14:09:16.809001+05:30	1	\N	\N	f
369	CUSTOMER	customer	Divavu	15039	2022-09-20 14:09:16.809062+05:30	2022-09-20 14:09:16.809092+05:30	1	\N	\N	f
370	CUSTOMER	customer	Quimm	15040	2022-09-20 14:09:16.809153+05:30	2022-09-20 14:09:16.809182+05:30	1	\N	\N	f
371	CUSTOMER	customer	Miboo	15041	2022-09-20 14:09:16.809242+05:30	2022-09-20 14:09:16.809271+05:30	1	\N	\N	f
372	CUSTOMER	customer	Feednation	15042	2022-09-20 14:09:16.80933+05:30	2022-09-20 14:09:16.809356+05:30	1	\N	\N	f
373	CUSTOMER	customer	Trilith	15043	2022-09-20 14:09:16.809405+05:30	2022-09-20 14:09:16.809435+05:30	1	\N	\N	f
374	CUSTOMER	customer	Photofeed	15044	2022-09-20 14:09:16.809493+05:30	2022-09-20 14:09:16.809522+05:30	1	\N	\N	f
375	CUSTOMER	customer	Avaveo	15045	2022-09-20 14:09:16.809579+05:30	2022-09-20 14:09:16.809608+05:30	1	\N	\N	f
376	CUSTOMER	customer	Bluejam	15046	2022-09-20 14:09:16.809666+05:30	2022-09-20 14:09:16.809695+05:30	1	\N	\N	f
377	CUSTOMER	customer	BlogXS	15047	2022-09-20 14:09:16.809753+05:30	2022-09-20 14:09:16.809782+05:30	1	\N	\N	f
378	CUSTOMER	customer	Thoughtworks	15048	2022-09-20 14:09:16.80984+05:30	2022-09-20 14:09:16.809869+05:30	1	\N	\N	f
379	CUSTOMER	customer	Aimbu	15049	2022-09-20 14:09:16.809927+05:30	2022-09-20 14:09:16.809948+05:30	1	\N	\N	f
380	CUSTOMER	customer	Livetube	15050	2022-09-20 14:09:16.809997+05:30	2022-09-20 14:09:16.81002+05:30	1	\N	\N	f
381	CUSTOMER	customer	Livefish	15051	2022-09-20 14:09:16.810069+05:30	2022-09-20 14:09:16.810099+05:30	1	\N	\N	f
382	CUSTOMER	customer	Skimia	15052	2022-09-20 14:09:16.810156+05:30	2022-09-20 14:09:16.810185+05:30	1	\N	\N	f
383	CUSTOMER	customer	Jabbertype	15053	2022-09-20 14:09:16.810242+05:30	2022-09-20 14:09:16.810285+05:30	1	\N	\N	f
384	CUSTOMER	customer	Feednation	15054	2022-09-20 14:09:16.810343+05:30	2022-09-20 14:09:16.810373+05:30	1	\N	\N	f
385	CUSTOMER	customer	Tanoodle	15055	2022-09-20 14:09:16.81043+05:30	2022-09-20 14:09:16.810459+05:30	1	\N	\N	f
386	CUSTOMER	customer	Dabtype	15056	2022-09-20 14:09:16.810516+05:30	2022-09-20 14:09:16.810545+05:30	1	\N	\N	f
387	CUSTOMER	customer	Mybuzz	15057	2022-09-20 14:09:16.810602+05:30	2022-09-20 14:09:16.810632+05:30	1	\N	\N	f
388	CUSTOMER	customer	Youbridge	15058	2022-09-20 14:09:16.810689+05:30	2022-09-20 14:09:16.810718+05:30	1	\N	\N	f
389	CUSTOMER	customer	Rhycero	15059	2022-09-20 14:09:16.810775+05:30	2022-09-20 14:09:16.810805+05:30	1	\N	\N	f
390	CUSTOMER	customer	Feednation	15060	2022-09-20 14:09:16.810862+05:30	2022-09-20 14:09:16.810891+05:30	1	\N	\N	f
391	CUSTOMER	customer	Dabtype	15061	2022-09-20 14:09:16.810948+05:30	2022-09-20 14:09:16.810978+05:30	1	\N	\N	f
392	CUSTOMER	customer	Jaxnation	15062	2022-09-20 14:09:16.811036+05:30	2022-09-20 14:09:16.811065+05:30	1	\N	\N	f
393	CUSTOMER	customer	Topicware	15063	2022-09-20 14:09:16.811122+05:30	2022-09-20 14:09:16.81115+05:30	1	\N	\N	f
394	CUSTOMER	customer	Voomm	15064	2022-09-20 14:09:16.811207+05:30	2022-09-20 14:09:16.811236+05:30	1	\N	\N	f
395	CUSTOMER	customer	Skivee	15065	2022-09-20 14:09:16.811293+05:30	2022-09-20 14:09:16.811322+05:30	1	\N	\N	f
396	CUSTOMER	customer	Topdrive	15066	2022-09-20 14:09:16.811378+05:30	2022-09-20 14:09:16.811407+05:30	1	\N	\N	f
397	CUSTOMER	customer	Dabvine	15067	2022-09-20 14:09:16.811464+05:30	2022-09-20 14:09:16.811494+05:30	1	\N	\N	f
398	CUSTOMER	customer	Thoughtstorm	15068	2022-09-20 14:09:16.81155+05:30	2022-09-20 14:09:16.81158+05:30	1	\N	\N	f
399	CUSTOMER	customer	Kazio	15069	2022-09-20 14:09:16.811637+05:30	2022-09-20 14:09:16.811666+05:30	1	\N	\N	f
400	CUSTOMER	customer	ABB Grain	16001	2022-09-20 14:09:16.811723+05:30	2022-09-20 14:09:16.811752+05:30	1	\N	\N	f
401	CUSTOMER	customer	ABC Learning	16002	2022-09-20 14:09:16.811808+05:30	2022-09-20 14:09:16.811838+05:30	1	\N	\N	f
402	CUSTOMER	customer	Adam Internet	16003	2022-09-20 14:09:16.826808+05:30	2022-09-20 14:09:16.826879+05:30	1	\N	\N	f
403	CUSTOMER	customer	Aerosonde Ltd	16004	2022-09-20 14:09:16.827006+05:30	2022-09-20 14:09:16.827042+05:30	1	\N	\N	f
404	CUSTOMER	customer	Alinta Gas	16005	2022-09-20 14:09:16.827134+05:30	2022-09-20 14:09:16.827176+05:30	1	\N	\N	f
405	CUSTOMER	customer	Allphones	16006	2022-09-20 14:09:16.827268+05:30	2022-09-20 14:09:16.827441+05:30	1	\N	\N	f
406	CUSTOMER	customer	Alumina	16007	2022-09-20 14:09:16.827528+05:30	2022-09-20 14:09:16.827569+05:30	1	\N	\N	f
407	CUSTOMER	customer	Amcor	16008	2022-09-20 14:09:16.827649+05:30	2022-09-20 14:09:16.827688+05:30	1	\N	\N	f
408	CUSTOMER	customer	ANCA	16009	2022-09-20 14:09:16.836776+05:30	2022-09-20 14:09:16.836824+05:30	1	\N	\N	f
409	CUSTOMER	customer	Angus and Robertson	16010	2022-09-20 14:09:16.836901+05:30	2022-09-20 14:09:16.836935+05:30	1	\N	\N	f
410	CUSTOMER	customer	Ansell	16011	2022-09-20 14:09:16.837006+05:30	2022-09-20 14:09:16.837038+05:30	1	\N	\N	f
411	CUSTOMER	customer	Appliances Online	16012	2022-09-20 14:09:16.837105+05:30	2022-09-20 14:09:16.837135+05:30	1	\N	\N	f
412	CUSTOMER	customer	Aristocrat Leisure	16013	2022-09-20 14:09:16.837192+05:30	2022-09-20 14:09:16.837221+05:30	1	\N	\N	f
413	CUSTOMER	customer	Arnott's Biscuits	16014	2022-09-20 14:09:16.851047+05:30	2022-09-20 14:09:16.851087+05:30	1	\N	\N	f
414	CUSTOMER	customer	Arrow Research Corporation	16015	2022-09-20 14:09:16.851158+05:30	2022-09-20 14:09:16.851179+05:30	1	\N	\N	f
415	CUSTOMER	customer	Atlassian	16016	2022-09-20 14:09:16.851249+05:30	2022-09-20 14:09:16.851269+05:30	1	\N	\N	f
416	CUSTOMER	customer	Aussie Broadband	16017	2022-09-20 14:09:16.85131+05:30	2022-09-20 14:09:16.851322+05:30	1	\N	\N	f
417	CUSTOMER	customer	Austal Ships	16018	2022-09-20 14:09:16.851363+05:30	2022-09-20 14:09:16.851384+05:30	1	\N	\N	f
418	CUSTOMER	customer	Austereo	16019	2022-09-20 14:09:16.851434+05:30	2022-09-20 14:09:16.851455+05:30	1	\N	\N	f
419	CUSTOMER	customer	Australia and New Zealand Banking Group (ANZ)	16020	2022-09-20 14:09:16.851506+05:30	2022-09-20 14:09:16.851528+05:30	1	\N	\N	f
420	CUSTOMER	customer	Australian Agricultural Company	16021	2022-09-20 14:09:16.851946+05:30	2022-09-20 14:09:16.855802+05:30	1	\N	\N	f
421	CUSTOMER	customer	Australian airExpress	16022	2022-09-20 14:09:16.855944+05:30	2022-09-20 14:09:16.85598+05:30	1	\N	\N	f
422	CUSTOMER	customer	Australian Broadcasting Corporation	16023	2022-09-20 14:09:16.856114+05:30	2022-09-20 14:09:16.856173+05:30	1	\N	\N	f
423	CUSTOMER	customer	Australian Defence Industries	16024	2022-09-20 14:09:16.856329+05:30	2022-09-20 14:09:16.856372+05:30	1	\N	\N	f
424	CUSTOMER	customer	Australian Gas Light Company	16025	2022-09-20 14:09:16.856435+05:30	2022-09-20 14:09:16.856457+05:30	1	\N	\N	f
425	CUSTOMER	customer	Australian Motor Industries (AMI)	16026	2022-09-20 14:09:16.856507+05:30	2022-09-20 14:09:16.856519+05:30	1	\N	\N	f
426	CUSTOMER	customer	Australian Railroad Group	16027	2022-09-20 14:09:16.856559+05:30	2022-09-20 14:09:16.856579+05:30	1	\N	\N	f
427	CUSTOMER	customer	Australian Securities Exchange	16028	2022-09-20 14:09:16.856632+05:30	2022-09-20 14:09:16.856652+05:30	1	\N	\N	f
428	CUSTOMER	customer	Ausway	16029	2022-09-20 14:09:16.856702+05:30	2022-09-20 14:09:16.856722+05:30	1	\N	\N	f
429	CUSTOMER	customer	AWB Limited	16030	2022-09-20 14:09:16.856763+05:30	2022-09-20 14:09:16.856774+05:30	1	\N	\N	f
430	CUSTOMER	customer	BAE Systems Australia	16031	2022-09-20 14:09:16.856816+05:30	2022-09-20 14:09:16.856836+05:30	1	\N	\N	f
431	CUSTOMER	customer	Bakers Delight	16032	2022-09-20 14:09:16.856888+05:30	2022-09-20 14:09:16.856907+05:30	1	\N	\N	f
432	CUSTOMER	customer	Beaurepaires	16033	2022-09-20 14:09:16.856947+05:30	2022-09-20 14:09:16.856958+05:30	1	\N	\N	f
433	CUSTOMER	customer	Becker Entertainment	16034	2022-09-20 14:09:16.856999+05:30	2022-09-20 14:09:16.85702+05:30	1	\N	\N	f
434	CUSTOMER	customer	Billabong	16035	2022-09-20 14:09:16.857071+05:30	2022-09-20 14:09:16.85709+05:30	1	\N	\N	f
435	CUSTOMER	customer	Bing Lee	16036	2022-09-20 14:09:16.85713+05:30	2022-09-20 14:09:16.857141+05:30	1	\N	\N	f
436	CUSTOMER	customer	BlueScope	16037	2022-09-20 14:09:16.857181+05:30	2022-09-20 14:09:16.857202+05:30	1	\N	\N	f
437	CUSTOMER	customer	Blundstone Footwear	16038	2022-09-20 14:09:16.857252+05:30	2022-09-20 14:09:16.857272+05:30	1	\N	\N	f
438	CUSTOMER	customer	Boost Juice Bars	16039	2022-09-20 14:09:16.857324+05:30	2022-09-20 14:09:16.857345+05:30	1	\N	\N	f
439	CUSTOMER	customer	Boral	16040	2022-09-20 14:09:16.857395+05:30	2022-09-20 14:09:16.857416+05:30	1	\N	\N	f
440	CUSTOMER	customer	Brown Brothers Milawa Vineyard	16041	2022-09-20 14:09:16.857467+05:30	2022-09-20 14:09:16.857488+05:30	1	\N	\N	f
441	CUSTOMER	customer	Bulla Dairy Foods	16042	2022-09-20 14:09:16.857539+05:30	2022-09-20 14:09:16.85755+05:30	1	\N	\N	f
442	CUSTOMER	customer	Burns Philp	16043	2022-09-20 14:09:16.857591+05:30	2022-09-20 14:09:16.857612+05:30	1	\N	\N	f
443	CUSTOMER	customer	Camperdown Dairy International	16044	2022-09-20 14:09:16.857661+05:30	2022-09-20 14:09:16.857672+05:30	1	\N	\N	f
444	CUSTOMER	customer	CBH Group	16045	2022-09-20 14:09:16.857713+05:30	2022-09-20 14:09:16.857733+05:30	1	\N	\N	f
445	CUSTOMER	customer	Cbus	16046	2022-09-20 14:09:16.857783+05:30	2022-09-20 14:09:16.857805+05:30	1	\N	\N	f
446	CUSTOMER	customer	CHEP	16047	2022-09-20 14:09:16.857855+05:30	2022-09-20 14:09:16.857876+05:30	1	\N	\N	f
447	CUSTOMER	customer	CIMIC Group	16048	2022-09-20 14:09:16.857926+05:30	2022-09-20 14:09:16.857947+05:30	1	\N	\N	f
448	CUSTOMER	customer	CMV Group	16049	2022-09-20 14:09:16.857997+05:30	2022-09-20 14:09:16.858007+05:30	1	\N	\N	f
449	CUSTOMER	customer	Coca-Cola Amatil	16050	2022-09-20 14:09:16.858049+05:30	2022-09-20 14:09:16.858069+05:30	1	\N	\N	f
450	CUSTOMER	customer	Coles Group	16051	2022-09-20 14:09:16.858121+05:30	2022-09-20 14:09:16.858132+05:30	1	\N	\N	f
451	CUSTOMER	customer	Commonwealth Bank	16052	2022-09-20 14:09:16.858172+05:30	2022-09-20 14:09:16.858192+05:30	1	\N	\N	f
452	CUSTOMER	customer	Compass Resources	16053	2022-09-20 14:09:16.858243+05:30	2022-09-20 14:09:16.858264+05:30	1	\N	\N	f
453	CUSTOMER	customer	Computershare	16054	2022-09-20 14:09:16.858316+05:30	2022-09-20 14:09:16.858337+05:30	1	\N	\N	f
454	CUSTOMER	customer	Cotton On	16055	2022-09-20 14:09:16.858386+05:30	2022-09-20 14:09:16.858407+05:30	1	\N	\N	f
455	CUSTOMER	customer	Country Energy	16056	2022-09-20 14:09:16.85846+05:30	2022-09-20 14:09:16.858481+05:30	1	\N	\N	f
456	CUSTOMER	customer	Crossecom	16057	2022-09-20 14:09:16.858537+05:30	2022-09-20 14:09:16.858567+05:30	1	\N	\N	f
457	CUSTOMER	customer	Crown Resorts	16058	2022-09-20 14:09:16.858623+05:30	2022-09-20 14:09:16.858647+05:30	1	\N	\N	f
458	CUSTOMER	customer	CSL Limited	16059	2022-09-20 14:09:16.858687+05:30	2022-09-20 14:09:16.858707+05:30	1	\N	\N	f
459	CUSTOMER	customer	CSR Limited	16060	2022-09-20 14:09:16.858764+05:30	2022-09-20 14:09:16.858793+05:30	1	\N	\N	f
460	CUSTOMER	customer	David Jones Limited	16061	2022-09-20 14:09:16.85885+05:30	2022-09-20 14:09:16.858869+05:30	1	\N	\N	f
461	CUSTOMER	customer	De Bortoli Wines	16062	2022-09-20 14:09:16.858918+05:30	2022-09-20 14:09:16.858945+05:30	1	\N	\N	f
462	CUSTOMER	customer	Delta Electricity	16063	2022-09-20 14:09:16.858992+05:30	2022-09-20 14:09:16.859022+05:30	1	\N	\N	f
463	CUSTOMER	customer	Dick Smith Electronics	16064	2022-09-20 14:09:16.884802+05:30	2022-09-20 14:09:16.884855+05:30	1	\N	\N	f
464	CUSTOMER	customer	Dorf Clark Industries	16065	2022-09-20 14:09:16.884933+05:30	2022-09-20 14:09:16.884967+05:30	1	\N	\N	f
465	CUSTOMER	customer	Downer Group	16066	2022-09-20 14:09:16.888374+05:30	2022-09-20 14:09:16.888418+05:30	1	\N	\N	f
466	CUSTOMER	customer	Dymocks Booksellers	16067	2022-09-20 14:09:16.888488+05:30	2022-09-20 14:09:16.888517+05:30	1	\N	\N	f
467	CUSTOMER	customer	Eagle Boys	16068	2022-09-20 14:09:16.888649+05:30	2022-09-20 14:09:16.888763+05:30	1	\N	\N	f
468	CUSTOMER	customer	Elders Limited	16069	2022-09-20 14:09:16.888952+05:30	2022-09-20 14:09:16.888988+05:30	1	\N	\N	f
469	CUSTOMER	customer	Elfin Cars	16070	2022-09-20 14:09:16.889383+05:30	2022-09-20 14:09:16.88942+05:30	1	\N	\N	f
470	CUSTOMER	customer	Adcock Ingram	17001	2022-09-20 14:09:16.889482+05:30	2022-09-20 14:09:16.889511+05:30	1	\N	\N	f
471	CUSTOMER	customer	Afrihost	17002	2022-09-20 14:09:16.889559+05:30	2022-09-20 14:09:16.889572+05:30	1	\N	\N	f
472	CUSTOMER	customer	ACSA	17003	2022-09-20 14:09:16.889613+05:30	2022-09-20 14:09:16.889625+05:30	1	\N	\N	f
473	CUSTOMER	customer	Anglo American	17004	2022-09-20 14:09:16.88967+05:30	2022-09-20 14:09:16.889696+05:30	1	\N	\N	f
474	CUSTOMER	customer	Anglo American Platinum	17005	2022-09-20 14:09:16.88988+05:30	2022-09-20 14:09:16.889913+05:30	1	\N	\N	f
475	CUSTOMER	customer	Aspen Pharmacare	17006	2022-09-20 14:09:16.890119+05:30	2022-09-20 14:09:16.890159+05:30	1	\N	\N	f
476	CUSTOMER	customer	Automobile Association of South Africa	17007	2022-09-20 14:09:16.890228+05:30	2022-09-20 14:09:16.890252+05:30	1	\N	\N	f
477	CUSTOMER	customer	ABSA Group	17008	2022-09-20 14:09:16.890297+05:30	2022-09-20 14:09:16.890319+05:30	1	\N	\N	f
478	CUSTOMER	customer	Business Connexion Group	17009	2022-09-20 14:09:16.890886+05:30	2022-09-20 14:09:16.890928+05:30	1	\N	\N	f
479	CUSTOMER	customer	Capitec Bank	17010	2022-09-20 14:09:16.891041+05:30	2022-09-20 14:09:16.891064+05:30	1	\N	\N	f
480	CUSTOMER	customer	Cell C	17011	2022-09-20 14:09:16.891114+05:30	2022-09-20 14:09:16.891135+05:30	1	\N	\N	f
481	CUSTOMER	customer	Checkers	17012	2022-09-20 14:09:16.891184+05:30	2022-09-20 14:09:16.891216+05:30	1	\N	\N	f
482	CUSTOMER	customer	De Beers	17013	2022-09-20 14:09:16.891632+05:30	2022-09-20 14:09:16.891667+05:30	1	\N	\N	f
483	CUSTOMER	customer	Defy Appliances	17014	2022-09-20 14:09:16.891726+05:30	2022-09-20 14:09:16.891746+05:30	1	\N	\N	f
484	CUSTOMER	customer	De Haan's Bus and Coach	17015	2022-09-20 14:09:16.891794+05:30	2022-09-20 14:09:16.891819+05:30	1	\N	\N	f
485	CUSTOMER	customer	Dimension Data	17016	2022-09-20 14:09:16.891867+05:30	2022-09-20 14:09:16.891897+05:30	1	\N	\N	f
486	CUSTOMER	customer	e.tv	17017	2022-09-20 14:09:16.892083+05:30	2022-09-20 14:09:16.892117+05:30	1	\N	\N	f
487	CUSTOMER	customer	Eskom	17018	2022-09-20 14:09:16.892167+05:30	2022-09-20 14:09:16.892189+05:30	1	\N	\N	f
488	CUSTOMER	customer	Exxaro	17019	2022-09-20 14:09:16.892475+05:30	2022-09-20 14:09:16.892525+05:30	1	\N	\N	f
489	CUSTOMER	customer	Food Lover's Market	17020	2022-09-20 14:09:16.892591+05:30	2022-09-20 14:09:16.892622+05:30	1	\N	\N	f
490	CUSTOMER	customer	First National Bank	17021	2022-09-20 14:09:16.893014+05:30	2022-09-20 14:09:16.893052+05:30	1	\N	\N	f
491	CUSTOMER	customer	First Rand	17022	2022-09-20 14:09:16.900738+05:30	2022-09-20 14:09:16.90078+05:30	1	\N	\N	f
492	CUSTOMER	customer	FNB Connect	17023	2022-09-20 14:09:16.900881+05:30	2022-09-20 14:09:16.901+05:30	1	\N	\N	f
493	CUSTOMER	customer	Gallo Record Company	17024	2022-09-20 14:09:16.901053+05:30	2022-09-20 14:09:16.901083+05:30	1	\N	\N	f
494	CUSTOMER	customer	Gijima Group	17025	2022-09-20 14:09:16.901132+05:30	2022-09-20 14:09:16.901162+05:30	1	\N	\N	f
495	CUSTOMER	customer	Gold Fields	17026	2022-09-20 14:09:16.903613+05:30	2022-09-20 14:09:16.903714+05:30	1	\N	\N	f
496	CUSTOMER	customer	Golden Arrow Bus Services	17027	2022-09-20 14:09:16.903819+05:30	2022-09-20 14:09:16.903847+05:30	1	\N	\N	f
497	CUSTOMER	customer	Harmony Gold	17028	2022-09-20 14:09:16.904059+05:30	2022-09-20 14:09:16.906924+05:30	1	\N	\N	f
498	CUSTOMER	customer	Hollard Group	17029	2022-09-20 14:09:16.907043+05:30	2022-09-20 14:09:16.907066+05:30	1	\N	\N	f
499	CUSTOMER	customer	Illovo Sugar	17030	2022-09-20 14:09:16.90712+05:30	2022-09-20 14:09:16.907151+05:30	1	\N	\N	f
500	CUSTOMER	customer	Impala Platinum	17031	2022-09-20 14:09:16.910215+05:30	2022-09-20 14:09:16.910304+05:30	1	\N	\N	f
501	CUSTOMER	customer	Junk Mail Digital Media	17032	2022-09-20 14:09:16.912248+05:30	2022-09-20 14:09:16.912309+05:30	1	\N	\N	f
502	CUSTOMER	customer	Kumba Iron Ore	17033	2022-09-20 14:09:16.912769+05:30	2022-09-20 14:09:16.912818+05:30	1	\N	\N	f
503	CUSTOMER	customer	Investec	17034	2022-09-20 14:09:16.912887+05:30	2022-09-20 14:09:16.912912+05:30	1	\N	\N	f
504	CUSTOMER	customer	LIFE Healthcare Group	17035	2022-09-20 14:09:16.913722+05:30	2022-09-20 14:09:16.913767+05:30	1	\N	\N	f
505	CUSTOMER	customer	Mathews and Associates Architects	17036	2022-09-20 14:09:16.913855+05:30	2022-09-20 14:09:16.913877+05:30	1	\N	\N	f
506	CUSTOMER	customer	Mediclinic International	17037	2022-09-20 14:09:16.91394+05:30	2022-09-20 14:09:16.913965+05:30	1	\N	\N	f
507	CUSTOMER	customer	M-Net	17038	2022-09-20 14:09:16.914594+05:30	2022-09-20 14:09:16.914628+05:30	1	\N	\N	f
508	CUSTOMER	customer	Mr. Price Group Ltd.	17039	2022-09-20 14:09:16.914686+05:30	2022-09-20 14:09:16.914719+05:30	1	\N	\N	f
509	CUSTOMER	customer	MTN Group	17040	2022-09-20 14:09:16.916233+05:30	2022-09-20 14:09:16.916281+05:30	1	\N	\N	f
510	CUSTOMER	customer	MultiChoice	17041	2022-09-20 14:09:16.916353+05:30	2022-09-20 14:09:16.916378+05:30	1	\N	\N	f
511	CUSTOMER	customer	MWEB	17042	2022-09-20 14:09:16.917845+05:30	2022-09-20 14:09:16.918238+05:30	1	\N	\N	f
512	CUSTOMER	customer	Naspers	17043	2022-09-20 14:09:16.922395+05:30	2022-09-20 14:09:16.934138+05:30	1	\N	\N	f
513	CUSTOMER	customer	Nedbank	17044	2022-09-20 14:09:17.003534+05:30	2022-09-20 14:09:17.003599+05:30	1	\N	\N	f
514	CUSTOMER	customer	Neotel	17045	2022-09-20 14:09:17.003691+05:30	2022-09-20 14:09:17.003728+05:30	1	\N	\N	f
515	CUSTOMER	customer	Netcare	17046	2022-09-20 14:09:17.004393+05:30	2022-09-20 14:09:17.004442+05:30	1	\N	\N	f
516	CUSTOMER	customer	Old Mutual	17047	2022-09-20 14:09:17.004512+05:30	2022-09-20 14:09:17.004545+05:30	1	\N	\N	f
517	CUSTOMER	customer	Pick 'n Pay	17048	2022-09-20 14:09:17.004645+05:30	2022-09-20 14:09:17.004705+05:30	1	\N	\N	f
518	CUSTOMER	customer	Pioneer Foods	17049	2022-09-20 14:09:17.00482+05:30	2022-09-20 14:09:17.004878+05:30	1	\N	\N	f
519	CUSTOMER	customer	PPC Ltd.	17050	2022-09-20 14:09:17.005003+05:30	2022-09-20 14:09:17.005041+05:30	1	\N	\N	f
520	CUSTOMER	customer	Premier FMCG	17051	2022-09-20 14:09:17.005109+05:30	2022-09-20 14:09:17.005139+05:30	1	\N	\N	f
521	CUSTOMER	customer	Primedia	17052	2022-09-20 14:09:17.005201+05:30	2022-09-20 14:09:17.005231+05:30	1	\N	\N	f
522	CUSTOMER	customer	Primedia Broadcasting	17053	2022-09-20 14:09:17.005294+05:30	2022-09-20 14:09:17.005322+05:30	1	\N	\N	f
523	CUSTOMER	customer	PUTCO	17054	2022-09-20 14:09:17.008055+05:30	2022-09-20 14:09:17.008336+05:30	1	\N	\N	f
524	CUSTOMER	customer	RCL Foods	17055	2022-09-20 14:09:17.008563+05:30	2022-09-20 14:09:17.008625+05:30	1	\N	\N	f
525	CUSTOMER	customer	Riovic	17056	2022-09-20 14:09:17.008755+05:30	2022-09-20 14:09:17.008816+05:30	1	\N	\N	f
526	CUSTOMER	customer	Rovos Rail	17057	2022-09-20 14:09:17.008928+05:30	2022-09-20 14:09:17.008972+05:30	1	\N	\N	f
527	CUSTOMER	customer	South African Broadcasting Corporation	17058	2022-09-20 14:09:17.009073+05:30	2022-09-20 14:09:17.009116+05:30	1	\N	\N	f
528	CUSTOMER	customer	Sanlam	17059	2022-09-20 14:09:17.009211+05:30	2022-09-20 14:09:17.009253+05:30	1	\N	\N	f
529	CUSTOMER	customer	Sasol	17060	2022-09-20 14:09:17.009346+05:30	2022-09-20 14:09:17.009388+05:30	1	\N	\N	f
530	CUSTOMER	customer	Shoprite	17061	2022-09-20 14:09:17.009481+05:30	2022-09-20 14:09:17.009522+05:30	1	\N	\N	f
531	CUSTOMER	customer	South African Breweries	17062	2022-09-20 14:09:17.009616+05:30	2022-09-20 14:09:17.009658+05:30	1	\N	\N	f
532	CUSTOMER	customer	Standard Bank	17063	2022-09-20 14:09:17.009748+05:30	2022-09-20 14:09:17.00979+05:30	1	\N	\N	f
533	CUSTOMER	customer	StarSat, South Africa	17064	2022-09-20 14:09:17.009889+05:30	2022-09-20 14:09:17.009933+05:30	1	\N	\N	f
534	CUSTOMER	customer	Telkom	17065	2022-09-20 14:09:17.010298+05:30	2022-09-20 14:09:17.010501+05:30	1	\N	\N	f
535	CUSTOMER	customer	Telkom Mobile	17066	2022-09-20 14:09:17.010923+05:30	2022-09-20 14:09:17.010961+05:30	1	\N	\N	f
536	CUSTOMER	customer	Tiger Brands	17067	2022-09-20 14:09:17.011031+05:30	2022-09-20 14:09:17.011063+05:30	1	\N	\N	f
537	CUSTOMER	customer	Times Media Group	17068	2022-09-20 14:09:17.011126+05:30	2022-09-20 14:09:17.011149+05:30	1	\N	\N	f
538	CUSTOMER	customer	Tongaat Hulett	17069	2022-09-20 14:09:17.011202+05:30	2022-09-20 14:09:17.011224+05:30	1	\N	\N	f
539	DEPARTMENT	department	Admin	300	2022-09-20 14:09:22.956173+05:30	2022-09-20 14:09:22.956223+05:30	1	\N	\N	f
540	DEPARTMENT	department	Services	200	2022-09-20 14:09:22.956293+05:30	2022-09-20 14:09:22.95685+05:30	1	\N	\N	f
541	DEPARTMENT	department	Sales	100	2022-09-20 14:09:22.957032+05:30	2022-09-20 14:09:22.957059+05:30	1	\N	\N	f
542	DEPARTMENT	department	IT	500	2022-09-20 14:09:22.957108+05:30	2022-09-20 14:09:22.957124+05:30	1	\N	\N	f
543	DEPARTMENT	department	Marketing	400	2022-09-20 14:09:22.957166+05:30	2022-09-20 14:09:22.957179+05:30	1	\N	\N	f
544	TAX_DETAIL	Tax Detail	UK Import Services Zero Rate	UK Import Services Zero Rate	2022-09-20 14:09:27.787535+05:30	2022-09-20 14:09:27.787614+05:30	1	t	{"tax_rate": 0.0, "tax_solution_id": "United Kingdom - VAT"}	f
545	TAX_DETAIL	Tax Detail	UK Purchase Goods Exempt Rate	UK Purchase Goods Exempt Rate	2022-09-20 14:09:27.787775+05:30	2022-09-20 14:09:27.787815+05:30	1	t	{"tax_rate": 0.0, "tax_solution_id": "United Kingdom - VAT"}	f
546	TAX_DETAIL	Tax Detail	UK Purchase Goods Reduced Rate	UK Purchase Goods Reduced Rate	2022-09-20 14:09:27.787908+05:30	2022-09-20 14:09:27.787939+05:30	1	t	{"tax_rate": 5.0, "tax_solution_id": "United Kingdom - VAT"}	f
547	TAX_DETAIL	Tax Detail	UK Purchase Goods Standard Rate	UK Purchase Goods Standard Rate	2022-09-20 14:09:27.788018+05:30	2022-09-20 14:09:27.788048+05:30	1	t	{"tax_rate": 20.0, "tax_solution_id": "United Kingdom - VAT"}	f
548	TAX_DETAIL	Tax Detail	UK Purchase Goods Zero Rate	UK Purchase Goods Zero Rate	2022-09-20 14:09:27.788121+05:30	2022-09-20 14:09:27.788151+05:30	1	t	{"tax_rate": 0.0, "tax_solution_id": "United Kingdom - VAT"}	f
549	TAX_DETAIL	Tax Detail	UK Purchase in Reverse Charge Box 6 Exempt UK	UK Purchase in Reverse Charge Box 6 Exempt UK	2022-09-20 14:09:27.788223+05:30	2022-09-20 14:09:27.788253+05:30	1	t	{"tax_rate": 0.0, "tax_solution_id": "United Kingdom - VAT"}	f
550	TAX_DETAIL	Tax Detail	UK Purchase in Reverse Charge Box 6 Reduced Rate UK Input	UK Purchase in Reverse Charge Box 6 Reduced Rate UK Input	2022-09-20 14:09:27.788323+05:30	2022-09-20 14:09:27.788352+05:30	1	t	{"tax_rate": 5.0, "tax_solution_id": "United Kingdom - VAT"}	f
551	TAX_DETAIL	Tax Detail	UK Purchase in Reverse Charge Box 6 Standard Rate UK Input	UK Purchase in Reverse Charge Box 6 Standard Rate UK Input	2022-09-20 14:09:27.788561+05:30	2022-09-20 14:09:27.788594+05:30	1	t	{"tax_rate": 20.0, "tax_solution_id": "United Kingdom - VAT"}	f
552	TAX_DETAIL	Tax Detail	UK Purchase in Reverse Charge Box 6 Zero Rate UK	UK Purchase in Reverse Charge Box 6 Zero Rate UK	2022-09-20 14:09:27.788665+05:30	2022-09-20 14:09:27.788706+05:30	1	t	{"tax_rate": 0.0, "tax_solution_id": "United Kingdom - VAT"}	f
553	TAX_DETAIL	Tax Detail	UK Purchase Reverse Charge Reduced Rate Input	UK Purchase Reverse Charge Reduced Rate Input	2022-09-20 14:09:27.788817+05:30	2022-09-20 14:09:27.78886+05:30	1	t	{"tax_rate": 5.0, "tax_solution_id": "United Kingdom - VAT"}	f
554	TAX_DETAIL	Tax Detail	UK Purchase Reverse Charge Standard Rate Input	UK Purchase Reverse Charge Standard Rate Input	2022-09-20 14:09:27.788978+05:30	2022-09-20 14:09:27.789016+05:30	1	t	{"tax_rate": 20.0, "tax_solution_id": "United Kingdom - VAT"}	f
555	TAX_DETAIL	Tax Detail	UK Purchase Services Exempt Rate	UK Purchase Services Exempt Rate	2022-09-20 14:09:27.78909+05:30	2022-09-20 14:09:27.789119+05:30	1	t	{"tax_rate": 0.0, "tax_solution_id": "United Kingdom - VAT"}	f
556	TAX_DETAIL	Tax Detail	UK Purchase Services Reduced Rate	UK Purchase Services Reduced Rate	2022-09-20 14:09:27.789191+05:30	2022-09-20 14:09:27.789221+05:30	1	t	{"tax_rate": 5.0, "tax_solution_id": "United Kingdom - VAT"}	f
557	TAX_DETAIL	Tax Detail	UK Purchase Services Standard Rate	UK Purchase Services Standard Rate	2022-09-20 14:09:27.789309+05:30	2022-09-20 14:09:27.789503+05:30	1	t	{"tax_rate": 20.0, "tax_solution_id": "United Kingdom - VAT"}	f
558	TAX_DETAIL	Tax Detail	UK Purchase Services Zero Rate	UK Purchase Services Zero Rate	2022-09-20 14:09:27.789629+05:30	2022-09-20 14:09:27.789663+05:30	1	t	{"tax_rate": 0.0, "tax_solution_id": "United Kingdom - VAT"}	f
559	TAX_DETAIL	Tax Detail	EC Purchase Goods Exempt Rate	EC Purchase Goods Exempt Rate	2022-09-20 14:09:27.789739+05:30	2022-09-20 14:09:27.789769+05:30	1	t	{"tax_rate": 0.0, "tax_solution_id": "United Kingdom - VAT"}	f
560	TAX_DETAIL	Tax Detail	EC Purchase Goods Reduced Rate Input	EC Purchase Goods Reduced Rate Input	2022-09-20 14:09:27.789844+05:30	2022-09-20 14:09:27.789874+05:30	1	t	{"tax_rate": 5.0, "tax_solution_id": "United Kingdom - VAT"}	f
561	TAX_DETAIL	Tax Detail	EC Purchase Goods Standard Rate Input	EC Purchase Goods Standard Rate Input	2022-09-20 14:09:27.789946+05:30	2022-09-20 14:09:27.789976+05:30	1	t	{"tax_rate": 20.0, "tax_solution_id": "United Kingdom - VAT"}	f
562	TAX_DETAIL	Tax Detail	EC Purchase Goods Zero Rate	EC Purchase Goods Zero Rate	2022-09-20 14:09:27.790047+05:30	2022-09-20 14:09:27.790078+05:30	1	t	{"tax_rate": 0.0, "tax_solution_id": "United Kingdom - VAT"}	f
563	TAX_DETAIL	Tax Detail	EC Purchase Services Exempt Rate	EC Purchase Services Exempt Rate	2022-09-20 14:09:27.790187+05:30	2022-09-20 14:09:27.790379+05:30	1	t	{"tax_rate": 0.0, "tax_solution_id": "United Kingdom - VAT"}	f
564	TAX_DETAIL	Tax Detail	EC Purchase Services Reduced Rate Input	EC Purchase Services Reduced Rate Input	2022-09-20 14:09:27.790632+05:30	2022-09-20 14:09:27.790674+05:30	1	t	{"tax_rate": 5.0, "tax_solution_id": "United Kingdom - VAT"}	f
565	TAX_DETAIL	Tax Detail	EC Purchase Services Standard Rate Input	EC Purchase Services Standard Rate Input	2022-09-20 14:09:27.790758+05:30	2022-09-20 14:09:27.790788+05:30	1	t	{"tax_rate": 20.0, "tax_solution_id": "United Kingdom - VAT"}	f
566	TAX_DETAIL	Tax Detail	EC Purchase Services Zero Rate	EC Purchase Services Zero Rate	2022-09-20 14:09:27.790864+05:30	2022-09-20 14:09:27.790894+05:30	1	t	{"tax_rate": 0.0, "tax_solution_id": "United Kingdom - VAT"}	f
567	TAX_DETAIL	Tax Detail	UK Import Goods Exempt Rate	UK Import Goods Exempt Rate	2022-09-20 14:09:27.790967+05:30	2022-09-20 14:09:27.790997+05:30	1	t	{"tax_rate": 0.0, "tax_solution_id": "United Kingdom - VAT"}	f
568	TAX_DETAIL	Tax Detail	UK Import Goods Reduced Rate	UK Import Goods Reduced Rate	2022-09-20 14:09:27.79107+05:30	2022-09-20 14:09:27.7911+05:30	1	t	{"tax_rate": 5.0, "tax_solution_id": "United Kingdom - VAT"}	f
569	TAX_DETAIL	Tax Detail	UK Import Goods Standard Rate	UK Import Goods Standard Rate	2022-09-20 14:09:27.791197+05:30	2022-09-20 14:09:27.791243+05:30	1	t	{"tax_rate": 20.0, "tax_solution_id": "United Kingdom - VAT"}	f
570	TAX_DETAIL	Tax Detail	UK Import Goods Zero Rate	UK Import Goods Zero Rate	2022-09-20 14:09:27.791506+05:30	2022-09-20 14:09:27.791538+05:30	1	t	{"tax_rate": 0.0, "tax_solution_id": "United Kingdom - VAT"}	f
571	TAX_DETAIL	Tax Detail	UK Import Services Exempt Rate	UK Import Services Exempt Rate	2022-09-20 14:09:27.791612+05:30	2022-09-20 14:09:27.791642+05:30	1	t	{"tax_rate": 0.0, "tax_solution_id": "United Kingdom - VAT"}	f
572	TAX_DETAIL	Tax Detail	UK Import Services Reduced Rate	UK Import Services Reduced Rate	2022-09-20 14:09:27.791714+05:30	2022-09-20 14:09:27.791751+05:30	1	t	{"tax_rate": 5.0, "tax_solution_id": "United Kingdom - VAT"}	f
573	TAX_DETAIL	Tax Detail	UK Import Services Standard Rate	UK Import Services Standard Rate	2022-09-20 14:09:27.791866+05:30	2022-09-20 14:09:27.79191+05:30	1	t	{"tax_rate": 20.0, "tax_solution_id": "United Kingdom - VAT"}	f
574	TAX_DETAIL	Tax Detail	G18 Input Tax Credit Adjustment	G18 Input Tax Credit Adjustment	2022-09-20 14:09:27.792025+05:30	2022-09-20 14:09:27.792067+05:30	1	t	{"tax_rate": 0.0, "tax_solution_id": "Australia - GST"}	f
575	TAX_DETAIL	Tax Detail	G13 Capital Purchases for Input Tax Sales	G13 Capital Purchases for Input Tax Sales	2022-09-20 14:09:27.792179+05:30	2022-09-20 14:09:27.792222+05:30	1	t	{"tax_rate": 10.0, "tax_solution_id": "Australia - GST"}	f
576	TAX_DETAIL	Tax Detail	G13 GST Free Capital Purchases for Input Tax Sales	G13 GST Free Capital Purchases for Input Tax Sales	2022-09-20 14:09:27.792359+05:30	2022-09-20 14:09:27.792556+05:30	1	t	{"tax_rate": 0.0, "tax_solution_id": "Australia - GST"}	f
577	TAX_DETAIL	Tax Detail	G15 Capital Purchases for Private Use	G15 Capital Purchases for Private Use	2022-09-20 14:09:27.792689+05:30	2022-09-20 14:09:27.792734+05:30	1	t	{"tax_rate": 10.0, "tax_solution_id": "Australia - GST"}	f
578	TAX_DETAIL	Tax Detail	G15 GST Free Capital Purchases for Private Use	G15 GST Free Capital Purchases for Private Use	2022-09-20 14:09:27.792826+05:30	2022-09-20 14:09:27.792857+05:30	1	t	{"tax_rate": 0.0, "tax_solution_id": "Australia - GST"}	f
579	TAX_DETAIL	Tax Detail	G10 Capital Acquisition	G10 Capital Acquisition	2022-09-20 14:09:27.792933+05:30	2022-09-20 14:09:27.792963+05:30	1	t	{"tax_rate": 10.0, "tax_solution_id": "Australia - GST"}	f
580	TAX_DETAIL	Tax Detail	G14 GST Free Capital Purchases	G14 GST Free Capital Purchases	2022-09-20 14:09:27.793037+05:30	2022-09-20 14:09:27.793066+05:30	1	t	{"tax_rate": 0.0, "tax_solution_id": "Australia - GST"}	f
581	TAX_DETAIL	Tax Detail	G13 Purchases for Input Tax Sales	G13 Purchases for Input Tax Sales	2022-09-20 14:09:27.793138+05:30	2022-09-20 14:09:27.793167+05:30	1	t	{"tax_rate": 10.0, "tax_solution_id": "Australia - GST"}	f
582	TAX_DETAIL	Tax Detail	G13 GST Free Purchases for Input Tax Sales	G13 GST Free Purchases for Input Tax Sales	2022-09-20 14:09:27.793238+05:30	2022-09-20 14:09:27.793268+05:30	1	t	{"tax_rate": 0.0, "tax_solution_id": "Australia - GST"}	f
583	TAX_DETAIL	Tax Detail	1F Luxury Car Tax Refundable	1F Luxury Car Tax Refundable	2022-09-20 14:09:27.793576+05:30	2022-09-20 14:09:27.793659+05:30	1	t	{"tax_rate": 0.0, "tax_solution_id": "Australia - GST"}	f
584	TAX_DETAIL	Tax Detail	G10 Motor Vehicle Acquisition	G10 Motor Vehicle Acquisition	2022-09-20 14:09:27.793809+05:30	2022-09-20 14:09:27.793943+05:30	1	t	{"tax_rate": 10.0, "tax_solution_id": "Australia - GST"}	f
585	TAX_DETAIL	Tax Detail	G11 Other Acquisition	G11 Other Acquisition	2022-09-20 14:09:27.794101+05:30	2022-09-20 14:09:27.794146+05:30	1	t	{"tax_rate": 10.0, "tax_solution_id": "Australia - GST"}	f
586	TAX_DETAIL	Tax Detail	G14 GST Free Non-Capital Purchases	G14 GST Free Non-Capital Purchases	2022-09-20 14:09:27.794525+05:30	2022-09-20 14:09:27.794595+05:30	1	t	{"tax_rate": 0.0, "tax_solution_id": "Australia - GST"}	f
587	TAX_DETAIL	Tax Detail	G15 Purchases for Private Use	G15 Purchases for Private Use	2022-09-20 14:09:27.794727+05:30	2022-09-20 14:09:27.794871+05:30	1	t	{"tax_rate": 10.0, "tax_solution_id": "Australia - GST"}	f
588	TAX_DETAIL	Tax Detail	G15 GST Free Purchases for Private Use	G15 GST Free Purchases for Private Use	2022-09-20 14:09:27.795077+05:30	2022-09-20 14:09:27.795117+05:30	1	t	{"tax_rate": 0.0, "tax_solution_id": "Australia - GST"}	f
589	TAX_DETAIL	Tax Detail	1D Wine Equalisation Tax Refundable	1D Wine Equalisation Tax Refundable	2022-09-20 14:09:27.795252+05:30	2022-09-20 14:09:27.795653+05:30	1	t	{"tax_rate": 0.0, "tax_solution_id": "Australia - GST"}	f
590	TAX_DETAIL	Tax Detail	W4 Withholding Tax	W4 Withholding Tax	2022-09-20 14:09:27.795831+05:30	2022-09-20 14:09:27.795874+05:30	1	t	{"tax_rate": 0.0, "tax_solution_id": "Australia - GST"}	f
591	TAX_DETAIL	Tax Detail	Standard Rate Input	Standard Rate Input	2022-09-20 14:09:27.796052+05:30	2022-09-20 14:09:27.79611+05:30	1	t	{"tax_rate": 15.0, "tax_solution_id": "South Africa - VAT"}	f
592	TAX_DETAIL	Tax Detail	Standard Rate (Capital Goods) Input	Standard Rate (Capital Goods) Input	2022-09-20 14:09:27.796254+05:30	2022-09-20 14:09:27.796436+05:30	1	t	{"tax_rate": 15.0, "tax_solution_id": "South Africa - VAT"}	f
593	TAX_DETAIL	Tax Detail	Change in Use Input	Change in Use Input	2022-09-20 14:09:27.796537+05:30	2022-09-20 14:09:27.796577+05:30	1	t	{"tax_rate": 15.0, "tax_solution_id": "South Africa - VAT"}	f
594	TAX_DETAIL	Tax Detail	Capital Goods Imported	Capital Goods Imported	2022-09-20 14:09:27.807918+05:30	2022-09-20 14:09:27.807958+05:30	1	t	{"tax_rate": 0.0, "tax_solution_id": "South Africa - VAT"}	f
595	TAX_DETAIL	Tax Detail	Other Goods Imported (Not Capital Goods)	Other Goods Imported (Not Capital Goods)	2022-09-20 14:09:27.808026+05:30	2022-09-20 14:09:27.808055+05:30	1	t	{"tax_rate": 0.0, "tax_solution_id": "South Africa - VAT"}	f
596	TAX_DETAIL	Tax Detail	Other Output Tax Adjustments	Other Output Tax Adjustments	2022-09-20 14:09:27.80812+05:30	2022-09-20 14:09:27.808148+05:30	1	t	{"tax_rate": 100.0, "tax_solution_id": "South Africa - VAT"}	f
597	TAX_DETAIL	Tax Detail	No Input VAT	No Input VAT	2022-09-20 14:09:27.808213+05:30	2022-09-20 14:09:27.808241+05:30	1	t	{"tax_rate": 0.0, "tax_solution_id": "South Africa - VAT"}	f
598	PROJECT	project	Direct Mail Campaign	10064	2022-09-20 14:09:34.293442+05:30	2022-09-20 14:09:34.293484+05:30	1	t	{"customer_id": "10064", "customer_name": "Med dot"}	f
599	PROJECT	project	Branding Follow Up	10063	2022-09-20 14:09:34.293557+05:30	2022-09-20 14:09:34.293588+05:30	1	t	{"customer_id": "10063", "customer_name": "Portore"}	f
600	PROJECT	project	labhvam	10083	2022-09-20 14:09:34.293908+05:30	2022-09-20 14:09:34.293939+05:30	1	t	{"customer_id": "10005", "customer_name": "Nirvana"}	f
601	PROJECT	project	Ecommerce Campaign	10062	2022-09-20 14:09:34.294006+05:30	2022-09-20 14:09:34.294034+05:30	1	t	{"customer_id": "10062", "customer_name": "Vertous"}	f
602	PROJECT	project	Branding Analysis	10061	2022-09-20 14:09:34.294099+05:30	2022-09-20 14:09:34.294126+05:30	1	t	{"customer_id": "10061", "customer_name": "Avu"}	f
603	PROJECT	project	Mobile App Redesign	10080	2022-09-20 14:09:34.29419+05:30	2022-09-20 14:09:34.294218+05:30	1	t	{"customer_id": null, "customer_name": null}	f
604	PROJECT	project	Platform APIs	10081	2022-09-20 14:09:34.294281+05:30	2022-09-20 14:09:34.294308+05:30	1	t	{"customer_id": null, "customer_name": null}	f
605	PROJECT	project	Fyle NetSuite Integration	10078	2022-09-20 14:09:34.294492+05:30	2022-09-20 14:09:34.294539+05:30	1	t	{"customer_id": null, "customer_name": null}	f
606	PROJECT	project	Fyle Sage Intacct Integration	10077	2022-09-20 14:09:34.294678+05:30	2022-09-20 14:09:34.294726+05:30	1	t	{"customer_id": null, "customer_name": null}	f
607	PROJECT	project	Support Taxes	10082	2022-09-20 14:09:34.294831+05:30	2022-09-20 14:09:34.294862+05:30	1	t	{"customer_id": null, "customer_name": null}	f
608	PROJECT	project	T&M Project with Five Tasks	Template-TM	2022-09-20 14:09:34.294936+05:30	2022-09-20 14:09:34.294964+05:30	1	t	{"customer_id": null, "customer_name": null}	f
609	PROJECT	project	Fixed Fee Project with Five Tasks	Template-FF	2022-09-20 14:09:34.295028+05:30	2022-09-20 14:09:34.295056+05:30	1	t	{"customer_id": null, "customer_name": null}	f
610	PROJECT	project	General Overhead	10000	2022-09-20 14:09:34.295119+05:30	2022-09-20 14:09:34.295146+05:30	1	t	{"customer_id": null, "customer_name": null}	f
611	PROJECT	project	General Overhead-Current	10025	2022-09-20 14:09:34.295209+05:30	2022-09-20 14:09:34.295237+05:30	1	t	{"customer_id": null, "customer_name": null}	f
612	PROJECT	project	Fyle Engineering	10079	2022-09-20 14:09:34.2953+05:30	2022-09-20 14:09:34.295327+05:30	1	t	{"customer_id": null, "customer_name": null}	f
613	PROJECT	project	Integrations	10076	2022-09-20 14:09:34.295505+05:30	2022-09-20 14:09:34.29553+05:30	1	t	{"customer_id": null, "customer_name": null}	f
614	EXPENSE_PAYMENT_TYPE	expense payment type	Company Credit Card	1	2022-09-20 14:09:45.743113+05:30	2022-09-20 14:09:45.743385+05:30	1	\N	{"is_reimbursable": false}	f
615	CLASS	class	Small Business	400	2022-09-20 14:09:48.468017+05:30	2022-09-20 14:09:48.468059+05:30	1	\N	\N	f
616	CLASS	class	Midsize Business	500	2022-09-20 14:09:48.468115+05:30	2022-09-20 14:09:48.468143+05:30	1	\N	\N	f
617	CLASS	class	Enterprise	600	2022-09-20 14:09:48.468196+05:30	2022-09-20 14:09:48.468223+05:30	1	\N	\N	f
618	CLASS	class	Service Line 2	200	2022-09-20 14:09:48.468276+05:30	2022-09-20 14:09:48.468303+05:30	1	\N	\N	f
619	CLASS	class	Service Line 1	100	2022-09-20 14:09:48.468356+05:30	2022-09-20 14:09:48.468383+05:30	1	\N	\N	f
620	CLASS	class	Service Line 3	300	2022-09-20 14:09:48.468597+05:30	2022-09-20 14:09:48.468637+05:30	1	\N	\N	f
621	CHARGE_CARD_NUMBER	Charge Card Account	Charge Card 1	Charge Card 1	2022-09-20 14:09:52.257834+05:30	2022-09-20 14:09:52.257879+05:30	1	\N	\N	f
622	CHARGE_CARD_NUMBER	Charge Card Account	nilesh	nilesh	2022-09-20 14:09:52.257935+05:30	2022-09-20 14:09:52.25795+05:30	1	\N	\N	f
623	CHARGE_CARD_NUMBER	Charge Card Account	nilesh2	nilesh2	2022-09-20 14:09:52.257988+05:30	2022-09-20 14:09:52.258009+05:30	1	\N	\N	f
624	CHARGE_CARD_NUMBER	Charge Card Account	jojobubu	jojobubu	2022-09-20 14:09:52.258075+05:30	2022-09-20 14:09:52.258103+05:30	1	\N	\N	f
625	CHARGE_CARD_NUMBER	Charge Card Account	creditcardsecondry	creditcardsecondry	2022-09-20 14:09:52.258156+05:30	2022-09-20 14:09:52.258184+05:30	1	\N	\N	f
626	PAYMENT_ACCOUNT	Payment Account	Demo Bank - 500_CHK	500_CHK	2022-09-20 14:10:00.017808+05:30	2022-09-20 14:10:00.018547+05:30	1	\N	\N	f
627	PAYMENT_ACCOUNT	Payment Account	Demo Bank - 400_CHK	400_CHK	2022-09-20 14:10:00.018865+05:30	2022-09-20 14:10:00.018968+05:30	1	\N	\N	f
628	PAYMENT_ACCOUNT	Payment Account	Demo Bank - 700_CHK	700_CHK	2022-09-20 14:10:00.019271+05:30	2022-09-20 14:10:00.019311+05:30	1	\N	\N	f
629	PAYMENT_ACCOUNT	Payment Account	Demo Bank - 100_CHK	100_CHK	2022-09-20 14:10:00.019399+05:30	2022-09-20 14:10:00.019442+05:30	1	\N	\N	f
630	PAYMENT_ACCOUNT	Payment Account	Demo Bank - 300_CHK	300_CHK	2022-09-20 14:10:00.019538+05:30	2022-09-20 14:10:00.019581+05:30	1	\N	\N	f
631	PAYMENT_ACCOUNT	Payment Account	Demo Bank - 200_CHK	200_CHK	2022-09-20 14:10:00.019678+05:30	2022-09-20 14:10:00.019728+05:30	1	\N	\N	f
632	PAYMENT_ACCOUNT	Payment Account	Demo Bank - 600_CHK	600_CHK	2022-09-20 14:10:00.019836+05:30	2022-09-20 14:10:00.019888+05:30	1	\N	\N	f
633	VENDOR	vendor	Vaishnavi Primary	Vaishnavi Primary	2022-09-20 14:10:03.828715+05:30	2022-09-20 14:10:03.828765+05:30	1	\N	{"email": "vaishnavi.mohan+primary@fyle.in"}	f
634	VENDOR	vendor	VM	VM	2022-09-20 14:10:03.828973+05:30	2022-09-20 14:10:03.829002+05:30	1	\N	{"email": "vaishnavi.mohan@fyle.in"}	f
635	VENDOR	vendor	Yash	Yash	2022-09-20 14:10:03.831136+05:30	2022-09-20 14:10:03.831205+05:30	1	\N	{"email": "ajain@fyle.in"}	f
636	VENDOR	vendor	gokul	gokul	2022-09-20 14:10:03.83134+05:30	2022-09-20 14:10:03.831373+05:30	1	\N	{"email": "gokul.kathiresan@fyle.in"}	f
637	VENDOR	vendor	Nilesh, Dhoni	Nilesh2 Dhoni	2022-09-20 14:10:03.831454+05:30	2022-09-20 14:10:03.831486+05:30	1	\N	{"email": "india2@vendor.com"}	f
638	VENDOR	vendor	Sachin, Saran	Sachin Saran	2022-09-20 14:10:03.831567+05:30	2022-09-20 14:10:03.83159+05:30	1	\N	{"email": "user5@fyleforbill.je"}	f
639	VENDOR	vendor	Victor Martinez	Victor Martinez	2022-09-20 14:10:03.831657+05:30	2022-09-20 14:10:03.831683+05:30	1	\N	{"email": "user6@fyleforbill.cct"}	f
640	VENDOR	vendor	akavuluru	akavuluru	2022-09-20 14:10:03.831745+05:30	2022-09-20 14:10:03.831767+05:30	1	\N	{"email": "akavuluru@fyle-us.com"}	f
641	VENDOR	vendor	Srav	Srav	2022-09-20 14:10:03.831837+05:30	2022-09-20 14:10:03.831867+05:30	1	\N	{"email": "sravan.kumar@fyle.in"}	f
642	VENDOR	vendor	Chris Curtis	Chris Curtis	2022-09-20 14:10:03.831936+05:30	2022-09-20 14:10:03.831965+05:30	1	\N	{"email": "user5@fyleforbill.cct"}	f
643	VENDOR	vendor	James Taylor	James Taylor	2022-09-20 14:10:03.832034+05:30	2022-09-20 14:10:03.832054+05:30	1	\N	{"email": "user7@fyleforbill.cct"}	f
644	VENDOR	vendor	Matthew Estrada	Matthew Estrada	2022-09-20 14:10:03.832116+05:30	2022-09-20 14:10:03.832636+05:30	1	\N	{"email": "user10@fyleforbill.cct"}	f
645	VENDOR	vendor	Samantha Washington	Samantha Washington	2022-09-20 14:10:03.833274+05:30	2022-09-20 14:10:03.833314+05:30	1	\N	{"email": "user4@fyleforbill.cct"}	f
646	VENDOR	vendor	Ashwin from NetSuite	Ashwin from NetSuite	2022-09-20 14:10:03.833406+05:30	2022-09-20 14:10:03.833438+05:30	1	\N	{"email": "ashwin.t@fyle.in"}	f
647	VENDOR	vendor	Justin Glass	Justin Glass	2022-09-20 14:10:03.833616+05:30	2022-09-20 14:10:03.834056+05:30	1	\N	{"email": "user9@fyleforbill.cct"}	f
648	VENDOR	vendor	Brian Foster	Brian Foster	2022-09-20 14:10:03.834295+05:30	2022-09-20 14:10:03.834327+05:30	1	\N	{"email": "user2@fyleforbill.cct"}	f
649	VENDOR	vendor	Jessica Lane	Jessica Lane	2022-09-20 14:10:03.834405+05:30	2022-09-20 14:10:03.83442+05:30	1	\N	{"email": "user8@fyleforbill.cct"}	f
650	VENDOR	vendor	Natalie Pope	Natalie Pope	2022-09-20 14:10:03.83448+05:30	2022-09-20 14:10:03.83451+05:30	1	\N	{"email": "user3@fyleforbill.cct"}	f
651	VENDOR	vendor	Kristofferson Consulting	20014	2022-09-20 14:10:03.834573+05:30	2022-09-20 14:10:03.834595+05:30	1	\N	{"email": null}	f
652	VENDOR	vendor	HC Equipment Repair	20015	2022-09-20 14:10:03.834664+05:30	2022-09-20 14:10:03.834693+05:30	1	\N	{"email": null}	f
653	VENDOR	vendor	Kaufman & Langer LLP	20013	2022-09-20 14:10:03.835117+05:30	2022-09-20 14:10:03.835242+05:30	1	\N	{"email": null}	f
654	VENDOR	vendor	Global Properties Inc.	20002	2022-09-20 14:10:03.835515+05:30	2022-09-20 14:10:03.835549+05:30	1	\N	{"email": null}	f
655	VENDOR	vendor	ADP	20003	2022-09-20 14:10:03.835803+05:30	2022-09-20 14:10:03.835829+05:30	1	\N	{"email": null}	f
656	VENDOR	vendor	National Grid	20004	2022-09-20 14:10:03.835898+05:30	2022-09-20 14:10:03.835929+05:30	1	\N	{"email": null}	f
657	VENDOR	vendor	Lenovo	20007	2022-09-20 14:10:03.835996+05:30	2022-09-20 14:10:03.836026+05:30	1	\N	{"email": null}	f
658	VENDOR	vendor	State Bank	20011	2022-09-20 14:10:03.836083+05:30	2022-09-20 14:10:03.836104+05:30	1	\N	{"email": null}	f
659	VENDOR	vendor	Linda Hicks	20021	2022-09-20 14:10:03.83617+05:30	2022-09-20 14:10:03.836199+05:30	1	\N	{"email": null}	f
660	VENDOR	vendor	Lee Thomas	20022	2022-09-20 14:10:03.836345+05:30	2022-09-20 14:10:03.83637+05:30	1	\N	{"email": null}	f
661	VENDOR	vendor	Singleton Brothers CPA	20012	2022-09-20 14:10:03.836434+05:30	2022-09-20 14:10:03.836455+05:30	1	\N	{"email": null}	f
662	VENDOR	vendor	The Nonprofit Alliance	20017	2022-09-20 14:10:03.836778+05:30	2022-09-20 14:10:03.836847+05:30	1	\N	{"email": null}	f
663	VENDOR	vendor	Massachusetts Department of Revenue	20001	2022-09-20 14:10:03.837024+05:30	2022-09-20 14:10:03.83706+05:30	1	\N	{"email": null}	f
664	VENDOR	vendor	Entity V600	20600	2022-09-20 14:10:03.837241+05:30	2022-09-20 14:10:03.837454+05:30	1	\N	{"email": null}	f
665	VENDOR	vendor	Entity V500	20500	2022-09-20 14:10:03.837664+05:30	2022-09-20 14:10:03.837735+05:30	1	\N	{"email": null}	f
666	VENDOR	vendor	Entity V400	20400	2022-09-20 14:10:03.837834+05:30	2022-09-20 14:10:03.837861+05:30	1	\N	{"email": null}	f
667	VENDOR	vendor	Entity V700	20700	2022-09-20 14:10:03.837931+05:30	2022-09-20 14:10:03.837956+05:30	1	\N	{"email": null}	f
668	VENDOR	vendor	Worldwide Commercial	20008	2022-09-20 14:10:03.838019+05:30	2022-09-20 14:10:03.838208+05:30	1	\N	{"email": null}	f
669	VENDOR	vendor	Citi Bank	20009	2022-09-20 14:10:03.838292+05:30	2022-09-20 14:10:03.838316+05:30	1	\N	{"email": null}	f
670	VENDOR	vendor	River Glen Insurance	20018	2022-09-20 14:10:03.838377+05:30	2022-09-20 14:10:03.838407+05:30	1	\N	{"email": null}	f
671	VENDOR	vendor	Hanson Learning Solutions	20019	2022-09-20 14:10:03.838485+05:30	2022-09-20 14:10:03.838504+05:30	1	\N	{"email": null}	f
672	VENDOR	vendor	Neighborhood Printers	20020	2022-09-20 14:10:03.838562+05:30	2022-09-20 14:10:03.838595+05:30	1	\N	{"email": null}	f
673	VENDOR	vendor	The Post Company	20016	2022-09-20 14:10:03.838648+05:30	2022-09-20 14:10:03.83867+05:30	1	\N	{"email": null}	f
674	VENDOR	vendor	Green Team Waste Management	20010	2022-09-20 14:10:03.838742+05:30	2022-09-20 14:10:03.838761+05:30	1	\N	{"email": null}	f
675	VENDOR	vendor	Entity V100	20100	2022-09-20 14:10:03.838814+05:30	2022-09-20 14:10:03.838847+05:30	1	\N	{"email": null}	f
676	VENDOR	vendor	Entity V200	20200	2022-09-20 14:10:03.838922+05:30	2022-09-20 14:10:03.838961+05:30	1	\N	{"email": null}	f
677	VENDOR	vendor	Entity V300	20300	2022-09-20 14:10:03.839181+05:30	2022-09-20 14:10:03.8392+05:30	1	\N	{"email": null}	f
678	VENDOR	vendor	American Express	20006	2022-09-20 14:10:03.839245+05:30	2022-09-20 14:10:03.839266+05:30	1	\N	{"email": null}	f
679	VENDOR	vendor	Canyon CPA	20061	2022-09-20 14:10:03.83934+05:30	2022-09-20 14:10:03.839377+05:30	1	\N	{"email": null}	f
680	VENDOR	vendor	Paramount Consulting	20062	2022-09-20 14:10:03.839437+05:30	2022-09-20 14:10:03.839459+05:30	1	\N	{"email": null}	f
681	VENDOR	vendor	Microns Consulting	20071	2022-09-20 14:10:03.839538+05:30	2022-09-20 14:10:03.839568+05:30	1	\N	{"email": null}	f
682	VENDOR	vendor	Global Printing	20063	2022-09-20 14:10:03.839642+05:30	2022-09-20 14:10:03.839668+05:30	1	\N	{"email": null}	f
683	VENDOR	vendor	Quick Post	20074	2022-09-20 14:10:03.852409+05:30	2022-09-20 14:10:03.852446+05:30	1	\N	{"email": null}	f
684	VENDOR	vendor	Scribe Post	20064	2022-09-20 14:10:03.854483+05:30	2022-09-20 14:10:03.854613+05:30	1	\N	{"email": null}	f
685	VENDOR	vendor	Vision Post	20073	2022-09-20 14:10:03.854935+05:30	2022-09-20 14:10:03.854985+05:30	1	\N	{"email": null}	f
686	VENDOR	vendor	Magnolia CPA	20072	2022-09-20 14:10:03.855708+05:30	2022-09-20 14:10:03.85577+05:30	1	\N	{"email": null}	f
687	VENDOR	vendor	Investor CPA	20051	2022-09-20 14:10:03.855906+05:30	2022-09-20 14:10:03.85596+05:30	1	\N	{"email": null}	f
688	VENDOR	vendor	Quali Consultants	20052	2022-09-20 14:10:03.856136+05:30	2022-09-20 14:10:03.856411+05:30	1	\N	{"email": null}	f
689	VENDOR	vendor	Prima Printing	20053	2022-09-20 14:10:03.857565+05:30	2022-09-20 14:10:03.857676+05:30	1	\N	{"email": null}	f
690	VENDOR	vendor	Boardwalk Post	20054	2022-09-20 14:10:03.858867+05:30	2022-09-20 14:10:03.858918+05:30	1	\N	{"email": null}	f
691	VENDOR	vendor	Consulting Grid	20041	2022-09-20 14:10:03.859006+05:30	2022-09-20 14:10:03.859037+05:30	1	\N	{"email": null}	f
692	VENDOR	vendor	Cornerstone	20042	2022-09-20 14:10:03.859112+05:30	2022-09-20 14:10:03.859141+05:30	1	\N	{"email": null}	f
693	VENDOR	vendor	Advisor Printing	20043	2022-09-20 14:10:03.859208+05:30	2022-09-20 14:10:03.859237+05:30	1	\N	{"email": null}	f
694	VENDOR	vendor	Prosper Post	20044	2022-09-20 14:10:03.859304+05:30	2022-09-20 14:10:03.859333+05:30	1	\N	{"email": null}	f
695	VENDOR	vendor	National Insurance	20005	2022-09-20 14:10:03.859401+05:30	2022-09-20 14:10:03.859433+05:30	1	\N	{"email": null}	f
696	VENDOR	vendor	Joshua Wood	Joshua Wood	2022-09-20 14:10:03.859502+05:30	2022-09-20 14:10:03.859692+05:30	1	\N	{"email": "user1@fyleforbill.cct"}	f
697	VENDOR	vendor	Theresa Brown	Theresa Brown	2022-09-20 14:10:03.859791+05:30	2022-09-20 14:10:03.859814+05:30	1	\N	{"email": "admin1@fyleforselectcfieldsns.in"}	f
698	VENDOR	vendor	Credit Card Misc	Credit Card Misc	2022-09-20 14:10:03.859917+05:30	2022-09-20 14:10:03.859933+05:30	1	\N	{"email": null}	f
699	VENDOR	vendor	Ashwin	Ashwin	2022-09-20 14:10:03.859986+05:30	2022-09-20 14:10:03.860016+05:30	1	\N	{"email": "ashwin.t@fyle.in"}	f
700	EMPLOYEE	employee	Franco, Ryan	1005	2022-09-20 14:10:08.456834+05:30	2022-09-20 14:10:08.456891+05:30	1	\N	{"email": "ryan@demo.com", "full_name": "Franco, Ryan", "location_id": null, "department_id": "100"}	f
701	EMPLOYEE	employee	Evans, Chelsea	1004	2022-09-20 14:10:08.45699+05:30	2022-09-20 14:10:08.457025+05:30	1	\N	{"email": "chelsea@demo.com", "full_name": "Evans, Chelsea", "location_id": null, "department_id": "200"}	f
702	EMPLOYEE	employee	Klein, Tom	1001	2022-09-20 14:10:08.45711+05:30	2022-09-20 14:10:08.457141+05:30	1	\N	{"email": "tom@demo.com", "full_name": "Klein, Tom", "location_id": null, "department_id": "300"}	f
703	EMPLOYEE	employee	Tesla, Nikki	1003	2022-09-20 14:10:08.457221+05:30	2022-09-20 14:10:08.457252+05:30	1	\N	{"email": "nikki@demo.com", "full_name": "Tesla, Nikki", "location_id": null, "department_id": "200"}	f
704	EMPLOYEE	employee	Moloney, Mark	1007	2022-09-20 14:10:08.457328+05:30	2022-09-20 14:10:08.457359+05:30	1	\N	{"email": "mark@demo.com", "full_name": "Moloney, Mark", "location_id": null, "department_id": "400"}	f
705	EMPLOYEE	employee	Collins, Mike	1026	2022-09-20 14:10:08.457433+05:30	2022-09-20 14:10:08.457462+05:30	1	\N	{"email": "mike@demo.com", "full_name": "Collins, Mike", "location_id": null, "department_id": null}	f
706	EMPLOYEE	employee	Penny, Emma	1000	2022-09-20 14:10:08.457533+05:30	2022-09-20 14:10:08.457562+05:30	1	\N	{"email": "emma@demo.com", "full_name": "Penny, Emma", "location_id": null, "department_id": "300"}	f
707	EMPLOYEE	employee	Joanna	Joanna	2022-09-20 14:10:08.457633+05:30	2022-09-20 14:10:08.457662+05:30	1	\N	{"email": "ashwin.t@fyle.in", "full_name": "Joanna", "location_id": null, "department_id": "300"}	f
708	EMPLOYEE	employee	Labhvam Bhaiya	Labhvam Bhaiya	2022-09-20 14:10:08.457733+05:30	2022-09-20 14:10:08.457762+05:30	1	\N	{"email": "user4@fylefordashboard1.com", "full_name": "Labhvam Bhaiya", "location_id": null, "department_id": "300"}	f
709	EMPLOYEE	employee	Brian Foster	Brian Foster	2022-09-20 14:10:08.457866+05:30	2022-09-20 14:10:08.457917+05:30	1	\N	{"email": "user2@fyleforfyle.cleanup", "full_name": "Brian Foster", "location_id": null, "department_id": "300"}	f
710	EMPLOYEE	employee	Chris Curtis	Chris Curtis	2022-09-20 14:10:08.458307+05:30	2022-09-20 14:10:08.458332+05:30	1	\N	{"email": "user5@fyleforfyle.cleanup", "full_name": "Chris Curtis", "location_id": null, "department_id": "300"}	f
711	EMPLOYEE	employee	Real OG	Real OG	2022-09-20 14:10:08.458396+05:30	2022-09-20 14:10:08.458427+05:30	1	\N	{"email": "user7@fyleforfyle.cleanup", "full_name": "Real OG", "location_id": null, "department_id": "300"}	f
712	EMPLOYEE	employee	Gale, Brittney	1074	2022-09-20 14:10:08.458499+05:30	2022-09-20 14:10:08.458529+05:30	1	\N	{"email": null, "full_name": "Gale, Brittney", "location_id": null, "department_id": "200"}	f
713	EMPLOYEE	employee	Darwin, Chuck	1002	2022-09-20 14:10:08.4586+05:30	2022-09-20 14:10:08.45863+05:30	1	\N	{"email": "chuck@demo.com", "full_name": "Darwin, Chuck", "location_id": null, "department_id": "300"}	f
714	EMPLOYEE	employee	Designer	1023	2022-09-20 14:10:08.458699+05:30	2022-09-20 14:10:08.458728+05:30	1	\N	{"email": null, "full_name": "Designer", "location_id": null, "department_id": null}	f
715	EMPLOYEE	employee	Rhodes, Giorgia	1062	2022-09-20 14:10:08.458798+05:30	2022-09-20 14:10:08.458828+05:30	1	\N	{"email": null, "full_name": "Rhodes, Giorgia", "location_id": "600", "department_id": "500"}	f
716	EMPLOYEE	employee	Rayner, Abigail	1052	2022-09-20 14:10:08.458897+05:30	2022-09-20 14:10:08.458926+05:30	1	\N	{"email": null, "full_name": "Rayner, Abigail", "location_id": null, "department_id": "200"}	f
717	EMPLOYEE	employee	Donovan, Simra	1044	2022-09-20 14:10:08.458996+05:30	2022-09-20 14:10:08.459038+05:30	1	\N	{"email": null, "full_name": "Donovan, Simra", "location_id": null, "department_id": "400"}	f
718	EMPLOYEE	employee	Searle, Lola	1054	2022-09-20 14:10:08.459159+05:30	2022-09-20 14:10:08.459203+05:30	1	\N	{"email": null, "full_name": "Searle, Lola", "location_id": null, "department_id": "300"}	f
719	EMPLOYEE	employee	Hodges, Jerome	1064	2022-09-20 14:10:08.45932+05:30	2022-09-20 14:10:08.459367+05:30	1	\N	{"email": null, "full_name": "Hodges, Jerome", "location_id": "600", "department_id": "300"}	f
720	EMPLOYEE	employee	Draper, Shelbie	1071	2022-09-20 14:10:08.45949+05:30	2022-09-20 14:10:08.459539+05:30	1	\N	{"email": null, "full_name": "Draper, Shelbie", "location_id": null, "department_id": "200"}	f
721	EMPLOYEE	employee	Barker, Brendan	1072	2022-09-20 14:10:08.459661+05:30	2022-09-20 14:10:08.459704+05:30	1	\N	{"email": null, "full_name": "Barker, Brendan", "location_id": null, "department_id": "200"}	f
722	EMPLOYEE	employee	Meadows, Tommy	1061	2022-09-20 14:10:08.459939+05:30	2022-09-20 14:10:08.459999+05:30	1	\N	{"email": null, "full_name": "Meadows, Tommy", "location_id": "600", "department_id": "200"}	f
723	EMPLOYEE	employee	Regan, Bruce	1063	2022-09-20 14:10:08.460132+05:30	2022-09-20 14:10:08.460176+05:30	1	\N	{"email": null, "full_name": "Regan, Bruce", "location_id": "600", "department_id": "100"}	f
724	EMPLOYEE	employee	Preece, Ewan	1073	2022-09-20 14:10:08.460294+05:30	2022-09-20 14:10:08.460339+05:30	1	\N	{"email": null, "full_name": "Preece, Ewan", "location_id": null, "department_id": "300"}	f
725	EMPLOYEE	employee	Singh, Sanjay	1011	2022-09-20 14:10:08.467702+05:30	2022-09-20 14:10:08.467875+05:30	1	\N	{"email": "sanjay@demo.com", "full_name": "Singh, Sanjay", "location_id": null, "department_id": "100"}	f
726	EMPLOYEE	employee	Monaghan, Toyah	1043	2022-09-20 14:10:08.468576+05:30	2022-09-20 14:10:08.468797+05:30	1	\N	{"email": null, "full_name": "Monaghan, Toyah", "location_id": null, "department_id": "300"}	f
727	EMPLOYEE	employee	Saunders, Jill	1018	2022-09-20 14:10:08.469652+05:30	2022-09-20 14:10:08.469702+05:30	1	\N	{"email": "jill@demo.com", "full_name": "Saunders, Jill", "location_id": null, "department_id": "400"}	f
728	EMPLOYEE	employee	Director	1022	2022-09-20 14:10:08.469829+05:30	2022-09-20 14:10:08.469877+05:30	1	\N	{"email": null, "full_name": "Director", "location_id": null, "department_id": null}	f
729	EMPLOYEE	employee	Developer	1024	2022-09-20 14:10:08.470491+05:30	2022-09-20 14:10:08.47072+05:30	1	\N	{"email": null, "full_name": "Developer", "location_id": null, "department_id": null}	f
730	EMPLOYEE	employee	Consultant	1025	2022-09-20 14:10:08.472746+05:30	2022-09-20 14:10:08.472887+05:30	1	\N	{"email": null, "full_name": "Consultant", "location_id": null, "department_id": null}	f
731	EMPLOYEE	employee	Project Manager	1021	2022-09-20 14:10:08.473093+05:30	2022-09-20 14:10:08.47312+05:30	1	\N	{"email": null, "full_name": "Project Manager", "location_id": null, "department_id": null}	f
732	EMPLOYEE	employee	Ponce, Gail	1042	2022-09-20 14:10:08.47329+05:30	2022-09-20 14:10:08.473419+05:30	1	\N	{"email": null, "full_name": "Ponce, Gail", "location_id": null, "department_id": "100"}	f
733	EMPLOYEE	employee	Torres, Dario	1041	2022-09-20 14:10:08.473496+05:30	2022-09-20 14:10:08.47352+05:30	1	\N	{"email": null, "full_name": "Torres, Dario", "location_id": null, "department_id": "300"}	f
734	EMPLOYEE	employee	Haines, Annika	1051	2022-09-20 14:10:08.473599+05:30	2022-09-20 14:10:08.474286+05:30	1	\N	{"email": null, "full_name": "Haines, Annika", "location_id": null, "department_id": "200"}	f
735	EMPLOYEE	employee	Medrano, Jenson	1053	2022-09-20 14:10:08.480723+05:30	2022-09-20 14:10:08.481196+05:30	1	\N	{"email": null, "full_name": "Medrano, Jenson", "location_id": null, "department_id": "200"}	f
736	EMPLOYEE	employee	Chen, Kathryn	1006	2022-09-20 14:10:08.481481+05:30	2022-09-20 14:10:08.481539+05:30	1	\N	{"email": "kathryn@demo.com", "full_name": "Chen, Kathryn", "location_id": null, "department_id": "100"}	f
737	EMPLOYEE	employee	Hoffman, Lisa	1008	2022-09-20 14:10:08.48166+05:30	2022-09-20 14:10:08.481694+05:30	1	\N	{"email": "lisa@demo.com", "full_name": "Hoffman, Lisa", "location_id": null, "department_id": "500"}	f
738	EMPLOYEE	employee	Peters, Derek	1009	2022-09-20 14:10:08.481785+05:30	2022-09-20 14:10:08.481816+05:30	1	\N	{"email": "derek@demo.com", "full_name": "Peters, Derek", "location_id": null, "department_id": "200"}	f
739	EMPLOYEE	employee	Wallace, Amy	1010	2022-09-20 14:10:08.481917+05:30	2022-09-20 14:10:08.481963+05:30	1	\N	{"email": "amy@demo.com", "full_name": "Wallace, Amy", "location_id": null, "department_id": "100"}	f
740	EMPLOYEE	employee	King, Kristin	1012	2022-09-20 14:10:08.482174+05:30	2022-09-20 14:10:08.482206+05:30	1	\N	{"email": "kristin@demo.com", "full_name": "King, Kristin", "location_id": null, "department_id": "100"}	f
741	EMPLOYEE	employee	Lee, Max	1013	2022-09-20 14:10:08.482317+05:30	2022-09-20 14:10:08.482339+05:30	1	\N	{"email": "max@demo.com", "full_name": "Lee, Max", "location_id": null, "department_id": "200"}	f
742	EMPLOYEE	employee	Farley, Nicole	1014	2022-09-20 14:10:08.482407+05:30	2022-09-20 14:10:08.482448+05:30	1	\N	{"email": "nicole@demo.com", "full_name": "Farley, Nicole", "location_id": null, "department_id": "400"}	f
743	EMPLOYEE	employee	Reyes, Christian	1015	2022-09-20 14:10:08.48254+05:30	2022-09-20 14:10:08.48257+05:30	1	\N	{"email": "christian@demo.com", "full_name": "Reyes, Christian", "location_id": null, "department_id": "500"}	f
744	EMPLOYEE	employee	Chang, Andrew	1016	2022-09-20 14:10:08.482635+05:30	2022-09-20 14:10:08.482664+05:30	1	\N	{"email": "andrew@demo.com", "full_name": "Chang, Andrew", "location_id": null, "department_id": "200"}	f
745	EMPLOYEE	employee	Gupta, Chandra	1017	2022-09-20 14:10:08.482743+05:30	2022-09-20 14:10:08.482774+05:30	1	\N	{"email": "chandra@demo.com", "full_name": "Gupta, Chandra", "location_id": null, "department_id": "400"}	f
746	EMPLOYEE	employee	Hicks, Linda	1019	2022-09-20 14:10:08.482913+05:30	2022-09-20 14:10:08.48295+05:30	1	\N	{"email": "linda@demo.com", "full_name": "Hicks, Linda", "location_id": null, "department_id": "500"}	f
747	EMPLOYEE	employee	Lee, Thomas	1020	2022-09-20 14:10:08.483222+05:30	2022-09-20 14:10:08.48326+05:30	1	\N	{"email": "thomas@demo.com", "full_name": "Lee, Thomas", "location_id": null, "department_id": "100"}	f
748	EMPLOYEE	employee	Ryan Gallagher	Ryan Gallagher	2022-09-20 14:10:08.483351+05:30	2022-09-20 14:10:08.483391+05:30	1	\N	{"email": "approver1@fylefordashboard2.com", "full_name": "Ryan Gallagher", "location_id": "600", "department_id": "300"}	f
749	EMPLOYEE	employee	Joshua Wood	Joshua Wood	2022-09-20 14:10:08.483463+05:30	2022-09-20 14:10:08.483487+05:30	1	\N	{"email": "user1@fylefordashboard2.com", "full_name": "Joshua Wood", "location_id": "600", "department_id": "300"}	f
750	EMPLOYEE	employee	Matthew Estrada	Matthew Estrada	2022-09-20 14:10:08.50909+05:30	2022-09-20 14:10:08.509257+05:30	1	\N	{"email": "user10@fylefordashboard2.com", "full_name": "Matthew Estrada", "location_id": "600", "department_id": "300"}	f
751	EMPLOYEE	employee	Natalie Pope	Natalie Pope	2022-09-20 14:10:08.509332+05:30	2022-09-20 14:10:08.509362+05:30	1	\N	{"email": "user3@fylefordashboard2.com", "full_name": "Natalie Pope", "location_id": "600", "department_id": "300"}	f
752	EMPLOYEE	employee	Harman	1100	2022-09-20 14:10:08.50943+05:30	2022-09-20 14:10:08.509459+05:30	1	\N	{"email": "expensify@thatharmansingh.com", "full_name": "Harman", "location_id": "600", "department_id": null}	f
753	EMPLOYEE	employee	Theresa Brown	Theresa Brown	2022-09-20 14:10:08.509526+05:30	2022-09-20 14:10:08.509555+05:30	1	\N	{"email": "admin1@fyleforfyle.cleanup", "full_name": "Theresa Brown", "location_id": null, "department_id": "300"}	f
754	EMPLOYEE	employee	uchicha, itachi	1101	2022-09-20 14:10:08.509622+05:30	2022-09-20 14:10:08.509651+05:30	1	\N	{"email": null, "full_name": "uchicha, itachi", "location_id": "600", "department_id": null}	f
933	ITEM	item	Billable Expenses	1004	2022-09-20 14:10:22.463786+05:30	2022-09-20 14:10:22.463827+05:30	1	\N	\N	f
934	ITEM	item	Subcontractor Expenses	1005	2022-09-20 14:10:22.463883+05:30	2022-09-20 14:10:22.463911+05:30	1	\N	\N	f
935	ITEM	item	Project Fee	1003	2022-09-20 14:10:22.463963+05:30	2022-09-20 14:10:22.46399+05:30	1	\N	\N	f
936	ITEM	item	Service 1	1001	2022-09-20 14:10:22.464043+05:30	2022-09-20 14:10:22.46407+05:30	1	\N	\N	f
937	ITEM	item	Service 2	1002	2022-09-20 14:10:22.464123+05:30	2022-09-20 14:10:22.464162+05:30	1	\N	\N	f
938	ITEM	item	Cube	1012	2022-09-20 14:10:22.464438+05:30	2022-09-20 14:10:22.464576+05:30	1	\N	\N	f
939	ITEM	item	This is added by L	321	2022-09-20 14:10:22.464713+05:30	2022-09-20 14:10:22.464745+05:30	1	\N	\N	f
940	ITEM	item	New item to be added	1011	2022-09-20 14:10:22.464804+05:30	2022-09-20 14:10:22.464833+05:30	1	\N	\N	f
941	TEAM	team	CCC	10003	2022-09-20 14:10:27.76449+05:30	2022-09-20 14:10:27.764531+05:30	1	\N	\N	f
942	TEAM	team	Integrations	10002	2022-09-20 14:10:27.764587+05:30	2022-09-20 14:10:27.764615+05:30	1	\N	\N	f
943	VENDOR	vendor	test Sharma	test Sharma	2022-09-29 17:39:25.990678+05:30	2022-09-29 17:39:25.99074+05:30	1	\N	{"email": "test@fyle.in"}	f
755	ACCOUNT	account	Patents & Licenses	16200	2022-09-20 14:10:13.410332+05:30	2022-09-20 14:10:13.410376+05:30	1	t	{"account_type": "balancesheet"}	f
756	ACCOUNT	account	Bank Charges	60600	2022-09-20 14:10:13.410441+05:30	2022-09-20 14:10:13.41047+05:30	1	t	{"account_type": "incomestatement"}	f
757	ACCOUNT	account	COGS - Sales	50100	2022-09-20 14:10:13.410527+05:30	2022-09-20 14:10:13.410555+05:30	1	t	{"account_type": "incomestatement"}	f
758	ACCOUNT	account	Employee Benefits	60110	2022-09-20 14:10:13.410612+05:30	2022-09-20 14:10:13.41064+05:30	1	t	{"account_type": "incomestatement"}	f
759	ACCOUNT	account	Commission	60120	2022-09-20 14:10:13.410695+05:30	2022-09-20 14:10:13.410723+05:30	1	t	{"account_type": "incomestatement"}	f
760	ACCOUNT	account	Office Supplies	60340	2022-09-20 14:10:13.410778+05:30	2022-09-20 14:10:13.410806+05:30	1	t	{"account_type": "incomestatement"}	f
761	ACCOUNT	account	Rent	60300	2022-09-20 14:10:13.410861+05:30	2022-09-20 14:10:13.410889+05:30	1	t	{"account_type": "incomestatement"}	f
762	ACCOUNT	account	COGS - Subcontractors	50300	2022-09-20 14:10:13.410944+05:30	2022-09-20 14:10:13.410971+05:30	1	t	{"account_type": "incomestatement"}	f
763	ACCOUNT	account	Contract Usage - Unbilled	40800-101	2022-09-20 14:10:13.411026+05:30	2022-09-20 14:10:13.411054+05:30	1	t	{"account_type": "incomestatement"}	f
764	ACCOUNT	account	Contract Usage - Billed	40800-102	2022-09-20 14:10:13.411108+05:30	2022-09-20 14:10:13.411387+05:30	1	t	{"account_type": "incomestatement"}	f
765	ACCOUNT	account	Contract Subscriptions - Unbilled	40600-101	2022-09-20 14:10:13.411479+05:30	2022-09-20 14:10:13.411508+05:30	1	t	{"account_type": "incomestatement"}	f
766	ACCOUNT	account	OE Subscriptions	40500	2022-09-20 14:10:13.411563+05:30	2022-09-20 14:10:13.411591+05:30	1	t	{"account_type": "incomestatement"}	f
767	ACCOUNT	account	Contract Subscriptions	40600	2022-09-20 14:10:13.411645+05:30	2022-09-20 14:10:13.411673+05:30	1	t	{"account_type": "incomestatement"}	f
768	ACCOUNT	account	Contract Usage	40800	2022-09-20 14:10:13.411727+05:30	2022-09-20 14:10:13.411754+05:30	1	t	{"account_type": "incomestatement"}	f
769	ACCOUNT	account	Contract Subscriptions - Billed	40600-102	2022-09-20 14:10:13.411808+05:30	2022-09-20 14:10:13.411835+05:30	1	t	{"account_type": "incomestatement"}	f
770	ACCOUNT	account	Contract Usage - Paid	40800-103	2022-09-20 14:10:13.411889+05:30	2022-09-20 14:10:13.411916+05:30	1	t	{"account_type": "incomestatement"}	f
771	ACCOUNT	account	Contract Subscriptions - Paid	40600-103	2022-09-20 14:10:13.41197+05:30	2022-09-20 14:10:13.411998+05:30	1	t	{"account_type": "incomestatement"}	f
772	ACCOUNT	account	Contract Services - Billed	40700-102	2022-09-20 14:10:13.412052+05:30	2022-09-20 14:10:13.412079+05:30	1	t	{"account_type": "incomestatement"}	f
773	ACCOUNT	account	Revenue - Services	40100	2022-09-20 14:10:13.412261+05:30	2022-09-20 14:10:13.412299+05:30	1	t	{"account_type": "incomestatement"}	f
774	ACCOUNT	account	Revenue - Subcontractors	40300	2022-09-20 14:10:13.412353+05:30	2022-09-20 14:10:13.41238+05:30	1	t	{"account_type": "incomestatement"}	f
775	ACCOUNT	account	Contract Services - Paid	40700-103	2022-09-20 14:10:13.412435+05:30	2022-09-20 14:10:13.412462+05:30	1	t	{"account_type": "incomestatement"}	f
776	ACCOUNT	account	Revenue - Reimbursed Expenses	40200	2022-09-20 14:10:13.412516+05:30	2022-09-20 14:10:13.412543+05:30	1	t	{"account_type": "incomestatement"}	f
777	ACCOUNT	account	Contract Services	40700	2022-09-20 14:10:13.412597+05:30	2022-09-20 14:10:13.412624+05:30	1	t	{"account_type": "incomestatement"}	f
778	ACCOUNT	account	Contract Services - Unbilled	40700-101	2022-09-20 14:10:13.412678+05:30	2022-09-20 14:10:13.412705+05:30	1	t	{"account_type": "incomestatement"}	f
779	ACCOUNT	account	Spot Bonus	60150	2022-09-20 14:10:13.412759+05:30	2022-09-20 14:10:13.412787+05:30	1	t	{"account_type": "incomestatement"}	f
780	ACCOUNT	account	CTA	36000	2022-09-20 14:10:13.41284+05:30	2022-09-20 14:10:13.412868+05:30	1	t	{"account_type": "balancesheet"}	f
781	ACCOUNT	account	COGS - Other	50900	2022-09-20 14:10:13.412922+05:30	2022-09-20 14:10:13.41295+05:30	1	t	{"account_type": "incomestatement"}	f
782	ACCOUNT	account	Allowance For Doubtful Accounts	12200	2022-09-20 14:10:13.413004+05:30	2022-09-20 14:10:13.413032+05:30	1	t	{"account_type": "balancesheet"}	f
783	ACCOUNT	account	Prepaid Insurance	14100	2022-09-20 14:10:13.413085+05:30	2022-09-20 14:10:13.413113+05:30	1	t	{"account_type": "balancesheet"}	f
784	ACCOUNT	account	Prepaid Rent	14200	2022-09-20 14:10:13.413405+05:30	2022-09-20 14:10:13.413435+05:30	1	t	{"account_type": "balancesheet"}	f
785	ACCOUNT	account	Prepaid Other	14300	2022-09-20 14:10:13.413489+05:30	2022-09-20 14:10:13.413517+05:30	1	t	{"account_type": "balancesheet"}	f
786	ACCOUNT	account	Employee Advances	12500	2022-09-20 14:10:13.413571+05:30	2022-09-20 14:10:13.413598+05:30	1	t	{"account_type": "balancesheet"}	f
787	ACCOUNT	account	Accrued Expense	20600	2022-09-20 14:10:13.413652+05:30	2022-09-20 14:10:13.41368+05:30	1	t	{"account_type": "balancesheet"}	f
788	ACCOUNT	account	Inventory - GRNI	20680	2022-09-20 14:10:13.413734+05:30	2022-09-20 14:10:13.413761+05:30	1	t	{"account_type": "balancesheet"}	f
789	ACCOUNT	account	Accrued Payroll Tax Payable	20650	2022-09-20 14:10:13.413815+05:30	2022-09-20 14:10:13.413843+05:30	1	t	{"account_type": "balancesheet"}	f
790	ACCOUNT	account	Accr. Sales Tax Payable	20610	2022-09-20 14:10:13.413896+05:30	2022-09-20 14:10:13.413924+05:30	1	t	{"account_type": "balancesheet"}	f
791	ACCOUNT	account	Bad Debt Expense	60650	2022-09-20 14:10:13.413979+05:30	2022-09-20 14:10:13.414006+05:30	1	t	{"account_type": "incomestatement"}	f
792	ACCOUNT	account	Travel	60200	2022-09-20 14:10:13.41406+05:30	2022-09-20 14:10:13.414087+05:30	1	t	{"account_type": "incomestatement"}	f
793	ACCOUNT	account	Interest Expense	70200	2022-09-20 14:10:13.414297+05:30	2022-09-20 14:10:13.414327+05:30	1	t	{"account_type": "incomestatement"}	f
794	ACCOUNT	account	Other G&A	60660	2022-09-20 14:10:13.414386+05:30	2022-09-20 14:10:13.414415+05:30	1	t	{"account_type": "incomestatement"}	f
795	ACCOUNT	account	Currency Gain-Loss	70500	2022-09-20 14:10:13.414472+05:30	2022-09-20 14:10:13.414511+05:30	1	t	{"account_type": "incomestatement"}	f
796	ACCOUNT	account	Telecommunications	60220	2022-09-20 14:10:13.414566+05:30	2022-09-20 14:10:13.414593+05:30	1	t	{"account_type": "incomestatement"}	f
797	ACCOUNT	account	Valuation Reserves	13500	2022-09-20 14:10:13.414647+05:30	2022-09-20 14:10:13.414674+05:30	1	t	{"account_type": "balancesheet"}	f
798	ACCOUNT	account	Goodwill	16100	2022-09-20 14:10:13.414728+05:30	2022-09-20 14:10:13.414768+05:30	1	t	{"account_type": "balancesheet"}	f
799	ACCOUNT	account	Depreciation Expense	60630	2022-09-20 14:10:13.414918+05:30	2022-09-20 14:10:13.414953+05:30	1	t	{"account_type": "incomestatement"}	f
800	ACCOUNT	account	Printing and Reproduction	60360	2022-09-20 14:10:13.41501+05:30	2022-09-20 14:10:13.415038+05:30	1	t	{"account_type": "incomestatement"}	f
801	ACCOUNT	account	Notes Payable	20200	2022-09-20 14:10:13.415092+05:30	2022-09-20 14:10:13.415141+05:30	1	t	{"account_type": "balancesheet"}	f
802	ACCOUNT	account	Long Term Debt	20400	2022-09-20 14:10:13.415323+05:30	2022-09-20 14:10:13.415351+05:30	1	t	{"account_type": "balancesheet"}	f
803	ACCOUNT	account	Unrealized Currency Gain and Loss	30310	2022-09-20 14:10:13.415405+05:30	2022-09-20 14:10:13.415433+05:30	1	t	{"account_type": "balancesheet"}	f
804	ACCOUNT	account	Trade Shows and Exhibits	60510	2022-09-20 14:10:13.415487+05:30	2022-09-20 14:10:13.415515+05:30	1	t	{"account_type": "incomestatement"}	f
805	ACCOUNT	account	Marketing and Advertising	60500	2022-09-20 14:10:13.422642+05:30	2022-09-20 14:10:13.422714+05:30	1	t	{"account_type": "incomestatement"}	f
806	ACCOUNT	account	Insurance	60330	2022-09-20 14:10:13.422839+05:30	2022-09-20 14:10:13.423003+05:30	1	t	{"account_type": "incomestatement"}	f
807	ACCOUNT	account	Meals and Entertainment	60210	2022-09-20 14:10:13.423097+05:30	2022-09-20 14:10:13.423151+05:30	1	t	{"account_type": "incomestatement"}	f
808	ACCOUNT	account	Postage and Delivery	60350	2022-09-20 14:10:13.423343+05:30	2022-09-20 14:10:13.423371+05:30	1	t	{"account_type": "incomestatement"}	f
809	ACCOUNT	account	Professional Fees Expense	60410	2022-09-20 14:10:13.423427+05:30	2022-09-20 14:10:13.423454+05:30	1	t	{"account_type": "incomestatement"}	f
810	ACCOUNT	account	Repairs and Maintenance	60320	2022-09-20 14:10:13.42351+05:30	2022-09-20 14:10:13.423538+05:30	1	t	{"account_type": "incomestatement"}	f
811	ACCOUNT	account	Salaries and Wages	60100	2022-09-20 14:10:13.423593+05:30	2022-09-20 14:10:13.42362+05:30	1	t	{"account_type": "incomestatement"}	f
812	ACCOUNT	account	Gain for Sale of an Asset	80500	2022-09-20 14:10:13.423675+05:30	2022-09-20 14:10:13.423702+05:30	1	t	{"account_type": "incomestatement"}	f
813	ACCOUNT	account	Dividends	80400	2022-09-20 14:10:13.423757+05:30	2022-09-20 14:10:13.423784+05:30	1	t	{"account_type": "incomestatement"}	f
814	ACCOUNT	account	Cash	10100	2022-09-20 14:10:13.423839+05:30	2022-09-20 14:10:13.423866+05:30	1	t	{"account_type": "balancesheet"}	f
815	ACCOUNT	account	Checking 4 - Bank Of Canada	10040	2022-09-20 14:10:13.423921+05:30	2022-09-20 14:10:13.423949+05:30	1	t	{"account_type": "balancesheet"}	f
816	ACCOUNT	account	Checking 5 - Bank Of England	10050	2022-09-20 14:10:13.424113+05:30	2022-09-20 14:10:13.424153+05:30	1	t	{"account_type": "balancesheet"}	f
817	ACCOUNT	account	Checking 6 - Bank Of Australia	10060	2022-09-20 14:10:13.424219+05:30	2022-09-20 14:10:13.424368+05:30	1	t	{"account_type": "balancesheet"}	f
818	ACCOUNT	account	Checking 7 - Bank Of South Africa	10070	2022-09-20 14:10:13.424435+05:30	2022-09-20 14:10:13.424463+05:30	1	t	{"account_type": "balancesheet"}	f
819	ACCOUNT	account	Investments and Securities	10400	2022-09-20 14:10:13.424517+05:30	2022-09-20 14:10:13.424545+05:30	1	t	{"account_type": "balancesheet"}	f
820	ACCOUNT	account	Checking 1 - SVB	10010	2022-09-20 14:10:13.424599+05:30	2022-09-20 14:10:13.424627+05:30	1	t	{"account_type": "balancesheet"}	f
821	ACCOUNT	account	Checking 2 - SVB	10020	2022-09-20 14:10:13.42468+05:30	2022-09-20 14:10:13.424708+05:30	1	t	{"account_type": "balancesheet"}	f
822	ACCOUNT	account	Checking 3 - SVB	10030	2022-09-20 14:10:13.424762+05:30	2022-09-20 14:10:13.42479+05:30	1	t	{"account_type": "balancesheet"}	f
823	ACCOUNT	account	Due from Entity 400	12900-400	2022-09-20 14:10:13.424844+05:30	2022-09-20 14:10:13.424871+05:30	1	t	{"account_type": "balancesheet"}	f
824	ACCOUNT	account	Due from Entity 700	12900-700	2022-09-20 14:10:13.424925+05:30	2022-09-20 14:10:13.424952+05:30	1	t	{"account_type": "balancesheet"}	f
825	ACCOUNT	account	Due from Entity 600	12900-600	2022-09-20 14:10:13.425005+05:30	2022-09-20 14:10:13.425033+05:30	1	t	{"account_type": "balancesheet"}	f
826	ACCOUNT	account	Due from Entity 500	12900-500	2022-09-20 14:10:13.425086+05:30	2022-09-20 14:10:13.425328+05:30	1	t	{"account_type": "balancesheet"}	f
827	ACCOUNT	account	Due from Entity 200	12900-200	2022-09-20 14:10:13.425398+05:30	2022-09-20 14:10:13.425426+05:30	1	t	{"account_type": "balancesheet"}	f
828	ACCOUNT	account	Due from Entity 300	12900-300	2022-09-20 14:10:13.425479+05:30	2022-09-20 14:10:13.425507+05:30	1	t	{"account_type": "balancesheet"}	f
829	ACCOUNT	account	Due from Entity 100	12900-100	2022-09-20 14:10:13.425595+05:30	2022-09-20 14:10:13.425662+05:30	1	t	{"account_type": "balancesheet"}	f
830	ACCOUNT	account	Intercompany Receivables	12900	2022-09-20 14:10:13.425753+05:30	2022-09-20 14:10:13.425774+05:30	1	t	{"account_type": "balancesheet"}	f
831	ACCOUNT	account	Unbilled AR - Contract Services	12701-200	2022-09-20 14:10:13.425824+05:30	2022-09-20 14:10:13.425854+05:30	1	t	{"account_type": "balancesheet"}	f
832	ACCOUNT	account	Unbilled AR - Contract Usage	12701-300	2022-09-20 14:10:13.425909+05:30	2022-09-20 14:10:13.425927+05:30	1	t	{"account_type": "balancesheet"}	f
833	ACCOUNT	account	Deferred Expense - Commission	17710-001	2022-09-20 14:10:13.425973+05:30	2022-09-20 14:10:13.426002+05:30	1	t	{"account_type": "balancesheet"}	f
834	ACCOUNT	account	Deferred Expense - Royalty	17710-002	2022-09-20 14:10:13.426059+05:30	2022-09-20 14:10:13.426178+05:30	1	t	{"account_type": "balancesheet"}	f
835	ACCOUNT	account	Tax Receivable	12620	2022-09-20 14:10:13.426227+05:30	2022-09-20 14:10:13.426248+05:30	1	t	{"account_type": "balancesheet"}	f
836	ACCOUNT	account	Deferred Expense	17710	2022-09-20 14:10:13.426305+05:30	2022-09-20 14:10:13.426335+05:30	1	t	{"account_type": "balancesheet"}	f
837	ACCOUNT	account	Unbilled AR - Contract Subscriptions	12701-100	2022-09-20 14:10:13.426688+05:30	2022-09-20 14:10:13.426707+05:30	1	t	{"account_type": "balancesheet"}	f
838	ACCOUNT	account	WIP (Labor Only)	12600	2022-09-20 14:10:13.426754+05:30	2022-09-20 14:10:13.426778+05:30	1	t	{"account_type": "balancesheet"}	f
839	ACCOUNT	account	Unbilled AR	12701	2022-09-20 14:10:13.426822+05:30	2022-09-20 14:10:13.426837+05:30	1	t	{"account_type": "balancesheet"}	f
840	ACCOUNT	account	Buildings Accm. Depr.	15110	2022-09-20 14:10:13.426883+05:30	2022-09-20 14:10:13.426922+05:30	1	t	{"account_type": "balancesheet"}	f
841	ACCOUNT	account	Capitalized Software Costs	16300	2022-09-20 14:10:13.427102+05:30	2022-09-20 14:10:13.427141+05:30	1	t	{"account_type": "balancesheet"}	f
842	ACCOUNT	account	Buildings	15100	2022-09-20 14:10:13.427196+05:30	2022-09-20 14:10:13.427223+05:30	1	t	{"account_type": "balancesheet"}	f
843	ACCOUNT	account	DR - Contract Subscriptions - Unbilled	20701-101	2022-09-20 14:10:13.427278+05:30	2022-09-20 14:10:13.427305+05:30	1	t	{"account_type": "balancesheet"}	f
844	ACCOUNT	account	DR - Contract Usage - Unbilled	20701-301	2022-09-20 14:10:13.427359+05:30	2022-09-20 14:10:13.427387+05:30	1	t	{"account_type": "balancesheet"}	f
845	ACCOUNT	account	DR - Contract Subscriptions - Billed	20701-102	2022-09-20 14:10:13.427441+05:30	2022-09-20 14:10:13.427468+05:30	1	t	{"account_type": "balancesheet"}	f
846	ACCOUNT	account	DR - Contract Services - Billed	20701-202	2022-09-20 14:10:13.427522+05:30	2022-09-20 14:10:13.42755+05:30	1	t	{"account_type": "balancesheet"}	f
847	ACCOUNT	account	DR - Contract Usage - Billed	20701-302	2022-09-20 14:10:13.427637+05:30	2022-09-20 14:10:13.427727+05:30	1	t	{"account_type": "balancesheet"}	f
848	ACCOUNT	account	DR - Contract Usage - Paid	20701-303	2022-09-20 14:10:13.427793+05:30	2022-09-20 14:10:13.427821+05:30	1	t	{"account_type": "balancesheet"}	f
849	ACCOUNT	account	DR - Contract Services - Paid	20701-203	2022-09-20 14:10:13.427875+05:30	2022-09-20 14:10:13.427903+05:30	1	t	{"account_type": "balancesheet"}	f
850	ACCOUNT	account	DR - Contract Subscriptions - Paid	20701-103	2022-09-20 14:10:13.427957+05:30	2022-09-20 14:10:13.427985+05:30	1	t	{"account_type": "balancesheet"}	f
851	ACCOUNT	account	DR - Contract Services - Unbilled	20701-201	2022-09-20 14:10:13.428038+05:30	2022-09-20 14:10:13.428066+05:30	1	t	{"account_type": "balancesheet"}	f
852	ACCOUNT	account	Deferred Revenue Contra	20702	2022-09-20 14:10:13.42812+05:30	2022-09-20 14:10:13.428147+05:30	1	t	{"account_type": "balancesheet"}	f
853	ACCOUNT	account	Deferred Revenue	20701	2022-09-20 14:10:13.428318+05:30	2022-09-20 14:10:13.428346+05:30	1	t	{"account_type": "balancesheet"}	f
854	ACCOUNT	account	Due to Entity 700	20900-700	2022-09-20 14:10:13.428399+05:30	2022-09-20 14:10:13.428427+05:30	1	t	{"account_type": "balancesheet"}	f
855	ACCOUNT	account	Due to Entity 500	20900-500	2022-09-20 14:10:13.434257+05:30	2022-09-20 14:10:13.4343+05:30	1	t	{"account_type": "balancesheet"}	f
856	ACCOUNT	account	Due to Entity 400	20900-400	2022-09-20 14:10:13.434366+05:30	2022-09-20 14:10:13.434395+05:30	1	t	{"account_type": "balancesheet"}	f
857	ACCOUNT	account	Due to Entity 600	20900-600	2022-09-20 14:10:13.434453+05:30	2022-09-20 14:10:13.434481+05:30	1	t	{"account_type": "balancesheet"}	f
858	ACCOUNT	account	Due to Entity 300	20900-300	2022-09-20 14:10:13.434538+05:30	2022-09-20 14:10:13.434566+05:30	1	t	{"account_type": "balancesheet"}	f
859	ACCOUNT	account	Due to Entity 100	20900-100	2022-09-20 14:10:13.434622+05:30	2022-09-20 14:10:13.43465+05:30	1	t	{"account_type": "balancesheet"}	f
860	ACCOUNT	account	Due to Entity 200	20900-200	2022-09-20 14:10:13.434705+05:30	2022-09-20 14:10:13.434733+05:30	1	t	{"account_type": "balancesheet"}	f
861	ACCOUNT	account	Intercompany Payables	20900	2022-09-20 14:10:13.434788+05:30	2022-09-20 14:10:13.434815+05:30	1	t	{"account_type": "balancesheet"}	f
862	ACCOUNT	account	Interest Income	80200	2022-09-20 14:10:13.43487+05:30	2022-09-20 14:10:13.434898+05:30	1	t	{"account_type": "incomestatement"}	f
863	ACCOUNT	account	Journal Entry Rounding	70400	2022-09-20 14:10:13.434953+05:30	2022-09-20 14:10:13.43498+05:30	1	t	{"account_type": "incomestatement"}	f
864	ACCOUNT	account	Intercompany Professional Fees	40400	2022-09-20 14:10:13.435035+05:30	2022-09-20 14:10:13.435062+05:30	1	t	{"account_type": "incomestatement"}	f
865	ACCOUNT	account	Accumulated OCI	30300	2022-09-20 14:10:13.435117+05:30	2022-09-20 14:10:13.435773+05:30	1	t	{"account_type": "balancesheet"}	f
866	ACCOUNT	account	Amortization Expense	60640	2022-09-20 14:10:13.43647+05:30	2022-09-20 14:10:13.436515+05:30	1	t	{"account_type": "incomestatement"}	f
867	ACCOUNT	account	Revenue - Other	40900	2022-09-20 14:10:13.436692+05:30	2022-09-20 14:10:13.436726+05:30	1	t	{"account_type": "incomestatement"}	f
868	ACCOUNT	account	Employee Deductions	60140	2022-09-20 14:10:13.436794+05:30	2022-09-20 14:10:13.436824+05:30	1	t	{"account_type": "incomestatement"}	f
869	ACCOUNT	account	Payroll Taxes	60130	2022-09-20 14:10:13.436889+05:30	2022-09-20 14:10:13.436919+05:30	1	t	{"account_type": "incomestatement"}	f
870	ACCOUNT	account	Other Taxes	60620	2022-09-20 14:10:13.43698+05:30	2022-09-20 14:10:13.43701+05:30	1	t	{"account_type": "incomestatement"}	f
871	ACCOUNT	account	Excise Tax	60610	2022-09-20 14:10:13.437256+05:30	2022-09-20 14:10:13.437289+05:30	1	t	{"account_type": "incomestatement"}	f
872	ACCOUNT	account	Reserved Inventory	13400	2022-09-20 14:10:13.437352+05:30	2022-09-20 14:10:13.437381+05:30	1	t	{"account_type": "balancesheet"}	f
873	ACCOUNT	account	Supplies	13300	2022-09-20 14:10:13.437443+05:30	2022-09-20 14:10:13.437473+05:30	1	t	{"account_type": "balancesheet"}	f
874	ACCOUNT	account	Goods in Transit	13200	2022-09-20 14:10:13.437558+05:30	2022-09-20 14:10:13.437602+05:30	1	t	{"account_type": "balancesheet"}	f
875	ACCOUNT	account	Inventory	13100	2022-09-20 14:10:13.437946+05:30	2022-09-20 14:10:13.438066+05:30	1	t	{"account_type": "balancesheet"}	f
876	ACCOUNT	account	Inventory - Other	13900	2022-09-20 14:10:13.43814+05:30	2022-09-20 14:10:13.438171+05:30	1	t	{"account_type": "balancesheet"}	f
877	ACCOUNT	account	Other Intangible Assets	16900	2022-09-20 14:10:13.438466+05:30	2022-09-20 14:10:13.438489+05:30	1	t	{"account_type": "balancesheet"}	f
878	ACCOUNT	account	Other Assets	17000	2022-09-20 14:10:13.43854+05:30	2022-09-20 14:10:13.438569+05:30	1	t	{"account_type": "balancesheet"}	f
879	ACCOUNT	account	Credit Card Offset	20500	2022-09-20 14:10:13.438632+05:30	2022-09-20 14:10:13.438655+05:30	1	t	{"account_type": "balancesheet"}	f
880	ACCOUNT	account	Sales Tax Payable	20620	2022-09-20 14:10:13.438713+05:30	2022-09-20 14:10:13.438742+05:30	1	t	{"account_type": "balancesheet"}	f
881	ACCOUNT	account	Common Stock	30100	2022-09-20 14:10:13.438801+05:30	2022-09-20 14:10:13.43884+05:30	1	t	{"account_type": "balancesheet"}	f
882	ACCOUNT	account	Preferred Stock	30200	2022-09-20 14:10:13.438895+05:30	2022-09-20 14:10:13.438922+05:30	1	t	{"account_type": "balancesheet"}	f
883	ACCOUNT	account	Retained Earnings	35000	2022-09-20 14:10:13.438987+05:30	2022-09-20 14:10:13.439129+05:30	1	t	{"account_type": "balancesheet"}	f
884	ACCOUNT	account	COGS - Materials	50200	2022-09-20 14:10:13.439188+05:30	2022-09-20 14:10:13.439227+05:30	1	t	{"account_type": "incomestatement"}	f
885	ACCOUNT	account	Paid Time Off	70303	2022-09-20 14:10:13.439282+05:30	2022-09-20 14:10:13.439309+05:30	1	t	{"account_type": "incomestatement"}	f
886	ACCOUNT	account	Indirect Labor	70300	2022-09-20 14:10:13.439364+05:30	2022-09-20 14:10:13.439391+05:30	1	t	{"account_type": "incomestatement"}	f
887	ACCOUNT	account	Holiday	70301	2022-09-20 14:10:13.439446+05:30	2022-09-20 14:10:13.439473+05:30	1	t	{"account_type": "incomestatement"}	f
888	ACCOUNT	account	Company Credit Card Offset	60700	2022-09-20 14:10:13.439527+05:30	2022-09-20 14:10:13.439555+05:30	1	t	{"account_type": "incomestatement"}	f
889	ACCOUNT	account	Other Expense	70100	2022-09-20 14:10:13.439609+05:30	2022-09-20 14:10:13.439636+05:30	1	t	{"account_type": "incomestatement"}	f
890	ACCOUNT	account	Professional Development	70302	2022-09-20 14:10:13.439691+05:30	2022-09-20 14:10:13.439719+05:30	1	t	{"account_type": "incomestatement"}	f
891	ACCOUNT	account	Indirect Labor Offset	70304	2022-09-20 14:10:13.439773+05:30	2022-09-20 14:10:13.439801+05:30	1	t	{"account_type": "incomestatement"}	f
892	ACCOUNT	account	Other Income	80100	2022-09-20 14:10:13.439855+05:30	2022-09-20 14:10:13.439883+05:30	1	t	{"account_type": "incomestatement"}	f
893	ACCOUNT	account	AR - Retainage	12710	2022-09-20 14:10:13.439937+05:30	2022-09-20 14:10:13.439965+05:30	1	t	{"account_type": "balancesheet"}	f
894	ACCOUNT	account	Accounts Receivable	12100	2022-09-20 14:10:13.440019+05:30	2022-09-20 14:10:13.440046+05:30	1	t	{"account_type": "balancesheet"}	f
895	ACCOUNT	account	Accounts Payable - Employees	20300	2022-09-20 14:10:13.4401+05:30	2022-09-20 14:10:13.440127+05:30	1	t	{"account_type": "balancesheet"}	f
896	ACCOUNT	account	Accounts Payable	20100	2022-09-20 14:10:13.440306+05:30	2022-09-20 14:10:13.440346+05:30	1	t	{"account_type": "balancesheet"}	f
897	ACCOUNT	account	Billable Overtime Hours	51708	2022-09-20 14:10:13.440401+05:30	2022-09-20 14:10:13.440428+05:30	1	t	{"account_type": "incomestatement"}	f
898	ACCOUNT	account	Non-Billable Overtime Hours	51709	2022-09-20 14:10:13.440482+05:30	2022-09-20 14:10:13.44051+05:30	1	t	{"account_type": "incomestatement"}	f
899	ACCOUNT	account	Billable Hours	51701	2022-09-20 14:10:13.440564+05:30	2022-09-20 14:10:13.440591+05:30	1	t	{"account_type": "incomestatement"}	f
900	ACCOUNT	account	Labor Cost Variance	51711	2022-09-20 14:10:13.440646+05:30	2022-09-20 14:10:13.440673+05:30	1	t	{"account_type": "incomestatement"}	f
901	ACCOUNT	account	Labor Cost Offset	51710	2022-09-20 14:10:13.440829+05:30	2022-09-20 14:10:13.440863+05:30	1	t	{"account_type": "incomestatement"}	f
902	ACCOUNT	account	Non-Billable Hours	51702	2022-09-20 14:10:13.440923+05:30	2022-09-20 14:10:13.440951+05:30	1	t	{"account_type": "incomestatement"}	f
903	ACCOUNT	account	COGS - Burden on Projects	51703	2022-09-20 14:10:13.441005+05:30	2022-09-20 14:10:13.441033+05:30	1	t	{"account_type": "incomestatement"}	f
904	ACCOUNT	account	COGS - Overhead on Projects	51704	2022-09-20 14:10:13.441087+05:30	2022-09-20 14:10:13.441257+05:30	1	t	{"account_type": "incomestatement"}	f
905	ACCOUNT	account	COGS - G&A on Projects	51705	2022-09-20 14:10:13.44715+05:30	2022-09-20 14:10:13.447201+05:30	1	t	{"account_type": "incomestatement"}	f
906	ACCOUNT	account	COGS - Indirect Projects Costs Offset	51706	2022-09-20 14:10:13.447282+05:30	2022-09-20 14:10:13.447329+05:30	1	t	{"account_type": "incomestatement"}	f
907	ACCOUNT	account	COGS - Reimbursed Expenses	51707	2022-09-20 14:10:13.447396+05:30	2022-09-20 14:10:13.447423+05:30	1	t	{"account_type": "incomestatement"}	f
908	ACCOUNT	account	Software and Licenses	60400	2022-09-20 14:10:13.447468+05:30	2022-09-20 14:10:13.447489+05:30	1	t	{"account_type": "incomestatement"}	f
909	ACCOUNT	account	Utilities	60310	2022-09-20 14:10:13.447542+05:30	2022-09-20 14:10:13.447553+05:30	1	t	{"account_type": "incomestatement"}	f
910	ACCOUNT	account	Downgrade	90006	2022-09-20 14:10:13.447601+05:30	2022-09-20 14:10:13.447626+05:30	1	t	{"account_type": "balancesheet"}	f
911	ACCOUNT	account	Contract Royalty Expense	50400	2022-09-20 14:10:13.447676+05:30	2022-09-20 14:10:13.447714+05:30	1	t	{"account_type": "incomestatement"}	f
912	ACCOUNT	account	Contract Commission	60160	2022-09-20 14:10:13.447769+05:30	2022-09-20 14:10:13.447796+05:30	1	t	{"account_type": "incomestatement"}	f
913	ACCOUNT	account	CMRR Offset	90009	2022-09-20 14:10:13.447851+05:30	2022-09-20 14:10:13.447878+05:30	1	t	{"account_type": "balancesheet"}	f
914	ACCOUNT	account	CMRR New	90002	2022-09-20 14:10:13.447932+05:30	2022-09-20 14:10:13.447959+05:30	1	t	{"account_type": "balancesheet"}	f
915	ACCOUNT	account	CMRR Add-On	90003	2022-09-20 14:10:13.448013+05:30	2022-09-20 14:10:13.44804+05:30	1	t	{"account_type": "balancesheet"}	f
916	ACCOUNT	account	Renewal Upgrade	90004	2022-09-20 14:10:13.448094+05:30	2022-09-20 14:10:13.448232+05:30	1	t	{"account_type": "balancesheet"}	f
917	ACCOUNT	account	Renewal Downgrade	90005	2022-09-20 14:10:13.448341+05:30	2022-09-20 14:10:13.44837+05:30	1	t	{"account_type": "balancesheet"}	f
918	ACCOUNT	account	CMRR Churn	90007	2022-09-20 14:10:13.448425+05:30	2022-09-20 14:10:13.448452+05:30	1	t	{"account_type": "balancesheet"}	f
919	ACCOUNT	account	CMRR Renewal	90008	2022-09-20 14:10:13.448506+05:30	2022-09-20 14:10:13.448533+05:30	1	t	{"account_type": "incomestatement"}	f
920	ACCOUNT	account	nilewh	12221	2022-09-20 14:10:13.448587+05:30	2022-09-20 14:10:13.448614+05:30	1	t	{"account_type": "balancesheet"}	f
921	ACCOUNT	account	Potential Billings	90000	2022-09-20 14:10:13.448668+05:30	2022-09-20 14:10:13.448695+05:30	1	t	{"account_type": "incomestatement"}	f
922	ACCOUNT	account	Potential Billings Offset	90001	2022-09-20 14:10:13.448749+05:30	2022-09-20 14:10:13.448776+05:30	1	t	{"account_type": "incomestatement"}	f
923	ACCOUNT	account	Elimination Adjustment	70600	2022-09-20 14:10:13.44883+05:30	2022-09-20 14:10:13.448857+05:30	1	t	{"account_type": "incomestatement"}	f
924	ACCOUNT	account	Transactor Clearing	12610	2022-09-20 14:10:13.448911+05:30	2022-09-20 14:10:13.448939+05:30	1	t	{"account_type": "balancesheet"}	f
925	EXPENSE_TYPE	Expense Types	Airfare	Airfare	2022-09-20 14:10:17.37637+05:30	2022-09-20 14:10:17.376416+05:30	1	t	{"gl_account_no": "60200", "gl_account_title": "Travel"}	f
926	EXPENSE_TYPE	Expense Types	Cell Phone	Cell Phone	2022-09-20 14:10:17.3765+05:30	2022-09-20 14:10:17.376531+05:30	1	t	{"gl_account_no": "60220", "gl_account_title": "Telecommunications"}	f
927	EXPENSE_TYPE	Expense Types	Ground Transportation-Parking	Ground Transportation/Parking	2022-09-20 14:10:17.376606+05:30	2022-09-20 14:10:17.376636+05:30	1	t	{"gl_account_no": "60200", "gl_account_title": "Travel"}	f
928	EXPENSE_TYPE	Expense Types	Hotel-Lodging	Hotel/Lodging	2022-09-20 14:10:17.376707+05:30	2022-09-20 14:10:17.376737+05:30	1	t	{"gl_account_no": "60200", "gl_account_title": "Travel"}	f
929	EXPENSE_TYPE	Expense Types	Internet	Internet	2022-09-20 14:10:17.376807+05:30	2022-09-20 14:10:17.376837+05:30	1	t	{"gl_account_no": "60220", "gl_account_title": "Telecommunications"}	f
930	EXPENSE_TYPE	Expense Types	Meals	Meals	2022-09-20 14:10:17.376906+05:30	2022-09-20 14:10:17.376936+05:30	1	t	{"gl_account_no": "60210", "gl_account_title": "Meals and Entertainment"}	f
931	EXPENSE_TYPE	Expense Types	Mileage	Mileage	2022-09-20 14:10:17.377005+05:30	2022-09-20 14:10:17.377034+05:30	1	t	{"gl_account_no": "60200", "gl_account_title": "Travel"}	f
932	EXPENSE_TYPE	Expense Types	Per Diem	Per Diem	2022-09-20 14:10:17.377104+05:30	2022-09-20 14:10:17.377134+05:30	1	t	{"gl_account_no": "60210", "gl_account_title": "Meals and Entertainment"}	f
\.


--
-- Data for Name: django_admin_log; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_admin_log (id, action_time, object_id, object_repr, action_flag, change_message, content_type_id, user_id) FROM stdin;
\.


--
-- Data for Name: django_content_type; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_content_type (id, app_label, model) FROM stdin;
1	admin	logentry
2	auth	permission
3	auth	group
4	contenttypes	contenttype
5	sessions	session
6	django_q	schedule
7	django_q	task
8	django_q	failure
9	django_q	success
10	django_q	ormq
11	fyle_rest_auth	authtoken
12	fyle_accounting_mappings	destinationattribute
13	fyle_accounting_mappings	expenseattribute
14	fyle_accounting_mappings	mappingsetting
15	fyle_accounting_mappings	mapping
16	fyle_accounting_mappings	employeemapping
17	fyle_accounting_mappings	categorymapping
18	users	user
19	workspaces	workspace
20	workspaces	sageintacctcredential
21	workspaces	fylecredential
22	workspaces	workspaceschedule
23	workspaces	configuration
24	fyle	expense
25	fyle	expensegroup
26	fyle	expensegroupsettings
27	fyle	reimbursement
28	sage_intacct	bill
29	sage_intacct	billlineitem
30	sage_intacct	expensereport
31	sage_intacct	expensereportlineitem
32	sage_intacct	chargecardtransaction
33	sage_intacct	chargecardtransactionlineitem
34	sage_intacct	appayment
35	sage_intacct	sageintacctreimbursement
36	sage_intacct	sageintacctreimbursementlineitem
37	sage_intacct	appaymentlineitem
38	sage_intacct	journalentry
39	sage_intacct	journalentrylineitem
40	tasks	tasklog
41	mappings	generalmapping
42	mappings	locationentitymapping
43	fyle_accounting_mappings	expensefield
\.


--
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_migrations (id, app, name, applied) FROM stdin;
1	users	0001_initial	2022-09-20 14:04:11.41152+05:30
2	contenttypes	0001_initial	2022-09-20 14:04:11.458906+05:30
3	admin	0001_initial	2022-09-20 14:04:11.499803+05:30
4	admin	0002_logentry_remove_auto_add	2022-09-20 14:04:11.537556+05:30
5	admin	0003_logentry_add_action_flag_choices	2022-09-20 14:04:11.553518+05:30
6	contenttypes	0002_remove_content_type_name	2022-09-20 14:04:11.594614+05:30
7	auth	0001_initial	2022-09-20 14:04:11.66851+05:30
8	auth	0002_alter_permission_name_max_length	2022-09-20 14:04:11.772457+05:30
9	auth	0003_alter_user_email_max_length	2022-09-20 14:04:11.785856+05:30
10	auth	0004_alter_user_username_opts	2022-09-20 14:04:11.79923+05:30
11	auth	0005_alter_user_last_login_null	2022-09-20 14:04:11.813922+05:30
12	auth	0006_require_contenttypes_0002	2022-09-20 14:04:11.821155+05:30
13	auth	0007_alter_validators_add_error_messages	2022-09-20 14:04:11.832817+05:30
14	auth	0008_alter_user_username_max_length	2022-09-20 14:04:11.850937+05:30
15	auth	0009_alter_user_last_name_max_length	2022-09-20 14:04:11.866633+05:30
16	auth	0010_alter_group_name_max_length	2022-09-20 14:04:11.891971+05:30
17	auth	0011_update_proxy_permissions	2022-09-20 14:04:11.949357+05:30
18	auth	0012_alter_user_first_name_max_length	2022-09-20 14:04:11.963037+05:30
19	django_q	0001_initial	2022-09-20 14:04:12.013497+05:30
20	django_q	0002_auto_20150630_1624	2022-09-20 14:04:12.060451+05:30
21	django_q	0003_auto_20150708_1326	2022-09-20 14:04:12.138208+05:30
22	django_q	0004_auto_20150710_1043	2022-09-20 14:04:12.210579+05:30
23	django_q	0005_auto_20150718_1506	2022-09-20 14:04:12.291295+05:30
24	django_q	0006_auto_20150805_1817	2022-09-20 14:04:12.340214+05:30
25	django_q	0007_ormq	2022-09-20 14:04:12.391175+05:30
26	django_q	0008_auto_20160224_1026	2022-09-20 14:04:12.402713+05:30
27	django_q	0009_auto_20171009_0915	2022-09-20 14:04:12.438764+05:30
28	django_q	0010_auto_20200610_0856	2022-09-20 14:04:12.464173+05:30
29	django_q	0011_auto_20200628_1055	2022-09-20 14:04:12.47932+05:30
30	django_q	0012_auto_20200702_1608	2022-09-20 14:04:12.490963+05:30
31	django_q	0013_task_attempt_count	2022-09-20 14:04:12.50976+05:30
32	workspaces	0001_initial	2022-09-20 14:04:12.698353+05:30
33	workspaces	0002_ccc	2022-09-20 14:04:12.813643+05:30
34	workspaces	0003_workspaceschedule	2022-09-20 14:04:12.937659+05:30
35	workspaces	0004_auto_20201228_0802	2022-09-20 14:04:12.977791+05:30
36	workspaces	0005_workspacegeneralsettings_import_projects	2022-09-20 14:04:13.010722+05:30
37	workspaces	0006_auto_20210208_0548	2022-09-20 14:04:13.042948+05:30
38	workspaces	0007_workspacegeneralsettings_auto_map_employees	2022-09-20 14:04:13.059131+05:30
39	workspaces	0008_workspacegeneralsettings_import_categories	2022-09-20 14:04:13.078101+05:30
40	workspaces	0009_workspacegeneralsettings_auto_create_destination_entity	2022-09-20 14:04:13.108958+05:30
41	workspaces	0010_auto_20210422_0817	2022-09-20 14:04:13.159052+05:30
42	workspaces	0011_workspace_cluster_domain	2022-09-20 14:04:13.192296+05:30
43	workspaces	0012_auto_20210723_0925	2022-09-20 14:04:13.249349+05:30
44	workspaces	0013_auto_20210723_1010	2022-09-20 14:04:13.301691+05:30
45	fyle	0001_initial	2022-09-20 14:04:13.436677+05:30
46	fyle	0002_fund_source	2022-09-20 14:04:13.786046+05:30
47	fyle	0003_expensegroup_exported_at	2022-09-20 14:04:13.826998+05:30
48	fyle	0004_auto_20201209_0558	2022-09-20 14:04:14.025983+05:30
49	fyle	0005_expense_billable	2022-09-20 14:04:14.045523+05:30
50	fyle	0006_auto_20210208_0548	2022-09-20 14:04:14.157745+05:30
51	fyle	0007_expense_org_id	2022-09-20 14:04:14.190587+05:30
52	fyle	0008_reimbursement_payment_number	2022-09-20 14:04:14.213617+05:30
53	fyle	0009_auto_20210917_0822	2022-09-20 14:04:14.239619+05:30
54	fyle	0010_auto_20211001_0525	2022-09-20 14:04:14.313223+05:30
55	fyle	0011_auto_20211203_1156	2022-09-20 14:04:14.396928+05:30
56	fyle	0012_auto_20220210_1106	2022-09-20 14:04:14.418038+05:30
57	fyle	0013_auto_20220510_1635	2022-09-20 14:04:14.456936+05:30
58	fyle	0014_expensegroupsettings_import_card_credits	2022-09-20 14:04:14.481284+05:30
59	fyle_accounting_mappings	0001_initial	2022-09-20 14:04:14.733253+05:30
60	fyle_accounting_mappings	0002_auto_20201117_0655	2022-09-20 14:04:15.21232+05:30
61	fyle_accounting_mappings	0003_auto_20201221_1244	2022-09-20 14:04:15.319885+05:30
62	fyle_accounting_mappings	0004_auto_20210127_1241	2022-09-20 14:04:15.394993+05:30
63	fyle_accounting_mappings	0005_expenseattribute_auto_mapped	2022-09-20 14:04:15.432968+05:30
64	fyle_accounting_mappings	0006_auto_20210305_0827	2022-09-20 14:04:15.51047+05:30
65	fyle_accounting_mappings	0007_auto_20210409_1931	2022-09-20 14:04:15.593389+05:30
66	fyle_accounting_mappings	0008_auto_20210604_0713	2022-09-20 14:04:15.913364+05:30
67	fyle_accounting_mappings	0009_auto_20210618_1004	2022-09-20 14:04:16.733441+05:30
68	fyle_accounting_mappings	0010_remove_mappingsetting_expense_field_id	2022-09-20 14:04:17.025427+05:30
69	fyle_accounting_mappings	0011_categorymapping_employeemapping	2022-09-20 14:04:17.278719+05:30
70	fyle_accounting_mappings	0012_auto_20211206_0600	2022-09-20 14:04:17.424863+05:30
71	fyle_accounting_mappings	0013_auto_20220323_1133	2022-09-20 14:04:17.515735+05:30
72	fyle_accounting_mappings	0014_mappingsetting_source_placeholder	2022-09-20 14:04:17.602735+05:30
73	fyle_accounting_mappings	0015_auto_20220412_0614	2022-09-20 14:04:17.839639+05:30
74	fyle_accounting_mappings	0016_auto_20220413_1624	2022-09-20 14:04:18.022281+05:30
75	fyle_accounting_mappings	0017_auto_20220419_0649	2022-09-20 14:04:18.731774+05:30
76	fyle_accounting_mappings	0018_auto_20220419_0709	2022-09-20 14:04:19.06654+05:30
77	fyle_rest_auth	0001_initial	2022-09-20 14:04:19.416057+05:30
78	fyle_rest_auth	0002_auto_20200101_1205	2022-09-20 14:04:19.51786+05:30
79	fyle_rest_auth	0003_auto_20200107_0921	2022-09-20 14:04:19.626702+05:30
80	fyle_rest_auth	0004_auto_20200107_1345	2022-09-20 14:04:19.946828+05:30
81	fyle_rest_auth	0005_remove_authtoken_access_token	2022-09-20 14:04:20.077756+05:30
82	fyle_rest_auth	0006_auto_20201221_0849	2022-09-20 14:04:20.237855+05:30
83	workspaces	0014_configuration_memo_structure	2022-09-20 14:04:20.433425+05:30
84	workspaces	0015_auto_20211229_1347	2022-09-20 14:04:20.489725+05:30
85	workspaces	0016_fylecredential_cluster_domain	2022-09-20 14:04:20.548133+05:30
86	workspaces	0017_configuration_import_tax_codes	2022-09-20 14:04:20.795793+05:30
87	mappings	0001_initial	2022-09-20 14:04:21.168003+05:30
88	mappings	0002_ccc	2022-09-20 14:04:21.416857+05:30
89	mappings	0003_auto_20210127_1551	2022-09-20 14:04:21.847549+05:30
90	mappings	0004_auto_20210208_0548	2022-09-20 14:04:22.499943+05:30
91	mappings	0005_auto_20210517_1650	2022-09-20 14:04:23.334661+05:30
92	mappings	0006_auto_20210603_0819	2022-09-20 14:04:23.580025+05:30
93	mappings	0007_auto_20210705_0933	2022-09-20 14:04:23.692476+05:30
94	mappings	0008_auto_20210831_0718	2022-09-20 14:04:23.776964+05:30
95	mappings	0009_auto_20220215_1553	2022-09-20 14:04:23.84625+05:30
96	mappings	0010_locationentitymapping	2022-09-20 14:04:23.919376+05:30
97	sage_intacct	0001_initial	2022-09-20 14:04:25.419418+05:30
98	sage_intacct	0002_charge_card_transactions	2022-09-20 14:04:27.477472+05:30
99	sage_intacct	0003_auto_20201209_0558	2022-09-20 14:04:28.695917+05:30
100	sage_intacct	0004_auto_20210127_1345	2022-09-20 14:04:29.947749+05:30
101	sage_intacct	0005_auto_20210208_0548	2022-09-20 14:04:32.634877+05:30
102	sage_intacct	0006_auto_20210224_0816	2022-09-20 14:04:33.370793+05:30
103	sage_intacct	0007_auto_20210308_0759	2022-09-20 14:04:35.042+05:30
104	sage_intacct	0008_auto_20210408_0812	2022-09-20 14:04:35.105949+05:30
105	sage_intacct	0009_auto_20210521_1008	2022-09-20 14:04:35.158518+05:30
106	sage_intacct	0010_expensereportlineitem_expense_payment_type	2022-09-20 14:04:35.18885+05:30
107	sage_intacct	0011_billlineitem_class_id	2022-09-20 14:04:35.254919+05:30
108	sage_intacct	0012_auto_20210907_0725	2022-09-20 14:04:35.358296+05:30
109	sage_intacct	0013_auto_20211203_1156	2022-09-20 14:04:35.422581+05:30
110	sage_intacct	0014_journalentry_journalentrylineitem	2022-09-20 14:04:36.915714+05:30
111	sage_intacct	0015_auto_20220103_0843	2022-09-20 14:04:37.395488+05:30
112	sage_intacct	0016_chargecardtransaction_payee	2022-09-20 14:04:37.46471+05:30
113	sage_intacct	0017_auto_20220210_1106	2022-09-20 14:04:37.893335+05:30
114	sessions	0001_initial	2022-09-20 14:04:37.975807+05:30
115	tasks	0001_initial	2022-09-20 14:04:39.601893+05:30
116	tasks	0002_charge_card_transactions	2022-09-20 14:04:41.715034+05:30
117	tasks	0003_auto_20210208_0548	2022-09-20 14:04:42.509343+05:30
118	tasks	0004_auto_20211203_1156	2022-09-20 14:04:44.935744+05:30
119	tasks	0005_tasklog_journal_entry	2022-09-20 14:04:45.270842+05:30
120	users	0002_auto_20201228_0802	2022-09-20 14:04:45.316135+05:30
121	workspaces	0018_auto_20220427_1043	2022-09-20 14:04:46.055545+05:30
122	workspaces	0019_auto_20220510_1635	2022-09-20 14:04:46.502776+05:30
123	workspaces	0020_configuration_change_accounting_period	2022-09-20 14:04:47.001754+05:30
124	workspaces	0021_configuration_import_vendors_as_merchants	2022-09-20 14:04:47.365985+05:30
125	workspaces	0022_configuration_employee_field_mapping	2022-09-20 14:04:47.637128+05:30
126	fyle	0015_expensegroup_export_type	2022-09-29 17:38:22.995468+05:30
127	fyle	0016_auto_20221213_0857	2022-12-15 12:24:10.950799+05:30
999	mappings	0011_auto_20221010_0741	2022-09-20 14:04:23.84625+05:30
128	sage_intacct	0018_auto_20221213_0819	2022-12-15 12:59:38.157471+05:30
129	sage_intacct	0018_auto_20221209_0901	2022-12-15 12:59:38.245266+05:30
130	sage_intacct	0019_merge_20221213_0857	2022-12-15 12:59:38.258629+05:30
131	workspaces	0023_auto_20221213_0857	2022-12-15 12:59:38.367282+05:30
132	fyle_accounting_mappings	0019_auto_20230105_1104	2023-03-13 11:45:36.100493+05:30
133	fyle_accounting_mappings	0020_auto_20230302_0519	2023-03-13 11:45:36.138972+05:30
134	sage_intacct	0019_auto_20230307_1746	2023-03-13 11:45:36.189955+05:30
\.


--
-- Data for Name: django_q_ormq; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_q_ormq (id, key, payload, lock) FROM stdin;
\.


--
-- Data for Name: django_q_schedule; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_q_schedule (id, func, hook, args, kwargs, schedule_type, repeats, next_run, task, name, minutes, cron) FROM stdin;
5	apps.mappings.tasks.auto_create_project_mappings	\N	1	\N	I	-5	2022-09-30 14:16:24.989603+05:30	54ab7ab7396741eea35de26e72b73c18	\N	1440	\N
2	apps.mappings.tasks.async_auto_map_employees	\N	1	\N	I	-5	2022-09-30 14:16:24.994645+05:30	7820d0fa2f7f4ac78c1a5e283560a143	\N	1440	\N
3	apps.mappings.tasks.auto_create_tax_codes_mappings	\N	1	\N	I	-5	2022-09-30 14:16:25.03867+05:30	72495cee26334ea9ad64b337f757c4a6	\N	1440	\N
4	apps.mappings.tasks.auto_create_vendors_as_merchants	\N	1	\N	I	-5	2022-09-30 14:16:25.0608+05:30	3bdcf280bd6c42a197ad24f932ce39c7	\N	1440	\N
6	apps.sage_intacct.tasks.create_ap_payment	\N	1	\N	I	-4	2022-09-30 14:17:19.647275+05:30	334370e333c54c669f6bc9e876d3ec60	\N	1440	\N
\.


--
-- Data for Name: django_q_task; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_q_task (name, func, hook, args, kwargs, result, started, stopped, success, id, "group", attempt_count) FROM stdin;
asparagus-single-jersey-blue	apps.mappings.tasks.auto_create_tax_codes_mappings	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-20 14:10:13.062302+05:30	2022-09-20 14:10:15.683139+05:30	t	802d2482ae304c14a0b445386e266838	3	1
friend-vegan-shade-zulu	apps.mappings.tasks.async_auto_map_employees	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-20 14:10:13.015775+05:30	2022-09-20 14:10:23.134177+05:30	t	325cb28cdceb4499be096c1fdb53b5c2	2	1
low-sad-river-yellow	apps.mappings.tasks.auto_create_vendors_as_merchants	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-20 14:10:13.122168+05:30	2022-09-20 14:10:24.046441+05:30	t	51f89542d0684e48b1a7af008d26cc9a	4	1
missouri-winner-utah-yankee	apps.mappings.tasks.auto_create_project_mappings	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-20 14:10:13.167858+05:30	2022-09-20 14:10:26.030092+05:30	t	59f22b0e0d7947c5924b2d1dedaab902	5	1
robert-july-kansas-monkey	apps.mappings.tasks.auto_create_category_mappings	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	gARdlC4=	2022-09-20 14:10:12.962536+05:30	2022-09-20 14:10:39.053201+05:30	t	b78956d25b524327a759f2631eace0c3	1	1
sodium-alabama-charlie-six	apps.mappings.tasks.auto_create_tax_codes_mappings	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-20 14:17:07.568062+05:30	2022-09-20 14:17:09.466315+05:30	t	8ed8aa314cf54df5ae67917d12e1c3f8	3	1
idaho-august-bakerloo-sweet	apps.mappings.tasks.auto_create_project_mappings	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-20 14:17:07.508948+05:30	2022-09-20 14:17:16.31791+05:30	t	3728e698bc884e77a6571dfd037b8827	5	1
dakota-pennsylvania-michigan-oranges	apps.mappings.tasks.auto_create_vendors_as_merchants	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-20 14:17:07.593487+05:30	2022-09-20 14:17:16.412242+05:30	t	a7bd586d911648619bf727c2def3119a	4	1
london-item-idaho-bacon	apps.mappings.tasks.async_auto_map_employees	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-20 14:17:07.540279+05:30	2022-09-20 14:17:16.427793+05:30	t	3cffad1235aa46b1b8ba30535aa7dc31	2	1
eight-michigan-virginia-mobile	apps.sage_intacct.tasks.create_ap_payment	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-20 14:17:49.746201+05:30	2022-09-20 14:17:52.196922+05:30	t	ef431c8b04584d98bf1cedbe816fb1d0	6	1
india-texas-beryllium-social	apps.fyle.tasks.create_expense_groups	\N	gASVUwIAAAAAAABLAV2UKIwIUEVSU09OQUyUjANDQ0OUZYwVZGphbmdvLmRiLm1vZGVscy5iYXNllIwObW9kZWxfdW5waWNrbGWUk5SMBXRhc2tzlIwHVGFza0xvZ5SGlIWUUpR9lCiMBl9zdGF0ZZRoA4wKTW9kZWxTdGF0ZZSTlCmBlH2UKIwMZmllbGRzX2NhY2hllH2UjAJkYpSMB2RlZmF1bHSUjAZhZGRpbmeUiXVijAJpZJRLAYwMd29ya3NwYWNlX2lklEsBjAR0eXBllIwRRkVUQ0hJTkdfRVhQRU5TRVOUjAd0YXNrX2lklE6MEGV4cGVuc2VfZ3JvdXBfaWSUTowHYmlsbF9pZJROjBFleHBlbnNlX3JlcG9ydF9pZJROjBpjaGFyZ2VfY2FyZF90cmFuc2FjdGlvbl9pZJROjBBqb3VybmFsX2VudHJ5X2lklE6MDWFwX3BheW1lbnRfaWSUTowdc2FnZV9pbnRhY2N0X3JlaW1idXJzZW1lbnRfaWSUTowGc3RhdHVzlIwIQ09NUExFVEWUjAZkZXRhaWyUfZRoFIwNZGVmYXVsdCB2YWx1ZZRzjBNzYWdlX2ludGFjY3RfZXJyb3JzlE6MCmNyZWF0ZWRfYXSUjAhkYXRldGltZZSMCGRhdGV0aW1llJOUQwoH5gkUCDAVAAJ2lIwEcHl0epSMBF9VVEOUk5QpUpSGlFKUjAp1cGRhdGVkX2F0lGgrQwoH5gkUCDAVC8VglGgwhpRSlIwPX2RqYW5nb192ZXJzaW9ulIwGMy4xLjE0lHVih5Qu	gAR9lC4=	\N	2022-09-20 14:18:21.025429+05:30	2022-09-20 14:18:21.779769+05:30	t	f8b7361a9d5b4c5796d41344c8836dea	\N	1
romeo-fish-twelve-vegan	apps.fyle.tasks.sync_reimbursements	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-20 14:18:35.736509+05:30	2022-09-20 14:18:37.363333+05:30	t	faa12acd7fc84bba942fe6bf33209b62	7f54e4e107e54f84851873e36f5ab041	1
seventeen-michigan-magnesium-east	apps.sage_intacct.tasks.create_bill	\N	gASV7QEAAAAAAACMFWRqYW5nby5kYi5tb2RlbHMuYmFzZZSMDm1vZGVsX3VucGlja2xllJOUjARmeWxllIwMRXhwZW5zZUdyb3VwlIaUhZRSlH2UKIwGX3N0YXRllGgAjApNb2RlbFN0YXRllJOUKYGUfZQojAxmaWVsZHNfY2FjaGWUfZSMBmFkZGluZ5SJjAJkYpSMB2RlZmF1bHSUdWKMAmlklEsBjAtmdW5kX3NvdXJjZZSMCFBFUlNPTkFMlIwMd29ya3NwYWNlX2lklEsBjAtkZXNjcmlwdGlvbpR9lCiMCXJlcG9ydF9pZJSMDHJwRVpHcVZDeVd4UZSMC2Z1bmRfc291cmNllIwIUEVSU09OQUyUjAxjbGFpbV9udW1iZXKUjA5DLzIwMjIvMDkvUi8yMZSMDmVtcGxveWVlX2VtYWlslIwQYXNod2luLnRAZnlsZS5pbpR1jApjcmVhdGVkX2F0lIwIZGF0ZXRpbWWUjAhkYXRldGltZZSTlEMKB+YJFAgwFQut15SMBHB5dHqUjARfVVRDlJOUKVKUhpRSlIwLZXhwb3J0ZWRfYXSUTowKdXBkYXRlZF9hdJRoJEMKB+YJFAgwFQuuBZRoKYaUUpSMD19kamFuZ29fdmVyc2lvbpSMBjMuMS4xNJR1YksChpQu	gAR9lC4=	\N	2022-09-20 14:18:37.377162+05:30	2022-09-20 14:18:40.023104+05:30	t	b6054434b7f6438bad8d6dcdc5c3043a	7f54e4e107e54f84851873e36f5ab041	1
undress-pip-two-lima	apps.fyle.tasks.sync_reimbursements	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-20 14:19:12.074551+05:30	2022-09-20 14:19:13.746885+05:30	t	ca9e00b2d0484c7bbb8962b46bd1c102	01f953e8bcfb4b3d8f539d84a14940fd	1
oven-helium-vermont-alabama	apps.sage_intacct.tasks.create_bill	\N	gASVXgMAAAAAAACMFWRqYW5nby5kYi5tb2RlbHMuYmFzZZSMDm1vZGVsX3VucGlja2xllJOUjARmeWxllIwMRXhwZW5zZUdyb3VwlIaUhZRSlH2UKIwGX3N0YXRllGgAjApNb2RlbFN0YXRllJOUKYGUfZQojAxmaWVsZHNfY2FjaGWUfZSMBGJpbGyUaAKMDHNhZ2VfaW50YWNjdJSMBEJpbGyUhpSFlFKUfZQoaAloCymBlH2UKIwCZGKUjAdkZWZhdWx0lGgOfZSMDWV4cGVuc2VfZ3JvdXCUaAdzjAZhZGRpbmeUiXVijAJpZJRLAYwQZXhwZW5zZV9ncm91cF9pZJRLAYwJdmVuZG9yX2lklIwGQXNod2lulIwLZGVzY3JpcHRpb26UfZQojAlyZXBvcnRfaWSUjAxycEVaR3FWQ3lXeFGUjAtmdW5kX3NvdXJjZZSMCFBFUlNPTkFMlIwMY2xhaW1fbnVtYmVylIwOQy8yMDIyLzA5L1IvMjGUjA5lbXBsb3llZV9lbWFpbJSMEGFzaHdpbi50QGZ5bGUuaW6UdYwEbWVtb5SMJVJlaW1idXJzYWJsZSBleHBlbnNlIC0gQy8yMDIyLzA5L1IvMjGUjAhjdXJyZW5jeZSMA1VTRJSMCXN1cGRvY19pZJROjBB0cmFuc2FjdGlvbl9kYXRllIwTMjAyMi0wOS0yMFQwODo0OToxNpSMDnBheW1lbnRfc3luY2VklImMFHBhaWRfb25fc2FnZV9pbnRhY2N0lImMCmNyZWF0ZWRfYXSUjAhkYXRldGltZZSMCGRhdGV0aW1llJOUQwoH5gkUCDEQBfyplIwEcHl0epSMBF9VVEOUk5QpUpSGlFKUjAp1cGRhdGVkX2F0lGg4QwoH5gkUCDEQBgIslGg9hpRSlIwPX2RqYW5nb192ZXJzaW9ulIwGMy4xLjE0lHVic2gdiWgZjAdkZWZhdWx0lHViaB5LAYwLZnVuZF9zb3VyY2WUjAhQRVJTT05BTJSMDHdvcmtzcGFjZV9pZJRLAWgiaCNoNWg4QwoH5gkUCDAVC63XlGg9hpRSlIwLZXhwb3J0ZWRfYXSUTmhAaDhDCgfmCRQIMBULrgWUaD2GlFKUjA9fZGphbmdvX3ZlcnNpb26UaEV1YksChpQu	gAR9lC4=	\N	2022-09-20 14:19:13.750365+05:30	2022-09-20 14:19:19.102546+05:30	t	6787d29bbe924030afc456d1a4d20473	01f953e8bcfb4b3d8f539d84a14940fd	1
vegan-nuts-ten-salami	apps.fyle.tasks.create_expense_groups	\N	gASVWwIAAAAAAABLAV2UKIwIUEVSU09OQUyUjANDQ0OUZYwVZGphbmdvLmRiLm1vZGVscy5iYXNllIwObW9kZWxfdW5waWNrbGWUk5SMBXRhc2tzlIwHVGFza0xvZ5SGlIWUUpR9lCiMBl9zdGF0ZZRoA4wKTW9kZWxTdGF0ZZSTlCmBlH2UKIwMZmllbGRzX2NhY2hllH2UjAZhZGRpbmeUiYwCZGKUjAdkZWZhdWx0lHVijAJpZJRLAYwMd29ya3NwYWNlX2lklEsBjAR0eXBllIwRRkVUQ0hJTkdfRVhQRU5TRVOUjAd0YXNrX2lklE6MEGV4cGVuc2VfZ3JvdXBfaWSUTowHYmlsbF9pZJROjBFleHBlbnNlX3JlcG9ydF9pZJROjBpjaGFyZ2VfY2FyZF90cmFuc2FjdGlvbl9pZJROjBBqb3VybmFsX2VudHJ5X2lklE6MDWFwX3BheW1lbnRfaWSUTowdc2FnZV9pbnRhY2N0X3JlaW1idXJzZW1lbnRfaWSUTowGc3RhdHVzlIwIQ09NUExFVEWUjAZkZXRhaWyUfZSMB2RlZmF1bHSUjA1kZWZhdWx0IHZhbHVllHOME3NhZ2VfaW50YWNjdF9lcnJvcnOUTowKY3JlYXRlZF9hdJSMCGRhdGV0aW1llIwIZGF0ZXRpbWWUk5RDCgfmCRQIMBUAAnaUjARweXR6lIwEX1VUQ5STlClSlIaUUpSMCnVwZGF0ZWRfYXSUaCxDCgfmCRQIMxsKOP6UaDGGlFKUjA9fZGphbmdvX3ZlcnNpb26UjAYzLjEuMTSUdWKHlC4=	gAR9lC4=	\N	2022-09-20 14:21:26.412218+05:30	2022-09-20 14:21:27.680767+05:30	t	20f78db05a22479fa0fa66e6348de9ef	\N	1
aspen-king-football-july	apps.fyle.tasks.sync_reimbursements	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-20 14:21:33.400089+05:30	2022-09-20 14:21:34.085655+05:30	t	1eb88d2796a44c0c892ab058956351ca	03e74dbb40794336811835d3bbd78800	1
fanta-zebra-red-failed	apps.fyle.tasks.sync_reimbursements	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-20 14:21:33.202866+05:30	2022-09-20 14:21:34.095834+05:30	t	f06271a131164f96beb945fa139dd31c	9850400d7ae1446498d1cce14bdea90a	1
kansas-missouri-high-ten	apps.sage_intacct.tasks.create_ap_payment	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-28 16:50:39.441124+05:30	2022-09-28 16:50:41.346546+05:30	t	446b5f1ff9644556a81230d709ee84b9	6	1
undress-xray-enemy-paris	apps.mappings.tasks.async_auto_map_employees	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-28 16:50:39.412662+05:30	2022-09-28 16:50:46.951256+05:30	t	1eb4c884d91543749bf8306cfbe1a711	2	1
aspen-april-mirror-alaska	apps.mappings.tasks.auto_create_vendors_as_merchants	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-28 16:50:39.430756+05:30	2022-09-28 16:50:47.741487+05:30	t	8c3b10abff37448ba38bcf6b1d635e23	4	1
ten-monkey-sodium-uranus	apps.mappings.tasks.auto_create_project_mappings	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-28 16:50:39.389393+05:30	2022-09-28 16:50:48.080556+05:30	t	a86d100ffd8945a089bd639a1c1a917f	5	1
delta-california-apart-sierra	apps.sage_intacct.tasks.create_bill	\N	gASVhQMAAAAAAACMFWRqYW5nby5kYi5tb2RlbHMuYmFzZZSMDm1vZGVsX3VucGlja2xllJOUjARmeWxllIwMRXhwZW5zZUdyb3VwlIaUhZRSlH2UKIwGX3N0YXRllGgAjApNb2RlbFN0YXRllJOUKYGUfZQojAxmaWVsZHNfY2FjaGWUfZSMBGJpbGyUaAKMDHNhZ2VfaW50YWNjdJSMBEJpbGyUhpSFlFKUfZQoaAloCymBlH2UKIwCZGKUjAdkZWZhdWx0lGgOfZSMDWV4cGVuc2VfZ3JvdXCUaAdzjAZhZGRpbmeUiXVijAJpZJRLAowQZXhwZW5zZV9ncm91cF9pZJRLAowJdmVuZG9yX2lklIwFMjAwNDOUjAtkZXNjcmlwdGlvbpR9lCiMCXJlcG9ydF9pZJSMDHJwU1RZTzhBZlVWQZSMCmV4cGVuc2VfaWSUjAx0eENxTHFzRW5BamaUjAtmdW5kX3NvdXJjZZSMA0NDQ5SMDGNsYWltX251bWJlcpSMDkMvMjAyMi8wOS9SLzIylIwOZW1wbG95ZWVfZW1haWyUjBBhc2h3aW4udEBmeWxlLmlulHWMBG1lbW+UjDtDb3Jwb3JhdGUgQ3JlZGl0IENhcmQgZXhwZW5zZSAtIEMvMjAyMi8wOS9SLzIyIC0gMjAvMDkvMjAyMpSMCGN1cnJlbmN5lIwDVVNElIwJc3VwZG9jX2lklE6MEHRyYW5zYWN0aW9uX2RhdGWUjBMyMDIyLTA5LTIwVDA4OjUxOjM2lIwOcGF5bWVudF9zeW5jZWSUiYwUcGFpZF9vbl9zYWdlX2ludGFjY3SUiYwKY3JlYXRlZF9hdJSMCGRhdGV0aW1llIwIZGF0ZXRpbWWUk5RDCgfmCRQIMyQCuRyUjARweXR6lIwEX1VUQ5STlClSlIaUUpSMCnVwZGF0ZWRfYXSUaDpDCgfmCRQIMyQCuUeUaD+GlFKUjA9fZGphbmdvX3ZlcnNpb26UjAYzLjEuMTSUdWJzaB2JaBmMB2RlZmF1bHSUdWJoHksCjAtmdW5kX3NvdXJjZZSMA0NDQ5SMDHdvcmtzcGFjZV9pZJRLAWgiaCNoN2g6QwoH5gkUCDMbCe9rlGg/hpRSlIwLZXhwb3J0ZWRfYXSUTmhCaDpDCgfmCRQIMxsJ75+UaD+GlFKUjA9fZGphbmdvX3ZlcnNpb26UaEd1YksDhpQu	gAR9lC4=	\N	2022-09-20 14:21:34.094557+05:30	2022-09-20 14:21:38.08379+05:30	t	05d919f7e8fe4b4396358623b7c59423	03e74dbb40794336811835d3bbd78800	1
lake-quebec-beryllium-yellow	apps.sage_intacct.tasks.create_bill	\N	gASVXgMAAAAAAACMFWRqYW5nby5kYi5tb2RlbHMuYmFzZZSMDm1vZGVsX3VucGlja2xllJOUjARmeWxllIwMRXhwZW5zZUdyb3VwlIaUhZRSlH2UKIwGX3N0YXRllGgAjApNb2RlbFN0YXRllJOUKYGUfZQojAxmaWVsZHNfY2FjaGWUfZSMBGJpbGyUaAKMDHNhZ2VfaW50YWNjdJSMBEJpbGyUhpSFlFKUfZQoaAloCymBlH2UKIwCZGKUjAdkZWZhdWx0lGgOfZSMDWV4cGVuc2VfZ3JvdXCUaAdzjAZhZGRpbmeUiXVijAJpZJRLA4wQZXhwZW5zZV9ncm91cF9pZJRLAYwJdmVuZG9yX2lklIwGQXNod2lulIwLZGVzY3JpcHRpb26UfZQojAlyZXBvcnRfaWSUjAxycEVaR3FWQ3lXeFGUjAtmdW5kX3NvdXJjZZSMCFBFUlNPTkFMlIwMY2xhaW1fbnVtYmVylIwOQy8yMDIyLzA5L1IvMjGUjA5lbXBsb3llZV9lbWFpbJSMEGFzaHdpbi50QGZ5bGUuaW6UdYwEbWVtb5SMJVJlaW1idXJzYWJsZSBleHBlbnNlIC0gQy8yMDIyLzA5L1IvMjGUjAhjdXJyZW5jeZSMA1VTRJSMCXN1cGRvY19pZJROjBB0cmFuc2FjdGlvbl9kYXRllIwTMjAyMi0wOS0yMFQwODo1MTozNpSMDnBheW1lbnRfc3luY2VklImMFHBhaWRfb25fc2FnZV9pbnRhY2N0lImMCmNyZWF0ZWRfYXSUjAhkYXRldGltZZSMCGRhdGV0aW1llJOUQwoH5gkUCDMkDOlTlIwEcHl0epSMBF9VVEOUk5QpUpSGlFKUjAp1cGRhdGVkX2F0lGg4QwoH5gkUCDMkDOl1lGg9hpRSlIwPX2RqYW5nb192ZXJzaW9ulIwGMy4xLjE0lHVic2gdiWgZjAdkZWZhdWx0lHViaB5LAYwLZnVuZF9zb3VyY2WUjAhQRVJTT05BTJSMDHdvcmtzcGFjZV9pZJRLAWgiaCNoNWg4QwoH5gkUCDAVC63XlGg9hpRSlIwLZXhwb3J0ZWRfYXSUTmhAaDhDCgfmCRQIMBULrgWUaD2GlFKUjA9fZGphbmdvX3ZlcnNpb26UaEV1YksChpQu	gAR9lC4=	\N	2022-09-20 14:21:34.197425+05:30	2022-09-20 14:21:38.764149+05:30	t	7b8631b94a25409a9ec48ac51ca41356	9850400d7ae1446498d1cce14bdea90a	1
foxtrot-papa-gee-carbon	apps.fyle.tasks.create_expense_groups	\N	gASVWwIAAAAAAABLAV2UKIwIUEVSU09OQUyUjANDQ0OUZYwVZGphbmdvLmRiLm1vZGVscy5iYXNllIwObW9kZWxfdW5waWNrbGWUk5SMBXRhc2tzlIwHVGFza0xvZ5SGlIWUUpR9lCiMBl9zdGF0ZZRoA4wKTW9kZWxTdGF0ZZSTlCmBlH2UKIwMZmllbGRzX2NhY2hllH2UjAZhZGRpbmeUiYwCZGKUjAdkZWZhdWx0lHVijAJpZJRLAYwMd29ya3NwYWNlX2lklEsBjAR0eXBllIwRRkVUQ0hJTkdfRVhQRU5TRVOUjAd0YXNrX2lklE6MEGV4cGVuc2VfZ3JvdXBfaWSUTowHYmlsbF9pZJROjBFleHBlbnNlX3JlcG9ydF9pZJROjBpjaGFyZ2VfY2FyZF90cmFuc2FjdGlvbl9pZJROjBBqb3VybmFsX2VudHJ5X2lklE6MDWFwX3BheW1lbnRfaWSUTowdc2FnZV9pbnRhY2N0X3JlaW1idXJzZW1lbnRfaWSUTowGc3RhdHVzlIwIQ09NUExFVEWUjAZkZXRhaWyUfZSMB2RlZmF1bHSUjA1kZWZhdWx0IHZhbHVllHOME3NhZ2VfaW50YWNjdF9lcnJvcnOUTowKY3JlYXRlZF9hdJSMCGRhdGV0aW1llIwIZGF0ZXRpbWWUk5RDCgfmCRQIMBUAAnaUjARweXR6lIwEX1VUQ5STlClSlIaUUpSMCnVwZGF0ZWRfYXSUaCxDCgfmCRQIODICTFaUaDGGlFKUjA9fZGphbmdvX3ZlcnNpb26UjAYzLjEuMTSUdWKHlC4=	gAR9lC4=	\N	2022-09-20 14:26:49.260438+05:30	2022-09-20 14:26:50.158376+05:30	t	2313225c5df34247a6c12510256abcec	\N	1
queen-nuts-edward-sixteen	apps.fyle.tasks.sync_reimbursements	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-20 14:27:02.275682+05:30	2022-09-20 14:27:03.087054+05:30	t	12f9623f65e44564b1ff2a5ebfdb0aa7	02277d4db84343239a89541cec3c7b82	1
double-apart-mirror-stream	apps.fyle.tasks.sync_reimbursements	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-20 14:27:02.332442+05:30	2022-09-20 14:27:03.186795+05:30	t	9789012adeb04f279f212b19b7df8b36	acc928ba6bf4400c8268331a29189313	1
uranus-december-orange-ink	apps.sage_intacct.tasks.create_bill	\N	gASVXgMAAAAAAACMFWRqYW5nby5kYi5tb2RlbHMuYmFzZZSMDm1vZGVsX3VucGlja2xllJOUjARmeWxllIwMRXhwZW5zZUdyb3VwlIaUhZRSlH2UKIwGX3N0YXRllGgAjApNb2RlbFN0YXRllJOUKYGUfZQojAxmaWVsZHNfY2FjaGWUfZSMBGJpbGyUaAKMDHNhZ2VfaW50YWNjdJSMBEJpbGyUhpSFlFKUfZQoaAloCymBlH2UKIwCZGKUjAdkZWZhdWx0lGgOfZSMDWV4cGVuc2VfZ3JvdXCUaAdzjAZhZGRpbmeUiXVijAJpZJRLBIwQZXhwZW5zZV9ncm91cF9pZJRLAYwJdmVuZG9yX2lklIwGQXNod2lulIwLZGVzY3JpcHRpb26UfZQojAlyZXBvcnRfaWSUjAxycEVaR3FWQ3lXeFGUjAtmdW5kX3NvdXJjZZSMCFBFUlNPTkFMlIwMY2xhaW1fbnVtYmVylIwOQy8yMDIyLzA5L1IvMjGUjA5lbXBsb3llZV9lbWFpbJSMEGFzaHdpbi50QGZ5bGUuaW6UdYwEbWVtb5SMJVJlaW1idXJzYWJsZSBleHBlbnNlIC0gQy8yMDIyLzA5L1IvMjGUjAhjdXJyZW5jeZSMA1VTRJSMCXN1cGRvY19pZJROjBB0cmFuc2FjdGlvbl9kYXRllIwTMjAyMi0wOS0yMFQwODo1NzowNZSMDnBheW1lbnRfc3luY2VklImMFHBhaWRfb25fc2FnZV9pbnRhY2N0lImMCmNyZWF0ZWRfYXSUjAhkYXRldGltZZSMCGRhdGV0aW1llJOUQwoH5gkUCDkFBPS8lIwEcHl0epSMBF9VVEOUk5QpUpSGlFKUjAp1cGRhdGVkX2F0lGg4QwoH5gkUCDkFBPTnlGg9hpRSlIwPX2RqYW5nb192ZXJzaW9ulIwGMy4xLjE0lHVic2gdiWgZjAdkZWZhdWx0lHViaB5LAYwLZnVuZF9zb3VyY2WUjAhQRVJTT05BTJSMDHdvcmtzcGFjZV9pZJRLAWgiaCNoNWg4QwoH5gkUCDAVC63XlGg9hpRSlIwLZXhwb3J0ZWRfYXSUTmhAaDhDCgfmCRQIMBULrgWUaD2GlFKUjA9fZGphbmdvX3ZlcnNpb26UaEV1YksChpQu	gAR9lC4=	\N	2022-09-20 14:27:03.089187+05:30	2022-09-20 14:27:06.870381+05:30	t	8bd9ce74882d4adf958f0cb39d68e777	02277d4db84343239a89541cec3c7b82	1
nebraska-leopard-romeo-pennsylvania	apps.sage_intacct.tasks.create_bill	\N	gASVhQMAAAAAAACMFWRqYW5nby5kYi5tb2RlbHMuYmFzZZSMDm1vZGVsX3VucGlja2xllJOUjARmeWxllIwMRXhwZW5zZUdyb3VwlIaUhZRSlH2UKIwGX3N0YXRllGgAjApNb2RlbFN0YXRllJOUKYGUfZQojAxmaWVsZHNfY2FjaGWUfZSMBGJpbGyUaAKMDHNhZ2VfaW50YWNjdJSMBEJpbGyUhpSFlFKUfZQoaAloCymBlH2UKIwCZGKUjAdkZWZhdWx0lGgOfZSMDWV4cGVuc2VfZ3JvdXCUaAdzjAZhZGRpbmeUiXVijAJpZJRLBYwQZXhwZW5zZV9ncm91cF9pZJRLAowJdmVuZG9yX2lklIwFMjAwNDOUjAtkZXNjcmlwdGlvbpR9lCiMCXJlcG9ydF9pZJSMDHJwU1RZTzhBZlVWQZSMCmV4cGVuc2VfaWSUjAx0eENxTHFzRW5BamaUjAtmdW5kX3NvdXJjZZSMA0NDQ5SMDGNsYWltX251bWJlcpSMDkMvMjAyMi8wOS9SLzIylIwOZW1wbG95ZWVfZW1haWyUjBBhc2h3aW4udEBmeWxlLmlulHWMBG1lbW+UjDtDb3Jwb3JhdGUgQ3JlZGl0IENhcmQgZXhwZW5zZSAtIEMvMjAyMi8wOS9SLzIyIC0gMjAvMDkvMjAyMpSMCGN1cnJlbmN5lIwDVVNElIwJc3VwZG9jX2lklE6MEHRyYW5zYWN0aW9uX2RhdGWUjBMyMDIyLTA5LTIwVDA4OjU3OjA1lIwOcGF5bWVudF9zeW5jZWSUiYwUcGFpZF9vbl9zYWdlX2ludGFjY3SUiYwKY3JlYXRlZF9hdJSMCGRhdGV0aW1llIwIZGF0ZXRpbWWUk5RDCgfmCRQIOQUNJJeUjARweXR6lIwEX1VUQ5STlClSlIaUUpSMCnVwZGF0ZWRfYXSUaDpDCgfmCRQIOQUNJLqUaD+GlFKUjA9fZGphbmdvX3ZlcnNpb26UjAYzLjEuMTSUdWJzaB2JaBmMB2RlZmF1bHSUdWJoHksCjAtmdW5kX3NvdXJjZZSMA0NDQ5SMDHdvcmtzcGFjZV9pZJRLAWgiaCNoN2g6QwoH5gkUCDMbCe9rlGg/hpRSlIwLZXhwb3J0ZWRfYXSUTmhCaDpDCgfmCRQIMxsJ75+UaD+GlFKUjA9fZGphbmdvX3ZlcnNpb26UaEd1YksDhpQu	gAR9lC4=	\N	2022-09-20 14:27:03.248067+05:30	2022-09-20 14:27:07.929346+05:30	t	5fec2004d21d4dfab405e6ebb3e557af	acc928ba6bf4400c8268331a29189313	1
utah-uncle-king-orange	apps.sage_intacct.tasks.create_bill	\N	gASV/wEAAAAAAACMFWRqYW5nby5kYi5tb2RlbHMuYmFzZZSMDm1vZGVsX3VucGlja2xllJOUjARmeWxllIwMRXhwZW5zZUdyb3VwlIaUhZRSlH2UKIwGX3N0YXRllGgAjApNb2RlbFN0YXRllJOUKYGUfZQojAxmaWVsZHNfY2FjaGWUfZSMBmFkZGluZ5SJjAJkYpSMB2RlZmF1bHSUdWKMAmlklEsDjAtmdW5kX3NvdXJjZZSMA0NDQ5SMDHdvcmtzcGFjZV9pZJRLAYwLZGVzY3JpcHRpb26UfZQojAlyZXBvcnRfaWSUjAxycEJmNWlicVVUNkKUjApleHBlbnNlX2lklIwMdHhUSGZFUFdPRU9wlIwLZnVuZF9zb3VyY2WUjANDQ0OUjAxjbGFpbV9udW1iZXKUjA5DLzIwMjIvMDkvUi8yM5SMDmVtcGxveWVlX2VtYWlslIwQYXNod2luLnRAZnlsZS5pbpR1jApjcmVhdGVkX2F0lIwIZGF0ZXRpbWWUjAhkYXRldGltZZSTlEMKB+YJFAg4MgI/TJSMBHB5dHqUjARfVVRDlJOUKVKUhpRSlIwLZXhwb3J0ZWRfYXSUTowKdXBkYXRlZF9hdJRoJkMKB+YJFAg4MgI/fJRoK4aUUpSMD19kamFuZ29fdmVyc2lvbpSMBjMuMS4xNJR1YksEhpQu	gAR9lC4=	\N	2022-09-20 14:27:07.930662+05:30	2022-09-20 14:27:10.250024+05:30	t	092706c1f82f42708b17f7190f0558f7	acc928ba6bf4400c8268331a29189313	1
edward-uncle-july-east	apps.mappings.tasks.auto_create_tax_codes_mappings	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-28 16:50:39.419171+05:30	2022-09-28 16:50:40.74238+05:30	t	6c59343bf7f04fada99d065f6361c3f9	3	1
yellow-montana-paris-utah	apps.fyle.tasks.sync_reimbursements	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-28 17:26:27.975206+05:30	2022-09-28 17:26:29.172725+05:30	t	93f23aa67d394197925f59388b487a50	cfdf480bf3fc455685e5b8b3a11977d0	1
blue-king-single-hawaii	apps.fyle.tasks.sync_reimbursements	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-28 17:26:28.025405+05:30	2022-09-28 17:26:29.204256+05:30	t	629646aa0a0e4137ba09ec99581affe6	8411b791379d452c90d082aa158668a4	1
yankee-eleven-fanta-lamp	apps.sage_intacct.tasks.create_bill	\N	gASVsQMAAAAAAACMFWRqYW5nby5kYi5tb2RlbHMuYmFzZZSMDm1vZGVsX3VucGlja2xllJOUjARmeWxllIwMRXhwZW5zZUdyb3VwlIaUhZRSlH2UKIwGX3N0YXRllGgAjApNb2RlbFN0YXRllJOUKYGUfZQojAxmaWVsZHNfY2FjaGWUfZSMBGJpbGyUaAKMDHNhZ2VfaW50YWNjdJSMBEJpbGyUhpSFlFKUfZQojAZfc3RhdGWUaAspgZR9lCiMAmRilIwHZGVmYXVsdJRoDn2UjA1leHBlbnNlX2dyb3VwlGgHc4wGYWRkaW5nlIl1YowCaWSUSweMEGV4cGVuc2VfZ3JvdXBfaWSUSwKMCXZlbmRvcl9pZJSMBTIwMDQzlIwLZGVzY3JpcHRpb26UfZQojAlyZXBvcnRfaWSUjAxycFNUWU84QWZVVkGUjApleHBlbnNlX2lklIwMdHhDcUxxc0VuQWpmlIwLZnVuZF9zb3VyY2WUjANDQ0OUjAxjbGFpbV9udW1iZXKUjA5DLzIwMjIvMDkvUi8yMpSMDmVtcGxveWVlX2VtYWlslIwQYXNod2luLnRAZnlsZS5pbpR1jARtZW1vlIw7Q29ycG9yYXRlIENyZWRpdCBDYXJkIGV4cGVuc2UgLSBDLzIwMjIvMDkvUi8yMiAtIDI4LzA5LzIwMjKUjAhjdXJyZW5jeZSMA1VTRJSMCXN1cGRvY19pZJROjBB0cmFuc2FjdGlvbl9kYXRllIwTMjAyMi0wOS0yOFQxMTo1NjozMZSMDnBheW1lbnRfc3luY2VklImMFHBhaWRfb25fc2FnZV9pbnRhY2N0lImMCmNyZWF0ZWRfYXSUjAhkYXRldGltZZSMCGRhdGV0aW1llJOUQwoH5gkcCzgfDOlBlIwEcHl0epSMBF9VVEOUk5QpUpSGlFKUjAp1cGRhdGVkX2F0lGg7QwoH5gkcCzgfDOl1lGhAhpRSlIwPX2RqYW5nb192ZXJzaW9ulIwGMy4xLjE0lHVic2geiWgajAdkZWZhdWx0lHVijAJpZJRLAowLZnVuZF9zb3VyY2WUjANDQ0OUjAx3b3Jrc3BhY2VfaWSUSwGMC2Rlc2NyaXB0aW9ulGgkjApjcmVhdGVkX2F0lGg7QwoH5gkUCDMbCe9rlGhAhpRSlIwLZXhwb3J0ZWRfYXSUTowKdXBkYXRlZF9hdJRoO0MKB+YJFAgzGwnvn5RoQIaUUpSMD19kamFuZ29fdmVyc2lvbpRoSHViSwOGlC4=	gAR9lC4=	\N	2022-09-28 17:26:29.46252+05:30	2022-09-28 17:26:33.943154+05:30	t	f1f296693ae042a5b8933158e4529c5c	8411b791379d452c90d082aa158668a4	1
virginia-tango-three-connecticut	apps.sage_intacct.tasks.create_bill	\N	gASVigMAAAAAAACMFWRqYW5nby5kYi5tb2RlbHMuYmFzZZSMDm1vZGVsX3VucGlja2xllJOUjARmeWxllIwMRXhwZW5zZUdyb3VwlIaUhZRSlH2UKIwGX3N0YXRllGgAjApNb2RlbFN0YXRllJOUKYGUfZQojAxmaWVsZHNfY2FjaGWUfZSMBGJpbGyUaAKMDHNhZ2VfaW50YWNjdJSMBEJpbGyUhpSFlFKUfZQojAZfc3RhdGWUaAspgZR9lCiMAmRilIwHZGVmYXVsdJRoDn2UjA1leHBlbnNlX2dyb3VwlGgHc4wGYWRkaW5nlIl1YowCaWSUSwaMEGV4cGVuc2VfZ3JvdXBfaWSUSwGMCXZlbmRvcl9pZJSMBkFzaHdpbpSMC2Rlc2NyaXB0aW9ulH2UKIwJcmVwb3J0X2lklIwMcnBFWkdxVkN5V3hRlIwLZnVuZF9zb3VyY2WUjAhQRVJTT05BTJSMDGNsYWltX251bWJlcpSMDkMvMjAyMi8wOS9SLzIxlIwOZW1wbG95ZWVfZW1haWyUjBBhc2h3aW4udEBmeWxlLmlulHWMBG1lbW+UjCVSZWltYnVyc2FibGUgZXhwZW5zZSAtIEMvMjAyMi8wOS9SLzIxlIwIY3VycmVuY3mUjANVU0SUjAlzdXBkb2NfaWSUTowQdHJhbnNhY3Rpb25fZGF0ZZSMEzIwMjItMDktMjhUMTE6NTY6MzGUjA5wYXltZW50X3N5bmNlZJSJjBRwYWlkX29uX3NhZ2VfaW50YWNjdJSJjApjcmVhdGVkX2F0lIwIZGF0ZXRpbWWUjAhkYXRldGltZZSTlEMKB+YJHAs4Hwt0spSMBHB5dHqUjARfVVRDlJOUKVKUhpRSlIwKdXBkYXRlZF9hdJRoOUMKB+YJHAs4Hwt1EZRoPoaUUpSMD19kamFuZ29fdmVyc2lvbpSMBjMuMS4xNJR1YnNoHoloGowHZGVmYXVsdJR1YowCaWSUSwGMC2Z1bmRfc291cmNllIwIUEVSU09OQUyUjAx3b3Jrc3BhY2VfaWSUSwGMC2Rlc2NyaXB0aW9ulGgkjApjcmVhdGVkX2F0lGg5QwoH5gkUCDAVC63XlGg+hpRSlIwLZXhwb3J0ZWRfYXSUTowKdXBkYXRlZF9hdJRoOUMKB+YJFAgwFQuuBZRoPoaUUpSMD19kamFuZ29fdmVyc2lvbpRoRnViSwKGlC4=	gAR9lC4=	\N	2022-09-28 17:26:29.226213+05:30	2022-09-28 17:26:34.697792+05:30	t	e5adc37ba5e646dc96486766f90fff25	cfdf480bf3fc455685e5b8b3a11977d0	1
zulu-violet-mirror-equal	apps.sage_intacct.tasks.create_bill	\N	gASVsQMAAAAAAACMFWRqYW5nby5kYi5tb2RlbHMuYmFzZZSMDm1vZGVsX3VucGlja2xllJOUjARmeWxllIwMRXhwZW5zZUdyb3VwlIaUhZRSlH2UKIwGX3N0YXRllGgAjApNb2RlbFN0YXRllJOUKYGUfZQojAxmaWVsZHNfY2FjaGWUfZSMBGJpbGyUaAKMDHNhZ2VfaW50YWNjdJSMBEJpbGyUhpSFlFKUfZQojAZfc3RhdGWUaAspgZR9lCiMAmRilIwHZGVmYXVsdJRoDn2UjA1leHBlbnNlX2dyb3VwlGgHc4wGYWRkaW5nlIl1YowCaWSUSwiMEGV4cGVuc2VfZ3JvdXBfaWSUSwOMCXZlbmRvcl9pZJSMBTIwMDQzlIwLZGVzY3JpcHRpb26UfZQojAlyZXBvcnRfaWSUjAxycEJmNWlicVVUNkKUjApleHBlbnNlX2lklIwMdHhUSGZFUFdPRU9wlIwLZnVuZF9zb3VyY2WUjANDQ0OUjAxjbGFpbV9udW1iZXKUjA5DLzIwMjIvMDkvUi8yM5SMDmVtcGxveWVlX2VtYWlslIwQYXNod2luLnRAZnlsZS5pbpR1jARtZW1vlIw7Q29ycG9yYXRlIENyZWRpdCBDYXJkIGV4cGVuc2UgLSBDLzIwMjIvMDkvUi8yMyAtIDI4LzA5LzIwMjKUjAhjdXJyZW5jeZSMA1VTRJSMCXN1cGRvY19pZJROjBB0cmFuc2FjdGlvbl9kYXRllIwTMjAyMi0wOS0yOFQxMTo1NjozNpSMDnBheW1lbnRfc3luY2VklImMFHBhaWRfb25fc2FnZV9pbnRhY2N0lImMCmNyZWF0ZWRfYXSUjAhkYXRldGltZZSMCGRhdGV0aW1llJOUQwoH5gkcCzgkA/lVlIwEcHl0epSMBF9VVEOUk5QpUpSGlFKUjAp1cGRhdGVkX2F0lGg7QwoH5gkcCzgkA/mulGhAhpRSlIwPX2RqYW5nb192ZXJzaW9ulIwGMy4xLjE0lHVic2geiWgajAdkZWZhdWx0lHVijAJpZJRLA4wLZnVuZF9zb3VyY2WUjANDQ0OUjAx3b3Jrc3BhY2VfaWSUSwGMC2Rlc2NyaXB0aW9ulGgkjApjcmVhdGVkX2F0lGg7QwoH5gkUCDgyAj9MlGhAhpRSlIwLZXhwb3J0ZWRfYXSUTowKdXBkYXRlZF9hdJRoO0MKB+YJFAg4MgI/fJRoQIaUUpSMD19kamFuZ29fdmVyc2lvbpRoSHViSwSGlC4=	gAR9lC4=	\N	2022-09-28 17:26:33.945362+05:30	2022-09-28 17:26:37.756708+05:30	t	c9cef20a69ac4e64b21cd6f460435330	8411b791379d452c90d082aa158668a4	1
king-texas-timing-quiet	apps.mappings.tasks.async_auto_map_employees	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-29 17:39:11.665781+05:30	2022-09-29 17:39:26.068827+05:30	t	7820d0fa2f7f4ac78c1a5e283560a143	2	1
twenty-tennis-stream-cold	apps.sage_intacct.tasks.create_ap_payment	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-29 17:39:11.684809+05:30	2022-09-29 17:39:26.511365+05:30	t	334370e333c54c669f6bc9e876d3ec60	6	1
muppet-delta-uniform-alanine	apps.mappings.tasks.auto_create_vendors_as_merchants	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-29 17:39:11.677356+05:30	2022-09-29 17:39:27.232264+05:30	t	3bdcf280bd6c42a197ad24f932ce39c7	4	1
delta-washington-king-triple	apps.mappings.tasks.auto_create_project_mappings	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-29 17:39:11.659031+05:30	2022-09-29 17:39:30.836702+05:30	t	54ab7ab7396741eea35de26e72b73c18	5	1
michigan-west-fourteen-seven	apps.mappings.tasks.auto_create_tax_codes_mappings	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-29 17:39:11.671086+05:30	2022-09-29 17:39:34.826193+05:30	t	72495cee26334ea9ad64b337f757c4a6	3	1
\.


--
-- Data for Name: django_session; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_session (session_key, session_data, expire_date) FROM stdin;
\.


--
-- Data for Name: employee_mappings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.employee_mappings (id, created_at, updated_at, destination_card_account_id, destination_employee_id, destination_vendor_id, source_employee_id, workspace_id) FROM stdin;
1	2022-09-20 14:10:23.121338+05:30	2022-09-20 14:10:23.121391+05:30	\N	707	699	1	1
\.


--
-- Data for Name: expense_attributes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.expense_attributes (id, attribute_type, display_name, value, source_id, created_at, updated_at, workspace_id, active, detail, auto_mapped, auto_created) FROM stdin;
2	EMPLOYEE	Employee	nilesh.p+123@fyle.in	ouEPFtpfacUg	2022-09-20 14:09:02.395739+05:30	2022-09-20 14:09:02.39597+05:30	1	\N	{"user_id": "usHDmw44Qmmy", "location": null, "full_name": "Brad Pitt", "department": null, "department_id": null, "employee_code": null, "department_code": null}	f	f
3	EMPLOYEE	Employee	user2@fyleforgotham.in	ou8TYuw4AxVG	2022-09-20 14:09:02.396218+05:30	2022-09-20 14:09:02.396251+05:30	1	\N	{"user_id": "usBlCjf2LQFc", "location": null, "full_name": "Brian Foster", "department": "Department 1", "department_id": "deptDhMjvs45aT", "employee_code": null, "department_code": null}	f	f
4	EMPLOYEE	Employee	user5@fyleforgotham.in	ouwVEj13iF6S	2022-09-20 14:09:02.396385+05:30	2022-09-20 14:09:02.396921+05:30	1	\N	{"user_id": "usJNh5yEotAI", "location": null, "full_name": "Chris Curtis", "department": "Department 1", "department_id": "deptDhMjvs45aT", "employee_code": null, "department_code": null}	f	f
5	EMPLOYEE	Employee	nilesh.p+167@fyle.in	oufShLZ4Yvn3	2022-09-20 14:09:02.397455+05:30	2022-09-20 14:09:02.397491+05:30	1	\N	{"user_id": "us8W8MDHAyCq", "location": null, "full_name": "Vikrant Messi", "department": null, "department_id": null, "employee_code": null, "department_code": null}	f	f
6	EMPLOYEE	Employee	nilesh.p@fyle.in	ouYbK261N8dp	2022-09-20 14:09:02.397943+05:30	2022-09-20 14:09:02.398056+05:30	1	\N	{"user_id": "usAQ5SpEekLK", "location": null, "full_name": "Nilesh Pant", "department": null, "department_id": null, "employee_code": null, "department_code": null}	f	f
7	EMPLOYEE	Employee	user9@fyleforgotham.in	ouh41Vnv7pl3	2022-09-20 14:09:02.403375+05:30	2022-09-20 14:09:02.403498+05:30	1	\N	{"user_id": "usjFy17trWLb", "location": null, "full_name": "Justin Glass", "department": "Department 3", "department_id": "dept0DswoMIby7", "employee_code": null, "department_code": null}	f	f
8	EMPLOYEE	Employee	user8@fyleforgotham.in	ouZF0bfmC1DV	2022-09-20 14:09:02.403952+05:30	2022-09-20 14:09:02.40401+05:30	1	\N	{"user_id": "us9jthy9XTZE", "location": null, "full_name": "Jessica Lane", "department": "Department 2", "department_id": "deptgZF9aUB0tH", "employee_code": null, "department_code": null}	f	f
9	EMPLOYEE	Employee	user7@fyleforgotham.in	ouT8HYOj1GYZ	2022-09-20 14:09:02.404323+05:30	2022-09-20 14:09:02.404388+05:30	1	\N	{"user_id": "usL3rGiHpp8q", "location": null, "full_name": "James Taylor", "department": "Department 4", "department_id": "depttugt5POp4K", "employee_code": null, "department_code": null}	f	f
10	EMPLOYEE	Employee	user6@fyleforgotham.in	ou5XWYQjmzym	2022-09-20 14:09:02.404476+05:30	2022-09-20 14:09:02.404591+05:30	1	\N	{"user_id": "usF2lrDTIZei", "location": null, "full_name": "Victor Martinez", "department": "Department 3", "department_id": "dept0DswoMIby7", "employee_code": null, "department_code": null}	f	f
11	EMPLOYEE	Employee	user4@fyleforgotham.in	ouEetwpFkf3F	2022-09-20 14:09:02.404731+05:30	2022-09-20 14:09:02.404772+05:30	1	\N	{"user_id": "usXk2TVwvJCf", "location": null, "full_name": "Samantha Washington", "department": "Department 3", "department_id": "dept0DswoMIby7", "employee_code": null, "department_code": null}	f	f
12	EMPLOYEE	Employee	user3@fyleforgotham.in	ounUmTSUyiHX	2022-09-20 14:09:02.404881+05:30	2022-09-20 14:09:02.404914+05:30	1	\N	{"user_id": "usYH6d98zJGT", "location": null, "full_name": "Natalie Pope", "department": "Department 1", "department_id": "deptDhMjvs45aT", "employee_code": null, "department_code": null}	f	f
13	EMPLOYEE	Employee	user1@fyleforgotham.in	ouVT4YfloipJ	2022-09-20 14:09:02.405826+05:30	2022-09-20 14:09:02.405886+05:30	1	\N	{"user_id": "usRKNmaNoXTy", "location": null, "full_name": "Joshua Wood", "department": "Department 2", "department_id": "deptgZF9aUB0tH", "employee_code": null, "department_code": null}	f	f
14	EMPLOYEE	Employee	user10@fyleforgotham.in	ou7yyjvEaliS	2022-09-20 14:09:02.406018+05:30	2022-09-20 14:09:02.406057+05:30	1	\N	{"user_id": "usH1U6GUQgbT", "location": null, "full_name": "Matthew Estrada", "department": "Department 4", "department_id": "depttugt5POp4K", "employee_code": null, "department_code": null}	f	f
15	EMPLOYEE	Employee	admin1@fyleforgotham.in	ouECRFhw3AjY	2022-09-20 14:09:02.406132+05:30	2022-09-20 14:09:02.40673+05:30	1	\N	{"user_id": "usnplBhNoBFN", "location": null, "full_name": "Theresa Brown", "department": null, "department_id": null, "employee_code": null, "department_code": null}	f	f
16	EMPLOYEE	Employee	owner@fyleforgotham.in	ouT4EarnaThA	2022-09-20 14:09:02.406866+05:30	2022-09-20 14:09:02.406922+05:30	1	\N	{"user_id": "uspg0D51Nts1", "location": null, "full_name": "Fyle For Arkham Asylum", "department": null, "department_id": null, "employee_code": null, "department_code": null}	f	f
17	EMPLOYEE	Employee	approver1@fyleforgotham.in	ouMvD0iJ0pXK	2022-09-20 14:09:02.407003+05:30	2022-09-20 14:09:02.407036+05:30	1	\N	{"user_id": "usAsCHVckAu8", "location": null, "full_name": "Ryan Gallagher", "department": null, "department_id": null, "employee_code": null, "department_code": null}	f	f
634	PROJECT	Project	goat	304630	2022-09-20 14:09:06.832998+05:30	2022-09-20 14:09:06.833037+05:30	1	t	\N	f	f
2137	COST_CENTER	Cost Center	Izio	10113	2022-09-20 14:09:10.414746+05:30	2022-09-20 14:09:10.414773+05:30	1	\N	\N	f	f
3178	MERCHANT	Merchant	Entity V500	852	2022-09-20 14:10:24.029136+05:30	2022-09-20 14:10:24.029271+05:30	1	\N	\N	f	f
1661	PROJECT	Project	TSM	247773	2022-09-20 14:09:09.282688+05:30	2022-09-20 14:09:09.282717+05:30	1	t	\N	f	f
1918	COST_CENTER	Cost Center	Quimm	10216	2022-09-20 14:09:10.306136+05:30	2022-09-20 14:09:10.30628+05:30	1	\N	\N	f	f
1874	COST_CENTER	Cost Center	Amy's Bird Sanctuary	13710	2022-09-20 14:09:10.293069+05:30	2022-09-20 14:09:10.293116+05:30	1	\N	\N	f	f
1875	COST_CENTER	Cost Center	Bill's Windsurf Shop	13711	2022-09-20 14:09:10.293189+05:30	2022-09-20 14:09:10.29322+05:30	1	\N	\N	f	f
1876	COST_CENTER	Cost Center	Cool Cars	13712	2022-09-20 14:09:10.293285+05:30	2022-09-20 14:09:10.293315+05:30	1	\N	\N	f	f
1877	COST_CENTER	Cost Center	Diego Rodriguez	13713	2022-09-20 14:09:10.293377+05:30	2022-09-20 14:09:10.293406+05:30	1	\N	\N	f	f
1878	COST_CENTER	Cost Center	Dukes Basketball Camp	13714	2022-09-20 14:09:10.293468+05:30	2022-09-20 14:09:10.293497+05:30	1	\N	\N	f	f
1879	COST_CENTER	Cost Center	Dylan Sollfrank	13715	2022-09-20 14:09:10.293761+05:30	2022-09-20 14:09:10.293882+05:30	1	\N	\N	f	f
1880	COST_CENTER	Cost Center	Freeman Sporting Goods	13716	2022-09-20 14:09:10.293966+05:30	2022-09-20 14:09:10.293995+05:30	1	\N	\N	f	f
1881	COST_CENTER	Cost Center	Freeman Sporting Goods:0969 Ocean View Road	13717	2022-09-20 14:09:10.294059+05:30	2022-09-20 14:09:10.294088+05:30	1	\N	\N	f	f
1882	COST_CENTER	Cost Center	Freeman Sporting Goods:55 Twin Lane	13718	2022-09-20 14:09:10.29415+05:30	2022-09-20 14:09:10.294179+05:30	1	\N	\N	f	f
1883	COST_CENTER	Cost Center	Geeta Kalapatapu	13719	2022-09-20 14:09:10.294242+05:30	2022-09-20 14:09:10.294271+05:30	1	\N	\N	f	f
1884	COST_CENTER	Cost Center	Gevelber Photography	13720	2022-09-20 14:09:10.294423+05:30	2022-09-20 14:09:10.294535+05:30	1	\N	\N	f	f
1885	COST_CENTER	Cost Center	goat	13721	2022-09-20 14:09:10.294619+05:30	2022-09-20 14:09:10.29466+05:30	1	\N	\N	f	f
1886	COST_CENTER	Cost Center	Jeff's Jalopies	13722	2022-09-20 14:09:10.294722+05:30	2022-09-20 14:09:10.294751+05:30	1	\N	\N	f	f
1887	COST_CENTER	Cost Center	John Melton	13723	2022-09-20 14:09:10.294811+05:30	2022-09-20 14:09:10.294841+05:30	1	\N	\N	f	f
1888	COST_CENTER	Cost Center	Kate Whelan	13724	2022-09-20 14:09:10.294901+05:30	2022-09-20 14:09:10.29493+05:30	1	\N	\N	f	f
1889	COST_CENTER	Cost Center	Kookies by Kathy	13725	2022-09-20 14:09:10.294992+05:30	2022-09-20 14:09:10.295021+05:30	1	\N	\N	f	f
1890	COST_CENTER	Cost Center	Mark Cho	13726	2022-09-20 14:09:10.29508+05:30	2022-09-20 14:09:10.295109+05:30	1	\N	\N	f	f
1891	COST_CENTER	Cost Center	Paulsen Medical Supplies	13727	2022-09-20 14:09:10.295169+05:30	2022-09-20 14:09:10.295198+05:30	1	\N	\N	f	f
1892	COST_CENTER	Cost Center	Rago Travel Agency	13728	2022-09-20 14:09:10.295258+05:30	2022-09-20 14:09:10.295287+05:30	1	\N	\N	f	f
1893	COST_CENTER	Cost Center	Red Rock Diner	13729	2022-09-20 14:09:10.295455+05:30	2022-09-20 14:09:10.29554+05:30	1	\N	\N	f	f
1894	COST_CENTER	Cost Center	Rondonuwu Fruit and Vegi	13730	2022-09-20 14:09:10.295595+05:30	2022-09-20 14:09:10.295624+05:30	1	\N	\N	f	f
1895	COST_CENTER	Cost Center	Shara Barnett	13731	2022-09-20 14:09:10.295685+05:30	2022-09-20 14:09:10.295714+05:30	1	\N	\N	f	f
1896	COST_CENTER	Cost Center	Shara Barnett:Barnett Design	13732	2022-09-20 14:09:10.295774+05:30	2022-09-20 14:09:10.295803+05:30	1	\N	\N	f	f
681	PROJECT	Project	Project 5	203313	2022-09-20 14:09:06.849026+05:30	2022-09-20 14:09:06.849055+05:30	1	t	\N	f	f
1897	COST_CENTER	Cost Center	Sonnenschein Family Store	13733	2022-09-20 14:09:10.296923+05:30	2022-09-20 14:09:10.297618+05:30	1	\N	\N	f	f
1898	COST_CENTER	Cost Center	Sushi by Katsuyuki	13734	2022-09-20 14:09:10.298005+05:30	2022-09-20 14:09:10.298037+05:30	1	\N	\N	f	f
1899	COST_CENTER	Cost Center	Travis Waldron	13735	2022-09-20 14:09:10.298423+05:30	2022-09-20 14:09:10.298455+05:30	1	\N	\N	f	f
1900	COST_CENTER	Cost Center	Video Games by Dan	13736	2022-09-20 14:09:10.298671+05:30	2022-09-20 14:09:10.298849+05:30	1	\N	\N	f	f
1901	COST_CENTER	Cost Center	Weiskopf Consulting	13737	2022-09-20 14:09:10.299067+05:30	2022-09-20 14:09:10.299099+05:30	1	\N	\N	f	f
1902	COST_CENTER	Cost Center	FAE:Mini FAE	12489	2022-09-20 14:09:10.299396+05:30	2022-09-20 14:09:10.299575+05:30	1	\N	\N	f	f
1903	COST_CENTER	Cost Center	Portore	10201	2022-09-20 14:09:10.299794+05:30	2022-09-20 14:09:10.299825+05:30	1	\N	\N	f	f
1904	COST_CENTER	Cost Center	Powell Clean Tech	10202	2022-09-20 14:09:10.300037+05:30	2022-09-20 14:09:10.300182+05:30	1	\N	\N	f	f
1905	COST_CENTER	Cost Center	PPC Ltd.	10203	2022-09-20 14:09:10.300445+05:30	2022-09-20 14:09:10.300627+05:30	1	\N	\N	f	f
1906	COST_CENTER	Cost Center	Premier FMCG	10204	2022-09-20 14:09:10.300846+05:30	2022-09-20 14:09:10.300878+05:30	1	\N	\N	f	f
1907	COST_CENTER	Cost Center	Premier Inc	10205	2022-09-20 14:09:10.301403+05:30	2022-09-20 14:09:10.301642+05:30	1	\N	\N	f	f
1908	COST_CENTER	Cost Center	Prescott Pharmaceuticals	10206	2022-09-20 14:09:10.30188+05:30	2022-09-20 14:09:10.301913+05:30	1	\N	\N	f	f
1909	COST_CENTER	Cost Center	Primatech Paper	10207	2022-09-20 14:09:10.302186+05:30	2022-09-20 14:09:10.302215+05:30	1	\N	\N	f	f
1910	COST_CENTER	Cost Center	Primedia	10208	2022-09-20 14:09:10.302501+05:30	2022-09-20 14:09:10.302736+05:30	1	\N	\N	f	f
1911	COST_CENTER	Cost Center	Primedia Broadcasting	10209	2022-09-20 14:09:10.303095+05:30	2022-09-20 14:09:10.303544+05:30	1	\N	\N	f	f
1912	COST_CENTER	Cost Center	Projo	10210	2022-09-20 14:09:10.303819+05:30	2022-09-20 14:09:10.304049+05:30	1	\N	\N	f	f
1913	COST_CENTER	Cost Center	Proton Centric	10211	2022-09-20 14:09:10.304433+05:30	2022-09-20 14:09:10.304664+05:30	1	\N	\N	f	f
1914	COST_CENTER	Cost Center	Proweb	10212	2022-09-20 14:09:10.304892+05:30	2022-09-20 14:09:10.305076+05:30	1	\N	\N	f	f
1915	COST_CENTER	Cost Center	PUTCO	10213	2022-09-20 14:09:10.305319+05:30	2022-09-20 14:09:10.30535+05:30	1	\N	\N	f	f
1916	COST_CENTER	Cost Center	Quallaby Corporation	10214	2022-09-20 14:09:10.305517+05:30	2022-09-20 14:09:10.305718+05:30	1	\N	\N	f	f
1917	COST_CENTER	Cost Center	Quantum Networks	10215	2022-09-20 14:09:10.305912+05:30	2022-09-20 14:09:10.305942+05:30	1	\N	\N	f	f
1919	COST_CENTER	Cost Center	Rand Corporation	10217	2022-09-20 14:09:10.30641+05:30	2022-09-20 14:09:10.306569+05:30	1	\N	\N	f	f
1920	COST_CENTER	Cost Center	RCL Foods	10218	2022-09-20 14:09:10.306889+05:30	2022-09-20 14:09:10.30692+05:30	1	\N	\N	f	f
1921	COST_CENTER	Cost Center	RedFin Insurance	10219	2022-09-20 14:09:10.307118+05:30	2022-09-20 14:09:10.307239+05:30	1	\N	\N	f	f
1922	COST_CENTER	Cost Center	Render	10220	2022-09-20 14:09:10.307369+05:30	2022-09-20 14:09:10.307529+05:30	1	\N	\N	f	f
1923	COST_CENTER	Cost Center	Renegade Furniture Group	10221	2022-09-20 14:09:10.307718+05:30	2022-09-20 14:09:10.307748+05:30	1	\N	\N	f	f
1924	COST_CENTER	Cost Center	Rhycero	10222	2022-09-20 14:09:10.339568+05:30	2022-09-20 14:09:10.339612+05:30	1	\N	\N	f	f
1925	COST_CENTER	Cost Center	Riffwire	10223	2022-09-20 14:09:10.339688+05:30	2022-09-20 14:09:10.339719+05:30	1	\N	\N	f	f
1926	COST_CENTER	Cost Center	Riovic	10224	2022-09-20 14:09:10.339786+05:30	2022-09-20 14:09:10.339816+05:30	1	\N	\N	f	f
1927	COST_CENTER	Cost Center	Rossum Corporation	10225	2022-09-20 14:09:10.339881+05:30	2022-09-20 14:09:10.339911+05:30	1	\N	\N	f	f
1928	COST_CENTER	Cost Center	Rovos Rail	10226	2022-09-20 14:09:10.339974+05:30	2022-09-20 14:09:10.340004+05:30	1	\N	\N	f	f
1929	COST_CENTER	Cost Center	Roxxon	10227	2022-09-20 14:09:10.340066+05:30	2022-09-20 14:09:10.340096+05:30	1	\N	\N	f	f
1930	COST_CENTER	Cost Center	Sagacent Finance	10228	2022-09-20 14:09:10.340158+05:30	2022-09-20 14:09:10.340187+05:30	1	\N	\N	f	f
1931	COST_CENTER	Cost Center	Sailthru	10229	2022-09-20 14:09:10.340249+05:30	2022-09-20 14:09:10.340278+05:30	1	\N	\N	f	f
1932	COST_CENTER	Cost Center	Sanlam	10230	2022-09-20 14:09:10.340339+05:30	2022-09-20 14:09:10.340369+05:30	1	\N	\N	f	f
1933	COST_CENTER	Cost Center	Sasol	10231	2022-09-20 14:09:10.340633+05:30	2022-09-20 14:09:10.340667+05:30	1	\N	\N	f	f
1934	COST_CENTER	Cost Center	Seburo	10232	2022-09-20 14:09:10.340731+05:30	2022-09-20 14:09:10.34076+05:30	1	\N	\N	f	f
1935	COST_CENTER	Cost Center	Sempra Energy	10233	2022-09-20 14:09:10.340821+05:30	2022-09-20 14:09:10.34085+05:30	1	\N	\N	f	f
1936	COST_CENTER	Cost Center	Serrano Genomics	10234	2022-09-20 14:09:10.34091+05:30	2022-09-20 14:09:10.340938+05:30	1	\N	\N	f	f
1937	COST_CENTER	Cost Center	Shinra Electric	10235	2022-09-20 14:09:10.340998+05:30	2022-09-20 14:09:10.341027+05:30	1	\N	\N	f	f
1938	COST_CENTER	Cost Center	Shoprite	10236	2022-09-20 14:09:10.341087+05:30	2022-09-20 14:09:10.341115+05:30	1	\N	\N	f	f
3179	MERCHANT	Merchant	Entity V600	852	2022-09-20 14:10:24.029339+05:30	2022-09-20 14:10:24.029366+05:30	1	\N	\N	f	f
1939	COST_CENTER	Cost Center	Simeon	10237	2022-09-20 14:09:10.341175+05:30	2022-09-20 14:09:10.341204+05:30	1	\N	\N	f	f
1940	COST_CENTER	Cost Center	Skimia	10238	2022-09-20 14:09:10.341263+05:30	2022-09-20 14:09:10.341292+05:30	1	\N	\N	f	f
1941	COST_CENTER	Cost Center	Skinte	10239	2022-09-20 14:09:10.341518+05:30	2022-09-20 14:09:10.341582+05:30	1	\N	\N	f	f
1942	COST_CENTER	Cost Center	Skivee	10240	2022-09-20 14:09:10.341679+05:30	2022-09-20 14:09:10.341709+05:30	1	\N	\N	f	f
1943	COST_CENTER	Cost Center	Sonicwall, Inc.	10241	2022-09-20 14:09:10.341772+05:30	2022-09-20 14:09:10.341801+05:30	1	\N	\N	f	f
1944	COST_CENTER	Cost Center	South African Breweries	10242	2022-09-20 14:09:10.341863+05:30	2022-09-20 14:09:10.341892+05:30	1	\N	\N	f	f
1945	COST_CENTER	Cost Center	South African Broadcasting Corporation	10243	2022-09-20 14:09:10.341954+05:30	2022-09-20 14:09:10.341983+05:30	1	\N	\N	f	f
1946	COST_CENTER	Cost Center	South Bay Medical Center	10244	2022-09-20 14:09:10.342043+05:30	2022-09-20 14:09:10.342073+05:30	1	\N	\N	f	f
1947	COST_CENTER	Cost Center	Southern Orthopedics	10245	2022-09-20 14:09:10.342133+05:30	2022-09-20 14:09:10.342162+05:30	1	\N	\N	f	f
1948	COST_CENTER	Cost Center	Soylent Corporation	10246	2022-09-20 14:09:10.342222+05:30	2022-09-20 14:09:10.342251+05:30	1	\N	\N	f	f
1949	COST_CENTER	Cost Center	Spencer, Scott and Dwyer	10247	2022-09-20 14:09:10.342317+05:30	2022-09-20 14:09:10.342346+05:30	1	\N	\N	f	f
1950	COST_CENTER	Cost Center	Spine Rehab Center	10248	2022-09-20 14:09:10.342757+05:30	2022-09-20 14:09:10.342821+05:30	1	\N	\N	f	f
1951	COST_CENTER	Cost Center	Standard Bank	10249	2022-09-20 14:09:10.342962+05:30	2022-09-20 14:09:10.343008+05:30	1	\N	\N	f	f
1952	COST_CENTER	Cost Center	Stark Industries	10250	2022-09-20 14:09:10.343136+05:30	2022-09-20 14:09:10.343402+05:30	1	\N	\N	f	f
1953	COST_CENTER	Cost Center	StarSat, South Africa	10251	2022-09-20 14:09:10.34353+05:30	2022-09-20 14:09:10.343577+05:30	1	\N	\N	f	f
1954	COST_CENTER	Cost Center	Stay Puft	10252	2022-09-20 14:09:10.343697+05:30	2022-09-20 14:09:10.343745+05:30	1	\N	\N	f	f
1955	COST_CENTER	Cost Center	Stoxnetwork Corporation	10253	2022-09-20 14:09:10.343868+05:30	2022-09-20 14:09:10.344484+05:30	1	\N	\N	f	f
1956	COST_CENTER	Cost Center	Strickland Propane	10254	2022-09-20 14:09:10.344669+05:30	2022-09-20 14:09:10.344725+05:30	1	\N	\N	f	f
1957	COST_CENTER	Cost Center	Sunshine Desserts	10255	2022-09-20 14:09:10.344862+05:30	2022-09-20 14:09:10.344925+05:30	1	\N	\N	f	f
1958	COST_CENTER	Cost Center	Talcomp Management Services	10256	2022-09-20 14:09:10.345428+05:30	2022-09-20 14:09:10.345561+05:30	1	\N	\N	f	f
1959	COST_CENTER	Cost Center	Tanoodle	10257	2022-09-20 14:09:10.345678+05:30	2022-09-20 14:09:10.345724+05:30	1	\N	\N	f	f
1960	COST_CENTER	Cost Center	Telkom	10258	2022-09-20 14:09:10.345841+05:30	2022-09-20 14:09:10.345886+05:30	1	\N	\N	f	f
1961	COST_CENTER	Cost Center	Telkom Mobile	10259	2022-09-20 14:09:10.34602+05:30	2022-09-20 14:09:10.346075+05:30	1	\N	\N	f	f
1962	COST_CENTER	Cost Center	TetraCorp	10260	2022-09-20 14:09:10.346185+05:30	2022-09-20 14:09:10.346225+05:30	1	\N	\N	f	f
1963	COST_CENTER	Cost Center	The android's Dungeon	10261	2022-09-20 14:09:10.346324+05:30	2022-09-20 14:09:10.346364+05:30	1	\N	\N	f	f
1964	COST_CENTER	Cost Center	The HCI Group	10262	2022-09-20 14:09:10.346608+05:30	2022-09-20 14:09:10.346657+05:30	1	\N	\N	f	f
1965	COST_CENTER	Cost Center	The Vanguard Group, Inc.	10263	2022-09-20 14:09:10.346916+05:30	2022-09-20 14:09:10.346971+05:30	1	\N	\N	f	f
1966	COST_CENTER	Cost Center	ThinkLite	10264	2022-09-20 14:09:10.347111+05:30	2022-09-20 14:09:10.347143+05:30	1	\N	\N	f	f
1967	COST_CENTER	Cost Center	Thoughtstorm	10265	2022-09-20 14:09:10.347211+05:30	2022-09-20 14:09:10.34724+05:30	1	\N	\N	f	f
1968	COST_CENTER	Cost Center	Thoughtworks	10266	2022-09-20 14:09:10.347303+05:30	2022-09-20 14:09:10.347333+05:30	1	\N	\N	f	f
1969	COST_CENTER	Cost Center	Tiger Brands	10267	2022-09-20 14:09:10.347508+05:30	2022-09-20 14:09:10.347538+05:30	1	\N	\N	f	f
1970	COST_CENTER	Cost Center	Times Media Group	10268	2022-09-20 14:09:10.347601+05:30	2022-09-20 14:09:10.34763+05:30	1	\N	\N	f	f
1971	COST_CENTER	Cost Center	Titanium Corporation Inc.	10269	2022-09-20 14:09:10.347705+05:30	2022-09-20 14:09:10.347728+05:30	1	\N	\N	f	f
1972	COST_CENTER	Cost Center	Tongaat Hulett	10270	2022-09-20 14:09:10.347789+05:30	2022-09-20 14:09:10.347819+05:30	1	\N	\N	f	f
1973	COST_CENTER	Cost Center	Topdrive	10271	2022-09-20 14:09:10.34788+05:30	2022-09-20 14:09:10.347909+05:30	1	\N	\N	f	f
1974	COST_CENTER	Cost Center	Topicstorm	10272	2022-09-20 14:09:10.37308+05:30	2022-09-20 14:09:10.373404+05:30	1	\N	\N	f	f
1975	COST_CENTER	Cost Center	Topicware	10273	2022-09-20 14:09:10.373832+05:30	2022-09-20 14:09:10.373864+05:30	1	\N	\N	f	f
1976	COST_CENTER	Cost Center	Topiczoom	10274	2022-09-20 14:09:10.374098+05:30	2022-09-20 14:09:10.374371+05:30	1	\N	\N	f	f
1977	COST_CENTER	Cost Center	Trade Federation	10275	2022-09-20 14:09:10.374617+05:30	2022-09-20 14:09:10.374648+05:30	1	\N	\N	f	f
1978	COST_CENTER	Cost Center	Transnet	10276	2022-09-20 14:09:10.374882+05:30	2022-09-20 14:09:10.375104+05:30	1	\N	\N	f	f
1979	COST_CENTER	Cost Center	Treadstone	10277	2022-09-20 14:09:10.375392+05:30	2022-09-20 14:09:10.375527+05:30	1	\N	\N	f	f
1980	COST_CENTER	Cost Center	Tricell	10278	2022-09-20 14:09:10.375747+05:30	2022-09-20 14:09:10.37578+05:30	1	\N	\N	f	f
1981	COST_CENTER	Cost Center	Trilith	10279	2022-09-20 14:09:10.375976+05:30	2022-09-20 14:09:10.376131+05:30	1	\N	\N	f	f
1982	COST_CENTER	Cost Center	TriOptimum	10280	2022-09-20 14:09:10.376376+05:30	2022-09-20 14:09:10.376405+05:30	1	\N	\N	f	f
1983	COST_CENTER	Cost Center	Trudeo	10281	2022-09-20 14:09:10.376584+05:30	2022-09-20 14:09:10.376732+05:30	1	\N	\N	f	f
1984	COST_CENTER	Cost Center	Trunyx	10282	2022-09-20 14:09:10.376932+05:30	2022-09-20 14:09:10.376959+05:30	1	\N	\N	f	f
1985	COST_CENTER	Cost Center	Twitterbeat	10283	2022-09-20 14:09:10.377464+05:30	2022-09-20 14:09:10.377624+05:30	1	\N	\N	f	f
1986	COST_CENTER	Cost Center	Tyrell Corp.	10284	2022-09-20 14:09:10.377823+05:30	2022-09-20 14:09:10.377854+05:30	1	\N	\N	f	f
1987	COST_CENTER	Cost Center	Ultor	10285	2022-09-20 14:09:10.378049+05:30	2022-09-20 14:09:10.378177+05:30	1	\N	\N	f	f
1988	COST_CENTER	Cost Center	Umbrella Corporation	10286	2022-09-20 14:09:10.378398+05:30	2022-09-20 14:09:10.378553+05:30	1	\N	\N	f	f
1989	COST_CENTER	Cost Center	Union Aerospace Corporation	10287	2022-09-20 14:09:10.378747+05:30	2022-09-20 14:09:10.378777+05:30	1	\N	\N	f	f
1990	COST_CENTER	Cost Center	United Liberty Paper	10288	2022-09-20 14:09:10.378965+05:30	2022-09-20 14:09:10.379122+05:30	1	\N	\N	f	f
1991	COST_CENTER	Cost Center	United Methodist Communications	10289	2022-09-20 14:09:10.379387+05:30	2022-09-20 14:09:10.379417+05:30	1	\N	\N	f	f
1992	COST_CENTER	Cost Center	United Robotronics	10290	2022-09-20 14:09:10.379582+05:30	2022-09-20 14:09:10.379612+05:30	1	\N	\N	f	f
1993	COST_CENTER	Cost Center	United Security Bank	10291	2022-09-20 14:09:10.379672+05:30	2022-09-20 14:09:10.379701+05:30	1	\N	\N	f	f
1994	COST_CENTER	Cost Center	Universal Exports	10292	2022-09-20 14:09:10.379762+05:30	2022-09-20 14:09:10.379791+05:30	1	\N	\N	f	f
1995	COST_CENTER	Cost Center	Universal Terraforming	10293	2022-09-20 14:09:10.379852+05:30	2022-09-20 14:09:10.379881+05:30	1	\N	\N	f	f
1996	COST_CENTER	Cost Center	U-North	10294	2022-09-20 14:09:10.379942+05:30	2022-09-20 14:09:10.37997+05:30	1	\N	\N	f	f
1997	COST_CENTER	Cost Center	Uplift Services	10295	2022-09-20 14:09:10.380031+05:30	2022-09-20 14:09:10.38006+05:30	1	\N	\N	f	f
1998	COST_CENTER	Cost Center	Uplink	10296	2022-09-20 14:09:10.38012+05:30	2022-09-20 14:09:10.380148+05:30	1	\N	\N	f	f
1999	COST_CENTER	Cost Center	Upton-Webber	10297	2022-09-20 14:09:10.380208+05:30	2022-09-20 14:09:10.380237+05:30	1	\N	\N	f	f
2000	COST_CENTER	Cost Center	Vaillante	10298	2022-09-20 14:09:10.380298+05:30	2022-09-20 14:09:10.380327+05:30	1	\N	\N	f	f
2001	COST_CENTER	Cost Center	Vandelay Industries	10299	2022-09-20 14:09:10.380473+05:30	2022-09-20 14:09:10.380502+05:30	1	\N	\N	f	f
2002	COST_CENTER	Cost Center	Vapid Battery	10300	2022-09-20 14:09:10.380562+05:30	2022-09-20 14:09:10.380592+05:30	1	\N	\N	f	f
2003	COST_CENTER	Cost Center	Veridian Dynamics	10301	2022-09-20 14:09:10.380652+05:30	2022-09-20 14:09:10.380681+05:30	1	\N	\N	f	f
2004	COST_CENTER	Cost Center	VersaLife Corporation	10302	2022-09-20 14:09:10.380741+05:30	2022-09-20 14:09:10.38077+05:30	1	\N	\N	f	f
2005	COST_CENTER	Cost Center	Vertous	10303	2022-09-20 14:09:10.380829+05:30	2022-09-20 14:09:10.380858+05:30	1	\N	\N	f	f
2006	COST_CENTER	Cost Center	Virtela Communications	10304	2022-09-20 14:09:10.380918+05:30	2022-09-20 14:09:10.380947+05:30	1	\N	\N	f	f
2007	COST_CENTER	Cost Center	Voolith	10305	2022-09-20 14:09:10.381007+05:30	2022-09-20 14:09:10.381036+05:30	1	\N	\N	f	f
2008	COST_CENTER	Cost Center	Voomm	10306	2022-09-20 14:09:10.381095+05:30	2022-09-20 14:09:10.381124+05:30	1	\N	\N	f	f
2009	COST_CENTER	Cost Center	Voonix	10307	2022-09-20 14:09:10.381184+05:30	2022-09-20 14:09:10.381213+05:30	1	\N	\N	f	f
2010	COST_CENTER	Cost Center	Wauwatosa Medical Group	10308	2022-09-20 14:09:10.381274+05:30	2022-09-20 14:09:10.381303+05:30	1	\N	\N	f	f
2011	COST_CENTER	Cost Center	Wayne Enterprises	10309	2022-09-20 14:09:10.381488+05:30	2022-09-20 14:09:10.381512+05:30	1	\N	\N	f	f
2012	COST_CENTER	Cost Center	Wernham Hogg	10310	2022-09-20 14:09:10.381583+05:30	2022-09-20 14:09:10.381733+05:30	1	\N	\N	f	f
2013	COST_CENTER	Cost Center	West Oak Capital Group Inc	10311	2022-09-20 14:09:10.38191+05:30	2022-09-20 14:09:10.381939+05:30	1	\N	\N	f	f
2014	COST_CENTER	Cost Center	Weyland-Yutani	10312	2022-09-20 14:09:10.382+05:30	2022-09-20 14:09:10.382029+05:30	1	\N	\N	f	f
2015	COST_CENTER	Cost Center	Wikibox	10313	2022-09-20 14:09:10.382089+05:30	2022-09-20 14:09:10.382117+05:30	1	\N	\N	f	f
2016	COST_CENTER	Cost Center	Woodlands Medical Group	10314	2022-09-20 14:09:10.382177+05:30	2022-09-20 14:09:10.382207+05:30	1	\N	\N	f	f
2017	COST_CENTER	Cost Center	X-Com	10315	2022-09-20 14:09:10.382361+05:30	2022-09-20 14:09:10.38239+05:30	1	\N	\N	f	f
2018	COST_CENTER	Cost Center	Yata	10316	2022-09-20 14:09:10.38245+05:30	2022-09-20 14:09:10.382479+05:30	1	\N	\N	f	f
2019	COST_CENTER	Cost Center	YellowHammer	10317	2022-09-20 14:09:10.382539+05:30	2022-09-20 14:09:10.382568+05:30	1	\N	\N	f	f
2020	COST_CENTER	Cost Center	Yodel	10318	2022-09-20 14:09:10.382628+05:30	2022-09-20 14:09:10.382656+05:30	1	\N	\N	f	f
2021	COST_CENTER	Cost Center	Yombu	10319	2022-09-20 14:09:10.382717+05:30	2022-09-20 14:09:10.382746+05:30	1	\N	\N	f	f
2022	COST_CENTER	Cost Center	Youbridge	10320	2022-09-20 14:09:10.382806+05:30	2022-09-20 14:09:10.382835+05:30	1	\N	\N	f	f
2023	COST_CENTER	Cost Center	Yoyodyne Propulsion	10321	2022-09-20 14:09:10.382895+05:30	2022-09-20 14:09:10.382923+05:30	1	\N	\N	f	f
2024	COST_CENTER	Cost Center	Zimms	10322	2022-09-20 14:09:10.389786+05:30	2022-09-20 14:09:10.389827+05:30	1	\N	\N	f	f
2025	COST_CENTER	Cost Center	Ziodex Industries	10323	2022-09-20 14:09:10.389894+05:30	2022-09-20 14:09:10.389922+05:30	1	\N	\N	f	f
2026	COST_CENTER	Cost Center	Zoombeat	10324	2022-09-20 14:09:10.389982+05:30	2022-09-20 14:09:10.390158+05:30	1	\N	\N	f	f
2027	COST_CENTER	Cost Center	Zoozzy	10325	2022-09-20 14:09:10.390412+05:30	2022-09-20 14:09:10.390559+05:30	1	\N	\N	f	f
2028	COST_CENTER	Cost Center	De Beers	10004	2022-09-20 14:09:10.390772+05:30	2022-09-20 14:09:10.390799+05:30	1	\N	\N	f	f
2029	COST_CENTER	Cost Center	De Bortoli Wines	10005	2022-09-20 14:09:10.391413+05:30	2022-09-20 14:09:10.391449+05:30	1	\N	\N	f	f
2030	COST_CENTER	Cost Center	Defy Appliances	10006	2022-09-20 14:09:10.391524+05:30	2022-09-20 14:09:10.391551+05:30	1	\N	\N	f	f
2031	COST_CENTER	Cost Center	De Haan's Bus and Coach	10007	2022-09-20 14:09:10.391609+05:30	2022-09-20 14:09:10.391636+05:30	1	\N	\N	f	f
2032	COST_CENTER	Cost Center	Delos	10008	2022-09-20 14:09:10.391693+05:30	2022-09-20 14:09:10.39172+05:30	1	\N	\N	f	f
2033	COST_CENTER	Cost Center	Delta Electricity	10009	2022-09-20 14:09:10.391777+05:30	2022-09-20 14:09:10.391804+05:30	1	\N	\N	f	f
2034	COST_CENTER	Cost Center	Delta Hotels	10010	2022-09-20 14:09:10.39186+05:30	2022-09-20 14:09:10.391887+05:30	1	\N	\N	f	f
2035	COST_CENTER	Cost Center	Denticare Of Oklahoma	10011	2022-09-20 14:09:10.391943+05:30	2022-09-20 14:09:10.39197+05:30	1	\N	\N	f	f
2036	COST_CENTER	Cost Center	Deon International	10012	2022-09-20 14:09:10.392026+05:30	2022-09-20 14:09:10.392054+05:30	1	\N	\N	f	f
2037	COST_CENTER	Cost Center	Devbug	10013	2022-09-20 14:09:10.392109+05:30	2022-09-20 14:09:10.392137+05:30	1	\N	\N	f	f
2038	COST_CENTER	Cost Center	Devlin MacGregor	10014	2022-09-20 14:09:10.392193+05:30	2022-09-20 14:09:10.39222+05:30	1	\N	\N	f	f
2039	COST_CENTER	Cost Center	Dhaliwal Labs	10015	2022-09-20 14:09:10.392276+05:30	2022-09-20 14:09:10.392303+05:30	1	\N	\N	f	f
2040	COST_CENTER	Cost Center	Dharma Initiative	10016	2022-09-20 14:09:10.392359+05:30	2022-09-20 14:09:10.392503+05:30	1	\N	\N	f	f
682	PROJECT	Project	Project 6	203314	2022-09-20 14:09:06.84919+05:30	2022-09-20 14:09:06.849364+05:30	1	t	\N	f	f
2041	COST_CENTER	Cost Center	Dick Smith Electronics	10017	2022-09-20 14:09:10.392592+05:30	2022-09-20 14:09:10.39262+05:30	1	\N	\N	f	f
2042	COST_CENTER	Cost Center	Digital Bio	10018	2022-09-20 14:09:10.392676+05:30	2022-09-20 14:09:10.392704+05:30	1	\N	\N	f	f
2043	COST_CENTER	Cost Center	Digital Extremes	10019	2022-09-20 14:09:10.39276+05:30	2022-09-20 14:09:10.392787+05:30	1	\N	\N	f	f
2044	COST_CENTER	Cost Center	Digivation Industries	10020	2022-09-20 14:09:10.392843+05:30	2022-09-20 14:09:10.392871+05:30	1	\N	\N	f	f
2045	COST_CENTER	Cost Center	Dimension Data	10021	2022-09-20 14:09:10.392927+05:30	2022-09-20 14:09:10.392954+05:30	1	\N	\N	f	f
2046	COST_CENTER	Cost Center	Discovery Air Defence	10022	2022-09-20 14:09:10.39301+05:30	2022-09-20 14:09:10.393037+05:30	1	\N	\N	f	f
104	CATEGORY	Category	hello	184630	2022-09-20 14:09:03.373599+05:30	2022-09-20 14:09:03.373619+05:30	1	t	\N	f	f
2047	COST_CENTER	Cost Center	Divavu	10023	2022-09-20 14:09:10.393093+05:30	2022-09-20 14:09:10.393133+05:30	1	\N	\N	f	f
2048	COST_CENTER	Cost Center	Dominion Voting Systems	10024	2022-09-20 14:09:10.393838+05:30	2022-09-20 14:09:10.393882+05:30	1	\N	\N	f	f
2049	COST_CENTER	Cost Center	Donner Metals	10025	2022-09-20 14:09:10.394087+05:30	2022-09-20 14:09:10.394118+05:30	1	\N	\N	f	f
2050	COST_CENTER	Cost Center	Dorf Clark Industries	10026	2022-09-20 14:09:10.394183+05:30	2022-09-20 14:09:10.39421+05:30	1	\N	\N	f	f
2051	COST_CENTER	Cost Center	Downer Group	10027	2022-09-20 14:09:10.394485+05:30	2022-09-20 14:09:10.394543+05:30	1	\N	\N	f	f
2052	COST_CENTER	Cost Center	Duff	10028	2022-09-20 14:09:10.394608+05:30	2022-09-20 14:09:10.394635+05:30	1	\N	\N	f	f
2053	COST_CENTER	Cost Center	Dunder Mifflin	10029	2022-09-20 14:09:10.394694+05:30	2022-09-20 14:09:10.394721+05:30	1	\N	\N	f	f
2054	COST_CENTER	Cost Center	Dymocks Booksellers	10030	2022-09-20 14:09:10.394779+05:30	2022-09-20 14:09:10.394806+05:30	1	\N	\N	f	f
2055	COST_CENTER	Cost Center	Dynabox	10031	2022-09-20 14:09:10.394863+05:30	2022-09-20 14:09:10.39489+05:30	1	\N	\N	f	f
2056	COST_CENTER	Cost Center	Dynamsoft	10032	2022-09-20 14:09:10.394947+05:30	2022-09-20 14:09:10.394975+05:30	1	\N	\N	f	f
2057	COST_CENTER	Cost Center	Dynatechnics	10033	2022-09-20 14:09:10.395031+05:30	2022-09-20 14:09:10.395059+05:30	1	\N	\N	f	f
2058	COST_CENTER	Cost Center	EA Black Box	10034	2022-09-20 14:09:10.395115+05:30	2022-09-20 14:09:10.395142+05:30	1	\N	\N	f	f
2059	COST_CENTER	Cost Center	Eadel	10035	2022-09-20 14:09:10.3952+05:30	2022-09-20 14:09:10.395227+05:30	1	\N	\N	f	f
2060	COST_CENTER	Cost Center	Eagle Boys	10036	2022-09-20 14:09:10.395285+05:30	2022-09-20 14:09:10.395312+05:30	1	\N	\N	f	f
2061	COST_CENTER	Cost Center	Ecumena	10037	2022-09-20 14:09:10.395369+05:30	2022-09-20 14:09:10.395528+05:30	1	\N	\N	f	f
2062	COST_CENTER	Cost Center	Edgars	10038	2022-09-20 14:09:10.395598+05:30	2022-09-20 14:09:10.395626+05:30	1	\N	\N	f	f
2063	COST_CENTER	Cost Center	Edgeblab	10039	2022-09-20 14:09:10.395682+05:30	2022-09-20 14:09:10.395709+05:30	1	\N	\N	f	f
2064	COST_CENTER	Cost Center	Elders Limited	10040	2022-09-20 14:09:10.395765+05:30	2022-09-20 14:09:10.395792+05:30	1	\N	\N	f	f
2065	COST_CENTER	Cost Center	Electrohome	10041	2022-09-20 14:09:10.395848+05:30	2022-09-20 14:09:10.395875+05:30	1	\N	\N	f	f
2066	COST_CENTER	Cost Center	Elfin Cars	10042	2022-09-20 14:09:10.395931+05:30	2022-09-20 14:09:10.395958+05:30	1	\N	\N	f	f
2067	COST_CENTER	Cost Center	Emera	10043	2022-09-20 14:09:10.396014+05:30	2022-09-20 14:09:10.396041+05:30	1	\N	\N	f	f
2068	COST_CENTER	Cost Center	ENCOM	10044	2022-09-20 14:09:10.396097+05:30	2022-09-20 14:09:10.396124+05:30	1	\N	\N	f	f
2069	COST_CENTER	Cost Center	Entity 100	10045	2022-09-20 14:09:10.39618+05:30	2022-09-20 14:09:10.396207+05:30	1	\N	\N	f	f
2070	COST_CENTER	Cost Center	Entity 200	10046	2022-09-20 14:09:10.396262+05:30	2022-09-20 14:09:10.396289+05:30	1	\N	\N	f	f
2071	COST_CENTER	Cost Center	Entity 300	10047	2022-09-20 14:09:10.396358+05:30	2022-09-20 14:09:10.396494+05:30	1	\N	\N	f	f
2072	COST_CENTER	Cost Center	Entity 400	10048	2022-09-20 14:09:10.396562+05:30	2022-09-20 14:09:10.396589+05:30	1	\N	\N	f	f
2073	COST_CENTER	Cost Center	Entity 500	10049	2022-09-20 14:09:10.396646+05:30	2022-09-20 14:09:10.396673+05:30	1	\N	\N	f	f
2074	COST_CENTER	Cost Center	Entity 600	10050	2022-09-20 14:09:10.402003+05:30	2022-09-20 14:09:10.402046+05:30	1	\N	\N	f	f
2075	COST_CENTER	Cost Center	Entity 700	10051	2022-09-20 14:09:10.402114+05:30	2022-09-20 14:09:10.402143+05:30	1	\N	\N	f	f
2076	COST_CENTER	Cost Center	Enwave	10052	2022-09-20 14:09:10.402203+05:30	2022-09-20 14:09:10.40223+05:30	1	\N	\N	f	f
2077	COST_CENTER	Cost Center	Eskom	10053	2022-09-20 14:09:10.402289+05:30	2022-09-20 14:09:10.402317+05:30	1	\N	\N	f	f
2078	COST_CENTER	Cost Center	e.tv	10054	2022-09-20 14:09:10.402529+05:30	2022-09-20 14:09:10.402573+05:30	1	\N	\N	f	f
2079	COST_CENTER	Cost Center	Ewing Oil	10055	2022-09-20 14:09:10.402636+05:30	2022-09-20 14:09:10.402664+05:30	1	\N	\N	f	f
2080	COST_CENTER	Cost Center	Exxaro	10056	2022-09-20 14:09:10.402722+05:30	2022-09-20 14:09:10.402749+05:30	1	\N	\N	f	f
2081	COST_CENTER	Cost Center	EZ Services	10057	2022-09-20 14:09:10.402806+05:30	2022-09-20 14:09:10.402834+05:30	1	\N	\N	f	f
2082	COST_CENTER	Cost Center	Fab Seven	10058	2022-09-20 14:09:10.402891+05:30	2022-09-20 14:09:10.402918+05:30	1	\N	\N	f	f
2083	COST_CENTER	Cost Center	Fairmont Hotels and Resorts	10059	2022-09-20 14:09:10.402975+05:30	2022-09-20 14:09:10.403002+05:30	1	\N	\N	f	f
2084	COST_CENTER	Cost Center	FandP Manufacturing Inc.	10060	2022-09-20 14:09:10.403059+05:30	2022-09-20 14:09:10.403086+05:30	1	\N	\N	f	f
2085	COST_CENTER	Cost Center	Farmers of North America	10061	2022-09-20 14:09:10.403143+05:30	2022-09-20 14:09:10.40317+05:30	1	\N	\N	f	f
2086	COST_CENTER	Cost Center	Feednation	10062	2022-09-20 14:09:10.403227+05:30	2022-09-20 14:09:10.403255+05:30	1	\N	\N	f	f
2087	COST_CENTER	Cost Center	Feedspan	10063	2022-09-20 14:09:10.403312+05:30	2022-09-20 14:09:10.40334+05:30	1	\N	\N	f	f
2088	COST_CENTER	Cost Center	Fido Solutions	10064	2022-09-20 14:09:10.403535+05:30	2022-09-20 14:09:10.403564+05:30	1	\N	\N	f	f
2089	COST_CENTER	Cost Center	Finscent	10065	2022-09-20 14:09:10.40362+05:30	2022-09-20 14:09:10.403647+05:30	1	\N	\N	f	f
2090	COST_CENTER	Cost Center	First Air	10066	2022-09-20 14:09:10.403704+05:30	2022-09-20 14:09:10.403731+05:30	1	\N	\N	f	f
2091	COST_CENTER	Cost Center	First National Bank	10067	2022-09-20 14:09:10.403788+05:30	2022-09-20 14:09:10.403815+05:30	1	\N	\N	f	f
2092	COST_CENTER	Cost Center	First Rand	10068	2022-09-20 14:09:10.403872+05:30	2022-09-20 14:09:10.403899+05:30	1	\N	\N	f	f
2093	COST_CENTER	Cost Center	Flashdog	10069	2022-09-20 14:09:10.403955+05:30	2022-09-20 14:09:10.403982+05:30	1	\N	\N	f	f
2094	COST_CENTER	Cost Center	Flickr	10070	2022-09-20 14:09:10.404039+05:30	2022-09-20 14:09:10.404066+05:30	1	\N	\N	f	f
2095	COST_CENTER	Cost Center	FNB Connect	10071	2022-09-20 14:09:10.404123+05:30	2022-09-20 14:09:10.40415+05:30	1	\N	\N	f	f
2096	COST_CENTER	Cost Center	Focus Med	10072	2022-09-20 14:09:10.404207+05:30	2022-09-20 14:09:10.404234+05:30	1	\N	\N	f	f
2097	COST_CENTER	Cost Center	Food Lover's Market	10073	2022-09-20 14:09:10.40429+05:30	2022-09-20 14:09:10.404317+05:30	1	\N	\N	f	f
2098	COST_CENTER	Cost Center	Ford Motor Company of Canada	10074	2022-09-20 14:09:10.404496+05:30	2022-09-20 14:09:10.404535+05:30	1	\N	\N	f	f
2099	COST_CENTER	Cost Center	Four Seasons Hotels and Resorts	10075	2022-09-20 14:09:10.404593+05:30	2022-09-20 14:09:10.40462+05:30	1	\N	\N	f	f
2100	COST_CENTER	Cost Center	Freedom Mobile	10076	2022-09-20 14:09:10.404677+05:30	2022-09-20 14:09:10.404704+05:30	1	\N	\N	f	f
2101	COST_CENTER	Cost Center	Fuji Air	10077	2022-09-20 14:09:10.40476+05:30	2022-09-20 14:09:10.404788+05:30	1	\N	\N	f	f
2102	COST_CENTER	Cost Center	Gadgetron	10078	2022-09-20 14:09:10.404845+05:30	2022-09-20 14:09:10.404872+05:30	1	\N	\N	f	f
2103	COST_CENTER	Cost Center	Gallo Record Company	10079	2022-09-20 14:09:10.404928+05:30	2022-09-20 14:09:10.404956+05:30	1	\N	\N	f	f
2104	COST_CENTER	Cost Center	GBD Inc	10080	2022-09-20 14:09:10.405012+05:30	2022-09-20 14:09:10.405039+05:30	1	\N	\N	f	f
2105	COST_CENTER	Cost Center	Gemini Manufacturing Services	10081	2022-09-20 14:09:10.405096+05:30	2022-09-20 14:09:10.405123+05:30	1	\N	\N	f	f
2106	COST_CENTER	Cost Center	Genentech, Inc.	10082	2022-09-20 14:09:10.405179+05:30	2022-09-20 14:09:10.405206+05:30	1	\N	\N	f	f
2107	COST_CENTER	Cost Center	Georgia Power Company	10083	2022-09-20 14:09:10.405262+05:30	2022-09-20 14:09:10.405289+05:30	1	\N	\N	f	f
2108	COST_CENTER	Cost Center	Gijima Group	10084	2022-09-20 14:09:10.405345+05:30	2022-09-20 14:09:10.405494+05:30	1	\N	\N	f	f
2109	COST_CENTER	Cost Center	Gilead Sciences	10085	2022-09-20 14:09:10.405563+05:30	2022-09-20 14:09:10.405591+05:30	1	\N	\N	f	f
2110	COST_CENTER	Cost Center	Global Dynamics	10086	2022-09-20 14:09:10.405648+05:30	2022-09-20 14:09:10.405675+05:30	1	\N	\N	f	f
2111	COST_CENTER	Cost Center	Global Manufacturing	10087	2022-09-20 14:09:10.405731+05:30	2022-09-20 14:09:10.405759+05:30	1	\N	\N	f	f
2112	COST_CENTER	Cost Center	Globochem	10088	2022-09-20 14:09:10.405815+05:30	2022-09-20 14:09:10.405842+05:30	1	\N	\N	f	f
2113	COST_CENTER	Cost Center	Golden Arrow Bus Services	10089	2022-09-20 14:09:10.405898+05:30	2022-09-20 14:09:10.405925+05:30	1	\N	\N	f	f
2114	COST_CENTER	Cost Center	Gold Fields	10090	2022-09-20 14:09:10.405981+05:30	2022-09-20 14:09:10.406009+05:30	1	\N	\N	f	f
2115	COST_CENTER	Cost Center	Grand Trunk Semaphore	10091	2022-09-20 14:09:10.406065+05:30	2022-09-20 14:09:10.406092+05:30	1	\N	\N	f	f
2116	COST_CENTER	Cost Center	Grayson Sky Domes	10092	2022-09-20 14:09:10.406148+05:30	2022-09-20 14:09:10.406176+05:30	1	\N	\N	f	f
2117	COST_CENTER	Cost Center	GSATi	10093	2022-09-20 14:09:10.406232+05:30	2022-09-20 14:09:10.40626+05:30	1	\N	\N	f	f
2118	COST_CENTER	Cost Center	GS Industries	10094	2022-09-20 14:09:10.406316+05:30	2022-09-20 14:09:10.406343+05:30	1	\N	\N	f	f
2119	COST_CENTER	Cost Center	Gulf States Paper Corporation	10095	2022-09-20 14:09:10.406528+05:30	2022-09-20 14:09:10.406569+05:30	1	\N	\N	f	f
2120	COST_CENTER	Cost Center	Hanso Foundation	10096	2022-09-20 14:09:10.406648+05:30	2022-09-20 14:09:10.406676+05:30	1	\N	\N	f	f
2121	COST_CENTER	Cost Center	Harmony Gold	10097	2022-09-20 14:09:10.406733+05:30	2022-09-20 14:09:10.406761+05:30	1	\N	\N	f	f
2122	COST_CENTER	Cost Center	Heart and Vascular Clinic	10098	2022-09-20 14:09:10.406817+05:30	2022-09-20 14:09:10.406844+05:30	1	\N	\N	f	f
2123	COST_CENTER	Cost Center	Hishii Industries	10099	2022-09-20 14:09:10.4069+05:30	2022-09-20 14:09:10.406927+05:30	1	\N	\N	f	f
2124	COST_CENTER	Cost Center	Hollard Group	10100	2022-09-20 14:09:10.413482+05:30	2022-09-20 14:09:10.413523+05:30	1	\N	\N	f	f
2125	COST_CENTER	Cost Center	Illovo Sugar	10101	2022-09-20 14:09:10.41359+05:30	2022-09-20 14:09:10.413619+05:30	1	\N	\N	f	f
2126	COST_CENTER	Cost Center	Impala Platinum	10102	2022-09-20 14:09:10.413678+05:30	2022-09-20 14:09:10.413706+05:30	1	\N	\N	f	f
2127	COST_CENTER	Cost Center	InGen	10103	2022-09-20 14:09:10.413764+05:30	2022-09-20 14:09:10.413792+05:30	1	\N	\N	f	f
2128	COST_CENTER	Cost Center	Innova Solutions	10104	2022-09-20 14:09:10.41385+05:30	2022-09-20 14:09:10.413877+05:30	1	\N	\N	f	f
2129	COST_CENTER	Cost Center	Innovation Arch	10105	2022-09-20 14:09:10.413934+05:30	2022-09-20 14:09:10.413961+05:30	1	\N	\N	f	f
2130	COST_CENTER	Cost Center	Insurance Megacorp	10106	2022-09-20 14:09:10.414018+05:30	2022-09-20 14:09:10.414045+05:30	1	\N	\N	f	f
2131	COST_CENTER	Cost Center	Intelligent Audit	10107	2022-09-20 14:09:10.414102+05:30	2022-09-20 14:09:10.414129+05:30	1	\N	\N	f	f
2132	COST_CENTER	Cost Center	Interplanetary Expeditions	10108	2022-09-20 14:09:10.414186+05:30	2022-09-20 14:09:10.414213+05:30	1	\N	\N	f	f
2133	COST_CENTER	Cost Center	Intrepid Minerals Corporation	10109	2022-09-20 14:09:10.41427+05:30	2022-09-20 14:09:10.414297+05:30	1	\N	\N	f	f
2134	COST_CENTER	Cost Center	Investec	10110	2022-09-20 14:09:10.414353+05:30	2022-09-20 14:09:10.41438+05:30	1	\N	\N	f	f
2135	COST_CENTER	Cost Center	IPS	10111	2022-09-20 14:09:10.414568+05:30	2022-09-20 14:09:10.414607+05:30	1	\N	\N	f	f
2136	COST_CENTER	Cost Center	Itex	10112	2022-09-20 14:09:10.414663+05:30	2022-09-20 14:09:10.41469+05:30	1	\N	\N	f	f
2138	COST_CENTER	Cost Center	Izon	10114	2022-09-20 14:09:10.414829+05:30	2022-09-20 14:09:10.414856+05:30	1	\N	\N	f	f
2139	COST_CENTER	Cost Center	Jabberstorm	10115	2022-09-20 14:09:10.414912+05:30	2022-09-20 14:09:10.414939+05:30	1	\N	\N	f	f
2140	COST_CENTER	Cost Center	Jabbertype	10116	2022-09-20 14:09:10.414995+05:30	2022-09-20 14:09:10.415022+05:30	1	\N	\N	f	f
2141	COST_CENTER	Cost Center	James Mintz Group, Inc.	10117	2022-09-20 14:09:10.415078+05:30	2022-09-20 14:09:10.415105+05:30	1	\N	\N	f	f
2142	COST_CENTER	Cost Center	Jaxnation	10118	2022-09-20 14:09:10.415161+05:30	2022-09-20 14:09:10.415188+05:30	1	\N	\N	f	f
2143	COST_CENTER	Cost Center	Jazzy	10119	2022-09-20 14:09:10.415244+05:30	2022-09-20 14:09:10.415271+05:30	1	\N	\N	f	f
2144	COST_CENTER	Cost Center	Junk Mail Digital Media	10120	2022-09-20 14:09:10.415326+05:30	2022-09-20 14:09:10.415458+05:30	1	\N	\N	f	f
2145	COST_CENTER	Cost Center	Kansas City Power and Light Co.	10121	2022-09-20 14:09:10.415515+05:30	2022-09-20 14:09:10.415543+05:30	1	\N	\N	f	f
2146	COST_CENTER	Cost Center	Kazio	10122	2022-09-20 14:09:10.415599+05:30	2022-09-20 14:09:10.415627+05:30	1	\N	\N	f	f
2147	COST_CENTER	Cost Center	KENTECH Consulting	10123	2022-09-20 14:09:10.415683+05:30	2022-09-20 14:09:10.41571+05:30	1	\N	\N	f	f
2148	COST_CENTER	Cost Center	Khumalo	10124	2022-09-20 14:09:10.415765+05:30	2022-09-20 14:09:10.415792+05:30	1	\N	\N	f	f
2149	COST_CENTER	Cost Center	Klondike Gold Corporation	10125	2022-09-20 14:09:10.415849+05:30	2022-09-20 14:09:10.415876+05:30	1	\N	\N	f	f
2150	COST_CENTER	Cost Center	Kumba Iron Ore	10126	2022-09-20 14:09:10.415942+05:30	2022-09-20 14:09:10.415969+05:30	1	\N	\N	f	f
2151	COST_CENTER	Cost Center	Kwik-E-Mart	10127	2022-09-20 14:09:10.416026+05:30	2022-09-20 14:09:10.416053+05:30	1	\N	\N	f	f
2152	COST_CENTER	Cost Center	Kwilith	10128	2022-09-20 14:09:10.416109+05:30	2022-09-20 14:09:10.416136+05:30	1	\N	\N	f	f
2153	COST_CENTER	Cost Center	Leexo	10129	2022-09-20 14:09:10.416193+05:30	2022-09-20 14:09:10.416232+05:30	1	\N	\N	f	f
2154	COST_CENTER	Cost Center	Leo A. Daly Company	10130	2022-09-20 14:09:10.416512+05:30	2022-09-20 14:09:10.416658+05:30	1	\N	\N	f	f
2155	COST_CENTER	Cost Center	LexCorp	10131	2022-09-20 14:09:10.416718+05:30	2022-09-20 14:09:10.416745+05:30	1	\N	\N	f	f
2156	COST_CENTER	Cost Center	Liandri Mining	10132	2022-09-20 14:09:10.416802+05:30	2022-09-20 14:09:10.41683+05:30	1	\N	\N	f	f
2157	COST_CENTER	Cost Center	LIFE Healthcare Group	10133	2022-09-20 14:09:10.416886+05:30	2022-09-20 14:09:10.416913+05:30	1	\N	\N	f	f
2158	COST_CENTER	Cost Center	Linkbuzz	10134	2022-09-20 14:09:10.416969+05:30	2022-09-20 14:09:10.416997+05:30	1	\N	\N	f	f
2159	COST_CENTER	Cost Center	Livefish	10135	2022-09-20 14:09:10.417053+05:30	2022-09-20 14:09:10.417081+05:30	1	\N	\N	f	f
2160	COST_CENTER	Cost Center	Livetube	10136	2022-09-20 14:09:10.417137+05:30	2022-09-20 14:09:10.417165+05:30	1	\N	\N	f	f
2161	COST_CENTER	Cost Center	Live With Intention	10137	2022-09-20 14:09:10.417221+05:30	2022-09-20 14:09:10.417248+05:30	1	\N	\N	f	f
2162	COST_CENTER	Cost Center	Mathews and Associates Architects	10138	2022-09-20 14:09:10.417305+05:30	2022-09-20 14:09:10.417347+05:30	1	\N	\N	f	f
2163	COST_CENTER	Cost Center	Matrox Electronic Systems Ltd.	10139	2022-09-20 14:09:10.417522+05:30	2022-09-20 14:09:10.41755+05:30	1	\N	\N	f	f
2164	COST_CENTER	Cost Center	Matsumura Fishworks	10140	2022-09-20 14:09:10.417607+05:30	2022-09-20 14:09:10.417634+05:30	1	\N	\N	f	f
2165	COST_CENTER	Cost Center	McCandless Communications	10141	2022-09-20 14:09:10.41769+05:30	2022-09-20 14:09:10.417718+05:30	1	\N	\N	f	f
2166	COST_CENTER	Cost Center	Med dot	10142	2022-09-20 14:09:10.417774+05:30	2022-09-20 14:09:10.417801+05:30	1	\N	\N	f	f
2167	COST_CENTER	Cost Center	Medical Mechanica	10143	2022-09-20 14:09:10.417858+05:30	2022-09-20 14:09:10.417885+05:30	1	\N	\N	f	f
2168	COST_CENTER	Cost Center	Medical Research Technologies	10144	2022-09-20 14:09:10.417941+05:30	2022-09-20 14:09:10.417968+05:30	1	\N	\N	f	f
2169	COST_CENTER	Cost Center	Mediclinic International	10145	2022-09-20 14:09:10.418024+05:30	2022-09-20 14:09:10.418052+05:30	1	\N	\N	f	f
2170	COST_CENTER	Cost Center	Mega Lo Mart	10146	2022-09-20 14:09:10.418108+05:30	2022-09-20 14:09:10.418135+05:30	1	\N	\N	f	f
2171	COST_CENTER	Cost Center	Mensa, Ltd.	10147	2022-09-20 14:09:10.418192+05:30	2022-09-20 14:09:10.41822+05:30	1	\N	\N	f	f
2172	COST_CENTER	Cost Center	Metacortex	10148	2022-09-20 14:09:10.418276+05:30	2022-09-20 14:09:10.418304+05:30	1	\N	\N	f	f
2173	COST_CENTER	Cost Center	Miboo	10149	2022-09-20 14:09:10.418372+05:30	2022-09-20 14:09:10.418486+05:30	1	\N	\N	f	f
2174	COST_CENTER	Cost Center	Mishima Zaibatsu	10150	2022-09-20 14:09:10.426011+05:30	2022-09-20 14:09:10.426058+05:30	1	\N	\N	f	f
2175	COST_CENTER	Cost Center	MK Manufacturing	10151	2022-09-20 14:09:10.426144+05:30	2022-09-20 14:09:10.426177+05:30	1	\N	\N	f	f
2176	COST_CENTER	Cost Center	M-Net	10152	2022-09-20 14:09:10.426249+05:30	2022-09-20 14:09:10.426288+05:30	1	\N	\N	f	f
2177	COST_CENTER	Cost Center	Monsters, Inc.	10153	2022-09-20 14:09:10.426527+05:30	2022-09-20 14:09:10.426561+05:30	1	\N	\N	f	f
2178	COST_CENTER	Cost Center	Mr. Price Group Ltd.	10154	2022-09-20 14:09:10.426631+05:30	2022-09-20 14:09:10.426661+05:30	1	\N	\N	f	f
2179	COST_CENTER	Cost Center	MTN Group	10155	2022-09-20 14:09:10.426732+05:30	2022-09-20 14:09:10.426761+05:30	1	\N	\N	f	f
2180	COST_CENTER	Cost Center	MultiChoice	10156	2022-09-20 14:09:10.426952+05:30	2022-09-20 14:09:10.427028+05:30	1	\N	\N	f	f
2181	COST_CENTER	Cost Center	MWEB	10157	2022-09-20 14:09:10.427297+05:30	2022-09-20 14:09:10.427543+05:30	1	\N	\N	f	f
2182	COST_CENTER	Cost Center	Mybuzz	10158	2022-09-20 14:09:10.427918+05:30	2022-09-20 14:09:10.427967+05:30	1	\N	\N	f	f
2183	COST_CENTER	Cost Center	Myworks	10159	2022-09-20 14:09:10.428056+05:30	2022-09-20 14:09:10.428118+05:30	1	\N	\N	f	f
2184	COST_CENTER	Cost Center	Nakatomi Corporation	10160	2022-09-20 14:09:10.4294+05:30	2022-09-20 14:09:10.429452+05:30	1	\N	\N	f	f
2185	COST_CENTER	Cost Center	Nanocell	10161	2022-09-20 14:09:10.429525+05:30	2022-09-20 14:09:10.429554+05:30	1	\N	\N	f	f
2186	COST_CENTER	Cost Center	Naples Pediatrics	10162	2022-09-20 14:09:10.429614+05:30	2022-09-20 14:09:10.429642+05:30	1	\N	\N	f	f
2187	COST_CENTER	Cost Center	Naspers	10163	2022-09-20 14:09:10.429701+05:30	2022-09-20 14:09:10.429728+05:30	1	\N	\N	f	f
2188	COST_CENTER	Cost Center	National Clean Energy	10164	2022-09-20 14:09:10.429785+05:30	2022-09-20 14:09:10.429812+05:30	1	\N	\N	f	f
2189	COST_CENTER	Cost Center	Nedbank	10165	2022-09-20 14:09:10.42987+05:30	2022-09-20 14:09:10.429897+05:30	1	\N	\N	f	f
2190	COST_CENTER	Cost Center	Neotel	10166	2022-09-20 14:09:10.429954+05:30	2022-09-20 14:09:10.429981+05:30	1	\N	\N	f	f
2191	COST_CENTER	Cost Center	Neoveo	10167	2022-09-20 14:09:10.430038+05:30	2022-09-20 14:09:10.430065+05:30	1	\N	\N	f	f
2192	COST_CENTER	Cost Center	N.E.R.D.	10168	2022-09-20 14:09:10.430122+05:30	2022-09-20 14:09:10.43015+05:30	1	\N	\N	f	f
2193	COST_CENTER	Cost Center	Netcare	10169	2022-09-20 14:09:10.430207+05:30	2022-09-20 14:09:10.430234+05:30	1	\N	\N	f	f
2194	COST_CENTER	Cost Center	Network23	10170	2022-09-20 14:09:10.43029+05:30	2022-09-20 14:09:10.430318+05:30	1	\N	\N	f	f
2195	COST_CENTER	Cost Center	new customer	10171	2022-09-20 14:09:10.430374+05:30	2022-09-20 14:09:10.430416+05:30	1	\N	\N	f	f
2196	COST_CENTER	Cost Center	News Day	10172	2022-09-20 14:09:10.430615+05:30	2022-09-20 14:09:10.430653+05:30	1	\N	\N	f	f
2197	COST_CENTER	Cost Center	Nirvana	10173	2022-09-20 14:09:10.430758+05:30	2022-09-20 14:09:10.430788+05:30	1	\N	\N	f	f
2198	COST_CENTER	Cost Center	Nordyne Defense	10174	2022-09-20 14:09:10.430849+05:30	2022-09-20 14:09:10.430888+05:30	1	\N	\N	f	f
2199	COST_CENTER	Cost Center	NorthAm Robotics	10175	2022-09-20 14:09:10.430946+05:30	2022-09-20 14:09:10.430973+05:30	1	\N	\N	f	f
2200	COST_CENTER	Cost Center	North Central Positronics	10176	2022-09-20 14:09:10.43103+05:30	2022-09-20 14:09:10.431057+05:30	1	\N	\N	f	f
2201	COST_CENTER	Cost Center	Novamed	10177	2022-09-20 14:09:10.431114+05:30	2022-09-20 14:09:10.431141+05:30	1	\N	\N	f	f
2202	COST_CENTER	Cost Center	Npath	10178	2022-09-20 14:09:10.431197+05:30	2022-09-20 14:09:10.431225+05:30	1	\N	\N	f	f
2203	COST_CENTER	Cost Center	Oakland County Community Mental Health	10179	2022-09-20 14:09:10.431281+05:30	2022-09-20 14:09:10.431308+05:30	1	\N	\N	f	f
2204	COST_CENTER	Cost Center	Old Mutual	10180	2022-09-20 14:09:10.431489+05:30	2022-09-20 14:09:10.43153+05:30	1	\N	\N	f	f
2205	COST_CENTER	Cost Center	Olin Corporation	10181	2022-09-20 14:09:10.431588+05:30	2022-09-20 14:09:10.431615+05:30	1	\N	\N	f	f
2206	COST_CENTER	Cost Center	Omni Consumer Products	10182	2022-09-20 14:09:10.431672+05:30	2022-09-20 14:09:10.431699+05:30	1	\N	\N	f	f
2207	COST_CENTER	Cost Center	Oncolytics Biotech Inc.	10183	2022-09-20 14:09:10.431755+05:30	2022-09-20 14:09:10.431783+05:30	1	\N	\N	f	f
2208	COST_CENTER	Cost Center	Optican	10184	2022-09-20 14:09:10.431838+05:30	2022-09-20 14:09:10.431866+05:30	1	\N	\N	f	f
2209	COST_CENTER	Cost Center	Orchard Group	10185	2022-09-20 14:09:10.431922+05:30	2022-09-20 14:09:10.431949+05:30	1	\N	\N	f	f
2210	COST_CENTER	Cost Center	OsCorp	10186	2022-09-20 14:09:10.432006+05:30	2022-09-20 14:09:10.432033+05:30	1	\N	\N	f	f
2211	COST_CENTER	Cost Center	Ovi	10187	2022-09-20 14:09:10.432089+05:30	2022-09-20 14:09:10.432116+05:30	1	\N	\N	f	f
2212	COST_CENTER	Cost Center	Pacificare Health Systems Az	10188	2022-09-20 14:09:10.432173+05:30	2022-09-20 14:09:10.4322+05:30	1	\N	\N	f	f
2213	COST_CENTER	Cost Center	Pacificorp	10189	2022-09-20 14:09:10.432255+05:30	2022-09-20 14:09:10.432282+05:30	1	\N	\N	f	f
2214	COST_CENTER	Cost Center	PA Neurosurgery and Neuroscience	10190	2022-09-20 14:09:10.432338+05:30	2022-09-20 14:09:10.432511+05:30	1	\N	\N	f	f
2215	COST_CENTER	Cost Center	Paper Street Soap Co.	10191	2022-09-20 14:09:10.432599+05:30	2022-09-20 14:09:10.432627+05:30	1	\N	\N	f	f
2216	COST_CENTER	Cost Center	Parrish Communications	10192	2022-09-20 14:09:10.432683+05:30	2022-09-20 14:09:10.432711+05:30	1	\N	\N	f	f
2217	COST_CENTER	Cost Center	Pediatric Subspecialty Faculty	10193	2022-09-20 14:09:10.432767+05:30	2022-09-20 14:09:10.432794+05:30	1	\N	\N	f	f
2218	COST_CENTER	Cost Center	Photofeed	10194	2022-09-20 14:09:10.43285+05:30	2022-09-20 14:09:10.432877+05:30	1	\N	\N	f	f
2219	COST_CENTER	Cost Center	Photojam	10195	2022-09-20 14:09:10.432933+05:30	2022-09-20 14:09:10.43296+05:30	1	\N	\N	f	f
2220	COST_CENTER	Cost Center	Pick 'n Pay	10196	2022-09-20 14:09:10.433016+05:30	2022-09-20 14:09:10.433044+05:30	1	\N	\N	f	f
2221	COST_CENTER	Cost Center	Piggly Wiggly Carolina Co.	10197	2022-09-20 14:09:10.4331+05:30	2022-09-20 14:09:10.433127+05:30	1	\N	\N	f	f
2222	COST_CENTER	Cost Center	Pioneer Foods	10198	2022-09-20 14:09:10.433183+05:30	2022-09-20 14:09:10.43321+05:30	1	\N	\N	f	f
2223	COST_CENTER	Cost Center	Pixonyx	10199	2022-09-20 14:09:10.433267+05:30	2022-09-20 14:09:10.433294+05:30	1	\N	\N	f	f
2224	COST_CENTER	Cost Center	Porter Technologies	10200	2022-09-20 14:09:10.438749+05:30	2022-09-20 14:09:10.438792+05:30	1	\N	\N	f	f
2225	COST_CENTER	Cost Center	33Across	9806	2022-09-20 14:09:10.438859+05:30	2022-09-20 14:09:10.438888+05:30	1	\N	\N	f	f
2226	COST_CENTER	Cost Center	3Way International Logistics	9807	2022-09-20 14:09:10.438947+05:30	2022-09-20 14:09:10.438975+05:30	1	\N	\N	f	f
2227	COST_CENTER	Cost Center	ABB Grain	9808	2022-09-20 14:09:10.439032+05:30	2022-09-20 14:09:10.43906+05:30	1	\N	\N	f	f
2228	COST_CENTER	Cost Center	ABC Learning	9809	2022-09-20 14:09:10.439118+05:30	2022-09-20 14:09:10.439145+05:30	1	\N	\N	f	f
2229	COST_CENTER	Cost Center	ABSA Group	9810	2022-09-20 14:09:10.439203+05:30	2022-09-20 14:09:10.439231+05:30	1	\N	\N	f	f
2230	COST_CENTER	Cost Center	AB SQUARE	9811	2022-09-20 14:09:10.439289+05:30	2022-09-20 14:09:10.439317+05:30	1	\N	\N	f	f
2231	COST_CENTER	Cost Center	Abstergo Industries	9812	2022-09-20 14:09:10.439374+05:30	2022-09-20 14:09:10.439402+05:30	1	\N	\N	f	f
2232	COST_CENTER	Cost Center	Ace Tomato	9813	2022-09-20 14:09:10.439613+05:30	2022-09-20 14:09:10.439641+05:30	1	\N	\N	f	f
2233	COST_CENTER	Cost Center	Ache Records	9814	2022-09-20 14:09:10.439699+05:30	2022-09-20 14:09:10.439726+05:30	1	\N	\N	f	f
2234	COST_CENTER	Cost Center	Acme	9815	2022-09-20 14:09:10.439783+05:30	2022-09-20 14:09:10.43981+05:30	1	\N	\N	f	f
2235	COST_CENTER	Cost Center	ACSA	9816	2022-09-20 14:09:10.439867+05:30	2022-09-20 14:09:10.439894+05:30	1	\N	\N	f	f
2236	COST_CENTER	Cost Center	Adam Internet	9817	2022-09-20 14:09:10.43995+05:30	2022-09-20 14:09:10.439978+05:30	1	\N	\N	f	f
2237	COST_CENTER	Cost Center	Adcock Ingram	9818	2022-09-20 14:09:10.440034+05:30	2022-09-20 14:09:10.440061+05:30	1	\N	\N	f	f
2238	COST_CENTER	Cost Center	Admire Arts	9819	2022-09-20 14:09:10.440118+05:30	2022-09-20 14:09:10.440145+05:30	1	\N	\N	f	f
2239	COST_CENTER	Cost Center	Advanced Cyclotron Systems	9820	2022-09-20 14:09:10.440202+05:30	2022-09-20 14:09:10.440229+05:30	1	\N	\N	f	f
2240	COST_CENTER	Cost Center	Aerosonde Ltd	9821	2022-09-20 14:09:10.440285+05:30	2022-09-20 14:09:10.440312+05:30	1	\N	\N	f	f
2241	COST_CENTER	Cost Center	Afrihost	9822	2022-09-20 14:09:10.44064+05:30	2022-09-20 14:09:10.440663+05:30	1	\N	\N	f	f
2242	COST_CENTER	Cost Center	AG Insurance	9823	2022-09-20 14:09:10.440824+05:30	2022-09-20 14:09:10.440852+05:30	1	\N	\N	f	f
2243	COST_CENTER	Cost Center	Aimbu	9824	2022-09-20 14:09:10.440909+05:30	2022-09-20 14:09:10.440936+05:30	1	\N	\N	f	f
2244	COST_CENTER	Cost Center	Ajax	9825	2022-09-20 14:09:10.440993+05:30	2022-09-20 14:09:10.44102+05:30	1	\N	\N	f	f
2245	COST_CENTER	Cost Center	Ajira Airways	9826	2022-09-20 14:09:10.441076+05:30	2022-09-20 14:09:10.441103+05:30	1	\N	\N	f	f
2246	COST_CENTER	Cost Center	Aldo Group	9827	2022-09-20 14:09:10.441159+05:30	2022-09-20 14:09:10.441186+05:30	1	\N	\N	f	f
2247	COST_CENTER	Cost Center	Algonquin Power and Utilities	9828	2022-09-20 14:09:10.441242+05:30	2022-09-20 14:09:10.441269+05:30	1	\N	\N	f	f
2248	COST_CENTER	Cost Center	Alinta Gas	9829	2022-09-20 14:09:10.441457+05:30	2022-09-20 14:09:10.441496+05:30	1	\N	\N	f	f
2249	COST_CENTER	Cost Center	Allied British Plastics	9830	2022-09-20 14:09:10.441552+05:30	2022-09-20 14:09:10.44158+05:30	1	\N	\N	f	f
2250	COST_CENTER	Cost Center	Allphones	9831	2022-09-20 14:09:10.441637+05:30	2022-09-20 14:09:10.441664+05:30	1	\N	\N	f	f
2251	COST_CENTER	Cost Center	Alumina	9832	2022-09-20 14:09:10.44172+05:30	2022-09-20 14:09:10.441747+05:30	1	\N	\N	f	f
2252	COST_CENTER	Cost Center	Amcor	9833	2022-09-20 14:09:10.441804+05:30	2022-09-20 14:09:10.441831+05:30	1	\N	\N	f	f
2253	COST_CENTER	Cost Center	ANCA	9834	2022-09-20 14:09:10.441887+05:30	2022-09-20 14:09:10.441914+05:30	1	\N	\N	f	f
2254	COST_CENTER	Cost Center	Anglo American	9835	2022-09-20 14:09:10.441988+05:30	2022-09-20 14:09:10.442017+05:30	1	\N	\N	f	f
2255	COST_CENTER	Cost Center	Anglo American Platinum	9836	2022-09-20 14:09:10.442081+05:30	2022-09-20 14:09:10.442111+05:30	1	\N	\N	f	f
2256	COST_CENTER	Cost Center	Angoss	9837	2022-09-20 14:09:10.442176+05:30	2022-09-20 14:09:10.442206+05:30	1	\N	\N	f	f
2257	COST_CENTER	Cost Center	Angus and Robertson	9838	2022-09-20 14:09:10.442267+05:30	2022-09-20 14:09:10.442296+05:30	1	\N	\N	f	f
2258	COST_CENTER	Cost Center	Ansell	9839	2022-09-20 14:09:10.442482+05:30	2022-09-20 14:09:10.44251+05:30	1	\N	\N	f	f
2259	COST_CENTER	Cost Center	Aperture Science	9840	2022-09-20 14:09:10.442567+05:30	2022-09-20 14:09:10.442594+05:30	1	\N	\N	f	f
2260	COST_CENTER	Cost Center	Appliances Online	9841	2022-09-20 14:09:10.442651+05:30	2022-09-20 14:09:10.442678+05:30	1	\N	\N	f	f
2261	COST_CENTER	Cost Center	Applied Biomics	9842	2022-09-20 14:09:10.442735+05:30	2022-09-20 14:09:10.442762+05:30	1	\N	\N	f	f
2262	COST_CENTER	Cost Center	Appnovation	9843	2022-09-20 14:09:10.442817+05:30	2022-09-20 14:09:10.442844+05:30	1	\N	\N	f	f
2263	COST_CENTER	Cost Center	Arbitration Association	9844	2022-09-20 14:09:10.442901+05:30	2022-09-20 14:09:10.442928+05:30	1	\N	\N	f	f
2264	COST_CENTER	Cost Center	ARCAM Corporation	9845	2022-09-20 14:09:10.442984+05:30	2022-09-20 14:09:10.443011+05:30	1	\N	\N	f	f
105	CATEGORY	Category	buh	184631	2022-09-20 14:09:03.37368+05:30	2022-09-20 14:09:03.373712+05:30	1	t	\N	f	f
2265	COST_CENTER	Cost Center	Aristocrat Leisure	9846	2022-09-20 14:09:10.443068+05:30	2022-09-20 14:09:10.443095+05:30	1	\N	\N	f	f
2266	COST_CENTER	Cost Center	Arkansas Blue Cross and Blue Shield	9847	2022-09-20 14:09:10.443152+05:30	2022-09-20 14:09:10.443179+05:30	1	\N	\N	f	f
2267	COST_CENTER	Cost Center	Army and Navy Stores	9848	2022-09-20 14:09:10.443235+05:30	2022-09-20 14:09:10.443263+05:30	1	\N	\N	f	f
2268	COST_CENTER	Cost Center	Arnott's Biscuits	9849	2022-09-20 14:09:10.443319+05:30	2022-09-20 14:09:10.443346+05:30	1	\N	\N	f	f
2269	COST_CENTER	Cost Center	Arrow Research Corporation	9850	2022-09-20 14:09:10.443542+05:30	2022-09-20 14:09:10.443571+05:30	1	\N	\N	f	f
2270	COST_CENTER	Cost Center	Aspen Pharmacare	9851	2022-09-20 14:09:10.443627+05:30	2022-09-20 14:09:10.443655+05:30	1	\N	\N	f	f
2271	COST_CENTER	Cost Center	Astromech	9852	2022-09-20 14:09:10.443712+05:30	2022-09-20 14:09:10.443739+05:30	1	\N	\N	f	f
2272	COST_CENTER	Cost Center	ATB Financial	9853	2022-09-20 14:09:10.443795+05:30	2022-09-20 14:09:10.443823+05:30	1	\N	\N	f	f
2273	COST_CENTER	Cost Center	Atlanta Integrative Medicine	9854	2022-09-20 14:09:10.443879+05:30	2022-09-20 14:09:10.443906+05:30	1	\N	\N	f	f
2274	COST_CENTER	Cost Center	Atlassian	9855	2022-09-20 14:09:10.450916+05:30	2022-09-20 14:09:10.450958+05:30	1	\N	\N	f	f
2275	COST_CENTER	Cost Center	Augusta Medical Associates	9856	2022-09-20 14:09:10.451027+05:30	2022-09-20 14:09:10.451056+05:30	1	\N	\N	f	f
2276	COST_CENTER	Cost Center	Aussie Broadband	9857	2022-09-20 14:09:10.451116+05:30	2022-09-20 14:09:10.451144+05:30	1	\N	\N	f	f
2277	COST_CENTER	Cost Center	Austal Ships	9858	2022-09-20 14:09:10.451202+05:30	2022-09-20 14:09:10.45123+05:30	1	\N	\N	f	f
2278	COST_CENTER	Cost Center	Austereo	9859	2022-09-20 14:09:10.451286+05:30	2022-09-20 14:09:10.451313+05:30	1	\N	\N	f	f
2279	COST_CENTER	Cost Center	Australia and New Zealand Banking Group (ANZ)	9860	2022-09-20 14:09:10.451497+05:30	2022-09-20 14:09:10.45153+05:30	1	\N	\N	f	f
2280	COST_CENTER	Cost Center	Australian Agricultural Company	9861	2022-09-20 14:09:10.451601+05:30	2022-09-20 14:09:10.451629+05:30	1	\N	\N	f	f
2281	COST_CENTER	Cost Center	Australian airExpress	9862	2022-09-20 14:09:10.451686+05:30	2022-09-20 14:09:10.451714+05:30	1	\N	\N	f	f
2282	COST_CENTER	Cost Center	Australian Broadcasting Corporation	9863	2022-09-20 14:09:10.451771+05:30	2022-09-20 14:09:10.451798+05:30	1	\N	\N	f	f
2283	COST_CENTER	Cost Center	Australian Defence Industries	9864	2022-09-20 14:09:10.451855+05:30	2022-09-20 14:09:10.451882+05:30	1	\N	\N	f	f
2284	COST_CENTER	Cost Center	Australian Gas Light Company	9865	2022-09-20 14:09:10.451938+05:30	2022-09-20 14:09:10.451965+05:30	1	\N	\N	f	f
2285	COST_CENTER	Cost Center	Australian Motor Industries (AMI)	9866	2022-09-20 14:09:10.452021+05:30	2022-09-20 14:09:10.452048+05:30	1	\N	\N	f	f
2286	COST_CENTER	Cost Center	Australian Railroad Group	9867	2022-09-20 14:09:10.452105+05:30	2022-09-20 14:09:10.452132+05:30	1	\N	\N	f	f
2287	COST_CENTER	Cost Center	Australian Securities Exchange	9868	2022-09-20 14:09:10.452188+05:30	2022-09-20 14:09:10.452215+05:30	1	\N	\N	f	f
2288	COST_CENTER	Cost Center	Ausway	9869	2022-09-20 14:09:10.452272+05:30	2022-09-20 14:09:10.452299+05:30	1	\N	\N	f	f
2289	COST_CENTER	Cost Center	Automobile Association of South Africa	9870	2022-09-20 14:09:10.452366+05:30	2022-09-20 14:09:10.452487+05:30	1	\N	\N	f	f
2290	COST_CENTER	Cost Center	Avaveo	9871	2022-09-20 14:09:10.452559+05:30	2022-09-20 14:09:10.452587+05:30	1	\N	\N	f	f
2291	COST_CENTER	Cost Center	Avu	9872	2022-09-20 14:09:10.452644+05:30	2022-09-20 14:09:10.452671+05:30	1	\N	\N	f	f
2292	COST_CENTER	Cost Center	AWB Limited	9873	2022-09-20 14:09:10.452728+05:30	2022-09-20 14:09:10.452756+05:30	1	\N	\N	f	f
2293	COST_CENTER	Cost Center	BAE Systems Australia	9874	2022-09-20 14:09:10.452812+05:30	2022-09-20 14:09:10.45284+05:30	1	\N	\N	f	f
2294	COST_CENTER	Cost Center	Bakers Delight	9875	2022-09-20 14:09:10.452897+05:30	2022-09-20 14:09:10.452924+05:30	1	\N	\N	f	f
2295	COST_CENTER	Cost Center	Banff Lodging Co	9876	2022-09-20 14:09:10.45298+05:30	2022-09-20 14:09:10.453008+05:30	1	\N	\N	f	f
2296	COST_CENTER	Cost Center	Bard Ventures	9877	2022-09-20 14:09:10.453064+05:30	2022-09-20 14:09:10.453092+05:30	1	\N	\N	f	f
2297	COST_CENTER	Cost Center	Bayer Corporation	9878	2022-09-20 14:09:10.453148+05:30	2022-09-20 14:09:10.453175+05:30	1	\N	\N	f	f
2298	COST_CENTER	Cost Center	BC Research	9879	2022-09-20 14:09:10.453232+05:30	2022-09-20 14:09:10.453259+05:30	1	\N	\N	f	f
2299	COST_CENTER	Cost Center	Beaurepaires	9880	2022-09-20 14:09:10.453315+05:30	2022-09-20 14:09:10.453343+05:30	1	\N	\N	f	f
2300	COST_CENTER	Cost Center	Becker Entertainment	9881	2022-09-20 14:09:10.45353+05:30	2022-09-20 14:09:10.453555+05:30	1	\N	\N	f	f
2301	COST_CENTER	Cost Center	Been Verified	9882	2022-09-20 14:09:10.453607+05:30	2022-09-20 14:09:10.453646+05:30	1	\N	\N	f	f
2302	COST_CENTER	Cost Center	Bella Technologies	9883	2022-09-20 14:09:10.453703+05:30	2022-09-20 14:09:10.453731+05:30	1	\N	\N	f	f
2303	COST_CENTER	Cost Center	Bell Canada	9884	2022-09-20 14:09:10.453788+05:30	2022-09-20 14:09:10.453815+05:30	1	\N	\N	f	f
2304	COST_CENTER	Cost Center	Benthic Petroleum	9885	2022-09-20 14:09:10.453872+05:30	2022-09-20 14:09:10.453899+05:30	1	\N	\N	f	f
2305	COST_CENTER	Cost Center	Biffco	9886	2022-09-20 14:09:10.453956+05:30	2022-09-20 14:09:10.453983+05:30	1	\N	\N	f	f
2306	COST_CENTER	Cost Center	Big Blue Bubble	9887	2022-09-20 14:09:10.45404+05:30	2022-09-20 14:09:10.454067+05:30	1	\N	\N	f	f
2307	COST_CENTER	Cost Center	Billabong	9888	2022-09-20 14:09:10.454137+05:30	2022-09-20 14:09:10.454319+05:30	1	\N	\N	f	f
2308	COST_CENTER	Cost Center	Binford	9889	2022-09-20 14:09:10.45452+05:30	2022-09-20 14:09:10.454549+05:30	1	\N	\N	f	f
2309	COST_CENTER	Cost Center	Bing Lee	9890	2022-09-20 14:09:10.454746+05:30	2022-09-20 14:09:10.454775+05:30	1	\N	\N	f	f
2310	COST_CENTER	Cost Center	BioClear	9891	2022-09-20 14:09:10.455026+05:30	2022-09-20 14:09:10.45514+05:30	1	\N	\N	f	f
2311	COST_CENTER	Cost Center	BioMed Labs	9892	2022-09-20 14:09:10.455214+05:30	2022-09-20 14:09:10.455342+05:30	1	\N	\N	f	f
2312	COST_CENTER	Cost Center	Biovail	9893	2022-09-20 14:09:10.455449+05:30	2022-09-20 14:09:10.455477+05:30	1	\N	\N	f	f
2313	COST_CENTER	Cost Center	BlackBerry Limited	9894	2022-09-20 14:09:10.455534+05:30	2022-09-20 14:09:10.455561+05:30	1	\N	\N	f	f
2314	COST_CENTER	Cost Center	Black Hen Music	9895	2022-09-20 14:09:10.455631+05:30	2022-09-20 14:09:10.45566+05:30	1	\N	\N	f	f
2315	COST_CENTER	Cost Center	Bledsoe Cathcart Diestel and Pedersen LLP	9896	2022-09-20 14:09:10.455719+05:30	2022-09-20 14:09:10.455741+05:30	1	\N	\N	f	f
2316	COST_CENTER	Cost Center	Blenz Coffee	9897	2022-09-20 14:09:10.456019+05:30	2022-09-20 14:09:10.45605+05:30	1	\N	\N	f	f
2317	COST_CENTER	Cost Center	BlogXS	9898	2022-09-20 14:09:10.456112+05:30	2022-09-20 14:09:10.456142+05:30	1	\N	\N	f	f
2318	COST_CENTER	Cost Center	Bluejam	9899	2022-09-20 14:09:10.456196+05:30	2022-09-20 14:09:10.456215+05:30	1	\N	\N	f	f
2319	COST_CENTER	Cost Center	BlueScope	9900	2022-09-20 14:09:10.456399+05:30	2022-09-20 14:09:10.456431+05:30	1	\N	\N	f	f
2320	COST_CENTER	Cost Center	Blue Sun Corporation	9901	2022-09-20 14:09:10.456493+05:30	2022-09-20 14:09:10.456518+05:30	1	\N	\N	f	f
2321	COST_CENTER	Cost Center	Blundstone Footwear	9902	2022-09-20 14:09:10.456565+05:30	2022-09-20 14:09:10.456576+05:30	1	\N	\N	f	f
2322	COST_CENTER	Cost Center	Bluth Company	9903	2022-09-20 14:09:10.456626+05:30	2022-09-20 14:09:10.456655+05:30	1	\N	\N	f	f
2323	COST_CENTER	Cost Center	Boeing Canada	9904	2022-09-20 14:09:10.456715+05:30	2022-09-20 14:09:10.456764+05:30	1	\N	\N	f	f
2324	COST_CENTER	Cost Center	Boost Juice Bars	9905	2022-09-20 14:09:10.462992+05:30	2022-09-20 14:09:10.463039+05:30	1	\N	\N	f	f
2325	COST_CENTER	Cost Center	Boral	9906	2022-09-20 14:09:10.463125+05:30	2022-09-20 14:09:10.463154+05:30	1	\N	\N	f	f
2326	COST_CENTER	Cost Center	Boston Pizza	9907	2022-09-20 14:09:10.463245+05:30	2022-09-20 14:09:10.463423+05:30	1	\N	\N	f	f
2327	COST_CENTER	Cost Center	Bottle Rocket Apps	9908	2022-09-20 14:09:10.463539+05:30	2022-09-20 14:09:10.463569+05:30	1	\N	\N	f	f
2328	COST_CENTER	Cost Center	Bowring Brothers	9909	2022-09-20 14:09:10.463632+05:30	2022-09-20 14:09:10.463661+05:30	1	\N	\N	f	f
2329	COST_CENTER	Cost Center	Brainlounge	9910	2022-09-20 14:09:10.463722+05:30	2022-09-20 14:09:10.463751+05:30	1	\N	\N	f	f
2330	COST_CENTER	Cost Center	Brant, Agron, Meiselman	9911	2022-09-20 14:09:10.463812+05:30	2022-09-20 14:09:10.463983+05:30	1	\N	\N	f	f
2331	COST_CENTER	Cost Center	BrightSide Technologies	9912	2022-09-20 14:09:10.464152+05:30	2022-09-20 14:09:10.464181+05:30	1	\N	\N	f	f
2332	COST_CENTER	Cost Center	Brown Brothers Milawa Vineyard	9913	2022-09-20 14:09:10.464394+05:30	2022-09-20 14:09:10.464558+05:30	1	\N	\N	f	f
2333	COST_CENTER	Cost Center	Browsebug	9914	2022-09-20 14:09:10.464787+05:30	2022-09-20 14:09:10.464809+05:30	1	\N	\N	f	f
2334	COST_CENTER	Cost Center	Bruce Power	9915	2022-09-20 14:09:10.46501+05:30	2022-09-20 14:09:10.465131+05:30	1	\N	\N	f	f
2335	COST_CENTER	Cost Center	Bubblebox	9916	2022-09-20 14:09:10.465354+05:30	2022-09-20 14:09:10.465381+05:30	1	\N	\N	f	f
2336	COST_CENTER	Cost Center	Bubblemix	9917	2022-09-20 14:09:10.465438+05:30	2022-09-20 14:09:10.465465+05:30	1	\N	\N	f	f
2337	COST_CENTER	Cost Center	BuddyTV	9918	2022-09-20 14:09:10.465522+05:30	2022-09-20 14:09:10.465549+05:30	1	\N	\N	f	f
2338	COST_CENTER	Cost Center	Bulla Dairy Foods	9919	2022-09-20 14:09:10.465606+05:30	2022-09-20 14:09:10.465633+05:30	1	\N	\N	f	f
2339	COST_CENTER	Cost Center	Bullfrog Power	9920	2022-09-20 14:09:10.465689+05:30	2022-09-20 14:09:10.465716+05:30	1	\N	\N	f	f
2340	COST_CENTER	Cost Center	Burns Philp	9921	2022-09-20 14:09:10.465773+05:30	2022-09-20 14:09:10.4658+05:30	1	\N	\N	f	f
2341	COST_CENTER	Cost Center	Business Connexion Group	9922	2022-09-20 14:09:10.465857+05:30	2022-09-20 14:09:10.465884+05:30	1	\N	\N	f	f
2342	COST_CENTER	Cost Center	Buynlarge Corporation	9923	2022-09-20 14:09:10.46594+05:30	2022-09-20 14:09:10.465967+05:30	1	\N	\N	f	f
2343	COST_CENTER	Cost Center	Cadillac Fairview	9924	2022-09-20 14:09:10.466038+05:30	2022-09-20 14:09:10.466066+05:30	1	\N	\N	f	f
2344	COST_CENTER	Cost Center	Camperdown Dairy International	9925	2022-09-20 14:09:10.466122+05:30	2022-09-20 14:09:10.466149+05:30	1	\N	\N	f	f
2345	COST_CENTER	Cost Center	Canada Deposit Insurance Corporation	9926	2022-09-20 14:09:10.466205+05:30	2022-09-20 14:09:10.466233+05:30	1	\N	\N	f	f
2346	COST_CENTER	Cost Center	Canadian Bank Note Company	9927	2022-09-20 14:09:10.466289+05:30	2022-09-20 14:09:10.466316+05:30	1	\N	\N	f	f
2347	COST_CENTER	Cost Center	Canadian Light Source	9928	2022-09-20 14:09:10.466585+05:30	2022-09-20 14:09:10.466644+05:30	1	\N	\N	f	f
2348	COST_CENTER	Cost Center	Canadian Natural Resources	9929	2022-09-20 14:09:10.466748+05:30	2022-09-20 14:09:10.466785+05:30	1	\N	\N	f	f
2349	COST_CENTER	Cost Center	Canadian Steamship Lines	9930	2022-09-20 14:09:10.466862+05:30	2022-09-20 14:09:10.466892+05:30	1	\N	\N	f	f
2350	COST_CENTER	Cost Center	Canadian Tire Bank	9931	2022-09-20 14:09:10.466955+05:30	2022-09-20 14:09:10.466984+05:30	1	\N	\N	f	f
2351	COST_CENTER	Cost Center	Candente Copper	9932	2022-09-20 14:09:10.467047+05:30	2022-09-20 14:09:10.467171+05:30	1	\N	\N	f	f
2352	COST_CENTER	Cost Center	Candor Corp	9933	2022-09-20 14:09:10.467383+05:30	2022-09-20 14:09:10.467412+05:30	1	\N	\N	f	f
2353	COST_CENTER	Cost Center	CanJet	9934	2022-09-20 14:09:10.46747+05:30	2022-09-20 14:09:10.467498+05:30	1	\N	\N	f	f
2354	COST_CENTER	Cost Center	Capcom Vancouver	9935	2022-09-20 14:09:10.467554+05:30	2022-09-20 14:09:10.467581+05:30	1	\N	\N	f	f
2355	COST_CENTER	Cost Center	Capitec Bank	9936	2022-09-20 14:09:10.467637+05:30	2022-09-20 14:09:10.467664+05:30	1	\N	\N	f	f
2356	COST_CENTER	Cost Center	Capsule	9937	2022-09-20 14:09:10.467721+05:30	2022-09-20 14:09:10.467748+05:30	1	\N	\N	f	f
2357	COST_CENTER	Cost Center	Cardiovascular Disease Special	9938	2022-09-20 14:09:10.467823+05:30	2022-09-20 14:09:10.468126+05:30	1	\N	\N	f	f
2358	COST_CENTER	Cost Center	Carolina Health Centers, Inc.	9939	2022-09-20 14:09:10.468193+05:30	2022-09-20 14:09:10.468336+05:30	1	\N	\N	f	f
2359	COST_CENTER	Cost Center	Casavant Frares	9940	2022-09-20 14:09:10.46851+05:30	2022-09-20 14:09:10.46854+05:30	1	\N	\N	f	f
2360	COST_CENTER	Cost Center	Cathedral Software	9941	2022-09-20 14:09:10.468735+05:30	2022-09-20 14:09:10.468761+05:30	1	\N	\N	f	f
2361	COST_CENTER	Cost Center	CBH Group	9942	2022-09-20 14:09:10.468829+05:30	2022-09-20 14:09:10.468857+05:30	1	\N	\N	f	f
2362	COST_CENTER	Cost Center	Cbus	9943	2022-09-20 14:09:10.468913+05:30	2022-09-20 14:09:10.46894+05:30	1	\N	\N	f	f
2363	COST_CENTER	Cost Center	CDC Ixis North America Inc.	9944	2022-09-20 14:09:10.469145+05:30	2022-09-20 14:09:10.469173+05:30	1	\N	\N	f	f
2364	COST_CENTER	Cost Center	Cell C	9945	2022-09-20 14:09:10.46935+05:30	2022-09-20 14:09:10.46939+05:30	1	\N	\N	f	f
2365	COST_CENTER	Cost Center	Cellcom Communications	9946	2022-09-20 14:09:10.469447+05:30	2022-09-20 14:09:10.469474+05:30	1	\N	\N	f	f
2366	COST_CENTER	Cost Center	Centra Gas Manitoba Inc.	9947	2022-09-20 14:09:10.46953+05:30	2022-09-20 14:09:10.469557+05:30	1	\N	\N	f	f
2367	COST_CENTER	Cost Center	CGH Medical Center	9948	2022-09-20 14:09:10.469613+05:30	2022-09-20 14:09:10.46964+05:30	1	\N	\N	f	f
2368	COST_CENTER	Cost Center	Chapters	9949	2022-09-20 14:09:10.469696+05:30	2022-09-20 14:09:10.469723+05:30	1	\N	\N	f	f
2369	COST_CENTER	Cost Center	Checkers	9950	2022-09-20 14:09:10.469779+05:30	2022-09-20 14:09:10.469806+05:30	1	\N	\N	f	f
2370	COST_CENTER	Cost Center	CHEP	9951	2022-09-20 14:09:10.469863+05:30	2022-09-20 14:09:10.46989+05:30	1	\N	\N	f	f
2371	COST_CENTER	Cost Center	Chevron Texaco	9952	2022-09-20 14:09:10.469946+05:30	2022-09-20 14:09:10.469973+05:30	1	\N	\N	f	f
2372	COST_CENTER	Cost Center	CHOAM	9953	2022-09-20 14:09:10.47003+05:30	2022-09-20 14:09:10.470057+05:30	1	\N	\N	f	f
2373	COST_CENTER	Cost Center	Choices Market	9954	2022-09-20 14:09:10.470113+05:30	2022-09-20 14:09:10.47014+05:30	1	\N	\N	f	f
2374	COST_CENTER	Cost Center	CIMIC Group	9955	2022-09-20 14:09:10.482026+05:30	2022-09-20 14:09:10.482106+05:30	1	\N	\N	f	f
2375	COST_CENTER	Cost Center	Cinium Financial Services	9956	2022-09-20 14:09:10.483204+05:30	2022-09-20 14:09:10.483268+05:30	1	\N	\N	f	f
2376	COST_CENTER	Cost Center	Cirque du Soleil	9957	2022-09-20 14:09:10.483358+05:30	2022-09-20 14:09:10.483393+05:30	1	\N	\N	f	f
2377	COST_CENTER	Cost Center	Citizens Communications	9958	2022-09-20 14:09:10.48364+05:30	2022-09-20 14:09:10.483679+05:30	1	\N	\N	f	f
2378	COST_CENTER	Cost Center	Cleco Corporation	9959	2022-09-20 14:09:10.483753+05:30	2022-09-20 14:09:10.483784+05:30	1	\N	\N	f	f
2379	COST_CENTER	Cost Center	Clerby	9960	2022-09-20 14:09:10.483854+05:30	2022-09-20 14:09:10.483884+05:30	1	\N	\N	f	f
2380	COST_CENTER	Cost Center	CMV Group	9961	2022-09-20 14:09:10.483949+05:30	2022-09-20 14:09:10.483979+05:30	1	\N	\N	f	f
2381	COST_CENTER	Cost Center	Coachman Insurance Company	9962	2022-09-20 14:09:10.484042+05:30	2022-09-20 14:09:10.484072+05:30	1	\N	\N	f	f
2382	COST_CENTER	Cost Center	Coca-Cola Amatil	9963	2022-09-20 14:09:10.484135+05:30	2022-09-20 14:09:10.484498+05:30	1	\N	\N	f	f
2383	COST_CENTER	Cost Center	Coles Group	9964	2022-09-20 14:09:10.484704+05:30	2022-09-20 14:09:10.484745+05:30	1	\N	\N	f	f
2384	COST_CENTER	Cost Center	Column Five	9965	2022-09-20 14:09:10.48482+05:30	2022-09-20 14:09:10.484857+05:30	1	\N	\N	f	f
2385	COST_CENTER	Cost Center	Comm100	9966	2022-09-20 14:09:10.484934+05:30	2022-09-20 14:09:10.484966+05:30	1	\N	\N	f	f
2386	COST_CENTER	Cost Center	Commonwealth Bank	9967	2022-09-20 14:09:10.48506+05:30	2022-09-20 14:09:10.48509+05:30	1	\N	\N	f	f
2387	COST_CENTER	Cost Center	Community Agency Services	9968	2022-09-20 14:09:10.485168+05:30	2022-09-20 14:09:10.485201+05:30	1	\N	\N	f	f
2388	COST_CENTER	Cost Center	Compass Investment Partners	9969	2022-09-20 14:09:10.48541+05:30	2022-09-20 14:09:10.485513+05:30	1	\N	\N	f	f
2389	COST_CENTER	Cost Center	Compass Resources	9970	2022-09-20 14:09:10.485635+05:30	2022-09-20 14:09:10.485676+05:30	1	\N	\N	f	f
2390	COST_CENTER	Cost Center	Computer Sciences Corporation	9971	2022-09-20 14:09:10.485755+05:30	2022-09-20 14:09:10.485784+05:30	1	\N	\N	f	f
2391	COST_CENTER	Cost Center	Computershare	9972	2022-09-20 14:09:10.485846+05:30	2022-09-20 14:09:10.485876+05:30	1	\N	\N	f	f
2392	COST_CENTER	Cost Center	ComTron	9973	2022-09-20 14:09:10.485937+05:30	2022-09-20 14:09:10.485966+05:30	1	\N	\N	f	f
2393	COST_CENTER	Cost Center	Conductor	9974	2022-09-20 14:09:10.486027+05:30	2022-09-20 14:09:10.486056+05:30	1	\N	\N	f	f
2394	COST_CENTER	Cost Center	Conestoga-Rovers and Associates	9975	2022-09-20 14:09:10.486141+05:30	2022-09-20 14:09:10.486182+05:30	1	\N	\N	f	f
2395	COST_CENTER	Cost Center	Conglomerated Amalgamated	9976	2022-09-20 14:09:10.4866+05:30	2022-09-20 14:09:10.486633+05:30	1	\N	\N	f	f
2396	COST_CENTER	Cost Center	Copper Ab	9977	2022-09-20 14:09:10.486702+05:30	2022-09-20 14:09:10.486745+05:30	1	\N	\N	f	f
2397	COST_CENTER	Cost Center	Cordiant Capital Inc.	9978	2022-09-20 14:09:10.486868+05:30	2022-09-20 14:09:10.486929+05:30	1	\N	\N	f	f
2398	COST_CENTER	Cost Center	Corley Energy	9979	2022-09-20 14:09:10.487038+05:30	2022-09-20 14:09:10.487079+05:30	1	\N	\N	f	f
2399	COST_CENTER	Cost Center	Corus Entertainment	9980	2022-09-20 14:09:10.487477+05:30	2022-09-20 14:09:10.487531+05:30	1	\N	\N	f	f
2400	COST_CENTER	Cost Center	CostLess Insurance	9981	2022-09-20 14:09:10.487614+05:30	2022-09-20 14:09:10.487647+05:30	1	\N	\N	f	f
2401	COST_CENTER	Cost Center	Cotton On	9982	2022-09-20 14:09:10.487716+05:30	2022-09-20 14:09:10.48778+05:30	1	\N	\N	f	f
2402	COST_CENTER	Cost Center	Country Energy	9983	2022-09-20 14:09:10.488089+05:30	2022-09-20 14:09:10.488126+05:30	1	\N	\N	f	f
2403	COST_CENTER	Cost Center	Country Style	9984	2022-09-20 14:09:10.488599+05:30	2022-09-20 14:09:10.488654+05:30	1	\N	\N	f	f
2404	COST_CENTER	Cost Center	Creative Healthcare	9985	2022-09-20 14:09:10.489024+05:30	2022-09-20 14:09:10.489077+05:30	1	\N	\N	f	f
2405	COST_CENTER	Cost Center	Crestline Coach	9986	2022-09-20 14:09:10.489147+05:30	2022-09-20 14:09:10.489175+05:30	1	\N	\N	f	f
2406	COST_CENTER	Cost Center	Crossecom	9987	2022-09-20 14:09:10.489235+05:30	2022-09-20 14:09:10.489263+05:30	1	\N	\N	f	f
2407	COST_CENTER	Cost Center	Crown Resorts	9988	2022-09-20 14:09:10.489321+05:30	2022-09-20 14:09:10.48936+05:30	1	\N	\N	f	f
2408	COST_CENTER	Cost Center	CSL Limited	9989	2022-09-20 14:09:10.489642+05:30	2022-09-20 14:09:10.489665+05:30	1	\N	\N	f	f
2409	COST_CENTER	Cost Center	CSR Limited	9990	2022-09-20 14:09:10.489718+05:30	2022-09-20 14:09:10.489746+05:30	1	\N	\N	f	f
2410	COST_CENTER	Cost Center	CTV Television Network	9991	2022-09-20 14:09:10.489801+05:30	2022-09-20 14:09:10.489831+05:30	1	\N	\N	f	f
2411	COST_CENTER	Cost Center	Cuna Mutual Insurance Society	9992	2022-09-20 14:09:10.489892+05:30	2022-09-20 14:09:10.489922+05:30	1	\N	\N	f	f
2412	COST_CENTER	Cost Center	Cvibe Insurance	9993	2022-09-20 14:09:10.489982+05:30	2022-09-20 14:09:10.490011+05:30	1	\N	\N	f	f
2413	COST_CENTER	Cost Center	Cyberdyne Systems	9994	2022-09-20 14:09:10.490072+05:30	2022-09-20 14:09:10.490101+05:30	1	\N	\N	f	f
2414	COST_CENTER	Cost Center	Cymax Stores	9995	2022-09-20 14:09:10.490161+05:30	2022-09-20 14:09:10.49019+05:30	1	\N	\N	f	f
2415	COST_CENTER	Cost Center	Cymer	9996	2022-09-20 14:09:10.49025+05:30	2022-09-20 14:09:10.490279+05:30	1	\N	\N	f	f
2416	COST_CENTER	Cost Center	Cym Labs	9997	2022-09-20 14:09:10.490344+05:30	2022-09-20 14:09:10.490462+05:30	1	\N	\N	f	f
2417	COST_CENTER	Cost Center	Dabtype	9998	2022-09-20 14:09:10.490534+05:30	2022-09-20 14:09:10.490562+05:30	1	\N	\N	f	f
2418	COST_CENTER	Cost Center	Dabvine	9999	2022-09-20 14:09:10.490618+05:30	2022-09-20 14:09:10.490645+05:30	1	\N	\N	f	f
2419	COST_CENTER	Cost Center	Dare Foods	10000	2022-09-20 14:09:10.490701+05:30	2022-09-20 14:09:10.490732+05:30	1	\N	\N	f	f
2420	COST_CENTER	Cost Center	DataDyne	10001	2022-09-20 14:09:10.49079+05:30	2022-09-20 14:09:10.490817+05:30	1	\N	\N	f	f
2421	COST_CENTER	Cost Center	David Jones Limited	10002	2022-09-20 14:09:10.490874+05:30	2022-09-20 14:09:10.490901+05:30	1	\N	\N	f	f
2422	COST_CENTER	Cost Center	Davis and Young LPA	10003	2022-09-20 14:09:10.490958+05:30	2022-09-20 14:09:10.490985+05:30	1	\N	\N	f	f
2423	COST_CENTER	Cost Center	Adidas	9584	2022-09-20 14:09:10.491041+05:30	2022-09-20 14:09:10.491068+05:30	1	\N	\N	f	f
2424	COST_CENTER	Cost Center	Fabrication	9585	2022-09-20 14:09:10.497515+05:30	2022-09-20 14:09:10.497607+05:30	1	\N	\N	f	f
2425	COST_CENTER	Cost Center	FAE	9586	2022-09-20 14:09:10.498314+05:30	2022-09-20 14:09:10.499646+05:30	1	\N	\N	f	f
2426	COST_CENTER	Cost Center	Eastside	9536	2022-09-20 14:09:10.500517+05:30	2022-09-20 14:09:10.500653+05:30	1	\N	\N	f	f
2427	COST_CENTER	Cost Center	North	9537	2022-09-20 14:09:10.50096+05:30	2022-09-20 14:09:10.501164+05:30	1	\N	\N	f	f
2428	COST_CENTER	Cost Center	South	9538	2022-09-20 14:09:10.502041+05:30	2022-09-20 14:09:10.502182+05:30	1	\N	\N	f	f
2429	COST_CENTER	Cost Center	West Coast	9539	2022-09-20 14:09:10.502482+05:30	2022-09-20 14:09:10.502517+05:30	1	\N	\N	f	f
2430	COST_CENTER	Cost Center	Legal and Secretarial	7229	2022-09-20 14:09:10.502586+05:30	2022-09-20 14:09:10.502613+05:30	1	\N	\N	f	f
2431	COST_CENTER	Cost Center	Strategy Planning	7228	2022-09-20 14:09:10.50267+05:30	2022-09-20 14:09:10.502698+05:30	1	\N	\N	f	f
2432	COST_CENTER	Cost Center	Administration	7227	2022-09-20 14:09:10.502754+05:30	2022-09-20 14:09:10.502781+05:30	1	\N	\N	f	f
2433	COST_CENTER	Cost Center	Retail	7226	2022-09-20 14:09:10.502838+05:30	2022-09-20 14:09:10.502865+05:30	1	\N	\N	f	f
2434	COST_CENTER	Cost Center	SME	7225	2022-09-20 14:09:10.502921+05:30	2022-09-20 14:09:10.502948+05:30	1	\N	\N	f	f
2435	COST_CENTER	Cost Center	Marketing	7224	2022-09-20 14:09:10.503004+05:30	2022-09-20 14:09:10.503032+05:30	1	\N	\N	f	f
2436	COST_CENTER	Cost Center	Audit	7223	2022-09-20 14:09:10.503088+05:30	2022-09-20 14:09:10.503115+05:30	1	\N	\N	f	f
2437	COST_CENTER	Cost Center	Treasury	7222	2022-09-20 14:09:10.503171+05:30	2022-09-20 14:09:10.503199+05:30	1	\N	\N	f	f
2438	COST_CENTER	Cost Center	Internal	7221	2022-09-20 14:09:10.503255+05:30	2022-09-20 14:09:10.503282+05:30	1	\N	\N	f	f
2439	COST_CENTER	Cost Center	Sales and Cross	7220	2022-09-20 14:09:10.503338+05:30	2022-09-20 14:09:10.503367+05:30	1	\N	\N	f	f
2440	SYSTEM_OPERATING	System Operating	Support-M	expense_custom_field.system operating.1	2022-09-20 14:09:10.752946+05:30	2022-09-20 14:09:10.752986+05:30	1	\N	{"placeholder": "Select System Operating", "custom_field_id": 174995}	f	f
2441	SYSTEM_OPERATING	System Operating	GB3-White	expense_custom_field.system operating.2	2022-09-20 14:09:10.753043+05:30	2022-09-20 14:09:10.753065+05:30	1	\N	{"placeholder": "Select System Operating", "custom_field_id": 174995}	f	f
2442	SYSTEM_OPERATING	System Operating	TSM - Black	expense_custom_field.system operating.3	2022-09-20 14:09:10.753128+05:30	2022-09-20 14:09:10.759395+05:30	1	\N	{"placeholder": "Select System Operating", "custom_field_id": 174995}	f	f
3180	MERCHANT	Merchant	Entity V700	852	2022-09-20 14:10:24.029423+05:30	2022-09-20 14:10:24.02945+05:30	1	\N	\N	f	f
2443	SYSTEM_OPERATING	System Operating	GB1-White	expense_custom_field.system operating.4	2022-09-20 14:09:10.768644+05:30	2022-09-20 14:09:10.768789+05:30	1	\N	{"placeholder": "Select System Operating", "custom_field_id": 174995}	f	f
2444	SYSTEM_OPERATING	System Operating	DevD	expense_custom_field.system operating.5	2022-09-20 14:09:10.768964+05:30	2022-09-20 14:09:10.769008+05:30	1	\N	{"placeholder": "Select System Operating", "custom_field_id": 174995}	f	f
2445	SYSTEM_OPERATING	System Operating	DevH	expense_custom_field.system operating.6	2022-09-20 14:09:10.769123+05:30	2022-09-20 14:09:10.769164+05:30	1	\N	{"placeholder": "Select System Operating", "custom_field_id": 174995}	f	f
2446	SYSTEM_OPERATING	System Operating	PMBr	expense_custom_field.system operating.7	2022-09-20 14:09:10.769733+05:30	2022-09-20 14:09:10.769797+05:30	1	\N	{"placeholder": "Select System Operating", "custom_field_id": 174995}	f	f
2447	SYSTEM_OPERATING	System Operating	octane squad	expense_custom_field.system operating.8	2022-09-20 14:09:10.769952+05:30	2022-09-20 14:09:10.769998+05:30	1	\N	{"placeholder": "Select System Operating", "custom_field_id": 174995}	f	f
2448	SYSTEM_OPERATING	System Operating	PMD	expense_custom_field.system operating.9	2022-09-20 14:09:10.770144+05:30	2022-09-20 14:09:10.77035+05:30	1	\N	{"placeholder": "Select System Operating", "custom_field_id": 174995}	f	f
2449	SYSTEM_OPERATING	System Operating	wraith squad	expense_custom_field.system operating.10	2022-09-20 14:09:10.770559+05:30	2022-09-20 14:09:10.770612+05:30	1	\N	{"placeholder": "Select System Operating", "custom_field_id": 174995}	f	f
2450	SYSTEM_OPERATING	System Operating	PMDD	expense_custom_field.system operating.11	2022-09-20 14:09:10.770767+05:30	2022-09-20 14:09:10.771407+05:30	1	\N	{"placeholder": "Select System Operating", "custom_field_id": 174995}	f	f
2451	SYSTEM_OPERATING	System Operating	BOOK	expense_custom_field.system operating.12	2022-09-20 14:09:10.771814+05:30	2022-09-20 14:09:10.77186+05:30	1	\N	{"placeholder": "Select System Operating", "custom_field_id": 174995}	f	f
2452	SYSTEM_OPERATING	System Operating	GB9-White	expense_custom_field.system operating.13	2022-09-20 14:09:10.772466+05:30	2022-09-20 14:09:10.772538+05:30	1	\N	{"placeholder": "Select System Operating", "custom_field_id": 174995}	f	f
2453	SYSTEM_OPERATING	System Operating	TSS - Black	expense_custom_field.system operating.14	2022-09-20 14:09:10.772743+05:30	2022-09-20 14:09:10.7728+05:30	1	\N	{"placeholder": "Select System Operating", "custom_field_id": 174995}	f	f
2454	SYSTEM_OPERATING	System Operating	PMWe	expense_custom_field.system operating.15	2022-09-20 14:09:10.773822+05:30	2022-09-20 14:09:10.773916+05:30	1	\N	{"placeholder": "Select System Operating", "custom_field_id": 174995}	f	f
683	PROJECT	Project	Project 7	203315	2022-09-20 14:09:06.850486+05:30	2022-09-20 14:09:06.850626+05:30	1	t	\N	f	f
2455	SYSTEM_OPERATING	System Operating	TSL - Black	expense_custom_field.system operating.16	2022-09-20 14:09:10.774574+05:30	2022-09-20 14:09:10.774624+05:30	1	\N	{"placeholder": "Select System Operating", "custom_field_id": 174995}	f	f
2456	SYSTEM_OPERATING	System Operating	Train-MS	expense_custom_field.system operating.17	2022-09-20 14:09:10.774731+05:30	2022-09-20 14:09:10.774783+05:30	1	\N	{"placeholder": "Select System Operating", "custom_field_id": 174995}	f	f
2457	SYSTEM_OPERATING	System Operating	GB6-White	expense_custom_field.system operating.18	2022-09-20 14:09:10.775079+05:30	2022-09-20 14:09:10.775183+05:30	1	\N	{"placeholder": "Select System Operating", "custom_field_id": 174995}	f	f
2712	TAX_GROUP	Tax Group	71DTN3JPS4	tg3s7XQ9gMS8	2022-09-20 14:09:11.576836+05:30	2022-09-20 14:09:11.576896+05:30	1	\N	{"tax_rate": 0.18}	f	f
2458	SYSTEM_OPERATING	System Operating	naruto uzumaki	expense_custom_field.system operating.19	2022-09-20 14:09:10.7759+05:30	2022-09-20 14:09:10.77663+05:30	1	\N	{"placeholder": "Select System Operating", "custom_field_id": 174995}	f	f
2459	TEAM	Team	CCC	expense_custom_field.team.1	2022-09-20 14:09:10.823717+05:30	2022-09-20 14:09:10.824018+05:30	1	\N	{"placeholder": "Select Team", "custom_field_id": 174175}	f	f
2460	TEAM	Team	Integrations	expense_custom_field.team.2	2022-09-20 14:09:10.824396+05:30	2022-09-20 14:09:10.824443+05:30	1	\N	{"placeholder": "Select Team", "custom_field_id": 174175}	f	f
2461	USER_DIMENSION_COPY	User Dimension Copy	Wedding Planning by Whitney	expense_custom_field.user dimension copy.1	2022-09-20 14:09:10.841239+05:30	2022-09-20 14:09:10.841279+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2462	USER_DIMENSION_COPY	User Dimension Copy	Dylan Sollfrank	expense_custom_field.user dimension copy.2	2022-09-20 14:09:10.841361+05:30	2022-09-20 14:09:10.841384+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2463	USER_DIMENSION_COPY	User Dimension Copy	Admin	expense_custom_field.user dimension copy.3	2022-09-20 14:09:10.841843+05:30	2022-09-20 14:09:10.841866+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2464	USER_DIMENSION_COPY	User Dimension Copy	Production	expense_custom_field.user dimension copy.4	2022-09-20 14:09:10.841925+05:30	2022-09-20 14:09:10.841946+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2465	USER_DIMENSION_COPY	User Dimension Copy	Fyle	expense_custom_field.user dimension copy.5	2022-09-20 14:09:10.842016+05:30	2022-09-20 14:09:10.842046+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2466	USER_DIMENSION_COPY	User Dimension Copy	Diego Rodriguez	expense_custom_field.user dimension copy.6	2022-09-20 14:09:10.842115+05:30	2022-09-20 14:09:10.842145+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
3043	MERCHANT	Merchant	Ashwin	852	2022-09-20 14:10:15.786052+05:30	2022-09-20 14:10:15.78614+05:30	1	\N	\N	f	f
2467	USER_DIMENSION_COPY	User Dimension Copy	wraith squad	expense_custom_field.user dimension copy.7	2022-09-20 14:09:10.842214+05:30	2022-09-20 14:09:10.842642+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2468	USER_DIMENSION_COPY	User Dimension Copy	Ashwinn	expense_custom_field.user dimension copy.8	2022-09-20 14:09:10.842746+05:30	2022-09-20 14:09:10.842769+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2469	USER_DIMENSION_COPY	User Dimension Copy	Geeta Kalapatapu	expense_custom_field.user dimension copy.9	2022-09-20 14:09:10.842833+05:30	2022-09-20 14:09:10.842862+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2470	USER_DIMENSION_COPY	User Dimension Copy	naruto uzumaki	expense_custom_field.user dimension copy.10	2022-09-20 14:09:10.842931+05:30	2022-09-20 14:09:10.84296+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2471	USER_DIMENSION_COPY	User Dimension Copy	Travis Waldron	expense_custom_field.user dimension copy.11	2022-09-20 14:09:10.843123+05:30	2022-09-20 14:09:10.843157+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2472	USER_DIMENSION_COPY	User Dimension Copy	Weiskopf Consulting	expense_custom_field.user dimension copy.12	2022-09-20 14:09:10.843227+05:30	2022-09-20 14:09:10.843254+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2473	USER_DIMENSION_COPY	User Dimension Copy	Dukes Basketball Camp	expense_custom_field.user dimension copy.13	2022-09-20 14:09:10.843307+05:30	2022-09-20 14:09:10.843328+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2474	USER_DIMENSION_COPY	User Dimension Copy	Product	expense_custom_field.user dimension copy.14	2022-09-20 14:09:10.843402+05:30	2022-09-20 14:09:10.843432+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2475	USER_DIMENSION_COPY	User Dimension Copy	Mark Cho	expense_custom_field.user dimension copy.15	2022-09-20 14:09:10.844001+05:30	2022-09-20 14:09:10.844035+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2476	USER_DIMENSION_COPY	User Dimension Copy	Sushi by Katsuyuki	expense_custom_field.user dimension copy.16	2022-09-20 14:09:10.84414+05:30	2022-09-20 14:09:10.844161+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2477	USER_DIMENSION_COPY	User Dimension Copy	Diego Rodriguez:Test Project	expense_custom_field.user dimension copy.17	2022-09-20 14:09:10.844328+05:30	2022-09-20 14:09:10.844377+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2478	USER_DIMENSION_COPY	User Dimension Copy	Sales	expense_custom_field.user dimension copy.18	2022-09-20 14:09:10.844501+05:30	2022-09-20 14:09:10.844543+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2479	USER_DIMENSION_COPY	User Dimension Copy	Pye's Cakes	expense_custom_field.user dimension copy.19	2022-09-20 14:09:10.845209+05:30	2022-09-20 14:09:10.845279+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2480	USER_DIMENSION_COPY	User Dimension Copy	Assembly	expense_custom_field.user dimension copy.20	2022-09-20 14:09:10.845433+05:30	2022-09-20 14:09:10.84548+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2481	USER_DIMENSION_COPY	User Dimension Copy	Freeman Sporting Goods:55 Twin Lane	expense_custom_field.user dimension copy.21	2022-09-20 14:09:10.845613+05:30	2022-09-20 14:09:10.845654+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2482	USER_DIMENSION_COPY	User Dimension Copy	Machine Shop	expense_custom_field.user dimension copy.22	2022-09-20 14:09:10.845779+05:30	2022-09-20 14:09:10.845821+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2483	USER_DIMENSION_COPY	User Dimension Copy	Kookies by Kathy	expense_custom_field.user dimension copy.23	2022-09-20 14:09:10.84595+05:30	2022-09-20 14:09:10.845992+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2484	USER_DIMENSION_COPY	User Dimension Copy	Shara Barnett:Barnett Design	expense_custom_field.user dimension copy.24	2022-09-20 14:09:10.846113+05:30	2022-09-20 14:09:10.846162+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2485	USER_DIMENSION_COPY	User Dimension Copy	Amy's Bird Sanctuary	expense_custom_field.user dimension copy.25	2022-09-20 14:09:10.846296+05:30	2022-09-20 14:09:10.846337+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2517	LOCATION	Location	Australia	expense_custom_field.location.5	2022-09-20 14:09:10.894617+05:30	2022-09-20 14:09:10.894661+05:30	1	\N	{"placeholder": "Select Location", "custom_field_id": 845}	f	f
2486	USER_DIMENSION_COPY	User Dimension Copy	Amy's Bird Sanctuary:Test Project	expense_custom_field.user dimension copy.26	2022-09-20 14:09:10.846451+05:30	2022-09-20 14:09:10.846497+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2487	USER_DIMENSION_COPY	User Dimension Copy	Gevelber Photography	expense_custom_field.user dimension copy.27	2022-09-20 14:09:10.846918+05:30	2022-09-20 14:09:10.847145+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2488	USER_DIMENSION_COPY	User Dimension Copy	Red Rock Diner	expense_custom_field.user dimension copy.28	2022-09-20 14:09:10.847412+05:30	2022-09-20 14:09:10.84782+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2489	USER_DIMENSION_COPY	User Dimension Copy	Fabrication	expense_custom_field.user dimension copy.29	2022-09-20 14:09:10.847937+05:30	2022-09-20 14:09:10.847967+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2490	USER_DIMENSION_COPY	User Dimension Copy	Cool Cars	expense_custom_field.user dimension copy.30	2022-09-20 14:09:10.848037+05:30	2022-09-20 14:09:10.848058+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2491	USER_DIMENSION_COPY	User Dimension Copy	octane squad	expense_custom_field.user dimension copy.31	2022-09-20 14:09:10.848126+05:30	2022-09-20 14:09:10.848146+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2492	USER_DIMENSION_COPY	User Dimension Copy	Sravan BLR Customer	expense_custom_field.user dimension copy.32	2022-09-20 14:09:10.848317+05:30	2022-09-20 14:09:10.848347+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2493	USER_DIMENSION_COPY	User Dimension Copy	Rago Travel Agency	expense_custom_field.user dimension copy.33	2022-09-20 14:09:10.848425+05:30	2022-09-20 14:09:10.848466+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2494	USER_DIMENSION_COPY	User Dimension Copy	Marketing	expense_custom_field.user dimension copy.34	2022-09-20 14:09:10.8487+05:30	2022-09-20 14:09:10.848719+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2495	USER_DIMENSION_COPY	User Dimension Copy	John Melton	expense_custom_field.user dimension copy.35	2022-09-20 14:09:10.848768+05:30	2022-09-20 14:09:10.848789+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2496	USER_DIMENSION_COPY	User Dimension Copy	Inspection	expense_custom_field.user dimension copy.36	2022-09-20 14:09:10.849628+05:30	2022-09-20 14:09:10.849676+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2497	USER_DIMENSION_COPY	User Dimension Copy	Bill's Windsurf Shop	expense_custom_field.user dimension copy.37	2022-09-20 14:09:10.849904+05:30	2022-09-20 14:09:10.849946+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2534	DEPARTMENTS	Departments	Admin	expense_custom_field.departments.5	2022-09-20 14:09:10.919259+05:30	2022-09-20 14:09:10.919285+05:30	1	\N	{"placeholder": "Select Departments", "custom_field_id": 174997}	f	f
2498	USER_DIMENSION_COPY	User Dimension Copy	Paulsen Medical Supplies	expense_custom_field.user dimension copy.38	2022-09-20 14:09:10.850109+05:30	2022-09-20 14:09:10.850578+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2499	USER_DIMENSION_COPY	User Dimension Copy	Kate Whelan	expense_custom_field.user dimension copy.39	2022-09-20 14:09:10.850781+05:30	2022-09-20 14:09:10.850809+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2500	USER_DIMENSION_COPY	User Dimension Copy	Freeman Sporting Goods:0969 Ocean View Road	expense_custom_field.user dimension copy.40	2022-09-20 14:09:10.850893+05:30	2022-09-20 14:09:10.850921+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2501	USER_DIMENSION_COPY	User Dimension Copy	Freeman Sporting Goods	expense_custom_field.user dimension copy.41	2022-09-20 14:09:10.850978+05:30	2022-09-20 14:09:10.850999+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2502	USER_DIMENSION_COPY	User Dimension Copy	Rondonuwu Fruit and Vegi	expense_custom_field.user dimension copy.42	2022-09-20 14:09:10.851058+05:30	2022-09-20 14:09:10.851074+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2503	USER_DIMENSION_COPY	User Dimension Copy	Shara Barnett	expense_custom_field.user dimension copy.43	2022-09-20 14:09:10.851145+05:30	2022-09-20 14:09:10.851351+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2504	USER_DIMENSION_COPY	User Dimension Copy	Video Games by Dan	expense_custom_field.user dimension copy.44	2022-09-20 14:09:10.851575+05:30	2022-09-20 14:09:10.851654+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2505	USER_DIMENSION_COPY	User Dimension Copy	Service	expense_custom_field.user dimension copy.45	2022-09-20 14:09:10.851748+05:30	2022-09-20 14:09:10.851781+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2745	TAX_GROUP	Tax Group	ITS-AU @0.0%	tg9e1bqo5zgV	2022-09-20 14:09:11.626516+05:30	2022-09-20 14:09:11.626589+05:30	1	\N	{"tax_rate": 0.0}	f	f
2506	USER_DIMENSION_COPY	User Dimension Copy	Engineering	expense_custom_field.user dimension copy.46	2022-09-20 14:09:10.851863+05:30	2022-09-20 14:09:10.851885+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2507	USER_DIMENSION_COPY	User Dimension Copy	Jeff's Jalopies	expense_custom_field.user dimension copy.47	2022-09-20 14:09:10.851945+05:30	2022-09-20 14:09:10.851965+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2508	USER_DIMENSION_COPY	User Dimension Copy	Sonnenschein Family Store	expense_custom_field.user dimension copy.48	2022-09-20 14:09:10.852026+05:30	2022-09-20 14:09:10.852063+05:30	1	\N	{"placeholder": "Select User Dimension Copy", "custom_field_id": 174991}	f	f
2509	OPERATING_SYSTEM	Operating System	India	expense_custom_field.operating system.1	2022-09-20 14:09:10.877424+05:30	2022-09-20 14:09:10.877464+05:30	1	\N	{"placeholder": "Select Operating System", "custom_field_id": 133433}	f	f
2510	OPERATING_SYSTEM	Operating System	USA1	expense_custom_field.operating system.2	2022-09-20 14:09:10.877535+05:30	2022-09-20 14:09:10.877557+05:30	1	\N	{"placeholder": "Select Operating System", "custom_field_id": 133433}	f	f
2511	OPERATING_SYSTEM	Operating System	USA2	expense_custom_field.operating system.3	2022-09-20 14:09:10.877626+05:30	2022-09-20 14:09:10.877646+05:30	1	\N	{"placeholder": "Select Operating System", "custom_field_id": 133433}	f	f
2512	OPERATING_SYSTEM	Operating System	USA3	expense_custom_field.operating system.4	2022-09-20 14:09:10.877703+05:30	2022-09-20 14:09:10.877733+05:30	1	\N	{"placeholder": "Select Operating System", "custom_field_id": 133433}	f	f
2513	LOCATION	Location	South Africa	expense_custom_field.location.1	2022-09-20 14:09:10.893887+05:30	2022-09-20 14:09:10.893935+05:30	1	\N	{"placeholder": "Select Location", "custom_field_id": 845}	f	f
2514	LOCATION	Location	Bangalore	expense_custom_field.location.2	2022-09-20 14:09:10.894017+05:30	2022-09-20 14:09:10.89404+05:30	1	\N	{"placeholder": "Select Location", "custom_field_id": 845}	f	f
2515	LOCATION	Location	London	expense_custom_field.location.3	2022-09-20 14:09:10.894328+05:30	2022-09-20 14:09:10.89437+05:30	1	\N	{"placeholder": "Select Location", "custom_field_id": 845}	f	f
2516	LOCATION	Location	New South Wales	expense_custom_field.location.4	2022-09-20 14:09:10.894475+05:30	2022-09-20 14:09:10.894508+05:30	1	\N	{"placeholder": "Select Location", "custom_field_id": 845}	f	f
3085	MERCHANT	Merchant	test Sharma	852	2022-09-20 14:10:15.929612+05:30	2022-09-20 14:10:15.929654+05:30	1	\N	\N	f	f
2518	LOCATION	Location	naruto uzumaki	expense_custom_field.location.6	2022-09-20 14:09:10.894748+05:30	2022-09-20 14:09:10.894776+05:30	1	\N	{"placeholder": "Select Location", "custom_field_id": 845}	f	f
2519	LOCATION	Location	octane squad	expense_custom_field.location.7	2022-09-20 14:09:10.894841+05:30	2022-09-20 14:09:10.89487+05:30	1	\N	{"placeholder": "Select Location", "custom_field_id": 845}	f	f
2520	LOCATION	Location	Holding Company	expense_custom_field.location.8	2022-09-20 14:09:10.894965+05:30	2022-09-20 14:09:10.895295+05:30	1	\N	{"placeholder": "Select Location", "custom_field_id": 845}	f	f
2521	LOCATION	Location	USA 1	expense_custom_field.location.9	2022-09-20 14:09:10.895395+05:30	2022-09-20 14:09:10.895418+05:30	1	\N	{"placeholder": "Select Location", "custom_field_id": 845}	f	f
3098	MERCHANT	Merchant	Ashwin from NetSuite	852	2022-09-20 14:10:15.969892+05:30	2022-09-20 14:10:15.969921+05:30	1	\N	\N	f	f
2522	LOCATION	Location	Elimination - Sub	expense_custom_field.location.10	2022-09-20 14:09:10.89549+05:30	2022-09-20 14:09:10.895927+05:30	1	\N	{"placeholder": "Select Location", "custom_field_id": 845}	f	f
2523	LOCATION	Location	wraith squad	expense_custom_field.location.11	2022-09-20 14:09:10.896367+05:30	2022-09-20 14:09:10.896398+05:30	1	\N	{"placeholder": "Select Location", "custom_field_id": 845}	f	f
2524	LOCATION	Location	USA 2	expense_custom_field.location.12	2022-09-20 14:09:10.896587+05:30	2022-09-20 14:09:10.896709+05:30	1	\N	{"placeholder": "Select Location", "custom_field_id": 845}	f	f
2525	LOCATION	Location	Elimination - Global	expense_custom_field.location.13	2022-09-20 14:09:10.896802+05:30	2022-09-20 14:09:10.896834+05:30	1	\N	{"placeholder": "Select Location", "custom_field_id": 845}	f	f
2526	LOCATION	Location	India	expense_custom_field.location.14	2022-09-20 14:09:10.896903+05:30	2022-09-20 14:09:10.896922+05:30	1	\N	{"placeholder": "Select Location", "custom_field_id": 845}	f	f
2527	LOCATION	Location	Elimination - NA	expense_custom_field.location.15	2022-09-20 14:09:10.896969+05:30	2022-09-20 14:09:10.896981+05:30	1	\N	{"placeholder": "Select Location", "custom_field_id": 845}	f	f
2528	LOCATION	Location	Canada	expense_custom_field.location.16	2022-09-20 14:09:10.897037+05:30	2022-09-20 14:09:10.897058+05:30	1	\N	{"placeholder": "Select Location", "custom_field_id": 845}	f	f
2529	LOCATION	Location	United Kingdom	expense_custom_field.location.17	2022-09-20 14:09:10.897135+05:30	2022-09-20 14:09:10.89716+05:30	1	\N	{"placeholder": "Select Location", "custom_field_id": 845}	f	f
2530	DEPARTMENTS	Departments	Services	expense_custom_field.departments.1	2022-09-20 14:09:10.918377+05:30	2022-09-20 14:09:10.918564+05:30	1	\N	{"placeholder": "Select Departments", "custom_field_id": 174997}	f	f
2531	DEPARTMENTS	Departments	Sales	expense_custom_field.departments.2	2022-09-20 14:09:10.918639+05:30	2022-09-20 14:09:10.918662+05:30	1	\N	{"placeholder": "Select Departments", "custom_field_id": 174997}	f	f
2532	DEPARTMENTS	Departments	IT	expense_custom_field.departments.3	2022-09-20 14:09:10.918729+05:30	2022-09-20 14:09:10.918799+05:30	1	\N	{"placeholder": "Select Departments", "custom_field_id": 174997}	f	f
2533	DEPARTMENTS	Departments	Marketing	expense_custom_field.departments.4	2022-09-20 14:09:10.918962+05:30	2022-09-20 14:09:10.91917+05:30	1	\N	{"placeholder": "Select Departments", "custom_field_id": 174997}	f	f
2535	TEAM_COPY	Team Copy	General Overhead-Current	expense_custom_field.team copy.1	2022-09-20 14:09:10.933098+05:30	2022-09-20 14:09:10.933126+05:30	1	\N	{"placeholder": "Select Team Copy", "custom_field_id": 174993}	f	f
2536	TEAM_COPY	Team Copy	General Overhead	expense_custom_field.team copy.2	2022-09-20 14:09:10.933178+05:30	2022-09-20 14:09:10.933201+05:30	1	\N	{"placeholder": "Select Team Copy", "custom_field_id": 174993}	f	f
2537	TEAM_COPY	Team Copy	Fyle Sage Intacct Integration	expense_custom_field.team copy.3	2022-09-20 14:09:10.933343+05:30	2022-09-20 14:09:10.933366+05:30	1	\N	{"placeholder": "Select Team Copy", "custom_field_id": 174993}	f	f
2538	TEAM_COPY	Team Copy	Integrations	expense_custom_field.team copy.4	2022-09-20 14:09:10.933425+05:30	2022-09-20 14:09:10.933446+05:30	1	\N	{"placeholder": "Select Team Copy", "custom_field_id": 174993}	f	f
2539	TEAM_COPY	Team Copy	Fyle Engineering	expense_custom_field.team copy.5	2022-09-20 14:09:10.933516+05:30	2022-09-20 14:09:10.933545+05:30	1	\N	{"placeholder": "Select Team Copy", "custom_field_id": 174993}	f	f
2540	TEAM_COPY	Team Copy	Platform APIs	expense_custom_field.team copy.6	2022-09-20 14:09:10.933614+05:30	2022-09-20 14:09:10.933643+05:30	1	\N	{"placeholder": "Select Team Copy", "custom_field_id": 174993}	f	f
2541	TEAM_COPY	Team Copy	Support Taxes	expense_custom_field.team copy.7	2022-09-20 14:09:10.933712+05:30	2022-09-20 14:09:10.933737+05:30	1	\N	{"placeholder": "Select Team Copy", "custom_field_id": 174993}	f	f
2542	TEAM_COPY	Team Copy	labhvam	expense_custom_field.team copy.8	2022-09-20 14:09:10.933797+05:30	2022-09-20 14:09:10.933827+05:30	1	\N	{"placeholder": "Select Team Copy", "custom_field_id": 174993}	f	f
2543	TEAM_COPY	Team Copy	Fyle NetSuite Integration	expense_custom_field.team copy.9	2022-09-20 14:09:10.933895+05:30	2022-09-20 14:09:10.933924+05:30	1	\N	{"placeholder": "Select Team Copy", "custom_field_id": 174993}	f	f
2746	TAX_GROUP	Tax Group	2VD4DE3305	tg9KXJlbl0fo	2022-09-20 14:09:11.626755+05:30	2022-09-20 14:09:11.62773+05:30	1	\N	{"tax_rate": 0.18}	f	f
2544	TEAM_COPY	Team Copy	T&M Project with Five Tasks	expense_custom_field.team copy.10	2022-09-20 14:09:10.933982+05:30	2022-09-20 14:09:10.933993+05:30	1	\N	{"placeholder": "Select Team Copy", "custom_field_id": 174993}	f	f
2545	TEAM_COPY	Team Copy	Fixed Fee Project with Five Tasks	expense_custom_field.team copy.11	2022-09-20 14:09:10.934048+05:30	2022-09-20 14:09:10.934078+05:30	1	\N	{"placeholder": "Select Team Copy", "custom_field_id": 174993}	f	f
2546	TEAM_COPY	Team Copy	Mobile App Redesign	expense_custom_field.team copy.12	2022-09-20 14:09:10.934146+05:30	2022-09-20 14:09:10.934176+05:30	1	\N	{"placeholder": "Select Team Copy", "custom_field_id": 174993}	f	f
2547	LOCATION_ENTITY	Location Entity	Wedding Planning by Whitney	expense_custom_field.location entity.1	2022-09-20 14:09:10.945031+05:30	2022-09-20 14:09:10.945075+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2548	LOCATION_ENTITY	Location Entity	Jeff's Jalopies	expense_custom_field.location entity.2	2022-09-20 14:09:10.945155+05:30	2022-09-20 14:09:10.945185+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2549	LOCATION_ENTITY	Location Entity	Dylan Sollfrank	expense_custom_field.location entity.3	2022-09-20 14:09:10.945253+05:30	2022-09-20 14:09:10.945281+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2550	LOCATION_ENTITY	Location Entity	Diego Rodriguez	expense_custom_field.location entity.4	2022-09-20 14:09:10.945349+05:30	2022-09-20 14:09:10.945376+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2551	LOCATION_ENTITY	Location Entity	Ashwinn	expense_custom_field.location entity.5	2022-09-20 14:09:10.945645+05:30	2022-09-20 14:09:10.945682+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2552	LOCATION_ENTITY	Location Entity	Geeta Kalapatapu	expense_custom_field.location entity.6	2022-09-20 14:09:10.94576+05:30	2022-09-20 14:09:10.945788+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2553	LOCATION_ENTITY	Location Entity	Travis Waldron	expense_custom_field.location entity.7	2022-09-20 14:09:10.945854+05:30	2022-09-20 14:09:10.945881+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2554	LOCATION_ENTITY	Location Entity	USA3	expense_custom_field.location entity.8	2022-09-20 14:09:10.945945+05:30	2022-09-20 14:09:10.945972+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
684	PROJECT	Project	Project 8	203316	2022-09-20 14:09:06.867492+05:30	2022-09-20 14:09:06.867576+05:30	1	t	\N	f	f
2555	LOCATION_ENTITY	Location Entity	Dukes Basketball Camp	expense_custom_field.location entity.9	2022-09-20 14:09:10.946037+05:30	2022-09-20 14:09:10.946064+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2556	LOCATION_ENTITY	Location Entity	Weiskopf Consulting	expense_custom_field.location entity.10	2022-09-20 14:09:10.946128+05:30	2022-09-20 14:09:10.946156+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2557	LOCATION_ENTITY	Location Entity	Mark Cho	expense_custom_field.location entity.11	2022-09-20 14:09:10.94622+05:30	2022-09-20 14:09:10.946247+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2558	LOCATION_ENTITY	Location Entity	Diego Rodriguez:Test Project	expense_custom_field.location entity.12	2022-09-20 14:09:10.946311+05:30	2022-09-20 14:09:10.946476+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2559	LOCATION_ENTITY	Location Entity	India	expense_custom_field.location entity.13	2022-09-20 14:09:10.946554+05:30	2022-09-20 14:09:10.946582+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2560	LOCATION_ENTITY	Location Entity	Pye's Cakes	expense_custom_field.location entity.14	2022-09-20 14:09:10.946646+05:30	2022-09-20 14:09:10.946673+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2561	LOCATION_ENTITY	Location Entity	Freeman Sporting Goods:55 Twin Lane	expense_custom_field.location entity.15	2022-09-20 14:09:10.94677+05:30	2022-09-20 14:09:10.946799+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2562	LOCATION_ENTITY	Location Entity	Shara Barnett:Barnett Design	expense_custom_field.location entity.16	2022-09-20 14:09:10.946868+05:30	2022-09-20 14:09:10.946897+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2563	LOCATION_ENTITY	Location Entity	Amy's Bird Sanctuary	expense_custom_field.location entity.17	2022-09-20 14:09:10.946965+05:30	2022-09-20 14:09:10.946994+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2564	LOCATION_ENTITY	Location Entity	Amy's Bird Sanctuary:Test Project	expense_custom_field.location entity.18	2022-09-20 14:09:10.947063+05:30	2022-09-20 14:09:10.947091+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2565	LOCATION_ENTITY	Location Entity	Gevelber Photography	expense_custom_field.location entity.19	2022-09-20 14:09:10.947165+05:30	2022-09-20 14:09:10.947195+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2566	LOCATION_ENTITY	Location Entity	Red Rock Diner	expense_custom_field.location entity.20	2022-09-20 14:09:10.947265+05:30	2022-09-20 14:09:10.947295+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2567	LOCATION_ENTITY	Location Entity	Cool Cars	expense_custom_field.location entity.21	2022-09-20 14:09:10.947513+05:30	2022-09-20 14:09:10.947546+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2568	LOCATION_ENTITY	Location Entity	Rago Travel Agency	expense_custom_field.location entity.22	2022-09-20 14:09:10.947625+05:30	2022-09-20 14:09:10.947652+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2569	LOCATION_ENTITY	Location Entity	Sravan BLR Customer	expense_custom_field.location entity.23	2022-09-20 14:09:10.947717+05:30	2022-09-20 14:09:10.947745+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2570	LOCATION_ENTITY	Location Entity	John Melton	expense_custom_field.location entity.24	2022-09-20 14:09:10.947809+05:30	2022-09-20 14:09:10.947836+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2571	LOCATION_ENTITY	Location Entity	USA1	expense_custom_field.location entity.25	2022-09-20 14:09:10.947901+05:30	2022-09-20 14:09:10.947928+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2572	LOCATION_ENTITY	Location Entity	Bill's Windsurf Shop	expense_custom_field.location entity.26	2022-09-20 14:09:10.947992+05:30	2022-09-20 14:09:10.94802+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2573	LOCATION_ENTITY	Location Entity	Paulsen Medical Supplies	expense_custom_field.location entity.27	2022-09-20 14:09:10.948084+05:30	2022-09-20 14:09:10.948111+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2574	LOCATION_ENTITY	Location Entity	Freeman Sporting Goods:0969 Ocean View Road	expense_custom_field.location entity.28	2022-09-20 14:09:10.948176+05:30	2022-09-20 14:09:10.948203+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2575	LOCATION_ENTITY	Location Entity	Kate Whelan	expense_custom_field.location entity.29	2022-09-20 14:09:10.948268+05:30	2022-09-20 14:09:10.948295+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2576	LOCATION_ENTITY	Location Entity	Freeman Sporting Goods	expense_custom_field.location entity.30	2022-09-20 14:09:10.948373+05:30	2022-09-20 14:09:10.948536+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2577	LOCATION_ENTITY	Location Entity	Shara Barnett	expense_custom_field.location entity.31	2022-09-20 14:09:10.948648+05:30	2022-09-20 14:09:10.948667+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
3100	MERCHANT	Merchant	Blob Johnson	852	2022-09-20 14:10:15.970071+05:30	2022-09-20 14:10:15.970199+05:30	1	\N	\N	f	f
2578	LOCATION_ENTITY	Location Entity	Rondonuwu Fruit and Vegi	expense_custom_field.location entity.32	2022-09-20 14:09:10.948717+05:30	2022-09-20 14:09:10.948739+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2579	LOCATION_ENTITY	Location Entity	Video Games by Dan	expense_custom_field.location entity.33	2022-09-20 14:09:10.948808+05:30	2022-09-20 14:09:10.948838+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2580	LOCATION_ENTITY	Location Entity	Sushi by Katsuyuki	expense_custom_field.location entity.34	2022-09-20 14:09:10.948902+05:30	2022-09-20 14:09:10.948913+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2581	LOCATION_ENTITY	Location Entity	USA2	expense_custom_field.location entity.35	2022-09-20 14:09:10.948964+05:30	2022-09-20 14:09:10.948981+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2582	LOCATION_ENTITY	Location Entity	Kookies by Kathy	expense_custom_field.location entity.36	2022-09-20 14:09:10.949035+05:30	2022-09-20 14:09:10.949059+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2583	LOCATION_ENTITY	Location Entity	Sonnenschein Family Store	expense_custom_field.location entity.37	2022-09-20 14:09:10.949119+05:30	2022-09-20 14:09:10.949141+05:30	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2584	CLASS	Class	goat	expense_custom_field.class.1	2022-09-20 14:09:10.963066+05:30	2022-09-20 14:09:10.963106+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
2585	CLASS	Class	Diego Rodriguez	expense_custom_field.class.2	2022-09-20 14:09:10.963175+05:30	2022-09-20 14:09:10.963203+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
2586	CLASS	Class	Dylan Sollfrank	expense_custom_field.class.3	2022-09-20 14:09:10.963386+05:30	2022-09-20 14:09:10.963414+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
2587	CLASS	Class	Rondonuwu Fruit and Vegi	expense_custom_field.class.4	2022-09-20 14:09:10.963476+05:30	2022-09-20 14:09:10.963515+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
2588	CLASS	Class	Bill's Windsurf Shop	expense_custom_field.class.5	2022-09-20 14:09:10.963601+05:30	2022-09-20 14:09:10.963639+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
3086	MERCHANT	Merchant	Tim Philip Masonry	852	2022-09-20 14:10:15.929809+05:30	2022-09-20 14:10:15.929843+05:30	1	\N	\N	f	f
2589	CLASS	Class	Kate Whelan	expense_custom_field.class.6	2022-09-20 14:09:10.964058+05:30	2022-09-20 14:09:10.964089+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
2590	CLASS	Class	Mark Cho	expense_custom_field.class.7	2022-09-20 14:09:10.96443+05:30	2022-09-20 14:09:10.96458+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
2591	CLASS	Class	Shara Barnett	expense_custom_field.class.8	2022-09-20 14:09:10.964777+05:30	2022-09-20 14:09:10.964799+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
2592	CLASS	Class	Shara Barnett:Barnett Design	expense_custom_field.class.9	2022-09-20 14:09:10.964976+05:30	2022-09-20 14:09:10.965004+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
2593	CLASS	Class	Kookies by Kathy	expense_custom_field.class.10	2022-09-20 14:09:10.965069+05:30	2022-09-20 14:09:10.965096+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
3099	MERCHANT	Merchant	Basket Case	852	2022-09-20 14:10:15.969982+05:30	2022-09-20 14:10:15.970011+05:30	1	\N	\N	f	f
2594	CLASS	Class	Weiskopf Consulting	expense_custom_field.class.11	2022-09-20 14:09:10.965161+05:30	2022-09-20 14:09:10.965188+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
2595	CLASS	Class	Red Rock Diner	expense_custom_field.class.12	2022-09-20 14:09:10.965264+05:30	2022-09-20 14:09:10.965399+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
2596	CLASS	Class	Freeman Sporting Goods:0969 Ocean View Road	expense_custom_field.class.13	2022-09-20 14:09:10.965475+05:30	2022-09-20 14:09:10.965502+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
2597	CLASS	Class	John Melton	expense_custom_field.class.14	2022-09-20 14:09:10.965567+05:30	2022-09-20 14:09:10.965594+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
2598	CLASS	Class	Dukes Basketball Camp	expense_custom_field.class.15	2022-09-20 14:09:10.965658+05:30	2022-09-20 14:09:10.965685+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
2599	CLASS	Class	Sonnenschein Family Store	expense_custom_field.class.16	2022-09-20 14:09:10.965749+05:30	2022-09-20 14:09:10.965776+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
2600	CLASS	Class	octane squad	expense_custom_field.class.17	2022-09-20 14:09:10.96584+05:30	2022-09-20 14:09:10.965867+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
2601	CLASS	Class	Video Games by Dan	expense_custom_field.class.18	2022-09-20 14:09:10.965931+05:30	2022-09-20 14:09:10.965959+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
2602	CLASS	Class	Jeff's Jalopies	expense_custom_field.class.19	2022-09-20 14:09:10.966023+05:30	2022-09-20 14:09:10.96605+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
2603	CLASS	Class	Wedding Planning by Whitney	expense_custom_field.class.20	2022-09-20 14:09:10.966114+05:30	2022-09-20 14:09:10.966142+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
2604	CLASS	Class	Pye's Cakes	expense_custom_field.class.21	2022-09-20 14:09:10.966206+05:30	2022-09-20 14:09:10.966233+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
2605	CLASS	Class	Freeman Sporting Goods	expense_custom_field.class.22	2022-09-20 14:09:10.966298+05:30	2022-09-20 14:09:10.966325+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
2606	CLASS	Class	wraith squad	expense_custom_field.class.23	2022-09-20 14:09:10.966513+05:30	2022-09-20 14:09:10.966544+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
2607	CLASS	Class	Rago Travel Agency	expense_custom_field.class.24	2022-09-20 14:09:10.966621+05:30	2022-09-20 14:09:10.966649+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
2608	CLASS	Class	Geeta Kalapatapu	expense_custom_field.class.25	2022-09-20 14:09:10.966714+05:30	2022-09-20 14:09:10.966741+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
2609	CLASS	Class	Freeman Sporting Goods:55 Twin Lane	expense_custom_field.class.26	2022-09-20 14:09:10.966805+05:30	2022-09-20 14:09:10.966832+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
2610	CLASS	Class	Travis Waldron	expense_custom_field.class.27	2022-09-20 14:09:10.966896+05:30	2022-09-20 14:09:10.966937+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
2611	CLASS	Class	Amy's Bird Sanctuary	expense_custom_field.class.28	2022-09-20 14:09:10.967006+05:30	2022-09-20 14:09:10.967035+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
2612	CLASS	Class	Sushi by Katsuyuki	expense_custom_field.class.29	2022-09-20 14:09:10.967104+05:30	2022-09-20 14:09:10.967133+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
2613	CLASS	Class	Cool Cars	expense_custom_field.class.30	2022-09-20 14:09:10.967202+05:30	2022-09-20 14:09:10.967231+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
2614	CLASS	Class	naruto uzumaki	expense_custom_field.class.31	2022-09-20 14:09:10.967404+05:30	2022-09-20 14:09:10.967445+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
2615	CLASS	Class	Paulsen Medical Supplies	expense_custom_field.class.32	2022-09-20 14:09:10.967513+05:30	2022-09-20 14:09:10.967541+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
2616	CLASS	Class	Gevelber Photography	expense_custom_field.class.33	2022-09-20 14:09:10.967605+05:30	2022-09-20 14:09:10.967633+05:30	1	\N	{"placeholder": "Select Class", "custom_field_id": 190717}	f	f
3101	MERCHANT	Merchant	Blooper Bloop	852	2022-09-20 14:10:15.970263+05:30	2022-09-20 14:10:15.970292+05:30	1	\N	\N	f	f
2617	USER_DIMENSION	User Dimension	Services	expense_custom_field.user dimension.1	2022-09-20 14:09:10.980758+05:30	2022-09-20 14:09:10.980797+05:30	1	\N	{"placeholder": "Select User Dimension", "custom_field_id": 174176}	f	f
2618	USER_DIMENSION	User Dimension	Sales	expense_custom_field.user dimension.2	2022-09-20 14:09:10.980866+05:30	2022-09-20 14:09:10.980894+05:30	1	\N	{"placeholder": "Select User Dimension", "custom_field_id": 174176}	f	f
2619	USER_DIMENSION	User Dimension	Marketing	expense_custom_field.user dimension.3	2022-09-20 14:09:10.98096+05:30	2022-09-20 14:09:10.980988+05:30	1	\N	{"placeholder": "Select User Dimension", "custom_field_id": 174176}	f	f
2620	USER_DIMENSION	User Dimension	Admin	expense_custom_field.user dimension.4	2022-09-20 14:09:10.981052+05:30	2022-09-20 14:09:10.98108+05:30	1	\N	{"placeholder": "Select User Dimension", "custom_field_id": 174176}	f	f
2621	USER_DIMENSION	User Dimension	IT	expense_custom_field.user dimension.5	2022-09-20 14:09:10.981144+05:30	2022-09-20 14:09:10.981171+05:30	1	\N	{"placeholder": "Select User Dimension", "custom_field_id": 174176}	f	f
2622	TEAM_2_POSTMAN	Team 2 Postman	Dukes Basketball Camp	expense_custom_field.team 2 postman.1	2022-09-20 14:09:10.992147+05:30	2022-09-20 14:09:10.992414+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2623	TEAM_2_POSTMAN	Team 2 Postman	Gevelber Photography	expense_custom_field.team 2 postman.2	2022-09-20 14:09:10.993352+05:30	2022-09-20 14:09:10.993408+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2624	TEAM_2_POSTMAN	Team 2 Postman	Geeta Kalapatapu	expense_custom_field.team 2 postman.3	2022-09-20 14:09:10.993564+05:30	2022-09-20 14:09:10.993635+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2625	TEAM_2_POSTMAN	Team 2 Postman	Bill's Windsurf Shop	expense_custom_field.team 2 postman.4	2022-09-20 14:09:10.993761+05:30	2022-09-20 14:09:10.993806+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2626	TEAM_2_POSTMAN	Team 2 Postman	Diego Rodriguez	expense_custom_field.team 2 postman.5	2022-09-20 14:09:10.993903+05:30	2022-09-20 14:09:10.993941+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2627	TEAM_2_POSTMAN	Team 2 Postman	Amy's Bird Sanctuary:Test Project	expense_custom_field.team 2 postman.6	2022-09-20 14:09:10.994057+05:30	2022-09-20 14:09:10.994101+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2628	TEAM_2_POSTMAN	Team 2 Postman	Dylan Sollfrank	expense_custom_field.team 2 postman.7	2022-09-20 14:09:10.994406+05:30	2022-09-20 14:09:10.994458+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2629	TEAM_2_POSTMAN	Team 2 Postman	Sravan BLR Customer	expense_custom_field.team 2 postman.8	2022-09-20 14:09:10.994547+05:30	2022-09-20 14:09:10.994577+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2630	TEAM_2_POSTMAN	Team 2 Postman	Kate Whelan	expense_custom_field.team 2 postman.9	2022-09-20 14:09:10.994662+05:30	2022-09-20 14:09:10.99471+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2713	TAX_GROUP	Tax Group	V1EJ6D8VGJ	tg45EVaI4yoO	2022-09-20 14:09:11.577033+05:30	2022-09-20 14:09:11.577082+05:30	1	\N	{"tax_rate": 0.18}	f	f
2631	TEAM_2_POSTMAN	Team 2 Postman	Coffee	expense_custom_field.team 2 postman.10	2022-09-20 14:09:10.994792+05:30	2022-09-20 14:09:10.994821+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2632	TEAM_2_POSTMAN	Team 2 Postman	Sushi by Katsuyuki	expense_custom_field.team 2 postman.11	2022-09-20 14:09:10.99489+05:30	2022-09-20 14:09:10.994919+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2633	TEAM_2_POSTMAN	Team 2 Postman	Freeman Sporting Goods:55 Twin Lane	expense_custom_field.team 2 postman.12	2022-09-20 14:09:10.99499+05:30	2022-09-20 14:09:10.995021+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2634	TEAM_2_POSTMAN	Team 2 Postman	Diego Rodriguez:Test Project	expense_custom_field.team 2 postman.13	2022-09-20 14:09:10.995543+05:30	2022-09-20 14:09:10.995585+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2635	TEAM_2_POSTMAN	Team 2 Postman	Chai	expense_custom_field.team 2 postman.14	2022-09-20 14:09:10.995665+05:30	2022-09-20 14:09:10.995692+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2636	TEAM_2_POSTMAN	Team 2 Postman	Cool Cars	expense_custom_field.team 2 postman.15	2022-09-20 14:09:10.995758+05:30	2022-09-20 14:09:10.995785+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2637	TEAM_2_POSTMAN	Team 2 Postman	Amy's Bird Sanctuary	expense_custom_field.team 2 postman.16	2022-09-20 14:09:10.99585+05:30	2022-09-20 14:09:10.995877+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2638	TEAM_2_POSTMAN	Team 2 Postman	Freeman Sporting Goods	expense_custom_field.team 2 postman.17	2022-09-20 14:09:10.995942+05:30	2022-09-20 14:09:10.995969+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2639	TEAM_2_POSTMAN	Team 2 Postman	Shara Barnett	expense_custom_field.team 2 postman.18	2022-09-20 14:09:10.996035+05:30	2022-09-20 14:09:10.996062+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2640	TEAM_2_POSTMAN	Team 2 Postman	Kookies by Kathy	expense_custom_field.team 2 postman.19	2022-09-20 14:09:10.996126+05:30	2022-09-20 14:09:10.996153+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2641	TEAM_2_POSTMAN	Team 2 Postman	Jeff's Jalopies	expense_custom_field.team 2 postman.20	2022-09-20 14:09:10.996217+05:30	2022-09-20 14:09:10.996244+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2642	TEAM_2_POSTMAN	Team 2 Postman	Red Rock Diner	expense_custom_field.team 2 postman.21	2022-09-20 14:09:10.996309+05:30	2022-09-20 14:09:10.996336+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2643	TEAM_2_POSTMAN	Team 2 Postman	Wedding Planning by Whitney	expense_custom_field.team 2 postman.22	2022-09-20 14:09:10.996537+05:30	2022-09-20 14:09:10.996566+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2644	TEAM_2_POSTMAN	Team 2 Postman	Sonnenschein Family Store	expense_custom_field.team 2 postman.23	2022-09-20 14:09:10.996631+05:30	2022-09-20 14:09:10.996658+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2645	TEAM_2_POSTMAN	Team 2 Postman	Shara Barnett:Barnett Design	expense_custom_field.team 2 postman.24	2022-09-20 14:09:10.996722+05:30	2022-09-20 14:09:10.99675+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2646	TEAM_2_POSTMAN	Team 2 Postman	Travis Waldron	expense_custom_field.team 2 postman.25	2022-09-20 14:09:10.996815+05:30	2022-09-20 14:09:10.996842+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2647	TEAM_2_POSTMAN	Team 2 Postman	Rondonuwu Fruit and Vegi	expense_custom_field.team 2 postman.26	2022-09-20 14:09:10.996907+05:30	2022-09-20 14:09:10.996934+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2648	TEAM_2_POSTMAN	Team 2 Postman	Ashwinn	expense_custom_field.team 2 postman.27	2022-09-20 14:09:10.996999+05:30	2022-09-20 14:09:10.997026+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2649	TEAM_2_POSTMAN	Team 2 Postman	Paulsen Medical Supplies	expense_custom_field.team 2 postman.28	2022-09-20 14:09:10.997091+05:30	2022-09-20 14:09:10.997118+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2650	TEAM_2_POSTMAN	Team 2 Postman	wraith squad	expense_custom_field.team 2 postman.29	2022-09-20 14:09:10.997183+05:30	2022-09-20 14:09:10.99721+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2688	CORPORATE_CARD	Corporate Card	American Express - 29578	bacce3rbqv5Veb	2022-09-20 14:09:11.194168+05:30	2022-09-20 14:09:11.194195+05:30	1	\N	{"cardholder_name": "Monica E. Geller-Bing's account"}	f	f
2651	TEAM_2_POSTMAN	Team 2 Postman	Weiskopf Consulting	expense_custom_field.team 2 postman.30	2022-09-20 14:09:10.997275+05:30	2022-09-20 14:09:10.997302+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2652	TEAM_2_POSTMAN	Team 2 Postman	octane squad	expense_custom_field.team 2 postman.31	2022-09-20 14:09:10.997483+05:30	2022-09-20 14:09:10.997513+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2653	TEAM_2_POSTMAN	Team 2 Postman	naruto uzumaki	expense_custom_field.team 2 postman.32	2022-09-20 14:09:10.997589+05:30	2022-09-20 14:09:10.997616+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2654	TEAM_2_POSTMAN	Team 2 Postman	Rago Travel Agency	expense_custom_field.team 2 postman.33	2022-09-20 14:09:10.997681+05:30	2022-09-20 14:09:10.997708+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2655	TEAM_2_POSTMAN	Team 2 Postman	Mark Cho	expense_custom_field.team 2 postman.34	2022-09-20 14:09:10.997773+05:30	2022-09-20 14:09:10.9978+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2656	TEAM_2_POSTMAN	Team 2 Postman	Freeman Sporting Goods:0969 Ocean View Road	expense_custom_field.team 2 postman.35	2022-09-20 14:09:10.997865+05:30	2022-09-20 14:09:10.997892+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2657	TEAM_2_POSTMAN	Team 2 Postman	Pye's Cakes	expense_custom_field.team 2 postman.36	2022-09-20 14:09:10.997957+05:30	2022-09-20 14:09:10.998009+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2658	TEAM_2_POSTMAN	Team 2 Postman	John Melton	expense_custom_field.team 2 postman.37	2022-09-20 14:09:10.998079+05:30	2022-09-20 14:09:10.998108+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2659	TEAM_2_POSTMAN	Team 2 Postman	Video Games by Dan	expense_custom_field.team 2 postman.38	2022-09-20 14:09:10.998183+05:30	2022-09-20 14:09:10.998211+05:30	1	\N	{"placeholder": "Select Team 2 Postman", "custom_field_id": 174994}	f	f
2660	TAX_GROUPS	Tax Groups	Exempt Sales @0.0%	expense_custom_field.tax groups.1	2022-09-20 14:09:11.012135+05:30	2022-09-20 14:09:11.012188+05:30	1	\N	{"placeholder": "Select Tax Groups", "custom_field_id": 195201}	f	f
2661	TAX_GROUPS	Tax Groups	MB - GST/RST on Purchases @12.0%	expense_custom_field.tax groups.2	2022-09-20 14:09:11.012267+05:30	2022-09-20 14:09:11.012297+05:30	1	\N	{"placeholder": "Select Tax Groups", "custom_field_id": 195201}	f	f
2662	TAX_GROUPS	Tax Groups	MB - GST/RST on Sales @12.0%	expense_custom_field.tax groups.3	2022-09-20 14:09:11.012367+05:30	2022-09-20 14:09:11.012398+05:30	1	\N	{"placeholder": "Select Tax Groups", "custom_field_id": 195201}	f	f
2663	TAX_GROUPS	Tax Groups	Oakdale Sales Tax @8.125%	expense_custom_field.tax groups.4	2022-09-20 14:09:11.012589+05:30	2022-09-20 14:09:11.012619+05:30	1	\N	{"placeholder": "Select Tax Groups", "custom_field_id": 195201}	f	f
2664	TAX_GROUPS	Tax Groups	Sales Tax on Imports @0.0%	expense_custom_field.tax groups.5	2022-09-20 14:09:11.012691+05:30	2022-09-20 14:09:11.01272+05:30	1	\N	{"placeholder": "Select Tax Groups", "custom_field_id": 195201}	f	f
2665	TAX_GROUPS	Tax Groups	Tax Exempt @0.0%	expense_custom_field.tax groups.6	2022-09-20 14:09:11.012792+05:30	2022-09-20 14:09:11.012822+05:30	1	\N	{"placeholder": "Select Tax Groups", "custom_field_id": 195201}	f	f
2666	TAX_GROUPS	Tax Groups	Tax on Consulting @8.25%	expense_custom_field.tax groups.7	2022-09-20 14:09:11.012892+05:30	2022-09-20 14:09:11.012921+05:30	1	\N	{"placeholder": "Select Tax Groups", "custom_field_id": 195201}	f	f
2667	TAX_GROUPS	Tax Groups	Tax on Goods @8.75%	expense_custom_field.tax groups.8	2022-09-20 14:09:11.012991+05:30	2022-09-20 14:09:11.013047+05:30	1	\N	{"placeholder": "Select Tax Groups", "custom_field_id": 195201}	f	f
2668	TAX_GROUPS	Tax Groups	Tax on Goodss @8.125%	expense_custom_field.tax groups.9	2022-09-20 14:09:11.013119+05:30	2022-09-20 14:09:11.013158+05:30	1	\N	{"placeholder": "Select Tax Groups", "custom_field_id": 195201}	f	f
2669	TAX_GROUPS	Tax Groups	Tax on Purchases @8.25%	expense_custom_field.tax groups.10	2022-09-20 14:09:11.013351+05:30	2022-09-20 14:09:11.013383+05:30	1	\N	{"placeholder": "Select Tax Groups", "custom_field_id": 195201}	f	f
2670	TAX_GROUPS	Tax Groups	tax for working @8.125%	expense_custom_field.tax groups.11	2022-09-20 14:09:11.013446+05:30	2022-09-20 14:09:11.013525+05:30	1	\N	{"placeholder": "Select Tax Groups", "custom_field_id": 195201}	f	f
2671	TAX_GROUPS	Tax Groups	tax for usa @8.125%	expense_custom_field.tax groups.12	2022-09-20 14:09:11.013631+05:30	2022-09-20 14:09:11.013678+05:30	1	\N	{"placeholder": "Select Tax Groups", "custom_field_id": 195201}	f	f
2672	TAX_GROUPS	Tax Groups	tax for usass @8.125%	expense_custom_field.tax groups.13	2022-09-20 14:09:11.014332+05:30	2022-09-20 14:09:11.014452+05:30	1	\N	{"placeholder": "Select Tax Groups", "custom_field_id": 195201}	f	f
2673	TAX_GROUPS	Tax Groups	tax for ussr @8.125%	expense_custom_field.tax groups.14	2022-09-20 14:09:11.014851+05:30	2022-09-20 14:09:11.014906+05:30	1	\N	{"placeholder": "Select Tax Groups", "custom_field_id": 195201}	f	f
2674	CORPORATE_CARD	Corporate Card	BANK OF INDIA - 219875	baccKkmmW4u1N4	2022-09-20 14:09:11.191689+05:30	2022-09-20 14:09:11.19173+05:30	1	\N	{"cardholder_name": null}	f	f
2675	CORPORATE_CARD	Corporate Card	Bank of America - 1319	baccJKh39lWI2L	2022-09-20 14:09:11.191804+05:30	2022-09-20 14:09:11.191833+05:30	1	\N	{"cardholder_name": null}	f	f
2676	CORPORATE_CARD	Corporate Card	BANK OF INDIA - 219874	baccxoXQr0p2kj	2022-09-20 14:09:11.191899+05:30	2022-09-20 14:09:11.191927+05:30	1	\N	{"cardholder_name": null}	f	f
2677	CORPORATE_CARD	Corporate Card	BANK OF INDIA - 219876	baccfiqYgkE8Db	2022-09-20 14:09:11.191992+05:30	2022-09-20 14:09:11.19202+05:30	1	\N	{"cardholder_name": null}	f	f
2678	CORPORATE_CARD	Corporate Card	American Express - 71149	baccaQY7KB7ogS	2022-09-20 14:09:11.192085+05:30	2022-09-20 14:09:11.192113+05:30	1	\N	{"cardholder_name": "Joseph Francis Tribbiani, Jr's account"}	f	f
2679	CORPORATE_CARD	Corporate Card	Bank of America - 8084	baccMCkKmsHV9X	2022-09-20 14:09:11.192178+05:30	2022-09-20 14:09:11.192205+05:30	1	\N	{"cardholder_name": null}	f	f
2731	TAX_GROUP	Tax Group	QZP8MCPJI0	tg7fDMpgFvdu	2022-09-20 14:09:11.591681+05:30	2022-09-20 14:09:11.591736+05:30	1	\N	{"tax_rate": 0.18}	f	f
2680	CORPORATE_CARD	Corporate Card	American Express - 30350	bacc3D6qx7cb4J	2022-09-20 14:09:11.19227+05:30	2022-09-20 14:09:11.192297+05:30	1	\N	{"cardholder_name": "Dr. Ross Eustace Geller's account"}	f	f
2681	CORPORATE_CARD	Corporate Card	American Express - 05556	baccuGmJMILiAr	2022-09-20 14:09:11.192703+05:30	2022-09-20 14:09:11.192787+05:30	1	\N	{"cardholder_name": "Phoebe Buffay-Hannigan's account"}	f	f
2682	CORPORATE_CARD	Corporate Card	American Express - 93634	bacc8nxvDzy9UB	2022-09-20 14:09:11.192881+05:30	2022-09-20 14:09:11.19291+05:30	1	\N	{"cardholder_name": "Joseph Francis Tribbiani, Jr's account"}	f	f
2683	CORPORATE_CARD	Corporate Card	American Express - 59344	baccRUz3T9WTG0	2022-09-20 14:09:11.19308+05:30	2022-09-20 14:09:11.193164+05:30	1	\N	{"cardholder_name": "Dr. Ross Eustace Geller's account"}	f	f
2684	CORPORATE_CARD	Corporate Card	American Express - 29676	baccJEu4LHANTj	2022-09-20 14:09:11.193557+05:30	2022-09-20 14:09:11.193607+05:30	1	\N	{"cardholder_name": "Monica E. Geller-Bing's account"}	f	f
2685	CORPORATE_CARD	Corporate Card	American Express - 97584	bacc3gPRo0BFI4	2022-09-20 14:09:11.193716+05:30	2022-09-20 14:09:11.193815+05:30	1	\N	{"cardholder_name": "Monica E. Geller-Bing's account"}	f	f
2686	CORPORATE_CARD	Corporate Card	American Express - 27881	baccT6Cr2LOoCU	2022-09-20 14:09:11.193978+05:30	2022-09-20 14:09:11.194008+05:30	1	\N	{"cardholder_name": "Monica E. Geller-Bing's account"}	f	f
2687	CORPORATE_CARD	Corporate Card	American Express - 40414	baccChwshlFsT5	2022-09-20 14:09:11.194076+05:30	2022-09-20 14:09:11.194104+05:30	1	\N	{"cardholder_name": "Monica E. Geller-Bing's account"}	f	f
2689	CORPORATE_CARD	Corporate Card	American Express - 93356	baccUhWPMgn4EB	2022-09-20 14:09:11.19426+05:30	2022-09-20 14:09:11.194288+05:30	1	\N	{"cardholder_name": "Dr. Ross Eustace Geller's account"}	f	f
2690	CORPORATE_CARD	Corporate Card	American Express - 64504	baccE0fU1LTqxm	2022-09-20 14:09:11.194353+05:30	2022-09-20 14:09:11.19439+05:30	1	\N	{"cardholder_name": "Joseph Francis Tribbiani, Jr's account"}	f	f
2691	CORPORATE_CARD	Corporate Card	American Express - 69115	baccKzSkYJjBQt	2022-09-20 14:09:11.194549+05:30	2022-09-20 14:09:11.194575+05:30	1	\N	{"cardholder_name": "Joseph Francis Tribbiani, Jr's account"}	f	f
2693	TAX_GROUP	Tax Group	LTFKCOG3FH	tg06xvLojY5h	2022-09-20 14:09:11.565609+05:30	2022-09-20 14:09:11.565649+05:30	1	\N	{"tax_rate": 0.18}	f	f
2694	TAX_GROUP	Tax Group	GST: NCF-AU @0.0%	tg09S3rMTTpo	2022-09-20 14:09:11.565774+05:30	2022-09-20 14:09:11.56581+05:30	1	\N	{"tax_rate": 0.0}	f	f
2695	TAX_GROUP	Tax Group	CGST	tg0fPRBFMZj7	2022-09-20 14:09:11.566245+05:30	2022-09-20 14:09:11.566304+05:30	1	\N	{"tax_rate": 0.5}	f	f
2696	TAX_GROUP	Tax Group	Z90LGUXCKD	tg0vUVJLRPvA	2022-09-20 14:09:11.566512+05:30	2022-09-20 14:09:11.567168+05:30	1	\N	{"tax_rate": 0.18}	f	f
2697	TAX_GROUP	Tax Group	R3BO0U5YZF	tg0vxs8Hz5F9	2022-09-20 14:09:11.567715+05:30	2022-09-20 14:09:11.567789+05:30	1	\N	{"tax_rate": 0.18}	f	f
2698	TAX_GROUP	Tax Group	PMNG0N8KSZ	tg1FdqJCybJs	2022-09-20 14:09:11.570109+05:30	2022-09-20 14:09:11.570194+05:30	1	\N	{"tax_rate": 0.18}	f	f
2699	TAX_GROUP	Tax Group	CA-Zero @0.0%	tg1KNSwtyeAW	2022-09-20 14:09:11.572056+05:30	2022-09-20 14:09:11.572106+05:30	1	\N	{"tax_rate": 0.0}	f	f
2700	TAX_GROUP	Tax Group	MTD7QH6N7D	tg1QK6lhb8J1	2022-09-20 14:09:11.572435+05:30	2022-09-20 14:09:11.572536+05:30	1	\N	{"tax_rate": 0.18}	f	f
2701	TAX_GROUP	Tax Group	QT8T97FF18	tg1Wr2J6mG2S	2022-09-20 14:09:11.572958+05:30	2022-09-20 14:09:11.573223+05:30	1	\N	{"tax_rate": 0.18}	f	f
2702	TAX_GROUP	Tax Group	RGLB5QES1M	tg1xpyImHPmA	2022-09-20 14:09:11.574082+05:30	2022-09-20 14:09:11.574216+05:30	1	\N	{"tax_rate": 0.18}	f	f
2703	TAX_GROUP	Tax Group	GV18OGZEWB	tg1ZsmGFRGSw	2022-09-20 14:09:11.574509+05:30	2022-09-20 14:09:11.574564+05:30	1	\N	{"tax_rate": 0.18}	f	f
2704	TAX_GROUP	Tax Group	WSTNCJ6Q5H	tg2bqtQzmNiO	2022-09-20 14:09:11.574976+05:30	2022-09-20 14:09:11.575011+05:30	1	\N	{"tax_rate": 0.18}	f	f
2705	TAX_GROUP	Tax Group	PST_CA_E @0.0%	tg2ecP3KC9Bk	2022-09-20 14:09:11.575101+05:30	2022-09-20 14:09:11.575133+05:30	1	\N	{"tax_rate": 0.0}	f	f
2706	TAX_GROUP	Tax Group	QVOZSLTNXZ	tg2lDhvY1epZ	2022-09-20 14:09:11.575583+05:30	2022-09-20 14:09:11.575921+05:30	1	\N	{"tax_rate": 0.18}	f	f
2707	TAX_GROUP	Tax Group	04DFQBACPE	tg30QAE0HLxw	2022-09-20 14:09:11.576059+05:30	2022-09-20 14:09:11.576105+05:30	1	\N	{"tax_rate": 0.18}	f	f
2708	TAX_GROUP	Tax Group	tax for xero @2.5%	tg38zIMqqDn3	2022-09-20 14:09:11.5763+05:30	2022-09-20 14:09:11.576323+05:30	1	\N	{"tax_rate": 0.03}	f	f
2709	TAX_GROUP	Tax Group	JHLK63ZZWB	tg3ArwZPL3it	2022-09-20 14:09:11.576398+05:30	2022-09-20 14:09:11.57649+05:30	1	\N	{"tax_rate": 0.18}	f	f
2710	TAX_GROUP	Tax Group	UK Tax @0.0%	tg3fLCqgcmCE	2022-09-20 14:09:11.576569+05:30	2022-09-20 14:09:11.576593+05:30	1	\N	{"tax_rate": 0.0}	f	f
2711	TAX_GROUP	Tax Group	VAT: UNDEF-GB @0.0%	tg3Luhktgf4N	2022-09-20 14:09:11.576672+05:30	2022-09-20 14:09:11.576701+05:30	1	\N	{"tax_rate": 0.0}	f	f
2714	TAX_GROUP	Tax Group	BNDNQCGL2A	tg49NLOzlAlX	2022-09-20 14:09:11.577202+05:30	2022-09-20 14:09:11.577244+05:30	1	\N	{"tax_rate": 0.18}	f	f
2715	TAX_GROUP	Tax Group	M20BG0G6TW	tg4MdV2zG6xY	2022-09-20 14:09:11.578266+05:30	2022-09-20 14:09:11.578334+05:30	1	\N	{"tax_rate": 0.18}	f	f
2716	TAX_GROUP	Tax Group	OEAN2S0661	tg4mhXQy2iSF	2022-09-20 14:09:11.579198+05:30	2022-09-20 14:09:11.579567+05:30	1	\N	{"tax_rate": 0.18}	f	f
2717	TAX_GROUP	Tax Group	XN7QJZBTGW	tg4UlWDpIpOz	2022-09-20 14:09:11.579801+05:30	2022-09-20 14:09:11.579961+05:30	1	\N	{"tax_rate": 0.18}	f	f
2718	TAX_GROUP	Tax Group	Tax on Goods @8.75%	tg4Zf3dJR6TA	2022-09-20 14:09:11.581067+05:30	2022-09-20 14:09:11.581192+05:30	1	\N	{"tax_rate": 0.09}	f	f
2719	TAX_GROUP	Tax Group	WWBU4JTK1W	tg4zTkLu4CGR	2022-09-20 14:09:11.582506+05:30	2022-09-20 14:09:11.582595+05:30	1	\N	{"tax_rate": 0.18}	f	f
2721	TAX_GROUP	Tax Group	HBKP7A0DNR	tg555KAYmC0B	2022-09-20 14:09:11.583118+05:30	2022-09-20 14:09:11.58317+05:30	1	\N	{"tax_rate": 0.18}	f	f
2722	TAX_GROUP	Tax Group	HOUPXN0V9X	tg5lJAlaYA8W	2022-09-20 14:09:11.583458+05:30	2022-09-20 14:09:11.583516+05:30	1	\N	{"tax_rate": 0.18}	f	f
2723	TAX_GROUP	Tax Group	EOHGT9QJO4	tg5MZxx4nAkU	2022-09-20 14:09:11.583643+05:30	2022-09-20 14:09:11.583686+05:30	1	\N	{"tax_rate": 0.18}	f	f
2724	TAX_GROUP	Tax Group	GST: TFS-AU @0.0%	tg5uf1kTpljU	2022-09-20 14:09:11.583804+05:30	2022-09-20 14:09:11.583845+05:30	1	\N	{"tax_rate": 0.0}	f	f
2726	TAX_GROUP	Tax Group	MB - GST/RST on Sales @12.0%	tg6rxcPps3Dd	2022-09-20 14:09:11.58412+05:30	2022-09-20 14:09:11.585432+05:30	1	\N	{"tax_rate": 0.12}	f	f
2727	TAX_GROUP	Tax Group	Out of scope @0%	tg6TnmXD9sUE	2022-09-20 14:09:11.586393+05:30	2022-09-20 14:09:11.586469+05:30	1	\N	{"tax_rate": 0.0}	f	f
2728	TAX_GROUP	Tax Group	62WRSSZKV3	tg6uJjoWWr5a	2022-09-20 14:09:11.586793+05:30	2022-09-20 14:09:11.586842+05:30	1	\N	{"tax_rate": 0.18}	f	f
2729	TAX_GROUP	Tax Group	8RJGQU3LBA	tg6VRu2QbZXW	2022-09-20 14:09:11.586963+05:30	2022-09-20 14:09:11.587003+05:30	1	\N	{"tax_rate": 0.18}	f	f
2730	TAX_GROUP	Tax Group	69W9JMEXIP	tg7AUo9qgugX	2022-09-20 14:09:11.587112+05:30	2022-09-20 14:09:11.587151+05:30	1	\N	{"tax_rate": 0.18}	f	f
2732	TAX_GROUP	Tax Group	M08GU5OX20	tg7IEw1ogNKf	2022-09-20 14:09:11.591841+05:30	2022-09-20 14:09:11.591875+05:30	1	\N	{"tax_rate": 0.18}	f	f
2733	TAX_GROUP	Tax Group	GST-free non-capital - 0%	tg7ig0JL47TA	2022-09-20 14:09:11.591963+05:30	2022-09-20 14:09:11.591995+05:30	1	\N	{"tax_rate": 0.28}	f	f
2734	TAX_GROUP	Tax Group	Pant Tax @0%	tg7JTybZgV72	2022-09-20 14:09:11.592078+05:30	2022-09-20 14:09:11.592109+05:30	1	\N	{"tax_rate": 0.0}	f	f
2735	TAX_GROUP	Tax Group	NVV6A35DEB	tg7MUaF3jn8g	2022-09-20 14:09:11.592181+05:30	2022-09-20 14:09:11.592204+05:30	1	\N	{"tax_rate": 0.18}	f	f
2736	TAX_GROUP	Tax Group	ERWLSCCF5Y	tg7nwnwdF4dT	2022-09-20 14:09:11.592283+05:30	2022-09-20 14:09:11.592313+05:30	1	\N	{"tax_rate": 0.18}	f	f
2738	TAX_GROUP	Tax Group	UNDEF-AU @0.0%	tg7TABrTPI9Y	2022-09-20 14:09:11.592493+05:30	2022-09-20 14:09:11.592522+05:30	1	\N	{"tax_rate": 0.0}	f	f
2739	TAX_GROUP	Tax Group	3TBA1Y8XTJ	tg82dF3hhe5n	2022-09-20 14:09:11.592597+05:30	2022-09-20 14:09:11.592627+05:30	1	\N	{"tax_rate": 0.18}	f	f
2740	TAX_GROUP	Tax Group	asdads	tg8H1IYs5tK1	2022-09-20 14:09:11.5927+05:30	2022-09-20 14:09:11.59273+05:30	1	\N	{"tax_rate": 0.98}	f	f
2741	TAX_GROUP	Tax Group	XNNLG4CWVK	tg8hMa98dhaY	2022-09-20 14:09:11.592798+05:30	2022-09-20 14:09:11.592821+05:30	1	\N	{"tax_rate": 0.18}	f	f
2742	TAX_GROUP	Tax Group	XEC9NORGDY	tg8KRs4k8dzZ	2022-09-20 14:09:11.625617+05:30	2022-09-20 14:09:11.625706+05:30	1	\N	{"tax_rate": 0.18}	f	f
2743	TAX_GROUP	Tax Group	GST on capital - 10%	tg8NsXbzhPL9	2022-09-20 14:09:11.625904+05:30	2022-09-20 14:09:11.625974+05:30	1	\N	{"tax_rate": 0.28}	f	f
2744	TAX_GROUP	Tax Group	G5HSJNY9V8	tg8u6LIgEveF	2022-09-20 14:09:11.626184+05:30	2022-09-20 14:09:11.626355+05:30	1	\N	{"tax_rate": 0.18}	f	f
2748	TAX_GROUP	Tax Group	13GI6S3UYN	tga0lMbZ6RBf	2022-09-20 14:09:11.632026+05:30	2022-09-20 14:09:11.632049+05:30	1	\N	{"tax_rate": 0.18}	f	f
2749	TAX_GROUP	Tax Group	AQB26CI4C2	tga8X5feRpon	2022-09-20 14:09:11.632113+05:30	2022-09-20 14:09:11.63215+05:30	1	\N	{"tax_rate": 0.18}	f	f
2750	TAX_GROUP	Tax Group	1PKB8P46QU	tga95PVTYDvs	2022-09-20 14:09:11.632329+05:30	2022-09-20 14:09:11.632354+05:30	1	\N	{"tax_rate": 0.18}	f	f
2752	TAX_GROUP	Tax Group	FDU2ZPCGV4	tgadQszc73ls	2022-09-20 14:09:11.632508+05:30	2022-09-20 14:09:11.632593+05:30	1	\N	{"tax_rate": 0.18}	f	f
3065	MERCHANT	Merchant	James Taylor	852	2022-09-20 14:10:15.859781+05:30	2022-09-20 14:10:15.85981+05:30	1	\N	\N	f	f
2753	TAX_GROUP	Tax Group	WRVEPSQLUO	tgaDUDX0wKfx	2022-09-20 14:09:11.632681+05:30	2022-09-20 14:09:11.632704+05:30	1	\N	{"tax_rate": 0.18}	f	f
2754	TAX_GROUP	Tax Group	QE0PQSDQPB	tgAfGyr9gLcC	2022-09-20 14:09:11.632777+05:30	2022-09-20 14:09:11.632807+05:30	1	\N	{"tax_rate": 0.18}	f	f
2755	TAX_GROUP	Tax Group	JVFYUUP52V	tgAGJvQftHOa	2022-09-20 14:09:11.632868+05:30	2022-09-20 14:09:11.63289+05:30	1	\N	{"tax_rate": 0.18}	f	f
2756	TAX_GROUP	Tax Group	6RTQSGGVBB	tgaitDrJ7HKX	2022-09-20 14:09:11.632953+05:30	2022-09-20 14:09:11.632973+05:30	1	\N	{"tax_rate": 0.18}	f	f
2757	TAX_GROUP	Tax Group	ABN: dfvdfvf @20.0%	tgaj9yDnx3V7	2022-09-20 14:09:11.633023+05:30	2022-09-20 14:09:11.633044+05:30	1	\N	{"tax_rate": 0.2}	f	f
2758	TAX_GROUP	Tax Group	SNB8I4896F	tgANllvJ4iN0	2022-09-20 14:09:11.633106+05:30	2022-09-20 14:09:11.633127+05:30	1	\N	{"tax_rate": 0.18}	f	f
2759	TAX_GROUP	Tax Group	GST: ADJ-AU @0.0%	tgArJ1XJSvQ1	2022-09-20 14:09:11.633197+05:30	2022-09-20 14:09:11.633218+05:30	1	\N	{"tax_rate": 0.0}	f	f
2760	TAX_GROUP	Tax Group	95FDDT0ADR	tgArL90u46SV	2022-09-20 14:09:11.633269+05:30	2022-09-20 14:09:11.63329+05:30	1	\N	{"tax_rate": 0.18}	f	f
2761	TAX_GROUP	Tax Group	9Q25F572X1	tgauWe29lsRy	2022-09-20 14:09:11.63335+05:30	2022-09-20 14:09:11.633372+05:30	1	\N	{"tax_rate": 0.18}	f	f
2762	TAX_GROUP	Tax Group	RCYUA4VYHK	tgb5nFjKsyl6	2022-09-20 14:09:11.633638+05:30	2022-09-20 14:09:11.633668+05:30	1	\N	{"tax_rate": 0.18}	f	f
2763	TAX_GROUP	Tax Group	Nilesh Tax @10%	tgB8tkI8kkOV	2022-09-20 14:09:11.633731+05:30	2022-09-20 14:09:11.633753+05:30	1	\N	{"tax_rate": 0.1}	f	f
2764	TAX_GROUP	Tax Group	DM7138IDE2	tgB8X2Wlujvd	2022-09-20 14:09:11.633823+05:30	2022-09-20 14:09:11.633852+05:30	1	\N	{"tax_rate": 0.18}	f	f
2765	TAX_GROUP	Tax Group	DWU8MKBQEV	tgb9lp7pgKro	2022-09-20 14:09:11.633941+05:30	2022-09-20 14:09:11.634+05:30	1	\N	{"tax_rate": 0.18}	f	f
2766	TAX_GROUP	Tax Group	9R407O18OU	tgbbjo87dXZh	2022-09-20 14:09:11.634073+05:30	2022-09-20 14:09:11.634106+05:30	1	\N	{"tax_rate": 0.18}	f	f
2767	TAX_GROUP	Tax Group	WUZT4BLA9Z	tgbCmfy69LBW	2022-09-20 14:09:11.634173+05:30	2022-09-20 14:09:11.634195+05:30	1	\N	{"tax_rate": 0.18}	f	f
2768	TAX_GROUP	Tax Group	747DS1JYZB	tgBDWcnUMBpx	2022-09-20 14:09:11.634418+05:30	2022-09-20 14:09:11.634442+05:30	1	\N	{"tax_rate": 0.18}	f	f
2769	TAX_GROUP	Tax Group	9GO0WXN6RN	tgBFrF9ipSCf	2022-09-20 14:09:11.634496+05:30	2022-09-20 14:09:11.634517+05:30	1	\N	{"tax_rate": 0.18}	f	f
2770	TAX_GROUP	Tax Group	X6T4RNW4II	tgBJW9eEDGUk	2022-09-20 14:09:11.634587+05:30	2022-09-20 14:09:11.634616+05:30	1	\N	{"tax_rate": 0.18}	f	f
2771	TAX_GROUP	Tax Group	AZMVYWZ7BW	tgBkiVZxAEj8	2022-09-20 14:09:11.634935+05:30	2022-09-20 14:09:11.634963+05:30	1	\N	{"tax_rate": 0.18}	f	f
2772	TAX_GROUP	Tax Group	EY28M1P22T	tgBQGdEkPr4j	2022-09-20 14:09:11.635039+05:30	2022-09-20 14:09:11.635062+05:30	1	\N	{"tax_rate": 0.18}	f	f
2773	TAX_GROUP	Tax Group	OYSLBGDVDT	tgBqKL4ngl1b	2022-09-20 14:09:11.635123+05:30	2022-09-20 14:09:11.635143+05:30	1	\N	{"tax_rate": 0.18}	f	f
2774	TAX_GROUP	Tax Group	XKZTXD6J07	tgbwF76xZ6Pb	2022-09-20 14:09:11.635194+05:30	2022-09-20 14:09:11.635215+05:30	1	\N	{"tax_rate": 0.18}	f	f
2775	TAX_GROUP	Tax Group	GST on capital @0%	tgbyQDWdp4HT	2022-09-20 14:09:11.635439+05:30	2022-09-20 14:09:11.63546+05:30	1	\N	{"tax_rate": 0.0}	f	f
2776	TAX_GROUP	Tax Group	OPUXX1NWJD	tgbzkdxqhtI1	2022-09-20 14:09:11.635515+05:30	2022-09-20 14:09:11.635536+05:30	1	\N	{"tax_rate": 0.18}	f	f
2777	TAX_GROUP	Tax Group	JYJHRR8B69	tgBZmftPpxAj	2022-09-20 14:09:11.635596+05:30	2022-09-20 14:09:11.635618+05:30	1	\N	{"tax_rate": 0.18}	f	f
2778	TAX_GROUP	Tax Group	GST on non-capital @10%	tgbzwu7Cka9M	2022-09-20 14:09:11.635679+05:30	2022-09-20 14:09:11.635701+05:30	1	\N	{"tax_rate": 0.1}	f	f
2779	TAX_GROUP	Tax Group	DEL4M6NRFW	tgC1lqWVovlW	2022-09-20 14:09:11.635761+05:30	2022-09-20 14:09:11.635782+05:30	1	\N	{"tax_rate": 0.18}	f	f
2780	TAX_GROUP	Tax Group	GST CA_0 @0.0%	tgc1rvIT6Bn1	2022-09-20 14:09:11.635844+05:30	2022-09-20 14:09:11.63587+05:30	1	\N	{"tax_rate": 0.0}	f	f
2781	TAX_GROUP	Tax Group	GST-free capital @0%	tgCfp1fUBdlX	2022-09-20 14:09:11.63593+05:30	2022-09-20 14:09:11.635949+05:30	1	\N	{"tax_rate": 0}	f	f
2782	TAX_GROUP	Tax Group	R92514U6N6	tgCuuwwIlvFm	2022-09-20 14:09:11.636001+05:30	2022-09-20 14:09:11.636022+05:30	1	\N	{"tax_rate": 0.18}	f	f
2783	TAX_GROUP	Tax Group	JDDDN0IM2E	tgcViap8gGOb	2022-09-20 14:09:11.636083+05:30	2022-09-20 14:09:11.636104+05:30	1	\N	{"tax_rate": 0.18}	f	f
2784	TAX_GROUP	Tax Group	OJ1ZB2W1AT	tgCW6oVxRh8S	2022-09-20 14:09:11.636164+05:30	2022-09-20 14:09:11.636184+05:30	1	\N	{"tax_rate": 0.18}	f	f
2785	TAX_GROUP	Tax Group	tax for sample @20.0%	tgD359VCOO4k	2022-09-20 14:09:11.636236+05:30	2022-09-20 14:09:11.636256+05:30	1	\N	{"tax_rate": 0.2}	f	f
2786	TAX_GROUP	Tax Group	LF3OR9B6UY	tgD4DZltfZm2	2022-09-20 14:09:11.636316+05:30	2022-09-20 14:09:11.636336+05:30	1	\N	{"tax_rate": 0.18}	f	f
2787	TAX_GROUP	Tax Group	ZSGKDU3OLB	tgd9jRwuVJ50	2022-09-20 14:09:11.636517+05:30	2022-09-20 14:09:11.636547+05:30	1	\N	{"tax_rate": 0.18}	f	f
3044	MERCHANT	Merchant	Labhvam	852	2022-09-20 14:10:15.786215+05:30	2022-09-20 14:10:15.786245+05:30	1	\N	\N	f	f
2788	TAX_GROUP	Tax Group	GST: UNDEF-AU @0.0%	tgdDcmqveXjC	2022-09-20 14:09:11.636612+05:30	2022-09-20 14:09:11.636633+05:30	1	\N	{"tax_rate": 0.0}	f	f
2789	TAX_GROUP	Tax Group	2WN3XRLS6H	tgddYlDJNOG9	2022-09-20 14:09:11.636704+05:30	2022-09-20 14:09:11.636724+05:30	1	\N	{"tax_rate": 0.18}	f	f
2790	TAX_GROUP	Tax Group	X4R0A458J3	tgdhExksqrBU	2022-09-20 14:09:11.636785+05:30	2022-09-20 14:09:11.636806+05:30	1	\N	{"tax_rate": 0.18}	f	f
2791	TAX_GROUP	Tax Group	Tax Exempt @0.0%	tgDHGmUj9YR8	2022-09-20 14:09:11.636866+05:30	2022-09-20 14:09:11.636887+05:30	1	\N	{"tax_rate": 0.0}	f	f
2792	TAX_GROUP	Tax Group	WGGUO7Z1SM	tgDHZqtOy6SU	2022-09-20 14:09:11.652543+05:30	2022-09-20 14:09:11.652583+05:30	1	\N	{"tax_rate": 0.18}	f	f
2793	TAX_GROUP	Tax Group	GST on non-capital @0%	tgdIMfh7iBOY	2022-09-20 14:09:11.652663+05:30	2022-09-20 14:09:11.652684+05:30	1	\N	{"tax_rate": 0.0}	f	f
2794	TAX_GROUP	Tax Group	LOITUJ2M1M	tgdIrsy8qgoa	2022-09-20 14:09:11.652744+05:30	2022-09-20 14:09:11.652764+05:30	1	\N	{"tax_rate": 0.18}	f	f
2795	TAX_GROUP	Tax Group	tax for jadu @20.0%	tgDiZoAy3aEI	2022-09-20 14:09:11.652823+05:30	2022-09-20 14:09:11.652846+05:30	1	\N	{"tax_rate": 0.2}	f	f
2796	TAX_GROUP	Tax Group	JVRYCPUK0F	tgdkgz4vv1Vl	2022-09-20 14:09:11.652916+05:30	2022-09-20 14:09:11.652936+05:30	1	\N	{"tax_rate": 0.18}	f	f
2797	TAX_GROUP	Tax Group	P9T0IITI3Q	tgdLysSnSLox	2022-09-20 14:09:11.652986+05:30	2022-09-20 14:09:11.653008+05:30	1	\N	{"tax_rate": 0.18}	f	f
2798	TAX_GROUP	Tax Group	VL45IRZHOK	tgdVMTXRNYu4	2022-09-20 14:09:11.653079+05:30	2022-09-20 14:09:11.6531+05:30	1	\N	{"tax_rate": 0.18}	f	f
2799	TAX_GROUP	Tax Group	RYHQGEPACZ	tgEAoIczkucD	2022-09-20 14:09:11.653159+05:30	2022-09-20 14:09:11.653179+05:30	1	\N	{"tax_rate": 0.18}	f	f
2800	TAX_GROUP	Tax Group	F0YGCWO5PP	tgEnkccvnY4e	2022-09-20 14:09:11.65323+05:30	2022-09-20 14:09:11.653251+05:30	1	\N	{"tax_rate": 0.18}	f	f
2801	TAX_GROUP	Tax Group	GST-free non-capital @0%	tgEru6wFHTM1	2022-09-20 14:09:11.653311+05:30	2022-09-20 14:09:11.653331+05:30	1	\N	{"tax_rate": 0}	f	f
2802	TAX_GROUP	Tax Group	NXPD1U8GHJ	tgERw1lWZaah	2022-09-20 14:09:11.653524+05:30	2022-09-20 14:09:11.653557+05:30	1	\N	{"tax_rate": 0.18}	f	f
2803	TAX_GROUP	Tax Group	VAT: Wow Tax @10.0%	tgEvaHjrKvx0	2022-09-20 14:09:11.653634+05:30	2022-09-20 14:09:11.653667+05:30	1	\N	{"tax_rate": 0.1}	f	f
2804	TAX_GROUP	Tax Group	560RKMO5QW	tgEYHASLyE0E	2022-09-20 14:09:11.653744+05:30	2022-09-20 14:09:11.653773+05:30	1	\N	{"tax_rate": 0.18}	f	f
2805	TAX_GROUP	Tax Group	GST: NA-AU @0.0%	tgf07hNu2f1L	2022-09-20 14:09:11.653847+05:30	2022-09-20 14:09:11.653878+05:30	1	\N	{"tax_rate": 0.0}	f	f
2806	TAX_GROUP	Tax Group	RHTSGJD4CV	tgf3cJ2q7Nqu	2022-09-20 14:09:11.653953+05:30	2022-09-20 14:09:11.653983+05:30	1	\N	{"tax_rate": 0.18}	f	f
2807	TAX_GROUP	Tax Group	CM556CRMO4	tgF7aZMGwdwa	2022-09-20 14:09:11.654064+05:30	2022-09-20 14:09:11.65409+05:30	1	\N	{"tax_rate": 0.18}	f	f
2808	TAX_GROUP	Tax Group	Y7ALNUN1XP	tgF9CJBTx6P9	2022-09-20 14:09:11.654175+05:30	2022-09-20 14:09:11.654385+05:30	1	\N	{"tax_rate": 0.18}	f	f
2809	TAX_GROUP	Tax Group	GST/HST: GST CA_5 @5.0%	tgFB3d6A5Nkf	2022-09-20 14:09:11.654473+05:30	2022-09-20 14:09:11.654496+05:30	1	\N	{"tax_rate": 0.05}	f	f
2810	TAX_GROUP	Tax Group	PZTO6DMVX2	tgFcheI45FJW	2022-09-20 14:09:11.654609+05:30	2022-09-20 14:09:11.654641+05:30	1	\N	{"tax_rate": 0.18}	f	f
2811	TAX_GROUP	Tax Group	NA-AU @0.0%	tgfMjmXkDsTx	2022-09-20 14:09:11.654708+05:30	2022-09-20 14:09:11.65472+05:30	1	\N	{"tax_rate": 0.0}	f	f
2812	TAX_GROUP	Tax Group	GST: EXPS-AU @0.0%	tgFQkkQOPT8i	2022-09-20 14:09:11.654782+05:30	2022-09-20 14:09:11.654805+05:30	1	\N	{"tax_rate": 0.0}	f	f
2813	TAX_GROUP	Tax Group	QXWLZB6RGO	tgfuGOalhfh1	2022-09-20 14:09:11.654878+05:30	2022-09-20 14:09:11.654909+05:30	1	\N	{"tax_rate": 0.18}	f	f
2814	TAX_GROUP	Tax Group	CPF-AU @0.0%	tgfZhOK0QWKu	2022-09-20 14:09:11.654982+05:30	2022-09-20 14:09:11.655005+05:30	1	\N	{"tax_rate": 0.0}	f	f
2815	TAX_GROUP	Tax Group	GST: NCI-AU @0.0%	tgG1mnAzZEit	2022-09-20 14:09:11.655076+05:30	2022-09-20 14:09:11.655107+05:30	1	\N	{"tax_rate": 0.0}	f	f
2816	TAX_GROUP	Tax Group	ZDM9M85NEK	tgg35A74tQRN	2022-09-20 14:09:11.655302+05:30	2022-09-20 14:09:11.655343+05:30	1	\N	{"tax_rate": 0.18}	f	f
2817	TAX_GROUP	Tax Group	MGCYQRWOJ8	tggb3nrVbdnw	2022-09-20 14:09:11.655417+05:30	2022-09-20 14:09:11.655438+05:30	1	\N	{"tax_rate": 0.18}	f	f
2818	TAX_GROUP	Tax Group	2CSL18LRX5	tgGE1ZWX2cgF	2022-09-20 14:09:11.655508+05:30	2022-09-20 14:09:11.655539+05:30	1	\N	{"tax_rate": 0.18}	f	f
2819	TAX_GROUP	Tax Group	XZXC2AN5UM	tgGedy1BnUMN	2022-09-20 14:09:11.655613+05:30	2022-09-20 14:09:11.655642+05:30	1	\N	{"tax_rate": 0.18}	f	f
2820	TAX_GROUP	Tax Group	WET: WET-AU @29.0%	tggmh4xFPIrY	2022-09-20 14:09:11.655726+05:30	2022-09-20 14:09:11.655756+05:30	1	\N	{"tax_rate": 0.29}	f	f
2821	TAX_GROUP	Tax Group	5VD52OUE8G	tgGMJFyqFBD0	2022-09-20 14:09:11.655821+05:30	2022-09-20 14:09:11.655841+05:30	1	\N	{"tax_rate": 0.18}	f	f
2823	TAX_GROUP	Tax Group	WQAYU3EVN9	tggps3ozYWXc	2022-09-20 14:09:11.656015+05:30	2022-09-20 14:09:11.656035+05:30	1	\N	{"tax_rate": 0.18}	f	f
2824	TAX_GROUP	Tax Group	GST CA_E @0.0%	tggQgp1T8mNX	2022-09-20 14:09:11.656156+05:30	2022-09-20 14:09:11.656311+05:30	1	\N	{"tax_rate": 0.0}	f	f
2825	TAX_GROUP	Tax Group	GST-free capital - 0%	tggu76WXIdjY	2022-09-20 14:09:11.656416+05:30	2022-09-20 14:09:11.656436+05:30	1	\N	{"tax_rate": 0.28}	f	f
679	PROJECT	Project	Project 3	203311	2022-09-20 14:09:06.848527+05:30	2022-09-20 14:09:06.848647+05:30	1	t	\N	f	f
2826	TAX_GROUP	Tax Group	M0P4RTHRRA	tgh43w8fzs1b	2022-09-20 14:09:11.656508+05:30	2022-09-20 14:09:11.656538+05:30	1	\N	{"tax_rate": 0.18}	f	f
2827	TAX_GROUP	Tax Group	GST: CPI-AU @0.0%	tgHbN222yK8n	2022-09-20 14:09:11.656602+05:30	2022-09-20 14:09:11.656624+05:30	1	\N	{"tax_rate": 0.0}	f	f
2828	TAX_GROUP	Tax Group	FYW3N2Z4G1	tgHiZcokwwZX	2022-09-20 14:09:11.656709+05:30	2022-09-20 14:09:11.656739+05:30	1	\N	{"tax_rate": 0.18}	f	f
2829	TAX_GROUP	Tax Group	GSTv21	tghOBz9yODLz	2022-09-20 14:09:11.656813+05:30	2022-09-20 14:09:11.656843+05:30	1	\N	{"tax_rate": 0.18}	f	f
2830	TAX_GROUP	Tax Group	tax for zero @0.0%	tgHOHGJBB9Oi	2022-09-20 14:09:11.656913+05:30	2022-09-20 14:09:11.656932+05:30	1	\N	{"tax_rate": 0.0}	f	f
2831	TAX_GROUP	Tax Group	T5G8M4IVT8	tgHsUgpvwEAv	2022-09-20 14:09:11.656995+05:30	2022-09-20 14:09:11.657018+05:30	1	\N	{"tax_rate": 0.18}	f	f
2832	TAX_GROUP	Tax Group	GLBTYBKH0W	tgHUR0p5j9MU	2022-09-20 14:09:11.657101+05:30	2022-09-20 14:09:11.657138+05:30	1	\N	{"tax_rate": 0.18}	f	f
2833	TAX_GROUP	Tax Group	Q230CP6HS8	tghVa6A2bxhj	2022-09-20 14:09:11.65733+05:30	2022-09-20 14:09:11.657362+05:30	1	\N	{"tax_rate": 0.18}	f	f
178	CATEGORY	Category	Legal	135913	2022-09-20 14:09:03.451678+05:30	2022-09-20 14:09:03.451707+05:30	1	t	\N	f	f
2835	TAX_GROUP	Tax Group	tax for ten @10.0%	tghYeIKavACw	2022-09-20 14:09:11.657514+05:30	2022-09-20 14:09:11.657526+05:30	1	\N	{"tax_rate": 0.1}	f	f
2836	TAX_GROUP	Tax Group	Exempt Sales @0.0%	tghz8Mq9SXTg	2022-09-20 14:09:11.657585+05:30	2022-09-20 14:09:11.657618+05:30	1	\N	{"tax_rate": 0.0}	f	f
2837	TAX_GROUP	Tax Group	M75YLYFLX2	tgIbiM63m7mV	2022-09-20 14:09:11.657739+05:30	2022-09-20 14:09:11.657769+05:30	1	\N	{"tax_rate": 0.18}	f	f
2838	TAX_GROUP	Tax Group	D1A81KCH82	tgIdDHOoKVzm	2022-09-20 14:09:11.65784+05:30	2022-09-20 14:09:11.657875+05:30	1	\N	{"tax_rate": 0.18}	f	f
2839	TAX_GROUP	Tax Group	RBJU6PV6UZ	tgIIYAOtOZ8o	2022-09-20 14:09:11.658003+05:30	2022-09-20 14:09:11.658025+05:30	1	\N	{"tax_rate": 0.18}	f	f
2841	TAX_GROUP	Tax Group	Q17J4DV6PY	tgiuRUp65soc	2022-09-20 14:09:11.658285+05:30	2022-09-20 14:09:11.659648+05:30	1	\N	{"tax_rate": 0.18}	f	f
2842	TAX_GROUP	Tax Group	CA-PST-AB @0.0%	tgiYnjwl2RtN	2022-09-20 14:09:11.672814+05:30	2022-09-20 14:09:11.672843+05:30	1	\N	{"tax_rate": 0.0}	f	f
2843	TAX_GROUP	Tax Group	GST: ITS-AU @0.0%	tgIyxnneqKm4	2022-09-20 14:09:11.672896+05:30	2022-09-20 14:09:11.672916+05:30	1	\N	{"tax_rate": 0.0}	f	f
2844	TAX_GROUP	Tax Group	QDJ8J2CPWA	tgizQ5b2qmlO	2022-09-20 14:09:11.672976+05:30	2022-09-20 14:09:11.672997+05:30	1	\N	{"tax_rate": 0.18}	f	f
2845	TAX_GROUP	Tax Group	GST: NCT-AU @10.0%	tgj97Eu6lEE3	2022-09-20 14:09:11.673059+05:30	2022-09-20 14:09:11.673079+05:30	1	\N	{"tax_rate": 0.1}	f	f
2846	TAX_GROUP	Tax Group	09ZKNVZ4O6	tgjAsjDeXCpN	2022-09-20 14:09:11.67314+05:30	2022-09-20 14:09:11.67316+05:30	1	\N	{"tax_rate": 0.18}	f	f
2847	TAX_GROUP	Tax Group	NCI-AU @0.0%	tgJD4Xo7hCep	2022-09-20 14:09:11.673221+05:30	2022-09-20 14:09:11.673241+05:30	1	\N	{"tax_rate": 0.0}	f	f
2848	TAX_GROUP	Tax Group	HTR8W6D3JR	tgjFfmEfMnki	2022-09-20 14:09:11.673302+05:30	2022-09-20 14:09:11.673322+05:30	1	\N	{"tax_rate": 0.18}	f	f
2849	TAX_GROUP	Tax Group	RMLZWIV6W7	tgJkpUDaCB6c	2022-09-20 14:09:11.673374+05:30	2022-09-20 14:09:11.673546+05:30	1	\N	{"tax_rate": 0.18}	f	f
2850	TAX_GROUP	Tax Group	USD4J624GO	tgjodMdR3Ag2	2022-09-20 14:09:11.673736+05:30	2022-09-20 14:09:11.673763+05:30	1	\N	{"tax_rate": 0.18}	f	f
2851	TAX_GROUP	Tax Group	PST_AB_0 @0.0%	tgjtVTJhrY3p	2022-09-20 14:09:11.673815+05:30	2022-09-20 14:09:11.673834+05:30	1	\N	{"tax_rate": 0.0}	f	f
2852	TAX_GROUP	Tax Group	T5AOOEOIMJ	tgjYXrePWshl	2022-09-20 14:09:11.673887+05:30	2022-09-20 14:09:11.673898+05:30	1	\N	{"tax_rate": 0.18}	f	f
2853	TAX_GROUP	Tax Group	ADJ-AU @0.0%	tgjzLEqLJLru	2022-09-20 14:09:11.673949+05:30	2022-09-20 14:09:11.67397+05:30	1	\N	{"tax_rate": 0.0}	f	f
2854	TAX_GROUP	Tax Group	4CF762Q721	tgk3oVtid3iD	2022-09-20 14:09:11.674031+05:30	2022-09-20 14:09:11.674052+05:30	1	\N	{"tax_rate": 0.18}	f	f
2855	TAX_GROUP	Tax Group	27Z4X2C201	tgKjEijcJFBE	2022-09-20 14:09:11.674113+05:30	2022-09-20 14:09:11.674133+05:30	1	\N	{"tax_rate": 0.18}	f	f
2856	TAX_GROUP	Tax Group	DJJWB6F4HM	tgKNmUyduTjf	2022-09-20 14:09:11.674185+05:30	2022-09-20 14:09:11.674204+05:30	1	\N	{"tax_rate": 0.18}	f	f
2858	TAX_GROUP	Tax Group	Z9EDD2VZC3	tgKSmIhciv9X	2022-09-20 14:09:11.674456+05:30	2022-09-20 14:09:11.674487+05:30	1	\N	{"tax_rate": 0.18}	f	f
2859	TAX_GROUP	Tax Group	BEOCQYS8EN	tgKwbHu63m6h	2022-09-20 14:09:11.674558+05:30	2022-09-20 14:09:11.674585+05:30	1	\N	{"tax_rate": 0.18}	f	f
2860	TAX_GROUP	Tax Group	VPJJOTDBCR	tgl4w9N3rm96	2022-09-20 14:09:11.674648+05:30	2022-09-20 14:09:11.674679+05:30	1	\N	{"tax_rate": 0.18}	f	f
2861	TAX_GROUP	Tax Group	LQEK36KCCF	tgL8ZiWvtrdS	2022-09-20 14:09:11.674778+05:30	2022-09-20 14:09:11.674808+05:30	1	\N	{"tax_rate": 0.18}	f	f
2862	TAX_GROUP	Tax Group	8ZUVNA95N1	tglCpwEHWoSk	2022-09-20 14:09:11.674916+05:30	2022-09-20 14:09:11.674944+05:30	1	\N	{"tax_rate": 0.18}	f	f
2863	TAX_GROUP	Tax Group	YO63CHLCBF	tglCtjyXrqTs	2022-09-20 14:09:11.674999+05:30	2022-09-20 14:09:11.67502+05:30	1	\N	{"tax_rate": 0.18}	f	f
2864	TAX_GROUP	Tax Group	R6KJ5YA4U9	tgLftvQ4yM0m	2022-09-20 14:09:11.675091+05:30	2022-09-20 14:09:11.675116+05:30	1	\N	{"tax_rate": 0.18}	f	f
2865	TAX_GROUP	Tax Group	GST on non-capital - 10%	tgLgjZDkBHOX	2022-09-20 14:09:11.675177+05:30	2022-09-20 14:09:11.675575+05:30	1	\N	{"tax_rate": 0.28}	f	f
2866	TAX_GROUP	Tax Group	O4Z369SVSU	tgLhjywOOpvH	2022-09-20 14:09:11.6758+05:30	2022-09-20 14:09:11.675834+05:30	1	\N	{"tax_rate": 0.18}	f	f
2867	TAX_GROUP	Tax Group	UX47SL7LOE	tgLHqwTlJ7cv	2022-09-20 14:09:11.675939+05:30	2022-09-20 14:09:11.675965+05:30	1	\N	{"tax_rate": 0.18}	f	f
2868	TAX_GROUP	Tax Group	GSTv2	tglItKJPWBfD	2022-09-20 14:09:11.676064+05:30	2022-09-20 14:09:11.676093+05:30	1	\N	{"tax_rate": 0.18}	f	f
2870	TAX_GROUP	Tax Group	611ZFAT5SM	tgLMpEVQmvzR	2022-09-20 14:09:11.676368+05:30	2022-09-20 14:09:11.676396+05:30	1	\N	{"tax_rate": 0.18}	f	f
2871	TAX_GROUP	Tax Group	Nilesh Tax @0%	tglmrXAQ8A5f	2022-09-20 14:09:11.676458+05:30	2022-09-20 14:09:11.67648+05:30	1	\N	{"tax_rate": 0.0}	f	f
2872	TAX_GROUP	Tax Group	9SI9Y9A036	tglnSdoifDoA	2022-09-20 14:09:11.676712+05:30	2022-09-20 14:09:11.676814+05:30	1	\N	{"tax_rate": 0.18}	f	f
2874	TAX_GROUP	Tax Group	OW43OS7WUO	tgLYWgsbLTpG	2022-09-20 14:09:11.676991+05:30	2022-09-20 14:09:11.67703+05:30	1	\N	{"tax_rate": 0.18}	f	f
2876	TAX_GROUP	Tax Group	CD5C1P0EBC	tgmANuJ1Lyyw	2022-09-20 14:09:11.677346+05:30	2022-09-20 14:09:11.677361+05:30	1	\N	{"tax_rate": 0.18}	f	f
2877	TAX_GROUP	Tax Group	5JHCVQD5SS	tgmEH8tzx7Fs	2022-09-20 14:09:11.677415+05:30	2022-09-20 14:09:11.677436+05:30	1	\N	{"tax_rate": 0.18}	f	f
2878	TAX_GROUP	Tax Group	03QBRUQL9Y	tgMJPwgwqLjl	2022-09-20 14:09:11.677732+05:30	2022-09-20 14:09:11.677764+05:30	1	\N	{"tax_rate": 0.18}	f	f
2879	TAX_GROUP	Tax Group	LCU8INQONN	tgMMC9y7yZLa	2022-09-20 14:09:11.677841+05:30	2022-09-20 14:09:11.677864+05:30	1	\N	{"tax_rate": 0.18}	f	f
2880	TAX_GROUP	Tax Group	CA-S-ON @0.0%	tgMn3pe1xFXO	2022-09-20 14:09:11.677928+05:30	2022-09-20 14:09:11.678316+05:30	1	\N	{"tax_rate": 0.0}	f	f
2881	TAX_GROUP	Tax Group	DWK2H94RM7	tgMslNJflABK	2022-09-20 14:09:11.678522+05:30	2022-09-20 14:09:11.678542+05:30	1	\N	{"tax_rate": 0.18}	f	f
2882	TAX_GROUP	Tax Group	WFRIUTX9C7	tgMu6kwxCgQ5	2022-09-20 14:09:11.678663+05:30	2022-09-20 14:09:11.67869+05:30	1	\N	{"tax_rate": 0.18}	f	f
2883	TAX_GROUP	Tax Group	6OJKRIJ9CD	tgmyCZ1JPg4G	2022-09-20 14:09:11.678745+05:30	2022-09-20 14:09:11.678802+05:30	1	\N	{"tax_rate": 0.18}	f	f
2885	TAX_GROUP	Tax Group	County: New York County @1.5%	tgn16RsBIa8O	2022-09-20 14:09:11.678974+05:30	2022-09-20 14:09:11.678995+05:30	1	\N	{"tax_rate": 0.01}	f	f
2886	TAX_GROUP	Tax Group	M8MES6DZKB	tgn18EUCd2TJ	2022-09-20 14:09:11.679057+05:30	2022-09-20 14:09:11.679077+05:30	1	\N	{"tax_rate": 0.18}	f	f
2887	TAX_GROUP	Tax Group	UTJEMXABWZ	tgN1c7PcZnTf	2022-09-20 14:09:11.679163+05:30	2022-09-20 14:09:11.679183+05:30	1	\N	{"tax_rate": 0.18}	f	f
2888	TAX_GROUP	Tax Group	6HEKYZATT2	tgN2DNgkzL1Q	2022-09-20 14:09:11.679263+05:30	2022-09-20 14:09:11.679283+05:30	1	\N	{"tax_rate": 0.18}	f	f
2889	TAX_GROUP	Tax Group	VACMTQNMYJ	tgNaVPIVhRk7	2022-09-20 14:09:11.679365+05:30	2022-09-20 14:09:11.680773+05:30	1	\N	{"tax_rate": 0.18}	f	f
2890	TAX_GROUP	Tax Group	VAT	tgnci8BWh2e2	2022-09-20 14:09:11.68124+05:30	2022-09-20 14:09:11.681428+05:30	1	\N	{"tax_rate": 0.1}	f	f
2891	TAX_GROUP	Tax Group	PO4UXUPB2Z	tgNDXVEuaGj4	2022-09-20 14:09:11.68155+05:30	2022-09-20 14:09:11.681577+05:30	1	\N	{"tax_rate": 0.18}	f	f
2892	TAX_GROUP	Tax Group	1A8A84WBA2	tgnGUH2NVrEA	2022-09-20 14:09:11.972666+05:30	2022-09-20 14:09:11.972784+05:30	1	\N	{"tax_rate": 0.18}	f	f
2894	TAX_GROUP	Tax Group	I4XUSD23KB	tgnvrN8trjBP	2022-09-20 14:09:11.973165+05:30	2022-09-20 14:09:11.973383+05:30	1	\N	{"tax_rate": 0.18}	f	f
2895	TAX_GROUP	Tax Group	TFS-AU @0.0%	tgO2rqAAcZTd	2022-09-20 14:09:11.973581+05:30	2022-09-20 14:09:11.973624+05:30	1	\N	{"tax_rate": 0.0}	f	f
2896	TAX_GROUP	Tax Group	GST: CPF-AU @0.0%	tgO8oQwXP01L	2022-09-20 14:09:11.973704+05:30	2022-09-20 14:09:11.973778+05:30	1	\N	{"tax_rate": 0.0}	f	f
2897	TAX_GROUP	Tax Group	Q5OGEJBTKM	tgoAmASNRgzk	2022-09-20 14:09:11.973874+05:30	2022-09-20 14:09:11.973904+05:30	1	\N	{"tax_rate": 0.18}	f	f
2898	TAX_GROUP	Tax Group	DSA93VPG9K	tgoExVlpnnbM	2022-09-20 14:09:11.973988+05:30	2022-09-20 14:09:11.974109+05:30	1	\N	{"tax_rate": 0.18}	f	f
2899	TAX_GROUP	Tax Group	EXPS-AU @0.0%	tgoGDuG6OMEa	2022-09-20 14:09:11.974208+05:30	2022-09-20 14:09:11.974239+05:30	1	\N	{"tax_rate": 0.0}	f	f
2900	TAX_GROUP	Tax Group	VAT: UK Tax @10.0%	tgogXSf1onY0	2022-09-20 14:09:11.97432+05:30	2022-09-20 14:09:11.974347+05:30	1	\N	{"tax_rate": 0.1}	f	f
2901	TAX_GROUP	Tax Group	II6NWV8PK4	tgoGzqpXD02A	2022-09-20 14:09:11.974678+05:30	2022-09-20 14:09:11.974761+05:30	1	\N	{"tax_rate": 0.18}	f	f
2902	TAX_GROUP	Tax Group	TG1OG645TP	tgoiydGXa6RI	2022-09-20 14:09:11.97495+05:30	2022-09-20 14:09:11.975021+05:30	1	\N	{"tax_rate": 0.18}	f	f
2903	TAX_GROUP	Tax Group	GP2UXTORT6	tgoK6ws8L40m	2022-09-20 14:09:11.975179+05:30	2022-09-20 14:09:11.975227+05:30	1	\N	{"tax_rate": 0.18}	f	f
2904	TAX_GROUP	Tax Group	H4FLZPRDRU	tgoRFNG0JKDV	2022-09-20 14:09:11.975596+05:30	2022-09-20 14:09:11.975747+05:30	1	\N	{"tax_rate": 0.18}	f	f
2906	TAX_GROUP	Tax Group	PNSOA0VKSF	tgOvm9YaBGPa	2022-09-20 14:09:11.975955+05:30	2022-09-20 14:09:11.975985+05:30	1	\N	{"tax_rate": 0.18}	f	f
2907	TAX_GROUP	Tax Group	6QLNH6Y4UM	tgoWBF2LV1DY	2022-09-20 14:09:11.976064+05:30	2022-09-20 14:09:11.976092+05:30	1	\N	{"tax_rate": 0.18}	f	f
2908	TAX_GROUP	Tax Group	Input tax - 0%	tgP2csYPZYr1	2022-09-20 14:09:11.976158+05:30	2022-09-20 14:09:11.976185+05:30	1	\N	{"tax_rate": 0.28}	f	f
2910	TAX_GROUP	Tax Group	QHGZ8OB0QW	tgp7Hi8kNwiw	2022-09-20 14:09:11.976465+05:30	2022-09-20 14:09:11.97651+05:30	1	\N	{"tax_rate": 0.18}	f	f
2911	TAX_GROUP	Tax Group	GG10QAP2S5	tgP8qUkLoAcJ	2022-09-20 14:09:11.976611+05:30	2022-09-20 14:09:11.976641+05:30	1	\N	{"tax_rate": 0.18}	f	f
2912	TAX_GROUP	Tax Group	1NIPCD4AIV	tgPBQtd1JY9j	2022-09-20 14:09:11.976724+05:30	2022-09-20 14:09:11.976753+05:30	1	\N	{"tax_rate": 0.18}	f	f
2913	TAX_GROUP	Tax Group	KF5LT1RF09	tgPDsE2wRsQz	2022-09-20 14:09:11.976831+05:30	2022-09-20 14:09:11.976858+05:30	1	\N	{"tax_rate": 0.18}	f	f
2914	TAX_GROUP	Tax Group	Tax on Consulting @8.25%	tgpgTQbdAQTE	2022-09-20 14:09:11.976924+05:30	2022-09-20 14:09:11.976951+05:30	1	\N	{"tax_rate": 0.08}	f	f
2915	TAX_GROUP	Tax Group	NCF-AU @0.0%	tgpIyPXp7YbJ	2022-09-20 14:09:11.977016+05:30	2022-09-20 14:09:11.977043+05:30	1	\N	{"tax_rate": 0.0}	f	f
2917	TAX_GROUP	Tax Group	9GZBIA2Z9H	tgPnK7or3K9x	2022-09-20 14:09:11.9772+05:30	2022-09-20 14:09:11.977227+05:30	1	\N	{"tax_rate": 0.18}	f	f
2918	TAX_GROUP	Tax Group	9KAP9QWA44	tgPOXTd5DoZ3	2022-09-20 14:09:11.977293+05:30	2022-09-20 14:09:11.97732+05:30	1	\N	{"tax_rate": 0.18}	f	f
2919	TAX_GROUP	Tax Group	Tax on Purchases @8.25%	tgPoY58NUJbl	2022-09-20 14:09:11.977523+05:30	2022-09-20 14:09:11.977562+05:30	1	\N	{"tax_rate": 0.08}	f	f
2920	TAX_GROUP	Tax Group	JQTAKMBYNJ	tgPs7otMgPlA	2022-09-20 14:09:11.977628+05:30	2022-09-20 14:09:11.977655+05:30	1	\N	{"tax_rate": 0.18}	f	f
2921	TAX_GROUP	Tax Group	O020KR52QV	tgPwj9u0NQHN	2022-09-20 14:09:11.97772+05:30	2022-09-20 14:09:11.977747+05:30	1	\N	{"tax_rate": 0.18}	f	f
2923	TAX_GROUP	Tax Group	Pant Tax @20%	tgq2mKV86LWz	2022-09-20 14:09:11.977905+05:30	2022-09-20 14:09:11.977933+05:30	1	\N	{"tax_rate": 0.2}	f	f
2924	TAX_GROUP	Tax Group	CA-E @0.0%	tgQC13IAQIR6	2022-09-20 14:09:11.977997+05:30	2022-09-20 14:09:11.978024+05:30	1	\N	{"tax_rate": 0.0}	f	f
2925	TAX_GROUP	Tax Group	K9ZTD8WVCG	tgqC2qkdsqic	2022-09-20 14:09:11.97809+05:30	2022-09-20 14:09:11.978117+05:30	1	\N	{"tax_rate": 0.18}	f	f
2926	TAX_GROUP	Tax Group	OT0WPR3LG1	tgqc7sfCgKPi	2022-09-20 14:09:11.978183+05:30	2022-09-20 14:09:11.97821+05:30	1	\N	{"tax_rate": 0.18}	f	f
2927	TAX_GROUP	Tax Group	YA65ILOGVV	tgqCwT8Q9Dsv	2022-09-20 14:09:11.978275+05:30	2022-09-20 14:09:11.978302+05:30	1	\N	{"tax_rate": 0.18}	f	f
2928	TAX_GROUP	Tax Group	VEU3R97JU6	tgQdlZoHLujH	2022-09-20 14:09:11.97849+05:30	2022-09-20 14:09:11.97853+05:30	1	\N	{"tax_rate": 0.18}	f	f
2929	TAX_GROUP	Tax Group	MQ3MHKG1JM	tgQf69ylVLyE	2022-09-20 14:09:11.978596+05:30	2022-09-20 14:09:11.978624+05:30	1	\N	{"tax_rate": 0.18}	f	f
2930	TAX_GROUP	Tax Group	8V1FTMOLVI	tgQfmwntIzWb	2022-09-20 14:09:11.978689+05:30	2022-09-20 14:09:11.978717+05:30	1	\N	{"tax_rate": 0.18}	f	f
2931	TAX_GROUP	Tax Group	AU1B8Y7TGS	tgqjARJIS7fE	2022-09-20 14:09:11.978782+05:30	2022-09-20 14:09:11.978809+05:30	1	\N	{"tax_rate": 0.18}	f	f
2932	TAX_GROUP	Tax Group	LW8V0C86U9	tgqJdKUbPCut	2022-09-20 14:09:11.978875+05:30	2022-09-20 14:09:11.978902+05:30	1	\N	{"tax_rate": 0.18}	f	f
2933	TAX_GROUP	Tax Group	-Not Taxable- @0.0%	tgQLIh7kwQc2	2022-09-20 14:09:11.97902+05:30	2022-09-20 14:09:11.979182+05:30	1	\N	{"tax_rate": 0.0}	f	f
2934	TAX_GROUP	Tax Group	ERLZ2WXGBY	tgqNfbt23hXF	2022-09-20 14:09:11.97927+05:30	2022-09-20 14:09:11.979297+05:30	1	\N	{"tax_rate": 0.18}	f	f
2935	TAX_GROUP	Tax Group	GST: ashwin_tax_code_1 @2.0%	tgqpMNwVNkyv	2022-09-20 14:09:11.979487+05:30	2022-09-20 14:09:11.979534+05:30	1	\N	{"tax_rate": 0.02}	f	f
2936	TAX_GROUP	Tax Group	5OJBS10VAC	tgRDxtr0jV61	2022-09-20 14:09:11.979661+05:30	2022-09-20 14:09:11.979705+05:30	1	\N	{"tax_rate": 0.18}	f	f
2937	TAX_GROUP	Tax Group	T1WP4WBELF	tgrEYpYAIhJh	2022-09-20 14:09:11.979922+05:30	2022-09-20 14:09:11.97996+05:30	1	\N	{"tax_rate": 0.18}	f	f
2938	TAX_GROUP	Tax Group	. @0.0%	tgrGkDS30KOf	2022-09-20 14:09:11.98027+05:30	2022-09-20 14:09:11.980328+05:30	1	\N	{"tax_rate": 0.0}	f	f
2940	TAX_GROUP	Tax Group	UNDEF-GB @0.0%	tgRieT5aVKOi	2022-09-20 14:09:11.981845+05:30	2022-09-20 14:09:11.981912+05:30	1	\N	{"tax_rate": 0.0}	f	f
2941	TAX_GROUP	Tax Group	City: New York City @0.5%	tgrihEBRsqmk	2022-09-20 14:09:11.982079+05:30	2022-09-20 14:09:11.982125+05:30	1	\N	{"tax_rate": 0.01}	f	f
2942	TAX_GROUP	Tax Group	W6RV83BFWU	tgril32Nl0pB	2022-09-20 14:09:11.988754+05:30	2022-09-20 14:09:11.988795+05:30	1	\N	{"tax_rate": 0.18}	f	f
2943	TAX_GROUP	Tax Group	Sales Tax on Imports @0.0%	tgrnS3h0Ruzg	2022-09-20 14:09:11.988864+05:30	2022-09-20 14:09:11.988892+05:30	1	\N	{"tax_rate": 0.0}	f	f
2944	TAX_GROUP	Tax Group	ABN: Nilesh @54.0%	tgRPkX7ymV2K	2022-09-20 14:09:11.988959+05:30	2022-09-20 14:09:11.988986+05:30	1	\N	{"tax_rate": 0.54}	f	f
2945	TAX_GROUP	Tax Group	7ZAAQDCQQN	tgRqeA5a9h0W	2022-09-20 14:09:11.989052+05:30	2022-09-20 14:09:11.98908+05:30	1	\N	{"tax_rate": 0.18}	f	f
2946	TAX_GROUP	Tax Group	GST: CPT-AU @10.0%	tgrSg9F7Y9sK	2022-09-20 14:09:11.989146+05:30	2022-09-20 14:09:11.989173+05:30	1	\N	{"tax_rate": 0.1}	f	f
2948	TAX_GROUP	Tax Group	ABN: Ashwin Tax Group @6.0%	tgrVpyLhsOsw	2022-09-20 14:09:11.989334+05:30	2022-09-20 14:09:11.989361+05:30	1	\N	{"tax_rate": 0.06}	f	f
2949	TAX_GROUP	Tax Group	MD8XPYK2C6	tgRz68cIQU2p	2022-09-20 14:09:11.98957+05:30	2022-09-20 14:09:11.98961+05:30	1	\N	{"tax_rate": 0.18}	f	f
2950	TAX_GROUP	Tax Group	D47UDLB4F8	tgS0DHQJFw70	2022-09-20 14:09:11.989969+05:30	2022-09-20 14:09:11.990003+05:30	1	\N	{"tax_rate": 0.18}	f	f
2951	TAX_GROUP	Tax Group	JQUIDWM0VG	tgsaNXWrKCc5	2022-09-20 14:09:11.990078+05:30	2022-09-20 14:09:11.990106+05:30	1	\N	{"tax_rate": 0.18}	f	f
680	PROJECT	Project	Project 4	203312	2022-09-20 14:09:06.848723+05:30	2022-09-20 14:09:06.848753+05:30	1	t	\N	f	f
2952	TAX_GROUP	Tax Group	CA-PST-ON @0.0%	tgSAZ4hJlF7y	2022-09-20 14:09:11.990171+05:30	2022-09-20 14:09:11.990198+05:30	1	\N	{"tax_rate": 0.0}	f	f
2953	TAX_GROUP	Tax Group	MB - GST/RST on Purchases @12.0%	tgSbMd0X3I3O	2022-09-20 14:09:11.990264+05:30	2022-09-20 14:09:11.99043+05:30	1	\N	{"tax_rate": 0.12}	f	f
3045	MERCHANT	Merchant	sravan	852	2022-09-20 14:10:15.786308+05:30	2022-09-20 14:10:15.786337+05:30	1	\N	\N	f	f
2955	TAX_GROUP	Tax Group	49BVB05MSS	tgsGJxfNb01o	2022-09-20 14:09:11.990605+05:30	2022-09-20 14:09:11.990632+05:30	1	\N	{"tax_rate": 0.18}	f	f
2956	TAX_GROUP	Tax Group	1KPDKITYMO	tgSLadNhUC0f	2022-09-20 14:09:11.990698+05:30	2022-09-20 14:09:11.990726+05:30	1	\N	{"tax_rate": 0.18}	f	f
2957	TAX_GROUP	Tax Group	H1979NVX85	tgsQFKNzf0SF	2022-09-20 14:09:11.990792+05:30	2022-09-20 14:09:11.99082+05:30	1	\N	{"tax_rate": 0.18}	f	f
2958	TAX_GROUP	Tax Group	CDGMCX2GYA	tgsqI5XeBb3m	2022-09-20 14:09:11.990885+05:30	2022-09-20 14:09:11.990913+05:30	1	\N	{"tax_rate": 0.18}	f	f
2959	TAX_GROUP	Tax Group	UATHCG2KXH	tgst2mtlstKq	2022-09-20 14:09:11.990979+05:30	2022-09-20 14:09:11.991006+05:30	1	\N	{"tax_rate": 0.18}	f	f
2960	TAX_GROUP	Tax Group	D477IUAK5W	tgtaKrDRl8rI	2022-09-20 14:09:11.991072+05:30	2022-09-20 14:09:11.9911+05:30	1	\N	{"tax_rate": 0.18}	f	f
2961	TAX_GROUP	Tax Group	OUR0YT9KBK	tgtDlBSNRU91	2022-09-20 14:09:11.991166+05:30	2022-09-20 14:09:11.991193+05:30	1	\N	{"tax_rate": 0.18}	f	f
2962	TAX_GROUP	Tax Group	PVDGPPF2SC	tgTekLsroRNM	2022-09-20 14:09:11.99126+05:30	2022-09-20 14:09:11.991287+05:30	1	\N	{"tax_rate": 0.18}	f	f
2963	TAX_GROUP	Tax Group	69NR7TNK5P	tgTEr828y2c4	2022-09-20 14:09:11.991353+05:30	2022-09-20 14:09:11.991501+05:30	1	\N	{"tax_rate": 0.18}	f	f
2964	TAX_GROUP	Tax Group	A5QP6EJ9HR	tgTmEhiHY9Wb	2022-09-20 14:09:11.991587+05:30	2022-09-20 14:09:11.991614+05:30	1	\N	{"tax_rate": 0.18}	f	f
2965	TAX_GROUP	Tax Group	YG9ZHOW03L	tgtnlAuPccmU	2022-09-20 14:09:11.99168+05:30	2022-09-20 14:09:11.991707+05:30	1	\N	{"tax_rate": 0.18}	f	f
2966	TAX_GROUP	Tax Group	E2ZA5DOLZP	tgTVkrIoFyPv	2022-09-20 14:09:11.991773+05:30	2022-09-20 14:09:11.991801+05:30	1	\N	{"tax_rate": 0.18}	f	f
2967	TAX_GROUP	Tax Group	37YWNDJGXS	tgTz2uOpFEAG	2022-09-20 14:09:11.991866+05:30	2022-09-20 14:09:11.991893+05:30	1	\N	{"tax_rate": 0.18}	f	f
2969	TAX_GROUP	Tax Group	CPI-AU @0.0%	tgUcIG8nhjfj	2022-09-20 14:09:11.992052+05:30	2022-09-20 14:09:11.992079+05:30	1	\N	{"tax_rate": 0.0}	f	f
2970	TAX_GROUP	Tax Group	N234JZCM07	tguDb9LHWbNf	2022-09-20 14:09:11.992145+05:30	2022-09-20 14:09:11.992172+05:30	1	\N	{"tax_rate": 0.18}	f	f
2971	TAX_GROUP	Tax Group	Z8STSQH7B8	tgufmQT6nguV	2022-09-20 14:09:11.992238+05:30	2022-09-20 14:09:11.992265+05:30	1	\N	{"tax_rate": 0.18}	f	f
2972	TAX_GROUP	Tax Group	PST: PST_ON_8 @8.0%	tgUHUWIkCUaG	2022-09-20 14:09:11.99233+05:30	2022-09-20 14:09:11.992496+05:30	1	\N	{"tax_rate": 0.08}	f	f
2973	TAX_GROUP	Tax Group	OZY0APPOHJ	tguiFXGObZCj	2022-09-20 14:09:11.992577+05:30	2022-09-20 14:09:11.992604+05:30	1	\N	{"tax_rate": 0.18}	f	f
2974	TAX_GROUP	Tax Group	tax for twelve @12.5%	tgUL6n1ekT5l	2022-09-20 14:09:11.99267+05:30	2022-09-20 14:09:11.992697+05:30	1	\N	{"tax_rate": 0.12}	f	f
2975	TAX_GROUP	Tax Group	AAHWZOY5QZ	tgUMC7ALYxAL	2022-09-20 14:09:11.992763+05:30	2022-09-20 14:09:11.99279+05:30	1	\N	{"tax_rate": 0.18}	f	f
2976	TAX_GROUP	Tax Group	MAUZTC2I53	tgUMh6FrCTvo	2022-09-20 14:09:11.992856+05:30	2022-09-20 14:09:11.992883+05:30	1	\N	{"tax_rate": 0.18}	f	f
2977	TAX_GROUP	Tax Group	LCT: LCT-AU @25.0%	tgupeKzRMBhH	2022-09-20 14:09:11.992949+05:30	2022-09-20 14:09:11.992976+05:30	1	\N	{"tax_rate": 0.25}	f	f
2978	TAX_GROUP	Tax Group	T2PVG1SAHV	tguQQbeTirzC	2022-09-20 14:09:11.993043+05:30	2022-09-20 14:09:11.99307+05:30	1	\N	{"tax_rate": 0.18}	f	f
2979	TAX_GROUP	Tax Group	7TF6ZC4WT9	tguu3K3w002b	2022-09-20 14:09:11.993135+05:30	2022-09-20 14:09:11.993162+05:30	1	\N	{"tax_rate": 0.18}	f	f
2980	TAX_GROUP	Tax Group	NY - Manhattan @8.5%	tgV1E80ArlhG	2022-09-20 14:09:11.993228+05:30	2022-09-20 14:09:11.993256+05:30	1	\N	{"tax_rate": 0.09}	f	f
2981	TAX_GROUP	Tax Group	IZJZZ3S9E7	tgVDrNQDr1Mw	2022-09-20 14:09:11.993321+05:30	2022-09-20 14:09:11.993359+05:30	1	\N	{"tax_rate": 0.18}	f	f
2983	TAX_GROUP	Tax Group	GST on capital @10%	tgVlVvok652A	2022-09-20 14:09:11.993655+05:30	2022-09-20 14:09:11.993682+05:30	1	\N	{"tax_rate": 0.1}	f	f
2985	TAX_GROUP	Tax Group	VFDBWILTZT	tgVpULIa6cnN	2022-09-20 14:09:11.99384+05:30	2022-09-20 14:09:11.993868+05:30	1	\N	{"tax_rate": 0.18}	f	f
2986	TAX_GROUP	Tax Group	OONDUAK3WT	tgVT2VnaV3Kt	2022-09-20 14:09:11.993933+05:30	2022-09-20 14:09:11.99396+05:30	1	\N	{"tax_rate": 0.18}	f	f
2987	TAX_GROUP	Tax Group	C72U5RL80N	tgvtS0wCmlx8	2022-09-20 14:09:11.994025+05:30	2022-09-20 14:09:11.994053+05:30	1	\N	{"tax_rate": 0.18}	f	f
2988	TAX_GROUP	Tax Group	CA-GST only @0.0%	tgvUMgvIjacH	2022-09-20 14:09:11.994118+05:30	2022-09-20 14:09:11.994145+05:30	1	\N	{"tax_rate": 0.0}	f	f
2989	TAX_GROUP	Tax Group	XBBEZH9O4N	tgvXYIFQvNTb	2022-09-20 14:09:11.994211+05:30	2022-09-20 14:09:11.994239+05:30	1	\N	{"tax_rate": 0.18}	f	f
2990	TAX_GROUP	Tax Group	SVWPR6H082	tgw8w0rFWK3u	2022-09-20 14:09:11.994305+05:30	2022-09-20 14:09:11.994332+05:30	1	\N	{"tax_rate": 0.18}	f	f
2991	TAX_GROUP	Tax Group	SD6IFM5X2M	tgW8w2tofnfF	2022-09-20 14:09:11.994538+05:30	2022-09-20 14:09:11.994566+05:30	1	\N	{"tax_rate": 0.18}	f	f
2992	TAX_GROUP	Tax Group	UI777ZUG5P	tgwkRoheKrgP	2022-09-20 14:09:12.003088+05:30	2022-09-20 14:09:12.003128+05:30	1	\N	{"tax_rate": 0.18}	f	f
2993	TAX_GROUP	Tax Group	XG2FEN961D	tgWnzNShpJWc	2022-09-20 14:09:12.003197+05:30	2022-09-20 14:09:12.003225+05:30	1	\N	{"tax_rate": 0.18}	f	f
2994	TAX_GROUP	Tax Group	ZW806W7J5F	tgWq0Vb4vTKD	2022-09-20 14:09:12.003292+05:30	2022-09-20 14:09:12.003329+05:30	1	\N	{"tax_rate": 0.18}	f	f
2995	TAX_GROUP	Tax Group	CABFH8FYWJ	tgWTT4lg0IM2	2022-09-20 14:09:12.003509+05:30	2022-09-20 14:09:12.003538+05:30	1	\N	{"tax_rate": 0.18}	f	f
2996	TAX_GROUP	Tax Group	YQKG0LTOUZ	tgwule26Fo6a	2022-09-20 14:09:12.003604+05:30	2022-09-20 14:09:12.003631+05:30	1	\N	{"tax_rate": 0.18}	f	f
2997	TAX_GROUP	Tax Group	ABN: Faltu Tax @25.0%	tgWVy7KigBlk	2022-09-20 14:09:12.003698+05:30	2022-09-20 14:09:12.003726+05:30	1	\N	{"tax_rate": 0.25}	f	f
2998	TAX_GROUP	Tax Group	5DNCP094R0	tgWW7v553bpm	2022-09-20 14:09:12.003792+05:30	2022-09-20 14:09:12.00382+05:30	1	\N	{"tax_rate": 0.18}	f	f
2999	TAX_GROUP	Tax Group	GST: ashwin_tax_code_2 @4.0%	tgwYo6RC8qsA	2022-09-20 14:09:12.003885+05:30	2022-09-20 14:09:12.003913+05:30	1	\N	{"tax_rate": 0.04}	f	f
3000	TAX_GROUP	Tax Group	55D90KR22F	tgx09djzUEYt	2022-09-20 14:09:12.003979+05:30	2022-09-20 14:09:12.004006+05:30	1	\N	{"tax_rate": 0.18}	f	f
3001	TAX_GROUP	Tax Group	1Q274U30JE	tgX6HYq92Vq3	2022-09-20 14:09:12.004072+05:30	2022-09-20 14:09:12.0041+05:30	1	\N	{"tax_rate": 0.18}	f	f
3002	TAX_GROUP	Tax Group	SBNNYXHGJM	tgx7VR8VjhN4	2022-09-20 14:09:12.004165+05:30	2022-09-20 14:09:12.004193+05:30	1	\N	{"tax_rate": 0.18}	f	f
3003	TAX_GROUP	Tax Group	0UDWEKF5QQ	tgxCVmcnUcnf	2022-09-20 14:09:12.004258+05:30	2022-09-20 14:09:12.004286+05:30	1	\N	{"tax_rate": 0.18}	f	f
3004	TAX_GROUP	Tax Group	OEZ61NIBGN	tgXFxQ9o7ZYt	2022-09-20 14:09:12.004352+05:30	2022-09-20 14:09:12.004391+05:30	1	\N	{"tax_rate": 0.18}	f	f
3005	TAX_GROUP	Tax Group	248OHESQX4	tgxlsyzztBiA	2022-09-20 14:09:12.004588+05:30	2022-09-20 14:09:12.004627+05:30	1	\N	{"tax_rate": 0.18}	f	f
3006	TAX_GROUP	Tax Group	State: New York State @6.5%	tgXqTTjgvNhW	2022-09-20 14:09:12.004707+05:30	2022-09-20 14:09:12.004735+05:30	1	\N	{"tax_rate": 0.07}	f	f
3007	TAX_GROUP	Tax Group	SOYMBT74SM	tgxTtJLTNwML	2022-09-20 14:09:12.004801+05:30	2022-09-20 14:09:12.004828+05:30	1	\N	{"tax_rate": 0.18}	f	f
3008	TAX_GROUP	Tax Group	CE1SD2SQIK	tgXu7Tt49YmB	2022-09-20 14:09:12.004894+05:30	2022-09-20 14:09:12.004921+05:30	1	\N	{"tax_rate": 0.18}	f	f
3009	TAX_GROUP	Tax Group	GST	tgXueCemFa6Q	2022-09-20 14:09:12.004988+05:30	2022-09-20 14:09:12.005015+05:30	1	\N	{"tax_rate": 0.18}	f	f
3010	TAX_GROUP	Tax Group	RGUG2EU1X7	tgXum4KLE0ib	2022-09-20 14:09:12.005081+05:30	2022-09-20 14:09:12.005108+05:30	1	\N	{"tax_rate": 0.18}	f	f
3011	TAX_GROUP	Tax Group	XNJ6IYQTT6	tgxVtrVbTvUQ	2022-09-20 14:09:12.005173+05:30	2022-09-20 14:09:12.0052+05:30	1	\N	{"tax_rate": 0.18}	f	f
3012	TAX_GROUP	Tax Group	CA-S-AB @0.0%	tgXWjsl5EyeS	2022-09-20 14:09:12.005266+05:30	2022-09-20 14:09:12.005293+05:30	1	\N	{"tax_rate": 0.0}	f	f
3013	TAX_GROUP	Tax Group	Pant Tax - 10%	tgy17771Fs0Z	2022-09-20 14:09:12.005461+05:30	2022-09-20 14:09:12.005482+05:30	1	\N	{"tax_rate": 0.28}	f	f
3014	TAX_GROUP	Tax Group	AVXYHDXGHR	tgy2bykBE9ad	2022-09-20 14:09:12.005553+05:30	2022-09-20 14:09:12.005581+05:30	1	\N	{"tax_rate": 0.18}	f	f
3015	TAX_GROUP	Tax Group	VNISXKB26C	tgY3NmihHRox	2022-09-20 14:09:12.005647+05:30	2022-09-20 14:09:12.005674+05:30	1	\N	{"tax_rate": 0.18}	f	f
3016	TAX_GROUP	Tax Group	GWNYCAUI7U	tgY6OZ8p4lMB	2022-09-20 14:09:12.00574+05:30	2022-09-20 14:09:12.005767+05:30	1	\N	{"tax_rate": 0.18}	f	f
3017	TAX_GROUP	Tax Group	Z07A9NN1DM	tgy6SBVsh5HM	2022-09-20 14:09:12.005833+05:30	2022-09-20 14:09:12.00586+05:30	1	\N	{"tax_rate": 0.18}	f	f
3018	TAX_GROUP	Tax Group	I3LOOW56KF	tgY9sJwvbriq	2022-09-20 14:09:12.005926+05:30	2022-09-20 14:09:12.005953+05:30	1	\N	{"tax_rate": 0.18}	f	f
3020	TAX_GROUP	Tax Group	50Q5KYEKC7	tgYdzyKe756m	2022-09-20 14:09:12.006112+05:30	2022-09-20 14:09:12.006138+05:30	1	\N	{"tax_rate": 0.18}	f	f
3021	TAX_GROUP	Tax Group	D1IO8OGBJ7	tgYIpi3wxhGt	2022-09-20 14:09:12.006205+05:30	2022-09-20 14:09:12.006232+05:30	1	\N	{"tax_rate": 0.18}	f	f
3022	TAX_GROUP	Tax Group	36TEBIWA0N	tgyjcu8nrbTy	2022-09-20 14:09:12.006297+05:30	2022-09-20 14:09:12.006325+05:30	1	\N	{"tax_rate": 0.18}	f	f
3023	TAX_GROUP	Tax Group	GST: TS-AU @10.0%	tgYJqx59P3t3	2022-09-20 14:09:12.006525+05:30	2022-09-20 14:09:12.006546+05:30	1	\N	{"tax_rate": 0.1}	f	f
3024	TAX_GROUP	Tax Group	SKJX43FH5L	tgyKbeg9FzL2	2022-09-20 14:09:12.006616+05:30	2022-09-20 14:09:12.006644+05:30	1	\N	{"tax_rate": 0.18}	f	f
3025	TAX_GROUP	Tax Group	ZIZU1AAHLF	tgYSo7xOCzh7	2022-09-20 14:09:12.00671+05:30	2022-09-20 14:09:12.006737+05:30	1	\N	{"tax_rate": 0.18}	f	f
3026	TAX_GROUP	Tax Group	6W2VT8W7SC	tgyvZ3fASuAF	2022-09-20 14:09:12.006803+05:30	2022-09-20 14:09:12.006831+05:30	1	\N	{"tax_rate": 0.18}	f	f
3027	TAX_GROUP	Tax Group	Other 2 Sales Tax: GST @18.0%	tgYw6DkCzssM	2022-09-20 14:09:12.006897+05:30	2022-09-20 14:09:12.006924+05:30	1	\N	{"tax_rate": 0.18}	f	f
3028	TAX_GROUP	Tax Group	IVX8Q7M4OL	tgYzbD4f1AjL	2022-09-20 14:09:12.00699+05:30	2022-09-20 14:09:12.007018+05:30	1	\N	{"tax_rate": 0.18}	f	f
3029	TAX_GROUP	Tax Group	KOY9ZL06FA	tgZ4TqDtyjyq	2022-09-20 14:09:12.007083+05:30	2022-09-20 14:09:12.007111+05:30	1	\N	{"tax_rate": 0.18}	f	f
3030	TAX_GROUP	Tax Group	Input tax @0%	tgZCQgT9K0Fk	2022-09-20 14:09:12.007176+05:30	2022-09-20 14:09:12.007203+05:30	1	\N	{"tax_rate": 0}	f	f
3031	TAX_GROUP	Tax Group	GHFPC90RHT	tgzDViut4LVz	2022-09-20 14:09:12.007269+05:30	2022-09-20 14:09:12.007296+05:30	1	\N	{"tax_rate": 0.18}	f	f
3032	TAX_GROUP	Tax Group	1SBDCCFM3Q	tgzgq9Qnzdvs	2022-09-20 14:09:12.007372+05:30	2022-09-20 14:09:12.007478+05:30	1	\N	{"tax_rate": 0.18}	f	f
3033	TAX_GROUP	Tax Group	CUBSMXQ74V	tgZhEaewHZCF	2022-09-20 14:09:12.007542+05:30	2022-09-20 14:09:12.00758+05:30	1	\N	{"tax_rate": 0.18}	f	f
3034	TAX_GROUP	Tax Group	QYQKO8SPR6	tgZIde9FACt7	2022-09-20 14:09:12.007646+05:30	2022-09-20 14:09:12.007674+05:30	1	\N	{"tax_rate": 0.18}	f	f
3035	TAX_GROUP	Tax Group	3GYAQ1QYHQ	tgZixx6QTCMo	2022-09-20 14:09:12.007739+05:30	2022-09-20 14:09:12.007767+05:30	1	\N	{"tax_rate": 0.18}	f	f
3036	TAX_GROUP	Tax Group	L519GF6JU0	tgZjxKuxJfEp	2022-09-20 14:09:12.007832+05:30	2022-09-20 14:09:12.007859+05:30	1	\N	{"tax_rate": 0.18}	f	f
3037	TAX_GROUP	Tax Group	0215IGBNYP	tgZJZ7FaRzyy	2022-09-20 14:09:12.007925+05:30	2022-09-20 14:09:12.007952+05:30	1	\N	{"tax_rate": 0.18}	f	f
3038	TAX_GROUP	Tax Group	IZZG6UH5Y8	tgzkV4S2Yw1h	2022-09-20 14:09:12.008018+05:30	2022-09-20 14:09:12.008045+05:30	1	\N	{"tax_rate": 0.18}	f	f
3039	TAX_GROUP	Tax Group	IKIJX0TM8Y	tgzKVrUU5UNa	2022-09-20 14:09:12.008111+05:30	2022-09-20 14:09:12.008138+05:30	1	\N	{"tax_rate": 0.18}	f	f
3040	TAX_GROUP	Tax Group	EGJMQFKSKM	tgzL3ZYEzsoZ	2022-09-20 14:09:12.008203+05:30	2022-09-20 14:09:12.00823+05:30	1	\N	{"tax_rate": 0.18}	f	f
3042	TAX_GROUP	Tax Group	Nilesh Tax - 10%	tgzVoKWXqWFB	2022-09-20 14:09:12.015868+05:30	2022-09-20 14:09:12.015907+05:30	1	\N	{"tax_rate": 0.28}	f	f
3046	MERCHANT	Merchant	light	852	2022-09-20 14:10:15.786398+05:30	2022-09-20 14:10:15.786428+05:30	1	\N	\N	f	f
3047	MERCHANT	Merchant	Abhishek 2	852	2022-09-20 14:10:15.786489+05:30	2022-09-20 14:10:15.786518+05:30	1	\N	\N	f	f
3048	MERCHANT	Merchant	Abhishek ji	852	2022-09-20 14:10:15.786579+05:30	2022-09-20 14:10:15.786608+05:30	1	\N	\N	f	f
3049	MERCHANT	Merchant	Bob's Burger Joint	852	2022-09-20 14:10:15.786669+05:30	2022-09-20 14:10:15.786698+05:30	1	\N	\N	f	f
3050	MERCHANT	Merchant	Books by Bessie	852	2022-09-20 14:10:15.786758+05:30	2022-09-20 14:10:15.786787+05:30	1	\N	\N	f	f
3051	MERCHANT	Merchant	Brian Foster	852	2022-09-20 14:10:15.786847+05:30	2022-09-20 14:10:15.786876+05:30	1	\N	\N	f	f
3052	MERCHANT	Merchant	Brosnahan Insurance Agency	852	2022-09-20 14:10:15.786937+05:30	2022-09-20 14:10:15.786966+05:30	1	\N	\N	f	f
3053	MERCHANT	Merchant	Cal Telephone	852	2022-09-20 14:10:15.787026+05:30	2022-09-20 14:10:15.787055+05:30	1	\N	\N	f	f
3054	MERCHANT	Merchant	Chin's Gas and Oil	852	2022-09-20 14:10:15.787115+05:30	2022-09-20 14:10:15.787144+05:30	1	\N	\N	f	f
3055	MERCHANT	Merchant	Cigna Health Care	852	2022-09-20 14:10:15.787205+05:30	2022-09-20 14:10:15.787234+05:30	1	\N	\N	f	f
3056	MERCHANT	Merchant	Computers by Jenni	852	2022-09-20 14:10:15.787294+05:30	2022-09-20 14:10:15.787323+05:30	1	\N	\N	f	f
3057	MERCHANT	Merchant	Credit Card Misc	852	2022-09-20 14:10:15.787384+05:30	2022-09-20 14:10:15.787413+05:30	1	\N	\N	f	f
3058	MERCHANT	Merchant	Diego's Road Warrior Bodyshop	852	2022-09-20 14:10:15.787473+05:30	2022-09-20 14:10:15.787494+05:30	1	\N	\N	f	f
3059	MERCHANT	Merchant	EDD	852	2022-09-20 14:10:15.787555+05:30	2022-09-20 14:10:15.794364+05:30	1	\N	\N	f	f
3060	MERCHANT	Merchant	Ellis Equipment Rental	852	2022-09-20 14:10:15.853096+05:30	2022-09-20 14:10:15.853163+05:30	1	\N	\N	f	f
3061	MERCHANT	Merchant	Fidelity	852	2022-09-20 14:10:15.859393+05:30	2022-09-20 14:10:15.85944+05:30	1	\N	\N	f	f
3062	MERCHANT	Merchant	Fyle For QBO Paymrnt Sync	852	2022-09-20 14:10:15.859509+05:30	2022-09-20 14:10:15.859539+05:30	1	\N	\N	f	f
3063	MERCHANT	Merchant	Hall Properties	852	2022-09-20 14:10:15.859601+05:30	2022-09-20 14:10:15.85963+05:30	1	\N	\N	f	f
3064	MERCHANT	Merchant	Hicks Hardware	852	2022-09-20 14:10:15.859691+05:30	2022-09-20 14:10:15.859721+05:30	1	\N	\N	f	f
3066	MERCHANT	Merchant	Jessica Lane	852	2022-09-20 14:10:15.859871+05:30	2022-09-20 14:10:15.8599+05:30	1	\N	\N	f	f
3067	MERCHANT	Merchant	Justin Glass	852	2022-09-20 14:10:15.859961+05:30	2022-09-20 14:10:15.85999+05:30	1	\N	\N	f	f
3068	MERCHANT	Merchant	Lee Advertising	852	2022-09-20 14:10:15.860051+05:30	2022-09-20 14:10:15.86008+05:30	1	\N	\N	f	f
3069	MERCHANT	Merchant	Mahoney Mugs	852	2022-09-20 14:10:15.860238+05:30	2022-09-20 14:10:15.869043+05:30	1	\N	\N	f	f
3070	MERCHANT	Merchant	Matthew Estrada	852	2022-09-20 14:10:15.869139+05:30	2022-09-20 14:10:15.881046+05:30	1	\N	\N	f	f
3071	MERCHANT	Merchant	Met Life Dental	852	2022-09-20 14:10:15.88118+05:30	2022-09-20 14:10:15.881216+05:30	1	\N	\N	f	f
3072	MERCHANT	Merchant	Natalie Pope	852	2022-09-20 14:10:15.881292+05:30	2022-09-20 14:10:15.881324+05:30	1	\N	\N	f	f
3073	MERCHANT	Merchant	National Eye Care	852	2022-09-20 14:10:15.881394+05:30	2022-09-20 14:10:15.881424+05:30	1	\N	\N	f	f
3074	MERCHANT	Merchant	Nilesh Pant	852	2022-09-20 14:10:15.881491+05:30	2022-09-20 14:10:15.881521+05:30	1	\N	\N	f	f
3075	MERCHANT	Merchant	Norton Lumber and Building Materials	852	2022-09-20 14:10:15.885902+05:30	2022-09-20 14:10:15.885941+05:30	1	\N	\N	f	f
3076	MERCHANT	Merchant	Pam Seitz	852	2022-09-20 14:10:15.888852+05:30	2022-09-20 14:10:15.888895+05:30	1	\N	\N	f	f
3077	MERCHANT	Merchant	PG&E	852	2022-09-20 14:10:15.888964+05:30	2022-09-20 14:10:15.888994+05:30	1	\N	\N	f	f
3078	MERCHANT	Merchant	Robertson & Associates	852	2022-09-20 14:10:15.889211+05:30	2022-09-20 14:10:15.889253+05:30	1	\N	\N	f	f
3079	MERCHANT	Merchant	Samantha Washington	852	2022-09-20 14:10:15.889336+05:30	2022-09-20 14:10:15.889366+05:30	1	\N	\N	f	f
3080	MERCHANT	Merchant	SPEEDWAY	852	2022-09-20 14:10:15.88943+05:30	2022-09-20 14:10:15.889465+05:30	1	\N	\N	f	f
3081	MERCHANT	Merchant	Squeaky Kleen Car Wash	852	2022-09-20 14:10:15.889588+05:30	2022-09-20 14:10:15.924766+05:30	1	\N	\N	f	f
3082	MERCHANT	Merchant	Sravan	852	2022-09-20 14:10:15.925107+05:30	2022-09-20 14:10:15.925797+05:30	1	\N	\N	f	f
3083	MERCHANT	Merchant	Sravan KSK	852	2022-09-20 14:10:15.929249+05:30	2022-09-20 14:10:15.929334+05:30	1	\N	\N	f	f
3084	MERCHANT	Merchant	Tania's Nursery	852	2022-09-20 14:10:15.929469+05:30	2022-09-20 14:10:15.929513+05:30	1	\N	\N	f	f
3087	MERCHANT	Merchant	Tony Rondonuwu	852	2022-09-20 14:10:15.929905+05:30	2022-09-20 14:10:15.929935+05:30	1	\N	\N	f	f
3088	MERCHANT	Merchant	United States Treasury	852	2022-09-20 14:10:15.929995+05:30	2022-09-20 14:10:15.930123+05:30	1	\N	\N	f	f
3089	MERCHANT	Merchant	vendor import	852	2022-09-20 14:10:15.930181+05:30	2022-09-20 14:10:15.930202+05:30	1	\N	\N	f	f
3090	MERCHANT	Merchant	Alexandra Fitzgerald	852	2022-09-20 14:10:15.930263+05:30	2022-09-20 14:10:15.930285+05:30	1	\N	\N	f	f
3091	MERCHANT	Merchant	Allison Hill	852	2022-09-20 14:10:15.930338+05:30	2022-09-20 14:10:15.930367+05:30	1	\N	\N	f	f
3092	MERCHANT	Merchant	Amanda Monroe	852	2022-09-20 14:10:15.932232+05:30	2022-09-20 14:10:15.93226+05:30	1	\N	\N	f	f
3093	MERCHANT	Merchant	Amazon	852	2022-09-20 14:10:15.96609+05:30	2022-09-20 14:10:15.966132+05:30	1	\N	\N	f	f
3094	MERCHANT	Merchant	Amazon Web Services	852	2022-09-20 14:10:15.969507+05:30	2022-09-20 14:10:15.969554+05:30	1	\N	\N	f	f
3095	MERCHANT	Merchant	Anna Williamson	852	2022-09-20 14:10:15.969624+05:30	2022-09-20 14:10:15.969653+05:30	1	\N	\N	f	f
3096	MERCHANT	Merchant	Anne Glass	852	2022-09-20 14:10:15.969714+05:30	2022-09-20 14:10:15.969743+05:30	1	\N	\N	f	f
3097	MERCHANT	Merchant	Anne Jackson	852	2022-09-20 14:10:15.969803+05:30	2022-09-20 14:10:15.969831+05:30	1	\N	\N	f	f
3102	MERCHANT	Merchant	Brenda Hawkins	852	2022-09-20 14:10:15.970353+05:30	2022-09-20 14:10:15.970382+05:30	1	\N	\N	f	f
3103	MERCHANT	Merchant	Central Coalfields	852	2022-09-20 14:10:15.970441+05:30	2022-09-20 14:10:15.97047+05:30	1	\N	\N	f	f
3104	MERCHANT	Merchant	Chris Curtis	852	2022-09-20 14:10:15.970531+05:30	2022-09-20 14:10:15.970559+05:30	1	\N	\N	f	f
3105	MERCHANT	Merchant	Debit Card Misc	852	2022-09-20 14:10:15.97062+05:30	2022-09-20 14:10:15.970649+05:30	1	\N	\N	f	f
3106	MERCHANT	Merchant	Dominos	852	2022-09-20 14:10:15.970709+05:30	2022-09-20 14:10:15.970738+05:30	1	\N	\N	f	f
3107	MERCHANT	Merchant	DOMINO'S	852	2022-09-20 14:10:15.970798+05:30	2022-09-20 14:10:15.970827+05:30	1	\N	\N	f	f
3108	MERCHANT	Merchant	DOMINO'S P	852	2022-09-20 14:10:15.970887+05:30	2022-09-20 14:10:15.970916+05:30	1	\N	\N	f	f
3109	MERCHANT	Merchant	Edward Blankenship	852	2022-09-20 14:10:15.970976+05:30	2022-09-20 14:10:15.971005+05:30	1	\N	\N	f	f
3110	MERCHANT	Merchant	Fyle Vendor	852	2022-09-20 14:10:15.971065+05:30	2022-09-20 14:10:15.971094+05:30	1	\N	\N	f	f
3111	MERCHANT	Merchant	Gokul	852	2022-09-20 14:10:15.971251+05:30	2022-09-20 14:10:15.971281+05:30	1	\N	\N	f	f
3112	MERCHANT	Merchant	Gokul Kathiresan	852	2022-09-20 14:10:15.971343+05:30	2022-09-20 14:10:15.971372+05:30	1	\N	\N	f	f
3113	MERCHANT	Merchant	Gokul Kathiresan King	852	2022-09-20 14:10:15.971433+05:30	2022-09-20 14:10:15.971462+05:30	1	\N	\N	f	f
3114	MERCHANT	Merchant	Jonathan Elliott	852	2022-09-20 14:10:15.971523+05:30	2022-09-20 14:10:15.971552+05:30	1	\N	\N	f	f
3115	MERCHANT	Merchant	Joshua Wood	852	2022-09-20 14:10:15.971612+05:30	2022-09-20 14:10:15.971642+05:30	1	\N	\N	f	f
3116	MERCHANT	Merchant	Lord Voldemort	852	2022-09-20 14:10:15.971702+05:30	2022-09-20 14:10:15.972321+05:30	1	\N	\N	f	f
3117	MERCHANT	Merchant	Matt Damon	852	2022-09-20 14:10:15.972502+05:30	2022-09-20 14:10:15.972548+05:30	1	\N	\N	f	f
3118	MERCHANT	Merchant	Peter Derek	852	2022-09-20 14:10:15.972641+05:30	2022-09-20 14:10:15.972675+05:30	1	\N	\N	f	f
3119	MERCHANT	Merchant	Ravindra Jadeja	852	2022-09-20 14:10:15.972755+05:30	2022-09-20 14:10:15.972783+05:30	1	\N	\N	f	f
3120	MERCHANT	Merchant	Ryan Gallagher	852	2022-09-20 14:10:15.972877+05:30	2022-09-20 14:10:15.972922+05:30	1	\N	\N	f	f
3121	MERCHANT	Merchant	Shwetabh Ji	852	2022-09-20 14:10:15.987609+05:30	2022-09-20 14:10:15.987662+05:30	1	\N	\N	f	f
3122	MERCHANT	Merchant	staging vendor	852	2022-09-20 14:10:15.987754+05:30	2022-09-20 14:10:15.987785+05:30	1	\N	\N	f	f
3123	MERCHANT	Merchant	STEAK-N-SHAKE#0664	852	2022-09-20 14:10:15.987861+05:30	2022-09-20 14:10:15.987898+05:30	1	\N	\N	f	f
3124	MERCHANT	Merchant	Theresa Brown	852	2022-09-20 14:10:15.987962+05:30	2022-09-20 14:10:15.992213+05:30	1	\N	\N	f	f
3125	MERCHANT	Merchant	Uber	852	2022-09-20 14:10:15.992369+05:30	2022-09-20 14:10:15.992416+05:30	1	\N	\N	f	f
3126	MERCHANT	Merchant	Victor Martinez	852	2022-09-20 14:10:15.99252+05:30	2022-09-20 14:10:15.992565+05:30	1	\N	\N	f	f
3127	MERCHANT	Merchant	Victor Martinez II	852	2022-09-20 14:10:15.992712+05:30	2022-09-20 14:10:15.992763+05:30	1	\N	\N	f	f
3128	MERCHANT	Merchant	Wal-Mart	852	2022-09-20 14:10:15.993087+05:30	2022-09-20 14:10:15.993146+05:30	1	\N	\N	f	f
3129	MERCHANT	Merchant	final staging vandor	852	2022-09-20 14:10:15.993665+05:30	2022-09-20 14:10:15.993716+05:30	1	\N	\N	f	f
3130	MERCHANT	Merchant	Killua	852	2022-09-20 14:10:15.993791+05:30	2022-09-20 14:10:15.993822+05:30	1	\N	\N	f	f
3131	MERCHANT	Merchant	labhvam	852	2022-09-20 14:10:15.993884+05:30	2022-09-20 14:10:15.993914+05:30	1	\N	\N	f	f
3132	MERCHANT	Merchant	Fyle new employeeee	852	2022-09-20 14:10:16.008963+05:30	2022-09-20 14:10:16.009024+05:30	1	\N	\N	f	f
3133	MERCHANT	Merchant	Ashwin Vendor 2.0	852	2022-09-20 14:10:16.009604+05:30	2022-09-20 14:10:16.009724+05:30	1	\N	\N	f	f
3134	MERCHANT	Merchant	California EDD (HQ)	852	2022-09-20 14:10:16.010008+05:30	2022-09-20 14:10:16.010116+05:30	1	\N	\N	f	f
3135	MERCHANT	Merchant	CPR ATLANTIC CASPER	852	2022-09-20 14:10:16.010378+05:30	2022-09-20 14:10:16.010643+05:30	1	\N	\N	f	f
3136	MERCHANT	Merchant	EXPENSIFY.COM SAN FRANCISCO USA	852	2022-09-20 14:10:16.0108+05:30	2022-09-20 14:10:16.010851+05:30	1	\N	\N	f	f
3137	MERCHANT	Merchant	FACEBK RUW7LCPQU2	852	2022-09-20 14:10:16.010972+05:30	2022-09-20 14:10:16.011019+05:30	1	\N	\N	f	f
3138	MERCHANT	Merchant	FORT DODGE FLIGHT SUPP	852	2022-09-20 14:10:16.011129+05:30	2022-09-20 14:10:16.011169+05:30	1	\N	\N	f	f
3139	MERCHANT	Merchant	GOOGLE*GOOGLE STORAGE IRELAND IRL	852	2022-09-20 14:10:16.011277+05:30	2022-09-20 14:10:16.011317+05:30	1	\N	\N	f	f
3140	MERCHANT	Merchant	GRAND AIRE, INC.	852	2022-09-20 14:10:16.011418+05:30	2022-09-20 14:10:16.011458+05:30	1	\N	\N	f	f
3141	MERCHANT	Merchant	Internal Revenue Service-FUTA (HQ)	852	2022-09-20 14:10:16.011558+05:30	2022-09-20 14:10:16.011598+05:30	1	\N	\N	f	f
3142	MERCHANT	Merchant	Internal Revenue Service- Income,FICA (HQ)	852	2022-09-20 14:10:16.011692+05:30	2022-09-20 14:10:16.011732+05:30	1	\N	\N	f	f
3143	MERCHANT	Merchant	MAILCHIMP ATLANTA USA	852	2022-09-20 14:10:16.050336+05:30	2022-09-20 14:10:16.050387+05:30	1	\N	\N	f	f
3144	MERCHANT	Merchant	MARRIOTT ANCHORAGE	852	2022-09-20 14:10:16.050468+05:30	2022-09-20 14:10:16.0505+05:30	1	\N	\N	f	f
3145	MERCHANT	Merchant	New York City (HQ)	852	2022-09-20 14:10:16.050571+05:30	2022-09-20 14:10:16.050601+05:30	1	\N	\N	f	f
3146	MERCHANT	Merchant	New York County (HQ)	852	2022-09-20 14:10:16.050668+05:30	2022-09-20 14:10:16.050697+05:30	1	\N	\N	f	f
3147	MERCHANT	Merchant	New York State (HQ)	852	2022-09-20 14:10:16.05076+05:30	2022-09-20 14:10:16.05079+05:30	1	\N	\N	f	f
3148	MERCHANT	Merchant	Nilesh	852	2022-09-20 14:10:16.050853+05:30	2022-09-20 14:10:16.050882+05:30	1	\N	\N	f	f
3149	MERCHANT	Merchant	Nippoin Accountants	852	2022-09-20 14:10:16.050945+05:30	2022-09-20 14:10:16.050967+05:30	1	\N	\N	f	f
3150	MERCHANT	Merchant	Purchase Al Dept Of Revenue	852	2022-09-20 14:10:16.05101+05:30	2022-09-20 14:10:16.051021+05:30	1	\N	\N	f	f
3151	MERCHANT	Merchant	Purchase Marshall Tag 2562754042	852	2022-09-20 14:10:16.051072+05:30	2022-09-20 14:10:16.051101+05:30	1	\N	\N	f	f
3152	MERCHANT	Merchant	Purchase Taxhandlingfee2562754042	852	2022-09-20 14:10:16.051163+05:30	2022-09-20 14:10:16.051192+05:30	1	\N	\N	f	f
3153	MERCHANT	Merchant	State Board of Equalization (HQ)	852	2022-09-20 14:10:16.052635+05:30	2022-09-20 14:10:16.052694+05:30	1	\N	\N	f	f
3154	MERCHANT	Merchant	Stein Investments (HQ)	852	2022-09-20 14:10:16.052799+05:30	2022-09-20 14:10:16.053056+05:30	1	\N	\N	f	f
3155	MERCHANT	Merchant	Store Tax Agency (HQ)	852	2022-09-20 14:10:16.053126+05:30	2022-09-20 14:10:16.053155+05:30	1	\N	\N	f	f
3156	MERCHANT	Merchant	Swiggy	852	2022-09-20 14:10:16.053216+05:30	2022-09-20 14:10:16.053245+05:30	1	\N	\N	f	f
3157	MERCHANT	Merchant	Tax Agency AK (3 - Honeycomb Holdings Inc.) (20210317-104301)	852	2022-09-20 14:10:16.053306+05:30	2022-09-20 14:10:16.053336+05:30	1	\N	\N	f	f
3158	MERCHANT	Merchant	Test Vendor	852	2022-09-20 14:10:16.053396+05:30	2022-09-20 14:10:16.053425+05:30	1	\N	\N	f	f
3159	MERCHANT	Merchant	TOWNEPLACE SUITES BY M	852	2022-09-20 14:10:16.053486+05:30	2022-09-20 14:10:16.053515+05:30	1	\N	\N	f	f
3160	MERCHANT	Merchant	ezagpulmvbxgogg	852	2022-09-20 14:10:16.053575+05:30	2022-09-20 14:10:16.053604+05:30	1	\N	\N	f	f
3161	MERCHANT	Merchant	hxnvqlydmnudjpi	852	2022-09-20 14:10:16.053664+05:30	2022-09-20 14:10:16.053693+05:30	1	\N	\N	f	f
3162	MERCHANT	Merchant	Joanna	852	2022-09-20 14:10:16.053753+05:30	2022-09-20 14:10:16.053782+05:30	1	\N	\N	f	f
3163	MERCHANT	Merchant	Provincial Treasurer AB	852	2022-09-20 14:10:16.053842+05:30	2022-09-20 14:10:16.053872+05:30	1	\N	\N	f	f
3164	MERCHANT	Merchant	Receiver General	852	2022-09-20 14:10:16.053924+05:30	2022-09-20 14:10:16.053945+05:30	1	\N	\N	f	f
3165	MERCHANT	Merchant	ADP	852	2022-09-20 14:10:24.027869+05:30	2022-09-20 14:10:24.027911+05:30	1	\N	\N	f	f
3166	MERCHANT	Merchant	Advisor Printing	852	2022-09-20 14:10:24.02797+05:30	2022-09-20 14:10:24.027998+05:30	1	\N	\N	f	f
3167	MERCHANT	Merchant	akavuluru	852	2022-09-20 14:10:24.028055+05:30	2022-09-20 14:10:24.028083+05:30	1	\N	\N	f	f
3168	MERCHANT	Merchant	American Express	852	2022-09-20 14:10:24.02827+05:30	2022-09-20 14:10:24.028309+05:30	1	\N	\N	f	f
3169	MERCHANT	Merchant	Boardwalk Post	852	2022-09-20 14:10:24.028366+05:30	2022-09-20 14:10:24.028393+05:30	1	\N	\N	f	f
3170	MERCHANT	Merchant	Canyon CPA	852	2022-09-20 14:10:24.028449+05:30	2022-09-20 14:10:24.028476+05:30	1	\N	\N	f	f
3171	MERCHANT	Merchant	Citi Bank	852	2022-09-20 14:10:24.028532+05:30	2022-09-20 14:10:24.02856+05:30	1	\N	\N	f	f
3172	MERCHANT	Merchant	Consulting Grid	852	2022-09-20 14:10:24.028616+05:30	2022-09-20 14:10:24.028643+05:30	1	\N	\N	f	f
3173	MERCHANT	Merchant	Cornerstone	852	2022-09-20 14:10:24.028699+05:30	2022-09-20 14:10:24.028726+05:30	1	\N	\N	f	f
3174	MERCHANT	Merchant	Entity V100	852	2022-09-20 14:10:24.028783+05:30	2022-09-20 14:10:24.02881+05:30	1	\N	\N	f	f
3175	MERCHANT	Merchant	Entity V200	852	2022-09-20 14:10:24.028874+05:30	2022-09-20 14:10:24.028901+05:30	1	\N	\N	f	f
3176	MERCHANT	Merchant	Entity V300	852	2022-09-20 14:10:24.028958+05:30	2022-09-20 14:10:24.028985+05:30	1	\N	\N	f	f
3177	MERCHANT	Merchant	Entity V400	852	2022-09-20 14:10:24.029041+05:30	2022-09-20 14:10:24.029068+05:30	1	\N	\N	f	f
3181	MERCHANT	Merchant	Global Printing	852	2022-09-20 14:10:24.029507+05:30	2022-09-20 14:10:24.029534+05:30	1	\N	\N	f	f
3182	MERCHANT	Merchant	Global Properties Inc.	852	2022-09-20 14:10:24.029591+05:30	2022-09-20 14:10:24.029618+05:30	1	\N	\N	f	f
3183	MERCHANT	Merchant	gokul	852	2022-09-20 14:10:24.029675+05:30	2022-09-20 14:10:24.029702+05:30	1	\N	\N	f	f
3184	MERCHANT	Merchant	Green Team Waste Management	852	2022-09-20 14:10:24.029758+05:30	2022-09-20 14:10:24.029785+05:30	1	\N	\N	f	f
3185	MERCHANT	Merchant	Hanson Learning Solutions	852	2022-09-20 14:10:24.029841+05:30	2022-09-20 14:10:24.029868+05:30	1	\N	\N	f	f
3186	MERCHANT	Merchant	HC Equipment Repair	852	2022-09-20 14:10:24.029925+05:30	2022-09-20 14:10:24.029952+05:30	1	\N	\N	f	f
3187	MERCHANT	Merchant	Investor CPA	852	2022-09-20 14:10:24.030009+05:30	2022-09-20 14:10:24.030036+05:30	1	\N	\N	f	f
3188	MERCHANT	Merchant	Kaufman & Langer LLP	852	2022-09-20 14:10:24.030093+05:30	2022-09-20 14:10:24.030131+05:30	1	\N	\N	f	f
3189	MERCHANT	Merchant	Kristofferson Consulting	852	2022-09-20 14:10:24.030308+05:30	2022-09-20 14:10:24.030336+05:30	1	\N	\N	f	f
3190	MERCHANT	Merchant	Lee Thomas	852	2022-09-20 14:10:24.030392+05:30	2022-09-20 14:10:24.030425+05:30	1	\N	\N	f	f
3191	MERCHANT	Merchant	Lenovo	852	2022-09-20 14:10:24.030482+05:30	2022-09-20 14:10:24.030509+05:30	1	\N	\N	f	f
3192	MERCHANT	Merchant	Linda Hicks	852	2022-09-20 14:10:24.030566+05:30	2022-09-20 14:10:24.030593+05:30	1	\N	\N	f	f
3193	MERCHANT	Merchant	Magnolia CPA	852	2022-09-20 14:10:24.030649+05:30	2022-09-20 14:10:24.030677+05:30	1	\N	\N	f	f
3194	MERCHANT	Merchant	Massachusetts Department of Revenue	852	2022-09-20 14:10:24.030733+05:30	2022-09-20 14:10:24.03076+05:30	1	\N	\N	f	f
3195	MERCHANT	Merchant	Microns Consulting	852	2022-09-20 14:10:24.030816+05:30	2022-09-20 14:10:24.030844+05:30	1	\N	\N	f	f
3196	MERCHANT	Merchant	National Grid	852	2022-09-20 14:10:24.0309+05:30	2022-09-20 14:10:24.030927+05:30	1	\N	\N	f	f
3197	MERCHANT	Merchant	National Insurance	852	2022-09-20 14:10:24.030989+05:30	2022-09-20 14:10:24.031017+05:30	1	\N	\N	f	f
3198	MERCHANT	Merchant	Neighborhood Printers	852	2022-09-20 14:10:24.031073+05:30	2022-09-20 14:10:24.031101+05:30	1	\N	\N	f	f
3199	MERCHANT	Merchant	Nilesh, Dhoni	852	2022-09-20 14:10:24.031264+05:30	2022-09-20 14:10:24.031289+05:30	1	\N	\N	f	f
3200	MERCHANT	Merchant	Paramount Consulting	852	2022-09-20 14:10:24.031343+05:30	2022-09-20 14:10:24.031356+05:30	1	\N	\N	f	f
3201	MERCHANT	Merchant	Prima Printing	852	2022-09-20 14:10:24.031395+05:30	2022-09-20 14:10:24.031415+05:30	1	\N	\N	f	f
3202	MERCHANT	Merchant	Prosper Post	852	2022-09-20 14:10:24.031483+05:30	2022-09-20 14:10:24.03151+05:30	1	\N	\N	f	f
3203	MERCHANT	Merchant	Quali Consultants	852	2022-09-20 14:10:24.031566+05:30	2022-09-20 14:10:24.031593+05:30	1	\N	\N	f	f
3204	MERCHANT	Merchant	Quick Post	852	2022-09-20 14:10:24.03165+05:30	2022-09-20 14:10:24.031677+05:30	1	\N	\N	f	f
3205	MERCHANT	Merchant	River Glen Insurance	852	2022-09-20 14:10:24.031733+05:30	2022-09-20 14:10:24.03176+05:30	1	\N	\N	f	f
3206	MERCHANT	Merchant	Sachin, Saran	852	2022-09-20 14:10:24.031828+05:30	2022-09-20 14:10:24.031856+05:30	1	\N	\N	f	f
3207	MERCHANT	Merchant	Scribe Post	852	2022-09-20 14:10:24.031917+05:30	2022-09-20 14:10:24.031944+05:30	1	\N	\N	f	f
3208	MERCHANT	Merchant	Singleton Brothers CPA	852	2022-09-20 14:10:24.032001+05:30	2022-09-20 14:10:24.032028+05:30	1	\N	\N	f	f
3209	MERCHANT	Merchant	Srav	852	2022-09-20 14:10:24.032084+05:30	2022-09-20 14:10:24.032123+05:30	1	\N	\N	f	f
3210	MERCHANT	Merchant	State Bank	852	2022-09-20 14:10:24.03227+05:30	2022-09-20 14:10:24.032298+05:30	1	\N	\N	f	f
3211	MERCHANT	Merchant	The Nonprofit Alliance	852	2022-09-20 14:10:24.032354+05:30	2022-09-20 14:10:24.032382+05:30	1	\N	\N	f	f
3212	MERCHANT	Merchant	The Post Company	852	2022-09-20 14:10:24.032511+05:30	2022-09-20 14:10:24.032678+05:30	1	\N	\N	f	f
3213	MERCHANT	Merchant	Vaishnavi Primary	852	2022-09-20 14:10:24.032979+05:30	2022-09-20 14:10:24.033121+05:30	1	\N	\N	f	f
3214	MERCHANT	Merchant	Vision Post	852	2022-09-20 14:10:24.033563+05:30	2022-09-20 14:10:24.033617+05:30	1	\N	\N	f	f
3215	MERCHANT	Merchant	VM	852	2022-09-20 14:10:24.040086+05:30	2022-09-20 14:10:24.040137+05:30	1	\N	\N	f	f
3216	MERCHANT	Merchant	Worldwide Commercial	852	2022-09-20 14:10:24.040336+05:30	2022-09-20 14:10:24.040364+05:30	1	\N	\N	f	f
3217	MERCHANT	Merchant	Yash	852	2022-09-20 14:10:24.040432+05:30	2022-09-20 14:10:24.040477+05:30	1	\N	\N	f	f
1	EMPLOYEE	Employee	ashwin.t@fyle.in	ouVLOYP8lelN	2022-09-20 14:09:02.390021+05:30	2022-09-20 14:09:02.390094+05:30	1	\N	{"user_id": "usqywo0f3nBY", "location": null, "full_name": "Joanna", "department": null, "department_id": null, "employee_code": null, "department_code": null}	t	f
3222	TAX_GROUP	Tax Group	N27HHEOEY8	tgA7LDFGfctm	2022-09-28 16:50:40.693894+05:30	2022-09-28 16:50:40.693975+05:30	1	\N	{"tax_rate": 0.18}	f	f
3223	TAX_GROUP	Tax Group	H7FH7Q9WJ6	tghvvY536lD4	2022-09-28 16:50:40.694094+05:30	2022-09-28 16:50:40.694113+05:30	1	\N	{"tax_rate": 0.18}	f	f
3224	TAX_GROUP	Tax Group	FML12E68S6	tgYjjc9hfkNP	2022-09-28 16:50:40.694203+05:30	2022-09-28 16:50:40.694237+05:30	1	\N	{"tax_rate": 0.18}	f	f
2692	TAX_GROUP	Tax Group	EC Purchase Goods Standard Rate Input	tg03sPKjNkKq	2022-09-20 14:09:11.565395+05:30	2022-09-20 14:09:11.565464+05:30	1	\N	{"tax_rate": 0.2}	t	f
2720	TAX_GROUP	Tax Group	UK Purchase Goods Reduced Rate	tg51CNoNSxiO	2022-09-20 14:09:11.582902+05:30	2022-09-20 14:09:11.582963+05:30	1	\N	{"tax_rate": 0.05}	t	f
2725	TAX_GROUP	Tax Group	EC Purchase Services Reduced Rate Input	tg6icu6uquJZ	2022-09-20 14:09:11.583955+05:30	2022-09-20 14:09:11.584005+05:30	1	\N	{"tax_rate": 0.05}	t	f
2737	TAX_GROUP	Tax Group	UK Import Goods Standard Rate	tg7sE7ZSw5Yn	2022-09-20 14:09:11.592389+05:30	2022-09-20 14:09:11.592419+05:30	1	\N	{"tax_rate": 0.2}	t	f
2751	TAX_GROUP	Tax Group	Other Output Tax Adjustments	tga9OiFNWcDh	2022-09-20 14:09:11.632416+05:30	2022-09-20 14:09:11.632436+05:30	1	\N	{"tax_rate": 1.0}	t	f
2822	TAX_GROUP	Tax Group	Standard Rate (Capital Goods) Input	tgGn1oIv0odS	2022-09-20 14:09:11.65591+05:30	2022-09-20 14:09:11.655941+05:30	1	\N	{"tax_rate": 0.15}	t	f
2834	TAX_GROUP	Tax Group	G13 Purchases for Input Tax Sales	tghyBGpukx04	2022-09-20 14:09:11.657436+05:30	2022-09-20 14:09:11.657456+05:30	1	\N	{"tax_rate": 0.1}	t	f
2840	TAX_GROUP	Tax Group	G15 Capital Purchases for Private Use	tginkDefSKP7	2022-09-20 14:09:11.658091+05:30	2022-09-20 14:09:11.658111+05:30	1	\N	{"tax_rate": 0.1}	t	f
2857	TAX_GROUP	Tax Group	Standard Rate Input	tgkrTg3hsBGo	2022-09-20 14:09:11.674255+05:30	2022-09-20 14:09:11.674277+05:30	1	\N	{"tax_rate": 0.15}	t	f
2869	TAX_GROUP	Tax Group	G10 Capital Acquisition	tgLj0KdoNp6n	2022-09-20 14:09:11.676154+05:30	2022-09-20 14:09:11.676176+05:30	1	\N	{"tax_rate": 0.1}	t	f
103	CATEGORY	Category	kfliuyfdlify liuflif	184629	2022-09-20 14:09:03.37353+05:30	2022-09-20 14:09:03.373552+05:30	1	t	\N	f	f
2873	TAX_GROUP	Tax Group	UK Purchase in Reverse Charge Box 6 Reduced Rate UK Input	tgLq1ZgwHe2N	2022-09-20 14:09:11.676895+05:30	2022-09-20 14:09:11.676915+05:30	1	\N	{"tax_rate": 0.05}	t	f
2875	TAX_GROUP	Tax Group	G13 Capital Purchases for Input Tax Sales	tgm1nnhMeKs4	2022-09-20 14:09:11.677165+05:30	2022-09-20 14:09:11.677204+05:30	1	\N	{"tax_rate": 0.1}	t	f
2884	TAX_GROUP	Tax Group	EC Purchase Goods Reduced Rate Input	tgMYde7GlsXF	2022-09-20 14:09:11.67889+05:30	2022-09-20 14:09:11.678912+05:30	1	\N	{"tax_rate": 0.05}	t	f
2893	TAX_GROUP	Tax Group	UK Purchase Reverse Charge Standard Rate Input	tgNqkGml9EGM	2022-09-20 14:09:11.972991+05:30	2022-09-20 14:09:11.973059+05:30	1	\N	{"tax_rate": 0.2}	t	f
2905	TAX_GROUP	Tax Group	UK Import Services Reduced Rate	tgOULxUfH6EV	2022-09-20 14:09:11.975849+05:30	2022-09-20 14:09:11.975876+05:30	1	\N	{"tax_rate": 0.05}	t	f
2916	TAX_GROUP	Tax Group	UK Purchase Goods Standard Rate	tgPM90wg21fN	2022-09-20 14:09:11.977108+05:30	2022-09-20 14:09:11.977135+05:30	1	\N	{"tax_rate": 0.2}	t	f
2922	TAX_GROUP	Tax Group	G11 Other Acquisition	tgPzaJl9YEIy	2022-09-20 14:09:11.977813+05:30	2022-09-20 14:09:11.97784+05:30	1	\N	{"tax_rate": 0.1}	t	f
2939	TAX_GROUP	Tax Group	Change in Use Input	tgRi0weoxcIg	2022-09-20 14:09:11.981003+05:30	2022-09-20 14:09:11.981102+05:30	1	\N	{"tax_rate": 0.15}	t	f
2947	TAX_GROUP	Tax Group	UK Import Services Standard Rate	tgRuU4aJDtp0	2022-09-20 14:09:11.98924+05:30	2022-09-20 14:09:11.989267+05:30	1	\N	{"tax_rate": 0.2}	t	f
2954	TAX_GROUP	Tax Group	G15 Purchases for Private Use	tgsFw1s5tPre	2022-09-20 14:09:11.990512+05:30	2022-09-20 14:09:11.99054+05:30	1	\N	{"tax_rate": 0.1}	t	f
2968	TAX_GROUP	Tax Group	EC Purchase Services Standard Rate Input	tgU4rY4PFZpv	2022-09-20 14:09:11.991959+05:30	2022-09-20 14:09:11.991986+05:30	1	\N	{"tax_rate": 0.2}	t	f
2982	TAX_GROUP	Tax Group	UK Purchase Reverse Charge Reduced Rate Input	tgVKGWKL7pPt	2022-09-20 14:09:11.993562+05:30	2022-09-20 14:09:11.99359+05:30	1	\N	{"tax_rate": 0.05}	t	f
2984	TAX_GROUP	Tax Group	UK Import Goods Reduced Rate	tgVnRMSNQpKK	2022-09-20 14:09:11.993748+05:30	2022-09-20 14:09:11.993775+05:30	1	\N	{"tax_rate": 0.05}	t	f
3019	TAX_GROUP	Tax Group	UK Purchase in Reverse Charge Box 6 Standard Rate UK Input	tgYDec7KVOw4	2022-09-20 14:09:12.006019+05:30	2022-09-20 14:09:12.006046+05:30	1	\N	{"tax_rate": 0.2}	t	f
3041	TAX_GROUP	Tax Group	G10 Motor Vehicle Acquisition	tgZUh8neIfxC	2022-09-20 14:09:12.008296+05:30	2022-09-20 14:09:12.008323+05:30	1	\N	{"tax_rate": 0.1}	t	f
3248	TAX_GROUP	Tax Group	No Input VAT	tgUIrIce3bbR	2022-09-29 17:39:34.570694+05:30	2022-09-29 17:39:34.570723+05:30	1	\N	{"tax_rate": 0.0}	t	f
3228	TAX_GROUP	Tax Group	G15 GST Free Purchases for Private Use	tg1mbgnpCD74	2022-09-29 17:39:34.562145+05:30	2022-09-29 17:39:34.562208+05:30	1	\N	{"tax_rate": 0.0}	t	f
3229	TAX_GROUP	Tax Group	1F Luxury Car Tax Refundable	tg2vcq1pLm4T	2022-09-29 17:39:34.562296+05:30	2022-09-29 17:39:34.562326+05:30	1	\N	{"tax_rate": 0.0}	t	f
3230	TAX_GROUP	Tax Group	EC Purchase Goods Exempt Rate	tgAJLZUDLsNQ	2022-09-29 17:39:34.562396+05:30	2022-09-29 17:39:34.562425+05:30	1	\N	{"tax_rate": 0.0}	t	f
3232	TAX_GROUP	Tax Group	G13 GST Free Capital Purchases for Input Tax Sales	tgbMrQbQlYQy	2022-09-29 17:39:34.562592+05:30	2022-09-29 17:39:34.562622+05:30	1	\N	{"tax_rate": 0.0}	t	f
3233	TAX_GROUP	Tax Group	1D Wine Equalisation Tax Refundable	tgcn2gXFEHY7	2022-09-29 17:39:34.562691+05:30	2022-09-29 17:39:34.562721+05:30	1	\N	{"tax_rate": 0.0}	t	f
270	CATEGORY	Category	Automobile	135717	2022-09-20 14:09:05.193039+05:30	2022-09-20 14:09:05.193068+05:30	1	t	\N	f	f
3234	TAX_GROUP	Tax Group	G13 GST Free Purchases for Input Tax Sales	tgdoF2v8wmrE	2022-09-29 17:39:34.562789+05:30	2022-09-29 17:39:34.562818+05:30	1	\N	{"tax_rate": 0.0}	t	f
3235	TAX_GROUP	Tax Group	G14 GST Free Non-Capital Purchases	tgemain9bLa7	2022-09-29 17:39:34.562886+05:30	2022-09-29 17:39:34.562915+05:30	1	\N	{"tax_rate": 0.0}	t	f
3236	TAX_GROUP	Tax Group	Other Goods Imported (Not Capital Goods)	tgkxSRv2TaRu	2022-09-29 17:39:34.569172+05:30	2022-09-29 17:39:34.569223+05:30	1	\N	{"tax_rate": 0.0}	t	f
3237	TAX_GROUP	Tax Group	G14 GST Free Capital Purchases	tgl1DZ4CwRD4	2022-09-29 17:39:34.569334+05:30	2022-09-29 17:39:34.569364+05:30	1	\N	{"tax_rate": 0.0}	t	f
3238	TAX_GROUP	Tax Group	UK Import Goods Exempt Rate	tgMiYO0TshL4	2022-09-29 17:39:34.569436+05:30	2022-09-29 17:39:34.569465+05:30	1	\N	{"tax_rate": 0.0}	t	f
3239	TAX_GROUP	Tax Group	UK Purchase Services Exempt Rate	tgmL0gaIk8QA	2022-09-29 17:39:34.569535+05:30	2022-09-29 17:39:34.569575+05:30	1	\N	{"tax_rate": 0.0}	t	f
3240	TAX_GROUP	Tax Group	UK Purchase in Reverse Charge Box 6 Zero Rate UK	tgoP36Onf0Zk	2022-09-29 17:39:34.569787+05:30	2022-09-29 17:39:34.569824+05:30	1	\N	{"tax_rate": 0.0}	t	f
3241	TAX_GROUP	Tax Group	G15 GST Free Capital Purchases for Private Use	tgq53BJYGByc	2022-09-29 17:39:34.569901+05:30	2022-09-29 17:39:34.569931+05:30	1	\N	{"tax_rate": 0.0}	t	f
3242	TAX_GROUP	Tax Group	UK Import Services Zero Rate	tgQgmFdOAuCf	2022-09-29 17:39:34.5701+05:30	2022-09-29 17:39:34.57013+05:30	1	\N	{"tax_rate": 0.0}	t	f
3243	TAX_GROUP	Tax Group	UK Purchase Goods Exempt Rate	tgQXbB0B4ayf	2022-09-29 17:39:34.5702+05:30	2022-09-29 17:39:34.570229+05:30	1	\N	{"tax_rate": 0.0}	t	f
3245	TAX_GROUP	Tax Group	UK Purchase in Reverse Charge Box 6 Exempt UK	tgS7uGNdnU3G	2022-09-29 17:39:34.570397+05:30	2022-09-29 17:39:34.570427+05:30	1	\N	{"tax_rate": 0.0}	t	f
3246	TAX_GROUP	Tax Group	Capital Goods Imported	tgtJswuKZ0Tm	2022-09-29 17:39:34.570497+05:30	2022-09-29 17:39:34.570526+05:30	1	\N	{"tax_rate": 0.0}	t	f
3247	TAX_GROUP	Tax Group	UK Import Goods Zero Rate	tgU9adO9cZ0v	2022-09-29 17:39:34.570596+05:30	2022-09-29 17:39:34.570625+05:30	1	\N	{"tax_rate": 0.0}	t	f
3249	TAX_GROUP	Tax Group	UK Purchase Goods Zero Rate	tgUMN1LbRgQn	2022-09-29 17:39:34.570792+05:30	2022-09-29 17:39:34.570821+05:30	1	\N	{"tax_rate": 0.0}	t	f
3250	TAX_GROUP	Tax Group	EC Purchase Services Zero Rate	tgv3qq4c4SkN	2022-09-29 17:39:34.57089+05:30	2022-09-29 17:39:34.57092+05:30	1	\N	{"tax_rate": 0.0}	t	f
3251	TAX_GROUP	Tax Group	G18 Input Tax Credit Adjustment	tgVdyPpozeoS	2022-09-29 17:39:34.571078+05:30	2022-09-29 17:39:34.571107+05:30	1	\N	{"tax_rate": 0.0}	t	f
3252	TAX_GROUP	Tax Group	EC Purchase Goods Zero Rate	tgXpOAMeNMux	2022-09-29 17:39:34.571177+05:30	2022-09-29 17:39:34.571206+05:30	1	\N	{"tax_rate": 0.0}	t	f
3253	TAX_GROUP	Tax Group	UK Import Services Exempt Rate	tgzgsasJ22yi	2022-09-29 17:39:34.571275+05:30	2022-09-29 17:39:34.571304+05:30	1	\N	{"tax_rate": 0.0}	t	f
3254	TAX_GROUP	Tax Group	EC Purchase Services Exempt Rate	tgzxd7JcZbz0	2022-09-29 17:39:34.571374+05:30	2022-09-29 17:39:34.571403+05:30	1	\N	{"tax_rate": 0.0}	t	f
2747	TAX_GROUP	Tax Group	UK Purchase Services Reduced Rate	tg9Q7Ppb49qU	2022-09-20 14:09:11.631836+05:30	2022-09-20 14:09:11.631913+05:30	1	\N	{"tax_rate": 0.05}	t	f
2909	TAX_GROUP	Tax Group	UK Purchase Services Standard Rate	tgp3usmS2kNN	2022-09-20 14:09:11.976251+05:30	2022-09-20 14:09:11.976278+05:30	1	\N	{"tax_rate": 0.2}	t	f
3231	TAX_GROUP	Tax Group	UK Purchase Services Zero Rate	tgb414CpV8wg	2022-09-29 17:39:34.562494+05:30	2022-09-29 17:39:34.562523+05:30	1	\N	{"tax_rate": 0.0}	t	f
3244	TAX_GROUP	Tax Group	W4 Withholding Tax	tgrpuUs8G1x2	2022-09-29 17:39:34.570298+05:30	2022-09-29 17:39:34.570327+05:30	1	\N	{"tax_rate": 0.0}	t	f
97	CATEGORY	Category	Xero Expense Account	192750	2022-09-20 14:09:03.372626+05:30	2022-09-20 14:09:03.372656+05:30	1	t	\N	f	f
98	CATEGORY	Category	New Aus	192534	2022-09-20 14:09:03.372716+05:30	2022-09-20 14:09:03.372745+05:30	1	t	\N	f	f
99	CATEGORY	Category	Final Aus Category	192535	2022-09-20 14:09:03.372805+05:30	2022-09-20 14:09:03.372834+05:30	1	t	\N	f	f
100	CATEGORY	Category	Nilesh Pant	192536	2022-09-20 14:09:03.372895+05:30	2022-09-20 14:09:03.372924+05:30	1	t	\N	f	f
101	CATEGORY	Category	Material purchase	191262	2022-09-20 14:09:03.373338+05:30	2022-09-20 14:09:03.373381+05:30	1	t	\N	f	f
102	CATEGORY	Category	Nilesh	184628	2022-09-20 14:09:03.373469+05:30	2022-09-20 14:09:03.37348+05:30	1	t	\N	f	f
106	CATEGORY	Category	Miscellaneous	163671	2022-09-20 14:09:03.374511+05:30	2022-09-20 14:09:03.374531+05:30	1	t	\N	f	f
107	CATEGORY	Category	Penalties & Settlements	163672	2022-09-20 14:09:03.374574+05:30	2022-09-20 14:09:03.374595+05:30	1	t	\N	f	f
108	CATEGORY	Category	Reconciliation Discrepancies	163673	2022-09-20 14:09:03.37465+05:30	2022-09-20 14:09:03.374671+05:30	1	t	\N	f	f
109	CATEGORY	Category	Checking	162001	2022-09-20 14:09:03.375565+05:30	2022-09-20 14:09:03.375613+05:30	1	t	\N	f	f
110	CATEGORY	Category	Savings	162002	2022-09-20 14:09:03.375782+05:30	2022-09-20 14:09:03.375809+05:30	1	t	\N	f	f
111	CATEGORY	Category	Advertising/Promotional	161875	2022-09-20 14:09:03.375861+05:30	2022-09-20 14:09:03.375882+05:30	1	t	\N	f	f
112	CATEGORY	Category	UK Expense Category	157669	2022-09-20 14:09:03.375971+05:30	2022-09-20 14:09:03.376371+05:30	1	t	\N	f	f
113	CATEGORY	Category	GST Paid	157846	2022-09-20 14:09:03.376985+05:30	2022-09-20 14:09:03.377032+05:30	1	t	\N	f	f
114	CATEGORY	Category	LCT Paid	157847	2022-09-20 14:09:03.377118+05:30	2022-09-20 14:09:03.377151+05:30	1	t	\N	f	f
115	CATEGORY	Category	WET Paid	157848	2022-09-20 14:09:03.378156+05:30	2022-09-20 14:09:03.378195+05:30	1	t	\N	f	f
116	CATEGORY	Category	ABN Withholding	157849	2022-09-20 14:09:03.378272+05:30	2022-09-20 14:09:03.378304+05:30	1	t	\N	f	f
117	CATEGORY	Category	Pay As You Go Withholding	157850	2022-09-20 14:09:03.378372+05:30	2022-09-20 14:09:03.378402+05:30	1	t	\N	f	f
118	CATEGORY	Category	VAT on Purchases	157851	2022-09-20 14:09:03.411993+05:30	2022-09-20 14:09:03.412058+05:30	1	t	\N	f	f
119	CATEGORY	Category	UK Expense Acct	157852	2022-09-20 14:09:03.414181+05:30	2022-09-20 14:09:03.414486+05:30	1	t	\N	f	f
120	CATEGORY	Category	UK EXP Account	157853	2022-09-20 14:09:03.414712+05:30	2022-09-20 14:09:03.414802+05:30	1	t	\N	f	f
121	CATEGORY	Category	Meals and Entertainment	135593	2022-09-20 14:09:03.414923+05:30	2022-09-20 14:09:03.414967+05:30	1	t	\N	f	f
122	CATEGORY	Category	Travel - Automobile	149798	2022-09-20 14:09:03.415097+05:30	2022-09-20 14:09:03.415139+05:30	1	t	\N	f	f
123	CATEGORY	Category	Aus Category	149228	2022-09-20 14:09:03.417914+05:30	2022-09-20 14:09:03.418009+05:30	1	t	\N	f	f
124	CATEGORY	Category	Bank Charges	135543	2022-09-20 14:09:03.418187+05:30	2022-09-20 14:09:03.418245+05:30	1	t	\N	f	f
125	CATEGORY	Category	Dues and Subscriptions	136468	2022-09-20 14:09:03.418374+05:30	2022-09-20 14:09:03.418424+05:30	1	t	\N	f	f
126	CATEGORY	Category	New Category	147927	2022-09-20 14:09:03.419031+05:30	2022-09-20 14:09:03.419575+05:30	1	t	\N	f	f
127	CATEGORY	Category	Travel expenses - selling expenses	147504	2022-09-20 14:09:03.419723+05:30	2022-09-20 14:09:03.419766+05:30	1	t	\N	f	f
18	CATEGORY	Category	post malone	208625	2022-09-20 14:09:03.250297+05:30	2022-09-20 14:09:03.25067+05:30	1	t	\N	f	f
19	CATEGORY	Category	Repair & Maintenance	208626	2022-09-20 14:09:03.250788+05:30	2022-09-20 14:09:03.250837+05:30	1	t	\N	f	f
28	CATEGORY	Category	KGF	208254	2022-09-20 14:09:03.252684+05:30	2022-09-20 14:09:03.252713+05:30	1	t	\N	f	f
29	CATEGORY	Category	Business Expense	208255	2022-09-20 14:09:03.252773+05:30	2022-09-20 14:09:03.252802+05:30	1	t	\N	f	f
30	CATEGORY	Category	Office/General Administrative Expenses	208256	2022-09-20 14:09:03.252863+05:30	2022-09-20 14:09:03.252892+05:30	1	t	\N	f	f
31	CATEGORY	Category	Entertainment	135450	2022-09-20 14:09:03.252953+05:30	2022-09-20 14:09:03.252981+05:30	1	t	\N	f	f
32	CATEGORY	Category	Rent	135556	2022-09-20 14:09:03.253041+05:30	2022-09-20 14:09:03.25307+05:30	1	t	\N	f	f
33	CATEGORY	Category	Insurance	135591	2022-09-20 14:09:03.253221+05:30	2022-09-20 14:09:03.253263+05:30	1	t	\N	f	f
34	CATEGORY	Category	Repairs and Maintenance	135594	2022-09-20 14:09:03.25333+05:30	2022-09-20 14:09:03.253359+05:30	1	t	\N	f	f
35	CATEGORY	Category	Interest Expense	135621	2022-09-20 14:09:03.253421+05:30	2022-09-20 14:09:03.253451+05:30	1	t	\N	f	f
36	CATEGORY	Category	Advertising	135716	2022-09-20 14:09:03.253511+05:30	2022-09-20 14:09:03.253541+05:30	1	t	\N	f	f
37	CATEGORY	Category	Office Expenses	135742	2022-09-20 14:09:03.253632+05:30	2022-09-20 14:09:03.253677+05:30	1	t	\N	f	f
38	CATEGORY	Category	Purchases	135747	2022-09-20 14:09:03.254086+05:30	2022-09-20 14:09:03.254134+05:30	1	t	\N	f	f
39	CATEGORY	Category	Cost of Goods Sold	135910	2022-09-20 14:09:03.254605+05:30	2022-09-20 14:09:03.254737+05:30	1	t	\N	f	f
40	CATEGORY	Category	Bank Fees	135991	2022-09-20 14:09:03.254859+05:30	2022-09-20 14:09:03.254895+05:30	1	t	\N	f	f
41	CATEGORY	Category	Cleaning	135992	2022-09-20 14:09:03.254966+05:30	2022-09-20 14:09:03.254996+05:30	1	t	\N	f	f
42	CATEGORY	Category	Consulting & Accounting	135993	2022-09-20 14:09:03.255064+05:30	2022-09-20 14:09:03.2551+05:30	1	t	\N	f	f
43	CATEGORY	Category	Depreciation	135994	2022-09-20 14:09:03.255232+05:30	2022-09-20 14:09:03.255675+05:30	1	t	\N	f	f
44	CATEGORY	Category	Freight & Courier	135995	2022-09-20 14:09:03.255887+05:30	2022-09-20 14:09:03.255941+05:30	1	t	\N	f	f
45	CATEGORY	Category	General Expenses	135996	2022-09-20 14:09:03.256232+05:30	2022-09-20 14:09:03.256319+05:30	1	t	\N	f	f
20	CATEGORY	Category	Mileage	135452	2022-09-20 14:09:03.250996+05:30	2022-09-20 14:09:03.251038+05:30	1	t	\N	t	f
21	CATEGORY	Category	Per Diem	135454	2022-09-20 14:09:03.251154+05:30	2022-09-20 14:09:03.251197+05:30	1	t	\N	t	f
46	CATEGORY	Category	Legal expenses	135997	2022-09-20 14:09:03.25644+05:30	2022-09-20 14:09:03.256483+05:30	1	t	\N	f	f
47	CATEGORY	Category	Light, Power, Heating	135998	2022-09-20 14:09:03.256605+05:30	2022-09-20 14:09:03.256647+05:30	1	t	\N	f	f
48	CATEGORY	Category	Motor Vehicle Expenses	135999	2022-09-20 14:09:03.256754+05:30	2022-09-20 14:09:03.2568+05:30	1	t	\N	f	f
49	CATEGORY	Category	Printing & Stationery	136000	2022-09-20 14:09:03.257278+05:30	2022-09-20 14:09:03.257498+05:30	1	t	\N	f	f
50	CATEGORY	Category	Wages and Salaries	136001	2022-09-20 14:09:03.257661+05:30	2022-09-20 14:09:03.257702+05:30	1	t	\N	f	f
51	CATEGORY	Category	Superannuation	136002	2022-09-20 14:09:03.257791+05:30	2022-09-20 14:09:03.257821+05:30	1	t	\N	f	f
52	CATEGORY	Category	Subscriptions	136003	2022-09-20 14:09:03.257917+05:30	2022-09-20 14:09:03.25809+05:30	1	t	\N	f	f
53	CATEGORY	Category	Telephone & Internet	136004	2022-09-20 14:09:03.258317+05:30	2022-09-20 14:09:03.258371+05:30	1	t	\N	f	f
54	CATEGORY	Category	Travel - National	136005	2022-09-20 14:09:03.2585+05:30	2022-09-20 14:09:03.258545+05:30	1	t	\N	f	f
55	CATEGORY	Category	Travel - International	136006	2022-09-20 14:09:03.258774+05:30	2022-09-20 14:09:03.258809+05:30	1	t	\N	f	f
56	CATEGORY	Category	Bank Revaluations	136007	2022-09-20 14:09:03.258961+05:30	2022-09-20 14:09:03.258992+05:30	1	t	\N	f	f
57	CATEGORY	Category	Unrealised Currency Gains	136008	2022-09-20 14:09:03.259066+05:30	2022-09-20 14:09:03.259083+05:30	1	t	\N	f	f
58	CATEGORY	Category	Realised Currency Gains	136009	2022-09-20 14:09:03.259153+05:30	2022-09-20 14:09:03.259184+05:30	1	t	\N	f	f
59	CATEGORY	Category	Income Tax Expense	136010	2022-09-20 14:09:03.259538+05:30	2022-09-20 14:09:03.259582+05:30	1	t	\N	f	f
60	CATEGORY	Category	9KAP9QWA44 / Turbo charged	195547	2022-09-20 14:09:03.260113+05:30	2022-09-20 14:09:03.260391+05:30	1	t	\N	f	f
61	CATEGORY	Category	CUBSMXQ74V / Turbo charged	194407	2022-09-20 14:09:03.260555+05:30	2022-09-20 14:09:03.260593+05:30	1	t	\N	f	f
62	CATEGORY	Category	7TF6ZC4WT9 / Turbo charged	194406	2022-09-20 14:09:03.260696+05:30	2022-09-20 14:09:03.26074+05:30	1	t	\N	f	f
63	CATEGORY	Category	6W2VT8W7SC / Turbo charged	194401	2022-09-20 14:09:03.260851+05:30	2022-09-20 14:09:03.260891+05:30	1	t	\N	f	f
64	CATEGORY	Category	XKZTXD6J07 / Turbo charged	194400	2022-09-20 14:09:03.261027+05:30	2022-09-20 14:09:03.261772+05:30	1	t	\N	f	f
65	CATEGORY	Category	T5G8M4IVT8 / Turbo charged	194399	2022-09-20 14:09:03.261854+05:30	2022-09-20 14:09:03.261871+05:30	1	t	\N	f	f
66	CATEGORY	Category	MGCYQRWOJ8 / Turbo charged	194398	2022-09-20 14:09:03.261923+05:30	2022-09-20 14:09:03.261952+05:30	1	t	\N	f	f
67	CATEGORY	Category	GP2UXTORT6 / Turbo charged	194397	2022-09-20 14:09:03.262033+05:30	2022-09-20 14:09:03.262094+05:30	1	t	\N	f	f
68	CATEGORY	Category	M75YLYFLX2 / Turbo charged	194396	2022-09-20 14:09:03.329636+05:30	2022-09-20 14:09:03.329682+05:30	1	t	\N	f	f
69	CATEGORY	Category	E2ZA5DOLZP / Turbo charged	194395	2022-09-20 14:09:03.329927+05:30	2022-09-20 14:09:03.33875+05:30	1	t	\N	f	f
70	CATEGORY	Category	N234JZCM07 / Turbo charged	194394	2022-09-20 14:09:03.338857+05:30	2022-09-20 14:09:03.338889+05:30	1	t	\N	f	f
71	CATEGORY	Category	VNISXKB26C / Turbo charged	194393	2022-09-20 14:09:03.338952+05:30	2022-09-20 14:09:03.338982+05:30	1	t	\N	f	f
72	CATEGORY	Category	JYJHRR8B69 / Turbo charged	194359	2022-09-20 14:09:03.339043+05:30	2022-09-20 14:09:03.339073+05:30	1	t	\N	f	f
73	CATEGORY	Category	OONDUAK3WT / Turbo charged	194332	2022-09-20 14:09:03.34269+05:30	2022-09-20 14:09:03.34275+05:30	1	t	\N	f	f
74	CATEGORY	Category	Q5OGEJBTKM / Turbo charged	194314	2022-09-20 14:09:03.342842+05:30	2022-09-20 14:09:03.342874+05:30	1	t	\N	f	f
75	CATEGORY	Category	SOYMBT74SM / Turbo charged	194302	2022-09-20 14:09:03.346765+05:30	2022-09-20 14:09:03.346885+05:30	1	t	\N	f	f
76	CATEGORY	Category	1PKB8P46QU / Turbo charged	194251	2022-09-20 14:09:03.349897+05:30	2022-09-20 14:09:03.349946+05:30	1	t	\N	f	f
77	CATEGORY	Category	R3BO0U5YZF / Turbo charged	194245	2022-09-20 14:09:03.350028+05:30	2022-09-20 14:09:03.350059+05:30	1	t	\N	f	f
78	CATEGORY	Category	Workers Compensation	193901	2022-09-20 14:09:03.35022+05:30	2022-09-20 14:09:03.350246+05:30	1	t	\N	f	f
79	CATEGORY	Category	Cost of Labor	193902	2022-09-20 14:09:03.350308+05:30	2022-09-20 14:09:03.350338+05:30	1	t	\N	f	f
80	CATEGORY	Category	Installation	193903	2022-09-20 14:09:03.35355+05:30	2022-09-20 14:09:03.354077+05:30	1	t	\N	f	f
81	CATEGORY	Category	Maintenance and Repairs	193904	2022-09-20 14:09:03.354328+05:30	2022-09-20 14:09:03.354365+05:30	1	t	\N	f	f
82	CATEGORY	Category	Job Materials	193905	2022-09-20 14:09:03.354428+05:30	2022-09-20 14:09:03.354449+05:30	1	t	\N	f	f
83	CATEGORY	Category	Decks and Patios	193906	2022-09-20 14:09:03.354501+05:30	2022-09-20 14:09:03.37025+05:30	1	t	\N	f	f
84	CATEGORY	Category	Fountain and Garden Lighting	193907	2022-09-20 14:09:03.37036+05:30	2022-09-20 14:09:03.370385+05:30	1	t	\N	f	f
85	CATEGORY	Category	Plants and Soil	193908	2022-09-20 14:09:03.370962+05:30	2022-09-20 14:09:03.371006+05:30	1	t	\N	f	f
86	CATEGORY	Category	Sprinklers and Drip Systems	193909	2022-09-20 14:09:03.371075+05:30	2022-09-20 14:09:03.371104+05:30	1	t	\N	f	f
87	CATEGORY	Category	Permits	193910	2022-09-20 14:09:03.371165+05:30	2022-09-20 14:09:03.371195+05:30	1	t	\N	f	f
88	CATEGORY	Category	Bookkeeper	193911	2022-09-20 14:09:03.371255+05:30	2022-09-20 14:09:03.371306+05:30	1	t	\N	f	f
89	CATEGORY	Category	Lawyer	193912	2022-09-20 14:09:03.371505+05:30	2022-09-20 14:09:03.371529+05:30	1	t	\N	f	f
90	CATEGORY	Category	Building Repairs	193913	2022-09-20 14:09:03.371625+05:30	2022-09-20 14:09:03.371656+05:30	1	t	\N	f	f
91	CATEGORY	Category	Computer Repairs	193914	2022-09-20 14:09:03.372043+05:30	2022-09-20 14:09:03.372065+05:30	1	t	\N	f	f
92	CATEGORY	Category	Equipment Repairs	193915	2022-09-20 14:09:03.372118+05:30	2022-09-20 14:09:03.372148+05:30	1	t	\N	f	f
93	CATEGORY	Category	Gas and Electric	193916	2022-09-20 14:09:03.37221+05:30	2022-09-20 14:09:03.372239+05:30	1	t	\N	f	f
94	CATEGORY	Category	Telephone	193917	2022-09-20 14:09:03.372303+05:30	2022-09-20 14:09:03.372333+05:30	1	t	\N	f	f
95	CATEGORY	Category	xero prod	193480	2022-09-20 14:09:03.372419+05:30	2022-09-20 14:09:03.372449+05:30	1	t	\N	f	f
96	CATEGORY	Category	Sravan Expense Account	192749	2022-09-20 14:09:03.372537+05:30	2022-09-20 14:09:03.372566+05:30	1	t	\N	f	f
128	CATEGORY	Category	Uncategorised Expense	147505	2022-09-20 14:09:03.419866+05:30	2022-09-20 14:09:03.419907+05:30	1	t	\N	f	f
129	CATEGORY	Category	Utilities - Electric & Gas	147506	2022-09-20 14:09:03.420004+05:30	2022-09-20 14:09:03.420044+05:30	1	t	\N	f	f
130	CATEGORY	Category	Utilities - Water	147507	2022-09-20 14:09:03.420138+05:30	2022-09-20 14:09:03.420178+05:30	1	t	\N	f	f
131	CATEGORY	Category	Wage expenses	147508	2022-09-20 14:09:03.420272+05:30	2022-09-20 14:09:03.420312+05:30	1	t	\N	f	f
132	CATEGORY	Category	Amortisation (and depreciation) expense	147479	2022-09-20 14:09:03.420405+05:30	2022-09-20 14:09:03.420446+05:30	1	t	\N	f	f
133	CATEGORY	Category	Bad debts	147480	2022-09-20 14:09:03.420674+05:30	2022-09-20 14:09:03.42301+05:30	1	t	\N	f	f
134	CATEGORY	Category	BAS Expense	147482	2022-09-20 14:09:03.423123+05:30	2022-09-20 14:09:03.425598+05:30	1	t	\N	f	f
135	CATEGORY	Category	Commissions and fees	147483	2022-09-20 14:09:03.425923+05:30	2022-09-20 14:09:03.425981+05:30	1	t	\N	f	f
136	CATEGORY	Category	Communication Expense - Fixed	147484	2022-09-20 14:09:03.426099+05:30	2022-09-20 14:09:03.426144+05:30	1	t	\N	f	f
137	CATEGORY	Category	Insurance - Disability	147488	2022-09-20 14:09:03.42624+05:30	2022-09-20 14:09:03.426283+05:30	1	t	\N	f	f
138	CATEGORY	Category	Insurance - General	147489	2022-09-20 14:09:03.426384+05:30	2022-09-20 14:09:03.427194+05:30	1	t	\N	f	f
139	CATEGORY	Category	Insurance - Liability	147490	2022-09-20 14:09:03.4273+05:30	2022-09-20 14:09:03.428789+05:30	1	t	\N	f	f
140	CATEGORY	Category	Legal and professional fees	147492	2022-09-20 14:09:03.428884+05:30	2022-09-20 14:09:03.428915+05:30	1	t	\N	f	f
141	CATEGORY	Category	Loss on discontinued operations, net of tax	147493	2022-09-20 14:09:03.428979+05:30	2022-09-20 14:09:03.429009+05:30	1	t	\N	f	f
142	CATEGORY	Category	Management compensation	147494	2022-09-20 14:09:03.429071+05:30	2022-09-20 14:09:03.429101+05:30	1	t	\N	f	f
143	CATEGORY	Category	Other general and administrative expenses	147497	2022-09-20 14:09:03.429163+05:30	2022-09-20 14:09:03.429192+05:30	1	t	\N	f	f
144	CATEGORY	Category	Other selling expenses	147498	2022-09-20 14:09:03.429254+05:30	2022-09-20 14:09:03.429284+05:30	1	t	\N	f	f
145	CATEGORY	Category	Other Types of Expenses-Advertising Expenses	147499	2022-09-20 14:09:03.429344+05:30	2022-09-20 14:09:03.429374+05:30	1	t	\N	f	f
146	CATEGORY	Category	Rent or lease payments	147500	2022-09-20 14:09:03.429435+05:30	2022-09-20 14:09:03.429464+05:30	1	t	\N	f	f
147	CATEGORY	Category	Shipping and delivery expense	147501	2022-09-20 14:09:03.429524+05:30	2022-09-20 14:09:03.429554+05:30	1	t	\N	f	f
148	CATEGORY	Category	Stationery and printing	147502	2022-09-20 14:09:03.429614+05:30	2022-09-20 14:09:03.429643+05:30	1	t	\N	f	f
149	CATEGORY	Category	Travel expenses - general and admin expenses	147503	2022-09-20 14:09:03.429704+05:30	2022-09-20 14:09:03.429734+05:30	1	t	\N	f	f
150	CATEGORY	Category	Office Supplies	135448	2022-09-20 14:09:03.429795+05:30	2022-09-20 14:09:03.429825+05:30	1	t	\N	f	f
151	CATEGORY	Category	Movies	145416	2022-09-20 14:09:03.429886+05:30	2022-09-20 14:09:03.429915+05:30	1	t	\N	f	f
152	CATEGORY	Category	Dues Expenses from Intacct	141965	2022-09-20 14:09:03.429976+05:30	2022-09-20 14:09:03.430005+05:30	1	t	\N	f	f
153	CATEGORY	Category	Workers' compensation	135887	2022-09-20 14:09:03.430066+05:30	2022-09-20 14:09:03.430096+05:30	1	t	\N	f	f
154	CATEGORY	Category	Disability	135888	2022-09-20 14:09:03.430438+05:30	2022-09-20 14:09:03.431988+05:30	1	t	\N	f	f
155	CATEGORY	Category	Miscellaneous Expense	135889	2022-09-20 14:09:03.432079+05:30	2022-09-20 14:09:03.432108+05:30	1	t	\N	f	f
156	CATEGORY	Category	Office Expense	135890	2022-09-20 14:09:03.43217+05:30	2022-09-20 14:09:03.432199+05:30	1	t	\N	f	f
157	CATEGORY	Category	Outside Services	135891	2022-09-20 14:09:03.43226+05:30	2022-09-20 14:09:03.432289+05:30	1	t	\N	f	f
158	CATEGORY	Category	Postage & Delivery	135892	2022-09-20 14:09:03.432363+05:30	2022-09-20 14:09:03.432392+05:30	1	t	\N	f	f
159	CATEGORY	Category	Professional Fees	135893	2022-09-20 14:09:03.432453+05:30	2022-09-20 14:09:03.432482+05:30	1	t	\N	f	f
160	CATEGORY	Category	Rent Expense	135894	2022-09-20 14:09:03.432542+05:30	2022-09-20 14:09:03.432571+05:30	1	t	\N	f	f
161	CATEGORY	Category	Repairs & Maintenance	135895	2022-09-20 14:09:03.432631+05:30	2022-09-20 14:09:03.43266+05:30	1	t	\N	f	f
162	CATEGORY	Category	Supplies Expense	135896	2022-09-20 14:09:03.432721+05:30	2022-09-20 14:09:03.43275+05:30	1	t	\N	f	f
163	CATEGORY	Category	Taxes & Licenses-Other	135897	2022-09-20 14:09:03.43281+05:30	2022-09-20 14:09:03.43284+05:30	1	t	\N	f	f
164	CATEGORY	Category	Business	135898	2022-09-20 14:09:03.4329+05:30	2022-09-20 14:09:03.432929+05:30	1	t	\N	f	f
165	CATEGORY	Category	Property	135899	2022-09-20 14:09:03.43299+05:30	2022-09-20 14:09:03.433019+05:30	1	t	\N	f	f
166	CATEGORY	Category	Vehicle Registration	135900	2022-09-20 14:09:03.433079+05:30	2022-09-20 14:09:03.433108+05:30	1	t	\N	f	f
167	CATEGORY	Category	Telephone Expense	135901	2022-09-20 14:09:03.433168+05:30	2022-09-20 14:09:03.433197+05:30	1	t	\N	f	f
168	CATEGORY	Category	Regular Service	135902	2022-09-20 14:09:03.45076+05:30	2022-09-20 14:09:03.450802+05:30	1	t	\N	f	f
169	CATEGORY	Category	Pager	135903	2022-09-20 14:09:03.450865+05:30	2022-09-20 14:09:03.450895+05:30	1	t	\N	f	f
170	CATEGORY	Category	Cellular	135904	2022-09-20 14:09:03.450956+05:30	2022-09-20 14:09:03.450985+05:30	1	t	\N	f	f
171	CATEGORY	Category	Online Fees	135905	2022-09-20 14:09:03.451045+05:30	2022-09-20 14:09:03.451078+05:30	1	t	\N	f	f
172	CATEGORY	Category	Gain (loss) on Sale of Assets	135906	2022-09-20 14:09:03.45114+05:30	2022-09-20 14:09:03.451169+05:30	1	t	\N	f	f
173	CATEGORY	Category	Salaries & Wages Expense	135907	2022-09-20 14:09:03.45123+05:30	2022-09-20 14:09:03.451259+05:30	1	t	\N	f	f
174	CATEGORY	Category	Advances Paid	135908	2022-09-20 14:09:03.45132+05:30	2022-09-20 14:09:03.451349+05:30	1	t	\N	f	f
175	CATEGORY	Category	Inventory Asset	135909	2022-09-20 14:09:03.451409+05:30	2022-09-20 14:09:03.451438+05:30	1	t	\N	f	f
176	CATEGORY	Category	Furniture & Fixtures Expense	135911	2022-09-20 14:09:03.451499+05:30	2022-09-20 14:09:03.451528+05:30	1	t	\N	f	f
177	CATEGORY	Category	Accounting	135912	2022-09-20 14:09:03.451588+05:30	2022-09-20 14:09:03.451618+05:30	1	t	\N	f	f
179	CATEGORY	Category	Exchange Rate Variance	135914	2022-09-20 14:09:03.451768+05:30	2022-09-20 14:09:03.451797+05:30	1	t	\N	f	f
180	CATEGORY	Category	Duty Expense	135915	2022-09-20 14:09:03.451857+05:30	2022-09-20 14:09:03.451887+05:30	1	t	\N	f	f
181	CATEGORY	Category	Freight Expense	135916	2022-09-20 14:09:03.451947+05:30	2022-09-20 14:09:03.451976+05:30	1	t	\N	f	f
182	CATEGORY	Category	Inventory Returned Not Credited	135917	2022-09-20 14:09:03.452931+05:30	2022-09-20 14:09:03.453006+05:30	1	t	\N	f	f
183	CATEGORY	Category	Damaged Goods	135918	2022-09-20 14:09:03.453815+05:30	2022-09-20 14:09:03.454107+05:30	1	t	\N	f	f
184	CATEGORY	Category	Inventory Write Offs	135919	2022-09-20 14:09:03.45418+05:30	2022-09-20 14:09:03.454211+05:30	1	t	\N	f	f
185	CATEGORY	Category	Inventory In Transit	135920	2022-09-20 14:09:03.454273+05:30	2022-09-20 14:09:03.454303+05:30	1	t	\N	f	f
186	CATEGORY	Category	Bill Quantity Variance	135921	2022-09-20 14:09:03.454365+05:30	2022-09-20 14:09:03.454394+05:30	1	t	\N	f	f
187	CATEGORY	Category	Bill Price Variance	135922	2022-09-20 14:09:03.454455+05:30	2022-09-20 14:09:03.454704+05:30	1	t	\N	f	f
188	CATEGORY	Category	Job Expenses:Equipment Rental	135726	2022-09-20 14:09:03.454943+05:30	2022-09-20 14:09:03.45498+05:30	1	t	\N	f	f
189	CATEGORY	Category	Job Expenses:Job Materials	135727	2022-09-20 14:09:03.455042+05:30	2022-09-20 14:09:03.45508+05:30	1	t	\N	f	f
190	CATEGORY	Category	Job Expenses:Job Materials:Decks and Patios	135728	2022-09-20 14:09:03.455139+05:30	2022-09-20 14:09:03.455161+05:30	1	t	\N	f	f
191	CATEGORY	Category	Job Expenses:Job Materials:Fountain and Garden Lighting	135729	2022-09-20 14:09:03.455226+05:30	2022-09-20 14:09:03.455245+05:30	1	t	\N	f	f
192	CATEGORY	Category	Job Expenses:Job Materials:Plants and Soil	135730	2022-09-20 14:09:03.455297+05:30	2022-09-20 14:09:03.455451+05:30	1	t	\N	f	f
193	CATEGORY	Category	Job Expenses:Job Materials:Sprinklers and Drip Systems	135731	2022-09-20 14:09:03.455542+05:30	2022-09-20 14:09:03.455908+05:30	1	t	\N	f	f
194	CATEGORY	Category	Job Expenses:Permits	135732	2022-09-20 14:09:03.456373+05:30	2022-09-20 14:09:03.456414+05:30	1	t	\N	f	f
195	CATEGORY	Category	Legal & Professional Fees	135733	2022-09-20 14:09:03.456526+05:30	2022-09-20 14:09:03.456663+05:30	1	t	\N	f	f
196	CATEGORY	Category	Legal & Professional Fees:Accounting	135734	2022-09-20 14:09:03.456744+05:30	2022-09-20 14:09:03.456773+05:30	1	t	\N	f	f
197	CATEGORY	Category	Legal & Professional Fees:Bookkeeper	135735	2022-09-20 14:09:03.456835+05:30	2022-09-20 14:09:03.456864+05:30	1	t	\N	f	f
198	CATEGORY	Category	Legal & Professional Fees:Lawyer	135736	2022-09-20 14:09:03.456925+05:30	2022-09-20 14:09:03.456954+05:30	1	t	\N	f	f
199	CATEGORY	Category	Maintenance and Repair	135737	2022-09-20 14:09:03.457054+05:30	2022-09-20 14:09:03.457112+05:30	1	t	\N	f	f
200	CATEGORY	Category	Maintenance and Repair:Building Repairs	135738	2022-09-20 14:09:03.457644+05:30	2022-09-20 14:09:03.457679+05:30	1	t	\N	f	f
201	CATEGORY	Category	Maintenance and Repair:Computer Repairs	135739	2022-09-20 14:09:03.457742+05:30	2022-09-20 14:09:03.457771+05:30	1	t	\N	f	f
202	CATEGORY	Category	Maintenance and Repair:Equipment Repairs	135740	2022-09-20 14:09:03.457823+05:30	2022-09-20 14:09:03.457844+05:30	1	t	\N	f	f
203	CATEGORY	Category	Office-General Administrative Expenses	135745	2022-09-20 14:09:03.458018+05:30	2022-09-20 14:09:03.458061+05:30	1	t	\N	f	f
204	CATEGORY	Category	Promotional	135746	2022-09-20 14:09:03.458126+05:30	2022-09-20 14:09:03.45815+05:30	1	t	\N	f	f
205	CATEGORY	Category	Rent or Lease	135748	2022-09-20 14:09:03.458202+05:30	2022-09-20 14:09:03.45899+05:30	1	t	\N	f	f
206	CATEGORY	Category	Stationery & Printing	135749	2022-09-20 14:09:03.459128+05:30	2022-09-20 14:09:03.459171+05:30	1	t	\N	f	f
207	CATEGORY	Category	Supplies Test 2	135750	2022-09-20 14:09:03.460106+05:30	2022-09-20 14:09:03.46023+05:30	1	t	\N	f	f
208	CATEGORY	Category	Taxes & Licenses	135751	2022-09-20 14:09:03.46074+05:30	2022-09-20 14:09:03.460773+05:30	1	t	\N	f	f
209	CATEGORY	Category	Test Staging	135753	2022-09-20 14:09:03.460824+05:30	2022-09-20 14:09:03.460845+05:30	1	t	\N	f	f
210	CATEGORY	Category	Insurance:Workers Compensation	135754	2022-09-20 14:09:03.460906+05:30	2022-09-20 14:09:03.460935+05:30	1	t	\N	f	f
211	CATEGORY	Category	Job Expenses	135755	2022-09-20 14:09:03.461141+05:30	2022-09-20 14:09:03.46118+05:30	1	t	\N	f	f
212	CATEGORY	Category	Job Expenses:Cost of Labor	135756	2022-09-20 14:09:03.461252+05:30	2022-09-20 14:09:03.461282+05:30	1	t	\N	f	f
213	CATEGORY	Category	Travel Meals	135757	2022-09-20 14:09:03.461365+05:30	2022-09-20 14:09:03.461394+05:30	1	t	\N	f	f
214	CATEGORY	Category	Unapplied Cash Bill Payment Expense	135758	2022-09-20 14:09:03.461455+05:30	2022-09-20 14:09:03.461476+05:30	1	t	\N	f	f
215	CATEGORY	Category	Uncategorized Expense	135759	2022-09-20 14:09:03.461528+05:30	2022-09-20 14:09:03.461549+05:30	1	t	\N	f	f
216	CATEGORY	Category	Utilities:Gas and Electric	135760	2022-09-20 14:09:03.46161+05:30	2022-09-20 14:09:03.461639+05:30	1	t	\N	f	f
217	CATEGORY	Category	Utilities:Telephone	135761	2022-09-20 14:09:03.4617+05:30	2022-09-20 14:09:03.46313+05:30	1	t	\N	f	f
218	CATEGORY	Category	Prepaid Expenses	135871	2022-09-20 14:09:05.126669+05:30	2022-09-20 14:09:05.126718+05:30	1	t	\N	f	f
219	CATEGORY	Category	Prepaid Income Taxes	135872	2022-09-20 14:09:05.126792+05:30	2022-09-20 14:09:05.126819+05:30	1	t	\N	f	f
220	CATEGORY	Category	Note Receivable-Current	135873	2022-09-20 14:09:05.126881+05:30	2022-09-20 14:09:05.126931+05:30	1	t	\N	f	f
221	CATEGORY	Category	Merchandise	135874	2022-09-20 14:09:05.145405+05:30	2022-09-20 14:09:05.145453+05:30	1	t	\N	f	f
222	CATEGORY	Category	Service	135875	2022-09-20 14:09:05.145526+05:30	2022-09-20 14:09:05.145556+05:30	1	t	\N	f	f
223	CATEGORY	Category	Salaries & Wages	135876	2022-09-20 14:09:05.145618+05:30	2022-09-20 14:09:05.145647+05:30	1	t	\N	f	f
224	CATEGORY	Category	Other Direct Costs	135877	2022-09-20 14:09:05.145769+05:30	2022-09-20 14:09:05.145803+05:30	1	t	\N	f	f
225	CATEGORY	Category	Inventory Variance	135878	2022-09-20 14:09:05.145875+05:30	2022-09-20 14:09:05.145897+05:30	1	t	\N	f	f
226	CATEGORY	Category	Automobile Expense	135879	2022-09-20 14:09:05.14596+05:30	2022-09-20 14:09:05.14598+05:30	1	t	\N	f	f
227	CATEGORY	Category	Gas & Oil	135880	2022-09-20 14:09:05.146042+05:30	2022-09-20 14:09:05.146063+05:30	1	t	\N	f	f
228	CATEGORY	Category	Repairs	135881	2022-09-20 14:09:05.146115+05:30	2022-09-20 14:09:05.146144+05:30	1	t	\N	f	f
229	CATEGORY	Category	Bank Service Charges	135882	2022-09-20 14:09:05.146304+05:30	2022-09-20 14:09:05.146324+05:30	1	t	\N	f	f
230	CATEGORY	Category	Contributions	135883	2022-09-20 14:09:05.146376+05:30	2022-09-20 14:09:05.146405+05:30	1	t	\N	f	f
231	CATEGORY	Category	Freight & Delivery	135884	2022-09-20 14:09:05.146466+05:30	2022-09-20 14:09:05.146495+05:30	1	t	\N	f	f
232	CATEGORY	Category	Insurance Expense	135885	2022-09-20 14:09:05.14655+05:30	2022-09-20 14:09:05.146571+05:30	1	t	\N	f	f
233	CATEGORY	Category	Liability	135886	2022-09-20 14:09:05.146632+05:30	2022-09-20 14:09:05.146661+05:30	1	t	\N	f	f
234	CATEGORY	Category	ASHWIN MANUALLY ADDED THIS2	135550	2022-09-20 14:09:05.146721+05:30	2022-09-20 14:09:05.146744+05:30	1	t	\N	f	f
235	CATEGORY	Category	Fyle	135551	2022-09-20 14:09:05.146795+05:30	2022-09-20 14:09:05.146816+05:30	1	t	\N	f	f
236	CATEGORY	Category	Furniture & Fixtures	135612	2022-09-20 14:09:05.146876+05:30	2022-09-20 14:09:05.146898+05:30	1	t	\N	f	f
237	CATEGORY	Category	Accm.Depr. Furniture & Fixtures	135613	2022-09-20 14:09:05.14695+05:30	2022-09-20 14:09:05.146971+05:30	1	t	\N	f	f
238	CATEGORY	Category	Deferred Revenue Contra	135614	2022-09-20 14:09:05.147023+05:30	2022-09-20 14:09:05.147052+05:30	1	t	\N	f	f
239	CATEGORY	Category	Deferred Revenue	135615	2022-09-20 14:09:05.147112+05:30	2022-09-20 14:09:05.147141+05:30	1	t	\N	f	f
240	CATEGORY	Category	Due to Entity 300	135616	2022-09-20 14:09:05.147196+05:30	2022-09-20 14:09:05.147217+05:30	1	t	\N	f	f
241	CATEGORY	Category	Due to Entity 100	135617	2022-09-20 14:09:05.147268+05:30	2022-09-20 14:09:05.147386+05:30	1	t	\N	f	f
242	CATEGORY	Category	Due to Entity 200	135618	2022-09-20 14:09:05.147441+05:30	2022-09-20 14:09:05.147461+05:30	1	t	\N	f	f
243	CATEGORY	Category	Intercompany Payables	135619	2022-09-20 14:09:05.147522+05:30	2022-09-20 14:09:05.147551+05:30	1	t	\N	f	f
244	CATEGORY	Category	Interest Income	135620	2022-09-20 14:09:05.147603+05:30	2022-09-20 14:09:05.147615+05:30	1	t	\N	f	f
245	CATEGORY	Category	Intercompany Professional Fees	135622	2022-09-20 14:09:05.147657+05:30	2022-09-20 14:09:05.147678+05:30	1	t	\N	f	f
246	CATEGORY	Category	Amortization Expense	135623	2022-09-20 14:09:05.147738+05:30	2022-09-20 14:09:05.147767+05:30	1	t	\N	f	f
247	CATEGORY	Category	Revenue - Other	135624	2022-09-20 14:09:05.147827+05:30	2022-09-20 14:09:05.147856+05:30	1	t	\N	f	f
248	CATEGORY	Category	Payroll Taxes	135625	2022-09-20 14:09:05.147912+05:30	2022-09-20 14:09:05.147932+05:30	1	t	\N	f	f
249	CATEGORY	Category	Inventory	135626	2022-09-20 14:09:05.147993+05:30	2022-09-20 14:09:05.148022+05:30	1	t	\N	f	f
250	CATEGORY	Category	Inventory-Other	135627	2022-09-20 14:09:05.148083+05:30	2022-09-20 14:09:05.148106+05:30	1	t	\N	f	f
251	CATEGORY	Category	Inventory-Kits	135628	2022-09-20 14:09:05.148158+05:30	2022-09-20 14:09:05.148187+05:30	1	t	\N	f	f
252	CATEGORY	Category	Other Intangible Assets	135629	2022-09-20 14:09:05.152885+05:30	2022-09-20 14:09:05.152917+05:30	1	t	\N	f	f
253	CATEGORY	Category	Other Assets	135630	2022-09-20 14:09:05.15298+05:30	2022-09-20 14:09:05.153009+05:30	1	t	\N	f	f
254	CATEGORY	Category	COGS-Damage, Scrap, Spoilage	135635	2022-09-20 14:09:05.15307+05:30	2022-09-20 14:09:05.153098+05:30	1	t	\N	f	f
255	CATEGORY	Category	Excise Tax	135636	2022-09-20 14:09:05.153158+05:30	2022-09-20 14:09:05.153187+05:30	1	t	\N	f	f
256	CATEGORY	Category	Other Taxes	135637	2022-09-20 14:09:05.153247+05:30	2022-09-20 14:09:05.153276+05:30	1	t	\N	f	f
257	CATEGORY	Category	Other Expense	135638	2022-09-20 14:09:05.153336+05:30	2022-09-20 14:09:05.153365+05:30	1	t	\N	f	f
258	CATEGORY	Category	Other Income	135639	2022-09-20 14:09:05.153425+05:30	2022-09-20 14:09:05.153454+05:30	1	t	\N	f	f
259	CATEGORY	Category	AR-Retainage	135640	2022-09-20 14:09:05.153514+05:30	2022-09-20 14:09:05.153543+05:30	1	t	\N	f	f
260	CATEGORY	Category	Accounts Receivable	135641	2022-09-20 14:09:05.153603+05:30	2022-09-20 14:09:05.153632+05:30	1	t	\N	f	f
261	CATEGORY	Category	Accounts Receivable - Other	135642	2022-09-20 14:09:05.153692+05:30	2022-09-20 14:09:05.153721+05:30	1	t	\N	f	f
262	CATEGORY	Category	Accounts Payable - Employees	135643	2022-09-20 14:09:05.153782+05:30	2022-09-20 14:09:05.153811+05:30	1	t	\N	f	f
263	CATEGORY	Category	Accounts Payable	135644	2022-09-20 14:09:05.153871+05:30	2022-09-20 14:09:05.1539+05:30	1	t	\N	f	f
264	CATEGORY	Category	Software and Licenses	135645	2022-09-20 14:09:05.154337+05:30	2022-09-20 14:09:05.15437+05:30	1	t	\N	f	f
265	CATEGORY	Category	Utilities	135646	2022-09-20 14:09:05.158632+05:30	2022-09-20 14:09:05.158712+05:30	1	t	\N	f	f
266	CATEGORY	Category	ASHWIN MANUALLY ADDED THIS	135647	2022-09-20 14:09:05.15888+05:30	2022-09-20 14:09:05.158995+05:30	1	t	\N	f	f
267	CATEGORY	Category	Fyleasdads	135648	2022-09-20 14:09:05.159067+05:30	2022-09-20 14:09:05.159097+05:30	1	t	\N	f	f
268	CATEGORY	Category	Fyle Expenses	135652	2022-09-20 14:09:05.192844+05:30	2022-09-20 14:09:05.192885+05:30	1	t	\N	f	f
269	CATEGORY	Category	Fyle Expenses!	135655	2022-09-20 14:09:05.192949+05:30	2022-09-20 14:09:05.192979+05:30	1	t	\N	f	f
271	CATEGORY	Category	Automobile:Fuel	135718	2022-09-20 14:09:05.193129+05:30	2022-09-20 14:09:05.193158+05:30	1	t	\N	f	f
272	CATEGORY	Category	Commissions & fees	135719	2022-09-20 14:09:05.193219+05:30	2022-09-20 14:09:05.193248+05:30	1	t	\N	f	f
273	CATEGORY	Category	Disposal Fees	135720	2022-09-20 14:09:05.193546+05:30	2022-09-20 14:09:05.193587+05:30	1	t	\N	f	f
274	CATEGORY	Category	Dues & Subscriptions	135721	2022-09-20 14:09:05.193645+05:30	2022-09-20 14:09:05.193674+05:30	1	t	\N	f	f
275	CATEGORY	Category	Incremental Account	135723	2022-09-20 14:09:05.193735+05:30	2022-09-20 14:09:05.193771+05:30	1	t	\N	f	f
276	CATEGORY	Category	Job Expenses:Cost of Labor:Installation	135724	2022-09-20 14:09:05.193839+05:30	2022-09-20 14:09:05.193868+05:30	1	t	\N	f	f
277	CATEGORY	Category	Job Expenses:Cost of Labor:Maintenance and Repairs	135725	2022-09-20 14:09:05.193959+05:30	2022-09-20 14:09:05.193984+05:30	1	t	\N	f	f
278	CATEGORY	Category	Office Party	135462	2022-09-20 14:09:05.194037+05:30	2022-09-20 14:09:05.194063+05:30	1	t	\N	f	f
279	CATEGORY	Category	Flight	135463	2022-09-20 14:09:05.194115+05:30	2022-09-20 14:09:05.194136+05:30	1	t	\N	f	f
280	CATEGORY	Category	Software	135464	2022-09-20 14:09:05.194196+05:30	2022-09-20 14:09:05.194225+05:30	1	t	\N	f	f
281	CATEGORY	Category	Parking	135465	2022-09-20 14:09:05.194285+05:30	2022-09-20 14:09:05.194314+05:30	1	t	\N	f	f
282	CATEGORY	Category	Toll Charge	135466	2022-09-20 14:09:05.194375+05:30	2022-09-20 14:09:05.194404+05:30	1	t	\N	f	f
283	CATEGORY	Category	Tax	135467	2022-09-20 14:09:05.194464+05:30	2022-09-20 14:09:05.194687+05:30	1	t	\N	f	f
284	CATEGORY	Category	Training	135468	2022-09-20 14:09:05.196104+05:30	2022-09-20 14:09:05.196136+05:30	1	t	\N	f	f
285	CATEGORY	Category	Prepaid Insurance	135571	2022-09-20 14:09:05.196199+05:30	2022-09-20 14:09:05.196228+05:30	1	t	\N	f	f
286	CATEGORY	Category	Prepaid Rent	135572	2022-09-20 14:09:05.201638+05:30	2022-09-20 14:09:05.201693+05:30	1	t	\N	f	f
287	CATEGORY	Category	Prepaid Other	135573	2022-09-20 14:09:05.201779+05:30	2022-09-20 14:09:05.20181+05:30	1	t	\N	f	f
288	CATEGORY	Category	Employee Advances	135574	2022-09-20 14:09:05.201876+05:30	2022-09-20 14:09:05.201911+05:30	1	t	\N	f	f
289	CATEGORY	Category	Salaries Payable	135575	2022-09-20 14:09:05.201974+05:30	2022-09-20 14:09:05.202001+05:30	1	t	\N	f	f
290	CATEGORY	Category	Goods Received Not Invoiced (GRNI)	135576	2022-09-20 14:09:05.202044+05:30	2022-09-20 14:09:05.202062+05:30	1	t	\N	f	f
291	CATEGORY	Category	Estimated Landed Costs	135577	2022-09-20 14:09:05.202107+05:30	2022-09-20 14:09:05.202128+05:30	1	t	\N	f	f
292	CATEGORY	Category	Actual Landed Costs	135578	2022-09-20 14:09:05.202188+05:30	2022-09-20 14:09:05.20376+05:30	1	t	\N	f	f
293	CATEGORY	Category	Accrued Payroll Tax Payable	135579	2022-09-20 14:09:05.204396+05:30	2022-09-20 14:09:05.20444+05:30	1	t	\N	f	f
294	CATEGORY	Category	Accrued Sales Tax Payable	135580	2022-09-20 14:09:05.216346+05:30	2022-09-20 14:09:05.216391+05:30	1	t	\N	f	f
295	CATEGORY	Category	Company Credit Card Offset	135581	2022-09-20 14:09:05.216478+05:30	2022-09-20 14:09:05.216838+05:30	1	t	\N	f	f
296	CATEGORY	Category	Telecommunication Expense	135582	2022-09-20 14:09:05.217382+05:30	2022-09-20 14:09:05.217414+05:30	1	t	\N	f	f
297	CATEGORY	Category	Employee Deductions	135583	2022-09-20 14:09:05.21748+05:30	2022-09-20 14:09:05.21751+05:30	1	t	\N	f	f
298	CATEGORY	Category	Goodwill	135584	2022-09-20 14:09:05.217616+05:30	2022-09-20 14:09:05.217643+05:30	1	t	\N	f	f
299	CATEGORY	Category	Depreciation Expense	135585	2022-09-20 14:09:05.217705+05:30	2022-09-20 14:09:05.217826+05:30	1	t	\N	f	f
300	CATEGORY	Category	Revenue - Accessories	135586	2022-09-20 14:09:05.22703+05:30	2022-09-20 14:09:05.227054+05:30	1	t	\N	f	f
301	CATEGORY	Category	Revenue - Entry	135587	2022-09-20 14:09:05.227109+05:30	2022-09-20 14:09:05.228641+05:30	1	t	\N	f	f
302	CATEGORY	Category	Revenue - Surveillance	135588	2022-09-20 14:09:05.230883+05:30	2022-09-20 14:09:05.230913+05:30	1	t	\N	f	f
303	CATEGORY	Category	Marketing and Advertising	135589	2022-09-20 14:09:05.23097+05:30	2022-09-20 14:09:05.230991+05:30	1	t	\N	f	f
304	CATEGORY	Category	Trade Shows and Exhibits	135590	2022-09-20 14:09:05.231643+05:30	2022-09-20 14:09:05.231677+05:30	1	t	\N	f	f
305	CATEGORY	Category	Professional Fees Expense	135592	2022-09-20 14:09:05.23175+05:30	2022-09-20 14:09:05.23178+05:30	1	t	\N	f	f
306	CATEGORY	Category	Salaries and Wages	135595	2022-09-20 14:09:05.233143+05:30	2022-09-20 14:09:05.247716+05:30	1	t	\N	f	f
307	CATEGORY	Category	Gain for Sale of an asset	135596	2022-09-20 14:09:05.248035+05:30	2022-09-20 14:09:05.248064+05:30	1	t	\N	f	f
308	CATEGORY	Category	Dividends	135597	2022-09-20 14:09:05.248125+05:30	2022-09-20 14:09:05.248155+05:30	1	t	\N	f	f
309	CATEGORY	Category	SVB Checking	135598	2022-09-20 14:09:05.248226+05:30	2022-09-20 14:09:05.248257+05:30	1	t	\N	f	f
310	CATEGORY	Category	SVB Checking 2	135599	2022-09-20 14:09:05.248319+05:30	2022-09-20 14:09:05.248493+05:30	1	t	\N	f	f
311	CATEGORY	Category	Cash	135601	2022-09-20 14:09:05.248558+05:30	2022-09-20 14:09:05.248587+05:30	1	t	\N	f	f
312	CATEGORY	Category	Cash Equivalents	135602	2022-09-20 14:09:05.248645+05:30	2022-09-20 14:09:05.248666+05:30	1	t	\N	f	f
313	CATEGORY	Category	Investments and Securities	135603	2022-09-20 14:09:05.248719+05:30	2022-09-20 14:09:05.248736+05:30	1	t	\N	f	f
314	CATEGORY	Category	Due from Entity 200	135604	2022-09-20 14:09:05.248786+05:30	2022-09-20 14:09:05.248816+05:30	1	t	\N	f	f
315	CATEGORY	Category	Due from Entity 300	135605	2022-09-20 14:09:05.248887+05:30	2022-09-20 14:09:05.248916+05:30	1	t	\N	f	f
316	CATEGORY	Category	Due from Entity 100	135606	2022-09-20 14:09:05.248978+05:30	2022-09-20 14:09:05.249005+05:30	1	t	\N	f	f
317	CATEGORY	Category	Intercompany Receivables	135607	2022-09-20 14:09:05.249154+05:30	2022-09-20 14:09:05.249197+05:30	1	t	\N	f	f
318	CATEGORY	Category	Capitalized Software Costs	135608	2022-09-20 14:09:05.264043+05:30	2022-09-20 14:09:05.264112+05:30	1	t	\N	f	f
319	CATEGORY	Category	Buildings Accm.Depr.	135609	2022-09-20 14:09:05.264448+05:30	2022-09-20 14:09:05.264533+05:30	1	t	\N	f	f
320	CATEGORY	Category	Machinery & Equipment	135610	2022-09-20 14:09:05.264741+05:30	2022-09-20 14:09:05.264836+05:30	1	t	\N	f	f
321	CATEGORY	Category	Machinery & Equipment Accm.Depr.	135611	2022-09-20 14:09:05.265052+05:30	2022-09-20 14:09:05.265075+05:30	1	t	\N	f	f
322	CATEGORY	Category	Snacks	135447	2022-09-20 14:09:05.265125+05:30	2022-09-20 14:09:05.265146+05:30	1	t	\N	f	f
323	CATEGORY	Category	Utility	135449	2022-09-20 14:09:05.265236+05:30	2022-09-20 14:09:05.265266+05:30	1	t	\N	f	f
324	CATEGORY	Category	Others	135451	2022-09-20 14:09:05.265329+05:30	2022-09-20 14:09:05.265356+05:30	1	t	\N	f	f
326	CATEGORY	Category	Bus	135455	2022-09-20 14:09:05.26577+05:30	2022-09-20 14:09:05.265841+05:30	1	t	\N	f	f
328	CATEGORY	Category	Courier	135458	2022-09-20 14:09:05.276799+05:30	2022-09-20 14:09:05.27723+05:30	1	t	\N	f	f
329	CATEGORY	Category	Hotel	135459	2022-09-20 14:09:05.27731+05:30	2022-09-20 14:09:05.277332+05:30	1	t	\N	f	f
330	CATEGORY	Category	Professional Services	135460	2022-09-20 14:09:05.277386+05:30	2022-09-20 14:09:05.277406+05:30	1	t	\N	f	f
331	CATEGORY	Category	Phone	135461	2022-09-20 14:09:05.277459+05:30	2022-09-20 14:09:05.279024+05:30	1	t	\N	f	f
332	CATEGORY	Category	Travel Expenses which supports National - International	135542	2022-09-20 14:09:05.279713+05:30	2022-09-20 14:09:05.279758+05:30	1	t	\N	f	f
333	CATEGORY	Category	Bad Debt Expense	135544	2022-09-20 14:09:05.279837+05:30	2022-09-20 14:09:05.279868+05:30	1	t	\N	f	f
327	CATEGORY	Category	Taxi	135457	2022-09-20 14:09:05.276717+05:30	2022-09-28 17:26:20.660976+05:30	1	t	\N	f	f
334	CATEGORY	Category	Travel	135545	2022-09-20 14:09:05.279951+05:30	2022-09-20 14:09:05.279975+05:30	1	t	\N	f	f
335	CATEGORY	Category	Notes Payable	135546	2022-09-20 14:09:05.280029+05:30	2022-09-20 14:09:05.280216+05:30	1	t	\N	f	f
336	CATEGORY	Category	Employee Benefits	135553	2022-09-20 14:09:05.281702+05:30	2022-09-20 14:09:05.281781+05:30	1	t	\N	f	f
337	CATEGORY	Category	Commission	135554	2022-09-20 14:09:05.281872+05:30	2022-09-20 14:09:05.281902+05:30	1	t	\N	f	f
338	CATEGORY	Category	Office Suppliesdfsd	135555	2022-09-20 14:09:05.281946+05:30	2022-09-20 14:09:05.281968+05:30	1	t	\N	f	f
339	CATEGORY	Category	COGS Services	135557	2022-09-20 14:09:05.282026+05:30	2022-09-20 14:09:05.282047+05:30	1	t	\N	f	f
340	CATEGORY	Category	COGS-Billable Hours	135558	2022-09-20 14:09:05.282109+05:30	2022-09-20 14:09:05.28214+05:30	1	t	\N	f	f
341	CATEGORY	Category	Labor Cost Variance	135559	2022-09-20 14:09:05.282205+05:30	2022-09-20 14:09:05.282527+05:30	1	t	\N	f	f
342	CATEGORY	Category	Labor Cost Offset	135560	2022-09-20 14:09:05.282922+05:30	2022-09-20 14:09:05.283128+05:30	1	t	\N	f	f
343	CATEGORY	Category	COGS-Non-Billable Hours	135561	2022-09-20 14:09:05.283983+05:30	2022-09-20 14:09:05.284194+05:30	1	t	\N	f	f
344	CATEGORY	Category	COGS-Burden on Projects	135562	2022-09-20 14:09:05.284281+05:30	2022-09-20 14:09:05.284312+05:30	1	t	\N	f	f
345	CATEGORY	Category	COGS-Overhead on Projects	135563	2022-09-20 14:09:05.284375+05:30	2022-09-20 14:09:05.284398+05:30	1	t	\N	f	f
346	CATEGORY	Category	COGS-G&A on Projects	135564	2022-09-20 14:09:05.284446+05:30	2022-09-20 14:09:05.284467+05:30	1	t	\N	f	f
347	CATEGORY	Category	COGS-Indirect projects Costs Offset	135565	2022-09-20 14:09:05.284527+05:30	2022-09-20 14:09:05.284557+05:30	1	t	\N	f	f
348	CATEGORY	Category	COGS-Reimbursed Expenses	135566	2022-09-20 14:09:05.285097+05:30	2022-09-20 14:09:05.285146+05:30	1	t	\N	f	f
349	CATEGORY	Category	COGS-Other	135569	2022-09-20 14:09:05.285212+05:30	2022-09-20 14:09:05.285234+05:30	1	t	\N	f	f
350	CATEGORY	Category	Payroll Expenses	135541	2022-09-20 14:09:05.285299+05:30	2022-09-20 14:09:05.285321+05:30	1	t	\N	f	f
351	CATEGORY	Category	Payroll Expense	135540	2022-09-20 14:09:05.285384+05:30	2022-09-20 14:09:05.285794+05:30	1	t	\N	f	f
352	CATEGORY	Category	Spot Bonus	135537	2022-09-20 14:09:05.285886+05:30	2022-09-20 14:09:05.286085+05:30	1	t	\N	f	f
353	CATEGORY	Category	Other G&A	135538	2022-09-20 14:09:05.28698+05:30	2022-09-20 14:09:05.287035+05:30	1	t	\N	f	f
354	CATEGORY	Category	Buildings	135539	2022-09-20 14:09:05.287123+05:30	2022-09-20 14:09:05.287151+05:30	1	t	\N	f	f
355	CATEGORY	Category	Dues and Expenses from Intacct	141657	2022-09-20 14:09:05.287398+05:30	2022-09-20 14:09:05.294211+05:30	1	t	\N	f	f
356	CATEGORY	Category	Supplies	145002	2022-09-20 14:09:05.294534+05:30	2022-09-20 14:09:05.294679+05:30	1	t	\N	f	f
357	CATEGORY	Category	Sync Expense Account	145003	2022-09-20 14:09:05.294753+05:30	2022-09-20 14:09:05.294775+05:30	1	t	\N	f	f
358	CATEGORY	Category	Netflix	146042	2022-09-20 14:09:05.294835+05:30	2022-09-20 14:09:05.294857+05:30	1	t	\N	f	f
359	CATEGORY	Category	Emma	146043	2022-09-20 14:09:05.294916+05:30	2022-09-20 14:09:05.294937+05:30	1	t	\N	f	f
360	CATEGORY	Category	Description about 00	137942	2022-09-20 14:09:05.294992+05:30	2022-09-20 14:09:05.295012+05:30	1	t	\N	f	f
361	CATEGORY	Category	Description about ASHWIN MANUALLY ADDED THIS	137943	2022-09-20 14:09:05.296144+05:30	2022-09-20 14:09:05.296218+05:30	1	t	\N	f	f
362	CATEGORY	Category	Description about ASHWIN MANUALLY ADDED THIS2	137944	2022-09-20 14:09:05.296307+05:30	2022-09-20 14:09:05.296333+05:30	1	t	\N	f	f
363	CATEGORY	Category	Furniture for the department	137945	2022-09-20 14:09:05.296897+05:30	2022-09-20 14:09:05.296936+05:30	1	t	\N	f	f
364	CATEGORY	Category	Equipment	137947	2022-09-20 14:09:05.297658+05:30	2022-09-20 14:09:05.298733+05:30	1	t	\N	f	f
365	CATEGORY	Category	Travel Expenses	137948	2022-09-20 14:09:05.301454+05:30	2022-09-20 14:09:05.301506+05:30	1	t	\N	f	f
366	CATEGORY	Category	test	137949	2022-09-20 14:09:05.302162+05:30	2022-09-20 14:09:05.302194+05:30	1	t	\N	f	f
367	CATEGORY	Category	WIP COGS	135931	2022-09-20 14:09:05.317972+05:30	2022-09-20 14:09:05.318031+05:30	1	t	\N	f	f
368	CATEGORY	Category	Mfg WIP	135932	2022-09-20 14:09:05.383194+05:30	2022-09-20 14:09:05.383226+05:30	1	t	\N	f	f
369	CATEGORY	Category	Purchase Price Variance	135933	2022-09-20 14:09:05.383276+05:30	2022-09-20 14:09:05.383298+05:30	1	t	\N	f	f
370	CATEGORY	Category	Build Price Variance	135934	2022-09-20 14:09:05.383694+05:30	2022-09-20 14:09:05.383833+05:30	1	t	\N	f	f
371	CATEGORY	Category	Build Quantity Variance	135935	2022-09-20 14:09:05.383901+05:30	2022-09-20 14:09:05.383923+05:30	1	t	\N	f	f
372	CATEGORY	Category	Vendor Rebates	135936	2022-09-20 14:09:05.383991+05:30	2022-09-20 14:09:05.384015+05:30	1	t	\N	f	f
373	CATEGORY	Category	Customer Return Variance	135937	2022-09-20 14:09:05.384065+05:30	2022-09-20 14:09:05.384087+05:30	1	t	\N	f	f
374	CATEGORY	Category	Vendor Return Variance	135938	2022-09-20 14:09:05.38415+05:30	2022-09-20 14:09:05.384178+05:30	1	t	\N	f	f
375	CATEGORY	Category	Mfg Scrap	135939	2022-09-20 14:09:05.38423+05:30	2022-09-20 14:09:05.384711+05:30	1	t	\N	f	f
376	CATEGORY	Category	Manufacturing Expenses	135940	2022-09-20 14:09:05.384854+05:30	2022-09-20 14:09:05.384939+05:30	1	t	\N	f	f
377	CATEGORY	Category	Labor	135941	2022-09-20 14:09:05.385003+05:30	2022-09-20 14:09:05.385024+05:30	1	t	\N	f	f
378	CATEGORY	Category	Labor Burden	135942	2022-09-20 14:09:05.385086+05:30	2022-09-20 14:09:05.385106+05:30	1	t	\N	f	f
379	CATEGORY	Category	Machine	135943	2022-09-20 14:09:05.385158+05:30	2022-09-20 14:09:05.385178+05:30	1	t	\N	f	f
380	CATEGORY	Category	Machine Burden	135944	2022-09-20 14:09:05.385231+05:30	2022-09-20 14:09:05.385252+05:30	1	t	\N	f	f
381	CATEGORY	Category	WIP Variance	135945	2022-09-20 14:09:05.385301+05:30	2022-09-20 14:09:05.385312+05:30	1	t	\N	f	f
382	CATEGORY	Category	ash	135946	2022-09-20 14:09:05.385355+05:30	2022-09-20 14:09:05.385375+05:30	1	t	\N	f	f
383	CATEGORY	Category	sub ash	135947	2022-09-20 14:09:05.385436+05:30	2022-09-20 14:09:05.385456+05:30	1	t	\N	f	f
384	CATEGORY	Category	Undeposited Funds	135868	2022-09-20 14:09:05.385506+05:30	2022-09-20 14:09:05.385516+05:30	1	t	\N	f	f
385	CATEGORY	Category	Other Receivables	135870	2022-09-20 14:09:05.385567+05:30	2022-09-20 14:09:05.385588+05:30	1	t	\N	f	f
386	CATEGORY	Category	Bill Exchange Rate Variance	135923	2022-09-20 14:09:05.385639+05:30	2022-09-20 14:09:05.38566+05:30	1	t	\N	f	f
387	CATEGORY	Category	Inventory Transfer Price Gain - Loss	135924	2022-09-20 14:09:05.385721+05:30	2022-09-20 14:09:05.385741+05:30	1	t	\N	f	f
388	CATEGORY	Category	Unbuild Variance	135925	2022-09-20 14:09:05.385791+05:30	2022-09-20 14:09:05.385812+05:30	1	t	\N	f	f
389	CATEGORY	Category	Rounding Gain-Loss	135926	2022-09-20 14:09:05.385872+05:30	2022-09-20 14:09:05.385892+05:30	1	t	\N	f	f
390	CATEGORY	Category	Realized Gain-Loss	135927	2022-09-20 14:09:05.385943+05:30	2022-09-20 14:09:05.385964+05:30	1	t	\N	f	f
391	CATEGORY	Category	Unrealized Gain-Loss	135928	2022-09-20 14:09:05.386024+05:30	2022-09-20 14:09:05.386045+05:30	1	t	\N	f	f
392	CATEGORY	Category	WIP	135929	2022-09-20 14:09:05.386095+05:30	2022-09-20 14:09:05.386105+05:30	1	t	\N	f	f
393	CATEGORY	Category	WIP Revenue	135930	2022-09-20 14:09:05.391399+05:30	2022-09-20 14:09:05.391464+05:30	1	t	\N	f	f
394	CATEGORY	Category	Integration Test Account	135794	2022-09-20 14:09:05.391628+05:30	2022-09-20 14:09:05.391679+05:30	1	t	\N	f	f
395	CATEGORY	Category	Travelling Charges	135795	2022-09-20 14:09:05.392393+05:30	2022-09-20 14:09:05.392471+05:30	1	t	\N	f	f
396	CATEGORY	Category	expense category	135797	2022-09-20 14:09:05.39286+05:30	2022-09-20 14:09:05.392929+05:30	1	t	\N	f	f
397	CATEGORY	Category	Cellular Phone	135792	2022-09-20 14:09:05.393+05:30	2022-09-20 14:09:05.393021+05:30	1	t	\N	f	f
398	CATEGORY	Category	Meals & Entertainment	135793	2022-09-20 14:09:05.393082+05:30	2022-09-20 14:09:05.393103+05:30	1	t	\N	f	f
399	CATEGORY	Category	Allowance For Doubtful Accounts	135570	2022-09-20 14:09:05.393164+05:30	2022-09-20 14:09:05.393184+05:30	1	t	\N	f	f
400	CATEGORY	Category	Office Supplies 2	135744	2022-09-20 14:09:05.393236+05:30	2022-09-20 14:09:05.393257+05:30	1	t	\N	f	f
401	CATEGORY	Category	Common Stock	135631	2022-09-20 14:09:05.393307+05:30	2022-09-20 14:09:05.393328+05:30	1	t	\N	f	f
402	CATEGORY	Category	Preferred Stock	135632	2022-09-20 14:09:05.393379+05:30	2022-09-20 14:09:05.393399+05:30	1	t	\N	f	f
403	CATEGORY	Category	Retained Earnings	135633	2022-09-20 14:09:05.39346+05:30	2022-09-20 14:09:05.39348+05:30	1	t	\N	f	f
404	CATEGORY	Category	COGS Sales	135634	2022-09-20 14:09:05.393529+05:30	2022-09-20 14:09:05.39354+05:30	1	t	\N	f	f
405	CATEGORY	Category	SVB Checking 3	135600	2022-09-20 14:09:05.39358+05:30	2022-09-20 14:09:05.393601+05:30	1	t	\N	f	f
406	CATEGORY	Category	Activity	135444	2022-09-20 14:09:05.393651+05:30	2022-09-20 14:09:05.393672+05:30	1	t	\N	f	f
407	CATEGORY	Category	Train	135445	2022-09-20 14:09:05.393732+05:30	2022-09-20 14:09:05.393753+05:30	1	t	\N	f	f
408	CATEGORY	Category	Allocations	135549	2022-09-20 14:09:05.393805+05:30	2022-09-20 14:09:05.393825+05:30	1	t	\N	f	f
409	CATEGORY	Category	Patents & Licenses	135552	2022-09-20 14:09:05.393874+05:30	2022-09-20 14:09:05.393885+05:30	1	t	\N	f	f
410	CATEGORY	Category	Accumulated OCI	135547	2022-09-20 14:09:05.393925+05:30	2022-09-20 14:09:05.393946+05:30	1	t	\N	f	f
411	CATEGORY	Category	Goods in Transit	135548	2022-09-20 14:09:05.394006+05:30	2022-09-20 14:09:05.394026+05:30	1	t	\N	f	f
412	CATEGORY	Category	UI777ZUG5P / Turbo charged	191853	2022-09-20 14:09:05.394076+05:30	2022-09-20 14:09:05.394097+05:30	1	t	\N	f	f
413	CATEGORY	Category	747DS1JYZB / Turbo charged	191852	2022-09-20 14:09:05.394157+05:30	2022-09-20 14:09:05.394177+05:30	1	t	\N	f	f
414	CATEGORY	Category	C72U5RL80N / Turbo charged	191851	2022-09-20 14:09:05.39422+05:30	2022-09-20 14:09:05.39424+05:30	1	t	\N	f	f
415	CATEGORY	Category	BNDNQCGL2A / Turbo charged	191850	2022-09-20 14:09:05.394301+05:30	2022-09-20 14:09:05.394322+05:30	1	t	\N	f	f
416	CATEGORY	Category	R6KJ5YA4U9 / Turbo charged	191848	2022-09-20 14:09:05.394374+05:30	2022-09-20 14:09:05.394746+05:30	1	t	\N	f	f
417	CATEGORY	Category	D1IO8OGBJ7 / Turbo charged	191847	2022-09-20 14:09:05.394814+05:30	2022-09-20 14:09:05.394843+05:30	1	t	\N	f	f
418	CATEGORY	Category	XEC9NORGDY / Turbo charged	191846	2022-09-20 14:09:05.952614+05:30	2022-09-20 14:09:05.952721+05:30	1	t	\N	f	f
419	CATEGORY	Category	DWK2H94RM7 / Turbo charged	191845	2022-09-20 14:09:05.952995+05:30	2022-09-20 14:09:05.953033+05:30	1	t	\N	f	f
420	CATEGORY	Category	IZJZZ3S9E7 / Turbo charged	191844	2022-09-20 14:09:05.953124+05:30	2022-09-20 14:09:05.953718+05:30	1	t	\N	f	f
421	CATEGORY	Category	0215IGBNYP / Turbo charged	191842	2022-09-20 14:09:05.954232+05:30	2022-09-20 14:09:05.954605+05:30	1	t	\N	f	f
422	CATEGORY	Category	1SBDCCFM3Q / Turbo charged	191841	2022-09-20 14:09:05.961483+05:30	2022-09-20 14:09:05.961526+05:30	1	t	\N	f	f
423	CATEGORY	Category	EOHGT9QJO4 / Turbo charged	191840	2022-09-20 14:09:05.961594+05:30	2022-09-20 14:09:05.961624+05:30	1	t	\N	f	f
424	CATEGORY	Category	NXPD1U8GHJ / Turbo charged	191813	2022-09-20 14:09:05.96169+05:30	2022-09-20 14:09:05.961722+05:30	1	t	\N	f	f
425	CATEGORY	Category	27Z4X2C201 / Turbo charged	191812	2022-09-20 14:09:05.963735+05:30	2022-09-20 14:09:05.963799+05:30	1	t	\N	f	f
426	CATEGORY	Category	CDGMCX2GYA / Turbo charged	191811	2022-09-20 14:09:05.965777+05:30	2022-09-20 14:09:05.965829+05:30	1	t	\N	f	f
427	CATEGORY	Category	JVFYUUP52V / Turbo charged	191810	2022-09-20 14:09:05.967202+05:30	2022-09-20 14:09:05.967358+05:30	1	t	\N	f	f
428	CATEGORY	Category	GG10QAP2S5 / Turbo charged	191809	2022-09-20 14:09:05.967575+05:30	2022-09-20 14:09:05.967614+05:30	1	t	\N	f	f
429	CATEGORY	Category	AAHWZOY5QZ / Turbo charged	191808	2022-09-20 14:09:05.967872+05:30	2022-09-20 14:09:05.967906+05:30	1	t	\N	f	f
430	CATEGORY	Category	6QLNH6Y4UM / Turbo charged	191807	2022-09-20 14:09:05.967967+05:30	2022-09-20 14:09:05.967988+05:30	1	t	\N	f	f
431	CATEGORY	Category	RHTSGJD4CV / Turbo charged	191806	2022-09-20 14:09:05.96804+05:30	2022-09-20 14:09:05.968053+05:30	1	t	\N	f	f
432	CATEGORY	Category	W6RV83BFWU / Turbo charged	191805	2022-09-20 14:09:05.968622+05:30	2022-09-20 14:09:05.968711+05:30	1	t	\N	f	f
433	CATEGORY	Category	ZIZU1AAHLF / Turbo charged	191804	2022-09-20 14:09:05.968836+05:30	2022-09-20 14:09:05.968877+05:30	1	t	\N	f	f
434	CATEGORY	Category	WRVEPSQLUO / Turbo charged	191803	2022-09-20 14:09:05.970364+05:30	2022-09-20 14:09:05.971616+05:30	1	t	\N	f	f
435	CATEGORY	Category	G5HSJNY9V8 / Turbo charged	191802	2022-09-20 14:09:05.973651+05:30	2022-09-20 14:09:05.973711+05:30	1	t	\N	f	f
436	CATEGORY	Category	FDU2ZPCGV4 / Turbo charged	191801	2022-09-20 14:09:05.975713+05:30	2022-09-20 14:09:05.97575+05:30	1	t	\N	f	f
437	CATEGORY	Category	Q230CP6HS8 / Turbo charged	191800	2022-09-20 14:09:05.975816+05:30	2022-09-20 14:09:05.975847+05:30	1	t	\N	f	f
438	CATEGORY	Category	SVWPR6H082 / Turbo charged	191799	2022-09-20 14:09:05.976067+05:30	2022-09-20 14:09:05.976101+05:30	1	t	\N	f	f
439	CATEGORY	Category	49BVB05MSS / Turbo charged	191798	2022-09-20 14:09:05.976165+05:30	2022-09-20 14:09:05.976194+05:30	1	t	\N	f	f
440	CATEGORY	Category	T5AOOEOIMJ / Turbo charged	191797	2022-09-20 14:09:05.976256+05:30	2022-09-20 14:09:05.976286+05:30	1	t	\N	f	f
441	CATEGORY	Category	03QBRUQL9Y / Turbo charged	191796	2022-09-20 14:09:05.976348+05:30	2022-09-20 14:09:05.976377+05:30	1	t	\N	f	f
442	CATEGORY	Category	MTD7QH6N7D / Turbo charged	191795	2022-09-20 14:09:05.976457+05:30	2022-09-20 14:09:05.980467+05:30	1	t	\N	f	f
443	CATEGORY	Category	RGUG2EU1X7 / Turbo charged	191794	2022-09-20 14:09:05.9806+05:30	2022-09-20 14:09:05.98062+05:30	1	t	\N	f	f
444	CATEGORY	Category	5JHCVQD5SS / Turbo charged	191793	2022-09-20 14:09:05.980675+05:30	2022-09-20 14:09:05.980706+05:30	1	t	\N	f	f
445	CATEGORY	Category	YO63CHLCBF / Turbo charged	191792	2022-09-20 14:09:05.980758+05:30	2022-09-20 14:09:05.980779+05:30	1	t	\N	f	f
446	CATEGORY	Category	2CSL18LRX5 / Turbo charged	191791	2022-09-20 14:09:05.980841+05:30	2022-09-20 14:09:05.980873+05:30	1	t	\N	f	f
447	CATEGORY	Category	LQEK36KCCF / Turbo charged	191790	2022-09-20 14:09:05.981057+05:30	2022-09-20 14:09:05.981435+05:30	1	t	\N	f	f
448	CATEGORY	Category	OT0WPR3LG1 / Turbo charged	191789	2022-09-20 14:09:05.981667+05:30	2022-09-20 14:09:05.981698+05:30	1	t	\N	f	f
449	CATEGORY	Category	YG9ZHOW03L / Turbo charged	191788	2022-09-20 14:09:05.981762+05:30	2022-09-20 14:09:05.981792+05:30	1	t	\N	f	f
450	CATEGORY	Category	9Q25F572X1 / Turbo charged	191787	2022-09-20 14:09:05.982043+05:30	2022-09-20 14:09:05.982077+05:30	1	t	\N	f	f
451	CATEGORY	Category	XNJ6IYQTT6 / Turbo charged	191786	2022-09-20 14:09:05.982142+05:30	2022-09-20 14:09:05.983429+05:30	1	t	\N	f	f
452	CATEGORY	Category	EGJMQFKSKM / Turbo charged	191785	2022-09-20 14:09:06.001358+05:30	2022-09-20 14:09:06.001407+05:30	1	t	\N	f	f
453	CATEGORY	Category	T1WP4WBELF / Turbo charged	191784	2022-09-20 14:09:06.001607+05:30	2022-09-20 14:09:06.001696+05:30	1	t	\N	f	f
454	CATEGORY	Category	MAUZTC2I53 / Turbo charged	191783	2022-09-20 14:09:06.001833+05:30	2022-09-20 14:09:06.00186+05:30	1	t	\N	f	f
455	CATEGORY	Category	TG1OG645TP / Turbo charged	191782	2022-09-20 14:09:06.001957+05:30	2022-09-20 14:09:06.002009+05:30	1	t	\N	f	f
456	CATEGORY	Category	X4R0A458J3 / Turbo charged	191781	2022-09-20 14:09:06.00257+05:30	2022-09-20 14:09:06.002617+05:30	1	t	\N	f	f
457	CATEGORY	Category	OUR0YT9KBK / Turbo charged	191780	2022-09-20 14:09:06.002692+05:30	2022-09-20 14:09:06.002763+05:30	1	t	\N	f	f
458	CATEGORY	Category	F0YGCWO5PP / Turbo charged	191779	2022-09-20 14:09:06.002978+05:30	2022-09-20 14:09:06.003013+05:30	1	t	\N	f	f
459	CATEGORY	Category	USD4J624GO / Turbo charged	191778	2022-09-20 14:09:06.003154+05:30	2022-09-20 14:09:06.003359+05:30	1	t	\N	f	f
460	CATEGORY	Category	0UDWEKF5QQ / Turbo charged	191777	2022-09-20 14:09:06.003448+05:30	2022-09-20 14:09:06.003472+05:30	1	t	\N	f	f
461	CATEGORY	Category	JQTAKMBYNJ / Turbo charged	191776	2022-09-20 14:09:06.003548+05:30	2022-09-20 14:09:06.003622+05:30	1	t	\N	f	f
462	CATEGORY	Category	1NIPCD4AIV / Turbo charged	191775	2022-09-20 14:09:06.004412+05:30	2022-09-20 14:09:06.004479+05:30	1	t	\N	f	f
463	CATEGORY	Category	95FDDT0ADR / Turbo charged	191774	2022-09-20 14:09:06.004746+05:30	2022-09-20 14:09:06.004778+05:30	1	t	\N	f	f
464	CATEGORY	Category	LW8V0C86U9 / Turbo charged	191773	2022-09-20 14:09:06.004843+05:30	2022-09-20 14:09:06.004864+05:30	1	t	\N	f	f
465	CATEGORY	Category	SBNNYXHGJM / Turbo charged	191772	2022-09-20 14:09:06.004925+05:30	2022-09-20 14:09:06.004946+05:30	1	t	\N	f	f
466	CATEGORY	Category	OEZ61NIBGN / Turbo charged	191771	2022-09-20 14:09:06.005035+05:30	2022-09-20 14:09:06.005084+05:30	1	t	\N	f	f
467	CATEGORY	Category	YA65ILOGVV / Turbo charged	191770	2022-09-20 14:09:06.005417+05:30	2022-09-20 14:09:06.005451+05:30	1	t	\N	f	f
468	CATEGORY	Category	Z9EDD2VZC3 / Turbo charged	191769	2022-09-20 14:09:06.054787+05:30	2022-09-20 14:09:06.054841+05:30	1	t	\N	f	f
469	CATEGORY	Category	I4XUSD23KB / Turbo charged	191768	2022-09-20 14:09:06.055069+05:30	2022-09-20 14:09:06.055192+05:30	1	t	\N	f	f
470	CATEGORY	Category	PNSOA0VKSF / Turbo charged	191767	2022-09-20 14:09:06.055481+05:30	2022-09-20 14:09:06.055515+05:30	1	t	\N	f	f
471	CATEGORY	Category	RBJU6PV6UZ / Turbo charged	191766	2022-09-20 14:09:06.055593+05:30	2022-09-20 14:09:06.055627+05:30	1	t	\N	f	f
472	CATEGORY	Category	PO4UXUPB2Z / Turbo charged	191765	2022-09-20 14:09:06.055812+05:30	2022-09-20 14:09:06.055901+05:30	1	t	\N	f	f
473	CATEGORY	Category	DM7138IDE2 / Turbo charged	191764	2022-09-20 14:09:06.056048+05:30	2022-09-20 14:09:06.056085+05:30	1	t	\N	f	f
474	CATEGORY	Category	PMNG0N8KSZ / Turbo charged	191763	2022-09-20 14:09:06.056207+05:30	2022-09-20 14:09:06.056251+05:30	1	t	\N	f	f
475	CATEGORY	Category	36TEBIWA0N / Turbo charged	191762	2022-09-20 14:09:06.056399+05:30	2022-09-20 14:09:06.056446+05:30	1	t	\N	f	f
476	CATEGORY	Category	GWNYCAUI7U / Turbo charged	191761	2022-09-20 14:09:06.05654+05:30	2022-09-20 14:09:06.056589+05:30	1	t	\N	f	f
477	CATEGORY	Category	XBBEZH9O4N / Turbo charged	191760	2022-09-20 14:09:06.057215+05:30	2022-09-20 14:09:06.058558+05:30	1	t	\N	f	f
478	CATEGORY	Category	HBKP7A0DNR / Turbo charged	191759	2022-09-20 14:09:06.059893+05:30	2022-09-20 14:09:06.059969+05:30	1	t	\N	f	f
479	CATEGORY	Category	7ZAAQDCQQN / Turbo charged	191758	2022-09-20 14:09:06.060193+05:30	2022-09-20 14:09:06.060452+05:30	1	t	\N	f	f
480	CATEGORY	Category	5DNCP094R0 / Turbo charged	191757	2022-09-20 14:09:06.060697+05:30	2022-09-20 14:09:06.060734+05:30	1	t	\N	f	f
481	CATEGORY	Category	LCU8INQONN / Turbo charged	191756	2022-09-20 14:09:06.060832+05:30	2022-09-20 14:09:06.060879+05:30	1	t	\N	f	f
482	CATEGORY	Category	DWU8MKBQEV / Turbo charged	191755	2022-09-20 14:09:06.060977+05:30	2022-09-20 14:09:06.061017+05:30	1	t	\N	f	f
483	CATEGORY	Category	O020KR52QV / Turbo charged	191754	2022-09-20 14:09:06.061109+05:30	2022-09-20 14:09:06.061146+05:30	1	t	\N	f	f
484	CATEGORY	Category	SNB8I4896F / Turbo charged	191753	2022-09-20 14:09:06.061225+05:30	2022-09-20 14:09:06.061259+05:30	1	t	\N	f	f
485	CATEGORY	Category	ZSGKDU3OLB / Turbo charged	191752	2022-09-20 14:09:06.061334+05:30	2022-09-20 14:09:06.06136+05:30	1	t	\N	f	f
486	CATEGORY	Category	XN7QJZBTGW / Turbo charged	191751	2022-09-20 14:09:06.06143+05:30	2022-09-20 14:09:06.061459+05:30	1	t	\N	f	f
487	CATEGORY	Category	Q17J4DV6PY / Turbo charged	191750	2022-09-20 14:09:06.061548+05:30	2022-09-20 14:09:06.061587+05:30	1	t	\N	f	f
488	CATEGORY	Category	VEU3R97JU6 / Turbo charged	191749	2022-09-20 14:09:06.06206+05:30	2022-09-20 14:09:06.062659+05:30	1	t	\N	f	f
489	CATEGORY	Category	H4FLZPRDRU / Turbo charged	191748	2022-09-20 14:09:06.062769+05:30	2022-09-20 14:09:06.0628+05:30	1	t	\N	f	f
490	CATEGORY	Category	MQ3MHKG1JM / Turbo charged	191747	2022-09-20 14:09:06.062852+05:30	2022-09-20 14:09:06.062872+05:30	1	t	\N	f	f
491	CATEGORY	Category	OPUXX1NWJD / Turbo charged	191746	2022-09-20 14:09:06.062913+05:30	2022-09-20 14:09:06.062935+05:30	1	t	\N	f	f
492	CATEGORY	Category	XZXC2AN5UM / Turbo charged	191745	2022-09-20 14:09:06.063156+05:30	2022-09-20 14:09:06.063333+05:30	1	t	\N	f	f
493	CATEGORY	Category	9GO0WXN6RN / Turbo charged	191744	2022-09-20 14:09:06.063648+05:30	2022-09-20 14:09:06.063694+05:30	1	t	\N	f	f
494	CATEGORY	Category	FYW3N2Z4G1 / Turbo charged	191743	2022-09-20 14:09:06.064358+05:30	2022-09-20 14:09:06.064406+05:30	1	t	\N	f	f
495	CATEGORY	Category	M0P4RTHRRA / Turbo charged	191742	2022-09-20 14:09:06.064615+05:30	2022-09-20 14:09:06.064667+05:30	1	t	\N	f	f
496	CATEGORY	Category	M8MES6DZKB / Turbo charged	191741	2022-09-20 14:09:06.064748+05:30	2022-09-20 14:09:06.064911+05:30	1	t	\N	f	f
497	CATEGORY	Category	2WN3XRLS6H / Turbo charged	191740	2022-09-20 14:09:06.065064+05:30	2022-09-20 14:09:06.06509+05:30	1	t	\N	f	f
498	CATEGORY	Category	8RJGQU3LBA / Turbo charged	191739	2022-09-20 14:09:06.065159+05:30	2022-09-20 14:09:06.065789+05:30	1	t	\N	f	f
499	CATEGORY	Category	6RTQSGGVBB / Turbo charged	191738	2022-09-20 14:09:06.066294+05:30	2022-09-20 14:09:06.066939+05:30	1	t	\N	f	f
500	CATEGORY	Category	71DTN3JPS4 / Turbo charged	191737	2022-09-20 14:09:06.067156+05:30	2022-09-20 14:09:06.067313+05:30	1	t	\N	f	f
501	CATEGORY	Category	QE0PQSDQPB / Turbo charged	191736	2022-09-20 14:09:06.069064+05:30	2022-09-20 14:09:06.069117+05:30	1	t	\N	f	f
502	CATEGORY	Category	CD5C1P0EBC / Turbo charged	191735	2022-09-20 14:09:06.069189+05:30	2022-09-20 14:09:06.069219+05:30	1	t	\N	f	f
503	CATEGORY	Category	4CF762Q721 / Turbo charged	191734	2022-09-20 14:09:06.069296+05:30	2022-09-20 14:09:06.069326+05:30	1	t	\N	f	f
504	CATEGORY	Category	62WRSSZKV3 / Turbo charged	191733	2022-09-20 14:09:06.069389+05:30	2022-09-20 14:09:06.069418+05:30	1	t	\N	f	f
505	CATEGORY	Category	XNNLG4CWVK / Turbo charged	191732	2022-09-20 14:09:06.06948+05:30	2022-09-20 14:09:06.069508+05:30	1	t	\N	f	f
506	CATEGORY	Category	6HEKYZATT2 / Turbo charged	191731	2022-09-20 14:09:06.06957+05:30	2022-09-20 14:09:06.069599+05:30	1	t	\N	f	f
507	CATEGORY	Category	9SI9Y9A036 / Turbo charged	191730	2022-09-20 14:09:06.06966+05:30	2022-09-20 14:09:06.069689+05:30	1	t	\N	f	f
508	CATEGORY	Category	D1A81KCH82 / Turbo charged	191728	2022-09-20 14:09:06.069751+05:30	2022-09-20 14:09:06.069782+05:30	1	t	\N	f	f
509	CATEGORY	Category	5VD52OUE8G / Turbo charged	191727	2022-09-20 14:09:06.069847+05:30	2022-09-20 14:09:06.070045+05:30	1	t	\N	f	f
510	CATEGORY	Category	RMLZWIV6W7 / Turbo charged	191726	2022-09-20 14:09:06.070187+05:30	2022-09-20 14:09:06.070428+05:30	1	t	\N	f	f
511	CATEGORY	Category	Z07A9NN1DM / Turbo charged	191694	2022-09-20 14:09:06.071579+05:30	2022-09-20 14:09:06.072185+05:30	1	t	\N	f	f
512	CATEGORY	Category	XG2FEN961D / Turbo charged	191693	2022-09-20 14:09:06.074397+05:30	2022-09-20 14:09:06.075535+05:30	1	t	\N	f	f
513	CATEGORY	Category	ZDM9M85NEK / Turbo charged	191692	2022-09-20 14:09:06.07588+05:30	2022-09-20 14:09:06.075961+05:30	1	t	\N	f	f
514	CATEGORY	Category	55D90KR22F / Turbo charged	191691	2022-09-20 14:09:06.076113+05:30	2022-09-20 14:09:06.076173+05:30	1	t	\N	f	f
515	CATEGORY	Category	69W9JMEXIP / Turbo charged	191690	2022-09-20 14:09:06.076314+05:30	2022-09-20 14:09:06.076783+05:30	1	t	\N	f	f
516	CATEGORY	Category	UTJEMXABWZ / Turbo charged	191689	2022-09-20 14:09:06.079092+05:30	2022-09-20 14:09:06.091651+05:30	1	t	\N	f	f
517	CATEGORY	Category	1KPDKITYMO / Turbo charged	191688	2022-09-20 14:09:06.092465+05:30	2022-09-20 14:09:06.092563+05:30	1	t	\N	f	f
518	CATEGORY	Category	09ZKNVZ4O6 / Turbo charged	191687	2022-09-20 14:09:06.124978+05:30	2022-09-20 14:09:06.125146+05:30	1	t	\N	f	f
519	CATEGORY	Category	RYHQGEPACZ / Turbo charged	191686	2022-09-20 14:09:06.125571+05:30	2022-09-20 14:09:06.125602+05:30	1	t	\N	f	f
520	CATEGORY	Category	OYSLBGDVDT / Turbo charged	191685	2022-09-20 14:09:06.125926+05:30	2022-09-20 14:09:06.126788+05:30	1	t	\N	f	f
521	CATEGORY	Category	KF5LT1RF09 / Turbo charged	191684	2022-09-20 14:09:06.126892+05:30	2022-09-20 14:09:06.126924+05:30	1	t	\N	f	f
522	CATEGORY	Category	SKJX43FH5L / Turbo charged	191683	2022-09-20 14:09:06.127896+05:30	2022-09-20 14:09:06.127932+05:30	1	t	\N	f	f
523	CATEGORY	Category	JHLK63ZZWB / Turbo charged	191682	2022-09-20 14:09:06.128028+05:30	2022-09-20 14:09:06.128058+05:30	1	t	\N	f	f
524	CATEGORY	Category	V1EJ6D8VGJ / Turbo charged	191680	2022-09-20 14:09:06.128118+05:30	2022-09-20 14:09:06.128137+05:30	1	t	\N	f	f
525	CATEGORY	Category	AVXYHDXGHR / Turbo charged	191679	2022-09-20 14:09:06.128185+05:30	2022-09-20 14:09:06.129634+05:30	1	t	\N	f	f
526	CATEGORY	Category	560RKMO5QW / Turbo charged	191678	2022-09-20 14:09:06.129897+05:30	2022-09-20 14:09:06.129935+05:30	1	t	\N	f	f
527	CATEGORY	Category	IVX8Q7M4OL / Turbo charged	191677	2022-09-20 14:09:06.130009+05:30	2022-09-20 14:09:06.130039+05:30	1	t	\N	f	f
528	CATEGORY	Category	JVRYCPUK0F / Turbo charged	191676	2022-09-20 14:09:06.130133+05:30	2022-09-20 14:09:06.130162+05:30	1	t	\N	f	f
529	CATEGORY	Category	DSA93VPG9K / Turbo charged	191675	2022-09-20 14:09:06.131942+05:30	2022-09-20 14:09:06.132031+05:30	1	t	\N	f	f
530	CATEGORY	Category	RGLB5QES1M / Turbo charged	191674	2022-09-20 14:09:06.132423+05:30	2022-09-20 14:09:06.13248+05:30	1	t	\N	f	f
531	CATEGORY	Category	BEOCQYS8EN / Turbo charged	191672	2022-09-20 14:09:06.132595+05:30	2022-09-20 14:09:06.132624+05:30	1	t	\N	f	f
532	CATEGORY	Category	QYQKO8SPR6 / Turbo charged	191671	2022-09-20 14:09:06.132681+05:30	2022-09-20 14:09:06.132703+05:30	1	t	\N	f	f
533	CATEGORY	Category	WFRIUTX9C7 / Turbo charged	191669	2022-09-20 14:09:06.133666+05:30	2022-09-20 14:09:06.133721+05:30	1	t	\N	f	f
534	CATEGORY	Category	D47UDLB4F8 / Turbo charged	191667	2022-09-20 14:09:06.133781+05:30	2022-09-20 14:09:06.133812+05:30	1	t	\N	f	f
535	CATEGORY	Category	IKIJX0TM8Y / Turbo charged	191666	2022-09-20 14:09:06.133892+05:30	2022-09-20 14:09:06.133916+05:30	1	t	\N	f	f
536	CATEGORY	Category	1A8A84WBA2 / Turbo charged	191665	2022-09-20 14:09:06.133973+05:30	2022-09-20 14:09:06.133994+05:30	1	t	\N	f	f
537	CATEGORY	Category	69NR7TNK5P / Turbo charged	191664	2022-09-20 14:09:06.135337+05:30	2022-09-20 14:09:06.135392+05:30	1	t	\N	f	f
538	CATEGORY	Category	RCYUA4VYHK / Turbo charged	191663	2022-09-20 14:09:06.135474+05:30	2022-09-20 14:09:06.135496+05:30	1	t	\N	f	f
539	CATEGORY	Category	H1979NVX85 / Turbo charged	191662	2022-09-20 14:09:06.135559+05:30	2022-09-20 14:09:06.13559+05:30	1	t	\N	f	f
540	CATEGORY	Category	OEAN2S0661 / Turbo charged	191661	2022-09-20 14:09:06.135651+05:30	2022-09-20 14:09:06.135663+05:30	1	t	\N	f	f
541	CATEGORY	Category	8ZUVNA95N1 / Turbo charged	191631	2022-09-20 14:09:06.135714+05:30	2022-09-20 14:09:06.13575+05:30	1	t	\N	f	f
542	CATEGORY	Category	GLBTYBKH0W / Turbo charged	191630	2022-09-20 14:09:06.135812+05:30	2022-09-20 14:09:06.135832+05:30	1	t	\N	f	f
543	CATEGORY	Category	T2PVG1SAHV / Turbo charged	191627	2022-09-20 14:09:06.135885+05:30	2022-09-20 14:09:06.135932+05:30	1	t	\N	f	f
544	CATEGORY	Category	II6NWV8PK4 / Turbo charged	191626	2022-09-20 14:09:06.135981+05:30	2022-09-20 14:09:06.136002+05:30	1	t	\N	f	f
545	CATEGORY	Category	R92514U6N6 / Turbo charged	191625	2022-09-20 14:09:06.136063+05:30	2022-09-20 14:09:06.136092+05:30	1	t	\N	f	f
546	CATEGORY	Category	Y7ALNUN1XP / Turbo charged	191624	2022-09-20 14:09:06.136604+05:30	2022-09-20 14:09:06.138926+05:30	1	t	\N	f	f
547	CATEGORY	Category	HTR8W6D3JR / Turbo charged	191623	2022-09-20 14:09:06.139133+05:30	2022-09-20 14:09:06.139207+05:30	1	t	\N	f	f
548	CATEGORY	Category	DEL4M6NRFW / Turbo charged	191622	2022-09-20 14:09:06.141256+05:30	2022-09-20 14:09:06.141302+05:30	1	t	\N	f	f
549	CATEGORY	Category	QVOZSLTNXZ / Turbo charged	191621	2022-09-20 14:09:06.141616+05:30	2022-09-20 14:09:06.141648+05:30	1	t	\N	f	f
550	CATEGORY	Category	Nilesh Pant 112 / Turbo charged	191614	2022-09-20 14:09:06.145256+05:30	2022-09-20 14:09:06.145424+05:30	1	t	\N	f	f
551	CATEGORY	Category	s;dhfsodhiyfowiehrwoiehrowiehrowiehr / Turbo charged	191578	2022-09-20 14:09:06.145488+05:30	2022-09-20 14:09:06.145519+05:30	1	t	\N	f	f
552	CATEGORY	Category	LF3OR9B6UY / Turbo charged	191229	2022-09-20 14:09:06.145578+05:30	2022-09-20 14:09:06.145591+05:30	1	t	\N	f	f
553	CATEGORY	Category	3GYAQ1QYHQ / Turbo charged	191228	2022-09-20 14:09:06.145662+05:30	2022-09-20 14:09:06.145693+05:30	1	t	\N	f	f
554	CATEGORY	Category	PVDGPPF2SC / Turbo charged	191158	2022-09-20 14:09:06.147223+05:30	2022-09-20 14:09:06.147261+05:30	1	t	\N	f	f
555	CATEGORY	Category	KOY9ZL06FA / Turbo charged	191157	2022-09-20 14:09:06.148508+05:30	2022-09-20 14:09:06.148564+05:30	1	t	\N	f	f
556	CATEGORY	Category	WSTNCJ6Q5H / Turbo charged	191156	2022-09-20 14:09:06.148619+05:30	2022-09-20 14:09:06.14864+05:30	1	t	\N	f	f
557	CATEGORY	Category	NVV6A35DEB / Turbo charged	191155	2022-09-20 14:09:06.148696+05:30	2022-09-20 14:09:06.148717+05:30	1	t	\N	f	f
558	CATEGORY	Category	Z90LGUXCKD / Turbo charged	191154	2022-09-20 14:09:06.148778+05:30	2022-09-20 14:09:06.148828+05:30	1	t	\N	f	f
559	CATEGORY	Category	13GI6S3UYN / Turbo charged	191153	2022-09-20 14:09:06.149605+05:30	2022-09-20 14:09:06.149643+05:30	1	t	\N	f	f
560	CATEGORY	Category	WQAYU3EVN9 / Turbo charged	191152	2022-09-20 14:09:06.149743+05:30	2022-09-20 14:09:06.149764+05:30	1	t	\N	f	f
561	CATEGORY	Category	GHFPC90RHT / Turbo charged	191151	2022-09-20 14:09:06.149818+05:30	2022-09-20 14:09:06.14984+05:30	1	t	\N	f	f
562	CATEGORY	Category	M20BG0G6TW / Turbo charged	191150	2022-09-20 14:09:06.149903+05:30	2022-09-20 14:09:06.149933+05:30	1	t	\N	f	f
563	CATEGORY	Category	LTFKCOG3FH / Turbo charged	191149	2022-09-20 14:09:06.149994+05:30	2022-09-20 14:09:06.150046+05:30	1	t	\N	f	f
564	CATEGORY	Category	M08GU5OX20 / Turbo charged	191148	2022-09-20 14:09:06.150854+05:30	2022-09-20 14:09:06.150882+05:30	1	t	\N	f	f
565	CATEGORY	Category	8V1FTMOLVI / Turbo charged	191147	2022-09-20 14:09:06.150938+05:30	2022-09-20 14:09:06.150961+05:30	1	t	\N	f	f
566	CATEGORY	Category	L2CSEXHPTK / Turbo charged	191146	2022-09-20 14:09:06.151118+05:30	2022-09-20 14:09:06.151474+05:30	1	t	\N	f	f
567	CATEGORY	Category	A5QP6EJ9HR / Turbo charged	191143	2022-09-20 14:09:06.151676+05:30	2022-09-20 14:09:06.151716+05:30	1	t	\N	f	f
568	CATEGORY	Category	EY28M1P22T / Turbo charged	191142	2022-09-20 14:09:06.169973+05:30	2022-09-20 14:09:06.170015+05:30	1	t	\N	f	f
569	CATEGORY	Category	VACMTQNMYJ / Turbo charged	190103	2022-09-20 14:09:06.170082+05:30	2022-09-20 14:09:06.170111+05:30	1	t	\N	f	f
570	CATEGORY	Category	CE1SD2SQIK / Turbo charged	190102	2022-09-20 14:09:06.170173+05:30	2022-09-20 14:09:06.170201+05:30	1	t	\N	f	f
571	CATEGORY	Category	YQKG0LTOUZ / Turbo charged	189447	2022-09-20 14:09:06.17026+05:30	2022-09-20 14:09:06.170288+05:30	1	t	\N	f	f
572	CATEGORY	Category	37YWNDJGXS / Turbo charged	189446	2022-09-20 14:09:06.170347+05:30	2022-09-20 14:09:06.170488+05:30	1	t	\N	f	f
573	CATEGORY	Category	5OJBS10VAC / Turbo charged	189445	2022-09-20 14:09:06.170553+05:30	2022-09-20 14:09:06.17058+05:30	1	t	\N	f	f
574	CATEGORY	Category	248OHESQX4 / Turbo charged	189444	2022-09-20 14:09:06.170638+05:30	2022-09-20 14:09:06.170665+05:30	1	t	\N	f	f
575	CATEGORY	Category	VL45IRZHOK / Turbo charged	189443	2022-09-20 14:09:06.170722+05:30	2022-09-20 14:09:06.170749+05:30	1	t	\N	f	f
576	CATEGORY	Category	OW43OS7WUO / Turbo charged	189442	2022-09-20 14:09:06.170806+05:30	2022-09-20 14:09:06.170834+05:30	1	t	\N	f	f
577	CATEGORY	Category	QXWLZB6RGO / Turbo charged	189441	2022-09-20 14:09:06.17089+05:30	2022-09-20 14:09:06.170918+05:30	1	t	\N	f	f
578	CATEGORY	Category	LOITUJ2M1M / Turbo charged	189440	2022-09-20 14:09:06.170985+05:30	2022-09-20 14:09:06.171018+05:30	1	t	\N	f	f
579	CATEGORY	Category	QZP8MCPJI0 / Turbo charged	189439	2022-09-20 14:09:06.171088+05:30	2022-09-20 14:09:06.171115+05:30	1	t	\N	f	f
580	CATEGORY	Category	MD8XPYK2C6 / Turbo charged	189438	2022-09-20 14:09:06.171172+05:30	2022-09-20 14:09:06.1712+05:30	1	t	\N	f	f
581	CATEGORY	Category	GV18OGZEWB / Turbo charged	189437	2022-09-20 14:09:06.171257+05:30	2022-09-20 14:09:06.171285+05:30	1	t	\N	f	f
582	CATEGORY	Category	6OJKRIJ9CD / Turbo charged	189436	2022-09-20 14:09:06.171341+05:30	2022-09-20 14:09:06.171473+05:30	1	t	\N	f	f
583	CATEGORY	Category	1Q274U30JE / Turbo charged	189435	2022-09-20 14:09:06.171533+05:30	2022-09-20 14:09:06.171561+05:30	1	t	\N	f	f
584	CATEGORY	Category	DJJWB6F4HM / Turbo charged	189433	2022-09-20 14:09:06.171618+05:30	2022-09-20 14:09:06.171645+05:30	1	t	\N	f	f
585	CATEGORY	Category	VPJJOTDBCR / Turbo charged	189432	2022-09-20 14:09:06.171703+05:30	2022-09-20 14:09:06.17173+05:30	1	t	\N	f	f
586	CATEGORY	Category	L519GF6JU0 / Turbo charged	189431	2022-09-20 14:09:06.171786+05:30	2022-09-20 14:09:06.171813+05:30	1	t	\N	f	f
587	CATEGORY	Category	I3LOOW56KF / Turbo charged	189430	2022-09-20 14:09:06.17202+05:30	2022-09-20 14:09:06.172082+05:30	1	t	\N	f	f
588	CATEGORY	Category	VFDBWILTZT / Turbo charged	189429	2022-09-20 14:09:06.172153+05:30	2022-09-20 14:09:06.17218+05:30	1	t	\N	f	f
589	CATEGORY	Category	QT8T97FF18 / Turbo charged	189428	2022-09-20 14:09:06.172239+05:30	2022-09-20 14:09:06.172266+05:30	1	t	\N	f	f
590	CATEGORY	Category	ERWLSCCF5Y / Turbo charged	189427	2022-09-20 14:09:06.172323+05:30	2022-09-20 14:09:06.172504+05:30	1	t	\N	f	f
591	CATEGORY	Category	WWBU4JTK1W / Turbo charged	189398	2022-09-20 14:09:06.172621+05:30	2022-09-20 14:09:06.172664+05:30	1	t	\N	f	f
592	CATEGORY	Category	AZMVYWZ7BW / Turbo charged	189397	2022-09-20 14:09:06.17478+05:30	2022-09-20 14:09:06.174847+05:30	1	t	\N	f	f
593	CATEGORY	Category	50Q5KYEKC7 / Turbo charged	189364	2022-09-20 14:09:06.174933+05:30	2022-09-20 14:09:06.174962+05:30	1	t	\N	f	f
594	CATEGORY	Category	OZY0APPOHJ / Turbo charged	189363	2022-09-20 14:09:06.175022+05:30	2022-09-20 14:09:06.17505+05:30	1	t	\N	f	f
595	CATEGORY	Category	2VD4DE3305 / Turbo charged	189362	2022-09-20 14:09:06.175108+05:30	2022-09-20 14:09:06.175135+05:30	1	t	\N	f	f
596	CATEGORY	Category	D477IUAK5W / Turbo charged	189361	2022-09-20 14:09:06.175192+05:30	2022-09-20 14:09:06.175219+05:30	1	t	\N	f	f
597	CATEGORY	Category	AU1B8Y7TGS / Turbo charged	189357	2022-09-20 14:09:06.175275+05:30	2022-09-20 14:09:06.175303+05:30	1	t	\N	f	f
598	CATEGORY	Category	QDJ8J2CPWA / Turbo charged	189356	2022-09-20 14:09:06.175359+05:30	2022-09-20 14:09:06.175397+05:30	1	t	\N	f	f
599	CATEGORY	Category	K9ZTD8WVCG / Turbo charged	189355	2022-09-20 14:09:06.175588+05:30	2022-09-20 14:09:06.175616+05:30	1	t	\N	f	f
600	CATEGORY	Category	611ZFAT5SM / Turbo charged	188251	2022-09-20 14:09:06.175672+05:30	2022-09-20 14:09:06.175699+05:30	1	t	\N	f	f
601	CATEGORY	Category	HOUPXN0V9X / Turbo charged	185671	2022-09-20 14:09:06.175756+05:30	2022-09-20 14:09:06.175783+05:30	1	t	\N	f	f
602	CATEGORY	Category	Z8STSQH7B8 / Turbo charged	185670	2022-09-20 14:09:06.175839+05:30	2022-09-20 14:09:06.175908+05:30	1	t	\N	f	f
603	CATEGORY	Category	QHGZ8OB0QW / Turbo charged	185669	2022-09-20 14:09:06.176004+05:30	2022-09-20 14:09:06.176033+05:30	1	t	\N	f	f
604	CATEGORY	Category	PZTO6DMVX2 / Turbo charged	185622	2022-09-20 14:09:06.176092+05:30	2022-09-20 14:09:06.176119+05:30	1	t	\N	f	f
605	CATEGORY	Category	P9T0IITI3Q / Turbo charged	185621	2022-09-20 14:09:06.176175+05:30	2022-09-20 14:09:06.176202+05:30	1	t	\N	f	f
606	CATEGORY	Category	X6T4RNW4II / Turbo charged	185616	2022-09-20 14:09:06.176259+05:30	2022-09-20 14:09:06.176286+05:30	1	t	\N	f	f
607	CATEGORY	Category	UX47SL7LOE / Turbo charged	185615	2022-09-20 14:09:06.176507+05:30	2022-09-20 14:09:06.176548+05:30	1	t	\N	f	f
608	CATEGORY	Category	JDDDN0IM2E / Turbo charged	185614	2022-09-20 14:09:06.176606+05:30	2022-09-20 14:09:06.176633+05:30	1	t	\N	f	f
609	CATEGORY	Category	WGGUO7Z1SM / Turbo charged	184700	2022-09-20 14:09:06.176691+05:30	2022-09-20 14:09:06.176718+05:30	1	t	\N	f	f
610	CATEGORY	Category	ZW806W7J5F / Turbo charged	184699	2022-09-20 14:09:06.176775+05:30	2022-09-20 14:09:06.176802+05:30	1	t	\N	f	f
611	CATEGORY	Category	O4Z369SVSU / Turbo charged	184698	2022-09-20 14:09:06.17686+05:30	2022-09-20 14:09:06.176887+05:30	1	t	\N	f	f
612	CATEGORY	Category	OJ1ZB2W1AT / Turbo charged	184697	2022-09-20 14:09:06.176944+05:30	2022-09-20 14:09:06.176972+05:30	1	t	\N	f	f
613	CATEGORY	Category	IZZG6UH5Y8 / Turbo charged	184696	2022-09-20 14:09:06.177028+05:30	2022-09-20 14:09:06.177056+05:30	1	t	\N	f	f
614	CATEGORY	Category	9R407O18OU / Turbo charged	184695	2022-09-20 14:09:06.177112+05:30	2022-09-20 14:09:06.17714+05:30	1	t	\N	f	f
615	CATEGORY	Category	UATHCG2KXH / Turbo charged	184694	2022-09-20 14:09:06.177197+05:30	2022-09-20 14:09:06.177224+05:30	1	t	\N	f	f
616	CATEGORY	Category	ERLZ2WXGBY / Turbo charged	184693	2022-09-20 14:09:06.177281+05:30	2022-09-20 14:09:06.177309+05:30	1	t	\N	f	f
617	CATEGORY	Category	9GZBIA2Z9H / Turbo charged	184686	2022-09-20 14:09:06.177489+05:30	2022-09-20 14:09:06.17752+05:30	1	t	\N	f	f
618	CATEGORY	Category	JQUIDWM0VG / Turbo charged	184685	2022-09-20 14:09:06.356884+05:30	2022-09-20 14:09:06.356937+05:30	1	t	\N	f	f
619	CATEGORY	Category	CABFH8FYWJ / Turbo charged	184684	2022-09-20 14:09:06.357015+05:30	2022-09-20 14:09:06.357058+05:30	1	t	\N	f	f
620	CATEGORY	Category	CM556CRMO4 / Turbo charged	184683	2022-09-20 14:09:06.357162+05:30	2022-09-20 14:09:06.357206+05:30	1	t	\N	f	f
621	CATEGORY	Category	3TBA1Y8XTJ / Turbo charged	184682	2022-09-20 14:09:06.357301+05:30	2022-09-20 14:09:06.357335+05:30	1	t	\N	f	f
622	CATEGORY	Category	WUZT4BLA9Z / Turbo charged	184681	2022-09-20 14:09:06.357398+05:30	2022-09-20 14:09:06.357451+05:30	1	t	\N	f	f
623	CATEGORY	Category	SD6IFM5X2M / Turbo charged	184588	2022-09-20 14:09:06.357512+05:30	2022-09-20 14:09:06.357541+05:30	1	t	\N	f	f
624	CATEGORY	Category	3IFD3F0WJD / Turbo charged	184587	2022-09-20 14:09:06.357602+05:30	2022-09-20 14:09:06.357632+05:30	1	t	\N	f	f
625	CATEGORY	Category	Engine samp122123 / Turbo charged	184580	2022-09-20 14:09:06.357692+05:30	2022-09-20 14:09:06.357721+05:30	1	t	\N	f	f
626	CATEGORY	Category	Engine samp122 / Turbo charged	184264	2022-09-20 14:09:06.358058+05:30	2022-09-20 14:09:06.358315+05:30	1	t	\N	f	f
627	CATEGORY	Category	Engine samp1122 / Turbo charged	184130	2022-09-20 14:09:06.358592+05:30	2022-09-20 14:09:06.358641+05:30	1	t	\N	f	f
628	CATEGORY	Category	Engine samp112 / Turbo charged	184124	2022-09-20 14:09:06.359058+05:30	2022-09-20 14:09:06.359174+05:30	1	t	\N	f	f
629	CATEGORY	Category	Engine samp111 / Turbo charged	183963	2022-09-20 14:09:06.359435+05:30	2022-09-20 14:09:06.359465+05:30	1	t	\N	f	f
630	CATEGORY	Category	Engine samp11 / Turbo charged	183961	2022-09-20 14:09:06.359524+05:30	2022-09-20 14:09:06.359552+05:30	1	t	\N	f	f
631	CATEGORY	Category	Engine samp1 / Turbo charged	183959	2022-09-20 14:09:06.359609+05:30	2022-09-20 14:09:06.359636+05:30	1	t	\N	f	f
632	CATEGORY	Category	Engine samp / Turbo charged	183957	2022-09-20 14:09:06.359693+05:30	2022-09-20 14:09:06.35972+05:30	1	t	\N	f	f
633	CATEGORY	Category	Engine / Turbo charged	183955	2022-09-20 14:09:06.359777+05:30	2022-09-20 14:09:06.359804+05:30	1	t	\N	f	f
22	CATEGORY	Category	Internet	135456	2022-09-20 14:09:03.251324+05:30	2022-09-20 14:09:03.251363+05:30	1	t	\N	t	f
23	CATEGORY	Category	Meals	135741	2022-09-20 14:09:03.251536+05:30	2022-09-20 14:09:03.252214+05:30	1	t	\N	t	f
24	CATEGORY	Category	Airfare	135796	2022-09-20 14:09:03.252319+05:30	2022-09-20 14:09:03.252351+05:30	1	t	\N	t	f
25	CATEGORY	Category	Cell Phone	137946	2022-09-20 14:09:03.252415+05:30	2022-09-20 14:09:03.252443+05:30	1	t	\N	t	f
26	CATEGORY	Category	Ground Transportation-Parking	149332	2022-09-20 14:09:03.252505+05:30	2022-09-20 14:09:03.252534+05:30	1	t	\N	t	f
27	CATEGORY	Category	Hotel-Lodging	149333	2022-09-20 14:09:03.252594+05:30	2022-09-20 14:09:03.252623+05:30	1	t	\N	t	f
325	CATEGORY	Category	Food	135453	2022-09-20 14:09:05.265411+05:30	2022-09-20 14:19:07.925686+05:30	1	t	\N	f	f
3225	CATEGORY	Category	FML12E68S6 / Turbo charged	209304	2022-09-28 17:25:41.765972+05:30	2022-09-28 17:25:41.766025+05:30	1	t	\N	f	f
3226	CATEGORY	Category	N27HHEOEY8 / Turbo charged	209303	2022-09-28 17:25:41.766086+05:30	2022-09-28 17:25:41.766117+05:30	1	t	\N	f	f
3227	CATEGORY	Category	H7FH7Q9WJ6 / Turbo charged	209299	2022-09-28 17:25:41.76618+05:30	2022-09-28 17:25:41.766211+05:30	1	t	\N	f	f
921	PROJECT	Project	Celia Corp	247033	2022-09-20 14:09:07.403966+05:30	2022-09-20 14:09:07.403997+05:30	1	t	\N	f	f
635	PROJECT	Project	Bank West	300057	2022-09-20 14:09:06.833093+05:30	2022-09-20 14:09:06.833123+05:30	1	t	\N	f	f
636	PROJECT	Project	Basket Case	300058	2022-09-20 14:09:06.833177+05:30	2022-09-20 14:09:06.833207+05:30	1	t	\N	f	f
637	PROJECT	Project	Bayside Club	300059	2022-09-20 14:09:06.833716+05:30	2022-09-20 14:09:06.833753+05:30	1	t	\N	f	f
638	PROJECT	Project	Boom FM	300060	2022-09-20 14:09:06.833818+05:30	2022-09-20 14:09:06.83385+05:30	1	t	\N	f	f
639	PROJECT	Project	City Agency	300061	2022-09-20 14:09:06.833914+05:30	2022-09-20 14:09:06.83412+05:30	1	t	\N	f	f
640	PROJECT	Project	City Limousines	300062	2022-09-20 14:09:06.834233+05:30	2022-09-20 14:09:06.834501+05:30	1	t	\N	f	f
641	PROJECT	Project	DIISR - Small Business Services	300063	2022-09-20 14:09:06.834734+05:30	2022-09-20 14:09:06.834915+05:30	1	t	\N	f	f
642	PROJECT	Project	Hamilton Smith Ltd	300064	2022-09-20 14:09:06.835448+05:30	2022-09-20 14:09:06.835673+05:30	1	t	\N	f	f
643	PROJECT	Project	Marine Systems	300065	2022-09-20 14:09:06.835763+05:30	2022-09-20 14:09:06.835884+05:30	1	t	\N	f	f
644	PROJECT	Project	Petrie McLoud Watson & Associates	300066	2022-09-20 14:09:06.835949+05:30	2022-09-20 14:09:06.836424+05:30	1	t	\N	f	f
645	PROJECT	Project	Port & Philip Freight	300067	2022-09-20 14:09:06.83653+05:30	2022-09-20 14:09:06.836562+05:30	1	t	\N	f	f
646	PROJECT	Project	Rex Media Group	300068	2022-09-20 14:09:06.836641+05:30	2022-09-20 14:09:06.836682+05:30	1	t	\N	f	f
647	PROJECT	Project	Ridgeway University	300069	2022-09-20 14:09:06.836748+05:30	2022-09-20 14:09:06.836771+05:30	1	t	\N	f	f
648	PROJECT	Project	Young Bros Transport	300070	2022-09-20 14:09:06.836845+05:30	2022-09-20 14:09:06.836972+05:30	1	t	\N	f	f
649	PROJECT	Project	Chennai	299998	2022-09-20 14:09:06.837507+05:30	2022-09-20 14:09:06.837544+05:30	1	t	\N	f	f
650	PROJECT	Project	Delhi	299999	2022-09-20 14:09:06.837609+05:30	2022-09-20 14:09:06.83764+05:30	1	t	\N	f	f
651	PROJECT	Project	Sravan BLR Customer	299945	2022-09-20 14:09:06.837702+05:30	2022-09-20 14:09:06.837723+05:30	1	t	\N	f	f
652	PROJECT	Project	Bangalore	292304	2022-09-20 14:09:06.83778+05:30	2022-09-20 14:09:06.837801+05:30	1	t	\N	f	f
653	PROJECT	Project	Bebe Rexha	292305	2022-09-20 14:09:06.837862+05:30	2022-09-20 14:09:06.838575+05:30	1	t	\N	f	f
654	PROJECT	Project	suhas_p1	292306	2022-09-20 14:09:06.838741+05:30	2022-09-20 14:09:06.838765+05:30	1	t	\N	f	f
655	PROJECT	Project	Wow Company	292246	2022-09-20 14:09:06.839021+05:30	2022-09-20 14:09:06.839047+05:30	1	t	\N	f	f
656	PROJECT	Project	Nilesh Pant	292244	2022-09-20 14:09:06.83911+05:30	2022-09-20 14:09:06.83913+05:30	1	t	\N	f	f
657	PROJECT	Project	Project Sravan	292245	2022-09-20 14:09:06.839969+05:30	2022-09-20 14:09:06.840105+05:30	1	t	\N	f	f
658	PROJECT	Project	Adidas	292241	2022-09-20 14:09:06.843983+05:30	2022-09-20 14:09:06.844025+05:30	1	t	\N	f	f
659	PROJECT	Project	Fabrication	292242	2022-09-20 14:09:06.844369+05:30	2022-09-20 14:09:06.84444+05:30	1	t	\N	f	f
660	PROJECT	Project	FAE	292243	2022-09-20 14:09:06.844504+05:30	2022-09-20 14:09:06.844527+05:30	1	t	\N	f	f
661	PROJECT	Project	BOOK	292184	2022-09-20 14:09:06.844591+05:30	2022-09-20 14:09:06.844619+05:30	1	t	\N	f	f
662	PROJECT	Project	DevD	292185	2022-09-20 14:09:06.844673+05:30	2022-09-20 14:09:06.844696+05:30	1	t	\N	f	f
663	PROJECT	Project	DevH	292186	2022-09-20 14:09:06.84475+05:30	2022-09-20 14:09:06.845942+05:30	1	t	\N	f	f
664	PROJECT	Project	GB1-White	292187	2022-09-20 14:09:06.846084+05:30	2022-09-20 14:09:06.846117+05:30	1	t	\N	f	f
665	PROJECT	Project	GB3-White	292188	2022-09-20 14:09:06.846181+05:30	2022-09-20 14:09:06.84621+05:30	1	t	\N	f	f
666	PROJECT	Project	GB6-White	292189	2022-09-20 14:09:06.846271+05:30	2022-09-20 14:09:06.8463+05:30	1	t	\N	f	f
667	PROJECT	Project	GB9-White	292190	2022-09-20 14:09:06.846594+05:30	2022-09-20 14:09:06.846643+05:30	1	t	\N	f	f
668	PROJECT	Project	PMBr	292191	2022-09-20 14:09:06.846718+05:30	2022-09-20 14:09:06.846748+05:30	1	t	\N	f	f
669	PROJECT	Project	PMD	292192	2022-09-20 14:09:06.846809+05:30	2022-09-20 14:09:06.84683+05:30	1	t	\N	f	f
670	PROJECT	Project	PMDD	292193	2022-09-20 14:09:06.846884+05:30	2022-09-20 14:09:06.846905+05:30	1	t	\N	f	f
671	PROJECT	Project	PMWe	292194	2022-09-20 14:09:06.846958+05:30	2022-09-20 14:09:06.846983+05:30	1	t	\N	f	f
672	PROJECT	Project	Support-M	292195	2022-09-20 14:09:06.847026+05:30	2022-09-20 14:09:06.847037+05:30	1	t	\N	f	f
673	PROJECT	Project	TSL - Black	292196	2022-09-20 14:09:06.84709+05:30	2022-09-20 14:09:06.847135+05:30	1	t	\N	f	f
674	PROJECT	Project	TSM - Black	292197	2022-09-20 14:09:06.84732+05:30	2022-09-20 14:09:06.847397+05:30	1	t	\N	f	f
675	PROJECT	Project	TSS - Black	292198	2022-09-20 14:09:06.847555+05:30	2022-09-20 14:09:06.84758+05:30	1	t	\N	f	f
676	PROJECT	Project	Train-MS	292199	2022-09-20 14:09:06.847807+05:30	2022-09-20 14:09:06.848025+05:30	1	t	\N	f	f
677	PROJECT	Project	Project 1	203309	2022-09-20 14:09:06.848101+05:30	2022-09-20 14:09:06.848164+05:30	1	t	\N	f	f
678	PROJECT	Project	Project 2	203310	2022-09-20 14:09:06.848369+05:30	2022-09-20 14:09:06.848455+05:30	1	t	\N	f	f
685	PROJECT	Project	Project 9	203317	2022-09-20 14:09:06.867731+05:30	2022-09-20 14:09:06.867791+05:30	1	t	\N	f	f
686	PROJECT	Project	Project 10	203318	2022-09-20 14:09:06.868033+05:30	2022-09-20 14:09:06.868333+05:30	1	t	\N	f	f
687	PROJECT	Project	Fyle Team Integrations	243607	2022-09-20 14:09:06.868509+05:30	2022-09-20 14:09:06.868561+05:30	1	t	\N	f	f
689	PROJECT	Project	Customer Mapped Project	243609	2022-09-20 14:09:06.869203+05:30	2022-09-20 14:09:06.869358+05:30	1	t	\N	f	f
690	PROJECT	Project	Sage project fyle	243610	2022-09-20 14:09:06.869711+05:30	2022-09-20 14:09:06.869935+05:30	1	t	\N	f	f
691	PROJECT	Project	Sage Project 8	243611	2022-09-20 14:09:06.870078+05:30	2022-09-20 14:09:06.870123+05:30	1	t	\N	f	f
692	PROJECT	Project	Sage Project 5	243612	2022-09-20 14:09:06.870433+05:30	2022-09-20 14:09:06.87052+05:30	1	t	\N	f	f
693	PROJECT	Project	Sage Project 3	243613	2022-09-20 14:09:06.87061+05:30	2022-09-20 14:09:06.870633+05:30	1	t	\N	f	f
694	PROJECT	Project	Sage Project 1	243614	2022-09-20 14:09:06.870704+05:30	2022-09-20 14:09:06.870734+05:30	1	t	\N	f	f
695	PROJECT	Project	Sage Project 4	243615	2022-09-20 14:09:06.870804+05:30	2022-09-20 14:09:06.870836+05:30	1	t	\N	f	f
696	PROJECT	Project	Sravan Prod Test Pr@d	243616	2022-09-20 14:09:06.870929+05:30	2022-09-20 14:09:06.870955+05:30	1	t	\N	f	f
697	PROJECT	Project	Sage Project 9	243617	2022-09-20 14:09:06.871444+05:30	2022-09-20 14:09:06.871486+05:30	1	t	\N	f	f
698	PROJECT	Project	Sage Project 2	243618	2022-09-20 14:09:06.87156+05:30	2022-09-20 14:09:06.871574+05:30	1	t	\N	f	f
699	PROJECT	Project	Sage Project 6	243619	2022-09-20 14:09:06.871625+05:30	2022-09-20 14:09:06.871651+05:30	1	t	\N	f	f
700	PROJECT	Project	Sage Project 7	243620	2022-09-20 14:09:06.871705+05:30	2022-09-20 14:09:06.871739+05:30	1	t	\N	f	f
701	PROJECT	Project	Sage Project 10	243621	2022-09-20 14:09:06.872651+05:30	2022-09-20 14:09:06.872705+05:30	1	t	\N	f	f
702	PROJECT	Project	Fyle Main Project	243622	2022-09-20 14:09:06.874636+05:30	2022-09-20 14:09:06.874751+05:30	1	t	\N	f	f
703	PROJECT	Project	Amy's Bird Sanctuary	246788	2022-09-20 14:09:06.875893+05:30	2022-09-20 14:09:06.875974+05:30	1	t	\N	f	f
704	PROJECT	Project	Amy's Bird Sanctuary:Test Project	246789	2022-09-20 14:09:06.876307+05:30	2022-09-20 14:09:06.87636+05:30	1	t	\N	f	f
705	PROJECT	Project	Bill's Windsurf Shop	246790	2022-09-20 14:09:06.876609+05:30	2022-09-20 14:09:06.876654+05:30	1	t	\N	f	f
706	PROJECT	Project	Cool Cars	246791	2022-09-20 14:09:06.876789+05:30	2022-09-20 14:09:06.876845+05:30	1	t	\N	f	f
707	PROJECT	Project	Diego Rodriguez	246792	2022-09-20 14:09:06.87703+05:30	2022-09-20 14:09:06.877075+05:30	1	t	\N	f	f
708	PROJECT	Project	Diego Rodriguez:Test Project	246793	2022-09-20 14:09:06.877205+05:30	2022-09-20 14:09:06.877249+05:30	1	t	\N	f	f
709	PROJECT	Project	Dukes Basketball Camp	246794	2022-09-20 14:09:06.878025+05:30	2022-09-20 14:09:06.878107+05:30	1	t	\N	f	f
710	PROJECT	Project	Dylan Sollfrank	246795	2022-09-20 14:09:06.878781+05:30	2022-09-20 14:09:06.878974+05:30	1	t	\N	f	f
711	PROJECT	Project	Freeman Sporting Goods	246796	2022-09-20 14:09:06.879084+05:30	2022-09-20 14:09:06.879121+05:30	1	t	\N	f	f
712	PROJECT	Project	Freeman Sporting Goods:0969 Ocean View Road	246797	2022-09-20 14:09:06.879351+05:30	2022-09-20 14:09:06.879383+05:30	1	t	\N	f	f
713	PROJECT	Project	Freeman Sporting Goods:55 Twin Lane	246798	2022-09-20 14:09:06.879474+05:30	2022-09-20 14:09:06.879536+05:30	1	t	\N	f	f
714	PROJECT	Project	Geeta Kalapatapu	246799	2022-09-20 14:09:06.879692+05:30	2022-09-20 14:09:06.879741+05:30	1	t	\N	f	f
715	PROJECT	Project	Gevelber Photography	246800	2022-09-20 14:09:06.881907+05:30	2022-09-20 14:09:06.881962+05:30	1	t	\N	f	f
716	PROJECT	Project	Jeff's Jalopies	246801	2022-09-20 14:09:06.882444+05:30	2022-09-20 14:09:06.882498+05:30	1	t	\N	f	f
717	PROJECT	Project	John Melton	246802	2022-09-20 14:09:06.882581+05:30	2022-09-20 14:09:06.882614+05:30	1	t	\N	f	f
718	PROJECT	Project	Kate Whelan	246803	2022-09-20 14:09:06.882683+05:30	2022-09-20 14:09:06.882713+05:30	1	t	\N	f	f
719	PROJECT	Project	Kookies by Kathy	246804	2022-09-20 14:09:06.882777+05:30	2022-09-20 14:09:06.882807+05:30	1	t	\N	f	f
720	PROJECT	Project	Mark Cho	246805	2022-09-20 14:09:06.882871+05:30	2022-09-20 14:09:06.8829+05:30	1	t	\N	f	f
721	PROJECT	Project	Paulsen Medical Supplies	246806	2022-09-20 14:09:06.882963+05:30	2022-09-20 14:09:06.882992+05:30	1	t	\N	f	f
722	PROJECT	Project	Pye's Cakes	246807	2022-09-20 14:09:06.883054+05:30	2022-09-20 14:09:06.883076+05:30	1	t	\N	f	f
723	PROJECT	Project	Rago Travel Agency	246808	2022-09-20 14:09:06.883129+05:30	2022-09-20 14:09:06.883158+05:30	1	t	\N	f	f
724	PROJECT	Project	Red Rock Diner	246809	2022-09-20 14:09:06.88324+05:30	2022-09-20 14:09:06.88326+05:30	1	t	\N	f	f
725	PROJECT	Project	Rondonuwu Fruit and Vegi	246810	2022-09-20 14:09:06.883313+05:30	2022-09-20 14:09:06.883342+05:30	1	t	\N	f	f
726	PROJECT	Project	Shara Barnett	246811	2022-09-20 14:09:06.883531+05:30	2022-09-20 14:09:06.883551+05:30	1	t	\N	f	f
727	PROJECT	Project	Shara Barnett:Barnett Design	246812	2022-09-20 14:09:06.883602+05:30	2022-09-20 14:09:06.883631+05:30	1	t	\N	f	f
728	PROJECT	Project	Sheldon Cooper	246813	2022-09-20 14:09:06.883692+05:30	2022-09-20 14:09:06.883721+05:30	1	t	\N	f	f
729	PROJECT	Project	Sheldon Cooper:Incremental Project	246814	2022-09-20 14:09:06.883782+05:30	2022-09-20 14:09:06.88381+05:30	1	t	\N	f	f
730	PROJECT	Project	Sonnenschein Family Store	246815	2022-09-20 14:09:06.883863+05:30	2022-09-20 14:09:06.883883+05:30	1	t	\N	f	f
731	PROJECT	Project	Sushi by Katsuyuki	246816	2022-09-20 14:09:06.883945+05:30	2022-09-20 14:09:06.88397+05:30	1	t	\N	f	f
732	PROJECT	Project	Travis Waldron	246817	2022-09-20 14:09:06.884014+05:30	2022-09-20 14:09:06.884035+05:30	1	t	\N	f	f
733	PROJECT	Project	Video Games by Dan	246818	2022-09-20 14:09:06.884101+05:30	2022-09-20 14:09:06.884124+05:30	1	t	\N	f	f
734	PROJECT	Project	Wedding Planning by Whitney	246819	2022-09-20 14:09:06.893616+05:30	2022-09-20 14:09:06.893658+05:30	1	t	\N	f	f
735	PROJECT	Project	Weiskopf Consulting	246820	2022-09-20 14:09:06.893723+05:30	2022-09-20 14:09:06.893752+05:30	1	t	\N	f	f
736	PROJECT	Project	Ashwinnnnnn	246821	2022-09-20 14:09:06.893813+05:30	2022-09-20 14:09:06.893842+05:30	1	t	\N	f	f
737	PROJECT	Project	3M	246849	2022-09-20 14:09:06.893902+05:30	2022-09-20 14:09:06.89393+05:30	1	t	\N	f	f
738	PROJECT	Project	AB&I Holdings	246850	2022-09-20 14:09:06.89399+05:30	2022-09-20 14:09:06.894019+05:30	1	t	\N	f	f
739	PROJECT	Project	ACM Group	246851	2022-09-20 14:09:06.89408+05:30	2022-09-20 14:09:06.894108+05:30	1	t	\N	f	f
740	PROJECT	Project	AIM Accounting	246852	2022-09-20 14:09:06.894169+05:30	2022-09-20 14:09:06.894198+05:30	1	t	\N	f	f
741	PROJECT	Project	AIQ Networks	246853	2022-09-20 14:09:06.894259+05:30	2022-09-20 14:09:06.894288+05:30	1	t	\N	f	f
742	PROJECT	Project	AMG Inc	246854	2022-09-20 14:09:06.894686+05:30	2022-09-20 14:09:06.894735+05:30	1	t	\N	f	f
743	PROJECT	Project	Aaron Abbott	246855	2022-09-20 14:09:06.894808+05:30	2022-09-20 14:09:06.894839+05:30	1	t	\N	f	f
744	PROJECT	Project	Absolute Location Support	246856	2022-09-20 14:09:06.8949+05:30	2022-09-20 14:09:06.894929+05:30	1	t	\N	f	f
745	PROJECT	Project	Academy Avenue Liquor Store	246857	2022-09-20 14:09:06.894989+05:30	2022-09-20 14:09:06.895018+05:30	1	t	\N	f	f
746	PROJECT	Project	Academy Sports & Outdoors	246858	2022-09-20 14:09:06.895077+05:30	2022-09-20 14:09:06.895106+05:30	1	t	\N	f	f
747	PROJECT	Project	Academy Vision Science Clinic	246859	2022-09-20 14:09:06.895166+05:30	2022-09-20 14:09:06.895195+05:30	1	t	\N	f	f
748	PROJECT	Project	Accountants Inc	246860	2022-09-20 14:09:06.895255+05:30	2022-09-20 14:09:06.895284+05:30	1	t	\N	f	f
749	PROJECT	Project	Acera	246861	2022-09-20 14:09:06.895959+05:30	2022-09-20 14:09:06.896247+05:30	1	t	\N	f	f
750	PROJECT	Project	Acme Systems Incorporated	246862	2022-09-20 14:09:06.896514+05:30	2022-09-20 14:09:06.896546+05:30	1	t	\N	f	f
751	PROJECT	Project	AcuVision Eye Centre	246863	2022-09-20 14:09:06.89661+05:30	2022-09-20 14:09:06.89664+05:30	1	t	\N	f	f
752	PROJECT	Project	Advanced Design & Drafting Ltd	246864	2022-09-20 14:09:06.896701+05:30	2022-09-20 14:09:06.89673+05:30	1	t	\N	f	f
753	PROJECT	Project	Advanced Machining Techniques Inc.	246865	2022-09-20 14:09:06.896791+05:30	2022-09-20 14:09:06.89682+05:30	1	t	\N	f	f
754	PROJECT	Project	Agrela Apartments Agency	246866	2022-09-20 14:09:06.89688+05:30	2022-09-20 14:09:06.896909+05:30	1	t	\N	f	f
755	PROJECT	Project	Ahonen Catering Group	246867	2022-09-20 14:09:06.896969+05:30	2022-09-20 14:09:06.896998+05:30	1	t	\N	f	f
756	PROJECT	Project	Alain Henderson	246868	2022-09-20 14:09:06.897059+05:30	2022-09-20 14:09:06.897087+05:30	1	t	\N	f	f
757	PROJECT	Project	Alamo Catering Group	246869	2022-09-20 14:09:06.897148+05:30	2022-09-20 14:09:06.897176+05:30	1	t	\N	f	f
758	PROJECT	Project	Alchemy PR	246870	2022-09-20 14:09:06.897236+05:30	2022-09-20 14:09:06.897265+05:30	1	t	\N	f	f
759	PROJECT	Project	Alesna Leasing Sales	246871	2022-09-20 14:09:06.897325+05:30	2022-09-20 14:09:06.897354+05:30	1	t	\N	f	f
760	PROJECT	Project	Alex Benedet	246872	2022-09-20 14:09:06.897532+05:30	2022-09-20 14:09:06.897569+05:30	1	t	\N	f	f
761	PROJECT	Project	Alex Fabre	246873	2022-09-20 14:09:06.897633+05:30	2022-09-20 14:09:06.897662+05:30	1	t	\N	f	f
762	PROJECT	Project	Alex Wolfe	246874	2022-09-20 14:09:06.897722+05:30	2022-09-20 14:09:06.897751+05:30	1	t	\N	f	f
763	PROJECT	Project	All Occassions Event Coordination	246875	2022-09-20 14:09:06.897812+05:30	2022-09-20 14:09:06.897841+05:30	1	t	\N	f	f
764	PROJECT	Project	All Outdoors	246876	2022-09-20 14:09:06.897901+05:30	2022-09-20 14:09:06.89793+05:30	1	t	\N	f	f
765	PROJECT	Project	All World Produce	246877	2022-09-20 14:09:06.89799+05:30	2022-09-20 14:09:06.898018+05:30	1	t	\N	f	f
766	PROJECT	Project	All-Lift Inc	246878	2022-09-20 14:09:06.898078+05:30	2022-09-20 14:09:06.898107+05:30	1	t	\N	f	f
767	PROJECT	Project	Alpart	246879	2022-09-20 14:09:06.898167+05:30	2022-09-20 14:09:06.898196+05:30	1	t	\N	f	f
768	PROJECT	Project	Alpine Cafe and Wine Bar	246880	2022-09-20 14:09:06.898255+05:30	2022-09-20 14:09:06.898284+05:30	1	t	\N	f	f
769	PROJECT	Project	Altamirano Apartments Services	246881	2022-09-20 14:09:06.898442+05:30	2022-09-20 14:09:06.898479+05:30	1	t	\N	f	f
770	PROJECT	Project	Altonen Windows Rentals	246882	2022-09-20 14:09:06.898542+05:30	2022-09-20 14:09:06.898572+05:30	1	t	\N	f	f
771	PROJECT	Project	Amarillo Apartments Distributors	246883	2022-09-20 14:09:06.898632+05:30	2022-09-20 14:09:06.898661+05:30	1	t	\N	f	f
772	PROJECT	Project	Ambc	246884	2022-09-20 14:09:06.898722+05:30	2022-09-20 14:09:06.89875+05:30	1	t	\N	f	f
773	PROJECT	Project	AmerCaire	246885	2022-09-20 14:09:06.89881+05:30	2022-09-20 14:09:06.898839+05:30	1	t	\N	f	f
774	PROJECT	Project	Ammann Builders Fabricators	246886	2022-09-20 14:09:06.898899+05:30	2022-09-20 14:09:06.898927+05:30	1	t	\N	f	f
775	PROJECT	Project	Amsterdam Drug Store	246887	2022-09-20 14:09:06.898982+05:30	2022-09-20 14:09:06.899003+05:30	1	t	\N	f	f
776	PROJECT	Project	Amy Kall	246888	2022-09-20 14:09:06.899062+05:30	2022-09-20 14:09:06.899091+05:30	1	t	\N	f	f
777	PROJECT	Project	Anderson Boughton Inc.	246889	2022-09-20 14:09:06.899151+05:30	2022-09-20 14:09:06.89918+05:30	1	t	\N	f	f
778	PROJECT	Project	Andersson Hospital Inc.	246890	2022-09-20 14:09:06.899239+05:30	2022-09-20 14:09:06.899268+05:30	1	t	\N	f	f
779	PROJECT	Project	Andrew Mager	246891	2022-09-20 14:09:06.899329+05:30	2022-09-20 14:09:06.899358+05:30	1	t	\N	f	f
780	PROJECT	Project	Andy Johnson	246892	2022-09-20 14:09:06.899535+05:30	2022-09-20 14:09:06.899565+05:30	1	t	\N	f	f
781	PROJECT	Project	Andy Thompson	246893	2022-09-20 14:09:06.899626+05:30	2022-09-20 14:09:06.899655+05:30	1	t	\N	f	f
782	PROJECT	Project	Angerman Markets Company	246894	2022-09-20 14:09:06.899715+05:30	2022-09-20 14:09:06.899744+05:30	1	t	\N	f	f
783	PROJECT	Project	Anonymous Customer HQ	246895	2022-09-20 14:09:06.899805+05:30	2022-09-20 14:09:06.899834+05:30	1	t	\N	f	f
784	PROJECT	Project	Another Killer Product	246896	2022-09-20 14:09:06.911007+05:30	2022-09-20 14:09:06.911048+05:30	1	t	\N	f	f
785	PROJECT	Project	Another Killer Product 1	246897	2022-09-20 14:09:06.911108+05:30	2022-09-20 14:09:06.911129+05:30	1	t	\N	f	f
786	PROJECT	Project	Anthony Jacobs	246898	2022-09-20 14:09:06.911169+05:30	2022-09-20 14:09:06.91119+05:30	1	t	\N	f	f
787	PROJECT	Project	Antioch Construction Company	246899	2022-09-20 14:09:06.911368+05:30	2022-09-20 14:09:06.911397+05:30	1	t	\N	f	f
788	PROJECT	Project	Apfel Electric Co.	246900	2022-09-20 14:09:06.911453+05:30	2022-09-20 14:09:06.911474+05:30	1	t	\N	f	f
789	PROJECT	Project	Applications to go Inc	246901	2022-09-20 14:09:06.911535+05:30	2022-09-20 14:09:06.911554+05:30	1	t	\N	f	f
790	PROJECT	Project	Aquino Apartments Dynamics	246902	2022-09-20 14:09:06.911648+05:30	2022-09-20 14:09:06.911668+05:30	1	t	\N	f	f
791	PROJECT	Project	Arcizo Automotive Sales	246903	2022-09-20 14:09:06.911719+05:30	2022-09-20 14:09:06.91173+05:30	1	t	\N	f	f
792	PROJECT	Project	Arlington Software Management	246904	2022-09-20 14:09:06.91177+05:30	2022-09-20 14:09:06.911791+05:30	1	t	\N	f	f
793	PROJECT	Project	Arnold Tanner	246905	2022-09-20 14:09:06.911852+05:30	2022-09-20 14:09:06.911872+05:30	1	t	\N	f	f
794	PROJECT	Project	Arredla and Hillseth Hardware -	246906	2022-09-20 14:09:06.911958+05:30	2022-09-20 14:09:06.911978+05:30	1	t	\N	f	f
795	PROJECT	Project	Art Institute of California	246907	2022-09-20 14:09:06.912018+05:30	2022-09-20 14:09:06.912039+05:30	1	t	\N	f	f
796	PROJECT	Project	Asch _ Agency	246908	2022-09-20 14:09:06.912099+05:30	2022-09-20 14:09:06.912119+05:30	1	t	\N	f	f
797	PROJECT	Project	Ashley Smoth	246909	2022-09-20 14:09:06.912169+05:30	2022-09-20 14:09:06.912179+05:30	1	t	\N	f	f
798	PROJECT	Project	Ashton Consulting Ltd	246910	2022-09-20 14:09:06.912402+05:30	2022-09-20 14:09:06.912439+05:30	1	t	\N	f	f
799	PROJECT	Project	Aslanian Publishing Agency	246911	2022-09-20 14:09:06.91252+05:30	2022-09-20 14:09:06.912542+05:30	1	t	\N	f	f
800	PROJECT	Project	Astry Software Holding Corp.	246912	2022-09-20 14:09:06.91261+05:30	2022-09-20 14:09:06.912632+05:30	1	t	\N	f	f
801	PROJECT	Project	Atherton Grocery	246913	2022-09-20 14:09:06.912703+05:30	2022-09-20 14:09:06.912726+05:30	1	t	\N	f	f
802	PROJECT	Project	August Li	246914	2022-09-20 14:09:06.912798+05:30	2022-09-20 14:09:06.912823+05:30	1	t	\N	f	f
803	PROJECT	Project	Ausbrooks Construction Incorporated	246915	2022-09-20 14:09:06.912881+05:30	2022-09-20 14:09:06.912892+05:30	1	t	\N	f	f
804	PROJECT	Project	Austin Builders Distributors	246916	2022-09-20 14:09:06.912936+05:30	2022-09-20 14:09:06.912947+05:30	1	t	\N	f	f
805	PROJECT	Project	Austin Publishing Inc.	246917	2022-09-20 14:09:06.912993+05:30	2022-09-20 14:09:06.913005+05:30	1	t	\N	f	f
806	PROJECT	Project	Avac Supplies Ltd.	246918	2022-09-20 14:09:06.913051+05:30	2022-09-20 14:09:06.913062+05:30	1	t	\N	f	f
807	PROJECT	Project	Avani Walters	246919	2022-09-20 14:09:06.913107+05:30	2022-09-20 14:09:06.913117+05:30	1	t	\N	f	f
808	PROJECT	Project	Axxess Group	246920	2022-09-20 14:09:06.913162+05:30	2022-09-20 14:09:06.913172+05:30	1	t	\N	f	f
809	PROJECT	Project	B-Sharp Music	246921	2022-09-20 14:09:06.913218+05:30	2022-09-20 14:09:06.913229+05:30	1	t	\N	f	f
810	PROJECT	Project	BFI Inc	246922	2022-09-20 14:09:06.913274+05:30	2022-09-20 14:09:06.913285+05:30	1	t	\N	f	f
811	PROJECT	Project	Baim Lumber -	246923	2022-09-20 14:09:06.913494+05:30	2022-09-20 14:09:06.913516+05:30	1	t	\N	f	f
812	PROJECT	Project	Bakkala Catering Distributors	246924	2022-09-20 14:09:06.91356+05:30	2022-09-20 14:09:06.913572+05:30	1	t	\N	f	f
813	PROJECT	Project	Bankey and Marris Hardware Corporation	246925	2022-09-20 14:09:06.913616+05:30	2022-09-20 14:09:06.913626+05:30	1	t	\N	f	f
814	PROJECT	Project	Barham Automotive Services	246926	2022-09-20 14:09:06.913671+05:30	2022-09-20 14:09:06.913682+05:30	1	t	\N	f	f
815	PROJECT	Project	Barich Metal Fabricators Inc.	246927	2022-09-20 14:09:06.913729+05:30	2022-09-20 14:09:06.91374+05:30	1	t	\N	f	f
816	PROJECT	Project	Barners and Rushlow Liquors Sales	246928	2022-09-20 14:09:06.913784+05:30	2022-09-20 14:09:06.913796+05:30	1	t	\N	f	f
817	PROJECT	Project	Barnhurst Title Inc.	246929	2022-09-20 14:09:06.91384+05:30	2022-09-20 14:09:06.91385+05:30	1	t	\N	f	f
818	PROJECT	Project	Baron Chess	246930	2022-09-20 14:09:06.913897+05:30	2022-09-20 14:09:06.91391+05:30	1	t	\N	f	f
819	PROJECT	Project	Bartkus Automotive Company	246931	2022-09-20 14:09:06.913958+05:30	2022-09-20 14:09:06.913969+05:30	1	t	\N	f	f
820	PROJECT	Project	Baumgarn Windows and Associates	246932	2022-09-20 14:09:06.91401+05:30	2022-09-20 14:09:06.914022+05:30	1	t	\N	f	f
821	PROJECT	Project	Bay Media Research	246933	2022-09-20 14:09:06.914068+05:30	2022-09-20 14:09:06.914081+05:30	1	t	\N	f	f
822	PROJECT	Project	BaySide Office Space	246934	2022-09-20 14:09:06.91413+05:30	2022-09-20 14:09:06.914153+05:30	1	t	\N	f	f
823	PROJECT	Project	Bayas Hardware Dynamics	246935	2022-09-20 14:09:06.914201+05:30	2022-09-20 14:09:06.914213+05:30	1	t	\N	f	f
824	PROJECT	Project	Baylore	246936	2022-09-20 14:09:06.914259+05:30	2022-09-20 14:09:06.91427+05:30	1	t	\N	f	f
825	PROJECT	Project	Beams Electric Agency	246937	2022-09-20 14:09:06.914315+05:30	2022-09-20 14:09:06.914327+05:30	1	t	\N	f	f
826	PROJECT	Project	Beatie Leasing Networking	246938	2022-09-20 14:09:06.914467+05:30	2022-09-20 14:09:06.914499+05:30	1	t	\N	f	f
827	PROJECT	Project	Beattie Batteries	246939	2022-09-20 14:09:06.914567+05:30	2022-09-20 14:09:06.91458+05:30	1	t	\N	f	f
828	PROJECT	Project	Beaubien Antiques Leasing	246940	2022-09-20 14:09:06.914628+05:30	2022-09-20 14:09:06.91465+05:30	1	t	\N	f	f
829	PROJECT	Project	Belgrade Telecom -	246941	2022-09-20 14:09:06.914713+05:30	2022-09-20 14:09:06.91475+05:30	1	t	\N	f	f
830	PROJECT	Project	Belisle Title Networking	246942	2022-09-20 14:09:06.914811+05:30	2022-09-20 14:09:06.914831+05:30	1	t	\N	f	f
831	PROJECT	Project	Below Liquors Corporation	246943	2022-09-20 14:09:06.914901+05:30	2022-09-20 14:09:06.914921+05:30	1	t	\N	f	f
832	PROJECT	Project	Bemo Publishing Corporation	246944	2022-09-20 14:09:06.914995+05:30	2022-09-20 14:09:06.915037+05:30	1	t	\N	f	f
833	PROJECT	Project	Ben Lomond Software Incorporated	246945	2022-09-20 14:09:06.915118+05:30	2022-09-20 14:09:06.915138+05:30	1	t	\N	f	f
834	PROJECT	Project	Ben Sandler	246946	2022-09-20 14:09:07.372807+05:30	2022-09-20 14:09:07.372859+05:30	1	t	\N	f	f
835	PROJECT	Project	Benabides and Louris Builders Services	246947	2022-09-20 14:09:07.372936+05:30	2022-09-20 14:09:07.372967+05:30	1	t	\N	f	f
836	PROJECT	Project	Benbow Software	246948	2022-09-20 14:09:07.373036+05:30	2022-09-20 14:09:07.373303+05:30	1	t	\N	f	f
837	PROJECT	Project	Benge Liquors Incorporated	246949	2022-09-20 14:09:07.373382+05:30	2022-09-20 14:09:07.373412+05:30	1	t	\N	f	f
838	PROJECT	Project	Bennett Consulting	246950	2022-09-20 14:09:07.373481+05:30	2022-09-20 14:09:07.373511+05:30	1	t	\N	f	f
839	PROJECT	Project	Benton Construction Inc.	246951	2022-09-20 14:09:07.373719+05:30	2022-09-20 14:09:07.373779+05:30	1	t	\N	f	f
840	PROJECT	Project	Berliner Apartments Networking	246952	2022-09-20 14:09:07.373898+05:30	2022-09-20 14:09:07.373943+05:30	1	t	\N	f	f
841	PROJECT	Project	Berschauer Leasing Rentals	246953	2022-09-20 14:09:07.374057+05:30	2022-09-20 14:09:07.37409+05:30	1	t	\N	f	f
842	PROJECT	Project	Berthelette Antiques	246954	2022-09-20 14:09:07.374161+05:30	2022-09-20 14:09:07.374191+05:30	1	t	\N	f	f
843	PROJECT	Project	Bertot Attorneys Company	246955	2022-09-20 14:09:07.374257+05:30	2022-09-20 14:09:07.374287+05:30	1	t	\N	f	f
844	PROJECT	Project	Bertulli & Assoc	246956	2022-09-20 14:09:07.374695+05:30	2022-09-20 14:09:07.374729+05:30	1	t	\N	f	f
845	PROJECT	Project	Bethurum Telecom Sales	246957	2022-09-20 14:09:07.374796+05:30	2022-09-20 14:09:07.374833+05:30	1	t	\N	f	f
846	PROJECT	Project	Better Buy	246958	2022-09-20 14:09:07.37493+05:30	2022-09-20 14:09:07.37496+05:30	1	t	\N	f	f
847	PROJECT	Project	Bezak Construction Dynamics	246959	2022-09-20 14:09:07.375026+05:30	2022-09-20 14:09:07.375055+05:30	1	t	\N	f	f
848	PROJECT	Project	Bicycle Trailers	246960	2022-09-20 14:09:07.37512+05:30	2022-09-20 14:09:07.375149+05:30	1	t	\N	f	f
849	PROJECT	Project	Big 5 Sporting Goods	246961	2022-09-20 14:09:07.375228+05:30	2022-09-20 14:09:07.3754+05:30	1	t	\N	f	f
850	PROJECT	Project	Big Bear Lake Electric	246962	2022-09-20 14:09:07.375504+05:30	2022-09-20 14:09:07.375548+05:30	1	t	\N	f	f
851	PROJECT	Project	Big Bear Lake Plumbing Holding Corp.	246963	2022-09-20 14:09:07.375647+05:30	2022-09-20 14:09:07.375691+05:30	1	t	\N	f	f
852	PROJECT	Project	Billafuerte Software Company	246964	2022-09-20 14:09:07.375791+05:30	2022-09-20 14:09:07.375833+05:30	1	t	\N	f	f
853	PROJECT	Project	Bisonette Leasing	246965	2022-09-20 14:09:07.375969+05:30	2022-09-20 14:09:07.376015+05:30	1	t	\N	f	f
854	PROJECT	Project	Bleser Antiques Incorporated	246966	2022-09-20 14:09:07.376136+05:30	2022-09-20 14:09:07.376189+05:30	1	t	\N	f	f
855	PROJECT	Project	Blier Lumber Dynamics	246967	2022-09-20 14:09:07.376384+05:30	2022-09-20 14:09:07.376413+05:30	1	t	\N	f	f
856	PROJECT	Project	Blue Street Liquor Store	246968	2022-09-20 14:09:07.376506+05:30	2022-09-20 14:09:07.376551+05:30	1	t	\N	f	f
857	PROJECT	Project	Bob Ledner	246969	2022-09-20 14:09:07.376682+05:30	2022-09-20 14:09:07.376733+05:30	1	t	\N	f	f
858	PROJECT	Project	Bob Smith (bsmith@bobsmith.com)	246970	2022-09-20 14:09:07.376839+05:30	2022-09-20 14:09:07.376874+05:30	1	t	\N	f	f
859	PROJECT	Project	Bob Walsh Funiture Store	246971	2022-09-20 14:09:07.376951+05:30	2022-09-20 14:09:07.376978+05:30	1	t	\N	f	f
860	PROJECT	Project	Bobby Kelly	246972	2022-09-20 14:09:07.37704+05:30	2022-09-20 14:09:07.377067+05:30	1	t	\N	f	f
861	PROJECT	Project	Bobby Strands (Bobby@Strands.com)	246973	2022-09-20 14:09:07.377171+05:30	2022-09-20 14:09:07.37734+05:30	1	t	\N	f	f
862	PROJECT	Project	Bochenek and Skoog Liquors Company	246974	2022-09-20 14:09:07.377477+05:30	2022-09-20 14:09:07.377524+05:30	1	t	\N	f	f
863	PROJECT	Project	Bodfish Liquors Corporation	246975	2022-09-20 14:09:07.377629+05:30	2022-09-20 14:09:07.377659+05:30	1	t	\N	f	f
864	PROJECT	Project	Boise Antiques and Associates	246976	2022-09-20 14:09:07.37772+05:30	2022-09-20 14:09:07.377749+05:30	1	t	\N	f	f
865	PROJECT	Project	Boise Publishing Co.	246977	2022-09-20 14:09:07.377809+05:30	2022-09-20 14:09:07.377838+05:30	1	t	\N	f	f
866	PROJECT	Project	Boisselle Windows Distributors	246978	2022-09-20 14:09:07.377897+05:30	2022-09-20 14:09:07.377926+05:30	1	t	\N	f	f
867	PROJECT	Project	Bolder Construction Inc.	246979	2022-09-20 14:09:07.377986+05:30	2022-09-20 14:09:07.378015+05:30	1	t	\N	f	f
868	PROJECT	Project	Bollman Attorneys Company	246980	2022-09-20 14:09:07.378154+05:30	2022-09-20 14:09:07.3782+05:30	1	t	\N	f	f
869	PROJECT	Project	Bona Source	246981	2022-09-20 14:09:07.378379+05:30	2022-09-20 14:09:07.378409+05:30	1	t	\N	f	f
870	PROJECT	Project	Boney Electric Dynamics	246982	2022-09-20 14:09:07.378471+05:30	2022-09-20 14:09:07.3785+05:30	1	t	\N	f	f
871	PROJECT	Project	Borowski Catering Management	246983	2022-09-20 14:09:07.378596+05:30	2022-09-20 14:09:07.378638+05:30	1	t	\N	f	f
872	PROJECT	Project	Botero Electric Co.	246984	2022-09-20 14:09:07.378737+05:30	2022-09-20 14:09:07.378774+05:30	1	t	\N	f	f
873	PROJECT	Project	Bowling Green Painting Incorporated	246985	2022-09-20 14:09:07.378864+05:30	2022-09-20 14:09:07.378899+05:30	1	t	\N	f	f
874	PROJECT	Project	Boynton Beach Title Networking	246986	2022-09-20 14:09:07.378988+05:30	2022-09-20 14:09:07.379025+05:30	1	t	\N	f	f
875	PROJECT	Project	Bracken Works Inc	246987	2022-09-20 14:09:07.379115+05:30	2022-09-20 14:09:07.379153+05:30	1	t	\N	f	f
876	PROJECT	Project	Braithwaite Tech	246988	2022-09-20 14:09:07.379243+05:30	2022-09-20 14:09:07.379281+05:30	1	t	\N	f	f
877	PROJECT	Project	Bramucci Construction	246989	2022-09-20 14:09:07.379488+05:30	2022-09-20 14:09:07.379528+05:30	1	t	\N	f	f
878	PROJECT	Project	Brandwein Builders Fabricators	246990	2022-09-20 14:09:07.379618+05:30	2022-09-20 14:09:07.379656+05:30	1	t	\N	f	f
879	PROJECT	Project	Brea Painting Company	246991	2022-09-20 14:09:07.379744+05:30	2022-09-20 14:09:07.379797+05:30	1	t	\N	f	f
880	PROJECT	Project	Brent Apartments Rentals	246992	2022-09-20 14:09:07.379873+05:30	2022-09-20 14:09:07.379902+05:30	1	t	\N	f	f
881	PROJECT	Project	Brewers Retail	246993	2022-09-20 14:09:07.379963+05:30	2022-09-20 14:09:07.379992+05:30	1	t	\N	f	f
882	PROJECT	Project	Brick Metal Fabricators Services	246994	2022-09-20 14:09:07.380053+05:30	2022-09-20 14:09:07.380539+05:30	1	t	\N	f	f
883	PROJECT	Project	Bridgham Electric Inc.	246995	2022-09-20 14:09:07.380748+05:30	2022-09-20 14:09:07.380897+05:30	1	t	\N	f	f
884	PROJECT	Project	Bright Brothers Design	246996	2022-09-20 14:09:07.398587+05:30	2022-09-20 14:09:07.398627+05:30	1	t	\N	f	f
885	PROJECT	Project	Broadnay and Posthuma Lumber and Associates	246997	2022-09-20 14:09:07.398688+05:30	2022-09-20 14:09:07.398716+05:30	1	t	\N	f	f
886	PROJECT	Project	Brochard Metal Fabricators Incorporated	246998	2022-09-20 14:09:07.398772+05:30	2022-09-20 14:09:07.398799+05:30	1	t	\N	f	f
887	PROJECT	Project	Brosey Antiques -	246999	2022-09-20 14:09:07.398856+05:30	2022-09-20 14:09:07.398883+05:30	1	t	\N	f	f
888	PROJECT	Project	Bruce Storm	247000	2022-09-20 14:09:07.398939+05:30	2022-09-20 14:09:07.398966+05:30	1	t	\N	f	f
889	PROJECT	Project	Brutsch Builders Incorporated	247001	2022-09-20 14:09:07.399023+05:30	2022-09-20 14:09:07.39905+05:30	1	t	\N	f	f
890	PROJECT	Project	Brytor Inetrnational	247002	2022-09-20 14:09:07.399107+05:30	2022-09-20 14:09:07.399134+05:30	1	t	\N	f	f
891	PROJECT	Project	Burney and Oesterreich Title Manufacturing	247003	2022-09-20 14:09:07.399189+05:30	2022-09-20 14:09:07.399217+05:30	1	t	\N	f	f
892	PROJECT	Project	Buroker Markets Incorporated	247004	2022-09-20 14:09:07.399273+05:30	2022-09-20 14:09:07.3993+05:30	1	t	\N	f	f
893	PROJECT	Project	Busacker Liquors Services	247005	2022-09-20 14:09:07.399366+05:30	2022-09-20 14:09:07.399504+05:30	1	t	\N	f	f
894	PROJECT	Project	Bushnell	247006	2022-09-20 14:09:07.39956+05:30	2022-09-20 14:09:07.399571+05:30	1	t	\N	f	f
895	PROJECT	Project	By The Beach Cafe	247007	2022-09-20 14:09:07.399617+05:30	2022-09-20 14:09:07.399638+05:30	1	t	\N	f	f
896	PROJECT	Project	CH2M Hill Ltd	247008	2022-09-20 14:09:07.399698+05:30	2022-09-20 14:09:07.399728+05:30	1	t	\N	f	f
897	PROJECT	Project	CICA	247009	2022-09-20 14:09:07.399778+05:30	2022-09-20 14:09:07.39979+05:30	1	t	\N	f	f
898	PROJECT	Project	CIS Environmental Services	247010	2022-09-20 14:09:07.399839+05:30	2022-09-20 14:09:07.399868+05:30	1	t	\N	f	f
899	PROJECT	Project	CPS ltd	247011	2022-09-20 14:09:07.399927+05:30	2022-09-20 14:09:07.399948+05:30	1	t	\N	f	f
900	PROJECT	Project	CPSA	247012	2022-09-20 14:09:07.400008+05:30	2022-09-20 14:09:07.400037+05:30	1	t	\N	f	f
901	PROJECT	Project	CVM Business Solutions	247013	2022-09-20 14:09:07.400088+05:30	2022-09-20 14:09:07.400101+05:30	1	t	\N	f	f
902	PROJECT	Project	Caleb Attorneys Distributors	247014	2022-09-20 14:09:07.40015+05:30	2022-09-20 14:09:07.400179+05:30	1	t	\N	f	f
903	PROJECT	Project	Calley Leasing and Associates	247015	2022-09-20 14:09:07.400323+05:30	2022-09-20 14:09:07.400731+05:30	1	t	\N	f	f
904	PROJECT	Project	Cambareri Painting Sales	247016	2022-09-20 14:09:07.400868+05:30	2022-09-20 14:09:07.400894+05:30	1	t	\N	f	f
905	PROJECT	Project	Canadian Customer	247017	2022-09-20 14:09:07.400947+05:30	2022-09-20 14:09:07.400976+05:30	1	t	\N	f	f
906	PROJECT	Project	Canuck Door Systems Co.	247018	2022-09-20 14:09:07.401036+05:30	2022-09-20 14:09:07.401065+05:30	1	t	\N	f	f
907	PROJECT	Project	Capano Labs	247019	2022-09-20 14:09:07.401125+05:30	2022-09-20 14:09:07.401154+05:30	1	t	\N	f	f
908	PROJECT	Project	Caquias and Jank Catering Distributors	247020	2022-09-20 14:09:07.401321+05:30	2022-09-20 14:09:07.40136+05:30	1	t	\N	f	f
909	PROJECT	Project	Careymon Dudley	247021	2022-09-20 14:09:07.401421+05:30	2022-09-20 14:09:07.40145+05:30	1	t	\N	f	f
910	PROJECT	Project	Carloni Builders Company	247022	2022-09-20 14:09:07.401511+05:30	2022-09-20 14:09:07.40154+05:30	1	t	\N	f	f
911	PROJECT	Project	Carlos Beato	247023	2022-09-20 14:09:07.401595+05:30	2022-09-20 14:09:07.401615+05:30	1	t	\N	f	f
912	PROJECT	Project	Carmel Valley Metal Fabricators Holding Corp.	247024	2022-09-20 14:09:07.401675+05:30	2022-09-20 14:09:07.401705+05:30	1	t	\N	f	f
913	PROJECT	Project	Carpentersville Publishing	247025	2022-09-20 14:09:07.402175+05:30	2022-09-20 14:09:07.402212+05:30	1	t	\N	f	f
914	PROJECT	Project	Carpinteria Leasing Services	247026	2022-09-20 14:09:07.402493+05:30	2022-09-20 14:09:07.402524+05:30	1	t	\N	f	f
915	PROJECT	Project	Carrie Davis	247027	2022-09-20 14:09:07.403082+05:30	2022-09-20 14:09:07.403117+05:30	1	t	\N	f	f
916	PROJECT	Project	Cash & Warren	247028	2022-09-20 14:09:07.403169+05:30	2022-09-20 14:09:07.40319+05:30	1	t	\N	f	f
917	PROJECT	Project	Castek Inc	247029	2022-09-20 14:09:07.403339+05:30	2022-09-20 14:09:07.403369+05:30	1	t	\N	f	f
918	PROJECT	Project	Casuse Liquors Inc.	247030	2022-09-20 14:09:07.40343+05:30	2022-09-20 14:09:07.403458+05:30	1	t	\N	f	f
919	PROJECT	Project	Cathy Thoms	247031	2022-09-20 14:09:07.403533+05:30	2022-09-20 14:09:07.403653+05:30	1	t	\N	f	f
920	PROJECT	Project	Cawthron and Ullo Windows Corporation	247032	2022-09-20 14:09:07.403834+05:30	2022-09-20 14:09:07.403879+05:30	1	t	\N	f	f
922	PROJECT	Project	Central Islip Antiques Fabricators	247034	2022-09-20 14:09:07.404073+05:30	2022-09-20 14:09:07.404106+05:30	1	t	\N	f	f
923	PROJECT	Project	Cerritos Telecom and Associates	247035	2022-09-20 14:09:07.404202+05:30	2022-09-20 14:09:07.404237+05:30	1	t	\N	f	f
924	PROJECT	Project	Chamberlain Service Ltd	247036	2022-09-20 14:09:07.404472+05:30	2022-09-20 14:09:07.404495+05:30	1	t	\N	f	f
925	PROJECT	Project	Champaign Painting Rentals	247037	2022-09-20 14:09:07.404556+05:30	2022-09-20 14:09:07.404577+05:30	1	t	\N	f	f
926	PROJECT	Project	Chandrasekara Markets Sales	247038	2022-09-20 14:09:07.404621+05:30	2022-09-20 14:09:07.404641+05:30	1	t	\N	f	f
927	PROJECT	Project	Channer Antiques Dynamics	247039	2022-09-20 14:09:07.404696+05:30	2022-09-20 14:09:07.404717+05:30	1	t	\N	f	f
928	PROJECT	Project	Charlotte Hospital Incorporated	247040	2022-09-20 14:09:07.404777+05:30	2022-09-20 14:09:07.404806+05:30	1	t	\N	f	f
929	PROJECT	Project	Cheese Factory	247041	2022-09-20 14:09:07.404866+05:30	2022-09-20 14:09:07.404895+05:30	1	t	\N	f	f
930	PROJECT	Project	Chess Art Gallery	247042	2022-09-20 14:09:07.404976+05:30	2022-09-20 14:09:07.405127+05:30	1	t	\N	f	f
931	PROJECT	Project	Chiaminto Attorneys Agency	247043	2022-09-20 14:09:07.405446+05:30	2022-09-20 14:09:07.405496+05:30	1	t	\N	f	f
932	PROJECT	Project	China Cuisine	247044	2022-09-20 14:09:07.405601+05:30	2022-09-20 14:09:07.405649+05:30	1	t	\N	f	f
933	PROJECT	Project	Chittenden _ Agency	247045	2022-09-20 14:09:07.405738+05:30	2022-09-20 14:09:07.405758+05:30	1	t	\N	f	f
934	PROJECT	Project	Cino & Cino	247046	2022-09-20 14:09:07.422009+05:30	2022-09-20 14:09:07.422077+05:30	1	t	\N	f	f
935	PROJECT	Project	Circuit Cities	247047	2022-09-20 14:09:07.4225+05:30	2022-09-20 14:09:07.423089+05:30	1	t	\N	f	f
936	PROJECT	Project	Clayton and Bubash Telecom Services	247048	2022-09-20 14:09:07.426042+05:30	2022-09-20 14:09:07.426075+05:30	1	t	\N	f	f
937	PROJECT	Project	Clubb Electric Co.	247049	2022-09-20 14:09:07.427139+05:30	2022-09-20 14:09:07.42751+05:30	1	t	\N	f	f
938	PROJECT	Project	Cochell Markets Group	247050	2022-09-20 14:09:07.427671+05:30	2022-09-20 14:09:07.428511+05:30	1	t	\N	f	f
939	PROJECT	Project	Coen Publishing Co.	247051	2022-09-20 14:09:07.428747+05:30	2022-09-20 14:09:07.428931+05:30	1	t	\N	f	f
940	PROJECT	Project	Coklow Leasing Dynamics	247052	2022-09-20 14:09:07.429722+05:30	2022-09-20 14:09:07.429775+05:30	1	t	\N	f	f
941	PROJECT	Project	Coletta Hospital Inc.	247053	2022-09-20 14:09:07.430023+05:30	2022-09-20 14:09:07.430073+05:30	1	t	\N	f	f
942	PROJECT	Project	Colony Antiques	247054	2022-09-20 14:09:07.430394+05:30	2022-09-20 14:09:07.430424+05:30	1	t	\N	f	f
943	PROJECT	Project	Colorado Springs Leasing Fabricators	247055	2022-09-20 14:09:07.430483+05:30	2022-09-20 14:09:07.43052+05:30	1	t	\N	f	f
944	PROJECT	Project	Colosimo Catering and Associates	247056	2022-09-20 14:09:07.43059+05:30	2022-09-20 14:09:07.430628+05:30	1	t	\N	f	f
945	PROJECT	Project	Computer Literacy	247057	2022-09-20 14:09:07.431167+05:30	2022-09-20 14:09:07.431323+05:30	1	t	\N	f	f
946	PROJECT	Project	Computer Training Associates	247058	2022-09-20 14:09:07.431391+05:30	2022-09-20 14:09:07.431413+05:30	1	t	\N	f	f
947	PROJECT	Project	Connectus	247059	2022-09-20 14:09:07.431468+05:30	2022-09-20 14:09:07.4315+05:30	1	t	\N	f	f
948	PROJECT	Project	Constanza Liquors -	247060	2022-09-20 14:09:07.431896+05:30	2022-09-20 14:09:07.431927+05:30	1	t	\N	f	f
949	PROJECT	Project	Conteras Liquors Agency	247061	2022-09-20 14:09:07.43198+05:30	2022-09-20 14:09:07.432001+05:30	1	t	\N	f	f
950	PROJECT	Project	Conterras and Katen Attorneys Services	247062	2022-09-20 14:09:07.432058+05:30	2022-09-20 14:09:07.432079+05:30	1	t	\N	f	f
951	PROJECT	Project	Convery Attorneys and Associates	247063	2022-09-20 14:09:07.432413+05:30	2022-09-20 14:09:07.432438+05:30	1	t	\N	f	f
952	PROJECT	Project	Conway Products	247064	2022-09-20 14:09:07.432497+05:30	2022-09-20 14:09:07.432518+05:30	1	t	\N	f	f
953	PROJECT	Project	Cooler Title Company	247065	2022-09-20 14:09:07.432571+05:30	2022-09-20 14:09:07.432655+05:30	1	t	\N	f	f
954	PROJECT	Project	Cooper Equipment	247066	2022-09-20 14:09:07.432712+05:30	2022-09-20 14:09:07.432733+05:30	1	t	\N	f	f
955	PROJECT	Project	Cooper Industries	247067	2022-09-20 14:09:07.432794+05:30	2022-09-20 14:09:07.432823+05:30	1	t	\N	f	f
956	PROJECT	Project	Core Care Canada	247068	2022-09-20 14:09:07.432884+05:30	2022-09-20 14:09:07.433138+05:30	1	t	\N	f	f
957	PROJECT	Project	Core Care Technologies Inc.	247069	2022-09-20 14:09:07.433474+05:30	2022-09-20 14:09:07.433507+05:30	1	t	\N	f	f
958	PROJECT	Project	Coressel _ -	247070	2022-09-20 14:09:07.433706+05:30	2022-09-20 14:09:07.433792+05:30	1	t	\N	f	f
959	PROJECT	Project	Cosimini Software Agency	247071	2022-09-20 14:09:07.433881+05:30	2022-09-20 14:09:07.433992+05:30	1	t	\N	f	f
960	PROJECT	Project	Cotterman Software Company	247072	2022-09-20 14:09:07.43405+05:30	2022-09-20 14:09:07.434136+05:30	1	t	\N	f	f
961	PROJECT	Project	Cottew Publishing Inc.	247073	2022-09-20 14:09:07.434192+05:30	2022-09-20 14:09:07.434213+05:30	1	t	\N	f	f
962	PROJECT	Project	Cottman Publishing Manufacturing	247074	2022-09-20 14:09:07.434466+05:30	2022-09-20 14:09:07.434575+05:30	1	t	\N	f	f
963	PROJECT	Project	Coxum Software Dynamics	247075	2022-09-20 14:09:07.434741+05:30	2022-09-20 14:09:07.434767+05:30	1	t	\N	f	f
964	PROJECT	Project	Cray Systems	247076	2022-09-20 14:09:07.434816+05:30	2022-09-20 14:09:07.434837+05:30	1	t	\N	f	f
965	PROJECT	Project	Creasman Antiques Holding Corp.	247077	2022-09-20 14:09:07.435453+05:30	2022-09-20 14:09:07.435499+05:30	1	t	\N	f	f
966	PROJECT	Project	Creighton & Company	247078	2022-09-20 14:09:07.435579+05:30	2022-09-20 14:09:07.435608+05:30	1	t	\N	f	f
967	PROJECT	Project	Crighton Catering Company	247079	2022-09-20 14:09:07.435984+05:30	2022-09-20 14:09:07.43603+05:30	1	t	\N	f	f
968	PROJECT	Project	Crisafulli Hardware Holding Corp.	247080	2022-09-20 14:09:07.436318+05:30	2022-09-20 14:09:07.43635+05:30	1	t	\N	f	f
969	PROJECT	Project	Cruce Builders	247081	2022-09-20 14:09:07.436405+05:30	2022-09-20 14:09:07.436419+05:30	1	t	\N	f	f
970	PROJECT	Project	Culprit Inc.	247082	2022-09-20 14:09:07.436469+05:30	2022-09-20 14:09:07.436489+05:30	1	t	\N	f	f
971	PROJECT	Project	Cwik and Klayman Metal Fabricators Holding Corp.	247083	2022-09-20 14:09:07.436542+05:30	2022-09-20 14:09:07.436571+05:30	1	t	\N	f	f
972	PROJECT	Project	Cytec Industries Inc	247084	2022-09-20 14:09:07.436732+05:30	2022-09-20 14:09:07.436777+05:30	1	t	\N	f	f
973	PROJECT	Project	D&H Manufacturing	247085	2022-09-20 14:09:07.437477+05:30	2022-09-20 14:09:07.437554+05:30	1	t	\N	f	f
974	PROJECT	Project	Dale Jenson	247086	2022-09-20 14:09:07.437743+05:30	2022-09-20 14:09:07.437773+05:30	1	t	\N	f	f
975	PROJECT	Project	Dambrose and Ottum Leasing Holding Corp.	247087	2022-09-20 14:09:07.437921+05:30	2022-09-20 14:09:07.437947+05:30	1	t	\N	f	f
1190	PROJECT	Project	Iain Bennett	247302	2022-09-20 14:09:07.944534+05:30	2022-09-20 14:09:07.944573+05:30	1	t	\N	f	f
976	PROJECT	Project	Danniels Antiques Inc.	247088	2022-09-20 14:09:07.438046+05:30	2022-09-20 14:09:07.438088+05:30	1	t	\N	f	f
977	PROJECT	Project	Daquino Painting -	247089	2022-09-20 14:09:07.438424+05:30	2022-09-20 14:09:07.438438+05:30	1	t	\N	f	f
978	PROJECT	Project	Dary Construction Corporation	247090	2022-09-20 14:09:07.43884+05:30	2022-09-20 14:09:07.438879+05:30	1	t	\N	f	f
979	PROJECT	Project	David Langhor	247091	2022-09-20 14:09:07.438955+05:30	2022-09-20 14:09:07.438984+05:30	1	t	\N	f	f
980	PROJECT	Project	Days Creek Electric Services	247092	2022-09-20 14:09:07.439203+05:30	2022-09-20 14:09:07.439673+05:30	1	t	\N	f	f
981	PROJECT	Project	Deblasio Painting Holding Corp.	247093	2022-09-20 14:09:07.439801+05:30	2022-09-20 14:09:07.439847+05:30	1	t	\N	f	f
982	PROJECT	Project	Defaveri Construction	247094	2022-09-20 14:09:07.439977+05:30	2022-09-20 14:09:07.440015+05:30	1	t	\N	f	f
983	PROJECT	Project	Dehaney Liquors Co.	247095	2022-09-20 14:09:07.44008+05:30	2022-09-20 14:09:07.44011+05:30	1	t	\N	f	f
984	PROJECT	Project	DelRey Distributors	247096	2022-09-20 14:09:07.460764+05:30	2022-09-20 14:09:07.460811+05:30	1	t	\N	f	f
985	PROJECT	Project	DellPack (UK)	247097	2022-09-20 14:09:07.46088+05:30	2022-09-20 14:09:07.460909+05:30	1	t	\N	f	f
986	PROJECT	Project	Demaire Automotive Systems	247098	2022-09-20 14:09:07.460972+05:30	2022-09-20 14:09:07.460994+05:30	1	t	\N	f	f
987	PROJECT	Project	Denise Sweet	247099	2022-09-20 14:09:07.46104+05:30	2022-09-20 14:09:07.461052+05:30	1	t	\N	f	f
988	PROJECT	Project	Dennis Batemanger	247100	2022-09-20 14:09:07.461101+05:30	2022-09-20 14:09:07.46113+05:30	1	t	\N	f	f
989	PROJECT	Project	Diamond Bar Plumbing	247101	2022-09-20 14:09:07.461726+05:30	2022-09-20 14:09:07.46203+05:30	1	t	\N	f	f
990	PROJECT	Project	Diekema Attorneys Manufacturing	247102	2022-09-20 14:09:07.462631+05:30	2022-09-20 14:09:07.462663+05:30	1	t	\N	f	f
991	PROJECT	Project	Difebbo and Lewelling Markets Agency	247103	2022-09-20 14:09:07.462721+05:30	2022-09-20 14:09:07.462743+05:30	1	t	\N	f	f
992	PROJECT	Project	Dillain Collins	247104	2022-09-20 14:09:07.462809+05:30	2022-09-20 14:09:07.462838+05:30	1	t	\N	f	f
993	PROJECT	Project	Diluzio Automotive Group	247105	2022-09-20 14:09:07.462938+05:30	2022-09-20 14:09:07.463894+05:30	1	t	\N	f	f
994	PROJECT	Project	Dipiano Automotive Sales	247106	2022-09-20 14:09:07.464158+05:30	2022-09-20 14:09:07.464202+05:30	1	t	\N	f	f
995	PROJECT	Project	Doerrer Apartments Inc.	247107	2022-09-20 14:09:07.464945+05:30	2022-09-20 14:09:07.465024+05:30	1	t	\N	f	f
996	PROJECT	Project	Dogan Painting Leasing	247108	2022-09-20 14:09:07.465603+05:30	2022-09-20 14:09:07.465749+05:30	1	t	\N	f	f
997	PROJECT	Project	Doiel and Mcdivitt Construction Holding Corp.	247109	2022-09-20 14:09:07.465917+05:30	2022-09-20 14:09:07.465944+05:30	1	t	\N	f	f
998	PROJECT	Project	Dolfi Software Group	247110	2022-09-20 14:09:07.466148+05:30	2022-09-20 14:09:07.46618+05:30	1	t	\N	f	f
999	PROJECT	Project	Dominion Consulting	247111	2022-09-20 14:09:07.466238+05:30	2022-09-20 14:09:07.466253+05:30	1	t	\N	f	f
1000	PROJECT	Project	Dorey Attorneys Distributors	247112	2022-09-20 14:09:07.466294+05:30	2022-09-20 14:09:07.466315+05:30	1	t	\N	f	f
1001	PROJECT	Project	Dorminy Windows Rentals	247113	2022-09-20 14:09:07.467103+05:30	2022-09-20 14:09:07.467142+05:30	1	t	\N	f	f
1002	PROJECT	Project	Douse Telecom Leasing	247114	2022-09-20 14:09:07.467562+05:30	2022-09-20 14:09:07.467591+05:30	1	t	\N	f	f
1003	PROJECT	Project	Downey Catering Agency	247115	2022-09-20 14:09:07.46766+05:30	2022-09-20 14:09:07.467694+05:30	1	t	\N	f	f
1004	PROJECT	Project	Downey and Sweezer Electric Group	247116	2022-09-20 14:09:07.46811+05:30	2022-09-20 14:09:07.468144+05:30	1	t	\N	f	f
1005	PROJECT	Project	Dries Hospital Manufacturing	247117	2022-09-20 14:09:07.468216+05:30	2022-09-20 14:09:07.468258+05:30	1	t	\N	f	f
1006	PROJECT	Project	Drown Markets Services	247118	2022-09-20 14:09:07.468729+05:30	2022-09-20 14:09:07.468762+05:30	1	t	\N	f	f
1007	PROJECT	Project	Drumgoole Attorneys Corporation	247119	2022-09-20 14:09:07.468873+05:30	2022-09-20 14:09:07.468898+05:30	1	t	\N	f	f
1008	PROJECT	Project	Duhamel Lumber Co.	247120	2022-09-20 14:09:07.468951+05:30	2022-09-20 14:09:07.468976+05:30	1	t	\N	f	f
1009	PROJECT	Project	Duman Windows Sales	247121	2022-09-20 14:09:07.469029+05:30	2022-09-20 14:09:07.469097+05:30	1	t	\N	f	f
1010	PROJECT	Project	Dunlevy Software Corporation	247122	2022-09-20 14:09:07.46959+05:30	2022-09-20 14:09:07.469614+05:30	1	t	\N	f	f
1011	PROJECT	Project	Duroseau Publishing	247123	2022-09-20 14:09:07.469682+05:30	2022-09-20 14:09:07.46971+05:30	1	t	\N	f	f
1012	PROJECT	Project	Eachus Metal Fabricators Incorporated	247124	2022-09-20 14:09:07.469756+05:30	2022-09-20 14:09:07.469777+05:30	1	t	\N	f	f
1013	PROJECT	Project	Eberlein and Preslipsky _ Holding Corp.	247125	2022-09-20 14:09:07.477884+05:30	2022-09-20 14:09:07.47816+05:30	1	t	\N	f	f
1014	PROJECT	Project	Eckerman Leasing Management	247126	2022-09-20 14:09:07.478266+05:30	2022-09-20 14:09:07.478301+05:30	1	t	\N	f	f
1015	PROJECT	Project	Eckler Leasing	247127	2022-09-20 14:09:07.478828+05:30	2022-09-20 14:09:07.47894+05:30	1	t	\N	f	f
1016	PROJECT	Project	Eckrote Construction Fabricators	247128	2022-09-20 14:09:07.479018+05:30	2022-09-20 14:09:07.479039+05:30	1	t	\N	f	f
1017	PROJECT	Project	Ed Obuz	247129	2022-09-20 14:09:07.479169+05:30	2022-09-20 14:09:07.479201+05:30	1	t	\N	f	f
1018	PROJECT	Project	Ede Title Rentals	247130	2022-09-20 14:09:07.479539+05:30	2022-09-20 14:09:07.479574+05:30	1	t	\N	f	f
1019	PROJECT	Project	Edin Lumber Distributors	247131	2022-09-20 14:09:07.479627+05:30	2022-09-20 14:09:07.479649+05:30	1	t	\N	f	f
1020	PROJECT	Project	Effectiovation Inc	247132	2022-09-20 14:09:07.479703+05:30	2022-09-20 14:09:07.479724+05:30	1	t	\N	f	f
1021	PROJECT	Project	Efficiency Engineering	247133	2022-09-20 14:09:07.479801+05:30	2022-09-20 14:09:07.480171+05:30	1	t	\N	f	f
1022	PROJECT	Project	Eichner Antiques -	247134	2022-09-20 14:09:07.480343+05:30	2022-09-20 14:09:07.48037+05:30	1	t	\N	f	f
1023	PROJECT	Project	El Paso Hardware Co.	247135	2022-09-20 14:09:07.480434+05:30	2022-09-20 14:09:07.480464+05:30	1	t	\N	f	f
1024	PROJECT	Project	Electronics Direct to You	247136	2022-09-20 14:09:07.48076+05:30	2022-09-20 14:09:07.480791+05:30	1	t	\N	f	f
1025	PROJECT	Project	Elegance Interior Design	247137	2022-09-20 14:09:07.481279+05:30	2022-09-20 14:09:07.481319+05:30	1	t	\N	f	f
1026	PROJECT	Project	Eliszewski Windows Dynamics	247138	2022-09-20 14:09:07.481426+05:30	2022-09-20 14:09:07.481823+05:30	1	t	\N	f	f
1027	PROJECT	Project	Ellenberger Windows Management	247139	2022-09-20 14:09:07.481906+05:30	2022-09-20 14:09:07.481929+05:30	1	t	\N	f	f
1028	PROJECT	Project	Emergys	247140	2022-09-20 14:09:07.482039+05:30	2022-09-20 14:09:07.482062+05:30	1	t	\N	f	f
1029	PROJECT	Project	Empire Financial Group	247141	2022-09-20 14:09:07.482115+05:30	2022-09-20 14:09:07.482136+05:30	1	t	\N	f	f
1030	PROJECT	Project	Engelkemier Catering Management	247142	2022-09-20 14:09:07.482186+05:30	2022-09-20 14:09:07.4822+05:30	1	t	\N	f	f
1031	PROJECT	Project	Epling Builders Inc.	247143	2022-09-20 14:09:07.48289+05:30	2022-09-20 14:09:07.482928+05:30	1	t	\N	f	f
1032	PROJECT	Project	Eric Korb	247144	2022-09-20 14:09:07.483238+05:30	2022-09-20 14:09:07.483276+05:30	1	t	\N	f	f
1033	PROJECT	Project	Eric Schmidt	247145	2022-09-20 14:09:07.483343+05:30	2022-09-20 14:09:07.483674+05:30	1	t	\N	f	f
1034	PROJECT	Project	Erin Kessman	247146	2022-09-20 14:09:07.907998+05:30	2022-09-20 14:09:07.908042+05:30	1	t	\N	f	f
1035	PROJECT	Project	Ertle Painting Leasing	247147	2022-09-20 14:09:07.908108+05:30	2022-09-20 14:09:07.908137+05:30	1	t	\N	f	f
1036	PROJECT	Project	Espar Heater Systems	247148	2022-09-20 14:09:07.90836+05:30	2022-09-20 14:09:07.90839+05:30	1	t	\N	f	f
1037	PROJECT	Project	Estanislau and Brodka Electric Holding Corp.	247149	2022-09-20 14:09:07.908461+05:30	2022-09-20 14:09:07.908489+05:30	1	t	\N	f	f
1038	PROJECT	Project	Estee Lauder	247150	2022-09-20 14:09:07.908548+05:30	2022-09-20 14:09:07.908576+05:30	1	t	\N	f	f
1039	PROJECT	Project	Estevez Title and Associates	247151	2022-09-20 14:09:07.908634+05:30	2022-09-20 14:09:07.908661+05:30	1	t	\N	f	f
1040	PROJECT	Project	Eugenio	247152	2022-09-20 14:09:07.908719+05:30	2022-09-20 14:09:07.908746+05:30	1	t	\N	f	f
1041	PROJECT	Project	Evans Leasing Fabricators	247153	2022-09-20 14:09:07.908803+05:30	2022-09-20 14:09:07.90883+05:30	1	t	\N	f	f
1042	PROJECT	Project	Everett Fine Wines	247154	2022-09-20 14:09:07.908888+05:30	2022-09-20 14:09:07.908915+05:30	1	t	\N	f	f
1043	PROJECT	Project	Everett International	247155	2022-09-20 14:09:07.909026+05:30	2022-09-20 14:09:07.909057+05:30	1	t	\N	f	f
1044	PROJECT	Project	Eyram Marketing	247156	2022-09-20 14:09:07.909118+05:30	2022-09-20 14:09:07.909152+05:30	1	t	\N	f	f
1045	PROJECT	Project	FA-HB Inc.	247157	2022-09-20 14:09:07.909311+05:30	2022-09-20 14:09:07.909333+05:30	1	t	\N	f	f
1046	PROJECT	Project	FA-HB Job	247158	2022-09-20 14:09:07.909387+05:30	2022-09-20 14:09:07.909409+05:30	1	t	\N	f	f
1047	PROJECT	Project	FSI Industries (EUR)	247159	2022-09-20 14:09:07.909452+05:30	2022-09-20 14:09:07.909473+05:30	1	t	\N	f	f
1048	PROJECT	Project	Fabre Enterprises	247160	2022-09-20 14:09:07.909533+05:30	2022-09-20 14:09:07.909572+05:30	1	t	\N	f	f
1049	PROJECT	Project	Fabrizio's Dry Cleaners	247161	2022-09-20 14:09:07.909628+05:30	2022-09-20 14:09:07.909655+05:30	1	t	\N	f	f
1050	PROJECT	Project	Fagnani Builders	247162	2022-09-20 14:09:07.909712+05:30	2022-09-20 14:09:07.909739+05:30	1	t	\N	f	f
1051	PROJECT	Project	Falls Church _ Agency	247163	2022-09-20 14:09:07.909795+05:30	2022-09-20 14:09:07.909823+05:30	1	t	\N	f	f
1052	PROJECT	Project	Fantasy Gemmart	247164	2022-09-20 14:09:07.909879+05:30	2022-09-20 14:09:07.909906+05:30	1	t	\N	f	f
1053	PROJECT	Project	Fasefax Systems	247165	2022-09-20 14:09:07.909963+05:30	2022-09-20 14:09:07.90999+05:30	1	t	\N	f	f
1054	PROJECT	Project	Faske Software Group	247166	2022-09-20 14:09:07.910046+05:30	2022-09-20 14:09:07.910073+05:30	1	t	\N	f	f
1055	PROJECT	Project	Fauerbach _ Agency	247167	2022-09-20 14:09:07.910129+05:30	2022-09-20 14:09:07.910156+05:30	1	t	\N	f	f
1056	PROJECT	Project	Fenceroy and Herling Metal Fabricators Management	247168	2022-09-20 14:09:07.910213+05:30	2022-09-20 14:09:07.91024+05:30	1	t	\N	f	f
1057	PROJECT	Project	Fernstrom Automotive Systems	247169	2022-09-20 14:09:07.910296+05:30	2022-09-20 14:09:07.910323+05:30	1	t	\N	f	f
1058	PROJECT	Project	Ferrio and Donlon Builders Management	247170	2022-09-20 14:09:07.910379+05:30	2022-09-20 14:09:07.91042+05:30	1	t	\N	f	f
1059	PROJECT	Project	Fetterolf and Loud Apartments Inc.	247171	2022-09-20 14:09:07.91059+05:30	2022-09-20 14:09:07.910618+05:30	1	t	\N	f	f
1060	PROJECT	Project	Ficke Apartments Group	247172	2022-09-20 14:09:07.910674+05:30	2022-09-20 14:09:07.910701+05:30	1	t	\N	f	f
1061	PROJECT	Project	FigmentSoft Inc	247173	2022-09-20 14:09:07.910758+05:30	2022-09-20 14:09:07.910784+05:30	1	t	\N	f	f
1062	PROJECT	Project	Fiore Fashion Inc	247174	2022-09-20 14:09:07.910841+05:30	2022-09-20 14:09:07.910868+05:30	1	t	\N	f	f
1063	PROJECT	Project	Florence Liquors and Associates	247175	2022-09-20 14:09:07.910924+05:30	2022-09-20 14:09:07.910951+05:30	1	t	\N	f	f
1064	PROJECT	Project	Flores Inc	247176	2022-09-20 14:09:07.911006+05:30	2022-09-20 14:09:07.911033+05:30	1	t	\N	f	f
1065	PROJECT	Project	Focal Point Opticians	247177	2022-09-20 14:09:07.911089+05:30	2022-09-20 14:09:07.911116+05:30	1	t	\N	f	f
1066	PROJECT	Project	Ford Models Inc	247178	2022-09-20 14:09:07.911172+05:30	2022-09-20 14:09:07.911199+05:30	1	t	\N	f	f
1067	PROJECT	Project	Forest Grove Liquors Company	247179	2022-09-20 14:09:07.911254+05:30	2022-09-20 14:09:07.911281+05:30	1	t	\N	f	f
1068	PROJECT	Project	Formal Furnishings	247180	2022-09-20 14:09:07.911338+05:30	2022-09-20 14:09:07.911467+05:30	1	t	\N	f	f
1069	PROJECT	Project	Formisano Hardware -	247181	2022-09-20 14:09:07.911536+05:30	2022-09-20 14:09:07.911572+05:30	1	t	\N	f	f
1070	PROJECT	Project	Fort Walton Beach Electric Company	247182	2022-09-20 14:09:07.911634+05:30	2022-09-20 14:09:07.911663+05:30	1	t	\N	f	f
1071	PROJECT	Project	Fossil Watch Limited	247183	2022-09-20 14:09:07.911721+05:30	2022-09-20 14:09:07.911742+05:30	1	t	\N	f	f
1072	PROJECT	Project	Foulds Plumbing -	247184	2022-09-20 14:09:07.911809+05:30	2022-09-20 14:09:07.911836+05:30	1	t	\N	f	f
1073	PROJECT	Project	Foxe Windows Management	247185	2022-09-20 14:09:07.911892+05:30	2022-09-20 14:09:07.911919+05:30	1	t	\N	f	f
1074	PROJECT	Project	Foxmoor Formula	247186	2022-09-20 14:09:07.911975+05:30	2022-09-20 14:09:07.912002+05:30	1	t	\N	f	f
1075	PROJECT	Project	Frank Edwards	247187	2022-09-20 14:09:07.912058+05:30	2022-09-20 14:09:07.912085+05:30	1	t	\N	f	f
1076	PROJECT	Project	Frankland Attorneys Sales	247188	2022-09-20 14:09:07.912141+05:30	2022-09-20 14:09:07.912169+05:30	1	t	\N	f	f
1077	PROJECT	Project	Franklin Photography	247189	2022-09-20 14:09:07.912224+05:30	2022-09-20 14:09:07.912251+05:30	1	t	\N	f	f
1078	PROJECT	Project	Franklin Windows Inc.	247190	2022-09-20 14:09:07.912308+05:30	2022-09-20 14:09:07.912346+05:30	1	t	\N	f	f
1079	PROJECT	Project	Fredericksburg Liquors Dynamics	247191	2022-09-20 14:09:07.912518+05:30	2022-09-20 14:09:07.912565+05:30	1	t	\N	f	f
1080	PROJECT	Project	Freier Markets Incorporated	247192	2022-09-20 14:09:07.912659+05:30	2022-09-20 14:09:07.9127+05:30	1	t	\N	f	f
1081	PROJECT	Project	Freshour Apartments Agency	247193	2022-09-20 14:09:07.912762+05:30	2022-09-20 14:09:07.912791+05:30	1	t	\N	f	f
1082	PROJECT	Project	FuTech	247194	2022-09-20 14:09:07.912851+05:30	2022-09-20 14:09:07.912872+05:30	1	t	\N	f	f
1083	PROJECT	Project	Fuhrmann Lumber Manufacturing	247195	2022-09-20 14:09:07.912928+05:30	2022-09-20 14:09:07.912949+05:30	1	t	\N	f	f
1084	PROJECT	Project	Fujimura Catering Corporation	247196	2022-09-20 14:09:07.919825+05:30	2022-09-20 14:09:07.919867+05:30	1	t	\N	f	f
1085	PROJECT	Project	Fullerton Software Inc.	247197	2022-09-20 14:09:07.919935+05:30	2022-09-20 14:09:07.919963+05:30	1	t	\N	f	f
1086	PROJECT	Project	Furay and Bielawski Liquors Corporation	247198	2022-09-20 14:09:07.920023+05:30	2022-09-20 14:09:07.92005+05:30	1	t	\N	f	f
1087	PROJECT	Project	Furniture Concepts	247199	2022-09-20 14:09:07.920109+05:30	2022-09-20 14:09:07.920136+05:30	1	t	\N	f	f
1088	PROJECT	Project	Fuster Builders Co.	247200	2022-09-20 14:09:07.920193+05:30	2022-09-20 14:09:07.92022+05:30	1	t	\N	f	f
1089	PROJECT	Project	Future Office Designs	247201	2022-09-20 14:09:07.920277+05:30	2022-09-20 14:09:07.920304+05:30	1	t	\N	f	f
1090	PROJECT	Project	GProxy Online	247202	2022-09-20 14:09:07.920362+05:30	2022-09-20 14:09:07.920389+05:30	1	t	\N	f	f
1091	PROJECT	Project	Gacad Publishing Co.	247203	2022-09-20 14:09:07.920674+05:30	2022-09-20 14:09:07.920716+05:30	1	t	\N	f	f
1092	PROJECT	Project	Gadison Electric Inc.	247204	2022-09-20 14:09:07.920787+05:30	2022-09-20 14:09:07.920815+05:30	1	t	\N	f	f
1093	PROJECT	Project	Gainesville Plumbing Co.	247205	2022-09-20 14:09:07.920872+05:30	2022-09-20 14:09:07.920899+05:30	1	t	\N	f	f
1094	PROJECT	Project	Galagher Plumbing Sales	247206	2022-09-20 14:09:07.920955+05:30	2022-09-20 14:09:07.920982+05:30	1	t	\N	f	f
1095	PROJECT	Project	Galas Electric Rentals	247207	2022-09-20 14:09:07.921038+05:30	2022-09-20 14:09:07.921066+05:30	1	t	\N	f	f
1096	PROJECT	Project	Gale Custom Sailboat	247208	2022-09-20 14:09:07.921122+05:30	2022-09-20 14:09:07.921149+05:30	1	t	\N	f	f
1097	PROJECT	Project	Gallaugher Title Dynamics	247209	2022-09-20 14:09:07.921207+05:30	2022-09-20 14:09:07.921234+05:30	1	t	\N	f	f
1098	PROJECT	Project	Galvan Attorneys Systems	247210	2022-09-20 14:09:07.92129+05:30	2022-09-20 14:09:07.92143+05:30	1	t	\N	f	f
1099	PROJECT	Project	Garden Automotive Systems	247211	2022-09-20 14:09:07.921563+05:30	2022-09-20 14:09:07.921591+05:30	1	t	\N	f	f
1100	PROJECT	Project	Gardnerville Automotive Sales	247212	2022-09-20 14:09:07.921647+05:30	2022-09-20 14:09:07.921674+05:30	1	t	\N	f	f
1101	PROJECT	Project	Garitty Metal Fabricators Rentals	247213	2022-09-20 14:09:07.921731+05:30	2022-09-20 14:09:07.921758+05:30	1	t	\N	f	f
1102	PROJECT	Project	Garret Leasing Rentals	247214	2022-09-20 14:09:07.921815+05:30	2022-09-20 14:09:07.921842+05:30	1	t	\N	f	f
1103	PROJECT	Project	Gary Underwood	247215	2022-09-20 14:09:07.921898+05:30	2022-09-20 14:09:07.921926+05:30	1	t	\N	f	f
1104	PROJECT	Project	Gauch Metal Fabricators Sales	247216	2022-09-20 14:09:07.922008+05:30	2022-09-20 14:09:07.92203+05:30	1	t	\N	f	f
1105	PROJECT	Project	Gearan Title Networking	247217	2022-09-20 14:09:07.922091+05:30	2022-09-20 14:09:07.922121+05:30	1	t	\N	f	f
1106	PROJECT	Project	Genis Builders Holding Corp.	247218	2022-09-20 14:09:07.922175+05:30	2022-09-20 14:09:07.922308+05:30	1	t	\N	f	f
1107	PROJECT	Project	Gerba Construction Corporation	247219	2022-09-20 14:09:07.922375+05:30	2022-09-20 14:09:07.922398+05:30	1	t	\N	f	f
1108	PROJECT	Project	Gerney Antiques Management	247220	2022-09-20 14:09:07.922501+05:30	2022-09-20 14:09:07.922539+05:30	1	t	\N	f	f
1109	PROJECT	Project	Gesamondo Construction Leasing	247221	2022-09-20 14:09:07.922597+05:30	2022-09-20 14:09:07.922905+05:30	1	t	\N	f	f
1110	PROJECT	Project	Gettenberg Title Manufacturing	247222	2022-09-20 14:09:07.922978+05:30	2022-09-20 14:09:07.923002+05:30	1	t	\N	f	f
1111	PROJECT	Project	Gibsons Corporation	247223	2022-09-20 14:09:07.923045+05:30	2022-09-20 14:09:07.923056+05:30	1	t	\N	f	f
1112	PROJECT	Project	Gilcrease Telecom Systems	247224	2022-09-20 14:09:07.923115+05:30	2022-09-20 14:09:07.923142+05:30	1	t	\N	f	f
1113	PROJECT	Project	Gilroy Electric Services	247225	2022-09-20 14:09:07.923198+05:30	2022-09-20 14:09:07.923225+05:30	1	t	\N	f	f
1114	PROJECT	Project	Gionest Metal Fabricators Co.	247226	2022-09-20 14:09:07.9234+05:30	2022-09-20 14:09:07.923439+05:30	1	t	\N	f	f
1115	PROJECT	Project	GlassHouse Systems	247227	2022-09-20 14:09:07.923496+05:30	2022-09-20 14:09:07.923523+05:30	1	t	\N	f	f
1116	PROJECT	Project	Glish Hospital Incorporated	247228	2022-09-20 14:09:07.923578+05:30	2022-09-20 14:09:07.923605+05:30	1	t	\N	f	f
1117	PROJECT	Project	Global Supplies Inc.	247229	2022-09-20 14:09:07.923661+05:30	2022-09-20 14:09:07.923689+05:30	1	t	\N	f	f
1696	PROJECT	Project	Tim Griffin	247808	2022-09-20 14:09:09.299948+05:30	2022-09-20 14:09:09.299977+05:30	1	t	\N	f	f
1118	PROJECT	Project	Glore Apartments Distributors	247230	2022-09-20 14:09:07.923744+05:30	2022-09-20 14:09:07.923772+05:30	1	t	\N	f	f
1119	PROJECT	Project	Goepel Windows Management	247231	2022-09-20 14:09:07.923828+05:30	2022-09-20 14:09:07.923855+05:30	1	t	\N	f	f
1120	PROJECT	Project	Graber & Assoc	247232	2022-09-20 14:09:07.923911+05:30	2022-09-20 14:09:07.923938+05:30	1	t	\N	f	f
1121	PROJECT	Project	Grana Automotive and Associates	247233	2022-09-20 14:09:07.923995+05:30	2022-09-20 14:09:07.924022+05:30	1	t	\N	f	f
1122	PROJECT	Project	Grangeville Apartments Dynamics	247234	2022-09-20 14:09:07.924078+05:30	2022-09-20 14:09:07.924105+05:30	1	t	\N	f	f
1123	PROJECT	Project	Grant Electronics	247235	2022-09-20 14:09:07.924161+05:30	2022-09-20 14:09:07.924188+05:30	1	t	\N	f	f
1124	PROJECT	Project	Graphics R Us	247236	2022-09-20 14:09:07.924246+05:30	2022-09-20 14:09:07.924273+05:30	1	t	\N	f	f
1125	PROJECT	Project	Grave Apartments Sales	247237	2022-09-20 14:09:07.924329+05:30	2022-09-20 14:09:07.924356+05:30	1	t	\N	f	f
1126	PROJECT	Project	Graydon	247238	2022-09-20 14:09:07.924539+05:30	2022-09-20 14:09:07.924577+05:30	1	t	\N	f	f
1127	PROJECT	Project	Green Grocery	247239	2022-09-20 14:09:07.924634+05:30	2022-09-20 14:09:07.924661+05:30	1	t	\N	f	f
1128	PROJECT	Project	Green Street Spirits	247240	2022-09-20 14:09:07.924718+05:30	2022-09-20 14:09:07.924745+05:30	1	t	\N	f	f
1129	PROJECT	Project	Greg Muller	247241	2022-09-20 14:09:07.924801+05:30	2022-09-20 14:09:07.924828+05:30	1	t	\N	f	f
1130	PROJECT	Project	Greg Yamashige	247242	2022-09-20 14:09:07.924884+05:30	2022-09-20 14:09:07.924911+05:30	1	t	\N	f	f
1131	PROJECT	Project	Gregory Daniels	247243	2022-09-20 14:09:07.924967+05:30	2022-09-20 14:09:07.924994+05:30	1	t	\N	f	f
1132	PROJECT	Project	Gresham	247244	2022-09-20 14:09:07.925051+05:30	2022-09-20 14:09:07.925078+05:30	1	t	\N	f	f
1133	PROJECT	Project	Grines Apartments Co.	247245	2022-09-20 14:09:07.925135+05:30	2022-09-20 14:09:07.925162+05:30	1	t	\N	f	f
1134	PROJECT	Project	Guidaboni Publishing Leasing	247246	2022-09-20 14:09:07.931211+05:30	2022-09-20 14:09:07.931255+05:30	1	t	\N	f	f
1135	PROJECT	Project	Gus Lee	247247	2022-09-20 14:09:07.931324+05:30	2022-09-20 14:09:07.93146+05:30	1	t	\N	f	f
1136	PROJECT	Project	Gus Li	247248	2022-09-20 14:09:07.931542+05:30	2022-09-20 14:09:07.93157+05:30	1	t	\N	f	f
1137	PROJECT	Project	Gus Photography	247249	2022-09-20 14:09:07.931642+05:30	2022-09-20 14:09:07.931669+05:30	1	t	\N	f	f
1138	PROJECT	Project	Guzalak Leasing Leasing	247250	2022-09-20 14:09:07.931727+05:30	2022-09-20 14:09:07.931754+05:30	1	t	\N	f	f
1139	PROJECT	Project	HGH Vision	247251	2022-09-20 14:09:07.931811+05:30	2022-09-20 14:09:07.931838+05:30	1	t	\N	f	f
1140	PROJECT	Project	Hahn & Associates	247252	2022-09-20 14:09:07.931895+05:30	2022-09-20 14:09:07.931922+05:30	1	t	\N	f	f
1141	PROJECT	Project	Haleiwa Windows Leasing	247253	2022-09-20 14:09:07.931979+05:30	2022-09-20 14:09:07.932006+05:30	1	t	\N	f	f
1142	PROJECT	Project	Halick Title and Associates	247254	2022-09-20 14:09:07.932062+05:30	2022-09-20 14:09:07.93209+05:30	1	t	\N	f	f
1143	PROJECT	Project	Hambly Spirits	247255	2022-09-20 14:09:07.932146+05:30	2022-09-20 14:09:07.932173+05:30	1	t	\N	f	f
1144	PROJECT	Project	Hanninen Painting Distributors	247256	2022-09-20 14:09:07.93223+05:30	2022-09-20 14:09:07.932257+05:30	1	t	\N	f	f
1145	PROJECT	Project	Hansen Car Dealership	247257	2022-09-20 14:09:07.932314+05:30	2022-09-20 14:09:07.932341+05:30	1	t	\N	f	f
1146	PROJECT	Project	Harriage Plumbing Dynamics	247258	2022-09-20 14:09:07.932539+05:30	2022-09-20 14:09:07.932568+05:30	1	t	\N	f	f
1147	PROJECT	Project	Harriott Construction Services	247259	2022-09-20 14:09:07.932626+05:30	2022-09-20 14:09:07.932653+05:30	1	t	\N	f	f
1148	PROJECT	Project	Harrop Attorneys Inc.	247260	2022-09-20 14:09:07.93271+05:30	2022-09-20 14:09:07.932738+05:30	1	t	\N	f	f
1149	PROJECT	Project	Harting Electric Fabricators	247261	2022-09-20 14:09:07.932794+05:30	2022-09-20 14:09:07.932821+05:30	1	t	\N	f	f
1150	PROJECT	Project	Hawk Liquors Agency	247262	2022-09-20 14:09:07.932878+05:30	2022-09-20 14:09:07.932905+05:30	1	t	\N	f	f
1151	PROJECT	Project	Healy Lumber -	247263	2022-09-20 14:09:07.932962+05:30	2022-09-20 14:09:07.932989+05:30	1	t	\N	f	f
1152	PROJECT	Project	Hebden Automotive Dynamics	247264	2022-09-20 14:09:07.933046+05:30	2022-09-20 14:09:07.933073+05:30	1	t	\N	f	f
1153	PROJECT	Project	Heeralall Metal Fabricators Incorporated	247265	2022-09-20 14:09:07.93313+05:30	2022-09-20 14:09:07.933158+05:30	1	t	\N	f	f
1154	PROJECT	Project	Helfenbein Apartments Co.	247266	2022-09-20 14:09:07.933214+05:30	2022-09-20 14:09:07.933242+05:30	1	t	\N	f	f
1155	PROJECT	Project	Helferty _ Services	247267	2022-09-20 14:09:07.933299+05:30	2022-09-20 14:09:07.933326+05:30	1	t	\N	f	f
1156	PROJECT	Project	Helker and Heidkamp Software Systems	247268	2022-09-20 14:09:07.933507+05:30	2022-09-20 14:09:07.933546+05:30	1	t	\N	f	f
1157	PROJECT	Project	Helping Hands Medical Supply	247269	2022-09-20 14:09:07.933603+05:30	2022-09-20 14:09:07.93363+05:30	1	t	\N	f	f
1158	PROJECT	Project	Helvey Catering Distributors	247270	2022-09-20 14:09:07.933687+05:30	2022-09-20 14:09:07.933714+05:30	1	t	\N	f	f
1159	PROJECT	Project	Hemauer Builders Inc.	247271	2022-09-20 14:09:07.933771+05:30	2022-09-20 14:09:07.933798+05:30	1	t	\N	f	f
1160	PROJECT	Project	Hemet Builders Sales	247272	2022-09-20 14:09:07.933854+05:30	2022-09-20 14:09:07.933882+05:30	1	t	\N	f	f
1161	PROJECT	Project	Henderson Cooper	247273	2022-09-20 14:09:07.933938+05:30	2022-09-20 14:09:07.933965+05:30	1	t	\N	f	f
1162	PROJECT	Project	Henderson Liquors Manufacturing	247274	2022-09-20 14:09:07.934021+05:30	2022-09-20 14:09:07.934048+05:30	1	t	\N	f	f
1163	PROJECT	Project	Hendrikson Builders Corporation	247275	2022-09-20 14:09:07.934104+05:30	2022-09-20 14:09:07.934132+05:30	1	t	\N	f	f
1164	PROJECT	Project	Henneman Hardware	247276	2022-09-20 14:09:07.934188+05:30	2022-09-20 14:09:07.934216+05:30	1	t	\N	f	f
1165	PROJECT	Project	Herline Hospital Holding Corp.	247277	2022-09-20 14:09:07.934272+05:30	2022-09-20 14:09:07.9343+05:30	1	t	\N	f	f
1166	PROJECT	Project	Hershey's Canada	247278	2022-09-20 14:09:07.934367+05:30	2022-09-20 14:09:07.934522+05:30	1	t	\N	f	f
1167	PROJECT	Project	Hess Sundries	247279	2022-09-20 14:09:07.934568+05:30	2022-09-20 14:09:07.93459+05:30	1	t	\N	f	f
1168	PROJECT	Project	Hextall Consulting	247280	2022-09-20 14:09:07.934669+05:30	2022-09-20 14:09:07.934697+05:30	1	t	\N	f	f
1169	PROJECT	Project	Hillian Construction Fabricators	247281	2022-09-20 14:09:07.934753+05:30	2022-09-20 14:09:07.93478+05:30	1	t	\N	f	f
1170	PROJECT	Project	Hilltop Info Inc	247282	2022-09-20 14:09:07.934837+05:30	2022-09-20 14:09:07.934864+05:30	1	t	\N	f	f
1171	PROJECT	Project	Hirschy and Fahrenwald Liquors Incorporated	247283	2022-09-20 14:09:07.93492+05:30	2022-09-20 14:09:07.934947+05:30	1	t	\N	f	f
1172	PROJECT	Project	Hixson Construction Agency	247284	2022-09-20 14:09:07.935003+05:30	2022-09-20 14:09:07.935031+05:30	1	t	\N	f	f
1173	PROJECT	Project	Holgerson Automotive Services	247285	2022-09-20 14:09:07.935086+05:30	2022-09-20 14:09:07.935113+05:30	1	t	\N	f	f
1174	PROJECT	Project	Holly Romine	247286	2022-09-20 14:09:07.935169+05:30	2022-09-20 14:09:07.935197+05:30	1	t	\N	f	f
1175	PROJECT	Project	Hollyday Construction Networking	247287	2022-09-20 14:09:07.935252+05:30	2022-09-20 14:09:07.93528+05:30	1	t	\N	f	f
1176	PROJECT	Project	Holtmeier Leasing -	247288	2022-09-20 14:09:07.935452+05:30	2022-09-20 14:09:07.9355+05:30	1	t	\N	f	f
1177	PROJECT	Project	Honie Hospital Systems	247289	2022-09-20 14:09:07.93556+05:30	2022-09-20 14:09:07.935587+05:30	1	t	\N	f	f
1178	PROJECT	Project	Honolulu Attorneys Sales	247290	2022-09-20 14:09:07.935644+05:30	2022-09-20 14:09:07.935671+05:30	1	t	\N	f	f
1179	PROJECT	Project	Honolulu Markets Group	247291	2022-09-20 14:09:07.935727+05:30	2022-09-20 14:09:07.935754+05:30	1	t	\N	f	f
1180	PROJECT	Project	Hood River Telecom	247292	2022-09-20 14:09:07.93581+05:30	2022-09-20 14:09:07.935837+05:30	1	t	\N	f	f
1181	PROJECT	Project	Huck Apartments Inc.	247293	2022-09-20 14:09:07.935894+05:30	2022-09-20 14:09:07.935921+05:30	1	t	\N	f	f
1182	PROJECT	Project	Hughson Runners	247294	2022-09-20 14:09:07.935978+05:30	2022-09-20 14:09:07.936005+05:30	1	t	\N	f	f
1183	PROJECT	Project	Huit and Duer Publishing Dynamics	247295	2022-09-20 14:09:07.936061+05:30	2022-09-20 14:09:07.936088+05:30	1	t	\N	f	f
1184	PROJECT	Project	Humphrey Yogurt	247296	2022-09-20 14:09:07.943889+05:30	2022-09-20 14:09:07.943929+05:30	1	t	\N	f	f
1185	PROJECT	Project	Huntsville Apartments and Associates	247297	2022-09-20 14:09:07.943988+05:30	2022-09-20 14:09:07.944016+05:30	1	t	\N	f	f
1186	PROJECT	Project	Hurlbutt Markets -	247298	2022-09-20 14:09:07.944073+05:30	2022-09-20 14:09:07.9441+05:30	1	t	\N	f	f
1187	PROJECT	Project	Hurtgen Hospital Manufacturing	247299	2022-09-20 14:09:07.944157+05:30	2022-09-20 14:09:07.944184+05:30	1	t	\N	f	f
1188	PROJECT	Project	IBA Enterprises Inc	247300	2022-09-20 14:09:07.94424+05:30	2022-09-20 14:09:07.944267+05:30	1	t	\N	f	f
1189	PROJECT	Project	ICC Inc	247301	2022-09-20 14:09:07.944323+05:30	2022-09-20 14:09:07.94435+05:30	1	t	\N	f	f
1191	PROJECT	Project	Imperial Liquors Distributors	247303	2022-09-20 14:09:07.944629+05:30	2022-09-20 14:09:07.944656+05:30	1	t	\N	f	f
1192	PROJECT	Project	Imran Kahn	247304	2022-09-20 14:09:07.944712+05:30	2022-09-20 14:09:07.94474+05:30	1	t	\N	f	f
1193	PROJECT	Project	Indianapolis Liquors Rentals	247305	2022-09-20 14:09:07.944796+05:30	2022-09-20 14:09:07.944823+05:30	1	t	\N	f	f
1194	PROJECT	Project	Installation 2	247306	2022-09-20 14:09:07.944879+05:30	2022-09-20 14:09:07.944906+05:30	1	t	\N	f	f
1195	PROJECT	Project	Installation FP	247307	2022-09-20 14:09:07.944962+05:30	2022-09-20 14:09:07.944989+05:30	1	t	\N	f	f
1196	PROJECT	Project	Integrys Ltd	247308	2022-09-20 14:09:07.945045+05:30	2022-09-20 14:09:07.945073+05:30	1	t	\N	f	f
1197	PROJECT	Project	InterWorks Ltd	247309	2022-09-20 14:09:07.945128+05:30	2022-09-20 14:09:07.945156+05:30	1	t	\N	f	f
1198	PROJECT	Project	Interior Solutions	247310	2022-09-20 14:09:07.945212+05:30	2022-09-20 14:09:07.945239+05:30	1	t	\N	f	f
1199	PROJECT	Project	Iorio Lumber Incorporated	247311	2022-09-20 14:09:07.945295+05:30	2022-09-20 14:09:07.945323+05:30	1	t	\N	f	f
1200	PROJECT	Project	JKL Co.	247312	2022-09-20 14:09:07.945466+05:30	2022-09-20 14:09:07.945494+05:30	1	t	\N	f	f
1201	PROJECT	Project	Jackie Kugan	247313	2022-09-20 14:09:07.945564+05:30	2022-09-20 14:09:07.945593+05:30	1	t	\N	f	f
1202	PROJECT	Project	Jackson Alexander	247314	2022-09-20 14:09:07.945662+05:30	2022-09-20 14:09:07.945688+05:30	1	t	\N	f	f
1203	PROJECT	Project	Jaenicke Builders Management	247315	2022-09-20 14:09:07.945731+05:30	2022-09-20 14:09:07.945751+05:30	1	t	\N	f	f
1204	PROJECT	Project	Jake Hamilton	247316	2022-09-20 14:09:07.945812+05:30	2022-09-20 14:09:07.945841+05:30	1	t	\N	f	f
1205	PROJECT	Project	James McClure	247317	2022-09-20 14:09:07.9459+05:30	2022-09-20 14:09:07.945939+05:30	1	t	\N	f	f
1206	PROJECT	Project	Jamie Taylor	247318	2022-09-20 14:09:07.945995+05:30	2022-09-20 14:09:07.946023+05:30	1	t	\N	f	f
1207	PROJECT	Project	Janiak Attorneys Inc.	247319	2022-09-20 14:09:07.946078+05:30	2022-09-20 14:09:07.946105+05:30	1	t	\N	f	f
1208	PROJECT	Project	Jasmer Antiques Management	247320	2022-09-20 14:09:07.946162+05:30	2022-09-20 14:09:07.946189+05:30	1	t	\N	f	f
1209	PROJECT	Project	Jason Jacob	247321	2022-09-20 14:09:07.946245+05:30	2022-09-20 14:09:07.946283+05:30	1	t	\N	f	f
1210	PROJECT	Project	Jason Paul Distribution	247322	2022-09-20 14:09:07.946432+05:30	2022-09-20 14:09:07.946461+05:30	1	t	\N	f	f
1211	PROJECT	Project	Jeff Campbell	247323	2022-09-20 14:09:07.946529+05:30	2022-09-20 14:09:07.946697+05:30	1	t	\N	f	f
1212	PROJECT	Project	Jelle Catering Group	247324	2022-09-20 14:09:07.946897+05:30	2022-09-20 14:09:07.946928+05:30	1	t	\N	f	f
1213	PROJECT	Project	Jennings Financial	247325	2022-09-20 14:09:07.947107+05:30	2022-09-20 14:09:07.947478+05:30	1	t	\N	f	f
1214	PROJECT	Project	Jennings Financial Inc.	247326	2022-09-20 14:09:07.947679+05:30	2022-09-20 14:09:07.947707+05:30	1	t	\N	f	f
1215	PROJECT	Project	Jeune Antiques Group	247327	2022-09-20 14:09:07.947765+05:30	2022-09-20 14:09:07.947792+05:30	1	t	\N	f	f
1216	PROJECT	Project	Jeziorski _ Dynamics	247328	2022-09-20 14:09:07.947849+05:30	2022-09-20 14:09:07.947876+05:30	1	t	\N	f	f
1217	PROJECT	Project	Jim Strong	247329	2022-09-20 14:09:07.947932+05:30	2022-09-20 14:09:07.947959+05:30	1	t	\N	f	f
1218	PROJECT	Project	Jim's Custom Frames	247330	2022-09-20 14:09:07.948016+05:30	2022-09-20 14:09:07.948043+05:30	1	t	\N	f	f
1219	PROJECT	Project	Joanne Miller	247331	2022-09-20 14:09:07.948099+05:30	2022-09-20 14:09:07.948126+05:30	1	t	\N	f	f
1220	PROJECT	Project	Joe Smith	247332	2022-09-20 14:09:07.948183+05:30	2022-09-20 14:09:07.94821+05:30	1	t	\N	f	f
1221	PROJECT	Project	Johar Software Corporation	247333	2022-09-20 14:09:07.948266+05:30	2022-09-20 14:09:07.948293+05:30	1	t	\N	f	f
1222	PROJECT	Project	John Boba	247334	2022-09-20 14:09:07.948481+05:30	2022-09-20 14:09:07.948521+05:30	1	t	\N	f	f
1223	PROJECT	Project	John G. Roche Opticians	247335	2022-09-20 14:09:07.948578+05:30	2022-09-20 14:09:07.948606+05:30	1	t	\N	f	f
1224	PROJECT	Project	John Nguyen	247336	2022-09-20 14:09:07.948662+05:30	2022-09-20 14:09:07.948689+05:30	1	t	\N	f	f
1225	PROJECT	Project	John Paulsen	247337	2022-09-20 14:09:07.948745+05:30	2022-09-20 14:09:07.948772+05:30	1	t	\N	f	f
1226	PROJECT	Project	John Smith Home Design	247338	2022-09-20 14:09:07.948828+05:30	2022-09-20 14:09:07.948855+05:30	1	t	\N	f	f
1227	PROJECT	Project	Johnson & Johnson	247339	2022-09-20 14:09:07.948911+05:30	2022-09-20 14:09:07.948938+05:30	1	t	\N	f	f
1228	PROJECT	Project	Jonas Island Applied Radiation	247340	2022-09-20 14:09:07.948995+05:30	2022-09-20 14:09:07.949022+05:30	1	t	\N	f	f
1229	PROJECT	Project	Jonathan Ketner	247341	2022-09-20 14:09:07.949078+05:30	2022-09-20 14:09:07.949105+05:30	1	t	\N	f	f
1230	PROJECT	Project	Jones & Bernstein Law Firm	247342	2022-09-20 14:09:07.949161+05:30	2022-09-20 14:09:07.949188+05:30	1	t	\N	f	f
1231	PROJECT	Project	Julia Daniels	247343	2022-09-20 14:09:07.949245+05:30	2022-09-20 14:09:07.949272+05:30	1	t	\N	f	f
1232	PROJECT	Project	Julie Frankel	247344	2022-09-20 14:09:07.949328+05:30	2022-09-20 14:09:07.949366+05:30	1	t	\N	f	f
1233	PROJECT	Project	Juno Gold Wines	247345	2022-09-20 14:09:07.949545+05:30	2022-09-20 14:09:07.949573+05:30	1	t	\N	f	f
1234	PROJECT	Project	Justin Hartman	247346	2022-09-20 14:09:08.382899+05:30	2022-09-20 14:09:08.382953+05:30	1	t	\N	f	f
1235	PROJECT	Project	Justin Ramos	247347	2022-09-20 14:09:08.383014+05:30	2022-09-20 14:09:08.383042+05:30	1	t	\N	f	f
1236	PROJECT	Project	KEM Corporation	247348	2022-09-20 14:09:08.3831+05:30	2022-09-20 14:09:08.383128+05:30	1	t	\N	f	f
1237	PROJECT	Project	Kababik and Ramariz Liquors Corporation	247349	2022-09-20 14:09:08.383185+05:30	2022-09-20 14:09:08.383213+05:30	1	t	\N	f	f
1238	PROJECT	Project	Kalfa Painting Holding Corp.	247350	2022-09-20 14:09:08.38327+05:30	2022-09-20 14:09:08.383297+05:30	1	t	\N	f	f
1239	PROJECT	Project	Kalinsky Consulting Group	247351	2022-09-20 14:09:08.383369+05:30	2022-09-20 14:09:08.383512+05:30	1	t	\N	f	f
1240	PROJECT	Project	Kalisch Lumber Group	247352	2022-09-20 14:09:08.383581+05:30	2022-09-20 14:09:08.383609+05:30	1	t	\N	f	f
1241	PROJECT	Project	Kallmeyer Antiques Dynamics	247353	2022-09-20 14:09:08.383667+05:30	2022-09-20 14:09:08.383694+05:30	1	t	\N	f	f
1242	PROJECT	Project	Kamps Electric Systems	247354	2022-09-20 14:09:08.383752+05:30	2022-09-20 14:09:08.383779+05:30	1	t	\N	f	f
1243	PROJECT	Project	Kara's Cafe	247355	2022-09-20 14:09:08.383849+05:30	2022-09-20 14:09:08.383878+05:30	1	t	\N	f	f
1244	PROJECT	Project	Kate Winters	247356	2022-09-20 14:09:08.383939+05:30	2022-09-20 14:09:08.383968+05:30	1	t	\N	f	f
1245	PROJECT	Project	Katie Fischer	247357	2022-09-20 14:09:08.384029+05:30	2022-09-20 14:09:08.384068+05:30	1	t	\N	f	f
1246	PROJECT	Project	Kavadias Construction Sales	247358	2022-09-20 14:09:08.384126+05:30	2022-09-20 14:09:08.384153+05:30	1	t	\N	f	f
1247	PROJECT	Project	Kavanagh Brothers	247359	2022-09-20 14:09:08.384209+05:30	2022-09-20 14:09:08.384237+05:30	1	t	\N	f	f
1248	PROJECT	Project	Kavanaugh Real Estate	247360	2022-09-20 14:09:08.384294+05:30	2022-09-20 14:09:08.384321+05:30	1	t	\N	f	f
1249	PROJECT	Project	Keblish Catering Distributors	247361	2022-09-20 14:09:08.384485+05:30	2022-09-20 14:09:08.384515+05:30	1	t	\N	f	f
1250	PROJECT	Project	Kelleher Title Services	247362	2022-09-20 14:09:08.384584+05:30	2022-09-20 14:09:08.384612+05:30	1	t	\N	f	f
1251	PROJECT	Project	Kemme Builders Management	247363	2022-09-20 14:09:08.384669+05:30	2022-09-20 14:09:08.384697+05:30	1	t	\N	f	f
1252	PROJECT	Project	Kempker Title Manufacturing	247364	2022-09-20 14:09:08.384754+05:30	2022-09-20 14:09:08.384782+05:30	1	t	\N	f	f
1253	PROJECT	Project	Ken Chua	247365	2022-09-20 14:09:08.384839+05:30	2022-09-20 14:09:08.384866+05:30	1	t	\N	f	f
1254	PROJECT	Project	Kenney Windows Dynamics	247366	2022-09-20 14:09:08.384923+05:30	2022-09-20 14:09:08.384951+05:30	1	t	\N	f	f
1255	PROJECT	Project	Kerekes Lumber Networking	247367	2022-09-20 14:09:08.385008+05:30	2022-09-20 14:09:08.385036+05:30	1	t	\N	f	f
1256	PROJECT	Project	Kerfien Title Company	247368	2022-09-20 14:09:08.385093+05:30	2022-09-20 14:09:08.38512+05:30	1	t	\N	f	f
1257	PROJECT	Project	Kerry Furnishings & Design	247369	2022-09-20 14:09:08.385177+05:30	2022-09-20 14:09:08.385204+05:30	1	t	\N	f	f
1258	PROJECT	Project	Kevin Smith	247370	2022-09-20 14:09:08.385261+05:30	2022-09-20 14:09:08.385289+05:30	1	t	\N	f	f
1259	PROJECT	Project	Kiedrowski Telecom Services	247371	2022-09-20 14:09:08.385346+05:30	2022-09-20 14:09:08.385495+05:30	1	t	\N	f	f
1260	PROJECT	Project	Kieff Software Fabricators	247372	2022-09-20 14:09:08.385561+05:30	2022-09-20 14:09:08.385602+05:30	1	t	\N	f	f
1261	PROJECT	Project	Killian Construction Networking	247373	2022-09-20 14:09:08.385683+05:30	2022-09-20 14:09:08.385711+05:30	1	t	\N	f	f
1262	PROJECT	Project	Kim Wilson	247374	2022-09-20 14:09:08.385767+05:30	2022-09-20 14:09:08.385795+05:30	1	t	\N	f	f
1263	PROJECT	Project	Kingman Antiques Corporation	247375	2022-09-20 14:09:08.385852+05:30	2022-09-20 14:09:08.385879+05:30	1	t	\N	f	f
1264	PROJECT	Project	Kino Inc	247376	2022-09-20 14:09:08.385936+05:30	2022-09-20 14:09:08.385963+05:30	1	t	\N	f	f
1265	PROJECT	Project	Kirkville Builders -	247377	2022-09-20 14:09:08.38602+05:30	2022-09-20 14:09:08.386047+05:30	1	t	\N	f	f
1266	PROJECT	Project	Kittel Hardware Dynamics	247378	2022-09-20 14:09:08.386104+05:30	2022-09-20 14:09:08.386131+05:30	1	t	\N	f	f
1267	PROJECT	Project	Knoop Telecom Agency	247379	2022-09-20 14:09:08.386187+05:30	2022-09-20 14:09:08.386215+05:30	1	t	\N	f	f
1268	PROJECT	Project	Knotek Hospital Company	247380	2022-09-20 14:09:08.386271+05:30	2022-09-20 14:09:08.386298+05:30	1	t	\N	f	f
1269	PROJECT	Project	Konecny Markets Co.	247381	2022-09-20 14:09:08.386366+05:30	2022-09-20 14:09:08.386503+05:30	1	t	\N	f	f
1270	PROJECT	Project	Koshi Metal Fabricators Corporation	247382	2022-09-20 14:09:08.386573+05:30	2022-09-20 14:09:08.3866+05:30	1	t	\N	f	f
1271	PROJECT	Project	Kovats Publishing	247383	2022-09-20 14:09:08.386657+05:30	2022-09-20 14:09:08.386684+05:30	1	t	\N	f	f
1272	PROJECT	Project	Kramer Construction	247384	2022-09-20 14:09:08.386741+05:30	2022-09-20 14:09:08.386769+05:30	1	t	\N	f	f
1273	PROJECT	Project	Krista Thomas Recruiting	247385	2022-09-20 14:09:08.386825+05:30	2022-09-20 14:09:08.386853+05:30	1	t	\N	f	f
1274	PROJECT	Project	Kristen Welch	247386	2022-09-20 14:09:08.386909+05:30	2022-09-20 14:09:08.386937+05:30	1	t	\N	f	f
1275	PROJECT	Project	Kroetz Electric Dynamics	247387	2022-09-20 14:09:08.386994+05:30	2022-09-20 14:09:08.387021+05:30	1	t	\N	f	f
1276	PROJECT	Project	Kugan Autodesk Inc	247388	2022-09-20 14:09:08.387078+05:30	2022-09-20 14:09:08.387105+05:30	1	t	\N	f	f
1277	PROJECT	Project	Kunstlinger Automotive Manufacturing	247389	2022-09-20 14:09:08.387162+05:30	2022-09-20 14:09:08.38719+05:30	1	t	\N	f	f
1278	PROJECT	Project	Kyle Keosian	247390	2022-09-20 14:09:08.387246+05:30	2022-09-20 14:09:08.387273+05:30	1	t	\N	f	f
1279	PROJECT	Project	La Grande Liquors Dynamics	247391	2022-09-20 14:09:08.38733+05:30	2022-09-20 14:09:08.387368+05:30	1	t	\N	f	f
1280	PROJECT	Project	Labarba Markets Corporation	247392	2022-09-20 14:09:08.387544+05:30	2022-09-20 14:09:08.387571+05:30	1	t	\N	f	f
1281	PROJECT	Project	Laditka and Ceppetelli Publishing Holding Corp.	247393	2022-09-20 14:09:08.387629+05:30	2022-09-20 14:09:08.387656+05:30	1	t	\N	f	f
1282	PROJECT	Project	Lafayette Hardware Services	247394	2022-09-20 14:09:08.387713+05:30	2022-09-20 14:09:08.38774+05:30	1	t	\N	f	f
1283	PROJECT	Project	Lafayette Metal Fabricators Rentals	247395	2022-09-20 14:09:08.387797+05:30	2022-09-20 14:09:08.387824+05:30	1	t	\N	f	f
1284	PROJECT	Project	Lake Worth Markets Fabricators	247396	2022-09-20 14:09:08.395007+05:30	2022-09-20 14:09:08.395045+05:30	1	t	\N	f	f
1285	PROJECT	Project	Lakeside Inc	247397	2022-09-20 14:09:08.395106+05:30	2022-09-20 14:09:08.395133+05:30	1	t	\N	f	f
1286	PROJECT	Project	Lancaster Liquors Inc.	247398	2022-09-20 14:09:08.39519+05:30	2022-09-20 14:09:08.395217+05:30	1	t	\N	f	f
1287	PROJECT	Project	Lanning and Urraca Construction Corporation	247399	2022-09-20 14:09:08.395274+05:30	2022-09-20 14:09:08.395301+05:30	1	t	\N	f	f
1288	PROJECT	Project	Laramie Construction Co.	247400	2022-09-20 14:09:08.395358+05:30	2022-09-20 14:09:08.395482+05:30	1	t	\N	f	f
1289	PROJECT	Project	Largo Lumber Co.	247401	2022-09-20 14:09:08.395552+05:30	2022-09-20 14:09:08.39558+05:30	1	t	\N	f	f
1290	PROJECT	Project	Lariosa Lumber Corporation	247402	2022-09-20 14:09:08.395637+05:30	2022-09-20 14:09:08.395665+05:30	1	t	\N	f	f
1291	PROJECT	Project	Las Vegas Electric Manufacturing	247403	2022-09-20 14:09:08.395721+05:30	2022-09-20 14:09:08.395749+05:30	1	t	\N	f	f
1292	PROJECT	Project	Laser Images Inc.	247404	2022-09-20 14:09:08.395805+05:30	2022-09-20 14:09:08.395832+05:30	1	t	\N	f	f
1293	PROJECT	Project	Lawley and Barends Painting Distributors	247405	2022-09-20 14:09:08.395889+05:30	2022-09-20 14:09:08.395916+05:30	1	t	\N	f	f
1294	PROJECT	Project	Lead 154	247406	2022-09-20 14:09:08.395972+05:30	2022-09-20 14:09:08.395999+05:30	1	t	\N	f	f
1295	PROJECT	Project	Lead 155	247407	2022-09-20 14:09:08.396055+05:30	2022-09-20 14:09:08.396082+05:30	1	t	\N	f	f
1296	PROJECT	Project	Leemans Builders Agency	247408	2022-09-20 14:09:08.39615+05:30	2022-09-20 14:09:08.39618+05:30	1	t	\N	f	f
1297	PROJECT	Project	Lenza and Lanzoni Plumbing Co.	247409	2022-09-20 14:09:08.39624+05:30	2022-09-20 14:09:08.396269+05:30	1	t	\N	f	f
1298	PROJECT	Project	Levitan Plumbing Dynamics	247410	2022-09-20 14:09:08.396329+05:30	2022-09-20 14:09:08.396359+05:30	1	t	\N	f	f
1299	PROJECT	Project	Lexington Hospital Sales	247411	2022-09-20 14:09:08.396562+05:30	2022-09-20 14:09:08.396592+05:30	1	t	\N	f	f
1300	PROJECT	Project	Liechti Lumber Sales	247412	2022-09-20 14:09:08.39666+05:30	2022-09-20 14:09:08.397102+05:30	1	t	\N	f	f
1301	PROJECT	Project	Lillian Thurham	247413	2022-09-20 14:09:08.397298+05:30	2022-09-20 14:09:08.397327+05:30	1	t	\N	f	f
1302	PROJECT	Project	Limbo Leasing Leasing	247414	2022-09-20 14:09:08.397397+05:30	2022-09-20 14:09:08.397424+05:30	1	t	\N	f	f
1303	PROJECT	Project	Lina's Dance Studio	247415	2022-09-20 14:09:08.397482+05:30	2022-09-20 14:09:08.397509+05:30	1	t	\N	f	f
1304	PROJECT	Project	Linberg Windows Agency	247416	2022-09-20 14:09:08.397566+05:30	2022-09-20 14:09:08.397593+05:30	1	t	\N	f	f
1305	PROJECT	Project	Linder Windows Rentals	247417	2022-09-20 14:09:08.39765+05:30	2022-09-20 14:09:08.397677+05:30	1	t	\N	f	f
1306	PROJECT	Project	Linderman Builders Agency	247418	2022-09-20 14:09:08.397733+05:30	2022-09-20 14:09:08.397761+05:30	1	t	\N	f	f
1307	PROJECT	Project	Lindman and Kastens Antiques -	247419	2022-09-20 14:09:08.397817+05:30	2022-09-20 14:09:08.397844+05:30	1	t	\N	f	f
1308	PROJECT	Project	Linear International Footwear	247420	2022-09-20 14:09:08.3979+05:30	2022-09-20 14:09:08.397928+05:30	1	t	\N	f	f
1309	PROJECT	Project	Lintex Group	247421	2022-09-20 14:09:08.397984+05:30	2022-09-20 14:09:08.398011+05:30	1	t	\N	f	f
1310	PROJECT	Project	Lisa Fiore	247422	2022-09-20 14:09:08.398068+05:30	2022-09-20 14:09:08.398095+05:30	1	t	\N	f	f
1311	PROJECT	Project	Lisa Wilson	247423	2022-09-20 14:09:08.398152+05:30	2022-09-20 14:09:08.398179+05:30	1	t	\N	f	f
1312	PROJECT	Project	Liverpool Hospital Leasing	247424	2022-09-20 14:09:08.398236+05:30	2022-09-20 14:09:08.398263+05:30	1	t	\N	f	f
1313	PROJECT	Project	Lizarrago Markets Corporation	247425	2022-09-20 14:09:08.398319+05:30	2022-09-20 14:09:08.398346+05:30	1	t	\N	f	f
1314	PROJECT	Project	Lobby Remodel	247426	2022-09-20 14:09:08.398403+05:30	2022-09-20 14:09:08.398561+05:30	1	t	\N	f	f
1315	PROJECT	Project	Lodato Painting and Associates	247427	2022-09-20 14:09:08.398632+05:30	2022-09-20 14:09:08.39866+05:30	1	t	\N	f	f
1316	PROJECT	Project	Loeza Catering Agency	247428	2022-09-20 14:09:08.398717+05:30	2022-09-20 14:09:08.398745+05:30	1	t	\N	f	f
1317	PROJECT	Project	Lois Automotive Agency	247429	2022-09-20 14:09:08.398801+05:30	2022-09-20 14:09:08.398828+05:30	1	t	\N	f	f
1318	PROJECT	Project	Lomax Transportation	247430	2022-09-20 14:09:08.398885+05:30	2022-09-20 14:09:08.398912+05:30	1	t	\N	f	f
1319	PROJECT	Project	Lompoc _ Systems	247431	2022-09-20 14:09:08.398969+05:30	2022-09-20 14:09:08.398996+05:30	1	t	\N	f	f
1320	PROJECT	Project	Lonabaugh Markets Distributors	247432	2022-09-20 14:09:08.399053+05:30	2022-09-20 14:09:08.39908+05:30	1	t	\N	f	f
1321	PROJECT	Project	Lorandeau Builders Holding Corp.	247433	2022-09-20 14:09:08.399137+05:30	2022-09-20 14:09:08.399164+05:30	1	t	\N	f	f
1322	PROJECT	Project	Lou Baus	247434	2022-09-20 14:09:08.39922+05:30	2022-09-20 14:09:08.399248+05:30	1	t	\N	f	f
1323	PROJECT	Project	Louis Fabre	247435	2022-09-20 14:09:08.399304+05:30	2022-09-20 14:09:08.399342+05:30	1	t	\N	f	f
1324	PROJECT	Project	Loven and Frothingham Hardware Distributors	247436	2022-09-20 14:09:08.399523+05:30	2022-09-20 14:09:08.399551+05:30	1	t	\N	f	f
1325	PROJECT	Project	Lucic and Perfect Publishing Systems	247437	2022-09-20 14:09:08.399607+05:30	2022-09-20 14:09:08.399634+05:30	1	t	\N	f	f
1326	PROJECT	Project	Lucie Hospital Group	247438	2022-09-20 14:09:08.399691+05:30	2022-09-20 14:09:08.399718+05:30	1	t	\N	f	f
1327	PROJECT	Project	Luffy Apartments Company	247439	2022-09-20 14:09:08.399786+05:30	2022-09-20 14:09:08.399998+05:30	1	t	\N	f	f
1328	PROJECT	Project	Luigi Imports	247440	2022-09-20 14:09:08.400057+05:30	2022-09-20 14:09:08.400084+05:30	1	t	\N	f	f
1329	PROJECT	Project	Lummus Telecom Rentals	247441	2022-09-20 14:09:08.400141+05:30	2022-09-20 14:09:08.400169+05:30	1	t	\N	f	f
1330	PROJECT	Project	Lurtz Painting Co.	247442	2022-09-20 14:09:08.400225+05:30	2022-09-20 14:09:08.400263+05:30	1	t	\N	f	f
1331	PROJECT	Project	Lyas Builders Inc.	247443	2022-09-20 14:09:08.400443+05:30	2022-09-20 14:09:08.400471+05:30	1	t	\N	f	f
1332	PROJECT	Project	MAC	247444	2022-09-20 14:09:08.400528+05:30	2022-09-20 14:09:08.400555+05:30	1	t	\N	f	f
1333	PROJECT	Project	MPower	247445	2022-09-20 14:09:08.400612+05:30	2022-09-20 14:09:08.400639+05:30	1	t	\N	f	f
1334	PROJECT	Project	MW International (CAD)	247446	2022-09-20 14:09:08.406643+05:30	2022-09-20 14:09:08.406685+05:30	1	t	\N	f	f
1335	PROJECT	Project	Mackenzie Corporation	247447	2022-09-20 14:09:08.406751+05:30	2022-09-20 14:09:08.40678+05:30	1	t	\N	f	f
1336	PROJECT	Project	Mackie Painting Company	247448	2022-09-20 14:09:08.406841+05:30	2022-09-20 14:09:08.406869+05:30	1	t	\N	f	f
1337	PROJECT	Project	Malena Construction Fabricators	247449	2022-09-20 14:09:08.406928+05:30	2022-09-20 14:09:08.406955+05:30	1	t	\N	f	f
1338	PROJECT	Project	Maleonado Publishing Company	247450	2022-09-20 14:09:08.407013+05:30	2022-09-20 14:09:08.407041+05:30	1	t	\N	f	f
1339	PROJECT	Project	Mandos	247451	2022-09-20 14:09:08.407477+05:30	2022-09-20 14:09:08.40781+05:30	1	t	\N	f	f
1340	PROJECT	Project	Manivong Apartments Incorporated	247452	2022-09-20 14:09:08.407872+05:30	2022-09-20 14:09:08.4079+05:30	1	t	\N	f	f
1341	PROJECT	Project	Manwarren Markets Holding Corp.	247453	2022-09-20 14:09:08.40796+05:30	2022-09-20 14:09:08.407987+05:30	1	t	\N	f	f
1342	PROJECT	Project	Maple Leaf Foods	247454	2022-09-20 14:09:08.408045+05:30	2022-09-20 14:09:08.408072+05:30	1	t	\N	f	f
1343	PROJECT	Project	Marabella Title Agency	247455	2022-09-20 14:09:08.40813+05:30	2022-09-20 14:09:08.408158+05:30	1	t	\N	f	f
1344	PROJECT	Project	Marietta Title Co.	247456	2022-09-20 14:09:08.408215+05:30	2022-09-20 14:09:08.408242+05:30	1	t	\N	f	f
1345	PROJECT	Project	Marionneaux Catering Incorporated	247457	2022-09-20 14:09:08.408299+05:30	2022-09-20 14:09:08.408337+05:30	1	t	\N	f	f
1346	PROJECT	Project	Mark's Sporting Goods	247458	2022-09-20 14:09:08.408504+05:30	2022-09-20 14:09:08.408529+05:30	1	t	\N	f	f
1347	PROJECT	Project	Markewich Builders Rentals	247459	2022-09-20 14:09:08.408601+05:30	2022-09-20 14:09:08.408628+05:30	1	t	\N	f	f
1348	PROJECT	Project	Marrello Software Services	247460	2022-09-20 14:09:08.408686+05:30	2022-09-20 14:09:08.408713+05:30	1	t	\N	f	f
1349	PROJECT	Project	Marston Hardware -	247461	2022-09-20 14:09:08.40877+05:30	2022-09-20 14:09:08.408797+05:30	1	t	\N	f	f
1350	PROJECT	Project	Martin Gelina	247462	2022-09-20 14:09:08.408855+05:30	2022-09-20 14:09:08.408882+05:30	1	t	\N	f	f
1351	PROJECT	Project	Mason's Travel Services	247463	2022-09-20 14:09:08.408939+05:30	2022-09-20 14:09:08.408966+05:30	1	t	\N	f	f
1352	PROJECT	Project	Matsuzaki Builders Services	247464	2022-09-20 14:09:08.409023+05:30	2022-09-20 14:09:08.40905+05:30	1	t	\N	f	f
1353	PROJECT	Project	Matthew Davison	247465	2022-09-20 14:09:08.409106+05:30	2022-09-20 14:09:08.409133+05:30	1	t	\N	f	f
1354	PROJECT	Project	Matzke Title Co.	247466	2022-09-20 14:09:08.40919+05:30	2022-09-20 14:09:08.409216+05:30	1	t	\N	f	f
1355	PROJECT	Project	Maxx Corner Market	247467	2022-09-20 14:09:08.409273+05:30	2022-09-20 14:09:08.4093+05:30	1	t	\N	f	f
1356	PROJECT	Project	McEdwards & Whitwell	247468	2022-09-20 14:09:08.409371+05:30	2022-09-20 14:09:08.409494+05:30	1	t	\N	f	f
1357	PROJECT	Project	McKay Financial	247469	2022-09-20 14:09:08.409569+05:30	2022-09-20 14:09:08.409596+05:30	1	t	\N	f	f
1358	PROJECT	Project	Mcburnie Hardware Dynamics	247470	2022-09-20 14:09:08.409653+05:30	2022-09-20 14:09:08.40968+05:30	1	t	\N	f	f
1359	PROJECT	Project	Mcdorman Software Holding Corp.	247471	2022-09-20 14:09:08.409737+05:30	2022-09-20 14:09:08.409764+05:30	1	t	\N	f	f
1360	PROJECT	Project	Mcelderry Apartments Systems	247472	2022-09-20 14:09:08.40982+05:30	2022-09-20 14:09:08.409847+05:30	1	t	\N	f	f
1361	PROJECT	Project	Mcguff and Spriggins Hospital Group	247473	2022-09-20 14:09:08.410119+05:30	2022-09-20 14:09:08.410153+05:30	1	t	\N	f	f
1362	PROJECT	Project	Mcoy and Donlin Attorneys Sales	247474	2022-09-20 14:09:08.410213+05:30	2022-09-20 14:09:08.410453+05:30	1	t	\N	f	f
1363	PROJECT	Project	Medcan Mgmt Inc	247475	2022-09-20 14:09:08.410686+05:30	2022-09-20 14:09:08.410881+05:30	1	t	\N	f	f
1364	PROJECT	Project	Medved	247476	2022-09-20 14:09:08.411072+05:30	2022-09-20 14:09:08.4111+05:30	1	t	\N	f	f
1365	PROJECT	Project	Megaloid labs	247477	2022-09-20 14:09:08.411535+05:30	2022-09-20 14:09:08.411563+05:30	1	t	\N	f	f
1366	PROJECT	Project	Meisner Software Inc.	247478	2022-09-20 14:09:08.411621+05:30	2022-09-20 14:09:08.411649+05:30	1	t	\N	f	f
1367	PROJECT	Project	Mele Plumbing Manufacturing	247479	2022-09-20 14:09:08.411705+05:30	2022-09-20 14:09:08.411732+05:30	1	t	\N	f	f
1368	PROJECT	Project	Melissa Wine Shop	247480	2022-09-20 14:09:08.411788+05:30	2022-09-20 14:09:08.411816+05:30	1	t	\N	f	f
1369	PROJECT	Project	Melville Painting Rentals	247481	2022-09-20 14:09:08.411872+05:30	2022-09-20 14:09:08.411899+05:30	1	t	\N	f	f
1370	PROJECT	Project	Meneses Telecom Corporation	247482	2022-09-20 14:09:08.411955+05:30	2022-09-20 14:09:08.411983+05:30	1	t	\N	f	f
1371	PROJECT	Project	Mentor Graphics	247483	2022-09-20 14:09:08.412039+05:30	2022-09-20 14:09:08.412067+05:30	1	t	\N	f	f
1372	PROJECT	Project	Micehl Bertrand	247484	2022-09-20 14:09:08.412123+05:30	2022-09-20 14:09:08.41215+05:30	1	t	\N	f	f
1373	PROJECT	Project	Michael Jannsen	247485	2022-09-20 14:09:08.412206+05:30	2022-09-20 14:09:08.412233+05:30	1	t	\N	f	f
1374	PROJECT	Project	Michael Spencer	247486	2022-09-20 14:09:08.41229+05:30	2022-09-20 14:09:08.412317+05:30	1	t	\N	f	f
1375	PROJECT	Project	Michael Wakefield	247487	2022-09-20 14:09:08.412374+05:30	2022-09-20 14:09:08.412412+05:30	1	t	\N	f	f
1376	PROJECT	Project	Microskills	247488	2022-09-20 14:09:08.412591+05:30	2022-09-20 14:09:08.412619+05:30	1	t	\N	f	f
1377	PROJECT	Project	Midgette Markets	247489	2022-09-20 14:09:08.412676+05:30	2022-09-20 14:09:08.412704+05:30	1	t	\N	f	f
1378	PROJECT	Project	Mike Dee	247490	2022-09-20 14:09:08.41276+05:30	2022-09-20 14:09:08.412787+05:30	1	t	\N	f	f
1379	PROJECT	Project	Mike Franko	247491	2022-09-20 14:09:08.412843+05:30	2022-09-20 14:09:08.412871+05:30	1	t	\N	f	f
1380	PROJECT	Project	Mike Miller	247492	2022-09-20 14:09:08.412927+05:30	2022-09-20 14:09:08.412954+05:30	1	t	\N	f	f
1381	PROJECT	Project	Millenium Engineering	247493	2022-09-20 14:09:08.413012+05:30	2022-09-20 14:09:08.41304+05:30	1	t	\N	f	f
1382	PROJECT	Project	Miller's Dry Cleaning	247494	2022-09-20 14:09:08.413096+05:30	2022-09-20 14:09:08.413124+05:30	1	t	\N	f	f
1383	PROJECT	Project	Mindy Peiris	247495	2022-09-20 14:09:08.41318+05:30	2022-09-20 14:09:08.413207+05:30	1	t	\N	f	f
1384	PROJECT	Project	Mineral Painting Inc.	247496	2022-09-20 14:09:08.421222+05:30	2022-09-20 14:09:08.421275+05:30	1	t	\N	f	f
1385	PROJECT	Project	Miquel Apartments Leasing	247497	2022-09-20 14:09:08.421643+05:30	2022-09-20 14:09:08.421807+05:30	1	t	\N	f	f
1386	PROJECT	Project	Mission Liquors	247498	2022-09-20 14:09:08.422556+05:30	2022-09-20 14:09:08.422605+05:30	1	t	\N	f	f
1387	PROJECT	Project	Mitani Hardware Company	247499	2022-09-20 14:09:08.42269+05:30	2022-09-20 14:09:08.422723+05:30	1	t	\N	f	f
1819	PROJECT	Project	test	247931	2022-09-20 14:09:09.340644+05:30	2022-09-20 14:09:09.340672+05:30	1	t	\N	f	f
1388	PROJECT	Project	Mitchell & assoc	247500	2022-09-20 14:09:08.422798+05:30	2022-09-20 14:09:08.422828+05:30	1	t	\N	f	f
1389	PROJECT	Project	Mitchelle Title -	247501	2022-09-20 14:09:08.422897+05:30	2022-09-20 14:09:08.422926+05:30	1	t	\N	f	f
1390	PROJECT	Project	Mitra	247502	2022-09-20 14:09:08.422992+05:30	2022-09-20 14:09:08.423021+05:30	1	t	\N	f	f
1391	PROJECT	Project	Molesworth and Repress Liquors Leasing	247503	2022-09-20 14:09:08.423085+05:30	2022-09-20 14:09:08.423114+05:30	1	t	\N	f	f
1392	PROJECT	Project	Momphard Painting Sales	247504	2022-09-20 14:09:08.423177+05:30	2022-09-20 14:09:08.423206+05:30	1	t	\N	f	f
1393	PROJECT	Project	Monica Parker	247505	2022-09-20 14:09:08.423596+05:30	2022-09-20 14:09:08.423702+05:30	1	t	\N	f	f
1394	PROJECT	Project	Moores Builders Agency	247506	2022-09-20 14:09:08.42384+05:30	2022-09-20 14:09:08.423891+05:30	1	t	\N	f	f
1395	PROJECT	Project	Moots Painting Distributors	247507	2022-09-20 14:09:08.424169+05:30	2022-09-20 14:09:08.424214+05:30	1	t	\N	f	f
1396	PROJECT	Project	Moreb Plumbing Corporation	247508	2022-09-20 14:09:08.424303+05:30	2022-09-20 14:09:08.42435+05:30	1	t	\N	f	f
1397	PROJECT	Project	Mortgage Center	247509	2022-09-20 14:09:08.424617+05:30	2022-09-20 14:09:08.42466+05:30	1	t	\N	f	f
1398	PROJECT	Project	Moss Builders	247510	2022-09-20 14:09:08.424748+05:30	2022-09-20 14:09:08.424779+05:30	1	t	\N	f	f
1399	PROJECT	Project	Mount Lake Terrace Markets Fabricators	247511	2022-09-20 14:09:08.424855+05:30	2022-09-20 14:09:08.424906+05:30	1	t	\N	f	f
1400	PROJECT	Project	Moving Store	247512	2022-09-20 14:09:08.425064+05:30	2022-09-20 14:09:08.425118+05:30	1	t	\N	f	f
1401	PROJECT	Project	MuscleTech	247513	2022-09-20 14:09:08.425238+05:30	2022-09-20 14:09:08.425287+05:30	1	t	\N	f	f
1402	PROJECT	Project	Nania Painting Networking	247514	2022-09-20 14:09:08.425791+05:30	2022-09-20 14:09:08.425883+05:30	1	t	\N	f	f
1403	PROJECT	Project	Neal Ferguson	247515	2022-09-20 14:09:08.426045+05:30	2022-09-20 14:09:08.426221+05:30	1	t	\N	f	f
1404	PROJECT	Project	Nephew Publishing Group	247516	2022-09-20 14:09:08.426643+05:30	2022-09-20 14:09:08.426711+05:30	1	t	\N	f	f
1405	PROJECT	Project	NetPace Promotions	247517	2022-09-20 14:09:08.426869+05:30	2022-09-20 14:09:08.426934+05:30	1	t	\N	f	f
1406	PROJECT	Project	NetStar Inc	247518	2022-09-20 14:09:08.427233+05:30	2022-09-20 14:09:08.427293+05:30	1	t	\N	f	f
1407	PROJECT	Project	NetSuite Incorp	247519	2022-09-20 14:09:08.427713+05:30	2022-09-20 14:09:08.427888+05:30	1	t	\N	f	f
1408	PROJECT	Project	New Design of Rack	247520	2022-09-20 14:09:08.428004+05:30	2022-09-20 14:09:08.428038+05:30	1	t	\N	f	f
1409	PROJECT	Project	New Server Rack Design	247521	2022-09-20 14:09:08.428112+05:30	2022-09-20 14:09:08.428143+05:30	1	t	\N	f	f
1410	PROJECT	Project	New Ventures	247522	2022-09-20 14:09:08.428211+05:30	2022-09-20 14:09:08.428242+05:30	1	t	\N	f	f
1411	PROJECT	Project	Niedzwiedz Antiques and Associates	247523	2022-09-20 14:09:08.428308+05:30	2022-09-20 14:09:08.428339+05:30	1	t	\N	f	f
1412	PROJECT	Project	Nikon	247524	2022-09-20 14:09:08.428587+05:30	2022-09-20 14:09:08.428655+05:30	1	t	\N	f	f
1413	PROJECT	Project	Nordon Metal Fabricators Systems	247525	2022-09-20 14:09:08.428882+05:30	2022-09-20 14:09:08.428929+05:30	1	t	\N	f	f
1414	PROJECT	Project	Novida and Chochrek Leasing Manufacturing	247526	2022-09-20 14:09:08.429017+05:30	2022-09-20 14:09:08.429048+05:30	1	t	\N	f	f
1415	PROJECT	Project	Novx	247527	2022-09-20 14:09:08.429113+05:30	2022-09-20 14:09:08.429142+05:30	1	t	\N	f	f
1416	PROJECT	Project	ONLINE1	247528	2022-09-20 14:09:08.429207+05:30	2022-09-20 14:09:08.429481+05:30	1	t	\N	f	f
1417	PROJECT	Project	OREA	247529	2022-09-20 14:09:08.429561+05:30	2022-09-20 14:09:08.42959+05:30	1	t	\N	f	f
1418	PROJECT	Project	OSPE Inc	247530	2022-09-20 14:09:08.429656+05:30	2022-09-20 14:09:08.429685+05:30	1	t	\N	f	f
1419	PROJECT	Project	Oaks and Winters Inc	247531	2022-09-20 14:09:08.429758+05:30	2022-09-20 14:09:08.429786+05:30	1	t	\N	f	f
1420	PROJECT	Project	Oceanside Hardware	247532	2022-09-20 14:09:08.429845+05:30	2022-09-20 14:09:08.429873+05:30	1	t	\N	f	f
1421	PROJECT	Project	Oconner _ Holding Corp.	247533	2022-09-20 14:09:08.429931+05:30	2022-09-20 14:09:08.429958+05:30	1	t	\N	f	f
1422	PROJECT	Project	Oeder Liquors Company	247534	2022-09-20 14:09:08.430177+05:30	2022-09-20 14:09:08.430345+05:30	1	t	\N	f	f
1494	PROJECT	Project	Randy James	247606	2022-09-20 14:09:08.957653+05:30	2022-09-20 14:09:08.957764+05:30	1	t	\N	f	f
1423	PROJECT	Project	Oestreich Liquors Inc.	247535	2022-09-20 14:09:08.430912+05:30	2022-09-20 14:09:08.430951+05:30	1	t	\N	f	f
1424	PROJECT	Project	Office Remodel	247536	2022-09-20 14:09:08.431023+05:30	2022-09-20 14:09:08.431052+05:30	1	t	\N	f	f
1425	PROJECT	Project	Oiler Corporation	247537	2022-09-20 14:09:08.431111+05:30	2022-09-20 14:09:08.431138+05:30	1	t	\N	f	f
1426	PROJECT	Project	Oldsmar Liquors and Associates	247538	2022-09-20 14:09:08.431196+05:30	2022-09-20 14:09:08.431223+05:30	1	t	\N	f	f
1427	PROJECT	Project	Oliver Skin Supplies	247539	2022-09-20 14:09:08.43128+05:30	2022-09-20 14:09:08.431307+05:30	1	t	\N	f	f
1428	PROJECT	Project	Olympia Antiques Management	247540	2022-09-20 14:09:08.431497+05:30	2022-09-20 14:09:08.431536+05:30	1	t	\N	f	f
1429	PROJECT	Project	Orange Leasing -	247541	2022-09-20 14:09:08.431594+05:30	2022-09-20 14:09:08.431621+05:30	1	t	\N	f	f
1430	PROJECT	Project	Orion Hardware	247542	2022-09-20 14:09:08.431678+05:30	2022-09-20 14:09:08.431705+05:30	1	t	\N	f	f
1431	PROJECT	Project	Orlando Automotive Leasing	247543	2022-09-20 14:09:08.431764+05:30	2022-09-20 14:09:08.431791+05:30	1	t	\N	f	f
1432	PROJECT	Project	Ornelas and Ciejka Painting and Associates	247544	2022-09-20 14:09:08.431848+05:30	2022-09-20 14:09:08.431875+05:30	1	t	\N	f	f
1433	PROJECT	Project	Ortego Construction Distributors	247545	2022-09-20 14:09:08.431932+05:30	2022-09-20 14:09:08.431959+05:30	1	t	\N	f	f
1434	PROJECT	Project	Osler Antiques -	247546	2022-09-20 14:09:08.842721+05:30	2022-09-20 14:09:08.842772+05:30	1	t	\N	f	f
1435	PROJECT	Project	Ostling Metal Fabricators Fabricators	247547	2022-09-20 14:09:08.842848+05:30	2022-09-20 14:09:08.842889+05:30	1	t	\N	f	f
1436	PROJECT	Project	Ostrzyeki Markets Distributors	247548	2022-09-20 14:09:08.842953+05:30	2022-09-20 14:09:08.842981+05:30	1	t	\N	f	f
1437	PROJECT	Project	Owasso Attorneys Holding Corp.	247549	2022-09-20 14:09:08.843039+05:30	2022-09-20 14:09:08.843076+05:30	1	t	\N	f	f
1438	PROJECT	Project	Pacific Northwest	247550	2022-09-20 14:09:08.843143+05:30	2022-09-20 14:09:08.843154+05:30	1	t	\N	f	f
1439	PROJECT	Project	Pagliari Builders Services	247551	2022-09-20 14:09:08.84335+05:30	2022-09-20 14:09:08.843378+05:30	1	t	\N	f	f
1440	PROJECT	Project	Palmer and Barnar Liquors Leasing	247552	2022-09-20 14:09:08.843455+05:30	2022-09-20 14:09:08.843488+05:30	1	t	\N	f	f
1441	PROJECT	Project	Palmisano Hospital Fabricators	247553	2022-09-20 14:09:08.843543+05:30	2022-09-20 14:09:08.843568+05:30	1	t	\N	f	f
1442	PROJECT	Project	Palys Attorneys	247554	2022-09-20 14:09:08.843622+05:30	2022-09-20 14:09:08.843659+05:30	1	t	\N	f	f
1443	PROJECT	Project	Panora Lumber Dynamics	247555	2022-09-20 14:09:08.843729+05:30	2022-09-20 14:09:08.843752+05:30	1	t	\N	f	f
1444	PROJECT	Project	Parking Lot Construction	247556	2022-09-20 14:09:08.843808+05:30	2022-09-20 14:09:08.843821+05:30	1	t	\N	f	f
1445	PROJECT	Project	Pasanen Attorneys Agency	247557	2022-09-20 14:09:08.843875+05:30	2022-09-20 14:09:08.843899+05:30	1	t	\N	f	f
1446	PROJECT	Project	Patel Cafe	247558	2022-09-20 14:09:08.843969+05:30	2022-09-20 14:09:08.843992+05:30	1	t	\N	f	f
1447	PROJECT	Project	Paveglio Leasing Leasing	247559	2022-09-20 14:09:08.844052+05:30	2022-09-20 14:09:08.844066+05:30	1	t	\N	f	f
1448	PROJECT	Project	Peak Products	247560	2022-09-20 14:09:08.84412+05:30	2022-09-20 14:09:08.844154+05:30	1	t	\N	f	f
1449	PROJECT	Project	Penalver Automotive and Associates	247561	2022-09-20 14:09:08.844321+05:30	2022-09-20 14:09:08.844343+05:30	1	t	\N	f	f
1450	PROJECT	Project	Penco Medical Inc.	247562	2022-09-20 14:09:08.844396+05:30	2022-09-20 14:09:08.844433+05:30	1	t	\N	f	f
1451	PROJECT	Project	Penister Hospital Fabricators	247563	2022-09-20 14:09:08.844506+05:30	2022-09-20 14:09:08.844557+05:30	1	t	\N	f	f
1452	PROJECT	Project	Pertuit Liquors Management	247564	2022-09-20 14:09:08.844619+05:30	2022-09-20 14:09:08.844645+05:30	1	t	\N	f	f
1453	PROJECT	Project	Peterson Builders & Assoc	247565	2022-09-20 14:09:08.844699+05:30	2022-09-20 14:09:08.844723+05:30	1	t	\N	f	f
1454	PROJECT	Project	Petticrew Apartments Incorporated	247566	2022-09-20 14:09:08.844795+05:30	2022-09-20 14:09:08.844818+05:30	1	t	\N	f	f
1455	PROJECT	Project	Peveler and Tyrer Software Networking	247567	2022-09-20 14:09:08.844871+05:30	2022-09-20 14:09:08.844893+05:30	1	t	\N	f	f
1456	PROJECT	Project	Phillip Van Hook	247568	2022-09-20 14:09:08.844954+05:30	2022-09-20 14:09:08.844994+05:30	1	t	\N	f	f
1457	PROJECT	Project	Pickler Construction Leasing	247569	2022-09-20 14:09:08.845192+05:30	2022-09-20 14:09:08.845501+05:30	1	t	\N	f	f
1458	PROJECT	Project	Pigler Plumbing Management	247570	2022-09-20 14:09:08.845597+05:30	2022-09-20 14:09:08.845638+05:30	1	t	\N	f	f
1459	PROJECT	Project	Pilkerton Windows Sales	247571	2022-09-20 14:09:08.845732+05:30	2022-09-20 14:09:08.845763+05:30	1	t	\N	f	f
1460	PROJECT	Project	Pitney Bowes	247572	2022-09-20 14:09:08.845869+05:30	2022-09-20 14:09:08.845893+05:30	1	t	\N	f	f
1461	PROJECT	Project	Pittaway Inc	247573	2022-09-20 14:09:08.845944+05:30	2022-09-20 14:09:08.845964+05:30	1	t	\N	f	f
1462	PROJECT	Project	Pittsburgh Quantum Analytics	247574	2022-09-20 14:09:08.846016+05:30	2022-09-20 14:09:08.846037+05:30	1	t	\N	f	f
1463	PROJECT	Project	Pittsburgh Windows Incorporated	247575	2022-09-20 14:09:08.84611+05:30	2022-09-20 14:09:08.846139+05:30	1	t	\N	f	f
1464	PROJECT	Project	Plantronics (EUR)	247576	2022-09-20 14:09:08.846254+05:30	2022-09-20 14:09:08.846294+05:30	1	t	\N	f	f
1465	PROJECT	Project	Plexfase Construction Inc.	247577	2022-09-20 14:09:08.846358+05:30	2022-09-20 14:09:08.846387+05:30	1	t	\N	f	f
1466	PROJECT	Project	Podvin Software Networking	247578	2022-09-20 14:09:08.846448+05:30	2022-09-20 14:09:08.846478+05:30	1	t	\N	f	f
1467	PROJECT	Project	Poland and Burrus Plumbing	247579	2022-09-20 14:09:08.84653+05:30	2022-09-20 14:09:08.846559+05:30	1	t	\N	f	f
1468	PROJECT	Project	Polard Windows	247580	2022-09-20 14:09:08.84662+05:30	2022-09-20 14:09:08.846649+05:30	1	t	\N	f	f
1469	PROJECT	Project	Pomona Hardware Leasing	247581	2022-09-20 14:09:08.84671+05:30	2022-09-20 14:09:08.846792+05:30	1	t	\N	f	f
1470	PROJECT	Project	Ponniah	247582	2022-09-20 14:09:08.846937+05:30	2022-09-20 14:09:08.846963+05:30	1	t	\N	f	f
1471	PROJECT	Project	Port Angeles Telecom Networking	247583	2022-09-20 14:09:08.847027+05:30	2022-09-20 14:09:08.847051+05:30	1	t	\N	f	f
1472	PROJECT	Project	Port Townsend Title Corporation	247584	2022-09-20 14:09:08.847634+05:30	2022-09-20 14:09:08.847667+05:30	1	t	\N	f	f
1473	PROJECT	Project	Pote Leasing Rentals	247585	2022-09-20 14:09:08.84773+05:30	2022-09-20 14:09:08.847752+05:30	1	t	\N	f	f
1474	PROJECT	Project	Primas Consulting	247586	2022-09-20 14:09:08.847814+05:30	2022-09-20 14:09:08.847835+05:30	1	t	\N	f	f
1475	PROJECT	Project	Princeton Automotive Management	247587	2022-09-20 14:09:08.847888+05:30	2022-09-20 14:09:08.847917+05:30	1	t	\N	f	f
1476	PROJECT	Project	Pritts Construction Distributors	247588	2022-09-20 14:09:08.847978+05:30	2022-09-20 14:09:08.848007+05:30	1	t	\N	f	f
1477	PROJECT	Project	Progress Inc	247589	2022-09-20 14:09:08.848062+05:30	2022-09-20 14:09:08.848084+05:30	1	t	\N	f	f
1478	PROJECT	Project	Prokup Plumbing Corporation	247590	2022-09-20 14:09:08.848145+05:30	2022-09-20 14:09:08.848174+05:30	1	t	\N	f	f
1479	PROJECT	Project	Prudential	247591	2022-09-20 14:09:08.84836+05:30	2022-09-20 14:09:08.84839+05:30	1	t	\N	f	f
1480	PROJECT	Project	Ptomey Title Group	247592	2022-09-20 14:09:08.848453+05:30	2022-09-20 14:09:08.848475+05:30	1	t	\N	f	f
1481	PROJECT	Project	Pueblo Construction Fabricators	247593	2022-09-20 14:09:08.848536+05:30	2022-09-20 14:09:08.848557+05:30	1	t	\N	f	f
1482	PROJECT	Project	Pulse	247594	2022-09-20 14:09:08.848608+05:30	2022-09-20 14:09:08.848637+05:30	1	t	\N	f	f
1483	PROJECT	Project	Purchase Construction Agency	247595	2022-09-20 14:09:08.848688+05:30	2022-09-20 14:09:08.848706+05:30	1	t	\N	f	f
1484	PROJECT	Project	Puyallup Liquors Networking	247596	2022-09-20 14:09:08.955018+05:30	2022-09-20 14:09:08.955327+05:30	1	t	\N	f	f
1485	PROJECT	Project	QJunction Inc	247597	2022-09-20 14:09:08.955665+05:30	2022-09-20 14:09:08.95572+05:30	1	t	\N	f	f
1486	PROJECT	Project	Qualle Metal Fabricators Distributors	247598	2022-09-20 14:09:08.956141+05:30	2022-09-20 14:09:08.95633+05:30	1	t	\N	f	f
1487	PROJECT	Project	Quantum X	247599	2022-09-20 14:09:08.956485+05:30	2022-09-20 14:09:08.956537+05:30	1	t	\N	f	f
1488	PROJECT	Project	Quezad Lumber Leasing	247600	2022-09-20 14:09:08.956656+05:30	2022-09-20 14:09:08.956697+05:30	1	t	\N	f	f
1489	PROJECT	Project	Quiterio Windows Co.	247601	2022-09-20 14:09:08.956916+05:30	2022-09-20 14:09:08.956963+05:30	1	t	\N	f	f
1490	PROJECT	Project	Rabeck Liquors Group	247602	2022-09-20 14:09:08.957081+05:30	2022-09-20 14:09:08.957125+05:30	1	t	\N	f	f
1491	PROJECT	Project	Ralphs Attorneys Group	247603	2022-09-20 14:09:08.957198+05:30	2022-09-20 14:09:08.957228+05:30	1	t	\N	f	f
1492	PROJECT	Project	Ramal Builders Incorporated	247604	2022-09-20 14:09:08.957289+05:30	2022-09-20 14:09:08.957301+05:30	1	t	\N	f	f
1493	PROJECT	Project	Ramsy Publishing Company	247605	2022-09-20 14:09:08.957448+05:30	2022-09-20 14:09:08.957512+05:30	1	t	\N	f	f
1495	PROJECT	Project	Randy Rudd	247607	2022-09-20 14:09:08.958152+05:30	2022-09-20 14:09:08.958327+05:30	1	t	\N	f	f
1496	PROJECT	Project	Ras Windows -	247608	2022-09-20 14:09:08.959693+05:30	2022-09-20 14:09:08.959921+05:30	1	t	\N	f	f
1497	PROJECT	Project	Rastorfer Automotive Holding Corp.	247609	2022-09-20 14:09:08.960099+05:30	2022-09-20 14:09:08.960144+05:30	1	t	\N	f	f
1498	PROJECT	Project	Rauf Catering	247610	2022-09-20 14:09:08.960343+05:30	2022-09-20 14:09:08.960363+05:30	1	t	\N	f	f
1499	PROJECT	Project	RedPath Sugars	247611	2022-09-20 14:09:08.960428+05:30	2022-09-20 14:09:08.96045+05:30	1	t	\N	f	f
1500	PROJECT	Project	Redick Antiques Inc.	247612	2022-09-20 14:09:08.960506+05:30	2022-09-20 14:09:08.960519+05:30	1	t	\N	f	f
1501	PROJECT	Project	Reedus Telecom Group	247613	2022-09-20 14:09:08.96057+05:30	2022-09-20 14:09:08.960591+05:30	1	t	\N	f	f
1502	PROJECT	Project	Refco	247614	2022-09-20 14:09:08.960819+05:30	2022-09-20 14:09:08.960848+05:30	1	t	\N	f	f
1503	PROJECT	Project	Reinfeld and Jurczak Hospital Incorporated	247615	2022-09-20 14:09:08.960911+05:30	2022-09-20 14:09:08.96094+05:30	1	t	\N	f	f
1504	PROJECT	Project	Reinhardt and Sabori Painting Group	247616	2022-09-20 14:09:08.961002+05:30	2022-09-20 14:09:08.961031+05:30	1	t	\N	f	f
1505	PROJECT	Project	Reisdorf Title Services	247617	2022-09-20 14:09:08.961151+05:30	2022-09-20 14:09:08.961192+05:30	1	t	\N	f	f
1506	PROJECT	Project	Reisman Windows Management	247618	2022-09-20 14:09:08.961415+05:30	2022-09-20 14:09:08.961458+05:30	1	t	\N	f	f
1507	PROJECT	Project	Remodel	247619	2022-09-20 14:09:08.961526+05:30	2022-09-20 14:09:08.961548+05:30	1	t	\N	f	f
1508	PROJECT	Project	Rennemeyer Liquors Systems	247620	2022-09-20 14:09:08.961614+05:30	2022-09-20 14:09:08.961639+05:30	1	t	\N	f	f
1509	PROJECT	Project	Republic Builders and Associates	247621	2022-09-20 14:09:08.961702+05:30	2022-09-20 14:09:08.961792+05:30	1	t	\N	f	f
1510	PROJECT	Project	Rey Software Inc.	247622	2022-09-20 14:09:08.97052+05:30	2022-09-20 14:09:08.97058+05:30	1	t	\N	f	f
1511	PROJECT	Project	Rezentes Catering Dynamics	247623	2022-09-20 14:09:08.970701+05:30	2022-09-20 14:09:08.97072+05:30	1	t	\N	f	f
1512	PROJECT	Project	Rhody Leasing and Associates	247624	2022-09-20 14:09:08.970775+05:30	2022-09-20 14:09:08.970807+05:30	1	t	\N	f	f
1513	PROJECT	Project	Rickers Apartments Company	247625	2022-09-20 14:09:08.970871+05:30	2022-09-20 14:09:08.970912+05:30	1	t	\N	f	f
1514	PROJECT	Project	Ridderhoff Painting Services	247626	2022-09-20 14:09:08.970991+05:30	2022-09-20 14:09:08.971009+05:30	1	t	\N	f	f
1515	PROJECT	Project	Ridgeway Corporation	247627	2022-09-20 14:09:08.97105+05:30	2022-09-20 14:09:08.971071+05:30	1	t	\N	f	f
1516	PROJECT	Project	Riede Title and Associates	247628	2022-09-20 14:09:08.971141+05:30	2022-09-20 14:09:08.971181+05:30	1	t	\N	f	f
1517	PROJECT	Project	Rio Rancho Painting Agency	247629	2022-09-20 14:09:08.971426+05:30	2022-09-20 14:09:08.971458+05:30	1	t	\N	f	f
1518	PROJECT	Project	Riverside Hospital and Associates	247630	2022-09-20 14:09:08.971531+05:30	2022-09-20 14:09:08.971571+05:30	1	t	\N	f	f
1519	PROJECT	Project	Robare Builders Corporation	247631	2022-09-20 14:09:08.971641+05:30	2022-09-20 14:09:08.97167+05:30	1	t	\N	f	f
1520	PROJECT	Project	Robert Brady	247632	2022-09-20 14:09:08.971735+05:30	2022-09-20 14:09:08.971757+05:30	1	t	\N	f	f
1521	PROJECT	Project	Robert Huffman	247633	2022-09-20 14:09:08.971837+05:30	2022-09-20 14:09:08.971883+05:30	1	t	\N	f	f
1522	PROJECT	Project	Robert Lee	247634	2022-09-20 14:09:08.971937+05:30	2022-09-20 14:09:08.971956+05:30	1	t	\N	f	f
1523	PROJECT	Project	Robert Solan	247635	2022-09-20 14:09:08.97201+05:30	2022-09-20 14:09:08.972029+05:30	1	t	\N	f	f
1524	PROJECT	Project	Rogers Communication	247636	2022-09-20 14:09:08.972099+05:30	2022-09-20 14:09:08.972129+05:30	1	t	\N	f	f
1525	PROJECT	Project	Rosner and Savo Antiques Systems	247637	2022-09-20 14:09:08.972297+05:30	2022-09-20 14:09:08.972323+05:30	1	t	\N	f	f
1526	PROJECT	Project	Ross Nepean	247638	2022-09-20 14:09:08.972404+05:30	2022-09-20 14:09:08.972448+05:30	1	t	\N	f	f
1527	PROJECT	Project	Roswell Leasing Management	247639	2022-09-20 14:09:08.972504+05:30	2022-09-20 14:09:08.972525+05:30	1	t	\N	f	f
1528	PROJECT	Project	Roule and Mattsey _ Management	247640	2022-09-20 14:09:08.972594+05:30	2022-09-20 14:09:08.972634+05:30	1	t	\N	f	f
1529	PROJECT	Project	Roundtree Attorneys Inc.	247641	2022-09-20 14:09:08.972704+05:30	2022-09-20 14:09:08.972737+05:30	1	t	\N	f	f
1530	PROJECT	Project	Rowie Williams	247642	2022-09-20 14:09:08.972791+05:30	2022-09-20 14:09:08.97282+05:30	1	t	\N	f	f
1531	PROJECT	Project	Roycroft Construction	247643	2022-09-20 14:09:08.972891+05:30	2022-09-20 14:09:08.972913+05:30	1	t	\N	f	f
1532	PROJECT	Project	Ruleman Title Distributors	247644	2022-09-20 14:09:08.972982+05:30	2022-09-20 14:09:08.973003+05:30	1	t	\N	f	f
1533	PROJECT	Project	Russ Mygrant	247645	2022-09-20 14:09:08.973065+05:30	2022-09-20 14:09:08.973105+05:30	1	t	\N	f	f
1534	PROJECT	Project	Russell Telecom	247646	2022-09-20 14:09:08.981993+05:30	2022-09-20 14:09:08.982053+05:30	1	t	\N	f	f
1535	PROJECT	Project	Ruts Construction Holding Corp.	247647	2022-09-20 14:09:08.982125+05:30	2022-09-20 14:09:08.982213+05:30	1	t	\N	f	f
1536	PROJECT	Project	SS&C	247648	2022-09-20 14:09:08.982292+05:30	2022-09-20 14:09:08.98232+05:30	1	t	\N	f	f
1537	PROJECT	Project	Saenger _ Inc.	247649	2022-09-20 14:09:08.982537+05:30	2022-09-20 14:09:08.982599+05:30	1	t	\N	f	f
1538	PROJECT	Project	Salisbury Attorneys Group	247650	2022-09-20 14:09:08.982673+05:30	2022-09-20 14:09:08.982714+05:30	1	t	\N	f	f
1539	PROJECT	Project	Sally Ward	247651	2022-09-20 14:09:08.982943+05:30	2022-09-20 14:09:08.982989+05:30	1	t	\N	f	f
1540	PROJECT	Project	Sam Brown	247652	2022-09-20 14:09:08.983102+05:30	2022-09-20 14:09:08.983131+05:30	1	t	\N	f	f
1686	PROJECT	Project	Test a	247798	2022-09-20 14:09:09.296831+05:30	2022-09-20 14:09:09.296991+05:30	1	t	\N	f	f
1541	PROJECT	Project	Samantha Walker	247653	2022-09-20 14:09:08.98318+05:30	2022-09-20 14:09:08.983201+05:30	1	t	\N	f	f
1542	PROJECT	Project	San Angelo Automotive Rentals	247654	2022-09-20 14:09:08.983378+05:30	2022-09-20 14:09:08.983422+05:30	1	t	\N	f	f
1543	PROJECT	Project	San Diego Plumbing Distributors	247655	2022-09-20 14:09:08.98349+05:30	2022-09-20 14:09:08.983519+05:30	1	t	\N	f	f
1544	PROJECT	Project	San Diego Windows Agency	247656	2022-09-20 14:09:08.983574+05:30	2022-09-20 14:09:08.983595+05:30	1	t	\N	f	f
1545	PROJECT	Project	San Francisco Design Center	247657	2022-09-20 14:09:08.983675+05:30	2022-09-20 14:09:08.98372+05:30	1	t	\N	f	f
1546	PROJECT	Project	San Luis Obispo Construction Inc.	247658	2022-09-20 14:09:08.98378+05:30	2022-09-20 14:09:08.983794+05:30	1	t	\N	f	f
1547	PROJECT	Project	Sandoval Products Inc	247659	2022-09-20 14:09:08.983843+05:30	2022-09-20 14:09:08.983865+05:30	1	t	\N	f	f
1548	PROJECT	Project	Sandra Burns	247660	2022-09-20 14:09:08.983917+05:30	2022-09-20 14:09:08.983956+05:30	1	t	\N	f	f
1549	PROJECT	Project	Sandwich Antiques Services	247661	2022-09-20 14:09:08.984022+05:30	2022-09-20 14:09:08.984254+05:30	1	t	\N	f	f
1550	PROJECT	Project	Sandwich Telecom Sales	247662	2022-09-20 14:09:08.984446+05:30	2022-09-20 14:09:08.984477+05:30	1	t	\N	f	f
1551	PROJECT	Project	Sandy King	247663	2022-09-20 14:09:08.984544+05:30	2022-09-20 14:09:08.984559+05:30	1	t	\N	f	f
1552	PROJECT	Project	Sandy Whines	247664	2022-09-20 14:09:08.984619+05:30	2022-09-20 14:09:08.984647+05:30	1	t	\N	f	f
1553	PROJECT	Project	Santa Ana Telecom Management	247665	2022-09-20 14:09:08.984705+05:30	2022-09-20 14:09:08.984732+05:30	1	t	\N	f	f
1554	PROJECT	Project	Santa Fe Springs Construction Corporation	247666	2022-09-20 14:09:08.984789+05:30	2022-09-20 14:09:08.984816+05:30	1	t	\N	f	f
1555	PROJECT	Project	Santa Maria Lumber Inc.	247667	2022-09-20 14:09:08.984872+05:30	2022-09-20 14:09:08.9849+05:30	1	t	\N	f	f
1556	PROJECT	Project	Santa Monica Attorneys Manufacturing	247668	2022-09-20 14:09:08.984957+05:30	2022-09-20 14:09:08.984984+05:30	1	t	\N	f	f
1557	PROJECT	Project	Sarasota Software Rentals	247669	2022-09-20 14:09:08.98504+05:30	2022-09-20 14:09:08.985068+05:30	1	t	\N	f	f
1558	PROJECT	Project	Sarchett Antiques Networking	247670	2022-09-20 14:09:08.985124+05:30	2022-09-20 14:09:08.985151+05:30	1	t	\N	f	f
1559	PROJECT	Project	Sawatzky Catering Rentals	247671	2022-09-20 14:09:08.985208+05:30	2022-09-20 14:09:08.985235+05:30	1	t	\N	f	f
1560	PROJECT	Project	Sax Lumber Co.	247672	2022-09-20 14:09:08.985292+05:30	2022-09-20 14:09:08.985319+05:30	1	t	\N	f	f
1561	PROJECT	Project	Scalley Construction Inc.	247673	2022-09-20 14:09:08.985492+05:30	2022-09-20 14:09:08.985532+05:30	1	t	\N	f	f
1562	PROJECT	Project	Schlicker Metal Fabricators Fabricators	247674	2022-09-20 14:09:08.98559+05:30	2022-09-20 14:09:08.985617+05:30	1	t	\N	f	f
1563	PROJECT	Project	Schmauder Markets Corporation	247675	2022-09-20 14:09:08.985674+05:30	2022-09-20 14:09:08.985701+05:30	1	t	\N	f	f
1564	PROJECT	Project	Schmidt Sporting Goods	247676	2022-09-20 14:09:08.985758+05:30	2022-09-20 14:09:08.985785+05:30	1	t	\N	f	f
1565	PROJECT	Project	Schneck Automotive Group	247677	2022-09-20 14:09:08.985842+05:30	2022-09-20 14:09:08.985869+05:30	1	t	\N	f	f
1566	PROJECT	Project	Scholl Catering -	247678	2022-09-20 14:09:08.985925+05:30	2022-09-20 14:09:08.985953+05:30	1	t	\N	f	f
1567	PROJECT	Project	Schreck Hardware Systems	247679	2022-09-20 14:09:08.986009+05:30	2022-09-20 14:09:08.986036+05:30	1	t	\N	f	f
1568	PROJECT	Project	Schwarzenbach Attorneys Systems	247680	2022-09-20 14:09:08.986093+05:30	2022-09-20 14:09:08.98612+05:30	1	t	\N	f	f
1569	PROJECT	Project	Scottsbluff Lumber -	247681	2022-09-20 14:09:08.986176+05:30	2022-09-20 14:09:08.986204+05:30	1	t	\N	f	f
1570	PROJECT	Project	Scottsbluff Plumbing Rentals	247682	2022-09-20 14:09:08.986261+05:30	2022-09-20 14:09:08.986288+05:30	1	t	\N	f	f
1571	PROJECT	Project	Scullion Telecom Agency	247683	2022-09-20 14:09:08.986345+05:30	2022-09-20 14:09:08.986484+05:30	1	t	\N	f	f
1572	PROJECT	Project	Sebastian Inc.	247684	2022-09-20 14:09:08.986553+05:30	2022-09-20 14:09:08.986592+05:30	1	t	\N	f	f
1573	PROJECT	Project	Sebek Builders Distributors	247685	2022-09-20 14:09:08.986649+05:30	2022-09-20 14:09:08.986676+05:30	1	t	\N	f	f
1574	PROJECT	Project	Sedlak Inc	247686	2022-09-20 14:09:08.986733+05:30	2022-09-20 14:09:08.986759+05:30	1	t	\N	f	f
1575	PROJECT	Project	Seecharan and Horten Hardware Manufacturing	247687	2022-09-20 14:09:08.986816+05:30	2022-09-20 14:09:08.986843+05:30	1	t	\N	f	f
1576	PROJECT	Project	Seena Rose	247688	2022-09-20 14:09:08.986899+05:30	2022-09-20 14:09:08.986926+05:30	1	t	\N	f	f
1577	PROJECT	Project	Seilhymer Antiques Distributors	247689	2022-09-20 14:09:08.986983+05:30	2022-09-20 14:09:08.98701+05:30	1	t	\N	f	f
1578	PROJECT	Project	Selders Distributors	247690	2022-09-20 14:09:08.987066+05:30	2022-09-20 14:09:08.987093+05:30	1	t	\N	f	f
1579	PROJECT	Project	Selia Metal Fabricators Company	247691	2022-09-20 14:09:08.987149+05:30	2022-09-20 14:09:08.987176+05:30	1	t	\N	f	f
1580	PROJECT	Project	Seney Windows Agency	247692	2022-09-20 14:09:08.987247+05:30	2022-09-20 14:09:08.988044+05:30	1	t	\N	f	f
1581	PROJECT	Project	Sequim Automotive Systems	247693	2022-09-20 14:09:08.98817+05:30	2022-09-20 14:09:08.988326+05:30	1	t	\N	f	f
1582	PROJECT	Project	Service Job	247694	2022-09-20 14:09:08.988815+05:30	2022-09-20 14:09:08.98908+05:30	1	t	\N	f	f
1583	PROJECT	Project	Seyler Title Distributors	247695	2022-09-20 14:09:08.989186+05:30	2022-09-20 14:09:08.989363+05:30	1	t	\N	f	f
1584	PROJECT	Project	Shackelton Hospital Sales	247696	2022-09-20 14:09:08.998889+05:30	2022-09-20 14:09:08.998926+05:30	1	t	\N	f	f
1585	PROJECT	Project	Sharon Stone	247697	2022-09-20 14:09:08.999158+05:30	2022-09-20 14:09:08.999186+05:30	1	t	\N	f	f
1586	PROJECT	Project	Sheinbein Construction Fabricators	247698	2022-09-20 14:09:08.999391+05:30	2022-09-20 14:09:08.999434+05:30	1	t	\N	f	f
1587	PROJECT	Project	Shininger Lumber Holding Corp.	247699	2022-09-20 14:09:08.999522+05:30	2022-09-20 14:09:08.999545+05:30	1	t	\N	f	f
1588	PROJECT	Project	Shutter Title Services	247700	2022-09-20 14:09:08.999598+05:30	2022-09-20 14:09:08.999627+05:30	1	t	\N	f	f
1589	PROJECT	Project	Siddiq Software -	247701	2022-09-20 14:09:08.999736+05:30	2022-09-20 14:09:08.99978+05:30	1	t	\N	f	f
1590	PROJECT	Project	Simatry	247702	2022-09-20 14:09:08.999894+05:30	2022-09-20 14:09:08.999931+05:30	1	t	\N	f	f
1591	PROJECT	Project	Simi Valley Telecom Dynamics	247703	2022-09-20 14:09:09.000042+05:30	2022-09-20 14:09:09.000081+05:30	1	t	\N	f	f
1592	PROJECT	Project	Sindt Electric	247704	2022-09-20 14:09:09.000158+05:30	2022-09-20 14:09:09.000335+05:30	1	t	\N	f	f
1593	PROJECT	Project	Skibo Construction Dynamics	247705	2022-09-20 14:09:09.000442+05:30	2022-09-20 14:09:09.000462+05:30	1	t	\N	f	f
1594	PROJECT	Project	Slankard Automotive	247706	2022-09-20 14:09:09.000514+05:30	2022-09-20 14:09:09.000543+05:30	1	t	\N	f	f
1595	PROJECT	Project	Slatter Metal Fabricators Inc.	247707	2022-09-20 14:09:09.000604+05:30	2022-09-20 14:09:09.000623+05:30	1	t	\N	f	f
1596	PROJECT	Project	SlingShot Communications	247708	2022-09-20 14:09:09.000676+05:30	2022-09-20 14:09:09.000705+05:30	1	t	\N	f	f
1597	PROJECT	Project	Sloman and Zeccardi Builders Agency	247709	2022-09-20 14:09:09.000765+05:30	2022-09-20 14:09:09.000789+05:30	1	t	\N	f	f
1598	PROJECT	Project	Smelley _ Manufacturing	247710	2022-09-20 14:09:09.000841+05:30	2022-09-20 14:09:09.000869+05:30	1	t	\N	f	f
1599	PROJECT	Project	Smith East	247711	2022-09-20 14:09:09.000921+05:30	2022-09-20 14:09:09.00095+05:30	1	t	\N	f	f
1600	PROJECT	Project	Smith Inc.	247712	2022-09-20 14:09:09.001009+05:30	2022-09-20 14:09:09.00103+05:30	1	t	\N	f	f
1601	PROJECT	Project	Smith Photographic Equipment	247713	2022-09-20 14:09:09.001091+05:30	2022-09-20 14:09:09.001116+05:30	1	t	\N	f	f
1602	PROJECT	Project	Smith West	247714	2022-09-20 14:09:09.001168+05:30	2022-09-20 14:09:09.001196+05:30	1	t	\N	f	f
1603	PROJECT	Project	Snode and Draper Leasing Rentals	247715	2022-09-20 14:09:09.001347+05:30	2022-09-20 14:09:09.001367+05:30	1	t	\N	f	f
1604	PROJECT	Project	Soares Builders Inc.	247716	2022-09-20 14:09:09.001416+05:30	2022-09-20 14:09:09.001446+05:30	1	t	\N	f	f
1605	PROJECT	Project	Solidd Group Ltd	247717	2022-09-20 14:09:09.001499+05:30	2022-09-20 14:09:09.001517+05:30	1	t	\N	f	f
1606	PROJECT	Project	Soltrus	247718	2022-09-20 14:09:09.001559+05:30	2022-09-20 14:09:09.001579+05:30	1	t	\N	f	f
1607	PROJECT	Project	Solymani Electric Leasing	247719	2022-09-20 14:09:09.00164+05:30	2022-09-20 14:09:09.001661+05:30	1	t	\N	f	f
1608	PROJECT	Project	Sossong Plumbing Holding Corp.	247720	2022-09-20 14:09:09.001713+05:30	2022-09-20 14:09:09.001742+05:30	1	t	\N	f	f
1609	PROJECT	Project	South East	247721	2022-09-20 14:09:09.001803+05:30	2022-09-20 14:09:09.001832+05:30	1	t	\N	f	f
1610	PROJECT	Project	Spany ltd	247722	2022-09-20 14:09:09.001892+05:30	2022-09-20 14:09:09.001915+05:30	1	t	\N	f	f
1611	PROJECT	Project	Spectrum Eye	247723	2022-09-20 14:09:09.001968+05:30	2022-09-20 14:09:09.001997+05:30	1	t	\N	f	f
1612	PROJECT	Project	Sport Station	247724	2022-09-20 14:09:09.002057+05:30	2022-09-20 14:09:09.002086+05:30	1	t	\N	f	f
1613	PROJECT	Project	Sports Authority	247725	2022-09-20 14:09:09.00214+05:30	2022-09-20 14:09:09.002151+05:30	1	t	\N	f	f
1614	PROJECT	Project	Spurgin Telecom Agency	247726	2022-09-20 14:09:09.002479+05:30	2022-09-20 14:09:09.002503+05:30	1	t	\N	f	f
1615	PROJECT	Project	St Lawrence Starch	247727	2022-09-20 14:09:09.002551+05:30	2022-09-20 14:09:09.002564+05:30	1	t	\N	f	f
1616	PROJECT	Project	St. Francis Yacht Club	247728	2022-09-20 14:09:09.002614+05:30	2022-09-20 14:09:09.002638+05:30	1	t	\N	f	f
1617	PROJECT	Project	St. Mark's Church	247729	2022-09-20 14:09:09.0027+05:30	2022-09-20 14:09:09.002729+05:30	1	t	\N	f	f
1618	PROJECT	Project	Stai Publishing -	247730	2022-09-20 14:09:09.002785+05:30	2022-09-20 14:09:09.002812+05:30	1	t	\N	f	f
1619	PROJECT	Project	Stampe Leasing and Associates	247731	2022-09-20 14:09:09.002869+05:30	2022-09-20 14:09:09.002896+05:30	1	t	\N	f	f
1620	PROJECT	Project	Stantec Inc	247732	2022-09-20 14:09:09.002954+05:30	2022-09-20 14:09:09.002981+05:30	1	t	\N	f	f
1621	PROJECT	Project	Star Structural	247733	2022-09-20 14:09:09.003038+05:30	2022-09-20 14:09:09.003065+05:30	1	t	\N	f	f
1622	PROJECT	Project	Steacy Tech Inc	247734	2022-09-20 14:09:09.003122+05:30	2022-09-20 14:09:09.003149+05:30	1	t	\N	f	f
1623	PROJECT	Project	Steep and Cloud Liquors Co.	247735	2022-09-20 14:09:09.003207+05:30	2022-09-20 14:09:09.003234+05:30	1	t	\N	f	f
1624	PROJECT	Project	Steffensmeier Markets Co.	247736	2022-09-20 14:09:09.003291+05:30	2022-09-20 14:09:09.003319+05:30	1	t	\N	f	f
1625	PROJECT	Project	Steinberg Electric Networking	247737	2022-09-20 14:09:09.003469+05:30	2022-09-20 14:09:09.003508+05:30	1	t	\N	f	f
1626	PROJECT	Project	Stella Sebastian Inc	247738	2022-09-20 14:09:09.003565+05:30	2022-09-20 14:09:09.003592+05:30	1	t	\N	f	f
1627	PROJECT	Project	Stephan Simms	247739	2022-09-20 14:09:09.003649+05:30	2022-09-20 14:09:09.003676+05:30	1	t	\N	f	f
1628	PROJECT	Project	Sternberger Telecom Incorporated	247740	2022-09-20 14:09:09.003733+05:30	2022-09-20 14:09:09.00376+05:30	1	t	\N	f	f
1629	PROJECT	Project	Sterr Lumber Systems	247741	2022-09-20 14:09:09.0041+05:30	2022-09-20 14:09:09.004132+05:30	1	t	\N	f	f
1630	PROJECT	Project	Steve Davis	247742	2022-09-20 14:09:09.004191+05:30	2022-09-20 14:09:09.004212+05:30	1	t	\N	f	f
1631	PROJECT	Project	Steve Smith	247743	2022-09-20 14:09:09.004378+05:30	2022-09-20 14:09:09.004409+05:30	1	t	\N	f	f
1632	PROJECT	Project	Stewart's Valet Parking	247744	2022-09-20 14:09:09.00451+05:30	2022-09-20 14:09:09.00454+05:30	1	t	\N	f	f
1633	PROJECT	Project	Stirling Truck Services	247745	2022-09-20 14:09:09.00468+05:30	2022-09-20 14:09:09.004726+05:30	1	t	\N	f	f
1634	PROJECT	Project	Stitch Software Distributors	247746	2022-09-20 14:09:09.279987+05:30	2022-09-20 14:09:09.280029+05:30	1	t	\N	f	f
1635	PROJECT	Project	Stoett Telecom Rentals	247747	2022-09-20 14:09:09.280094+05:30	2022-09-20 14:09:09.280123+05:30	1	t	\N	f	f
1636	PROJECT	Project	Stofflet Hardware Incorporated	247748	2022-09-20 14:09:09.280185+05:30	2022-09-20 14:09:09.280214+05:30	1	t	\N	f	f
1637	PROJECT	Project	Stone & Cox	247749	2022-09-20 14:09:09.280275+05:30	2022-09-20 14:09:09.280304+05:30	1	t	\N	f	f
1638	PROJECT	Project	Stonum Catering Group	247750	2022-09-20 14:09:09.280453+05:30	2022-09-20 14:09:09.280483+05:30	1	t	\N	f	f
1639	PROJECT	Project	Storch Title Manufacturing	247751	2022-09-20 14:09:09.280545+05:30	2022-09-20 14:09:09.280574+05:30	1	t	\N	f	f
1640	PROJECT	Project	Stotelmyer and Conelly Metal Fabricators Group	247752	2022-09-20 14:09:09.280634+05:30	2022-09-20 14:09:09.280664+05:30	1	t	\N	f	f
1641	PROJECT	Project	Stower Electric Company	247753	2022-09-20 14:09:09.280725+05:30	2022-09-20 14:09:09.280754+05:30	1	t	\N	f	f
1642	PROJECT	Project	Streib and Cravy Hardware Rentals	247754	2022-09-20 14:09:09.280814+05:30	2022-09-20 14:09:09.280844+05:30	1	t	\N	f	f
1643	PROJECT	Project	Sturrup Antiques Management	247755	2022-09-20 14:09:09.280904+05:30	2022-09-20 14:09:09.280934+05:30	1	t	\N	f	f
1644	PROJECT	Project	Summerton Hospital Services	247756	2022-09-20 14:09:09.280995+05:30	2022-09-20 14:09:09.281024+05:30	1	t	\N	f	f
1645	PROJECT	Project	Summons Apartments Company	247757	2022-09-20 14:09:09.281085+05:30	2022-09-20 14:09:09.281114+05:30	1	t	\N	f	f
1646	PROJECT	Project	Sumter Apartments Systems	247758	2022-09-20 14:09:09.281174+05:30	2022-09-20 14:09:09.281203+05:30	1	t	\N	f	f
1647	PROJECT	Project	Sunnybrook Hospital	247759	2022-09-20 14:09:09.281264+05:30	2022-09-20 14:09:09.281293+05:30	1	t	\N	f	f
1648	PROJECT	Project	Superior Car care Inc.	247760	2022-09-20 14:09:09.281353+05:30	2022-09-20 14:09:09.281464+05:30	1	t	\N	f	f
1649	PROJECT	Project	Support T&M	247761	2022-09-20 14:09:09.281526+05:30	2022-09-20 14:09:09.281556+05:30	1	t	\N	f	f
1650	PROJECT	Project	Sur Windows Services	247762	2022-09-20 14:09:09.281616+05:30	2022-09-20 14:09:09.281645+05:30	1	t	\N	f	f
1651	PROJECT	Project	Svancara Antiques Holding Corp.	247763	2022-09-20 14:09:09.281706+05:30	2022-09-20 14:09:09.281735+05:30	1	t	\N	f	f
1652	PROJECT	Project	Swanger Spirits	247764	2022-09-20 14:09:09.281795+05:30	2022-09-20 14:09:09.281825+05:30	1	t	\N	f	f
1653	PROJECT	Project	Sweeton and Ketron Liquors Group	247765	2022-09-20 14:09:09.281885+05:30	2022-09-20 14:09:09.281914+05:30	1	t	\N	f	f
1654	PROJECT	Project	Swiech Telecom Networking	247766	2022-09-20 14:09:09.281974+05:30	2022-09-20 14:09:09.282003+05:30	1	t	\N	f	f
1655	PROJECT	Project	Swinea Antiques Holding Corp.	247767	2022-09-20 14:09:09.282063+05:30	2022-09-20 14:09:09.282093+05:30	1	t	\N	f	f
1656	PROJECT	Project	Symore Construction Dynamics	247768	2022-09-20 14:09:09.282153+05:30	2022-09-20 14:09:09.282182+05:30	1	t	\N	f	f
1657	PROJECT	Project	Szewczyk Apartments Holding Corp.	247769	2022-09-20 14:09:09.282242+05:30	2022-09-20 14:09:09.282271+05:30	1	t	\N	f	f
1658	PROJECT	Project	T-M Manufacturing Corp.	247770	2022-09-20 14:09:09.282331+05:30	2022-09-20 14:09:09.282445+05:30	1	t	\N	f	f
1659	PROJECT	Project	TAB Ltd	247771	2022-09-20 14:09:09.282508+05:30	2022-09-20 14:09:09.282538+05:30	1	t	\N	f	f
1660	PROJECT	Project	TES Inc	247772	2022-09-20 14:09:09.282599+05:30	2022-09-20 14:09:09.282628+05:30	1	t	\N	f	f
1662	PROJECT	Project	TST Solutions Inc	247774	2022-09-20 14:09:09.282778+05:30	2022-09-20 14:09:09.282807+05:30	1	t	\N	f	f
1663	PROJECT	Project	TTS inc	247775	2022-09-20 14:09:09.282867+05:30	2022-09-20 14:09:09.282897+05:30	1	t	\N	f	f
1664	PROJECT	Project	TWC Financial	247776	2022-09-20 14:09:09.282956+05:30	2022-09-20 14:09:09.282985+05:30	1	t	\N	f	f
1665	PROJECT	Project	Taback Construction Leasing	247777	2022-09-20 14:09:09.283046+05:30	2022-09-20 14:09:09.283075+05:30	1	t	\N	f	f
1666	PROJECT	Project	Talboti and Pauli Title Agency	247778	2022-09-20 14:09:09.283136+05:30	2022-09-20 14:09:09.283165+05:30	1	t	\N	f	f
1667	PROJECT	Project	Tam Liquors	247779	2022-09-20 14:09:09.283225+05:30	2022-09-20 14:09:09.283254+05:30	1	t	\N	f	f
1668	PROJECT	Project	Tamara Gibson	247780	2022-09-20 14:09:09.283314+05:30	2022-09-20 14:09:09.283344+05:30	1	t	\N	f	f
1669	PROJECT	Project	Tanya Guerrero	247781	2022-09-20 14:09:09.283488+05:30	2022-09-20 14:09:09.283518+05:30	1	t	\N	f	f
1670	PROJECT	Project	Tarangelo and Mccrea Apartments Holding Corp.	247782	2022-09-20 14:09:09.28358+05:30	2022-09-20 14:09:09.283609+05:30	1	t	\N	f	f
1671	PROJECT	Project	Tarbutton Software Management	247783	2022-09-20 14:09:09.28367+05:30	2022-09-20 14:09:09.283699+05:30	1	t	\N	f	f
1672	PROJECT	Project	TargetVision	247784	2022-09-20 14:09:09.283758+05:30	2022-09-20 14:09:09.283792+05:30	1	t	\N	f	f
1673	PROJECT	Project	Taverna Liquors Networking	247785	2022-09-20 14:09:09.283854+05:30	2022-09-20 14:09:09.283883+05:30	1	t	\N	f	f
1674	PROJECT	Project	Team Industrial	247786	2022-09-20 14:09:09.283944+05:30	2022-09-20 14:09:09.283974+05:30	1	t	\N	f	f
1675	PROJECT	Project	Tebo Builders Management	247787	2022-09-20 14:09:09.284035+05:30	2022-09-20 14:09:09.284064+05:30	1	t	\N	f	f
1676	PROJECT	Project	Technology Consultants	247788	2022-09-20 14:09:09.284124+05:30	2022-09-20 14:09:09.284153+05:30	1	t	\N	f	f
1677	PROJECT	Project	Teddy Leasing Manufacturing	247789	2022-09-20 14:09:09.284213+05:30	2022-09-20 14:09:09.284242+05:30	1	t	\N	f	f
1678	PROJECT	Project	Tenen Markets Dynamics	247790	2022-09-20 14:09:09.284302+05:30	2022-09-20 14:09:09.284331+05:30	1	t	\N	f	f
1679	PROJECT	Project	Territory JMP 2	247791	2022-09-20 14:09:09.284475+05:30	2022-09-20 14:09:09.284505+05:30	1	t	\N	f	f
1680	PROJECT	Project	Territory JMP 3	247792	2022-09-20 14:09:09.284566+05:30	2022-09-20 14:09:09.284596+05:30	1	t	\N	f	f
1681	PROJECT	Project	Territory JMP 4	247793	2022-09-20 14:09:09.284657+05:30	2022-09-20 14:09:09.284686+05:30	1	t	\N	f	f
1682	PROJECT	Project	Tessa Darby	247794	2022-09-20 14:09:09.284746+05:30	2022-09-20 14:09:09.284775+05:30	1	t	\N	f	f
1683	PROJECT	Project	Test 2	247795	2022-09-20 14:09:09.284836+05:30	2022-09-20 14:09:09.284865+05:30	1	t	\N	f	f
1684	PROJECT	Project	Test 3	247796	2022-09-20 14:09:09.296187+05:30	2022-09-20 14:09:09.296409+05:30	1	t	\N	f	f
1685	PROJECT	Project	Test Test	247797	2022-09-20 14:09:09.296609+05:30	2022-09-20 14:09:09.29664+05:30	1	t	\N	f	f
1687	PROJECT	Project	Teton Winter Sports	247799	2022-09-20 14:09:09.297157+05:30	2022-09-20 14:09:09.297187+05:30	1	t	\N	f	f
1688	PROJECT	Project	The Coffee Corner	247800	2022-09-20 14:09:09.297636+05:30	2022-09-20 14:09:09.297667+05:30	1	t	\N	f	f
1689	PROJECT	Project	The Liquor Barn	247801	2022-09-20 14:09:09.297861+05:30	2022-09-20 14:09:09.297891+05:30	1	t	\N	f	f
1690	PROJECT	Project	The Validation Group	247802	2022-09-20 14:09:09.29808+05:30	2022-09-20 14:09:09.298352+05:30	1	t	\N	f	f
1691	PROJECT	Project	Thermo Electron Corporation	247803	2022-09-20 14:09:09.298422+05:30	2022-09-20 14:09:09.298718+05:30	1	t	\N	f	f
1692	PROJECT	Project	Therrell Publishing Networking	247804	2022-09-20 14:09:09.298913+05:30	2022-09-20 14:09:09.298943+05:30	1	t	\N	f	f
1693	PROJECT	Project	Thomison Windows Networking	247805	2022-09-20 14:09:09.299135+05:30	2022-09-20 14:09:09.299247+05:30	1	t	\N	f	f
1694	PROJECT	Project	Thongchanh Telecom Rentals	247806	2022-09-20 14:09:09.299378+05:30	2022-09-20 14:09:09.299538+05:30	1	t	\N	f	f
1695	PROJECT	Project	Thorne & Assoc	247807	2022-09-20 14:09:09.299725+05:30	2022-09-20 14:09:09.299756+05:30	1	t	\N	f	f
1697	PROJECT	Project	Timinsky Lumber Dynamics	247809	2022-09-20 14:09:09.300167+05:30	2022-09-20 14:09:09.300303+05:30	1	t	\N	f	f
1698	PROJECT	Project	Timmy Brown	247810	2022-09-20 14:09:09.300433+05:30	2022-09-20 14:09:09.300592+05:30	1	t	\N	f	f
1699	PROJECT	Project	Titam Business Services	247811	2022-09-20 14:09:09.300829+05:30	2022-09-20 14:09:09.300859+05:30	1	t	\N	f	f
1700	PROJECT	Project	Tom Calhoun	247812	2022-09-20 14:09:09.301645+05:30	2022-09-20 14:09:09.30171+05:30	1	t	\N	f	f
1701	PROJECT	Project	Tom Kratz	247813	2022-09-20 14:09:09.301806+05:30	2022-09-20 14:09:09.302179+05:30	1	t	\N	f	f
1702	PROJECT	Project	Tom MacGillivray	247814	2022-09-20 14:09:09.30244+05:30	2022-09-20 14:09:09.3026+05:30	1	t	\N	f	f
1703	PROJECT	Project	Tomlinson	247815	2022-09-20 14:09:09.302812+05:30	2022-09-20 14:09:09.302839+05:30	1	t	\N	f	f
1704	PROJECT	Project	Tony Matsuda	247816	2022-09-20 14:09:09.303108+05:30	2022-09-20 14:09:09.303153+05:30	1	t	\N	f	f
1705	PROJECT	Project	Top Drawer Creative	247817	2022-09-20 14:09:09.303446+05:30	2022-09-20 14:09:09.30348+05:30	1	t	\N	f	f
1706	PROJECT	Project	Touchard Liquors Holding Corp.	247818	2022-09-20 14:09:09.305886+05:30	2022-09-20 14:09:09.30628+05:30	1	t	\N	f	f
1707	PROJECT	Project	Tower AV and Telephone Install	247819	2022-09-20 14:09:09.306822+05:30	2022-09-20 14:09:09.306931+05:30	1	t	\N	f	f
1708	PROJECT	Project	Tower PL-01	247820	2022-09-20 14:09:09.307197+05:30	2022-09-20 14:09:09.307238+05:30	1	t	\N	f	f
1709	PROJECT	Project	Towsend Software Co.	247821	2022-09-20 14:09:09.307892+05:30	2022-09-20 14:09:09.307947+05:30	1	t	\N	f	f
1710	PROJECT	Project	Tracy Attorneys Management	247822	2022-09-20 14:09:09.308236+05:30	2022-09-20 14:09:09.308558+05:30	1	t	\N	f	f
1711	PROJECT	Project	Travis Gilbert	247823	2022-09-20 14:09:09.3087+05:30	2022-09-20 14:09:09.308959+05:30	1	t	\N	f	f
1712	PROJECT	Project	Trebor Allen Candy	247824	2022-09-20 14:09:09.310193+05:30	2022-09-20 14:09:09.310531+05:30	1	t	\N	f	f
1713	PROJECT	Project	Tredwell Lumber Holding Corp.	247825	2022-09-20 14:09:09.310733+05:30	2022-09-20 14:09:09.310802+05:30	1	t	\N	f	f
1714	PROJECT	Project	Trent Barry	247826	2022-09-20 14:09:09.310981+05:30	2022-09-20 14:09:09.311066+05:30	1	t	\N	f	f
1715	PROJECT	Project	Trenton Upwood Ltd	247827	2022-09-20 14:09:09.3118+05:30	2022-09-20 14:09:09.311859+05:30	1	t	\N	f	f
1716	PROJECT	Project	Tucson Apartments and Associates	247828	2022-09-20 14:09:09.311964+05:30	2022-09-20 14:09:09.312007+05:30	1	t	\N	f	f
1717	PROJECT	Project	Turso Catering Agency	247829	2022-09-20 14:09:09.312109+05:30	2022-09-20 14:09:09.312196+05:30	1	t	\N	f	f
1718	PROJECT	Project	Tuy and Sinha Construction Manufacturing	247830	2022-09-20 14:09:09.312375+05:30	2022-09-20 14:09:09.312401+05:30	1	t	\N	f	f
1719	PROJECT	Project	Twigg Attorneys Company	247831	2022-09-20 14:09:09.312461+05:30	2022-09-20 14:09:09.312482+05:30	1	t	\N	f	f
1720	PROJECT	Project	Twine Title Group	247832	2022-09-20 14:09:09.312541+05:30	2022-09-20 14:09:09.312562+05:30	1	t	\N	f	f
1721	PROJECT	Project	UK Customer	247833	2022-09-20 14:09:09.312634+05:30	2022-09-20 14:09:09.31267+05:30	1	t	\N	f	f
1722	PROJECT	Project	Udoh Publishing Manufacturing	247834	2022-09-20 14:09:09.312727+05:30	2022-09-20 14:09:09.312749+05:30	1	t	\N	f	f
1723	PROJECT	Project	Uimari Antiques Agency	247835	2022-09-20 14:09:09.312855+05:30	2022-09-20 14:09:09.3129+05:30	1	t	\N	f	f
1724	PROJECT	Project	Umali Publishing Distributors	247836	2022-09-20 14:09:09.313028+05:30	2022-09-20 14:09:09.313068+05:30	1	t	\N	f	f
1725	PROJECT	Project	Umbrell Liquors Rentals	247837	2022-09-20 14:09:09.313145+05:30	2022-09-20 14:09:09.313162+05:30	1	t	\N	f	f
1726	PROJECT	Project	Umeh Telecom Management	247838	2022-09-20 14:09:09.313339+05:30	2022-09-20 14:09:09.313377+05:30	1	t	\N	f	f
1727	PROJECT	Project	Underdown Metal Fabricators and Associates	247839	2022-09-20 14:09:09.313463+05:30	2022-09-20 14:09:09.313494+05:30	1	t	\N	f	f
1728	PROJECT	Project	Underwood New York	247840	2022-09-20 14:09:09.313556+05:30	2022-09-20 14:09:09.313584+05:30	1	t	\N	f	f
1729	PROJECT	Project	Underwood Systems	247841	2022-09-20 14:09:09.313646+05:30	2022-09-20 14:09:09.313658+05:30	1	t	\N	f	f
1730	PROJECT	Project	UniExchange	247842	2022-09-20 14:09:09.31371+05:30	2022-09-20 14:09:09.313732+05:30	1	t	\N	f	f
1731	PROJECT	Project	Unnold Hospital Co.	247843	2022-09-20 14:09:09.313812+05:30	2022-09-20 14:09:09.313854+05:30	1	t	\N	f	f
1732	PROJECT	Project	Upper 49th	247844	2022-09-20 14:09:09.313918+05:30	2022-09-20 14:09:09.313931+05:30	1	t	\N	f	f
1733	PROJECT	Project	Ursery Publishing Group	247845	2022-09-20 14:09:09.313988+05:30	2022-09-20 14:09:09.31401+05:30	1	t	\N	f	f
1734	PROJECT	Project	Urwin Leasing Group	247846	2022-09-20 14:09:09.322777+05:30	2022-09-20 14:09:09.322831+05:30	1	t	\N	f	f
1735	PROJECT	Project	Valley Center Catering Leasing	247847	2022-09-20 14:09:09.322976+05:30	2022-09-20 14:09:09.323029+05:30	1	t	\N	f	f
1736	PROJECT	Project	Vanaken Apartments Holding Corp.	247848	2022-09-20 14:09:09.323123+05:30	2022-09-20 14:09:09.323174+05:30	1	t	\N	f	f
1737	PROJECT	Project	Vanasse Antiques Networking	247849	2022-09-20 14:09:09.323415+05:30	2022-09-20 14:09:09.323459+05:30	1	t	\N	f	f
1738	PROJECT	Project	Vance Construction and Associates	247850	2022-09-20 14:09:09.32353+05:30	2022-09-20 14:09:09.323559+05:30	1	t	\N	f	f
1739	PROJECT	Project	Vanwyngaarden Title Systems	247851	2022-09-20 14:09:09.32362+05:30	2022-09-20 14:09:09.323659+05:30	1	t	\N	f	f
1740	PROJECT	Project	Vegas Tours	247852	2022-09-20 14:09:09.323731+05:30	2022-09-20 14:09:09.323743+05:30	1	t	\N	f	f
1741	PROJECT	Project	Vellekamp Title Distributors	247853	2022-09-20 14:09:09.323794+05:30	2022-09-20 14:09:09.323823+05:30	1	t	\N	f	f
1742	PROJECT	Project	Veradale Telecom Manufacturing	247854	2022-09-20 14:09:09.323884+05:30	2022-09-20 14:09:09.323913+05:30	1	t	\N	f	f
1743	PROJECT	Project	Vermont Attorneys Company	247855	2022-09-20 14:09:09.323973+05:30	2022-09-20 14:09:09.324002+05:30	1	t	\N	f	f
1744	PROJECT	Project	Verrelli Construction -	247856	2022-09-20 14:09:09.324067+05:30	2022-09-20 14:09:09.324096+05:30	1	t	\N	f	f
1745	PROJECT	Project	Vertex	247857	2022-09-20 14:09:09.324156+05:30	2022-09-20 14:09:09.324194+05:30	1	t	\N	f	f
1746	PROJECT	Project	Vessel Painting Holding Corp.	247858	2022-09-20 14:09:09.324251+05:30	2022-09-20 14:09:09.324279+05:30	1	t	\N	f	f
1747	PROJECT	Project	Villanova Lumber Systems	247859	2022-09-20 14:09:09.324601+05:30	2022-09-20 14:09:09.324631+05:30	1	t	\N	f	f
1748	PROJECT	Project	Virginia Beach Hospital Manufacturing	247860	2022-09-20 14:09:09.324689+05:30	2022-09-20 14:09:09.324716+05:30	1	t	\N	f	f
1749	PROJECT	Project	Vista Lumber Agency	247861	2022-09-20 14:09:09.324773+05:30	2022-09-20 14:09:09.3248+05:30	1	t	\N	f	f
1750	PROJECT	Project	Vivas Electric Sales	247862	2022-09-20 14:09:09.324856+05:30	2022-09-20 14:09:09.324883+05:30	1	t	\N	f	f
1751	PROJECT	Project	Vodaphone	247863	2022-09-20 14:09:09.324941+05:30	2022-09-20 14:09:09.324968+05:30	1	t	\N	f	f
1752	PROJECT	Project	Volden Publishing Systems	247864	2022-09-20 14:09:09.325133+05:30	2022-09-20 14:09:09.325216+05:30	1	t	\N	f	f
1753	PROJECT	Project	Volmar Liquors and Associates	247865	2022-09-20 14:09:09.325446+05:30	2022-09-20 14:09:09.325488+05:30	1	t	\N	f	f
1754	PROJECT	Project	Volmink Builders Inc.	247866	2022-09-20 14:09:09.325569+05:30	2022-09-20 14:09:09.325601+05:30	1	t	\N	f	f
1755	PROJECT	Project	Wagenheim Painting and Associates	247867	2022-09-20 14:09:09.326388+05:30	2022-09-20 14:09:09.326452+05:30	1	t	\N	f	f
1756	PROJECT	Project	Wahlers Lumber Management	247868	2022-09-20 14:09:09.326534+05:30	2022-09-20 14:09:09.326565+05:30	1	t	\N	f	f
1757	PROJECT	Project	Wallace Printers	247869	2022-09-20 14:09:09.326642+05:30	2022-09-20 14:09:09.326684+05:30	1	t	\N	f	f
1758	PROJECT	Project	Walter Martin	247870	2022-09-20 14:09:09.32677+05:30	2022-09-20 14:09:09.326803+05:30	1	t	\N	f	f
1759	PROJECT	Project	Walters Production Company	247871	2022-09-20 14:09:09.326867+05:30	2022-09-20 14:09:09.326897+05:30	1	t	\N	f	f
1760	PROJECT	Project	Wapp Hardware Sales	247872	2022-09-20 14:09:09.326958+05:30	2022-09-20 14:09:09.326988+05:30	1	t	\N	f	f
1761	PROJECT	Project	Warnberg Automotive and Associates	247873	2022-09-20 14:09:09.327049+05:30	2022-09-20 14:09:09.327078+05:30	1	t	\N	f	f
1762	PROJECT	Project	Warwick Lumber	247874	2022-09-20 14:09:09.327139+05:30	2022-09-20 14:09:09.327168+05:30	1	t	\N	f	f
1763	PROJECT	Project	Wasager Wine Sales	247875	2022-09-20 14:09:09.327229+05:30	2022-09-20 14:09:09.327258+05:30	1	t	\N	f	f
1764	PROJECT	Project	Wassenaar Construction Services	247876	2022-09-20 14:09:09.327318+05:30	2022-09-20 14:09:09.327347+05:30	1	t	\N	f	f
1765	PROJECT	Project	Watertown Hicks	247877	2022-09-20 14:09:09.32741+05:30	2022-09-20 14:09:09.327586+05:30	1	t	\N	f	f
1766	PROJECT	Project	Weare and Norvell Painting Co.	247878	2022-09-20 14:09:09.327654+05:30	2022-09-20 14:09:09.327683+05:30	1	t	\N	f	f
1767	PROJECT	Project	Webmaster Gproxy	247879	2022-09-20 14:09:09.327744+05:30	2022-09-20 14:09:09.327773+05:30	1	t	\N	f	f
1768	PROJECT	Project	Webster Electric	247880	2022-09-20 14:09:09.327862+05:30	2022-09-20 14:09:09.327891+05:30	1	t	\N	f	f
1769	PROJECT	Project	Wedge Automotive Fabricators	247881	2022-09-20 14:09:09.327951+05:30	2022-09-20 14:09:09.328001+05:30	1	t	\N	f	f
1770	PROJECT	Project	Wenatchee Builders Fabricators	247882	2022-09-20 14:09:09.328174+05:30	2022-09-20 14:09:09.328226+05:30	1	t	\N	f	f
1771	PROJECT	Project	Wence Antiques Rentals	247883	2022-09-20 14:09:09.328529+05:30	2022-09-20 14:09:09.328733+05:30	1	t	\N	f	f
1772	PROJECT	Project	Wendler Markets Leasing	247884	2022-09-20 14:09:09.328852+05:30	2022-09-20 14:09:09.328902+05:30	1	t	\N	f	f
1773	PROJECT	Project	West Covina Builders Distributors	247885	2022-09-20 14:09:09.329014+05:30	2022-09-20 14:09:09.329047+05:30	1	t	\N	f	f
1774	PROJECT	Project	West Palm Beach Painting Manufacturing	247886	2022-09-20 14:09:09.329128+05:30	2022-09-20 14:09:09.329158+05:30	1	t	\N	f	f
1775	PROJECT	Project	Westminster Lumber Sales	247887	2022-09-20 14:09:09.329224+05:30	2022-09-20 14:09:09.329254+05:30	1	t	\N	f	f
1776	PROJECT	Project	Westminster Lumber Sales 1	247888	2022-09-20 14:09:09.32932+05:30	2022-09-20 14:09:09.329351+05:30	1	t	\N	f	f
1777	PROJECT	Project	Wethersfield Hardware Dynamics	247889	2022-09-20 14:09:09.329535+05:30	2022-09-20 14:09:09.329566+05:30	1	t	\N	f	f
1778	PROJECT	Project	Wettlaufer Construction Systems	247890	2022-09-20 14:09:09.329632+05:30	2022-09-20 14:09:09.329667+05:30	1	t	\N	f	f
1779	PROJECT	Project	Wever Apartments -	247891	2022-09-20 14:09:09.329732+05:30	2022-09-20 14:09:09.329762+05:30	1	t	\N	f	f
1780	PROJECT	Project	Whetzell and Maymon Antiques Sales	247892	2022-09-20 14:09:09.329835+05:30	2022-09-20 14:09:09.329862+05:30	1	t	\N	f	f
1781	PROJECT	Project	Whittier Hardware -	247893	2022-09-20 14:09:09.329921+05:30	2022-09-20 14:09:09.329948+05:30	1	t	\N	f	f
1782	PROJECT	Project	Whole Oats Markets	247894	2022-09-20 14:09:09.330016+05:30	2022-09-20 14:09:09.330088+05:30	1	t	\N	f	f
1783	PROJECT	Project	Wickenhauser Hardware Management	247895	2022-09-20 14:09:09.330189+05:30	2022-09-20 14:09:09.330217+05:30	1	t	\N	f	f
1784	PROJECT	Project	Wicklund Leasing Corporation	247896	2022-09-20 14:09:09.336943+05:30	2022-09-20 14:09:09.336995+05:30	1	t	\N	f	f
1785	PROJECT	Project	Wiesel Construction Dynamics	247897	2022-09-20 14:09:09.337063+05:30	2022-09-20 14:09:09.337092+05:30	1	t	\N	f	f
1786	PROJECT	Project	Wiggles Inc.	247898	2022-09-20 14:09:09.337152+05:30	2022-09-20 14:09:09.33718+05:30	1	t	\N	f	f
1787	PROJECT	Project	Wilkey Markets Group	247899	2022-09-20 14:09:09.337252+05:30	2022-09-20 14:09:09.337282+05:30	1	t	\N	f	f
1788	PROJECT	Project	Will's Leather Co.	247900	2022-09-20 14:09:09.337344+05:30	2022-09-20 14:09:09.337559+05:30	1	t	\N	f	f
1789	PROJECT	Project	Williams Electronics and Communications	247901	2022-09-20 14:09:09.337638+05:30	2022-09-20 14:09:09.337668+05:30	1	t	\N	f	f
1790	PROJECT	Project	Williams Wireless World	247902	2022-09-20 14:09:09.337732+05:30	2022-09-20 14:09:09.337761+05:30	1	t	\N	f	f
1791	PROJECT	Project	Wilner Liquors	247903	2022-09-20 14:09:09.337822+05:30	2022-09-20 14:09:09.337852+05:30	1	t	\N	f	f
1792	PROJECT	Project	Wilson Kaplan	247904	2022-09-20 14:09:09.337912+05:30	2022-09-20 14:09:09.337941+05:30	1	t	\N	f	f
1793	PROJECT	Project	Windisch Title Corporation	247905	2022-09-20 14:09:09.338003+05:30	2022-09-20 14:09:09.338032+05:30	1	t	\N	f	f
1794	PROJECT	Project	Witten Antiques Services	247906	2022-09-20 14:09:09.338092+05:30	2022-09-20 14:09:09.338121+05:30	1	t	\N	f	f
1795	PROJECT	Project	Wolfenden Markets Holding Corp.	247907	2022-09-20 14:09:09.338189+05:30	2022-09-20 14:09:09.338216+05:30	1	t	\N	f	f
1796	PROJECT	Project	Wollan Software Rentals	247908	2022-09-20 14:09:09.338273+05:30	2022-09-20 14:09:09.338301+05:30	1	t	\N	f	f
1797	PROJECT	Project	Wood Wonders Funiture	247909	2022-09-20 14:09:09.338462+05:30	2022-09-20 14:09:09.338494+05:30	1	t	\N	f	f
1798	PROJECT	Project	Wood-Mizer	247910	2022-09-20 14:09:09.338555+05:30	2022-09-20 14:09:09.33858+05:30	1	t	\N	f	f
1799	PROJECT	Project	Woods Publishing Co.	247911	2022-09-20 14:09:09.338629+05:30	2022-09-20 14:09:09.33865+05:30	1	t	\N	f	f
1800	PROJECT	Project	Woon Hardware Networking	247912	2022-09-20 14:09:09.338718+05:30	2022-09-20 14:09:09.338745+05:30	1	t	\N	f	f
1801	PROJECT	Project	Wraight Software and Associates	247913	2022-09-20 14:09:09.338803+05:30	2022-09-20 14:09:09.338829+05:30	1	t	\N	f	f
1802	PROJECT	Project	X Eye Corp	247914	2022-09-20 14:09:09.338897+05:30	2022-09-20 14:09:09.338926+05:30	1	t	\N	f	f
1803	PROJECT	Project	Y-Tec Manufacturing	247915	2022-09-20 14:09:09.338987+05:30	2022-09-20 14:09:09.339016+05:30	1	t	\N	f	f
1804	PROJECT	Project	Yahl Markets Incorporated	247916	2022-09-20 14:09:09.339072+05:30	2022-09-20 14:09:09.339092+05:30	1	t	\N	f	f
1805	PROJECT	Project	Yanity Apartments and Associates	247917	2022-09-20 14:09:09.339153+05:30	2022-09-20 14:09:09.339272+05:30	1	t	\N	f	f
1806	PROJECT	Project	Yarnell Catering Holding Corp.	247918	2022-09-20 14:09:09.339335+05:30	2022-09-20 14:09:09.339364+05:30	1	t	\N	f	f
1807	PROJECT	Project	Yockey Markets Inc.	247919	2022-09-20 14:09:09.339424+05:30	2022-09-20 14:09:09.339446+05:30	1	t	\N	f	f
1808	PROJECT	Project	Yong Yi	247920	2022-09-20 14:09:09.339505+05:30	2022-09-20 14:09:09.339528+05:30	1	t	\N	f	f
1809	PROJECT	Project	Yucca Valley Camping	247921	2022-09-20 14:09:09.339577+05:30	2022-09-20 14:09:09.339598+05:30	1	t	\N	f	f
1810	PROJECT	Project	Yucca Valley Title Agency	247922	2022-09-20 14:09:09.339659+05:30	2022-09-20 14:09:09.339688+05:30	1	t	\N	f	f
1811	PROJECT	Project	Zearfoss Windows Group	247923	2022-09-20 14:09:09.339747+05:30	2022-09-20 14:09:09.339768+05:30	1	t	\N	f	f
1812	PROJECT	Project	Zechiel _ Management	247924	2022-09-20 14:09:09.339822+05:30	2022-09-20 14:09:09.339937+05:30	1	t	\N	f	f
1813	PROJECT	Project	Zombro Telecom Leasing	247925	2022-09-20 14:09:09.33999+05:30	2022-09-20 14:09:09.340029+05:30	1	t	\N	f	f
1814	PROJECT	Project	Zucca Electric Agency	247926	2022-09-20 14:09:09.340086+05:30	2022-09-20 14:09:09.340113+05:30	1	t	\N	f	f
1815	PROJECT	Project	Zucconi Telecom Sales	247927	2022-09-20 14:09:09.340169+05:30	2022-09-20 14:09:09.340197+05:30	1	t	\N	f	f
1816	PROJECT	Project	Zurasky Markets Dynamics	247928	2022-09-20 14:09:09.340253+05:30	2022-09-20 14:09:09.34029+05:30	1	t	\N	f	f
1817	PROJECT	Project	eNable Corp	247929	2022-09-20 14:09:09.340464+05:30	2022-09-20 14:09:09.340495+05:30	1	t	\N	f	f
1818	PROJECT	Project	qa 54	247930	2022-09-20 14:09:09.340555+05:30	2022-09-20 14:09:09.340584+05:30	1	t	\N	f	f
1820	PROJECT	Project	tester1	247932	2022-09-20 14:09:09.340732+05:30	2022-09-20 14:09:09.340761+05:30	1	t	\N	f	f
1821	PROJECT	Project	ugkas	247933	2022-09-20 14:09:09.340821+05:30	2022-09-20 14:09:09.340849+05:30	1	t	\N	f	f
1822	PROJECT	Project	Company 1618550408	249071	2022-09-20 14:09:09.340909+05:30	2022-09-20 14:09:09.340938+05:30	1	t	\N	f	f
1823	PROJECT	Project	Company 1618566776	250488	2022-09-20 14:09:09.340998+05:30	2022-09-20 14:09:09.341027+05:30	1	t	\N	f	f
1824	PROJECT	Project	Project Red	251304	2022-09-20 14:09:09.341087+05:30	2022-09-20 14:09:09.341115+05:30	1	t	\N	f	f
1825	PROJECT	Project	Sravan Prod Test Prod	254098	2022-09-20 14:09:09.341175+05:30	2022-09-20 14:09:09.341204+05:30	1	t	\N	f	f
1826	PROJECT	Project	Ashwinn	254145	2022-09-20 14:09:09.341263+05:30	2022-09-20 14:09:09.341292+05:30	1	t	\N	f	f
1827	PROJECT	Project	Customer Sravan	274656	2022-09-20 14:09:09.341352+05:30	2022-09-20 14:09:09.341385+05:30	1	t	\N	f	f
1828	PROJECT	Project	Fyle Integrations	274657	2022-09-20 14:09:09.341501+05:30	2022-09-20 14:09:09.341531+05:30	1	t	\N	f	f
1829	PROJECT	Project	Fyle Nilesh	274658	2022-09-20 14:09:09.341592+05:30	2022-09-20 14:09:09.341621+05:30	1	t	\N	f	f
1830	PROJECT	Project	Nilesh	274659	2022-09-20 14:09:09.34178+05:30	2022-09-20 14:09:09.341844+05:30	1	t	\N	f	f
1831	PROJECT	Project	Brosey Antiques	278175	2022-09-20 14:09:09.342037+05:30	2022-09-20 14:09:09.342091+05:30	1	t	\N	f	f
1832	PROJECT	Project	Sample Test	278284	2022-09-20 14:09:09.342191+05:30	2022-09-20 14:09:09.342226+05:30	1	t	\N	f	f
1833	PROJECT	Project	Adwin Ko	278532	2022-09-20 14:09:09.342312+05:30	2022-09-20 14:09:09.342613+05:30	1	t	\N	f	f
1834	PROJECT	Project	Alex Blakey	278533	2022-09-20 14:09:09.539047+05:30	2022-09-20 14:09:09.53908+05:30	1	t	\N	f	f
1835	PROJECT	Project	Benjamin Yeung	278534	2022-09-20 14:09:09.539136+05:30	2022-09-20 14:09:09.539167+05:30	1	t	\N	f	f
1836	PROJECT	Project	Cathy Quon	278535	2022-09-20 14:09:09.539361+05:30	2022-09-20 14:09:09.539385+05:30	1	t	\N	f	f
1837	PROJECT	Project	Chadha's Consultants	278536	2022-09-20 14:09:09.539438+05:30	2022-09-20 14:09:09.539467+05:30	1	t	\N	f	f
1838	PROJECT	Project	Charlie Whitehead	278537	2022-09-20 14:09:09.539528+05:30	2022-09-20 14:09:09.53955+05:30	1	t	\N	f	f
1839	PROJECT	Project	Cheng-Cheng Lok	278538	2022-09-20 14:09:09.539602+05:30	2022-09-20 14:09:09.539631+05:30	1	t	\N	f	f
1840	PROJECT	Project	Clement's Cleaners	278539	2022-09-20 14:09:09.539691+05:30	2022-09-20 14:09:09.53972+05:30	1	t	\N	f	f
1841	PROJECT	Project	Ecker Designs	278540	2022-09-20 14:09:09.53978+05:30	2022-09-20 14:09:09.539802+05:30	1	t	\N	f	f
1842	PROJECT	Project	Froilan Rosqueta	278541	2022-09-20 14:09:09.539854+05:30	2022-09-20 14:09:09.539883+05:30	1	t	\N	f	f
1843	PROJECT	Project	Gorman Ho	278542	2022-09-20 14:09:09.539943+05:30	2022-09-20 14:09:09.539972+05:30	1	t	\N	f	f
1844	PROJECT	Project	Hazel Robinson	278543	2022-09-20 14:09:09.540032+05:30	2022-09-20 14:09:09.540054+05:30	1	t	\N	f	f
1845	PROJECT	Project	Himateja Madala	278544	2022-09-20 14:09:09.540105+05:30	2022-09-20 14:09:09.540134+05:30	1	t	\N	f	f
1846	PROJECT	Project	Jacint Tumacder	278545	2022-09-20 14:09:09.540309+05:30	2022-09-20 14:09:09.54034+05:30	1	t	\N	f	f
1847	PROJECT	Project	Jen Zaccarella	278546	2022-09-20 14:09:09.540392+05:30	2022-09-20 14:09:09.540413+05:30	1	t	\N	f	f
1848	PROJECT	Project	Jordan Burgess	278547	2022-09-20 14:09:09.540474+05:30	2022-09-20 14:09:09.540503+05:30	1	t	\N	f	f
1849	PROJECT	Project	Justine Outland	278548	2022-09-20 14:09:09.540555+05:30	2022-09-20 14:09:09.540574+05:30	1	t	\N	f	f
1850	PROJECT	Project	Kari Steblay	278549	2022-09-20 14:09:09.540622+05:30	2022-09-20 14:09:09.540643+05:30	1	t	\N	f	f
1851	PROJECT	Project	Karna Nisewaner	278550	2022-09-20 14:09:09.540687+05:30	2022-09-20 14:09:09.540708+05:30	1	t	\N	f	f
1852	PROJECT	Project	Kristy Abercrombie	278551	2022-09-20 14:09:09.540768+05:30	2022-09-20 14:09:09.540797+05:30	1	t	\N	f	f
1853	PROJECT	Project	Lew Plumbing	278552	2022-09-20 14:09:09.541607+05:30	2022-09-20 14:09:09.5417+05:30	1	t	\N	f	f
1854	PROJECT	Project	Moturu Tapasvi	278553	2022-09-20 14:09:09.541881+05:30	2022-09-20 14:09:09.541972+05:30	1	t	\N	f	f
1855	PROJECT	Project	Nadia Phillipchuk	278554	2022-09-20 14:09:09.542081+05:30	2022-09-20 14:09:09.542124+05:30	1	t	\N	f	f
1856	PROJECT	Project	Oxon Insurance Agency	278555	2022-09-20 14:09:09.542374+05:30	2022-09-20 14:09:09.542409+05:30	1	t	\N	f	f
1857	PROJECT	Project	Oxon Insurance Agency:Oxon -- Holiday Party	278556	2022-09-20 14:09:09.542538+05:30	2022-09-20 14:09:09.542641+05:30	1	t	\N	f	f
1858	PROJECT	Project	Oxon Insurance Agency:Oxon - Retreat	278557	2022-09-20 14:09:09.542773+05:30	2022-09-20 14:09:09.542819+05:30	1	t	\N	f	f
1859	PROJECT	Project	Rob deMontarnal	278558	2022-09-20 14:09:09.542932+05:30	2022-09-20 14:09:09.542981+05:30	1	t	\N	f	f
1871	PROJECT	Project	Attack on titans / Ackerman	290927	2022-09-20 14:09:09.547665+05:30	2022-09-20 14:09:09.547687+05:30	1	t	\N	f	f
1872	PROJECT	Project	MSD Project	292180	2022-09-20 14:09:09.548615+05:30	2022-09-20 14:09:09.548662+05:30	1	t	\N	f	f
1873	PROJECT	Project	Fast and Furious	292182	2022-09-20 14:09:09.548807+05:30	2022-09-20 14:09:09.548851+05:30	1	t	\N	f	f
688	PROJECT	Project	Fyle Engineering	243608	2022-09-20 14:09:06.869004+05:30	2022-09-20 14:09:06.86906+05:30	1	t	\N	t	f
1860	PROJECT	Project	Fixed Fee Project with Five Tasks	284355	2022-09-20 14:09:09.543086+05:30	2022-09-20 14:09:09.544981+05:30	1	t	\N	t	f
1861	PROJECT	Project	Fyle NetSuite Integration	284356	2022-09-20 14:09:09.545129+05:30	2022-09-20 14:09:09.545173+05:30	1	t	\N	t	f
1862	PROJECT	Project	Fyle Sage Intacct Integration	284357	2022-09-20 14:09:09.545518+05:30	2022-09-20 14:09:09.545565+05:30	1	t	\N	t	f
1863	PROJECT	Project	General Overhead	284358	2022-09-20 14:09:09.545645+05:30	2022-09-20 14:09:09.546619+05:30	1	t	\N	t	f
1864	PROJECT	Project	General Overhead-Current	284359	2022-09-20 14:09:09.546745+05:30	2022-09-20 14:09:09.546781+05:30	1	t	\N	t	f
1865	PROJECT	Project	Integrations	284360	2022-09-20 14:09:09.546879+05:30	2022-09-20 14:09:09.546914+05:30	1	t	\N	t	f
1866	PROJECT	Project	Mobile App Redesign	284361	2022-09-20 14:09:09.547005+05:30	2022-09-20 14:09:09.54705+05:30	1	t	\N	t	f
1867	PROJECT	Project	Platform APIs	284362	2022-09-20 14:09:09.547165+05:30	2022-09-20 14:09:09.547192+05:30	1	t	\N	t	f
1868	PROJECT	Project	Support Taxes	284363	2022-09-20 14:09:09.547342+05:30	2022-09-20 14:09:09.547362+05:30	1	t	\N	t	f
1869	PROJECT	Project	T&M Project with Five Tasks	284364	2022-09-20 14:09:09.547423+05:30	2022-09-20 14:09:09.547462+05:30	1	t	\N	t	f
1870	PROJECT	Project	labhvam	290031	2022-09-20 14:09:09.547574+05:30	2022-09-20 14:09:09.547604+05:30	1	t	\N	t	f
3218	PROJECT	Project	Branding Analysis	304665	2022-09-20 14:10:25.829933+05:30	2022-09-20 14:10:25.830111+05:30	1	t	\N	t	f
3219	PROJECT	Project	Branding Follow Up	304666	2022-09-20 14:10:25.832021+05:30	2022-09-20 14:10:25.832103+05:30	1	t	\N	t	f
3220	PROJECT	Project	Direct Mail Campaign	304667	2022-09-20 14:10:25.834913+05:30	2022-09-20 14:10:25.83498+05:30	1	t	\N	t	f
3221	PROJECT	Project	Ecommerce Campaign	304668	2022-09-20 14:10:25.835186+05:30	2022-09-20 14:10:25.835223+05:30	1	t	\N	t	f
\.


--
-- Data for Name: expense_fields; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.expense_fields (id, attribute_type, source_field_id, is_enabled, created_at, updated_at, workspace_id) FROM stdin;
\.


--
-- Data for Name: expense_group_settings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.expense_group_settings (id, reimbursable_expense_group_fields, corporate_credit_card_expense_group_fields, expense_state, reimbursable_export_date_type, created_at, updated_at, workspace_id, ccc_export_date_type, import_card_credits, ccc_expense_state) FROM stdin;
1	{employee_email,report_id,claim_number,fund_source}	{employee_email,report_id,expense_id,claim_number,fund_source}	PAYMENT_PROCESSING	current_date	2022-09-20 14:08:03.358472+05:30	2022-09-20 14:09:32.022875+05:30	1	spent_at	f	PAID
\.


--
-- Data for Name: expense_groups; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.expense_groups (id, description, created_at, updated_at, workspace_id, fund_source, exported_at, export_type) FROM stdin;
1	{"report_id": "rpEZGqVCyWxQ", "fund_source": "PERSONAL", "claim_number": "C/2022/09/R/21", "employee_email": "ashwin.t@fyle.in"}	2022-09-20 14:18:21.765399+05:30	2022-09-20 14:18:21.765445+05:30	1	PERSONAL	\N	\N
2	{"report_id": "rpSTYO8AfUVA", "expense_id": "txCqLqsEnAjf", "fund_source": "CCC", "claim_number": "C/2022/09/R/22", "employee_email": "ashwin.t@fyle.in"}	2022-09-20 14:21:27.651115+05:30	2022-09-20 14:21:27.651167+05:30	1	CCC	\N	\N
3	{"report_id": "rpBf5ibqUT6B", "expense_id": "txTHfEPWOEOp", "fund_source": "CCC", "claim_number": "C/2022/09/R/23", "employee_email": "ashwin.t@fyle.in"}	2022-09-20 14:26:50.147276+05:30	2022-09-20 14:26:50.147324+05:30	1	CCC	\N	\N
\.


--
-- Data for Name: expense_groups_expenses; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.expense_groups_expenses (id, expensegroup_id, expense_id) FROM stdin;
1	1	1
2	2	2
3	3	3
\.


--
-- Data for Name: expense_report_lineitems; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.expense_report_lineitems (id, expense_type_id, gl_account_number, project_id, location_id, department_id, memo, amount, created_at, updated_at, expense_report_id, expense_id, transaction_date, billable, customer_id, item_id, user_defined_dimensions, expense_payment_type, class_id, tax_amount, tax_code, cost_type_id, task_id) FROM stdin;
\.


--
-- Data for Name: expense_reports; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.expense_reports (id, employee_id, description, supdoc_id, created_at, updated_at, expense_group_id, memo, transaction_date, paid_on_sage_intacct, payment_synced, currency) FROM stdin;
\.


--
-- Data for Name: expenses; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.expenses (id, employee_email, category, sub_category, project, expense_id, expense_number, claim_number, amount, currency, foreign_amount, foreign_currency, settlement_id, reimbursable, state, vendor, cost_center, purpose, report_id, spent_at, approved_at, expense_created_at, expense_updated_at, created_at, updated_at, fund_source, custom_properties, verified_at, billable, paid_on_sage_intacct, org_id, tax_amount, tax_group_id, file_ids, payment_number) FROM stdin;
1	ashwin.t@fyle.in	Food	\N	Aaron Abbott	txR9dyrqr1Jn	E/2022/09/T/21	C/2022/09/R/21	21	USD	\N	\N	setqwcKcC9q1k	t	PAYMENT_PROCESSING	Ashwin	Marketing	\N	rpEZGqVCyWxQ	2022-09-20 22:30:00+05:30	2022-09-20 01:24:36.96+05:30	2022-09-20 01:24:15.870239+05:30	2022-09-20 01:25:58.641995+05:30	2022-09-20 14:18:21.737374+05:30	2022-09-20 14:18:21.737392+05:30	PERSONAL	{"Team": "", "Class": "", "Klass": "", "Location": "", "Team Copy": "", "Tax Groups": "", "Departments": "", "Team 2 Postman": "", "User Dimension": "", "Location Entity": "", "Operating System": "", "System Operating": "", "User Dimension Copy": "", "Custom Expense Field": null}	\N	\N	f	or79Cob97KSh	\N	\N	{}	P/2022/09/R/18
2	ashwin.t@fyle.in	Food	\N	Aaron Abbott	txCqLqsEnAjf	E/2022/09/T/22	C/2022/09/R/22	11	USD	\N	\N	setzhjuqQ6Pl5	f	PAYMENT_PROCESSING	Ashwin	Marketing	\N	rpSTYO8AfUVA	2022-09-20 22:30:00+05:30	2022-09-20 14:20:48.428+05:30	2022-09-20 14:20:27.570399+05:30	2022-09-20 14:21:13.891379+05:30	2022-09-20 14:21:27.566571+05:30	2022-09-20 14:21:27.566598+05:30	CCC	{"Team": "", "Class": "", "Klass": "", "Location": "", "Team Copy": "", "Tax Groups": "", "Departments": "", "Team 2 Postman": "", "User Dimension": "", "Location Entity": "", "Operating System": "", "System Operating": "", "User Dimension Copy": "", "Custom Expense Field": null}	\N	t	f	or79Cob97KSh	2.41	tggu76WXIdjY	{}	P/2022/09/R/19
3	ashwin.t@fyle.in	Taxi	\N	Aaron Abbott	txTHfEPWOEOp	E/2022/09/T/23	C/2022/09/R/23	22	USD	\N	\N	set0SnAq66Zbq	f	PAYMENT_PROCESSING	Ashwin	Marketing	\N	rpBf5ibqUT6B	2022-09-20 22:30:00+05:30	2022-09-20 14:26:09.337+05:30	2022-09-20 14:25:53.246893+05:30	2022-09-20 14:26:40.795304+05:30	2022-09-20 14:26:50.117313+05:30	2022-09-20 14:26:50.117349+05:30	CCC	{"Team": "", "Class": "", "Klass": "", "Location": "", "Team Copy": "", "Tax Groups": "", "Departments": "", "Team 2 Postman": "", "User Dimension": "", "Location Entity": "", "Operating System": "", "System Operating": "", "User Dimension Copy": "", "Custom Expense Field": null}	\N	\N	f	or79Cob97KSh	4.81	tggu76WXIdjY	{}	P/2022/09/R/20
\.


--
-- Data for Name: fyle_credentials; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.fyle_credentials (id, refresh_token, created_at, updated_at, workspace_id, cluster_domain) FROM stdin;
1	eyJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2NjM2NjMwNzIsImlzcyI6IkZ5bGVBcHAiLCJvcmdfdXNlcl9pZCI6Ilwib3VWTE9ZUDhsZWxOXCIiLCJ0cGFfaWQiOiJcInRwYXlmalBQSFREZ3ZcIiIsInRwYV9uYW1lIjoiXCJGeWxlIDw-IFNhZ2UgSW4uLlwiIiwiY2x1c3Rlcl9kb21haW4iOiJcImh0dHBzOi8vc3RhZ2luZy5meWxlLnRlY2hcIiIsImV4cCI6MTk3OTAyMzA3Mn0.NGRySUzDx7ycSD_6LaRy_wTGMD7Yl-u3I1FmOo9BWhk	2022-09-20 14:08:03.43928+05:30	2022-09-20 14:08:03.439323+05:30	1	https://staging.fyle.tech
\.


--
-- Data for Name: general_mappings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.general_mappings (id, default_location_name, default_location_id, default_department_name, default_department_id, default_project_name, default_project_id, created_at, updated_at, workspace_id, default_charge_card_name, default_charge_card_id, default_ccc_vendor_name, default_ccc_vendor_id, default_item_id, default_item_name, payment_account_id, payment_account_name, default_ccc_expense_payment_type_id, default_ccc_expense_payment_type_name, default_reimbursable_expense_payment_type_id, default_reimbursable_expense_payment_type_name, use_intacct_employee_departments, use_intacct_employee_locations, location_entity_id, location_entity_name, default_class_id, default_class_name, default_tax_code_id, default_tax_code_name, default_credit_card_id, default_credit_card_name) FROM stdin;
1	Australia	600	Admin	300	Branding Analysis	10061	2022-09-20 14:17:19.634467+05:30	2022-10-10 13:55:16.32686+05:30	1		20600		20043	1012	Cube	400_CHK	Demo Bank - 400_CHK		\N			f	f			600	Enterprise	W4 Withholding Tax	W4 Withholding Tax	20610	Accr. Sales Tax Payable
\.


--
-- Data for Name: journal_entries; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.journal_entries (id, description, memo, currency, supdoc_id, transaction_date, created_at, updated_at, expense_group_id) FROM stdin;
\.


--
-- Data for Name: journal_entry_lineitems; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.journal_entry_lineitems (id, gl_account_number, project_id, location_id, class_id, department_id, customer_id, item_id, memo, user_defined_dimensions, amount, billable, transaction_date, created_at, updated_at, expense_id, journal_entry_id, employee_id, vendor_id, tax_amount, tax_code, cost_type_id, task_id) FROM stdin;
\.


--
-- Data for Name: location_entity_mappings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.location_entity_mappings (id, location_entity_name, country_name, destination_id, created_at, updated_at, workspace_id) FROM stdin;
1	Australia	Australia	600	2022-09-20 14:09:00.668977+05:30	2022-09-20 14:09:00.669049+05:30	1
\.


--
-- Data for Name: mapping_settings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.mapping_settings (id, source_field, destination_field, created_at, updated_at, workspace_id, import_to_fyle, is_custom, source_placeholder, expense_field_id) FROM stdin;
1	EMPLOYEE	EMPLOYEE	2022-09-20 14:09:32.083277+05:30	2022-09-20 14:09:32.083321+05:30	1	f	f	\N	\N
2	CATEGORY	EXPENSE_TYPE	2022-09-20 14:09:32.159859+05:30	2022-09-20 14:09:32.159909+05:30	1	f	f	\N	\N
4	EMPLOYEE	VENDOR	2022-09-20 14:16:24.843685+05:30	2022-09-20 14:16:24.843742+05:30	1	f	f	\N	\N
5	CATEGORY	ACCOUNT	2022-09-20 14:16:24.937151+05:30	2022-09-20 14:16:24.937198+05:30	1	f	f	\N	\N
3	PROJECT	PROJECT	2022-09-20 14:09:32.268681+05:30	2022-09-20 14:16:24.988239+05:30	1	t	f	\N	\N
666	TAX_GROUP	TAX_CODE	2022-09-20 14:09:32.268681+05:30	2022-09-20 14:16:24.988239+05:30	1	t	f	\N	\N
\.


--
-- Data for Name: mappings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.mappings (id, source_type, destination_type, created_at, updated_at, destination_id, source_id, workspace_id) FROM stdin;
1	PROJECT	PROJECT	2022-09-20 14:10:25.866372+05:30	2022-09-20 14:10:25.866416+05:30	602	3218	1
2	PROJECT	PROJECT	2022-09-20 14:10:25.866474+05:30	2022-09-20 14:10:25.866504+05:30	599	3219	1
3	PROJECT	PROJECT	2022-09-20 14:10:25.866558+05:30	2022-09-20 14:10:25.866587+05:30	598	3220	1
4	PROJECT	PROJECT	2022-09-20 14:10:25.866639+05:30	2022-09-20 14:10:25.866668+05:30	601	3221	1
5	PROJECT	PROJECT	2022-09-20 14:10:25.866721+05:30	2022-09-20 14:10:25.86675+05:30	609	1860	1
6	PROJECT	PROJECT	2022-09-20 14:10:25.866801+05:30	2022-09-20 14:10:25.86683+05:30	612	688	1
7	PROJECT	PROJECT	2022-09-20 14:10:25.866881+05:30	2022-09-20 14:10:25.86691+05:30	605	1861	1
8	PROJECT	PROJECT	2022-09-20 14:10:25.866961+05:30	2022-09-20 14:10:25.86699+05:30	606	1862	1
9	PROJECT	PROJECT	2022-09-20 14:10:25.867042+05:30	2022-09-20 14:10:25.867071+05:30	610	1863	1
10	PROJECT	PROJECT	2022-09-20 14:10:25.867122+05:30	2022-09-20 14:10:25.868347+05:30	611	1864	1
11	PROJECT	PROJECT	2022-09-20 14:10:25.869298+05:30	2022-09-20 14:10:25.869483+05:30	613	1865	1
12	PROJECT	PROJECT	2022-09-20 14:10:25.872684+05:30	2022-09-20 14:10:25.873014+05:30	600	1870	1
13	PROJECT	PROJECT	2022-09-20 14:10:25.873601+05:30	2022-09-20 14:10:25.873804+05:30	603	1866	1
14	PROJECT	PROJECT	2022-09-20 14:10:25.874137+05:30	2022-09-20 14:10:25.87417+05:30	604	1867	1
15	PROJECT	PROJECT	2022-09-20 14:10:25.874787+05:30	2022-09-20 14:10:25.874823+05:30	607	1868	1
16	PROJECT	PROJECT	2022-09-20 14:10:25.874882+05:30	2022-09-20 14:10:25.874912+05:30	608	1869	1
160	PROJECT	CUSTOMER	2022-09-20 14:10:25.874882+05:30	2022-09-20 14:10:25.874912+05:30	614	1	1
17	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.625158+05:30	2022-09-29 17:39:34.625202+05:30	589	3233	1
18	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.625256+05:30	2022-09-29 17:39:34.625286+05:30	583	3229	1
19	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.625338+05:30	2022-09-29 17:39:34.625368+05:30	594	3246	1
20	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.62542+05:30	2022-09-29 17:39:34.625449+05:30	593	2939	1
21	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.625501+05:30	2022-09-29 17:39:34.62553+05:30	559	3230	1
22	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.625582+05:30	2022-09-29 17:39:34.625612+05:30	560	2884	1
23	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.625663+05:30	2022-09-29 17:39:34.625693+05:30	561	2692	1
24	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.625745+05:30	2022-09-29 17:39:34.625774+05:30	562	3252	1
25	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.625826+05:30	2022-09-29 17:39:34.625855+05:30	563	3254	1
26	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.625907+05:30	2022-09-29 17:39:34.625936+05:30	564	2725	1
27	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.62752+05:30	2022-09-29 17:39:34.628546+05:30	565	2968	1
28	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.628792+05:30	2022-09-29 17:39:34.629404+05:30	566	3250	1
29	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.630356+05:30	2022-09-29 17:39:34.630412+05:30	579	2869	1
30	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.631269+05:30	2022-09-29 17:39:34.631309+05:30	584	3041	1
31	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.634545+05:30	2022-09-29 17:39:34.634583+05:30	585	2922	1
32	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.634639+05:30	2022-09-29 17:39:34.634668+05:30	575	2875	1
33	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.634721+05:30	2022-09-29 17:39:34.63475+05:30	576	3232	1
34	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.634803+05:30	2022-09-29 17:39:34.634832+05:30	582	3234	1
35	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.635751+05:30	2022-09-29 17:39:34.636281+05:30	581	2834	1
36	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.636474+05:30	2022-09-29 17:39:34.636518+05:30	580	3237	1
37	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.63658+05:30	2022-09-29 17:39:34.63661+05:30	586	3235	1
38	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.636662+05:30	2022-09-29 17:39:34.636692+05:30	577	2840	1
39	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.636744+05:30	2022-09-29 17:39:34.636773+05:30	578	3241	1
40	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.636826+05:30	2022-09-29 17:39:34.636855+05:30	588	3228	1
41	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.636907+05:30	2022-09-29 17:39:34.637467+05:30	587	2954	1
42	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.63805+05:30	2022-09-29 17:39:34.638087+05:30	574	3251	1
43	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.639538+05:30	2022-09-29 17:39:34.639569+05:30	597	3248	1
44	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.639745+05:30	2022-09-29 17:39:34.639776+05:30	595	3236	1
45	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.639934+05:30	2022-09-29 17:39:34.639964+05:30	596	2751	1
46	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.640017+05:30	2022-09-29 17:39:34.640046+05:30	592	2822	1
47	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.640098+05:30	2022-09-29 17:39:34.640127+05:30	591	2857	1
48	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.640179+05:30	2022-09-29 17:39:34.640208+05:30	567	3238	1
49	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.64026+05:30	2022-09-29 17:39:34.640289+05:30	568	2984	1
50	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.640341+05:30	2022-09-29 17:39:34.64037+05:30	569	2737	1
51	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.640422+05:30	2022-09-29 17:39:34.640451+05:30	570	3247	1
52	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.640503+05:30	2022-09-29 17:39:34.640532+05:30	571	3253	1
53	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.640584+05:30	2022-09-29 17:39:34.640613+05:30	572	2905	1
54	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.640665+05:30	2022-09-29 17:39:34.640694+05:30	573	2947	1
55	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.640746+05:30	2022-09-29 17:39:34.640775+05:30	544	3242	1
56	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.640827+05:30	2022-09-29 17:39:34.640856+05:30	545	3243	1
57	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.640908+05:30	2022-09-29 17:39:34.640937+05:30	546	2720	1
58	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.640989+05:30	2022-09-29 17:39:34.641199+05:30	547	2916	1
59	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.641253+05:30	2022-09-29 17:39:34.641282+05:30	548	3249	1
60	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.641334+05:30	2022-09-29 17:39:34.641364+05:30	549	3245	1
61	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.641415+05:30	2022-09-29 17:39:34.641444+05:30	550	2873	1
62	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.641496+05:30	2022-09-29 17:39:34.641525+05:30	551	3019	1
63	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.641577+05:30	2022-09-29 17:39:34.641607+05:30	552	3240	1
64	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.641659+05:30	2022-09-29 17:39:34.641702+05:30	553	2982	1
65	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.641755+05:30	2022-09-29 17:39:34.641784+05:30	554	2893	1
66	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.641836+05:30	2022-09-29 17:39:34.641865+05:30	555	3239	1
67	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.699518+05:30	2022-09-29 17:39:34.699563+05:30	556	2747	1
68	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.699623+05:30	2022-09-29 17:39:34.699655+05:30	557	2909	1
69	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.69971+05:30	2022-09-29 17:39:34.699741+05:30	558	3231	1
70	TAX_GROUP	TAX_DETAIL	2022-09-29 17:39:34.699794+05:30	2022-09-29 17:39:34.699824+05:30	590	3244	1
\.


--
-- Data for Name: reimbursements; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.reimbursements (id, settlement_id, reimbursement_id, state, created_at, updated_at, workspace_id, payment_number) FROM stdin;
1	setqwcKcC9q1k	reimzte4XjS5tx	PENDING	2022-09-20 14:17:51.808108+05:30	2022-09-20 14:17:51.808176+05:30	1	P/2022/09/R/18
2	set5FLB0eh8xU	reim2RjmQmJsUD	COMPLETE	2022-09-20 14:17:51.808248+05:30	2022-09-20 14:17:51.808281+05:30	1	P/2022/05/R/11
3	setjlrzx3KsTr	reim5Ig0uFpbo3	COMPLETE	2022-09-20 14:17:51.808422+05:30	2022-09-20 14:17:51.808453+05:30	1	P/2022/06/R/17
4	setmOIibblGoO	reime84IEu8wnG	COMPLETE	2022-09-20 14:17:51.808505+05:30	2022-09-20 14:17:51.808535+05:30	1	P/2022/06/R/15
5	setiy4J9cu4lV	reimeEcHpUxZ1L	COMPLETE	2022-09-20 14:17:51.808585+05:30	2022-09-20 14:17:51.808614+05:30	1	P/2022/06/R/11
6	set3llK6jy981	reimFd2WUwdrbJ	COMPLETE	2022-09-20 14:17:51.808664+05:30	2022-09-20 14:17:51.808693+05:30	1	P/2022/06/R/16
7	setMFIF5t1xZM	reimh6EMg30WNY	COMPLETE	2022-09-20 14:17:51.808734+05:30	2022-09-20 14:17:51.808763+05:30	1	P/2022/06/R/5
8	setvJYD03y62Z	reimHpPPfefahf	COMPLETE	2022-09-20 14:17:51.812682+05:30	2022-09-20 14:17:51.812739+05:30	1	P/2022/06/R/8
9	setxlydfOSEml	reimidjcT51i27	COMPLETE	2022-09-20 14:17:51.812808+05:30	2022-09-20 14:17:51.812842+05:30	1	P/2022/06/R/12
10	set70JEvCZqpM	reimKj2P1QF8ie	COMPLETE	2022-09-20 14:17:51.812899+05:30	2022-09-20 14:17:51.81293+05:30	1	P/2022/06/R/10
11	setrElGUl12ZH	reimlomI5EMKMh	COMPLETE	2022-09-20 14:17:51.812975+05:30	2022-09-20 14:17:51.812996+05:30	1	P/2022/06/R/6
12	setUXsf02fMoD	reimmgo2w4kva6	COMPLETE	2022-09-20 14:17:51.813046+05:30	2022-09-20 14:17:51.813057+05:30	1	P/2022/06/R/7
13	setzNuDqnpKlJ	reimPHrm7mFOXo	COMPLETE	2022-09-20 14:17:51.813096+05:30	2022-09-20 14:17:51.813125+05:30	1	P/2022/06/R/4
14	set2sqoTh6wb0	reimrHkkHUJ8Gn	COMPLETE	2022-09-20 14:17:51.81318+05:30	2022-09-20 14:17:51.813227+05:30	1	P/2022/05/R/14
15	setZUJiexagYV	reimTQIdCC1cxh	COMPLETE	2022-09-20 14:17:51.813677+05:30	2022-09-20 14:17:51.81371+05:30	1	P/2022/06/R/13
16	setp8l6eBKsMq	reimvpdXPsWWhu	COMPLETE	2022-09-20 14:17:51.813761+05:30	2022-09-20 14:17:51.81378+05:30	1	P/2022/06/R/3
17	set3j7OPg6Yl5	reimVUTPgEBWij	COMPLETE	2022-09-20 14:17:51.813818+05:30	2022-09-20 14:17:51.813847+05:30	1	P/2022/06/R/9
18	set8gJFi2HOmA	reimxHWDq39irq	COMPLETE	2022-09-20 14:17:51.813898+05:30	2022-09-20 14:17:51.813925+05:30	1	P/2022/06/R/2
19	setmOppa5zapS	reimXMxDsWHuXs	COMPLETE	2022-09-20 14:17:51.813965+05:30	2022-09-20 14:17:51.813986+05:30	1	P/2022/06/R/14
20	setj5Pk3oxJlx	reimyzPqNZtctG	COMPLETE	2022-09-20 14:17:51.814029+05:30	2022-09-20 14:17:51.814049+05:30	1	P/2022/05/R/12
21	setswbV0CUUFX	reimz57kBsJtld	COMPLETE	2022-09-20 14:17:51.814094+05:30	2022-09-20 14:17:51.814115+05:30	1	P/2022/05/R/13
22	setWkgMfopVep	reim0nbuTxhdkO	COMPLETE	2022-09-20 14:17:51.814163+05:30	2022-09-20 14:17:51.814192+05:30	1	P/2022/08/R/9
23	set2PSQwMhM6U	reim0YeymLba9C	COMPLETE	2022-09-20 14:17:51.814241+05:30	2022-09-20 14:17:51.81427+05:30	1	P/2022/08/R/5
24	setXt57nb6pKe	reim5ukhDLAnTq	COMPLETE	2022-09-20 14:17:51.814318+05:30	2022-09-20 14:17:51.814483+05:30	1	P/2022/08/R/17
25	setkPoEupZuYN	reimDkBxBu4yZf	COMPLETE	2022-09-20 14:17:51.814533+05:30	2022-09-20 14:17:51.814572+05:30	1	P/2022/08/R/18
26	setAeXPftpTJs	reimDNiCqHYHgS	COMPLETE	2022-09-20 14:17:51.814854+05:30	2022-09-20 14:17:51.814883+05:30	1	P/2022/08/R/7
27	set8a1tCmnYFS	reimetc9gMzjbc	COMPLETE	2022-09-20 14:17:51.814933+05:30	2022-09-20 14:17:51.814962+05:30	1	P/2022/08/R/11
28	setWz9XHlAq0A	reimGcNnYhpdIM	COMPLETE	2022-09-20 14:17:51.815011+05:30	2022-09-20 14:17:51.81504+05:30	1	P/2022/08/R/4
29	setgknnFFrKZm	reimGGoOlCtQxK	COMPLETE	2022-09-20 14:17:51.815088+05:30	2022-09-20 14:17:51.815117+05:30	1	P/2022/08/R/12
30	setvBgVgJrdp7	reimHg1m3UfObg	COMPLETE	2022-09-20 14:17:51.815166+05:30	2022-09-20 14:17:51.815188+05:30	1	P/2022/08/R/16
31	setEk25Ej2dYa	reimjggxQT2KT2	COMPLETE	2022-09-20 14:17:51.815227+05:30	2022-09-20 14:17:51.815253+05:30	1	P/2022/08/R/19
32	setV33iekWALa	reimKJxRnxnBJS	COMPLETE	2022-09-20 14:17:51.815295+05:30	2022-09-20 14:17:51.815316+05:30	1	P/2022/08/R/1
33	settgdQdi3kHO	reimKXsoQHd92z	COMPLETE	2022-09-20 14:17:51.815482+05:30	2022-09-20 14:17:51.815511+05:30	1	P/2022/08/R/6
34	setRMWuk4iYw9	reimnmvK7cV55S	COMPLETE	2022-09-20 14:17:51.81556+05:30	2022-09-20 14:17:51.815585+05:30	1	P/2022/08/R/14
35	setTtUB3Nxv64	reimP6VNLbE30x	COMPLETE	2022-09-20 14:17:51.81562+05:30	2022-09-20 14:17:51.81564+05:30	1	P/2022/08/R/13
36	setPg0GGgvKQI	reimP6x08mtt8I	COMPLETE	2022-09-20 14:17:51.815688+05:30	2022-09-20 14:17:51.815711+05:30	1	P/2022/08/R/15
37	setwE5XebQxQ7	reimS4CRRgYoRW	COMPLETE	2022-09-20 14:17:51.815749+05:30	2022-09-20 14:17:51.815762+05:30	1	P/2022/08/R/10
38	set76k4HcGUtW	reimu81hqajeUC	COMPLETE	2022-09-20 14:17:51.815799+05:30	2022-09-20 14:17:51.815828+05:30	1	P/2022/08/R/3
39	setFqwEHTJjrK	reimUTW9JYjtHU	COMPLETE	2022-09-20 14:17:51.815894+05:30	2022-09-20 14:17:51.816099+05:30	1	P/2022/08/R/8
40	setwUhRA0KaY4	reimX2Ixjiz7Vz	COMPLETE	2022-09-20 14:17:51.816147+05:30	2022-09-20 14:17:51.816163+05:30	1	P/2022/07/R/1
41	setUYgcGYmtmG	reimXluEZX1lnI	COMPLETE	2022-09-20 14:17:51.816193+05:30	2022-09-20 14:17:51.816204+05:30	1	P/2022/08/R/2
42	setiky8BvnZe2	reim1HUbZT2Uwb	COMPLETE	2022-09-20 14:17:51.816344+05:30	2022-09-20 14:17:51.816374+05:30	1	P/2022/09/R/5
43	setuA9bmHMCAB	reim7BEPKbVShk	COMPLETE	2022-09-20 14:17:51.816417+05:30	2022-09-20 14:17:51.816438+05:30	1	P/2022/09/R/12
44	setbLjsy1xfjA	reim9cHfXO85I8	COMPLETE	2022-09-20 14:17:51.816486+05:30	2022-09-20 14:17:51.816515+05:30	1	P/2022/08/R/24
45	setwxULQx5tq2	reimA8qgYTWcWH	COMPLETE	2022-09-20 14:17:51.816563+05:30	2022-09-20 14:17:51.816592+05:30	1	P/2022/09/R/11
46	setkpwnVyO3y5	reimEhgLUezlly	COMPLETE	2022-09-20 14:17:51.81664+05:30	2022-09-20 14:17:51.816668+05:30	1	P/2022/09/R/4
47	set1ajeVe3WRn	reimFntqayhgSZ	COMPLETE	2022-09-20 14:17:51.816716+05:30	2022-09-20 14:17:51.816744+05:30	1	P/2022/09/R/9
48	setNr2gpPnW5d	reimGu7DSy6msg	COMPLETE	2022-09-20 14:17:51.816793+05:30	2022-09-20 14:17:51.816821+05:30	1	P/2022/09/R/13
49	setM00XOyYg1I	reimHGvrzP8ssT	COMPLETE	2022-09-20 14:17:51.816869+05:30	2022-09-20 14:17:51.816898+05:30	1	P/2022/09/R/10
50	setlqphxXzMTJ	reimhZuvy914g5	COMPLETE	2022-09-20 14:17:51.816946+05:30	2022-09-20 14:17:51.816975+05:30	1	P/2022/09/R/6
51	setJ5iHytj8dq	reimJhGrnPNrnX	COMPLETE	2022-09-20 14:17:51.822402+05:30	2022-09-20 14:17:51.82245+05:30	1	P/2022/09/R/15
52	setkUxPBznLvB	reimP2ybXzvgpi	COMPLETE	2022-09-20 14:17:51.822581+05:30	2022-09-20 14:17:51.822614+05:30	1	P/2022/08/R/20
53	setHhVs7ch1f3	reimrRSByPXrfN	COMPLETE	2022-09-20 14:17:51.82267+05:30	2022-09-20 14:17:51.822701+05:30	1	P/2022/09/R/14
54	setbeE1A4FsJU	reims6JCiLNxFH	COMPLETE	2022-09-20 14:17:51.822754+05:30	2022-09-20 14:17:51.822784+05:30	1	P/2022/09/R/1
55	setanvdyKD6dO	reimSqj0iAonFo	COMPLETE	2022-09-20 14:17:51.822835+05:30	2022-09-20 14:17:51.822865+05:30	1	P/2022/09/R/7
56	sethxBoyUzcz6	reimUJs0SdG6dL	COMPLETE	2022-09-20 14:17:51.822914+05:30	2022-09-20 14:17:51.822936+05:30	1	P/2022/08/R/23
57	setA8r2MzF3kK	reimUzDJ5dUjkf	COMPLETE	2022-09-20 14:17:51.823341+05:30	2022-09-20 14:17:51.823392+05:30	1	P/2022/09/R/8
58	setuTsN3SkzH6	reimvck3fBDKrf	COMPLETE	2022-09-20 14:17:51.823454+05:30	2022-09-20 14:17:51.823476+05:30	1	P/2022/08/R/21
59	setnT6AjMPLB0	reimvPNgRCXhkc	COMPLETE	2022-09-20 14:17:51.823528+05:30	2022-09-20 14:17:51.823558+05:30	1	P/2022/09/R/2
60	setld9H2KG04t	reimWFb1v6hoe2	COMPLETE	2022-09-20 14:17:51.823609+05:30	2022-09-20 14:17:51.823638+05:30	1	P/2022/09/R/3
61	setwrURFfkW7c	reimWI4cDyd1r6	COMPLETE	2022-09-20 14:17:51.823688+05:30	2022-09-20 14:17:51.823717+05:30	1	P/2022/08/R/22
62	setWf2v1zXLMZ	reimcjxGshI8hJ	COMPLETE	2022-09-20 14:17:51.823766+05:30	2022-09-20 14:17:51.823795+05:30	1	P/2022/09/R/16
63	setKV0ZDxp4TS	reimgjdi6u2Zf5	COMPLETE	2022-09-20 14:17:51.823844+05:30	2022-09-20 14:17:51.823873+05:30	1	P/2022/09/R/17
64	setikmPeawoBZ	reimFavFEXjoSv	COMPLETE	2022-09-20 14:17:51.823921+05:30	2022-09-20 14:17:51.823951+05:30	1	P/2022/07/R/2
65	setqmieWjVpZm	reimzaZeihks67	COMPLETE	2022-09-20 14:17:51.823999+05:30	2022-09-20 14:17:51.824028+05:30	1	P/2022/06/R/1
66	setGtUuWv5015	reim8Lk8pWGDWL	COMPLETE	2022-09-20 14:17:51.824076+05:30	2022-09-20 14:17:51.824105+05:30	1	P/2022/05/R/6
67	set9k3fC23ByK	reimKAauskSQ9f	COMPLETE	2022-09-20 14:17:51.824153+05:30	2022-09-20 14:17:51.824181+05:30	1	P/2022/05/R/8
68	setDiksMn83K7	reimKUEIyXDetA	COMPLETE	2022-09-20 14:17:51.82423+05:30	2022-09-20 14:17:51.824259+05:30	1	P/2022/05/R/7
69	setCb41PcrHmO	reiml5iq0TVzp6	COMPLETE	2022-09-20 14:17:51.824306+05:30	2022-09-20 14:17:51.824335+05:30	1	P/2022/05/R/9
70	setlcYd0kfoBv	reimNM1P8qb3XS	COMPLETE	2022-09-20 14:17:51.824383+05:30	2022-09-20 14:17:51.824412+05:30	1	P/2022/05/R/10
71	setr9WSZQIwzH	reimrFgDFccXv9	COMPLETE	2022-09-20 14:17:51.82446+05:30	2022-09-20 14:17:51.824489+05:30	1	P/2022/05/R/3
72	sett283OqFZ42	reimuuvvDSapAh	COMPLETE	2022-09-20 14:17:51.824537+05:30	2022-09-20 14:17:51.824566+05:30	1	P/2022/05/R/4
73	set3ScziYvftR	reimxQfwQn2vSB	COMPLETE	2022-09-20 14:17:51.824613+05:30	2022-09-20 14:17:51.824642+05:30	1	P/2022/05/R/5
74	setUwjAkWcafS	reimiRGVADdoIt	COMPLETE	2022-09-20 14:17:51.82469+05:30	2022-09-20 14:17:51.824719+05:30	1	P/2022/05/R/2
75	setPAm1kjS3ld	reim9zPoX63qyx	COMPLETE	2022-09-20 14:17:51.824767+05:30	2022-09-20 14:17:51.824796+05:30	1	P/2022/05/R/1
76	set07HSTeqYTx	reimad8dQd65q8	COMPLETE	2022-09-20 14:17:51.824843+05:30	2022-09-20 14:17:51.824872+05:30	1	P/2022/04/R/27
77	setST8251H5Jr	reimhk1t2JezgC	COMPLETE	2022-09-20 14:17:51.824916+05:30	2022-09-20 14:17:51.824927+05:30	1	P/2022/04/R/28
78	setTGZBza3I48	reimapbaP4rd6m	COMPLETE	2022-09-20 14:17:51.824963+05:30	2022-09-20 14:17:51.824985+05:30	1	P/2022/04/R/26
79	set71RslsZm53	reim0uzF4CQrfv	COMPLETE	2022-09-20 14:17:51.825022+05:30	2022-09-20 14:17:51.825042+05:30	1	P/2022/04/R/21
80	setDCOvDMLWgp	reim2aiRHof8uf	COMPLETE	2022-09-20 14:17:51.825089+05:30	2022-09-20 14:17:51.825118+05:30	1	P/2022/04/R/14
81	set0E1WIAaUFt	reim5ULJ7gVG40	COMPLETE	2022-09-20 14:17:51.825166+05:30	2022-09-20 14:17:51.82519+05:30	1	P/2022/04/R/20
82	setXNNvb38eHN	reimHaaF2UZzXs	COMPLETE	2022-09-20 14:17:51.825229+05:30	2022-09-20 14:17:51.825258+05:30	1	P/2022/04/R/16
83	setdQvhTSJjIJ	reimj6e8QZkVon	COMPLETE	2022-09-20 14:17:51.825306+05:30	2022-09-20 14:17:51.825335+05:30	1	P/2022/04/R/23
84	setkXtd0l3JNq	reimLIKtE9x5Gq	COMPLETE	2022-09-20 14:17:51.825383+05:30	2022-09-20 14:17:51.825412+05:30	1	P/2022/04/R/18
85	setDGwWFhIIrG	reimLNl7P6yZ60	COMPLETE	2022-09-20 14:17:51.82546+05:30	2022-09-20 14:17:51.825489+05:30	1	P/2022/04/R/24
86	setIvuHHWWfQ7	reimo0xQELF5Om	COMPLETE	2022-09-20 14:17:51.825538+05:30	2022-09-20 14:17:51.825575+05:30	1	P/2022/04/R/19
87	setuEuBHtQhJJ	reimosKIcBRbFr	COMPLETE	2022-09-20 14:17:51.825908+05:30	2022-09-20 14:17:51.826388+05:30	1	P/2022/04/R/15
88	set8hrKnn02s5	reimp50f85KIJ6	COMPLETE	2022-09-20 14:17:51.827002+05:30	2022-09-20 14:17:51.827203+05:30	1	P/2022/04/R/17
89	setTLJ2yG0iME	reimqKq51CeH5R	COMPLETE	2022-09-20 14:17:51.827556+05:30	2022-09-20 14:17:51.827621+05:30	1	P/2022/04/R/13
90	setWklffaEIjT	reimVkyjTfI0fk	COMPLETE	2022-09-20 14:17:51.828021+05:30	2022-09-20 14:17:51.828567+05:30	1	P/2022/04/R/22
91	sethmLu8oDIGx	reim2P360jHuWg	COMPLETE	2022-09-20 14:17:51.829745+05:30	2022-09-20 14:17:51.82989+05:30	1	P/2022/03/R/17
92	setyuwUtkVB80	reim44c6rCEjFZ	COMPLETE	2022-09-20 14:17:51.830663+05:30	2022-09-20 14:17:51.830976+05:30	1	P/2022/03/R/2
93	setcGfp8wvVkh	reim4uhnCaijDm	COMPLETE	2022-09-20 14:17:51.832438+05:30	2022-09-20 14:17:51.833183+05:30	1	P/2022/03/R/13
94	setLSIPk4e2y7	reim6HoIExG9ip	COMPLETE	2022-09-20 14:17:51.83377+05:30	2022-09-20 14:17:51.834572+05:30	1	P/2022/03/R/15
95	settnQdWmPC0J	reim8P85qUFwub	COMPLETE	2022-09-20 14:17:51.837307+05:30	2022-09-20 14:17:51.838869+05:30	1	P/2022/03/R/8
96	setOcEEfhjFaz	reimAj1WFC7Cso	COMPLETE	2022-09-20 14:17:51.840527+05:30	2022-09-20 14:17:51.840967+05:30	1	P/2022/03/R/11
97	setZFCbhKDmlx	reimbLQoBvnHIc	COMPLETE	2022-09-20 14:17:51.841046+05:30	2022-09-20 14:17:51.842989+05:30	1	P/2022/03/R/5
98	setM00lSHnq5R	reimFQqG7b1TLN	COMPLETE	2022-09-20 14:17:51.843814+05:30	2022-09-20 14:17:51.844051+05:30	1	P/2022/03/R/9
99	setWksKskZS9T	reimHyqG6ycQsc	COMPLETE	2022-09-20 14:17:51.844874+05:30	2022-09-20 14:17:51.84499+05:30	1	P/2022/03/R/10
100	set4IB2lgkO81	reimIRnWM4OSjd	COMPLETE	2022-09-20 14:17:51.845486+05:30	2022-09-20 14:17:51.845671+05:30	1	P/2022/03/R/4
101	setNfPWvMVo9i	reimM5ApRLmRxs	COMPLETE	2022-09-20 14:17:51.859505+05:30	2022-09-20 14:17:51.859546+05:30	1	P/2022/03/R/1
102	setvN2PzkReuX	reimOQ0PjfcTrO	COMPLETE	2022-09-20 14:17:51.859594+05:30	2022-09-20 14:17:51.859625+05:30	1	P/2022/03/R/6
103	sethyy7hKOOJG	reimpO4DNwzKIP	COMPLETE	2022-09-20 14:17:51.859677+05:30	2022-09-20 14:17:51.859716+05:30	1	P/2022/03/R/7
104	setUiWCxpWU9W	reimq9xwG3c18j	COMPLETE	2022-09-20 14:17:51.859763+05:30	2022-09-20 14:17:51.85979+05:30	1	P/2022/03/R/14
105	setava6eJEse4	reimRbCnHMGfNE	COMPLETE	2022-09-20 14:17:51.859836+05:30	2022-09-20 14:17:51.859863+05:30	1	P/2022/03/R/16
106	setZMCqxqX9am	reimrrMZOocQOP	COMPLETE	2022-09-20 14:17:51.859909+05:30	2022-09-20 14:17:51.859936+05:30	1	P/2022/03/R/12
107	setgze09L0u2M	reimTuKaWlXWZp	COMPLETE	2022-09-20 14:17:51.859982+05:30	2022-09-20 14:17:51.860009+05:30	1	P/2022/03/R/18
108	set48IfVzq0yW	reimUC8ywjNm5X	COMPLETE	2022-09-20 14:17:51.860055+05:30	2022-09-20 14:17:51.860082+05:30	1	P/2022/03/R/3
109	set4nTmk49WTG	reimX2RpvsNWhL	COMPLETE	2022-09-20 14:17:51.860127+05:30	2022-09-20 14:17:51.860154+05:30	1	P/2022/04/R/1
110	seth6VNXcJYFY	reimZy8SIa2hrT	COMPLETE	2022-09-20 14:17:51.8602+05:30	2022-09-20 14:17:51.860227+05:30	1	P/2022/03/R/19
111	setRTRpBfxk74	reim0dzwluaekr	COMPLETE	2022-09-20 14:17:51.860272+05:30	2022-09-20 14:17:51.8603+05:30	1	P/2022/04/R/4
112	setGotI6V5Bc7	reim0jan70NxM0	COMPLETE	2022-09-20 14:17:51.860357+05:30	2022-09-20 14:17:51.860586+05:30	1	P/2022/04/R/12
113	setsUUIrSZ6FV	reim63zhXUcG3x	COMPLETE	2022-09-20 14:17:51.86078+05:30	2022-09-20 14:17:51.860809+05:30	1	P/2022/04/R/10
114	set0molu6y00L	reimazeO5ftv5e	COMPLETE	2022-09-20 14:17:51.86098+05:30	2022-09-20 14:17:51.861001+05:30	1	P/2022/04/R/2
115	setn5R9GYZJHa	reimcdR7M37m7u	COMPLETE	2022-09-20 14:17:51.861168+05:30	2022-09-20 14:17:51.861197+05:30	1	P/2022/04/R/5
116	setizmumgI16h	reimegLC8qXofr	COMPLETE	2022-09-20 14:17:51.861331+05:30	2022-09-20 14:17:51.86136+05:30	1	P/2022/04/R/6
117	setxTcm2NKM4z	reimEMBBTtWlaH	COMPLETE	2022-09-20 14:17:51.861416+05:30	2022-09-20 14:17:51.861444+05:30	1	P/2022/04/R/9
118	setuAmTQImATt	reimOkWc6NSeTV	COMPLETE	2022-09-20 14:17:51.861489+05:30	2022-09-20 14:17:51.861517+05:30	1	P/2022/04/R/7
119	set4EH2ck8BRV	reimPoi2fKYM43	COMPLETE	2022-09-20 14:17:51.861562+05:30	2022-09-20 14:17:51.86159+05:30	1	P/2022/04/R/11
120	setmykk0W2n2K	reimpzrHlcUWfA	COMPLETE	2022-09-20 14:17:51.861634+05:30	2022-09-20 14:17:51.861661+05:30	1	P/2022/04/R/3
121	setN6IN6qlZCZ	reims70NBaAJnI	COMPLETE	2022-09-20 14:17:51.861706+05:30	2022-09-20 14:17:51.861733+05:30	1	P/2022/04/R/8
122	setdZiDZ8D0ko	reim7RytpCGlTT	COMPLETE	2022-09-20 14:17:51.861778+05:30	2022-09-20 14:17:51.861805+05:30	1	P/2022/02/R/15
123	setpGurFkSvLj	reimAY92WzJm1Z	COMPLETE	2022-09-20 14:17:51.86185+05:30	2022-09-20 14:17:51.861877+05:30	1	P/2022/02/R/10
124	setsdctMW3RGI	reimgI9wRdvRSq	COMPLETE	2022-09-20 14:17:51.861922+05:30	2022-09-20 14:17:51.861949+05:30	1	P/2022/02/R/16
125	setwfuGqOD7Fj	reimgttOEE3GzU	COMPLETE	2022-09-20 14:17:51.861994+05:30	2022-09-20 14:17:51.862021+05:30	1	P/2022/02/R/8
126	setU5bHAY0duH	reimHXatGajJAF	COMPLETE	2022-09-20 14:17:51.862066+05:30	2022-09-20 14:17:51.862093+05:30	1	P/2022/02/R/9
127	setSB57y0GWNi	reimlRxqgraaSZ	COMPLETE	2022-09-20 14:17:51.862139+05:30	2022-09-20 14:17:51.862166+05:30	1	P/2022/02/R/13
128	setJVeW5M8DV0	reimMFnVXze33C	COMPLETE	2022-09-20 14:17:51.86221+05:30	2022-09-20 14:17:51.862238+05:30	1	P/2022/02/R/14
129	set4oKGBzriLU	reimNl0BNyTaqZ	COMPLETE	2022-09-20 14:17:51.862282+05:30	2022-09-20 14:17:51.86231+05:30	1	P/2022/02/R/6
130	setPB71bu3fMn	reimOEym6ene9g	COMPLETE	2022-09-20 14:17:51.862354+05:30	2022-09-20 14:17:51.862381+05:30	1	P/2022/02/R/12
131	setL6I4NXOECq	reimoUn2AZn8nN	COMPLETE	2022-09-20 14:17:51.862538+05:30	2022-09-20 14:17:51.862568+05:30	1	P/2022/02/R/7
132	setJa7ohOyOVq	reimuZORFOP1eU	COMPLETE	2022-09-20 14:17:51.862617+05:30	2022-09-20 14:17:51.862646+05:30	1	P/2022/02/R/11
133	setazA7r4XEAX	reim0xadXajpKe	COMPLETE	2022-09-20 14:17:51.862704+05:30	2022-09-20 14:17:51.862731+05:30	1	P/2022/02/R/3
134	set3Jk3g3Z6Zy	reim259bHDvtKo	COMPLETE	2022-09-20 14:17:51.862776+05:30	2022-09-20 14:17:51.862803+05:30	1	P/2022/02/R/1
135	setp4P01OhM7P	reim4PrtYFGswm	COMPLETE	2022-09-20 14:17:51.862848+05:30	2022-09-20 14:17:51.862875+05:30	1	P/2022/02/R/4
136	setCsqR7hm2Yd	reimdv6QjZULGh	COMPLETE	2022-09-20 14:17:51.862921+05:30	2022-09-20 14:17:51.862948+05:30	1	P/2022/02/R/5
137	setHcR9AfVjG7	reimtGSoHV9eOq	COMPLETE	2022-09-20 14:17:51.862994+05:30	2022-09-20 14:17:51.863021+05:30	1	P/2022/02/R/2
138	set8I1KlM4ViY	reim3Z8MRqSOb4	COMPLETE	2022-09-20 14:17:51.863066+05:30	2022-09-20 14:17:51.863093+05:30	1	P/2022/01/R/13
139	setXTEjf2wY78	reim96dgvtsQLS	COMPLETE	2022-09-20 14:17:51.863148+05:30	2022-09-20 14:17:51.863178+05:30	1	P/2022/01/R/12
140	setwQTDDrGSJN	reimHEsSEj7WOF	COMPLETE	2022-09-20 14:17:51.86329+05:30	2022-09-20 14:17:51.863335+05:30	1	P/2022/01/R/15
141	setRaxYbWGAop	reimmJmfHydjTQ	COMPLETE	2022-09-20 14:17:51.863385+05:30	2022-09-20 14:17:51.863414+05:30	1	P/2022/01/R/14
142	setsSgEIicV7I	reimnTXklcfx8j	COMPLETE	2022-09-20 14:17:51.863471+05:30	2022-09-20 14:17:51.863498+05:30	1	P/2022/01/R/16
143	setTlzHY8Idf9	reimUQB0yvKE2H	COMPLETE	2022-09-20 14:17:51.863544+05:30	2022-09-20 14:17:51.863571+05:30	1	P/2022/01/R/11
144	setIeo4DDtxHT	reimHw5QUpoQUA	COMPLETE	2022-09-20 14:17:51.863616+05:30	2022-09-20 14:17:51.863644+05:30	1	P/2022/01/R/9
145	setMh1EJsrbhI	reimtPqiobU07o	COMPLETE	2022-09-20 14:17:51.863689+05:30	2022-09-20 14:17:51.863717+05:30	1	P/2022/01/R/10
146	set47jUdkX7df	reimdgZAnTYkyF	COMPLETE	2022-09-20 14:17:51.863762+05:30	2022-09-20 14:17:51.863789+05:30	1	P/2022/01/R/4
147	setkga8K7pOvH	reimh25CqiYFmz	COMPLETE	2022-09-20 14:17:51.863834+05:30	2022-09-20 14:17:51.863862+05:30	1	P/2022/01/R/5
148	seth0ZuGB45cU	reimWim0WoP21K	COMPLETE	2022-09-20 14:17:51.863908+05:30	2022-09-20 14:17:51.863935+05:30	1	P/2022/01/R/7
149	setQNMA55r3t6	reimY3Ws7FdKI0	COMPLETE	2022-09-20 14:17:51.86398+05:30	2022-09-20 14:17:51.864008+05:30	1	P/2022/01/R/8
150	setxw08fdZkJm	reimzvABRys4JB	COMPLETE	2022-09-20 14:17:51.864053+05:30	2022-09-20 14:17:51.86408+05:30	1	P/2022/01/R/6
151	setYWyqpn2e7h	reim4sBDuBc9Pt	COMPLETE	2022-09-20 14:17:51.87007+05:30	2022-09-20 14:17:51.870117+05:30	1	P/2021/12/R/25
152	set5zxN39ACYT	reim8V4mh3dtgf	COMPLETE	2022-09-20 14:17:51.870177+05:30	2022-09-20 14:17:51.87021+05:30	1	P/2021/12/R/24
153	set8pZeam5Xmh	reimEI6qpFxCXR	COMPLETE	2022-09-20 14:17:51.870262+05:30	2022-09-20 14:17:51.870292+05:30	1	P/2021/12/R/18
154	setVAi6qgTKaK	reimKhDIL8x231	COMPLETE	2022-09-20 14:17:51.870435+05:30	2022-09-20 14:17:51.870465+05:30	1	P/2021/12/R/21
155	setIgWi3knZi2	reimqy792bKbjL	COMPLETE	2022-09-20 14:17:51.870514+05:30	2022-09-20 14:17:51.870544+05:30	1	P/2021/12/R/19
156	set45twRgTDmG	reimR6FirDraLC	COMPLETE	2022-09-20 14:17:51.870593+05:30	2022-09-20 14:17:51.870622+05:30	1	P/2021/12/R/20
157	set0N7wWCQJdo	reimTIgDJ8TaLa	COMPLETE	2022-09-20 14:17:51.870671+05:30	2022-09-20 14:17:51.8707+05:30	1	P/2021/12/R/22
158	setO0UbNqJarw	reimvIkvR2x3gf	COMPLETE	2022-09-20 14:17:51.870743+05:30	2022-09-20 14:17:51.870762+05:30	1	P/2021/12/R/23
159	set69I0nRQOSb	reimVm757JWven	COMPLETE	2022-09-20 14:17:51.870799+05:30	2022-09-20 14:17:51.870828+05:30	1	P/2021/12/R/26
160	setvuXeevsFUi	reim3oIVrBLR4A	COMPLETE	2022-09-20 14:17:51.870872+05:30	2022-09-20 14:17:51.870892+05:30	1	P/2021/12/R/10
161	setxPPoKPROKS	reim7dRnQrZ4gq	COMPLETE	2022-09-20 14:17:51.87094+05:30	2022-09-20 14:17:51.870969+05:30	1	P/2021/12/R/3
162	set9cHrSJF4W7	reimC0X9RmP78z	COMPLETE	2022-09-20 14:17:51.871017+05:30	2022-09-20 14:17:51.871046+05:30	1	P/2021/12/R/5
163	set7dGYd4zqWx	reimdOwXsZszou	COMPLETE	2022-09-20 14:17:51.871094+05:30	2022-09-20 14:17:51.871123+05:30	1	P/2021/12/R/9
164	setqc9v7zLUau	reimfUh2zXgVIw	COMPLETE	2022-09-20 14:17:51.871171+05:30	2022-09-20 14:17:51.8712+05:30	1	P/2021/12/R/7
165	setIadhiifLvi	reimKQseRs6OyS	COMPLETE	2022-09-20 14:17:51.871248+05:30	2022-09-20 14:17:51.871277+05:30	1	P/2021/12/R/4
166	setUMqw9puNZC	reimlmR3MalDTS	COMPLETE	2022-09-20 14:17:51.871403+05:30	2022-09-20 14:17:51.871428+05:30	1	P/2021/12/R/11
167	setOkP5YhBDUX	reimN6QK1thbzP	COMPLETE	2022-09-20 14:17:51.871485+05:30	2022-09-20 14:17:51.871522+05:30	1	P/2021/12/R/15
168	setfkCx1C0aF7	reimPiGJOk6k2m	COMPLETE	2022-09-20 14:17:51.871716+05:30	2022-09-20 14:17:51.871856+05:30	1	P/2021/12/R/8
169	setMFzLqjWn0w	reimry3avp5Bfx	COMPLETE	2022-09-20 14:17:51.871902+05:30	2022-09-20 14:17:51.871929+05:30	1	P/2021/12/R/6
170	setiTgqNEQmbv	reimTXCPHfMAtL	COMPLETE	2022-09-20 14:17:51.872119+05:30	2022-09-20 14:17:51.872148+05:30	1	P/2021/12/R/12
171	setsOLPmsclEl	reimuFXDylMOQ5	COMPLETE	2022-09-20 14:17:51.87237+05:30	2022-09-20 14:17:51.872391+05:30	1	P/2021/12/R/16
172	sett8PY0YfPTP	reimyJDGFMXl9q	COMPLETE	2022-09-20 14:17:51.872549+05:30	2022-09-20 14:17:51.872577+05:30	1	P/2021/12/R/14
173	setosMugG1BZB	reimZlL2cKDmqQ	COMPLETE	2022-09-20 14:17:51.872622+05:30	2022-09-20 14:17:51.87265+05:30	1	P/2021/12/R/17
174	set7fW1a59Iah	reimzWqPnZflvp	COMPLETE	2022-09-20 14:17:51.872695+05:30	2022-09-20 14:17:51.872722+05:30	1	P/2021/12/R/13
175	setJUM1qUuD0v	reimzZDyqtTR44	COMPLETE	2022-09-20 14:17:51.872767+05:30	2022-09-20 14:17:51.872795+05:30	1	P/2021/12/R/2
176	setO6eQ3l8ZTW	reimkGTejmdR29	COMPLETE	2022-09-20 14:17:51.87284+05:30	2022-09-20 14:17:51.872867+05:30	1	P/2021/12/R/1
177	setNVTcPkZ6on	reimGo4jgmkxgu	COMPLETE	2022-09-20 14:17:51.872913+05:30	2022-09-20 14:17:51.87294+05:30	1	P/2021/11/R/6
178	set6GUp6tcEEp	reimuryMHcTPqS	COMPLETE	2022-09-20 14:17:51.872985+05:30	2022-09-20 14:17:51.873012+05:30	1	P/2021/11/R/5
179	settnd33XXXUV	reim4Ky9i1G9Kr	COMPLETE	2022-09-20 14:17:51.873057+05:30	2022-09-20 14:17:51.873084+05:30	1	P/2021/11/R/3
180	setqGwGhrDyFI	reimBO6Mv4Qnt8	COMPLETE	2022-09-20 14:17:51.873129+05:30	2022-09-20 14:17:51.873156+05:30	1	P/2021/11/R/4
181	set8c1zvWojUn	reimRz56rpQsE7	COMPLETE	2022-09-20 14:17:51.873201+05:30	2022-09-20 14:17:51.873377+05:30	1	P/2021/11/R/2
182	setuDRccuk3ZY	reimSh5EFeUxBp	COMPLETE	2022-09-20 14:17:51.87347+05:30	2022-09-20 14:17:51.873507+05:30	1	P/2021/11/R/1
183	setD0FxMB9wgI	reim1yN4sXTxUv	COMPLETE	2022-09-20 14:17:51.873575+05:30	2022-09-20 14:17:51.873615+05:30	1	P/2021/10/R/3
184	setapiOdjBgFM	reim5qVte0TNYh	COMPLETE	2022-09-20 14:17:51.873661+05:30	2022-09-20 14:17:51.873688+05:30	1	P/2021/10/R/6
185	setfco2Zf8Bhv	reim6vFkSNiwz5	COMPLETE	2022-09-20 14:17:51.873734+05:30	2022-09-20 14:17:51.873761+05:30	1	P/2021/10/R/7
186	setW46pKF7T4Z	reimOlkDOh2UGE	COMPLETE	2022-09-20 14:17:51.873806+05:30	2022-09-20 14:17:51.873833+05:30	1	P/2021/10/R/5
187	setYcoiZJOBkw	reimOqdMXmFM12	COMPLETE	2022-09-20 14:17:51.873879+05:30	2022-09-20 14:17:51.873906+05:30	1	P/2021/10/R/4
188	setf9EYZDnHpj	reimPJD5oAnocg	COMPLETE	2022-09-20 14:17:51.873951+05:30	2022-09-20 14:17:51.873979+05:30	1	P/2021/10/R/2
189	setID9JbDdOJf	reimWOE3evTwSF	COMPLETE	2022-09-20 14:17:51.874023+05:30	2022-09-20 14:17:51.87405+05:30	1	P/2021/10/R/1
190	setI5KZUaZTJB	reim0kuGWiPtFf	COMPLETE	2022-09-20 14:17:51.874095+05:30	2022-09-20 14:17:51.874123+05:30	1	P/2021/09/R/19
191	setoj9oE3CToc	reim0nwzia1h2t	COMPLETE	2022-09-20 14:17:51.874167+05:30	2022-09-20 14:17:51.874194+05:30	1	P/2021/09/R/27
192	setNQPb1pIVSZ	reim6yNBIgEcAZ	COMPLETE	2022-09-20 14:17:51.874239+05:30	2022-09-20 14:17:51.874266+05:30	1	P/2021/09/R/25
193	setBgSo93ruxj	reimbFci0QSgKr	COMPLETE	2022-09-20 14:17:51.874311+05:30	2022-09-20 14:17:51.874338+05:30	1	P/2021/09/R/28
194	setFjKBjHQ01G	reimhgMByHKZUX	COMPLETE	2022-09-20 14:17:51.874397+05:30	2022-09-20 14:17:51.87454+05:30	1	P/2021/09/R/21
195	setebUutDZHeo	reimICJTmIn4kc	COMPLETE	2022-09-20 14:17:51.874596+05:30	2022-09-20 14:17:51.874624+05:30	1	P/2021/09/R/22
196	setszPgxuxwLp	reimJeucH6013K	COMPLETE	2022-09-20 14:17:51.874668+05:30	2022-09-20 14:17:51.874695+05:30	1	P/2021/09/R/18
197	setmLzx1yk8yi	reimOR7xV95PGa	COMPLETE	2022-09-20 14:17:51.87474+05:30	2022-09-20 14:17:51.874767+05:30	1	P/2021/09/R/26
198	set8C6wTvgMnF	reimQ18CEIcK6R	COMPLETE	2022-09-20 14:17:51.874813+05:30	2022-09-20 14:17:51.87484+05:30	1	P/2021/09/R/23
199	setu2LSD0aj5d	reimW0r9GHIOBl	COMPLETE	2022-09-20 14:17:51.874885+05:30	2022-09-20 14:17:51.874912+05:30	1	P/2021/09/R/24
200	set2DYrdlPs9H	reimw981ttF3Am	COMPLETE	2022-09-20 14:17:51.874957+05:30	2022-09-20 14:17:51.874984+05:30	1	P/2021/09/R/20
201	setlOgL4QsSHm	reim5NRAeRIKvC	COMPLETE	2022-09-20 14:17:52.135872+05:30	2022-09-20 14:17:52.13592+05:30	1	P/2021/09/R/17
202	setoDPXAbJVKE	reimKMjrt5Alzv	COMPLETE	2022-09-20 14:17:52.135977+05:30	2022-09-20 14:17:52.136007+05:30	1	P/2021/09/R/11
203	setdKKjOsJFQT	reimlmU2VmDQfi	COMPLETE	2022-09-20 14:17:52.136059+05:30	2022-09-20 14:17:52.136089+05:30	1	P/2021/09/R/14
204	setp6F16p8WGG	reimOLyU8dPMIC	COMPLETE	2022-09-20 14:17:52.13614+05:30	2022-09-20 14:17:52.136169+05:30	1	P/2021/09/R/16
205	setKuh6lPAIoU	reimOyBjNfxXl6	COMPLETE	2022-09-20 14:17:52.136218+05:30	2022-09-20 14:17:52.136247+05:30	1	P/2021/09/R/13
206	setiqT5I1nAPC	reimuIJOi0YHFw	COMPLETE	2022-09-20 14:17:52.136296+05:30	2022-09-20 14:17:52.136325+05:30	1	P/2021/09/R/15
207	setmPOMFfkp4F	reimzRqvxvT2Qg	COMPLETE	2022-09-20 14:17:52.136801+05:30	2022-09-20 14:17:52.137067+05:30	1	P/2021/09/R/12
208	setWTpwg4RovE	reim06HLC2nYuL	COMPLETE	2022-09-20 14:17:52.137145+05:30	2022-09-20 14:17:52.137598+05:30	1	P/2021/09/R/8
209	set40zby2tfZG	reim1ZP27BcTtK	COMPLETE	2022-09-20 14:17:52.13782+05:30	2022-09-20 14:17:52.137907+05:30	1	P/2021/09/R/5
210	setjlqb0ijG5p	reimlBDOZSnxnc	COMPLETE	2022-09-20 14:17:52.138065+05:30	2022-09-20 14:17:52.138088+05:30	1	P/2021/09/R/10
211	set1iQc9Aj7FQ	reimRv63PXtevO	COMPLETE	2022-09-20 14:17:52.138139+05:30	2022-09-20 14:17:52.138401+05:30	1	P/2021/09/R/9
212	set5MygblkDjN	reimTaHuQCU51d	COMPLETE	2022-09-20 14:17:52.139025+05:30	2022-09-20 14:17:52.139115+05:30	1	P/2021/09/R/4
213	setEQaoy2E3p5	reimUkyMiLsEJG	COMPLETE	2022-09-20 14:17:52.139169+05:30	2022-09-20 14:17:52.139198+05:30	1	P/2021/09/R/6
214	setljJSrcbhhw	reimyIKJwIBAPf	COMPLETE	2022-09-20 14:17:52.151007+05:30	2022-09-20 14:17:52.151593+05:30	1	P/2021/09/R/7
215	setoUlfPVilij	reimj9nMjpVDjX	COMPLETE	2022-09-20 14:17:52.15176+05:30	2022-09-20 14:17:52.151818+05:30	1	P/2021/09/R/2
216	setPDVdChFccy	reimwa6MME9059	COMPLETE	2022-09-20 14:17:52.152+05:30	2022-09-20 14:17:52.152189+05:30	1	P/2021/09/R/3
217	setRgyGDsFShB	reimyWTvWVgY0D	COMPLETE	2022-09-20 14:17:52.152316+05:30	2022-09-20 14:17:52.152534+05:30	1	P/2021/09/R/1
218	setkZYPYBVfTg	reimFWQZC5E4S0	COMPLETE	2022-09-20 14:17:52.152639+05:30	2022-09-20 14:17:52.152695+05:30	1	P/2021/08/R/6
219	setJJju741FFg	reimnI4LHXlyG7	COMPLETE	2022-09-20 14:17:52.152779+05:30	2022-09-20 14:17:52.152821+05:30	1	P/2021/08/R/7
220	setRISbQrl2qS	reimacWy4G0x7p	COMPLETE	2022-09-20 14:17:52.152896+05:30	2022-09-20 14:17:52.152939+05:30	1	P/2021/07/R/5
221	setoWnez7K7u8	reimG37HYNnSQr	COMPLETE	2022-09-20 14:17:52.153011+05:30	2022-09-20 14:17:52.153051+05:30	1	P/2021/07/R/6
222	set7GTJ65dqXR	reimjH3py8giuH	COMPLETE	2022-09-20 14:17:52.15314+05:30	2022-09-20 14:17:52.15318+05:30	1	P/2021/08/R/2
223	setGDT4k1lQf4	reimlx82ge41YV	COMPLETE	2022-09-20 14:17:52.153253+05:30	2022-09-20 14:17:52.153295+05:30	1	P/2021/08/R/4
224	setqXmQh9Pm0M	reimm6MtpMRnCC	COMPLETE	2022-09-20 14:17:52.15337+05:30	2022-09-20 14:17:52.153412+05:30	1	P/2021/08/R/5
225	setjVNiPVR1jN	reimmI9lRniCJr	COMPLETE	2022-09-20 14:17:52.153491+05:30	2022-09-20 14:17:52.153919+05:30	1	P/2021/08/R/3
226	setCs9kR5F9wG	reimRheySEVfV5	COMPLETE	2022-09-20 14:17:52.154024+05:30	2022-09-20 14:17:52.154058+05:30	1	P/2021/08/R/1
227	set7RuRljR2US	reimtZT3OfpqsH	COMPLETE	2022-09-20 14:17:52.154114+05:30	2022-09-20 14:17:52.154145+05:30	1	P/2021/07/R/7
228	setAkz6uawLzJ	reim0ar7e7cl1B	COMPLETE	2022-09-20 14:17:52.154197+05:30	2022-09-20 14:17:52.154227+05:30	1	P/2021/04/R/5
229	set8bqJuj42zM	reim2ddpn9CgIM	COMPLETE	2022-09-20 14:17:52.154278+05:30	2022-09-20 14:17:52.154307+05:30	1	P/2021/06/R/3
230	setbyBcekbrNS	reim4QHN8bo5dL	COMPLETE	2022-09-20 14:17:52.154357+05:30	2022-09-20 14:17:52.154386+05:30	1	P/2021/04/R/15
231	setHnAi3uuDk4	reim7hf6u5CIsz	COMPLETE	2022-09-20 14:17:52.154435+05:30	2022-09-20 14:17:52.154464+05:30	1	P/2021/04/R/1
232	sethlKpGuwoJ0	reimALBhmYbkZz	COMPLETE	2022-09-20 14:17:52.154769+05:30	2022-09-20 14:17:52.154821+05:30	1	P/2021/04/R/18
233	setpXKES1mcgV	reimApNMfycYDM	COMPLETE	2022-09-20 14:17:52.154906+05:30	2022-09-20 14:17:52.15495+05:30	1	P/2021/04/R/7
234	setzShIVVgOwy	reimAW3UcDsYc9	COMPLETE	2022-09-20 14:17:52.155032+05:30	2022-09-20 14:17:52.155076+05:30	1	P/2021/04/R/10
235	setsFBsWtVA0A	reimbExYNN4uAr	COMPLETE	2022-09-20 14:17:52.155179+05:30	2022-09-20 14:17:52.155333+05:30	1	P/2021/04/R/16
236	set22F2Ujz6bL	reimbRxTUFiuhl	COMPLETE	2022-09-20 14:17:52.155433+05:30	2022-09-20 14:17:52.155477+05:30	1	P/2021/04/R/4
237	setRPTkaLEA6A	reimbT0YDHy6EB	COMPLETE	2022-09-20 14:17:52.155562+05:30	2022-09-20 14:17:52.155603+05:30	1	P/2021/04/R/6
238	setWoXaZ315lj	reimc90pbbk0t3	COMPLETE	2022-09-20 14:17:52.155686+05:30	2022-09-20 14:17:52.155728+05:30	1	P/2021/04/R/19
239	setnVhKqxQBQU	reimCeZihHkHzD	COMPLETE	2022-09-20 14:17:52.155811+05:30	2022-09-20 14:17:52.155854+05:30	1	P/2021/07/R/1
240	setnBGGIIgsXv	reimEyMVFd0b2C	COMPLETE	2022-09-20 14:17:52.155935+05:30	2022-09-20 14:17:52.155977+05:30	1	P/2021/07/R/4
241	setkffhZNy5u8	reimfxqmcofdub	COMPLETE	2022-09-20 14:17:52.156057+05:30	2022-09-20 14:17:52.156099+05:30	1	P/2021/04/R/12
242	setK2qGXUVYeK	reimjc9STOOUXk	COMPLETE	2022-09-20 14:17:52.156176+05:30	2022-09-20 14:17:52.156217+05:30	1	P/2021/06/R/1
243	set1Q9cbXdFpo	reimjoFxMWVjo4	COMPLETE	2022-09-20 14:17:52.156316+05:30	2022-09-20 14:17:52.156504+05:30	1	P/2021/04/R/11
244	setIRZ77y74Iz	reimLT0dYtIS3T	COMPLETE	2022-09-20 14:17:52.156608+05:30	2022-09-20 14:17:52.156654+05:30	1	P/2021/06/R/4
245	setIAJr6wrvqe	reimmMOvMIeJch	COMPLETE	2022-09-20 14:17:52.15674+05:30	2022-09-20 14:17:52.156784+05:30	1	P/2021/07/R/3
246	setiC4kFrWhDq	reimoeF805mwct	COMPLETE	2022-09-20 14:17:52.156865+05:30	2022-09-20 14:17:52.156913+05:30	1	P/2021/04/R/9
247	set4utLw6FooE	reimOO96buaT6r	COMPLETE	2022-09-20 14:17:52.157001+05:30	2022-09-20 14:17:52.157047+05:30	1	P/2021/04/R/14
248	setdp4ha7hDyp	reimOyxJylgV0D	COMPLETE	2022-09-20 14:17:52.157133+05:30	2022-09-20 14:17:52.157179+05:30	1	P/2021/05/R/1
249	setElIlIKoxzB	reimP6wzvtmPz9	COMPLETE	2022-09-20 14:17:52.157259+05:30	2022-09-20 14:17:52.1573+05:30	1	P/2021/04/R/17
250	setYcZpeBJ801	reimrmENfuZaNy	COMPLETE	2022-09-20 14:17:52.157379+05:30	2022-09-20 14:17:52.157421+05:30	1	P/2021/04/R/3
251	set94gxAHNFqi	reimrYLmZPHMid	COMPLETE	2022-09-20 14:17:52.18222+05:30	2022-09-20 14:17:52.182258+05:30	1	P/2021/04/R/8
252	setnyEVTtuz1E	reimswrdQBVx7I	COMPLETE	2022-09-20 14:17:52.18231+05:30	2022-09-20 14:17:52.182325+05:30	1	P/2021/04/R/13
253	setDnWZq3KSJq	reimvET2ReVpzw	COMPLETE	2022-09-20 14:17:52.182368+05:30	2022-09-20 14:17:52.182393+05:30	1	P/2021/06/R/2
254	setTMM90SzQUX	reimVPDY0njHkG	COMPLETE	2022-09-20 14:17:52.182429+05:30	2022-09-20 14:17:52.18245+05:30	1	P/2021/07/R/2
255	setvGxsBVkZh4	reimYTokyRgXGY	COMPLETE	2022-09-20 14:17:52.182501+05:30	2022-09-20 14:17:52.18253+05:30	1	P/2021/04/R/2
256	setzhjuqQ6Pl5	reimYKDswIkdVo	PENDING	2022-09-20 14:21:34.07695+05:30	2022-09-20 14:21:34.077116+05:30	1	P/2022/09/R/19
257	set0SnAq66Zbq	reimRyIMU9MJzg	PENDING	2022-09-20 14:27:03.080411+05:30	2022-09-20 14:27:03.080539+05:30	1	P/2022/09/R/20
258	setzZCuAPxIsB	reimdGLTKKZwpK	PENDING	2022-09-29 17:39:26.484722+05:30	2022-09-29 17:39:26.484765+05:30	1	P/2022/09/R/21
\.


--
-- Data for Name: sage_intacct_credentials; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.sage_intacct_credentials (id, si_user_id, si_company_id, si_company_name, si_user_password, created_at, updated_at, workspace_id) FROM stdin;
1	team_cs	FyleMPP-DEV2	FyleMPP-DEV	gAAAAABjKXwVzRsxpid8IRVcaHGmjh-n8HoNrbe9PgWsXUEGdZ8WMcu9OaV_CFdVsKiyM714fc3hYCZPU4szITy-PZtQQxqU5Q==	2022-09-20 14:08:48.66191+05:30	2022-09-20 14:08:48.661952+05:30	1
\.


--
-- Data for Name: sage_intacct_reimbursement_lineitems; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.sage_intacct_reimbursement_lineitems (id, amount, record_key, created_at, updated_at, sage_intacct_reimbursement_id) FROM stdin;
\.


--
-- Data for Name: sage_intacct_reimbursements; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.sage_intacct_reimbursements (id, account_id, employee_id, memo, payment_description, created_at, updated_at, expense_group_id) FROM stdin;
\.


--
-- Data for Name: task_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.task_logs (id, type, task_id, status, detail, sage_intacct_errors, created_at, updated_at, bill_id, expense_report_id, expense_group_id, workspace_id, charge_card_transaction_id, ap_payment_id, sage_intacct_reimbursement_id, journal_entry_id) FROM stdin;
2	CREATING_BILLS	\N	FAILED	\N	[{"correction": "Use tax details that belong to the tax solution.", "expense_group_id": 1, "long_description": "Tax detail Capital Goods Imported cannot be used in this transaction because it does not belong to tax solution Australia - GST. [Support ID: Y@whFEB036~YzQ2cP0p2Zz-Iv9WTjEPDwAAABY]", "short_description": "Bills error"}, {"correction": "Check the transaction for errors or inconsistencies, then try again.", "expense_group_id": 1, "long_description": "Currently, we can't create the transaction 'Reimbursable expense - C/2022/09/R/21'.", "short_description": "Bills error"}]	2022-09-20 14:18:35.694698+05:30	2022-09-28 17:26:34.693143+05:30	\N	\N	1	1	\N	\N	\N	\N
4	CREATING_BILLS	\N	FAILED	\N	[{"correction": "Use tax details that belong to the tax solution.", "expense_group_id": 3, "long_description": "Tax detail Capital Goods Imported cannot be used in this transaction because it does not belong to tax solution Australia - GST. [Support ID: R8nHGEB032~YzQ2dP0F2Qk-@XXWEOh26wAAAAs]", "short_description": "Bills error"}, {"correction": "Check the transaction for errors or inconsistencies, then try again.", "expense_group_id": 3, "long_description": "Currently, we can't create the transaction 'Corporate Credit Card expense - C/2022/09/R/23 - 28/09/2022'.", "short_description": "Bills error"}]	2022-09-20 14:27:02.308154+05:30	2022-09-28 17:26:37.749629+05:30	\N	\N	3	1	\N	\N	\N	\N
3	CREATING_BILLS	\N	FAILED	\N	[{"correction": "Use tax details that belong to the tax solution.", "expense_group_id": 2, "long_description": "Tax detail Capital Goods Imported cannot be used in this transaction because it does not belong to tax solution Australia - GST. [Support ID: MLsapEB032~YzQ2cP0t2Y9-GgzWugr3IAAAAAU]", "short_description": "Bills error"}, {"correction": "Check the transaction for errors or inconsistencies, then try again.", "expense_group_id": 2, "long_description": "Currently, we can't create the transaction 'Corporate Credit Card expense - C/2022/09/R/22 - 28/09/2022'.", "short_description": "Bills error"}]	2022-09-20 14:21:33.345793+05:30	2022-09-28 17:26:33.933636+05:30	\N	\N	2	1	\N	\N	\N	\N
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (password, last_login, id, email, user_id, full_name, active, staff, admin) FROM stdin;
	\N	1	ashwin.t@fyle.in	usqywo0f3nBY		t	f	f
\.


--
-- Data for Name: workspace_schedules; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.workspace_schedules (id, enabled, start_datetime, interval_hours, schedule_id, workspace_id, additional_email_options, emails_selected, error_count) FROM stdin;
\.


--
-- Data for Name: workspaces; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.workspaces (id, name, fyle_org_id, last_synced_at, created_at, updated_at, destination_synced_at, source_synced_at, cluster_domain, ccc_last_synced_at) FROM stdin;
1	Fyle For Arkham Asylum	or79Cob97KSh	2022-09-20 14:26:50.098426+05:30	2022-09-20 14:08:03.352044+05:30	2022-09-20 14:26:50.098865+05:30	2022-09-28 17:26:39.11276+05:30	2022-09-28 17:25:42.90121+05:30	https://staging.fyle.tech	\N
\.


--
-- Data for Name: workspaces_user; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.workspaces_user (id, workspace_id, user_id) FROM stdin;
1	1	1
\.


--
-- Name: ap_payment_lineitems_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.ap_payment_lineitems_id_seq', 8, true);


--
-- Name: ap_payments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.ap_payments_id_seq', 8, true);


--
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_group_id_seq', 1, false);


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_group_permissions_id_seq', 1, false);


--
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_permission_id_seq', 172, true);


--
-- Name: category_mappings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.category_mappings_id_seq', 140, true);


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_admin_log_id_seq', 1, false);


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_content_type_id_seq', 43, true);


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_migrations_id_seq', 134, true);


--
-- Name: django_q_ormq_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_q_ormq_id_seq', 89, true);


--
-- Name: django_q_schedule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_q_schedule_id_seq', 92, true);


--
-- Name: employee_mappings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.employee_mappings_id_seq', 5, true);


--
-- Name: expense_fields_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.expense_fields_id_seq', 1, false);


--
-- Name: expense_group_settings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.expense_group_settings_id_seq', 5, true);


--
-- Name: fyle_accounting_mappings_destinationattribute_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.fyle_accounting_mappings_destinationattribute_id_seq', 955, true);


--
-- Name: fyle_accounting_mappings_expenseattribute_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.fyle_accounting_mappings_expenseattribute_id_seq', 3278, true);


--
-- Name: fyle_accounting_mappings_mapping_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.fyle_accounting_mappings_mapping_id_seq', 74, true);


--
-- Name: fyle_accounting_mappings_mappingsetting_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.fyle_accounting_mappings_mappingsetting_id_seq', 15, true);


--
-- Name: fyle_expense_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.fyle_expense_id_seq', 13, true);


--
-- Name: fyle_expensegroup_expenses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.fyle_expensegroup_expenses_id_seq', 25, true);


--
-- Name: fyle_expensegroup_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.fyle_expensegroup_id_seq', 9, true);


--
-- Name: fyle_rest_auth_authtokens_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.fyle_rest_auth_authtokens_id_seq', 1, true);


--
-- Name: journal_entries_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.journal_entries_id_seq', 10, true);


--
-- Name: journal_entry_lineitems_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.journal_entry_lineitems_id_seq', 10, true);


--
-- Name: location_entity_mappings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.location_entity_mappings_id_seq', 1, true);


--
-- Name: mappings_generalmapping_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.mappings_generalmapping_id_seq', 1, true);


--
-- Name: reimbursements_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.reimbursements_id_seq', 260, true);


--
-- Name: sage_intacct_bill_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.sage_intacct_bill_id_seq', 24, true);


--
-- Name: sage_intacct_billlineitem_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.sage_intacct_billlineitem_id_seq', 24, true);


--
-- Name: sage_intacct_chargecardtransaction_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.sage_intacct_chargecardtransaction_id_seq', 10, true);


--
-- Name: sage_intacct_chargecardtransactionlineitem_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.sage_intacct_chargecardtransactionlineitem_id_seq', 10, true);


--
-- Name: sage_intacct_expensereport_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.sage_intacct_expensereport_id_seq', 26, true);


--
-- Name: sage_intacct_expensereportlineitem_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.sage_intacct_expensereportlineitem_id_seq', 26, true);


--
-- Name: sage_intacct_reimbursement_lineitems_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.sage_intacct_reimbursement_lineitems_id_seq', 18, true);


--
-- Name: sage_intacct_reimbursements_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.sage_intacct_reimbursements_id_seq', 18, true);


--
-- Name: tasks_tasklog_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tasks_tasklog_id_seq', 42, true);


--
-- Name: users_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_user_id_seq', 15, true);


--
-- Name: workspace_schedules_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.workspace_schedules_id_seq', 6, true);


--
-- Name: workspaces_fylecredential_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.workspaces_fylecredential_id_seq', 3, true);


--
-- Name: workspaces_sageintacctcredential_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.workspaces_sageintacctcredential_id_seq', 3, true);


--
-- Name: workspaces_workspace_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.workspaces_workspace_id_seq', 3, true);


--
-- Name: workspaces_workspace_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.workspaces_workspace_user_id_seq', 4, true);


--
-- Name: workspaces_workspacegeneralsettings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.workspaces_workspacegeneralsettings_id_seq', 3, true);


--
-- Name: ap_payment_lineitems ap_payment_lineitems_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ap_payment_lineitems
    ADD CONSTRAINT ap_payment_lineitems_pkey PRIMARY KEY (id);


--
-- Name: ap_payments ap_payments_expense_group_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ap_payments
    ADD CONSTRAINT ap_payments_expense_group_id_key UNIQUE (expense_group_id);


--
-- Name: ap_payments ap_payments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ap_payments
    ADD CONSTRAINT ap_payments_pkey PRIMARY KEY (id);


--
-- Name: auth_cache auth_cache_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_cache
    ADD CONSTRAINT auth_cache_pkey PRIMARY KEY (cache_key);


--
-- Name: auth_group auth_group_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_name_key UNIQUE (name);


--
-- Name: auth_group_permissions auth_group_permissions_group_id_permission_id_0cd325b0_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_permission_id_0cd325b0_uniq UNIQUE (group_id, permission_id);


--
-- Name: auth_group_permissions auth_group_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_pkey PRIMARY KEY (id);


--
-- Name: auth_group auth_group_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_pkey PRIMARY KEY (id);


--
-- Name: auth_permission auth_permission_content_type_id_codename_01ab375a_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_codename_01ab375a_uniq UNIQUE (content_type_id, codename);


--
-- Name: auth_permission auth_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_pkey PRIMARY KEY (id);


--
-- Name: category_mappings category_mappings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.category_mappings
    ADD CONSTRAINT category_mappings_pkey PRIMARY KEY (id);


--
-- Name: category_mappings category_mappings_source_category_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.category_mappings
    ADD CONSTRAINT category_mappings_source_category_id_key UNIQUE (source_category_id);


--
-- Name: destination_attributes destination_attributes_destination_id_attribute_dfb58751_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.destination_attributes
    ADD CONSTRAINT destination_attributes_destination_id_attribute_dfb58751_uniq UNIQUE (destination_id, attribute_type, workspace_id);


--
-- Name: django_admin_log django_admin_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_pkey PRIMARY KEY (id);


--
-- Name: django_content_type django_content_type_app_label_model_76bd3d3b_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_app_label_model_76bd3d3b_uniq UNIQUE (app_label, model);


--
-- Name: django_content_type django_content_type_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_pkey PRIMARY KEY (id);


--
-- Name: django_migrations django_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_migrations
    ADD CONSTRAINT django_migrations_pkey PRIMARY KEY (id);


--
-- Name: django_q_ormq django_q_ormq_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_q_ormq
    ADD CONSTRAINT django_q_ormq_pkey PRIMARY KEY (id);


--
-- Name: django_q_schedule django_q_schedule_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_q_schedule
    ADD CONSTRAINT django_q_schedule_pkey PRIMARY KEY (id);


--
-- Name: django_q_task django_q_task_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_q_task
    ADD CONSTRAINT django_q_task_pkey PRIMARY KEY (id);


--
-- Name: django_session django_session_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_session
    ADD CONSTRAINT django_session_pkey PRIMARY KEY (session_key);


--
-- Name: employee_mappings employee_mappings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee_mappings
    ADD CONSTRAINT employee_mappings_pkey PRIMARY KEY (id);


--
-- Name: expense_attributes expense_attributes_value_attribute_type_wor_a06aa6b3_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_attributes
    ADD CONSTRAINT expense_attributes_value_attribute_type_wor_a06aa6b3_uniq UNIQUE (value, attribute_type, workspace_id);


--
-- Name: expense_fields expense_fields_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_fields
    ADD CONSTRAINT expense_fields_pkey PRIMARY KEY (id);


--
-- Name: expense_group_settings expense_group_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_group_settings
    ADD CONSTRAINT expense_group_settings_pkey PRIMARY KEY (id);


--
-- Name: expense_group_settings expense_group_settings_workspace_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_group_settings
    ADD CONSTRAINT expense_group_settings_workspace_id_key UNIQUE (workspace_id);


--
-- Name: expense_groups_expenses expense_groups_expenses_expensegroup_id_expense__6a42b67c_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_groups_expenses
    ADD CONSTRAINT expense_groups_expenses_expensegroup_id_expense__6a42b67c_uniq UNIQUE (expensegroup_id, expense_id);


--
-- Name: destination_attributes fyle_accounting_mappings_destinationattribute_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.destination_attributes
    ADD CONSTRAINT fyle_accounting_mappings_destinationattribute_pkey PRIMARY KEY (id);


--
-- Name: expense_attributes fyle_accounting_mappings_expenseattribute_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_attributes
    ADD CONSTRAINT fyle_accounting_mappings_expenseattribute_pkey PRIMARY KEY (id);


--
-- Name: mappings fyle_accounting_mappings_mapping_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mappings
    ADD CONSTRAINT fyle_accounting_mappings_mapping_pkey PRIMARY KEY (id);


--
-- Name: mapping_settings fyle_accounting_mappings_mappingsetting_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mapping_settings
    ADD CONSTRAINT fyle_accounting_mappings_mappingsetting_pkey PRIMARY KEY (id);


--
-- Name: mappings fyle_accounting_mappings_source_type_source_id_de_e40411c3_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mappings
    ADD CONSTRAINT fyle_accounting_mappings_source_type_source_id_de_e40411c3_uniq UNIQUE (source_type, source_id, destination_type, workspace_id);


--
-- Name: expenses fyle_expense_expense_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT fyle_expense_expense_id_key UNIQUE (expense_id);


--
-- Name: expenses fyle_expense_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT fyle_expense_pkey PRIMARY KEY (id);


--
-- Name: expense_groups_expenses fyle_expensegroup_expenses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_groups_expenses
    ADD CONSTRAINT fyle_expensegroup_expenses_pkey PRIMARY KEY (id);


--
-- Name: expense_groups fyle_expensegroup_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_groups
    ADD CONSTRAINT fyle_expensegroup_pkey PRIMARY KEY (id);


--
-- Name: auth_tokens fyle_rest_auth_authtokens_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_tokens
    ADD CONSTRAINT fyle_rest_auth_authtokens_pkey PRIMARY KEY (id);


--
-- Name: auth_tokens fyle_rest_auth_authtokens_user_id_3b4bd82e_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_tokens
    ADD CONSTRAINT fyle_rest_auth_authtokens_user_id_3b4bd82e_uniq UNIQUE (user_id);


--
-- Name: journal_entries journal_entries_expense_group_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.journal_entries
    ADD CONSTRAINT journal_entries_expense_group_id_key UNIQUE (expense_group_id);


--
-- Name: journal_entries journal_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.journal_entries
    ADD CONSTRAINT journal_entries_pkey PRIMARY KEY (id);


--
-- Name: journal_entry_lineitems journal_entry_lineitems_expense_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.journal_entry_lineitems
    ADD CONSTRAINT journal_entry_lineitems_expense_id_key UNIQUE (expense_id);


--
-- Name: journal_entry_lineitems journal_entry_lineitems_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.journal_entry_lineitems
    ADD CONSTRAINT journal_entry_lineitems_pkey PRIMARY KEY (id);


--
-- Name: location_entity_mappings location_entity_mappings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.location_entity_mappings
    ADD CONSTRAINT location_entity_mappings_pkey PRIMARY KEY (id);


--
-- Name: location_entity_mappings location_entity_mappings_workspace_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.location_entity_mappings
    ADD CONSTRAINT location_entity_mappings_workspace_id_key UNIQUE (workspace_id);


--
-- Name: mapping_settings mapping_settings_source_field_destination_cdc65270_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mapping_settings
    ADD CONSTRAINT mapping_settings_source_field_destination_cdc65270_uniq UNIQUE (source_field, destination_field, workspace_id);


--
-- Name: general_mappings mappings_generalmapping_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.general_mappings
    ADD CONSTRAINT mappings_generalmapping_pkey PRIMARY KEY (id);


--
-- Name: reimbursements reimbursements_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reimbursements
    ADD CONSTRAINT reimbursements_pkey PRIMARY KEY (id);


--
-- Name: reimbursements reimbursements_workspace_id_payment_number_4854354c_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reimbursements
    ADD CONSTRAINT reimbursements_workspace_id_payment_number_4854354c_uniq UNIQUE (workspace_id, payment_number);


--
-- Name: bills sage_intacct_bill_expense_group_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bills
    ADD CONSTRAINT sage_intacct_bill_expense_group_id_key UNIQUE (expense_group_id);


--
-- Name: bills sage_intacct_bill_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bills
    ADD CONSTRAINT sage_intacct_bill_pkey PRIMARY KEY (id);


--
-- Name: bill_lineitems sage_intacct_billlineitem_expense_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bill_lineitems
    ADD CONSTRAINT sage_intacct_billlineitem_expense_id_key UNIQUE (expense_id);


--
-- Name: bill_lineitems sage_intacct_billlineitem_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bill_lineitems
    ADD CONSTRAINT sage_intacct_billlineitem_pkey PRIMARY KEY (id);


--
-- Name: charge_card_transactions sage_intacct_chargecardtransaction_expense_group_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.charge_card_transactions
    ADD CONSTRAINT sage_intacct_chargecardtransaction_expense_group_id_key UNIQUE (expense_group_id);


--
-- Name: charge_card_transactions sage_intacct_chargecardtransaction_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.charge_card_transactions
    ADD CONSTRAINT sage_intacct_chargecardtransaction_pkey PRIMARY KEY (id);


--
-- Name: charge_card_transaction_lineitems sage_intacct_chargecardtransactionlineitem_expense_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.charge_card_transaction_lineitems
    ADD CONSTRAINT sage_intacct_chargecardtransactionlineitem_expense_id_key UNIQUE (expense_id);


--
-- Name: charge_card_transaction_lineitems sage_intacct_chargecardtransactionlineitem_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.charge_card_transaction_lineitems
    ADD CONSTRAINT sage_intacct_chargecardtransactionlineitem_pkey PRIMARY KEY (id);


--
-- Name: expense_reports sage_intacct_expensereport_expense_group_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_reports
    ADD CONSTRAINT sage_intacct_expensereport_expense_group_id_key UNIQUE (expense_group_id);


--
-- Name: expense_reports sage_intacct_expensereport_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_reports
    ADD CONSTRAINT sage_intacct_expensereport_pkey PRIMARY KEY (id);


--
-- Name: expense_report_lineitems sage_intacct_expensereportlineitem_expense_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_report_lineitems
    ADD CONSTRAINT sage_intacct_expensereportlineitem_expense_id_key UNIQUE (expense_id);


--
-- Name: expense_report_lineitems sage_intacct_expensereportlineitem_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_report_lineitems
    ADD CONSTRAINT sage_intacct_expensereportlineitem_pkey PRIMARY KEY (id);


--
-- Name: sage_intacct_reimbursement_lineitems sage_intacct_reimbursement_lineitems_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sage_intacct_reimbursement_lineitems
    ADD CONSTRAINT sage_intacct_reimbursement_lineitems_pkey PRIMARY KEY (id);


--
-- Name: sage_intacct_reimbursements sage_intacct_reimbursements_expense_group_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sage_intacct_reimbursements
    ADD CONSTRAINT sage_intacct_reimbursements_expense_group_id_key UNIQUE (expense_group_id);


--
-- Name: sage_intacct_reimbursements sage_intacct_reimbursements_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sage_intacct_reimbursements
    ADD CONSTRAINT sage_intacct_reimbursements_pkey PRIMARY KEY (id);


--
-- Name: task_logs tasks_tasklog_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_logs
    ADD CONSTRAINT tasks_tasklog_pkey PRIMARY KEY (id);


--
-- Name: users users_user_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_user_pkey PRIMARY KEY (id);


--
-- Name: users users_user_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_user_user_id_key UNIQUE (user_id);


--
-- Name: workspace_schedules workspace_schedules_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workspace_schedules
    ADD CONSTRAINT workspace_schedules_pkey PRIMARY KEY (id);


--
-- Name: workspace_schedules workspace_schedules_schedule_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workspace_schedules
    ADD CONSTRAINT workspace_schedules_schedule_id_key UNIQUE (schedule_id);


--
-- Name: workspace_schedules workspace_schedules_workspace_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workspace_schedules
    ADD CONSTRAINT workspace_schedules_workspace_id_key UNIQUE (workspace_id);


--
-- Name: fyle_credentials workspaces_fylecredential_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fyle_credentials
    ADD CONSTRAINT workspaces_fylecredential_pkey PRIMARY KEY (id);


--
-- Name: fyle_credentials workspaces_fylecredential_workspace_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fyle_credentials
    ADD CONSTRAINT workspaces_fylecredential_workspace_id_key UNIQUE (workspace_id);


--
-- Name: sage_intacct_credentials workspaces_sageintacctcredential_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sage_intacct_credentials
    ADD CONSTRAINT workspaces_sageintacctcredential_pkey PRIMARY KEY (id);


--
-- Name: sage_intacct_credentials workspaces_sageintacctcredential_workspace_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sage_intacct_credentials
    ADD CONSTRAINT workspaces_sageintacctcredential_workspace_id_key UNIQUE (workspace_id);


--
-- Name: workspaces_user workspaces_user_workspace_id_user_id_aee37428_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workspaces_user
    ADD CONSTRAINT workspaces_user_workspace_id_user_id_aee37428_uniq UNIQUE (workspace_id, user_id);


--
-- Name: workspaces workspaces_workspace_fyle_org_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workspaces
    ADD CONSTRAINT workspaces_workspace_fyle_org_id_key UNIQUE (fyle_org_id);


--
-- Name: workspaces workspaces_workspace_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workspaces
    ADD CONSTRAINT workspaces_workspace_pkey PRIMARY KEY (id);


--
-- Name: workspaces_user workspaces_workspace_user_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workspaces_user
    ADD CONSTRAINT workspaces_workspace_user_pkey PRIMARY KEY (id);


--
-- Name: configurations workspaces_workspacegeneralsettings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.configurations
    ADD CONSTRAINT workspaces_workspacegeneralsettings_pkey PRIMARY KEY (id);


--
-- Name: configurations workspaces_workspacegeneralsettings_workspace_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.configurations
    ADD CONSTRAINT workspaces_workspacegeneralsettings_workspace_id_key UNIQUE (workspace_id);


--
-- Name: ap_payment_lineitems_ap_payment_id_c7f4cfd8; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ap_payment_lineitems_ap_payment_id_c7f4cfd8 ON public.ap_payment_lineitems USING btree (ap_payment_id);


--
-- Name: auth_cache_expires; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_cache_expires ON public.auth_cache USING btree (expires);


--
-- Name: auth_group_name_a6ea08ec_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_group_name_a6ea08ec_like ON public.auth_group USING btree (name varchar_pattern_ops);


--
-- Name: auth_group_permissions_group_id_b120cbf9; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_group_permissions_group_id_b120cbf9 ON public.auth_group_permissions USING btree (group_id);


--
-- Name: auth_group_permissions_permission_id_84c5c92e; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_group_permissions_permission_id_84c5c92e ON public.auth_group_permissions USING btree (permission_id);


--
-- Name: auth_permission_content_type_id_2f476e4b; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_permission_content_type_id_2f476e4b ON public.auth_permission USING btree (content_type_id);


--
-- Name: bill_lineitems_bill_id_8d61e31f; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX bill_lineitems_bill_id_8d61e31f ON public.bill_lineitems USING btree (bill_id);


--
-- Name: category_mappings_destination_account_id_ebc44c1c; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX category_mappings_destination_account_id_ebc44c1c ON public.category_mappings USING btree (destination_account_id);


--
-- Name: category_mappings_destination_expense_head_id_0ed87fbd; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX category_mappings_destination_expense_head_id_0ed87fbd ON public.category_mappings USING btree (destination_expense_head_id);


--
-- Name: category_mappings_workspace_id_222ea301; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX category_mappings_workspace_id_222ea301 ON public.category_mappings USING btree (workspace_id);


--
-- Name: charge_card_transaction_li_charge_card_transaction_id_508bf6be; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX charge_card_transaction_li_charge_card_transaction_id_508bf6be ON public.charge_card_transaction_lineitems USING btree (charge_card_transaction_id);


--
-- Name: django_admin_log_content_type_id_c4bce8eb; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_admin_log_content_type_id_c4bce8eb ON public.django_admin_log USING btree (content_type_id);


--
-- Name: django_admin_log_user_id_c564eba6; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_admin_log_user_id_c564eba6 ON public.django_admin_log USING btree (user_id);


--
-- Name: django_q_task_id_32882367_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_q_task_id_32882367_like ON public.django_q_task USING btree (id varchar_pattern_ops);


--
-- Name: django_session_expire_date_a5c62663; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_session_expire_date_a5c62663 ON public.django_session USING btree (expire_date);


--
-- Name: django_session_session_key_c0390e0f_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_session_session_key_c0390e0f_like ON public.django_session USING btree (session_key varchar_pattern_ops);


--
-- Name: employee_mappings_destination_card_account_id_f030b899; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX employee_mappings_destination_card_account_id_f030b899 ON public.employee_mappings USING btree (destination_card_account_id);


--
-- Name: employee_mappings_destination_employee_id_b6764819; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX employee_mappings_destination_employee_id_b6764819 ON public.employee_mappings USING btree (destination_employee_id);


--
-- Name: employee_mappings_destination_vendor_id_c4bd73df; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX employee_mappings_destination_vendor_id_c4bd73df ON public.employee_mappings USING btree (destination_vendor_id);


--
-- Name: employee_mappings_source_employee_id_dd9948ba; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX employee_mappings_source_employee_id_dd9948ba ON public.employee_mappings USING btree (source_employee_id);


--
-- Name: employee_mappings_workspace_id_4a25f8c9; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX employee_mappings_workspace_id_4a25f8c9 ON public.employee_mappings USING btree (workspace_id);


--
-- Name: expense_fields_workspace_id_b60af18c; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX expense_fields_workspace_id_b60af18c ON public.expense_fields USING btree (workspace_id);


--
-- Name: expense_groups_expenses_expense_id_af963907; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX expense_groups_expenses_expense_id_af963907 ON public.expense_groups_expenses USING btree (expense_id);


--
-- Name: expense_groups_expenses_expensegroup_id_c5b379a2; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX expense_groups_expenses_expensegroup_id_c5b379a2 ON public.expense_groups_expenses USING btree (expensegroup_id);


--
-- Name: expense_groups_workspace_id_21fcb4ac; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX expense_groups_workspace_id_21fcb4ac ON public.expense_groups USING btree (workspace_id);


--
-- Name: expense_report_lineitems_expense_report_id_4c7e2508; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX expense_report_lineitems_expense_report_id_4c7e2508 ON public.expense_report_lineitems USING btree (expense_report_id);


--
-- Name: expenses_expense_id_0e3511ea_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX expenses_expense_id_0e3511ea_like ON public.expenses USING btree (expense_id varchar_pattern_ops);


--
-- Name: fyle_accounting_mappings_d_workspace_id_a6a3ab6a; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX fyle_accounting_mappings_d_workspace_id_a6a3ab6a ON public.destination_attributes USING btree (workspace_id);


--
-- Name: fyle_accounting_mappings_expenseattribute_workspace_id_4364b6d7; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX fyle_accounting_mappings_expenseattribute_workspace_id_4364b6d7 ON public.expense_attributes USING btree (workspace_id);


--
-- Name: fyle_accounting_mappings_mapping_destination_id_79497f6e; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX fyle_accounting_mappings_mapping_destination_id_79497f6e ON public.mappings USING btree (destination_id);


--
-- Name: fyle_accounting_mappings_mapping_source_id_7d692c36; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX fyle_accounting_mappings_mapping_source_id_7d692c36 ON public.mappings USING btree (source_id);


--
-- Name: fyle_accounting_mappings_mapping_workspace_id_10d6edd3; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX fyle_accounting_mappings_mapping_workspace_id_10d6edd3 ON public.mappings USING btree (workspace_id);


--
-- Name: fyle_accounting_mappings_mappingsetting_workspace_id_c123c088; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX fyle_accounting_mappings_mappingsetting_workspace_id_c123c088 ON public.mapping_settings USING btree (workspace_id);


--
-- Name: general_mappings_workspace_id_19666c5c; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX general_mappings_workspace_id_19666c5c ON public.general_mappings USING btree (workspace_id);


--
-- Name: journal_entry_lineitems_journal_entry_id_382a8abe; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX journal_entry_lineitems_journal_entry_id_382a8abe ON public.journal_entry_lineitems USING btree (journal_entry_id);


--
-- Name: mapping_settings_expense_field_id_e9afc6c2; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX mapping_settings_expense_field_id_e9afc6c2 ON public.mapping_settings USING btree (expense_field_id);


--
-- Name: reimbursements_workspace_id_084805e4; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX reimbursements_workspace_id_084805e4 ON public.reimbursements USING btree (workspace_id);


--
-- Name: sage_intacct_reimbursement_sage_intacct_reimbursement_96b8e4d9; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX sage_intacct_reimbursement_sage_intacct_reimbursement_96b8e4d9 ON public.sage_intacct_reimbursement_lineitems USING btree (sage_intacct_reimbursement_id);


--
-- Name: task_logs_ap_payment_id_51b8a8b4; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX task_logs_ap_payment_id_51b8a8b4 ON public.task_logs USING btree (ap_payment_id);


--
-- Name: task_logs_bill_id_f4fc5218; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX task_logs_bill_id_f4fc5218 ON public.task_logs USING btree (bill_id);


--
-- Name: task_logs_charge_card_transaction_id_0a86b771; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX task_logs_charge_card_transaction_id_0a86b771 ON public.task_logs USING btree (charge_card_transaction_id);


--
-- Name: task_logs_expense_group_id_f19c75f9; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX task_logs_expense_group_id_f19c75f9 ON public.task_logs USING btree (expense_group_id);


--
-- Name: task_logs_expense_report_id_0eda6a81; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX task_logs_expense_report_id_0eda6a81 ON public.task_logs USING btree (expense_report_id);


--
-- Name: task_logs_journal_entry_id_8c699a31; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX task_logs_journal_entry_id_8c699a31 ON public.task_logs USING btree (journal_entry_id);


--
-- Name: task_logs_sage_intacct_reimbursement_id_d336c210; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX task_logs_sage_intacct_reimbursement_id_d336c210 ON public.task_logs USING btree (sage_intacct_reimbursement_id);


--
-- Name: task_logs_workspace_id_d6109445; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX task_logs_workspace_id_d6109445 ON public.task_logs USING btree (workspace_id);


--
-- Name: users_user_user_id_4120b7b9_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX users_user_user_id_4120b7b9_like ON public.users USING btree (user_id varchar_pattern_ops);


--
-- Name: workspaces_fyle_org_id_a77e6782_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX workspaces_fyle_org_id_a77e6782_like ON public.workspaces USING btree (fyle_org_id varchar_pattern_ops);


--
-- Name: workspaces_user_user_id_4253baf7; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX workspaces_user_user_id_4253baf7 ON public.workspaces_user USING btree (user_id);


--
-- Name: workspaces_user_workspace_id_be6c5867; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX workspaces_user_workspace_id_be6c5867 ON public.workspaces_user USING btree (workspace_id);


--
-- Name: ap_payment_lineitems ap_payment_lineitems_ap_payment_id_c7f4cfd8_fk_ap_payments_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ap_payment_lineitems
    ADD CONSTRAINT ap_payment_lineitems_ap_payment_id_c7f4cfd8_fk_ap_payments_id FOREIGN KEY (ap_payment_id) REFERENCES public.ap_payments(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: ap_payments ap_payments_expense_group_id_9e5dd4dc_fk_expense_groups_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ap_payments
    ADD CONSTRAINT ap_payments_expense_group_id_9e5dd4dc_fk_expense_groups_id FOREIGN KEY (expense_group_id) REFERENCES public.expense_groups(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permissions auth_group_permissio_permission_id_84c5c92e_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissio_permission_id_84c5c92e_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permissions auth_group_permissions_group_id_b120cbf9_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_b120cbf9_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_permission auth_permission_content_type_id_2f476e4b_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_2f476e4b_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: bill_lineitems bill_lineitems_bill_id_8d61e31f_fk_bills_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bill_lineitems
    ADD CONSTRAINT bill_lineitems_bill_id_8d61e31f_fk_bills_id FOREIGN KEY (bill_id) REFERENCES public.bills(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: bill_lineitems bill_lineitems_expense_id_fc7ff7c3_fk_expenses_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bill_lineitems
    ADD CONSTRAINT bill_lineitems_expense_id_fc7ff7c3_fk_expenses_id FOREIGN KEY (expense_id) REFERENCES public.expenses(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: bills bills_expense_group_id_245e4cc1_fk_expense_groups_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bills
    ADD CONSTRAINT bills_expense_group_id_245e4cc1_fk_expense_groups_id FOREIGN KEY (expense_group_id) REFERENCES public.expense_groups(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: category_mappings category_mappings_destination_account__ebc44c1c_fk_destinati; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.category_mappings
    ADD CONSTRAINT category_mappings_destination_account__ebc44c1c_fk_destinati FOREIGN KEY (destination_account_id) REFERENCES public.destination_attributes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: category_mappings category_mappings_destination_expense__0ed87fbd_fk_destinati; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.category_mappings
    ADD CONSTRAINT category_mappings_destination_expense__0ed87fbd_fk_destinati FOREIGN KEY (destination_expense_head_id) REFERENCES public.destination_attributes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: category_mappings category_mappings_source_category_id_46f19d95_fk_expense_a; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.category_mappings
    ADD CONSTRAINT category_mappings_source_category_id_46f19d95_fk_expense_a FOREIGN KEY (source_category_id) REFERENCES public.expense_attributes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: category_mappings category_mappings_workspace_id_222ea301_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.category_mappings
    ADD CONSTRAINT category_mappings_workspace_id_222ea301_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: charge_card_transaction_lineitems charge_card_transact_charge_card_transact_508bf6be_fk_charge_ca; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.charge_card_transaction_lineitems
    ADD CONSTRAINT charge_card_transact_charge_card_transact_508bf6be_fk_charge_ca FOREIGN KEY (charge_card_transaction_id) REFERENCES public.charge_card_transactions(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: charge_card_transactions charge_card_transact_expense_group_id_a00fb88a_fk_expense_g; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.charge_card_transactions
    ADD CONSTRAINT charge_card_transact_expense_group_id_a00fb88a_fk_expense_g FOREIGN KEY (expense_group_id) REFERENCES public.expense_groups(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: charge_card_transaction_lineitems charge_card_transact_expense_id_d662cef7_fk_expenses_; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.charge_card_transaction_lineitems
    ADD CONSTRAINT charge_card_transact_expense_id_d662cef7_fk_expenses_ FOREIGN KEY (expense_id) REFERENCES public.expenses(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log django_admin_log_content_type_id_c4bce8eb_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_content_type_id_c4bce8eb_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log django_admin_log_user_id_c564eba6_fk_users_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_user_id_c564eba6_fk_users_user_id FOREIGN KEY (user_id) REFERENCES public.users(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: employee_mappings employee_mappings_destination_card_acc_f030b899_fk_destinati; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee_mappings
    ADD CONSTRAINT employee_mappings_destination_card_acc_f030b899_fk_destinati FOREIGN KEY (destination_card_account_id) REFERENCES public.destination_attributes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: employee_mappings employee_mappings_destination_employee_b6764819_fk_destinati; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee_mappings
    ADD CONSTRAINT employee_mappings_destination_employee_b6764819_fk_destinati FOREIGN KEY (destination_employee_id) REFERENCES public.destination_attributes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: employee_mappings employee_mappings_destination_vendor_i_c4bd73df_fk_destinati; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee_mappings
    ADD CONSTRAINT employee_mappings_destination_vendor_i_c4bd73df_fk_destinati FOREIGN KEY (destination_vendor_id) REFERENCES public.destination_attributes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: employee_mappings employee_mappings_source_employee_id_dd9948ba_fk_expense_a; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee_mappings
    ADD CONSTRAINT employee_mappings_source_employee_id_dd9948ba_fk_expense_a FOREIGN KEY (source_employee_id) REFERENCES public.expense_attributes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: employee_mappings employee_mappings_workspace_id_4a25f8c9_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee_mappings
    ADD CONSTRAINT employee_mappings_workspace_id_4a25f8c9_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: expense_fields expense_fields_workspace_id_b60af18c_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_fields
    ADD CONSTRAINT expense_fields_workspace_id_b60af18c_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: expense_group_settings expense_group_settings_workspace_id_4c110bbe_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_group_settings
    ADD CONSTRAINT expense_group_settings_workspace_id_4c110bbe_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: expense_groups_expenses expense_groups_expen_expensegroup_id_c5b379a2_fk_expense_g; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_groups_expenses
    ADD CONSTRAINT expense_groups_expen_expensegroup_id_c5b379a2_fk_expense_g FOREIGN KEY (expensegroup_id) REFERENCES public.expense_groups(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: expense_groups_expenses expense_groups_expenses_expense_id_af963907_fk_expenses_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_groups_expenses
    ADD CONSTRAINT expense_groups_expenses_expense_id_af963907_fk_expenses_id FOREIGN KEY (expense_id) REFERENCES public.expenses(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: expense_groups expense_groups_workspace_id_21fcb4ac_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_groups
    ADD CONSTRAINT expense_groups_workspace_id_21fcb4ac_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: expense_report_lineitems expense_report_linei_expense_report_id_4c7e2508_fk_expense_r; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_report_lineitems
    ADD CONSTRAINT expense_report_linei_expense_report_id_4c7e2508_fk_expense_r FOREIGN KEY (expense_report_id) REFERENCES public.expense_reports(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: expense_report_lineitems expense_report_lineitems_expense_id_847445bc_fk_expenses_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_report_lineitems
    ADD CONSTRAINT expense_report_lineitems_expense_id_847445bc_fk_expenses_id FOREIGN KEY (expense_id) REFERENCES public.expenses(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: expense_reports expense_reports_expense_group_id_3f864e9a_fk_expense_groups_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_reports
    ADD CONSTRAINT expense_reports_expense_group_id_3f864e9a_fk_expense_groups_id FOREIGN KEY (expense_group_id) REFERENCES public.expense_groups(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: mappings fyle_accounting_mapp_destination_id_79497f6e_fk_fyle_acco; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mappings
    ADD CONSTRAINT fyle_accounting_mapp_destination_id_79497f6e_fk_fyle_acco FOREIGN KEY (destination_id) REFERENCES public.destination_attributes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: mappings fyle_accounting_mapp_workspace_id_10d6edd3_fk_workspace; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mappings
    ADD CONSTRAINT fyle_accounting_mapp_workspace_id_10d6edd3_fk_workspace FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: expense_attributes fyle_accounting_mapp_workspace_id_4364b6d7_fk_workspace; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_attributes
    ADD CONSTRAINT fyle_accounting_mapp_workspace_id_4364b6d7_fk_workspace FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: destination_attributes fyle_accounting_mapp_workspace_id_a6a3ab6a_fk_workspace; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.destination_attributes
    ADD CONSTRAINT fyle_accounting_mapp_workspace_id_a6a3ab6a_fk_workspace FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: fyle_credentials fyle_credentials_workspace_id_52f7febf_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fyle_credentials
    ADD CONSTRAINT fyle_credentials_workspace_id_52f7febf_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_tokens fyle_rest_auth_authtokens_user_id_3b4bd82e_fk_users_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_tokens
    ADD CONSTRAINT fyle_rest_auth_authtokens_user_id_3b4bd82e_fk_users_user_id FOREIGN KEY (user_id) REFERENCES public.users(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: general_mappings general_mappings_workspace_id_19666c5c_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.general_mappings
    ADD CONSTRAINT general_mappings_workspace_id_19666c5c_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: configurations general_settings_workspace_id_091a11f5_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.configurations
    ADD CONSTRAINT general_settings_workspace_id_091a11f5_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: journal_entries journal_entries_expense_group_id_6cdaa98b_fk_expense_groups_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.journal_entries
    ADD CONSTRAINT journal_entries_expense_group_id_6cdaa98b_fk_expense_groups_id FOREIGN KEY (expense_group_id) REFERENCES public.expense_groups(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: journal_entry_lineitems journal_entry_lineit_journal_entry_id_382a8abe_fk_journal_e; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.journal_entry_lineitems
    ADD CONSTRAINT journal_entry_lineit_journal_entry_id_382a8abe_fk_journal_e FOREIGN KEY (journal_entry_id) REFERENCES public.journal_entries(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: journal_entry_lineitems journal_entry_lineitems_expense_id_5a5ca4ff_fk_expenses_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.journal_entry_lineitems
    ADD CONSTRAINT journal_entry_lineitems_expense_id_5a5ca4ff_fk_expenses_id FOREIGN KEY (expense_id) REFERENCES public.expenses(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: location_entity_mappings location_entity_mappings_workspace_id_efc692f9_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.location_entity_mappings
    ADD CONSTRAINT location_entity_mappings_workspace_id_efc692f9_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: mapping_settings mapping_settings_expense_field_id_e9afc6c2_fk_expense_fields_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mapping_settings
    ADD CONSTRAINT mapping_settings_expense_field_id_e9afc6c2_fk_expense_fields_id FOREIGN KEY (expense_field_id) REFERENCES public.expense_fields(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: mapping_settings mapping_settings_workspace_id_590f14f3_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mapping_settings
    ADD CONSTRAINT mapping_settings_workspace_id_590f14f3_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: mappings mappings_source_id_fd4f378f_fk_expense_attributes_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mappings
    ADD CONSTRAINT mappings_source_id_fd4f378f_fk_expense_attributes_id FOREIGN KEY (source_id) REFERENCES public.expense_attributes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reimbursements reimbursements_workspace_id_084805e4_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reimbursements
    ADD CONSTRAINT reimbursements_workspace_id_084805e4_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: sage_intacct_credentials sage_intacct_credentials_workspace_id_119b2476_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sage_intacct_credentials
    ADD CONSTRAINT sage_intacct_credentials_workspace_id_119b2476_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: sage_intacct_reimbursements sage_intacct_reimbur_expense_group_id_c6b34ea2_fk_expense_g; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sage_intacct_reimbursements
    ADD CONSTRAINT sage_intacct_reimbur_expense_group_id_c6b34ea2_fk_expense_g FOREIGN KEY (expense_group_id) REFERENCES public.expense_groups(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: sage_intacct_reimbursement_lineitems sage_intacct_reimbur_sage_intacct_reimbur_96b8e4d9_fk_sage_inta; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sage_intacct_reimbursement_lineitems
    ADD CONSTRAINT sage_intacct_reimbur_sage_intacct_reimbur_96b8e4d9_fk_sage_inta FOREIGN KEY (sage_intacct_reimbursement_id) REFERENCES public.sage_intacct_reimbursements(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: task_logs task_logs_ap_payment_id_51b8a8b4_fk_ap_payments_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_logs
    ADD CONSTRAINT task_logs_ap_payment_id_51b8a8b4_fk_ap_payments_id FOREIGN KEY (ap_payment_id) REFERENCES public.ap_payments(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: task_logs task_logs_bill_id_f4fc5218_fk_bills_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_logs
    ADD CONSTRAINT task_logs_bill_id_f4fc5218_fk_bills_id FOREIGN KEY (bill_id) REFERENCES public.bills(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: task_logs task_logs_charge_card_transact_0a86b771_fk_charge_ca; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_logs
    ADD CONSTRAINT task_logs_charge_card_transact_0a86b771_fk_charge_ca FOREIGN KEY (charge_card_transaction_id) REFERENCES public.charge_card_transactions(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: task_logs task_logs_expense_group_id_f19c75f9_fk_expense_groups_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_logs
    ADD CONSTRAINT task_logs_expense_group_id_f19c75f9_fk_expense_groups_id FOREIGN KEY (expense_group_id) REFERENCES public.expense_groups(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: task_logs task_logs_expense_report_id_0eda6a81_fk_expense_reports_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_logs
    ADD CONSTRAINT task_logs_expense_report_id_0eda6a81_fk_expense_reports_id FOREIGN KEY (expense_report_id) REFERENCES public.expense_reports(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: task_logs task_logs_journal_entry_id_8c699a31_fk_journal_entries_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_logs
    ADD CONSTRAINT task_logs_journal_entry_id_8c699a31_fk_journal_entries_id FOREIGN KEY (journal_entry_id) REFERENCES public.journal_entries(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: task_logs task_logs_sage_intacct_reimbur_d336c210_fk_sage_inta; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_logs
    ADD CONSTRAINT task_logs_sage_intacct_reimbur_d336c210_fk_sage_inta FOREIGN KEY (sage_intacct_reimbursement_id) REFERENCES public.sage_intacct_reimbursements(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: task_logs task_logs_workspace_id_d6109445_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_logs
    ADD CONSTRAINT task_logs_workspace_id_d6109445_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: workspace_schedules workspace_schedules_schedule_id_70b3d838_fk_django_q_; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workspace_schedules
    ADD CONSTRAINT workspace_schedules_schedule_id_70b3d838_fk_django_q_ FOREIGN KEY (schedule_id) REFERENCES public.django_q_schedule(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: workspace_schedules workspace_schedules_workspace_id_50ec990f_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workspace_schedules
    ADD CONSTRAINT workspace_schedules_workspace_id_50ec990f_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: workspaces_user workspaces_user_user_id_4253baf7_fk_users_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workspaces_user
    ADD CONSTRAINT workspaces_user_user_id_4253baf7_fk_users_user_id FOREIGN KEY (user_id) REFERENCES public.users(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: workspaces_user workspaces_user_workspace_id_be6c5867_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workspaces_user
    ADD CONSTRAINT workspaces_user_workspace_id_be6c5867_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- PostgreSQL database dump complete
--

