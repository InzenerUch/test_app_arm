--
-- PostgreSQL database dump
--

\restrict ulNjv2jhqaHAnQqGT6zdRBMsXJ6m2CQgrVvXp6nkiljkpmdwaB4Ydo6uecRq3Ih

-- Dumped from database version 16.13 (Ubuntu 16.13-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.13 (Ubuntu 16.13-0ubuntu0.24.04.1)

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

--
-- Name: krd; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA krd;


ALTER SCHEMA krd OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: addresses; Type: TABLE; Schema: krd; Owner: postgres
--

CREATE TABLE krd.addresses (
    id integer NOT NULL,
    krd_id integer NOT NULL,
    region character varying(100),
    district character varying(100),
    town character varying(100),
    street character varying(100),
    house character varying(50),
    building character varying(50),
    letter character varying(10),
    apartment character varying(50),
    room character varying(50),
    check_date date,
    check_result text
);


ALTER TABLE krd.addresses OWNER TO postgres;

--
-- Name: TABLE addresses; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON TABLE krd.addresses IS 'Адреса проживания военнослужащих';


--
-- Name: COLUMN addresses.id; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.addresses.id IS 'Идентификатор адреса проживания';


--
-- Name: COLUMN addresses.krd_id; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.addresses.krd_id IS 'Ссылка на КРД';


--
-- Name: addresses_id_seq; Type: SEQUENCE; Schema: krd; Owner: postgres
--

CREATE SEQUENCE krd.addresses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE krd.addresses_id_seq OWNER TO postgres;

--
-- Name: addresses_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: postgres
--

ALTER SEQUENCE krd.addresses_id_seq OWNED BY krd.addresses.id;


--
-- Name: audit_log; Type: TABLE; Schema: krd; Owner: postgres
--

CREATE TABLE krd.audit_log (
    id integer NOT NULL,
    user_id integer NOT NULL,
    username character varying(100) NOT NULL,
    action_type character varying(50) NOT NULL,
    table_name character varying(100) NOT NULL,
    record_id integer,
    krd_id integer,
    old_values jsonb,
    new_values jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    description text
);


ALTER TABLE krd.audit_log OWNER TO postgres;

--
-- Name: TABLE audit_log; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON TABLE krd.audit_log IS 'Журнал аудита действий пользователей';


--
-- Name: COLUMN audit_log.id; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.audit_log.id IS 'Идентификатор записи аудита';


--
-- Name: COLUMN audit_log.user_id; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.audit_log.user_id IS 'ID пользователя из таблицы users';


--
-- Name: COLUMN audit_log.username; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.audit_log.username IS 'Имя пользователя (для истории)';


--
-- Name: COLUMN audit_log.action_type; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.audit_log.action_type IS 'Тип действия: CREATE, UPDATE, DELETE, VIEW, LOGIN, LOGOUT, EXPORT и т.д.';


--
-- Name: COLUMN audit_log.table_name; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.audit_log.table_name IS 'Название таблицы, в которой произошло изменение';


--
-- Name: COLUMN audit_log.record_id; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.audit_log.record_id IS 'ID измененной записи';


--
-- Name: COLUMN audit_log.krd_id; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.audit_log.krd_id IS 'ID КРД (для удобства фильтрации по карточкам)';


--
-- Name: COLUMN audit_log.old_values; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.audit_log.old_values IS 'Старые значения в формате JSON';


--
-- Name: COLUMN audit_log.new_values; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.audit_log.new_values IS 'Новые значения в формате JSON';


--
-- Name: COLUMN audit_log.created_at; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.audit_log.created_at IS 'Дата и время действия';


--
-- Name: audit_log_id_seq; Type: SEQUENCE; Schema: krd; Owner: postgres
--

CREATE SEQUENCE krd.audit_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE krd.audit_log_id_seq OWNER TO postgres;

--
-- Name: audit_log_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: postgres
--

ALTER SEQUENCE krd.audit_log_id_seq OWNED BY krd.audit_log.id;


--
-- Name: categories; Type: TABLE; Schema: krd; Owner: postgres
--

CREATE TABLE krd.categories (
    id integer NOT NULL,
    name character varying(100) NOT NULL
);


ALTER TABLE krd.categories OWNER TO postgres;

--
-- Name: TABLE categories; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON TABLE krd.categories IS 'Справочник категорий военнослужащих';


--
-- Name: COLUMN categories.id; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.categories.id IS 'Идентификатор категории';


--
-- Name: COLUMN categories.name; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.categories.name IS 'Категория военнослужащего';


--
-- Name: categories_id_seq; Type: SEQUENCE; Schema: krd; Owner: postgres
--

CREATE SEQUENCE krd.categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE krd.categories_id_seq OWNER TO postgres;

--
-- Name: categories_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: postgres
--

ALTER SEQUENCE krd.categories_id_seq OWNED BY krd.categories.id;


--
-- Name: document_templates; Type: TABLE; Schema: krd; Owner: postgres
--

CREATE TABLE krd.document_templates (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    template_data bytea NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_deleted boolean DEFAULT false,
    deleted_at timestamp without time zone,
    deleted_by integer
);


ALTER TABLE krd.document_templates OWNER TO postgres;

--
-- Name: document_templates_id_seq; Type: SEQUENCE; Schema: krd; Owner: postgres
--

CREATE SEQUENCE krd.document_templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE krd.document_templates_id_seq OWNER TO postgres;

--
-- Name: document_templates_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: postgres
--

ALTER SEQUENCE krd.document_templates_id_seq OWNED BY krd.document_templates.id;


--
-- Name: field_mappings; Type: TABLE; Schema: krd; Owner: postgres
--

CREATE TABLE krd.field_mappings (
    id integer NOT NULL,
    template_id integer,
    field_name character varying(255) NOT NULL,
    db_column character varying(255) NOT NULL,
    table_name character varying(255) NOT NULL,
    description text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    db_columns jsonb,
    is_composite boolean DEFAULT false
);


ALTER TABLE krd.field_mappings OWNER TO postgres;

--
-- Name: COLUMN field_mappings.db_columns; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.field_mappings.db_columns IS 'JSONB массив столбцов для составных полей: [{"column": "town", "separator": ", "}, {"column": "street", "separator": ", "}, {"column": "house", "separator": ""}]';


--
-- Name: COLUMN field_mappings.is_composite; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.field_mappings.is_composite IS 'Флаг составного поля (объединяет несколько столбцов)';


--
-- Name: field_mappings_id_seq; Type: SEQUENCE; Schema: krd; Owner: postgres
--

CREATE SEQUENCE krd.field_mappings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE krd.field_mappings_id_seq OWNER TO postgres;

--
-- Name: field_mappings_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: postgres
--

ALTER SEQUENCE krd.field_mappings_id_seq OWNED BY krd.field_mappings.id;


--
-- Name: garrisons; Type: TABLE; Schema: krd; Owner: postgres
--

CREATE TABLE krd.garrisons (
    id integer NOT NULL,
    name character varying(255) NOT NULL
);


ALTER TABLE krd.garrisons OWNER TO postgres;

--
-- Name: TABLE garrisons; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON TABLE krd.garrisons IS 'Справочник гарнизонов';


--
-- Name: COLUMN garrisons.id; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.garrisons.id IS 'Идентификатор гарнизона';


--
-- Name: COLUMN garrisons.name; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.garrisons.name IS 'Наименование: «г. Красноярск», «г. Абакан»';


--
-- Name: garrisons_id_seq; Type: SEQUENCE; Schema: krd; Owner: postgres
--

CREATE SEQUENCE krd.garrisons_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE krd.garrisons_id_seq OWNER TO postgres;

--
-- Name: garrisons_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: postgres
--

ALTER SEQUENCE krd.garrisons_id_seq OWNED BY krd.garrisons.id;


--
-- Name: generated_documents; Type: TABLE; Schema: krd; Owner: postgres
--

CREATE TABLE krd.generated_documents (
    id integer NOT NULL,
    krd_id integer NOT NULL,
    template_id integer,
    document_type character varying(50),
    document_data bytea,
    file_name character varying(255),
    file_size integer,
    generated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    generated_by integer,
    is_deleted boolean DEFAULT false,
    metadata jsonb
);


ALTER TABLE krd.generated_documents OWNER TO postgres;

--
-- Name: generated_documents_id_seq; Type: SEQUENCE; Schema: krd; Owner: postgres
--

CREATE SEQUENCE krd.generated_documents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE krd.generated_documents_id_seq OWNER TO postgres;

--
-- Name: generated_documents_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: postgres
--

ALTER SEQUENCE krd.generated_documents_id_seq OWNED BY krd.generated_documents.id;


--
-- Name: incoming_orders; Type: TABLE; Schema: krd; Owner: postgres
--

CREATE TABLE krd.incoming_orders (
    id integer NOT NULL,
    krd_id integer NOT NULL,
    initiator_type_id integer NOT NULL,
    initiator_full_name character varying(255) NOT NULL,
    military_unit_id integer NOT NULL,
    order_date date NOT NULL,
    order_number character varying(100) NOT NULL,
    receipt_date date NOT NULL,
    receipt_number character varying(100) NOT NULL,
    postal_index character varying(20),
    postal_region character varying(100),
    postal_district character varying(100),
    postal_town character varying(100),
    postal_street character varying(100),
    postal_house character varying(50),
    postal_building character varying(50),
    postal_letter character varying(10),
    postal_apartment character varying(50),
    postal_room character varying(50),
    initiator_contacts character varying(255),
    our_response_date date,
    our_response_number character varying(100)
);


ALTER TABLE krd.incoming_orders OWNER TO postgres;

--
-- Name: TABLE incoming_orders; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON TABLE krd.incoming_orders IS 'Входящие поручения по КРД';


--
-- Name: COLUMN incoming_orders.id; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.incoming_orders.id IS 'Идентификатор входящего поручения';


--
-- Name: COLUMN incoming_orders.krd_id; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.incoming_orders.krd_id IS 'Ссылка на КРД';


--
-- Name: COLUMN incoming_orders.initiator_type_id; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.incoming_orders.initiator_type_id IS 'Ссылка на тип инициатора (комендатура и т.д.)';


--
-- Name: COLUMN incoming_orders.initiator_full_name; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.incoming_orders.initiator_full_name IS 'Полное наименование инициатора';


--
-- Name: COLUMN incoming_orders.military_unit_id; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.incoming_orders.military_unit_id IS 'Ссылка на военное управление (ЦВО, ВДВ и др.)';


--
-- Name: COLUMN incoming_orders.order_date; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.incoming_orders.order_date IS 'Дата поручения от инициатора';


--
-- Name: COLUMN incoming_orders.order_number; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.incoming_orders.order_number IS 'Номер поручения от инициатора';


--
-- Name: COLUMN incoming_orders.receipt_date; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.incoming_orders.receipt_date IS 'Дата поступления в комендатуру';


--
-- Name: COLUMN incoming_orders.receipt_number; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.incoming_orders.receipt_number IS 'Входящий номер в комендатуре';


--
-- Name: incoming_orders_id_seq; Type: SEQUENCE; Schema: krd; Owner: postgres
--

CREATE SEQUENCE krd.incoming_orders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE krd.incoming_orders_id_seq OWNER TO postgres;

--
-- Name: incoming_orders_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: postgres
--

ALTER SEQUENCE krd.incoming_orders_id_seq OWNED BY krd.incoming_orders.id;


--
-- Name: initiator_types; Type: TABLE; Schema: krd; Owner: postgres
--

CREATE TABLE krd.initiator_types (
    id integer NOT NULL,
    name character varying(100) NOT NULL
);


ALTER TABLE krd.initiator_types OWNER TO postgres;

--
-- Name: TABLE initiator_types; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON TABLE krd.initiator_types IS 'Справочник типов инициаторов';


--
-- Name: COLUMN initiator_types.id; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.initiator_types.id IS 'Идентификатор типа инициатора';


--
-- Name: COLUMN initiator_types.name; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.initiator_types.name IS 'Тип: «Комендатура», «Воинская часть», «РУВП»';


--
-- Name: initiator_types_id_seq; Type: SEQUENCE; Schema: krd; Owner: postgres
--

CREATE SEQUENCE krd.initiator_types_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE krd.initiator_types_id_seq OWNER TO postgres;

--
-- Name: initiator_types_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: postgres
--

ALTER SEQUENCE krd.initiator_types_id_seq OWNED BY krd.initiator_types.id;


--
-- Name: krd; Type: TABLE; Schema: krd; Owner: postgres
--

CREATE TABLE krd.krd (
    id integer NOT NULL,
    status_id integer,
    last_service_place_id integer,
    is_deleted boolean DEFAULT false,
    deleted_at timestamp without time zone,
    deleted_by integer
);


ALTER TABLE krd.krd OWNER TO postgres;

--
-- Name: TABLE krd; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON TABLE krd.krd IS 'Карточки розыска военнослужащих';


--
-- Name: COLUMN krd.id; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.krd.id IS 'Внутренний идентификатор КРД';


--
-- Name: COLUMN krd.status_id; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.krd.status_id IS 'Ссылка на справочник статусов КРД';


--
-- Name: COLUMN krd.last_service_place_id; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.krd.last_service_place_id IS 'ID последнего места службы';


--
-- Name: krd_id_seq; Type: SEQUENCE; Schema: krd; Owner: postgres
--

CREATE SEQUENCE krd.krd_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE krd.krd_id_seq OWNER TO postgres;

--
-- Name: krd_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: postgres
--

ALTER SEQUENCE krd.krd_id_seq OWNED BY krd.krd.id;


--
-- Name: military_units; Type: TABLE; Schema: krd; Owner: postgres
--

CREATE TABLE krd.military_units (
    id integer NOT NULL,
    name character varying(100) NOT NULL
);


ALTER TABLE krd.military_units OWNER TO postgres;

--
-- Name: TABLE military_units; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON TABLE krd.military_units IS 'Справочник военных управлений';


--
-- Name: COLUMN military_units.id; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.military_units.id IS 'Идентификатор военного управления';


--
-- Name: COLUMN military_units.name; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.military_units.name IS 'Наименование: «ЦВО», «ЮВО», «ВДВ»';


--
-- Name: military_units_id_seq; Type: SEQUENCE; Schema: krd; Owner: postgres
--

CREATE SEQUENCE krd.military_units_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE krd.military_units_id_seq OWNER TO postgres;

--
-- Name: military_units_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: postgres
--

ALTER SEQUENCE krd.military_units_id_seq OWNED BY krd.military_units.id;


--
-- Name: outgoing_requests; Type: TABLE; Schema: krd; Owner: postgres
--

CREATE TABLE krd.outgoing_requests (
    id integer NOT NULL,
    krd_id integer NOT NULL,
    request_type_id integer NOT NULL,
    military_unit_id integer,
    issue_date date NOT NULL,
    issue_number character varying(100) NOT NULL,
    request_text text,
    signed_by_position character varying(255),
    document_data bytea,
    is_deleted boolean DEFAULT false,
    deleted_at timestamp without time zone,
    deleted_by integer,
    recipient_id integer
);


ALTER TABLE krd.outgoing_requests OWNER TO postgres;

--
-- Name: TABLE outgoing_requests; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON TABLE krd.outgoing_requests IS 'Исходящие запросы по КРД';


--
-- Name: COLUMN outgoing_requests.id; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.outgoing_requests.id IS 'Идентификатор исходящего запроса';


--
-- Name: COLUMN outgoing_requests.krd_id; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.outgoing_requests.krd_id IS 'Ссылка на КРД';


--
-- Name: COLUMN outgoing_requests.request_type_id; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.outgoing_requests.request_type_id IS 'Ссылка на тип запроса (ЗАГС, ГИБДД и т.д.)';


--
-- Name: COLUMN outgoing_requests.issue_date; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.outgoing_requests.issue_date IS 'Дата запроса';


--
-- Name: COLUMN outgoing_requests.issue_number; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.outgoing_requests.issue_number IS 'Номер запроса';


--
-- Name: COLUMN outgoing_requests.document_data; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.outgoing_requests.document_data IS 'Содержимое сгенерированного документа в формате DOCX (бинарные данные)';


--
-- Name: COLUMN outgoing_requests.is_deleted; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.outgoing_requests.is_deleted IS 'Признак удаления запроса (мягкое удаление)';


--
-- Name: COLUMN outgoing_requests.deleted_at; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.outgoing_requests.deleted_at IS 'Дата и время удаления запроса';


--
-- Name: COLUMN outgoing_requests.deleted_by; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.outgoing_requests.deleted_by IS 'ID пользователя, удалившего запрос';


--
-- Name: outgoing_requests_id_seq; Type: SEQUENCE; Schema: krd; Owner: postgres
--

CREATE SEQUENCE krd.outgoing_requests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE krd.outgoing_requests_id_seq OWNER TO postgres;

--
-- Name: outgoing_requests_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: postgres
--

ALTER SEQUENCE krd.outgoing_requests_id_seq OWNED BY krd.outgoing_requests.id;


--
-- Name: positions; Type: TABLE; Schema: krd; Owner: postgres
--

CREATE TABLE krd.positions (
    id integer NOT NULL,
    name character varying(100) NOT NULL
);


ALTER TABLE krd.positions OWNER TO postgres;

--
-- Name: TABLE positions; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON TABLE krd.positions IS 'Справочник воинских должностей';


--
-- Name: COLUMN positions.id; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.positions.id IS 'Идентификатор воинской должности';


--
-- Name: COLUMN positions.name; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.positions.name IS 'Должность: «Водитель», «Стрелок» и др.';


--
-- Name: positions_id_seq; Type: SEQUENCE; Schema: krd; Owner: postgres
--

CREATE SEQUENCE krd.positions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE krd.positions_id_seq OWNER TO postgres;

--
-- Name: positions_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: postgres
--

ALTER SEQUENCE krd.positions_id_seq OWNED BY krd.positions.id;


--
-- Name: ranks; Type: TABLE; Schema: krd; Owner: postgres
--

CREATE TABLE krd.ranks (
    id integer NOT NULL,
    name character varying(100) NOT NULL
);


ALTER TABLE krd.ranks OWNER TO postgres;

--
-- Name: TABLE ranks; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON TABLE krd.ranks IS 'Справочник воинских званий';


--
-- Name: COLUMN ranks.id; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.ranks.id IS 'Идентификатор воинского звания';


--
-- Name: COLUMN ranks.name; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.ranks.name IS 'Наименование звания («Рядовой», «Лейтенант» и т.д.)';


--
-- Name: ranks_id_seq; Type: SEQUENCE; Schema: krd; Owner: postgres
--

CREATE SEQUENCE krd.ranks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE krd.ranks_id_seq OWNER TO postgres;

--
-- Name: ranks_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: postgres
--

ALTER SEQUENCE krd.ranks_id_seq OWNED BY krd.ranks.id;


--
-- Name: recipients; Type: TABLE; Schema: krd; Owner: postgres
--

CREATE TABLE krd.recipients (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    contacts character varying(255),
    postal_index character varying(20),
    postal_region character varying(100),
    postal_district character varying(100),
    postal_town character varying(100),
    postal_street character varying(100),
    postal_house character varying(50),
    postal_building character varying(50),
    postal_letter character varying(10),
    postal_apartment character varying(50),
    postal_room character varying(50),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_deleted boolean DEFAULT false
);


ALTER TABLE krd.recipients OWNER TO postgres;

--
-- Name: recipients_id_seq; Type: SEQUENCE; Schema: krd; Owner: postgres
--

CREATE SEQUENCE krd.recipients_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE krd.recipients_id_seq OWNER TO postgres;

--
-- Name: recipients_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: postgres
--

ALTER SEQUENCE krd.recipients_id_seq OWNED BY krd.recipients.id;


--
-- Name: report_templates; Type: TABLE; Schema: krd; Owner: postgres
--

CREATE TABLE krd.report_templates (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    template_type character varying(50) DEFAULT 'excel'::character varying,
    config_json jsonb NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_by integer,
    is_deleted boolean DEFAULT false,
    is_default boolean DEFAULT false,
    usage_count integer DEFAULT 0
);


ALTER TABLE krd.report_templates OWNER TO postgres;

--
-- Name: report_templates_id_seq; Type: SEQUENCE; Schema: krd; Owner: postgres
--

CREATE SEQUENCE krd.report_templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE krd.report_templates_id_seq OWNER TO postgres;

--
-- Name: report_templates_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: postgres
--

ALTER SEQUENCE krd.report_templates_id_seq OWNED BY krd.report_templates.id;


--
-- Name: request_types; Type: TABLE; Schema: krd; Owner: postgres
--

CREATE TABLE krd.request_types (
    id integer NOT NULL,
    name character varying(100) NOT NULL
);


ALTER TABLE krd.request_types OWNER TO postgres;

--
-- Name: TABLE request_types; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON TABLE krd.request_types IS 'Справочник типов запросов';


--
-- Name: COLUMN request_types.id; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.request_types.id IS 'Идентификатор типа запроса';


--
-- Name: COLUMN request_types.name; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.request_types.name IS 'Тип: «ЗАГС», «ГИБДД», «ФССП», «Военкомат»';


--
-- Name: request_types_id_seq; Type: SEQUENCE; Schema: krd; Owner: postgres
--

CREATE SEQUENCE krd.request_types_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE krd.request_types_id_seq OWNER TO postgres;

--
-- Name: request_types_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: postgres
--

ALTER SEQUENCE krd.request_types_id_seq OWNED BY krd.request_types.id;


--
-- Name: service_places; Type: TABLE; Schema: krd; Owner: postgres
--

CREATE TABLE krd.service_places (
    id integer NOT NULL,
    krd_id integer NOT NULL,
    place_name character varying(255) NOT NULL,
    military_unit_id integer,
    garrison_id integer,
    position_id integer,
    commanders text,
    postal_index character varying(20),
    postal_region character varying(100),
    postal_district character varying(100),
    postal_town character varying(100),
    postal_street character varying(100),
    postal_house character varying(50),
    postal_building character varying(50),
    postal_letter character varying(10),
    postal_apartment character varying(50),
    postal_room character varying(50),
    place_contacts character varying(255)
);


ALTER TABLE krd.service_places OWNER TO postgres;

--
-- Name: TABLE service_places; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON TABLE krd.service_places IS 'Места службы военнослужащих';


--
-- Name: COLUMN service_places.id; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.service_places.id IS 'Идентификатор места службы';


--
-- Name: COLUMN service_places.krd_id; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.service_places.krd_id IS 'Ссылка на КРД';


--
-- Name: COLUMN service_places.place_name; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.service_places.place_name IS 'Наименование места службы';


--
-- Name: service_places_id_seq; Type: SEQUENCE; Schema: krd; Owner: postgres
--

CREATE SEQUENCE krd.service_places_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE krd.service_places_id_seq OWNER TO postgres;

--
-- Name: service_places_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: postgres
--

ALTER SEQUENCE krd.service_places_id_seq OWNED BY krd.service_places.id;


--
-- Name: soch_episodes; Type: TABLE; Schema: krd; Owner: postgres
--

CREATE TABLE krd.soch_episodes (
    id integer NOT NULL,
    krd_id integer NOT NULL,
    soch_date date,
    soch_location character varying(255),
    order_date_number character varying(100),
    witnesses text,
    reasons text,
    weapon_info text,
    clothing text,
    movement_options text,
    other_info text,
    duty_officer_commissariat character varying(255),
    duty_officer_omvd character varying(255),
    investigation_info text,
    prosecution_info text,
    criminal_case_info text,
    search_date date,
    found_by character varying(255),
    search_circumstances text,
    notification_recipient character varying(255),
    notification_date date,
    notification_number character varying(100)
);


ALTER TABLE krd.soch_episodes OWNER TO postgres;

--
-- Name: TABLE soch_episodes; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON TABLE krd.soch_episodes IS 'Эпизоды самовольного оставления части (СОЧ)';


--
-- Name: COLUMN soch_episodes.id; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.soch_episodes.id IS 'Идентификатор эпизода самовольного оставления части (СОЧ)';


--
-- Name: COLUMN soch_episodes.krd_id; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.soch_episodes.krd_id IS 'Ссылка на КРД';


--
-- Name: soch_episodes_id_seq; Type: SEQUENCE; Schema: krd; Owner: postgres
--

CREATE SEQUENCE krd.soch_episodes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE krd.soch_episodes_id_seq OWNER TO postgres;

--
-- Name: soch_episodes_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: postgres
--

ALTER SEQUENCE krd.soch_episodes_id_seq OWNED BY krd.soch_episodes.id;


--
-- Name: social_data; Type: TABLE; Schema: krd; Owner: postgres
--

CREATE TABLE krd.social_data (
    id integer NOT NULL,
    krd_id integer NOT NULL,
    surname character varying(100) NOT NULL,
    name character varying(100) NOT NULL,
    patronymic character varying(100) NOT NULL,
    birth_date date,
    birth_place_town character varying(100),
    birth_place_district character varying(100),
    birth_place_region character varying(100),
    birth_place_country character varying(100),
    tab_number character varying(50),
    personal_number character varying(50),
    category_id integer,
    rank_id integer,
    drafted_by_commissariat character varying(255),
    draft_date date,
    povsk character varying(255),
    selection_date date,
    education character varying(255),
    criminal_record text,
    social_media_account character varying(255),
    bank_card_number character varying(50),
    passport_series character varying(10),
    passport_number character varying(20),
    passport_issue_date date,
    passport_issued_by character varying(255),
    military_id_series character varying(10),
    military_id_number character varying(20),
    military_id_issue_date date,
    military_id_issued_by character varying(255),
    appearance_features text,
    personal_marks text,
    federal_search_info text,
    military_contacts character varying(255),
    relatives_info text,
    photo_civilian bytea,
    photo_military_headgear bytea,
    photo_military_no_headgear bytea,
    photo_distinctive_marks bytea
);


ALTER TABLE krd.social_data OWNER TO postgres;

--
-- Name: TABLE social_data; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON TABLE krd.social_data IS 'Социально-демографические данные военнослужащих';


--
-- Name: COLUMN social_data.id; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.social_data.id IS 'Идентификатор записи социально-демографических данных';


--
-- Name: COLUMN social_data.krd_id; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.social_data.krd_id IS 'Ссылка на карточку розыска (КРД)';


--
-- Name: COLUMN social_data.surname; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.social_data.surname IS 'Фамилия военнослужащего (обязательное поле)';


--
-- Name: COLUMN social_data.name; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.social_data.name IS 'Имя военнослужащего';


--
-- Name: COLUMN social_data.patronymic; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.social_data.patronymic IS 'Отчество военнослужащего';


--
-- Name: COLUMN social_data.photo_civilian; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.social_data.photo_civilian IS 'Фотография в гражданской одежде (BYTEA)';


--
-- Name: COLUMN social_data.photo_military_headgear; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.social_data.photo_military_headgear IS 'Фотография в военной форме с головным убором (BYTEA)';


--
-- Name: COLUMN social_data.photo_military_no_headgear; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.social_data.photo_military_no_headgear IS 'Фотография в военной форме без головного убора (BYTEA)';


--
-- Name: COLUMN social_data.photo_distinctive_marks; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.social_data.photo_distinctive_marks IS 'Фотография отличительных примет: татуировки, шрамы, отсутствие зубов, пальцев и т.д. (BYTEA)';


--
-- Name: social_data_id_seq; Type: SEQUENCE; Schema: krd; Owner: postgres
--

CREATE SEQUENCE krd.social_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE krd.social_data_id_seq OWNER TO postgres;

--
-- Name: social_data_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: postgres
--

ALTER SEQUENCE krd.social_data_id_seq OWNED BY krd.social_data.id;


--
-- Name: statuses; Type: TABLE; Schema: krd; Owner: postgres
--

CREATE TABLE krd.statuses (
    id integer NOT NULL,
    name character varying(20) NOT NULL
);


ALTER TABLE krd.statuses OWNER TO postgres;

--
-- Name: TABLE statuses; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON TABLE krd.statuses IS 'Справочник статусов КРД';


--
-- Name: COLUMN statuses.id; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.statuses.id IS 'Идентификатор статуса';


--
-- Name: COLUMN statuses.name; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.statuses.name IS 'Статус КРД: «В розыске», «Разыскан»';


--
-- Name: statuses_id_seq; Type: SEQUENCE; Schema: krd; Owner: postgres
--

CREATE SEQUENCE krd.statuses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE krd.statuses_id_seq OWNER TO postgres;

--
-- Name: statuses_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: postgres
--

ALTER SEQUENCE krd.statuses_id_seq OWNED BY krd.statuses.id;


--
-- Name: user_roles; Type: TABLE; Schema: krd; Owner: postgres
--

CREATE TABLE krd.user_roles (
    id integer NOT NULL,
    role_name character varying(50) NOT NULL,
    description text,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE krd.user_roles OWNER TO postgres;

--
-- Name: user_roles_id_seq; Type: SEQUENCE; Schema: krd; Owner: postgres
--

CREATE SEQUENCE krd.user_roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE krd.user_roles_id_seq OWNER TO postgres;

--
-- Name: user_roles_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: postgres
--

ALTER SEQUENCE krd.user_roles_id_seq OWNED BY krd.user_roles.id;


--
-- Name: user_sessions; Type: TABLE; Schema: krd; Owner: postgres
--

CREATE TABLE krd.user_sessions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    login_time timestamp without time zone DEFAULT now() NOT NULL,
    logout_time timestamp without time zone,
    is_active boolean DEFAULT true
);


ALTER TABLE krd.user_sessions OWNER TO postgres;

--
-- Name: user_sessions_id_seq; Type: SEQUENCE; Schema: krd; Owner: postgres
--

CREATE SEQUENCE krd.user_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE krd.user_sessions_id_seq OWNER TO postgres;

--
-- Name: user_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: postgres
--

ALTER SEQUENCE krd.user_sessions_id_seq OWNED BY krd.user_sessions.id;


--
-- Name: user_settings; Type: TABLE; Schema: krd; Owner: postgres
--

CREATE TABLE krd.user_settings (
    id integer NOT NULL,
    user_id integer NOT NULL,
    theme_name character varying(50) DEFAULT 'light'::character varying,
    config_json jsonb DEFAULT '{}'::jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE krd.user_settings OWNER TO postgres;

--
-- Name: TABLE user_settings; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON TABLE krd.user_settings IS 'Настройки оформления пользователей';


--
-- Name: COLUMN user_settings.config_json; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.user_settings.config_json IS 'JSON с настройками: {"theme": "light", "colors": {...}}';


--
-- Name: user_settings_id_seq; Type: SEQUENCE; Schema: krd; Owner: postgres
--

CREATE SEQUENCE krd.user_settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE krd.user_settings_id_seq OWNER TO postgres;

--
-- Name: user_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: postgres
--

ALTER SEQUENCE krd.user_settings_id_seq OWNED BY krd.user_settings.id;


--
-- Name: user_themes; Type: TABLE; Schema: krd; Owner: postgres
--

CREATE TABLE krd.user_themes (
    id integer NOT NULL,
    user_id integer,
    theme_name character varying(100) NOT NULL,
    description text,
    config_json jsonb NOT NULL,
    is_active boolean DEFAULT false,
    is_default boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_by integer
);


ALTER TABLE krd.user_themes OWNER TO postgres;

--
-- Name: TABLE user_themes; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON TABLE krd.user_themes IS 'Пользовательские темы оформления и конфигурации интерфейса';


--
-- Name: COLUMN user_themes.config_json; Type: COMMENT; Schema: krd; Owner: postgres
--

COMMENT ON COLUMN krd.user_themes.config_json IS 'JSON конфигурация: {
    "social_data": {
        "visible_fields": ["surname", "name", "patronymic", ...],
        "field_order": ["surname", "name", ...],
        "required_fields": ["surname", "name", "patronymic"]
    },
    "addresses": {...},
    "ui_settings": {
        "theme": "light/dark",
        "compact_mode": true/false
    }
}';


--
-- Name: user_themes_id_seq; Type: SEQUENCE; Schema: krd; Owner: postgres
--

CREATE SEQUENCE krd.user_themes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE krd.user_themes_id_seq OWNER TO postgres;

--
-- Name: user_themes_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: postgres
--

ALTER SEQUENCE krd.user_themes_id_seq OWNED BY krd.user_themes.id;


--
-- Name: users; Type: TABLE; Schema: krd; Owner: postgres
--

CREATE TABLE krd.users (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    password_hash character varying(255) NOT NULL,
    role_id integer NOT NULL,
    full_name character varying(100),
    email character varying(100),
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT now(),
    last_login timestamp without time zone
);


ALTER TABLE krd.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: krd; Owner: postgres
--

CREATE SEQUENCE krd.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE krd.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: postgres
--

ALTER SEQUENCE krd.users_id_seq OWNED BY krd.users.id;


--
-- Name: addresses id; Type: DEFAULT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.addresses ALTER COLUMN id SET DEFAULT nextval('krd.addresses_id_seq'::regclass);


--
-- Name: audit_log id; Type: DEFAULT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.audit_log ALTER COLUMN id SET DEFAULT nextval('krd.audit_log_id_seq'::regclass);


--
-- Name: categories id; Type: DEFAULT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.categories ALTER COLUMN id SET DEFAULT nextval('krd.categories_id_seq'::regclass);


--
-- Name: document_templates id; Type: DEFAULT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.document_templates ALTER COLUMN id SET DEFAULT nextval('krd.document_templates_id_seq'::regclass);


--
-- Name: field_mappings id; Type: DEFAULT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.field_mappings ALTER COLUMN id SET DEFAULT nextval('krd.field_mappings_id_seq'::regclass);


--
-- Name: garrisons id; Type: DEFAULT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.garrisons ALTER COLUMN id SET DEFAULT nextval('krd.garrisons_id_seq'::regclass);


--
-- Name: generated_documents id; Type: DEFAULT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.generated_documents ALTER COLUMN id SET DEFAULT nextval('krd.generated_documents_id_seq'::regclass);


--
-- Name: incoming_orders id; Type: DEFAULT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.incoming_orders ALTER COLUMN id SET DEFAULT nextval('krd.incoming_orders_id_seq'::regclass);


--
-- Name: initiator_types id; Type: DEFAULT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.initiator_types ALTER COLUMN id SET DEFAULT nextval('krd.initiator_types_id_seq'::regclass);


--
-- Name: krd id; Type: DEFAULT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.krd ALTER COLUMN id SET DEFAULT nextval('krd.krd_id_seq'::regclass);


--
-- Name: military_units id; Type: DEFAULT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.military_units ALTER COLUMN id SET DEFAULT nextval('krd.military_units_id_seq'::regclass);


--
-- Name: outgoing_requests id; Type: DEFAULT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.outgoing_requests ALTER COLUMN id SET DEFAULT nextval('krd.outgoing_requests_id_seq'::regclass);


--
-- Name: positions id; Type: DEFAULT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.positions ALTER COLUMN id SET DEFAULT nextval('krd.positions_id_seq'::regclass);


--
-- Name: ranks id; Type: DEFAULT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.ranks ALTER COLUMN id SET DEFAULT nextval('krd.ranks_id_seq'::regclass);


--
-- Name: recipients id; Type: DEFAULT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.recipients ALTER COLUMN id SET DEFAULT nextval('krd.recipients_id_seq'::regclass);


--
-- Name: report_templates id; Type: DEFAULT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.report_templates ALTER COLUMN id SET DEFAULT nextval('krd.report_templates_id_seq'::regclass);


--
-- Name: request_types id; Type: DEFAULT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.request_types ALTER COLUMN id SET DEFAULT nextval('krd.request_types_id_seq'::regclass);


--
-- Name: service_places id; Type: DEFAULT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.service_places ALTER COLUMN id SET DEFAULT nextval('krd.service_places_id_seq'::regclass);


--
-- Name: soch_episodes id; Type: DEFAULT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.soch_episodes ALTER COLUMN id SET DEFAULT nextval('krd.soch_episodes_id_seq'::regclass);


--
-- Name: social_data id; Type: DEFAULT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.social_data ALTER COLUMN id SET DEFAULT nextval('krd.social_data_id_seq'::regclass);


--
-- Name: statuses id; Type: DEFAULT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.statuses ALTER COLUMN id SET DEFAULT nextval('krd.statuses_id_seq'::regclass);


--
-- Name: user_roles id; Type: DEFAULT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.user_roles ALTER COLUMN id SET DEFAULT nextval('krd.user_roles_id_seq'::regclass);


--
-- Name: user_sessions id; Type: DEFAULT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.user_sessions ALTER COLUMN id SET DEFAULT nextval('krd.user_sessions_id_seq'::regclass);


--
-- Name: user_settings id; Type: DEFAULT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.user_settings ALTER COLUMN id SET DEFAULT nextval('krd.user_settings_id_seq'::regclass);


--
-- Name: user_themes id; Type: DEFAULT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.user_themes ALTER COLUMN id SET DEFAULT nextval('krd.user_themes_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.users ALTER COLUMN id SET DEFAULT nextval('krd.users_id_seq'::regclass);


--
-- Name: addresses addresses_pkey; Type: CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.addresses
    ADD CONSTRAINT addresses_pkey PRIMARY KEY (id);


--
-- Name: audit_log audit_log_pkey; Type: CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.audit_log
    ADD CONSTRAINT audit_log_pkey PRIMARY KEY (id);


--
-- Name: categories categories_pkey; Type: CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.categories
    ADD CONSTRAINT categories_pkey PRIMARY KEY (id);


--
-- Name: document_templates document_templates_pkey; Type: CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.document_templates
    ADD CONSTRAINT document_templates_pkey PRIMARY KEY (id);


--
-- Name: field_mappings field_mappings_pkey; Type: CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.field_mappings
    ADD CONSTRAINT field_mappings_pkey PRIMARY KEY (id);


--
-- Name: garrisons garrisons_pkey; Type: CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.garrisons
    ADD CONSTRAINT garrisons_pkey PRIMARY KEY (id);


--
-- Name: generated_documents generated_documents_pkey; Type: CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.generated_documents
    ADD CONSTRAINT generated_documents_pkey PRIMARY KEY (id);


--
-- Name: incoming_orders incoming_orders_pkey; Type: CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.incoming_orders
    ADD CONSTRAINT incoming_orders_pkey PRIMARY KEY (id);


--
-- Name: initiator_types initiator_types_pkey; Type: CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.initiator_types
    ADD CONSTRAINT initiator_types_pkey PRIMARY KEY (id);


--
-- Name: krd krd_pkey; Type: CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.krd
    ADD CONSTRAINT krd_pkey PRIMARY KEY (id);


--
-- Name: military_units military_units_pkey; Type: CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.military_units
    ADD CONSTRAINT military_units_pkey PRIMARY KEY (id);


--
-- Name: outgoing_requests outgoing_requests_pkey; Type: CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.outgoing_requests
    ADD CONSTRAINT outgoing_requests_pkey PRIMARY KEY (id);


--
-- Name: positions positions_pkey; Type: CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.positions
    ADD CONSTRAINT positions_pkey PRIMARY KEY (id);


--
-- Name: ranks ranks_pkey; Type: CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.ranks
    ADD CONSTRAINT ranks_pkey PRIMARY KEY (id);


--
-- Name: recipients recipients_pkey; Type: CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.recipients
    ADD CONSTRAINT recipients_pkey PRIMARY KEY (id);


--
-- Name: report_templates report_templates_pkey; Type: CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.report_templates
    ADD CONSTRAINT report_templates_pkey PRIMARY KEY (id);


--
-- Name: request_types request_types_pkey; Type: CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.request_types
    ADD CONSTRAINT request_types_pkey PRIMARY KEY (id);


--
-- Name: service_places service_places_pkey; Type: CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.service_places
    ADD CONSTRAINT service_places_pkey PRIMARY KEY (id);


--
-- Name: soch_episodes soch_episodes_pkey; Type: CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.soch_episodes
    ADD CONSTRAINT soch_episodes_pkey PRIMARY KEY (id);


--
-- Name: social_data social_data_pkey; Type: CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.social_data
    ADD CONSTRAINT social_data_pkey PRIMARY KEY (id);


--
-- Name: statuses statuses_pkey; Type: CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.statuses
    ADD CONSTRAINT statuses_pkey PRIMARY KEY (id);


--
-- Name: user_roles user_roles_pkey; Type: CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.user_roles
    ADD CONSTRAINT user_roles_pkey PRIMARY KEY (id);


--
-- Name: user_roles user_roles_role_name_key; Type: CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.user_roles
    ADD CONSTRAINT user_roles_role_name_key UNIQUE (role_name);


--
-- Name: user_sessions user_sessions_pkey; Type: CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.user_sessions
    ADD CONSTRAINT user_sessions_pkey PRIMARY KEY (id);


--
-- Name: user_settings user_settings_pkey; Type: CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.user_settings
    ADD CONSTRAINT user_settings_pkey PRIMARY KEY (id);


--
-- Name: user_settings user_settings_user_id_key; Type: CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.user_settings
    ADD CONSTRAINT user_settings_user_id_key UNIQUE (user_id);


--
-- Name: user_themes user_themes_pkey; Type: CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.user_themes
    ADD CONSTRAINT user_themes_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: idx_addresses_krd_id; Type: INDEX; Schema: krd; Owner: postgres
--

CREATE INDEX idx_addresses_krd_id ON krd.addresses USING btree (krd_id);


--
-- Name: idx_audit_log_action_type; Type: INDEX; Schema: krd; Owner: postgres
--

CREATE INDEX idx_audit_log_action_type ON krd.audit_log USING btree (action_type);


--
-- Name: idx_audit_log_created_at; Type: INDEX; Schema: krd; Owner: postgres
--

CREATE INDEX idx_audit_log_created_at ON krd.audit_log USING btree (created_at);


--
-- Name: idx_audit_log_krd_id; Type: INDEX; Schema: krd; Owner: postgres
--

CREATE INDEX idx_audit_log_krd_id ON krd.audit_log USING btree (krd_id);


--
-- Name: idx_audit_log_table_name; Type: INDEX; Schema: krd; Owner: postgres
--

CREATE INDEX idx_audit_log_table_name ON krd.audit_log USING btree (table_name);


--
-- Name: idx_audit_log_user_id; Type: INDEX; Schema: krd; Owner: postgres
--

CREATE INDEX idx_audit_log_user_id ON krd.audit_log USING btree (user_id);


--
-- Name: idx_document_templates_is_deleted; Type: INDEX; Schema: krd; Owner: postgres
--

CREATE INDEX idx_document_templates_is_deleted ON krd.document_templates USING btree (is_deleted);


--
-- Name: idx_field_mappings_composite; Type: INDEX; Schema: krd; Owner: postgres
--

CREATE INDEX idx_field_mappings_composite ON krd.field_mappings USING btree (is_composite) WHERE (is_composite = true);


--
-- Name: idx_generated_documents_krd; Type: INDEX; Schema: krd; Owner: postgres
--

CREATE INDEX idx_generated_documents_krd ON krd.generated_documents USING btree (krd_id);


--
-- Name: idx_generated_documents_type; Type: INDEX; Schema: krd; Owner: postgres
--

CREATE INDEX idx_generated_documents_type ON krd.generated_documents USING btree (document_type);


--
-- Name: idx_incoming_orders_krd_id; Type: INDEX; Schema: krd; Owner: postgres
--

CREATE INDEX idx_incoming_orders_krd_id ON krd.incoming_orders USING btree (krd_id);


--
-- Name: idx_incoming_orders_receipt_number; Type: INDEX; Schema: krd; Owner: postgres
--

CREATE INDEX idx_incoming_orders_receipt_number ON krd.incoming_orders USING btree (receipt_number);


--
-- Name: idx_krd_is_deleted; Type: INDEX; Schema: krd; Owner: postgres
--

CREATE INDEX idx_krd_is_deleted ON krd.krd USING btree (is_deleted);


--
-- Name: idx_krd_status_id; Type: INDEX; Schema: krd; Owner: postgres
--

CREATE INDEX idx_krd_status_id ON krd.krd USING btree (status_id);


--
-- Name: idx_outgoing_requests_is_deleted; Type: INDEX; Schema: krd; Owner: postgres
--

CREATE INDEX idx_outgoing_requests_is_deleted ON krd.outgoing_requests USING btree (is_deleted);


--
-- Name: idx_outgoing_requests_krd_id; Type: INDEX; Schema: krd; Owner: postgres
--

CREATE INDEX idx_outgoing_requests_krd_id ON krd.outgoing_requests USING btree (krd_id);


--
-- Name: idx_report_templates_deleted; Type: INDEX; Schema: krd; Owner: postgres
--

CREATE INDEX idx_report_templates_deleted ON krd.report_templates USING btree (is_deleted);


--
-- Name: idx_report_templates_type; Type: INDEX; Schema: krd; Owner: postgres
--

CREATE INDEX idx_report_templates_type ON krd.report_templates USING btree (template_type);


--
-- Name: idx_service_places_krd_id; Type: INDEX; Schema: krd; Owner: postgres
--

CREATE INDEX idx_service_places_krd_id ON krd.service_places USING btree (krd_id);


--
-- Name: idx_soch_episodes_krd_id; Type: INDEX; Schema: krd; Owner: postgres
--

CREATE INDEX idx_soch_episodes_krd_id ON krd.soch_episodes USING btree (krd_id);


--
-- Name: idx_soch_episodes_soch_date; Type: INDEX; Schema: krd; Owner: postgres
--

CREATE INDEX idx_soch_episodes_soch_date ON krd.soch_episodes USING btree (soch_date);


--
-- Name: idx_social_data_krd_id; Type: INDEX; Schema: krd; Owner: postgres
--

CREATE INDEX idx_social_data_krd_id ON krd.social_data USING btree (krd_id);


--
-- Name: idx_social_data_personal_number; Type: INDEX; Schema: krd; Owner: postgres
--

CREATE INDEX idx_social_data_personal_number ON krd.social_data USING btree (personal_number);


--
-- Name: idx_social_data_photos; Type: INDEX; Schema: krd; Owner: postgres
--

CREATE INDEX idx_social_data_photos ON krd.social_data USING btree (krd_id) WHERE ((photo_civilian IS NOT NULL) OR (photo_military_headgear IS NOT NULL) OR (photo_military_no_headgear IS NOT NULL) OR (photo_distinctive_marks IS NOT NULL));


--
-- Name: idx_social_data_surname; Type: INDEX; Schema: krd; Owner: postgres
--

CREATE INDEX idx_social_data_surname ON krd.social_data USING btree (surname);


--
-- Name: idx_user_settings_user_id; Type: INDEX; Schema: krd; Owner: postgres
--

CREATE INDEX idx_user_settings_user_id ON krd.user_settings USING btree (user_id);


--
-- Name: idx_user_themes_active; Type: INDEX; Schema: krd; Owner: postgres
--

CREATE INDEX idx_user_themes_active ON krd.user_themes USING btree (is_active) WHERE (is_active = true);


--
-- Name: idx_user_themes_user_id; Type: INDEX; Schema: krd; Owner: postgres
--

CREATE INDEX idx_user_themes_user_id ON krd.user_themes USING btree (user_id);


--
-- Name: idx_users_role_id; Type: INDEX; Schema: krd; Owner: postgres
--

CREATE INDEX idx_users_role_id ON krd.users USING btree (role_id);


--
-- Name: idx_users_username; Type: INDEX; Schema: krd; Owner: postgres
--

CREATE INDEX idx_users_username ON krd.users USING btree (username);


--
-- Name: addresses addresses_krd_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.addresses
    ADD CONSTRAINT addresses_krd_id_fkey FOREIGN KEY (krd_id) REFERENCES krd.krd(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: krd fk_last_service_place; Type: FK CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.krd
    ADD CONSTRAINT fk_last_service_place FOREIGN KEY (last_service_place_id) REFERENCES krd.service_places(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: generated_documents generated_documents_template_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.generated_documents
    ADD CONSTRAINT generated_documents_template_id_fkey FOREIGN KEY (template_id) REFERENCES krd.report_templates(id);


--
-- Name: incoming_orders incoming_orders_initiator_type_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.incoming_orders
    ADD CONSTRAINT incoming_orders_initiator_type_id_fkey FOREIGN KEY (initiator_type_id) REFERENCES krd.initiator_types(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: incoming_orders incoming_orders_krd_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.incoming_orders
    ADD CONSTRAINT incoming_orders_krd_id_fkey FOREIGN KEY (krd_id) REFERENCES krd.krd(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: incoming_orders incoming_orders_military_unit_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.incoming_orders
    ADD CONSTRAINT incoming_orders_military_unit_id_fkey FOREIGN KEY (military_unit_id) REFERENCES krd.military_units(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: krd krd_status_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.krd
    ADD CONSTRAINT krd_status_id_fkey FOREIGN KEY (status_id) REFERENCES krd.statuses(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: outgoing_requests outgoing_requests_krd_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.outgoing_requests
    ADD CONSTRAINT outgoing_requests_krd_id_fkey FOREIGN KEY (krd_id) REFERENCES krd.krd(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: outgoing_requests outgoing_requests_military_unit_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.outgoing_requests
    ADD CONSTRAINT outgoing_requests_military_unit_id_fkey FOREIGN KEY (military_unit_id) REFERENCES krd.military_units(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: outgoing_requests outgoing_requests_recipient_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.outgoing_requests
    ADD CONSTRAINT outgoing_requests_recipient_id_fkey FOREIGN KEY (recipient_id) REFERENCES krd.recipients(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: outgoing_requests outgoing_requests_request_type_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.outgoing_requests
    ADD CONSTRAINT outgoing_requests_request_type_id_fkey FOREIGN KEY (request_type_id) REFERENCES krd.request_types(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: service_places service_places_garrison_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.service_places
    ADD CONSTRAINT service_places_garrison_id_fkey FOREIGN KEY (garrison_id) REFERENCES krd.garrisons(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: service_places service_places_krd_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.service_places
    ADD CONSTRAINT service_places_krd_id_fkey FOREIGN KEY (krd_id) REFERENCES krd.krd(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: service_places service_places_military_unit_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.service_places
    ADD CONSTRAINT service_places_military_unit_id_fkey FOREIGN KEY (military_unit_id) REFERENCES krd.military_units(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: service_places service_places_position_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.service_places
    ADD CONSTRAINT service_places_position_id_fkey FOREIGN KEY (position_id) REFERENCES krd.positions(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: soch_episodes soch_episodes_krd_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.soch_episodes
    ADD CONSTRAINT soch_episodes_krd_id_fkey FOREIGN KEY (krd_id) REFERENCES krd.krd(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: social_data social_data_category_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.social_data
    ADD CONSTRAINT social_data_category_id_fkey FOREIGN KEY (category_id) REFERENCES krd.categories(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: social_data social_data_krd_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.social_data
    ADD CONSTRAINT social_data_krd_id_fkey FOREIGN KEY (krd_id) REFERENCES krd.krd(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: social_data social_data_rank_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.social_data
    ADD CONSTRAINT social_data_rank_id_fkey FOREIGN KEY (rank_id) REFERENCES krd.ranks(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: user_sessions user_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.user_sessions
    ADD CONSTRAINT user_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES krd.users(id) ON DELETE CASCADE;


--
-- Name: user_settings user_settings_user_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.user_settings
    ADD CONSTRAINT user_settings_user_id_fkey FOREIGN KEY (user_id) REFERENCES krd.users(id) ON DELETE CASCADE;


--
-- Name: user_themes user_themes_created_by_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.user_themes
    ADD CONSTRAINT user_themes_created_by_fkey FOREIGN KEY (created_by) REFERENCES krd.users(id);


--
-- Name: user_themes user_themes_user_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.user_themes
    ADD CONSTRAINT user_themes_user_id_fkey FOREIGN KEY (user_id) REFERENCES krd.users(id) ON DELETE CASCADE;


--
-- Name: users users_role_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: postgres
--

ALTER TABLE ONLY krd.users
    ADD CONSTRAINT users_role_id_fkey FOREIGN KEY (role_id) REFERENCES krd.user_roles(id) ON DELETE RESTRICT;


--
-- Name: SCHEMA krd; Type: ACL; Schema: -; Owner: postgres
--

GRANT USAGE ON SCHEMA krd TO arm_user;


--
-- Name: TABLE addresses; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE krd.addresses TO arm_user;


--
-- Name: SEQUENCE addresses_id_seq; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE krd.addresses_id_seq TO arm_user;


--
-- Name: TABLE audit_log; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE krd.audit_log TO arm_user;


--
-- Name: SEQUENCE audit_log_id_seq; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE krd.audit_log_id_seq TO arm_user;


--
-- Name: TABLE categories; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE krd.categories TO arm_user;


--
-- Name: SEQUENCE categories_id_seq; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE krd.categories_id_seq TO arm_user;


--
-- Name: TABLE document_templates; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE krd.document_templates TO arm_user;


--
-- Name: SEQUENCE document_templates_id_seq; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE krd.document_templates_id_seq TO arm_user;


--
-- Name: TABLE field_mappings; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE krd.field_mappings TO arm_user;


--
-- Name: SEQUENCE field_mappings_id_seq; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE krd.field_mappings_id_seq TO arm_user;


--
-- Name: TABLE garrisons; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE krd.garrisons TO arm_user;


--
-- Name: SEQUENCE garrisons_id_seq; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE krd.garrisons_id_seq TO arm_user;


--
-- Name: TABLE generated_documents; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE krd.generated_documents TO arm_user;


--
-- Name: SEQUENCE generated_documents_id_seq; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE krd.generated_documents_id_seq TO arm_user;


--
-- Name: TABLE incoming_orders; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE krd.incoming_orders TO arm_user;


--
-- Name: SEQUENCE incoming_orders_id_seq; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE krd.incoming_orders_id_seq TO arm_user;


--
-- Name: TABLE initiator_types; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE krd.initiator_types TO arm_user;


--
-- Name: SEQUENCE initiator_types_id_seq; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE krd.initiator_types_id_seq TO arm_user;


--
-- Name: TABLE krd; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE krd.krd TO arm_user;


--
-- Name: SEQUENCE krd_id_seq; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE krd.krd_id_seq TO arm_user;


--
-- Name: TABLE military_units; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE krd.military_units TO arm_user;


--
-- Name: SEQUENCE military_units_id_seq; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE krd.military_units_id_seq TO arm_user;


--
-- Name: TABLE outgoing_requests; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE krd.outgoing_requests TO arm_user;


--
-- Name: SEQUENCE outgoing_requests_id_seq; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE krd.outgoing_requests_id_seq TO arm_user;


--
-- Name: TABLE positions; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE krd.positions TO arm_user;


--
-- Name: SEQUENCE positions_id_seq; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE krd.positions_id_seq TO arm_user;


--
-- Name: TABLE ranks; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE krd.ranks TO arm_user;


--
-- Name: SEQUENCE ranks_id_seq; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE krd.ranks_id_seq TO arm_user;


--
-- Name: TABLE recipients; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE krd.recipients TO arm_user;


--
-- Name: SEQUENCE recipients_id_seq; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE krd.recipients_id_seq TO arm_user;


--
-- Name: TABLE report_templates; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE krd.report_templates TO arm_user;


--
-- Name: SEQUENCE report_templates_id_seq; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE krd.report_templates_id_seq TO arm_user;


--
-- Name: TABLE request_types; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE krd.request_types TO arm_user;


--
-- Name: SEQUENCE request_types_id_seq; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE krd.request_types_id_seq TO arm_user;


--
-- Name: TABLE service_places; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE krd.service_places TO arm_user;


--
-- Name: SEQUENCE service_places_id_seq; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE krd.service_places_id_seq TO arm_user;


--
-- Name: TABLE soch_episodes; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE krd.soch_episodes TO arm_user;


--
-- Name: SEQUENCE soch_episodes_id_seq; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE krd.soch_episodes_id_seq TO arm_user;


--
-- Name: TABLE social_data; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE krd.social_data TO arm_user;


--
-- Name: SEQUENCE social_data_id_seq; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE krd.social_data_id_seq TO arm_user;


--
-- Name: TABLE statuses; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE krd.statuses TO arm_user;


--
-- Name: SEQUENCE statuses_id_seq; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE krd.statuses_id_seq TO arm_user;


--
-- Name: TABLE user_roles; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE krd.user_roles TO arm_user;


--
-- Name: SEQUENCE user_roles_id_seq; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE krd.user_roles_id_seq TO arm_user;


--
-- Name: TABLE user_sessions; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE krd.user_sessions TO arm_user;


--
-- Name: SEQUENCE user_sessions_id_seq; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE krd.user_sessions_id_seq TO arm_user;


--
-- Name: TABLE user_settings; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE krd.user_settings TO arm_user;


--
-- Name: SEQUENCE user_settings_id_seq; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE krd.user_settings_id_seq TO arm_user;


--
-- Name: TABLE user_themes; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE krd.user_themes TO arm_user;


--
-- Name: SEQUENCE user_themes_id_seq; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE krd.user_themes_id_seq TO arm_user;


--
-- Name: TABLE users; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE krd.users TO arm_user;


--
-- Name: SEQUENCE users_id_seq; Type: ACL; Schema: krd; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE krd.users_id_seq TO arm_user;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: krd; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA krd GRANT SELECT,USAGE ON SEQUENCES TO arm_user;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: krd; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA krd GRANT SELECT,INSERT,DELETE,UPDATE ON TABLES TO arm_user;


--
-- PostgreSQL database dump complete
--

\unrestrict ulNjv2jhqaHAnQqGT6zdRBMsXJ6m2CQgrVvXp6nkiljkpmdwaB4Ydo6uecRq3Ih

