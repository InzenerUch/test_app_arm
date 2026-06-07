--
-- PostgreSQL database dump
--

\restrict OzeazLUpjJjo4CU9mvebXjvMYc8sIaATU73uYD1h78PLzr97zVjKAxDOJ34KamF

-- Dumped from database version 16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)

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
-- Name: krd; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA krd;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: addresses; Type: TABLE; Schema: krd; Owner: -
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
    check_result text,
    postal_index character varying(6),
    is_deleted boolean DEFAULT false,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE addresses; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON TABLE krd.addresses IS 'Адреса проживания военнослужащих';


--
-- Name: COLUMN addresses.id; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.addresses.id IS 'Идентификатор адреса проживания';


--
-- Name: COLUMN addresses.krd_id; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.addresses.krd_id IS 'Ссылка на КРД';


--
-- Name: addresses_id_seq; Type: SEQUENCE; Schema: krd; Owner: -
--

CREATE SEQUENCE krd.addresses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: addresses_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: -
--

ALTER SEQUENCE krd.addresses_id_seq OWNED BY krd.addresses.id;


--
-- Name: audit_log; Type: TABLE; Schema: krd; Owner: -
--

CREATE TABLE krd.audit_log (
    id integer NOT NULL,
    user_id integer NOT NULL,
    username character varying(100) NOT NULL,
    action_type character varying(50) NOT NULL,
    table_name character varying(100) NOT NULL,
    record_id integer,
    krd_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    description text
);


--
-- Name: TABLE audit_log; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON TABLE krd.audit_log IS 'Журнал аудита действий пользователей';


--
-- Name: COLUMN audit_log.id; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.audit_log.id IS 'Идентификатор записи аудита';


--
-- Name: COLUMN audit_log.user_id; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.audit_log.user_id IS 'ID пользователя из таблицы users';


--
-- Name: COLUMN audit_log.username; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.audit_log.username IS 'Имя пользователя (для истории)';


--
-- Name: COLUMN audit_log.action_type; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.audit_log.action_type IS 'Тип действия: CREATE, UPDATE, DELETE, VIEW, LOGIN, LOGOUT, EXPORT и т.д.';


--
-- Name: COLUMN audit_log.table_name; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.audit_log.table_name IS 'Название таблицы, в которой произошло изменение';


--
-- Name: COLUMN audit_log.record_id; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.audit_log.record_id IS 'ID измененной записи';


--
-- Name: COLUMN audit_log.krd_id; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.audit_log.krd_id IS 'ID КРД (для удобства фильтрации по карточкам)';


--
-- Name: COLUMN audit_log.created_at; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.audit_log.created_at IS 'Дата и время действия';


--
-- Name: audit_log_id_seq; Type: SEQUENCE; Schema: krd; Owner: -
--

CREATE SEQUENCE krd.audit_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: audit_log_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: -
--

ALTER SEQUENCE krd.audit_log_id_seq OWNED BY krd.audit_log.id;


--
-- Name: categories; Type: TABLE; Schema: krd; Owner: -
--

CREATE TABLE krd.categories (
    id integer NOT NULL,
    name character varying(100) NOT NULL
);


--
-- Name: TABLE categories; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON TABLE krd.categories IS 'Справочник категорий военнослужащих';


--
-- Name: COLUMN categories.id; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.categories.id IS 'Идентификатор категории';


--
-- Name: COLUMN categories.name; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.categories.name IS 'Категория военнослужащего';


--
-- Name: categories_id_seq; Type: SEQUENCE; Schema: krd; Owner: -
--

CREATE SEQUENCE krd.categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: categories_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: -
--

ALTER SEQUENCE krd.categories_id_seq OWNED BY krd.categories.id;


--
-- Name: document_templates; Type: TABLE; Schema: krd; Owner: -
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


--
-- Name: document_templates_id_seq; Type: SEQUENCE; Schema: krd; Owner: -
--

CREATE SEQUENCE krd.document_templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: document_templates_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: -
--

ALTER SEQUENCE krd.document_templates_id_seq OWNED BY krd.document_templates.id;


--
-- Name: field_mappings; Type: TABLE; Schema: krd; Owner: -
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


--
-- Name: COLUMN field_mappings.db_columns; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.field_mappings.db_columns IS 'JSONB массив столбцов для составных полей: [{"column": "town", "separator": ", "}, {"column": "street", "separator": ", "}, {"column": "house", "separator": ""}]';


--
-- Name: COLUMN field_mappings.is_composite; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.field_mappings.is_composite IS 'Флаг составного поля (объединяет несколько столбцов)';


--
-- Name: field_mappings_id_seq; Type: SEQUENCE; Schema: krd; Owner: -
--

CREATE SEQUENCE krd.field_mappings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: field_mappings_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: -
--

ALTER SEQUENCE krd.field_mappings_id_seq OWNED BY krd.field_mappings.id;


--
-- Name: garrisons; Type: TABLE; Schema: krd; Owner: -
--

CREATE TABLE krd.garrisons (
    id integer NOT NULL,
    name character varying(255) NOT NULL
);


--
-- Name: TABLE garrisons; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON TABLE krd.garrisons IS 'Справочник гарнизонов';


--
-- Name: COLUMN garrisons.id; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.garrisons.id IS 'Идентификатор гарнизона';


--
-- Name: COLUMN garrisons.name; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.garrisons.name IS 'Наименование: «г. Красноярск», «г. Абакан»';


--
-- Name: garrisons_id_seq; Type: SEQUENCE; Schema: krd; Owner: -
--

CREATE SEQUENCE krd.garrisons_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: garrisons_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: -
--

ALTER SEQUENCE krd.garrisons_id_seq OWNED BY krd.garrisons.id;


--
-- Name: incoming_orders; Type: TABLE; Schema: krd; Owner: -
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
    postal_index character varying(6),
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
    our_response_number character varying(100),
    is_deleted boolean DEFAULT false,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE incoming_orders; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON TABLE krd.incoming_orders IS 'Входящие поручения по КРД';


--
-- Name: COLUMN incoming_orders.id; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.incoming_orders.id IS 'Идентификатор входящего поручения';


--
-- Name: COLUMN incoming_orders.krd_id; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.incoming_orders.krd_id IS 'Ссылка на КРД';


--
-- Name: COLUMN incoming_orders.initiator_type_id; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.incoming_orders.initiator_type_id IS 'Ссылка на тип инициатора (комендатура и т.д.)';


--
-- Name: COLUMN incoming_orders.initiator_full_name; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.incoming_orders.initiator_full_name IS 'Полное наименование инициатора';


--
-- Name: COLUMN incoming_orders.military_unit_id; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.incoming_orders.military_unit_id IS 'Ссылка на военное управление (ЦВО, ВДВ и др.)';


--
-- Name: COLUMN incoming_orders.order_date; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.incoming_orders.order_date IS 'Дата поручения от инициатора';


--
-- Name: COLUMN incoming_orders.order_number; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.incoming_orders.order_number IS 'Номер поручения от инициатора';


--
-- Name: COLUMN incoming_orders.receipt_date; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.incoming_orders.receipt_date IS 'Дата поступления в комендатуру';


--
-- Name: COLUMN incoming_orders.receipt_number; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.incoming_orders.receipt_number IS 'Входящий номер в комендатуре';


--
-- Name: incoming_orders_id_seq; Type: SEQUENCE; Schema: krd; Owner: -
--

CREATE SEQUENCE krd.incoming_orders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: incoming_orders_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: -
--

ALTER SEQUENCE krd.incoming_orders_id_seq OWNED BY krd.incoming_orders.id;


--
-- Name: initiator_types; Type: TABLE; Schema: krd; Owner: -
--

CREATE TABLE krd.initiator_types (
    id integer NOT NULL,
    name character varying(100) NOT NULL
);


--
-- Name: TABLE initiator_types; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON TABLE krd.initiator_types IS 'Справочник типов инициаторов';


--
-- Name: COLUMN initiator_types.id; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.initiator_types.id IS 'Идентификатор типа инициатора';


--
-- Name: COLUMN initiator_types.name; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.initiator_types.name IS 'Тип: «Комендатура», «Воинская часть», «РУВП»';


--
-- Name: initiator_types_id_seq; Type: SEQUENCE; Schema: krd; Owner: -
--

CREATE SEQUENCE krd.initiator_types_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: initiator_types_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: -
--

ALTER SEQUENCE krd.initiator_types_id_seq OWNED BY krd.initiator_types.id;


--
-- Name: krd; Type: TABLE; Schema: krd; Owner: -
--

CREATE TABLE krd.krd (
    id integer NOT NULL,
    status_id integer,
    last_service_place_id integer,
    is_deleted boolean DEFAULT false,
    deleted_at timestamp without time zone,
    deleted_by integer,
    is_locked boolean DEFAULT false,
    locked_by integer,
    locked_at timestamp without time zone
);


--
-- Name: TABLE krd; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON TABLE krd.krd IS 'Карточки розыска военнослужащих';


--
-- Name: COLUMN krd.id; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.krd.id IS 'Внутренний идентификатор КРД';


--
-- Name: COLUMN krd.status_id; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.krd.status_id IS 'Ссылка на справочник статусов КРД';


--
-- Name: COLUMN krd.last_service_place_id; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.krd.last_service_place_id IS 'ID последнего места службы';


--
-- Name: krd_id_seq; Type: SEQUENCE; Schema: krd; Owner: -
--

CREATE SEQUENCE krd.krd_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: krd_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: -
--

ALTER SEQUENCE krd.krd_id_seq OWNED BY krd.krd.id;


--
-- Name: krd_versions; Type: TABLE; Schema: krd; Owner: -
--

CREATE TABLE krd.krd_versions (
    id integer NOT NULL,
    krd_id integer NOT NULL,
    version_number integer NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by integer,
    description text,
    snapshot_data jsonb NOT NULL
);


--
-- Name: TABLE krd_versions; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON TABLE krd.krd_versions IS 'Журнал версий КРД для отката изменений';


--
-- Name: COLUMN krd_versions.description; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.krd_versions.description IS 'Примечание: "Автосохранение", "Ручной откат", и т.п.';


--
-- Name: COLUMN krd_versions.snapshot_data; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.krd_versions.snapshot_data IS 'JSONB-снимок всех таблиц КРД (social_data, addresses, и т.д.)';


--
-- Name: krd_versions_id_seq; Type: SEQUENCE; Schema: krd; Owner: -
--

CREATE SEQUENCE krd.krd_versions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: krd_versions_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: -
--

ALTER SEQUENCE krd.krd_versions_id_seq OWNED BY krd.krd_versions.id;


--
-- Name: military_units; Type: TABLE; Schema: krd; Owner: -
--

CREATE TABLE krd.military_units (
    id integer NOT NULL,
    name character varying(100) NOT NULL
);


--
-- Name: TABLE military_units; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON TABLE krd.military_units IS 'Справочник военных управлений';


--
-- Name: COLUMN military_units.id; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.military_units.id IS 'Идентификатор военного управления';


--
-- Name: COLUMN military_units.name; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.military_units.name IS 'Наименование: «ЦВО», «ЮВО», «ВДВ»';


--
-- Name: military_units_id_seq; Type: SEQUENCE; Schema: krd; Owner: -
--

CREATE SEQUENCE krd.military_units_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: military_units_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: -
--

ALTER SEQUENCE krd.military_units_id_seq OWNED BY krd.military_units.id;


--
-- Name: outgoing_requests; Type: TABLE; Schema: krd; Owner: -
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
    recipient_id integer,
    response_date date,
    response_number character varying(100),
    response_data bytea,
    response_status character varying(50) DEFAULT 'Ожидание'::character varying
);


--
-- Name: TABLE outgoing_requests; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON TABLE krd.outgoing_requests IS 'Исходящие запросы по КРД';


--
-- Name: COLUMN outgoing_requests.id; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.outgoing_requests.id IS 'Идентификатор исходящего запроса';


--
-- Name: COLUMN outgoing_requests.krd_id; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.outgoing_requests.krd_id IS 'Ссылка на КРД';


--
-- Name: COLUMN outgoing_requests.request_type_id; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.outgoing_requests.request_type_id IS 'Ссылка на тип запроса (ЗАГС, ГИБДД и т.д.)';


--
-- Name: COLUMN outgoing_requests.issue_date; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.outgoing_requests.issue_date IS 'Дата запроса';


--
-- Name: COLUMN outgoing_requests.issue_number; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.outgoing_requests.issue_number IS 'Номер запроса';


--
-- Name: COLUMN outgoing_requests.document_data; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.outgoing_requests.document_data IS 'Содержимое сгенерированного документа в формате DOCX (бинарные данные)';


--
-- Name: COLUMN outgoing_requests.is_deleted; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.outgoing_requests.is_deleted IS 'Признак удаления запроса (мягкое удаление)';


--
-- Name: COLUMN outgoing_requests.deleted_at; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.outgoing_requests.deleted_at IS 'Дата и время удаления запроса';


--
-- Name: COLUMN outgoing_requests.deleted_by; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.outgoing_requests.deleted_by IS 'ID пользователя, удалившего запрос';


--
-- Name: outgoing_requests_id_seq; Type: SEQUENCE; Schema: krd; Owner: -
--

CREATE SEQUENCE krd.outgoing_requests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: outgoing_requests_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: -
--

ALTER SEQUENCE krd.outgoing_requests_id_seq OWNED BY krd.outgoing_requests.id;


--
-- Name: positions; Type: TABLE; Schema: krd; Owner: -
--

CREATE TABLE krd.positions (
    id integer NOT NULL,
    name character varying(100) NOT NULL
);


--
-- Name: TABLE positions; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON TABLE krd.positions IS 'Справочник воинских должностей';


--
-- Name: COLUMN positions.id; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.positions.id IS 'Идентификатор воинской должности';


--
-- Name: COLUMN positions.name; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.positions.name IS 'Должность: «Водитель», «Стрелок» и др.';


--
-- Name: positions_id_seq; Type: SEQUENCE; Schema: krd; Owner: -
--

CREATE SEQUENCE krd.positions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: positions_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: -
--

ALTER SEQUENCE krd.positions_id_seq OWNED BY krd.positions.id;


--
-- Name: ranks; Type: TABLE; Schema: krd; Owner: -
--

CREATE TABLE krd.ranks (
    id integer NOT NULL,
    name character varying(100) NOT NULL
);


--
-- Name: TABLE ranks; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON TABLE krd.ranks IS 'Справочник воинских званий';


--
-- Name: COLUMN ranks.id; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.ranks.id IS 'Идентификатор воинского звания';


--
-- Name: COLUMN ranks.name; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.ranks.name IS 'Наименование звания («Рядовой», «Лейтенант» и т.д.)';


--
-- Name: ranks_id_seq; Type: SEQUENCE; Schema: krd; Owner: -
--

CREATE SEQUENCE krd.ranks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ranks_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: -
--

ALTER SEQUENCE krd.ranks_id_seq OWNED BY krd.ranks.id;


--
-- Name: recipients; Type: TABLE; Schema: krd; Owner: -
--

CREATE TABLE krd.recipients (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    contacts character varying(255),
    postal_index character varying(6),
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
    is_deleted boolean DEFAULT false,
    request_type_id integer
);


--
-- Name: recipients_id_seq; Type: SEQUENCE; Schema: krd; Owner: -
--

CREATE SEQUENCE krd.recipients_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: recipients_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: -
--

ALTER SEQUENCE krd.recipients_id_seq OWNED BY krd.recipients.id;


--
-- Name: report_templates; Type: TABLE; Schema: krd; Owner: -
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
    usage_count integer DEFAULT 0,
    deleted_by integer,
    deleted_at timestamp without time zone
);


--
-- Name: report_templates_id_seq; Type: SEQUENCE; Schema: krd; Owner: -
--

CREATE SEQUENCE krd.report_templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: report_templates_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: -
--

ALTER SEQUENCE krd.report_templates_id_seq OWNED BY krd.report_templates.id;


--
-- Name: request_types; Type: TABLE; Schema: krd; Owner: -
--

CREATE TABLE krd.request_types (
    id integer NOT NULL,
    name character varying(100) NOT NULL
);


--
-- Name: TABLE request_types; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON TABLE krd.request_types IS 'Справочник типов запросов';


--
-- Name: COLUMN request_types.id; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.request_types.id IS 'Идентификатор типа запроса';


--
-- Name: COLUMN request_types.name; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.request_types.name IS 'Тип: «ЗАГС», «ГИБДД», «ФССП», «Военкомат»';


--
-- Name: request_types_id_seq; Type: SEQUENCE; Schema: krd; Owner: -
--

CREATE SEQUENCE krd.request_types_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: request_types_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: -
--

ALTER SEQUENCE krd.request_types_id_seq OWNED BY krd.request_types.id;


--
-- Name: service_places; Type: TABLE; Schema: krd; Owner: -
--

CREATE TABLE krd.service_places (
    id integer NOT NULL,
    krd_id integer NOT NULL,
    place_name character varying(255) NOT NULL,
    military_unit_id integer,
    garrison_id integer,
    position_id integer,
    commanders text,
    postal_index character varying(6),
    postal_region character varying(100),
    postal_district character varying(100),
    postal_town character varying(100),
    postal_street character varying(100),
    postal_house character varying(50),
    postal_building character varying(50),
    postal_letter character varying(10),
    postal_apartment character varying(50),
    postal_room character varying(50),
    place_contacts character varying(255),
    is_deleted boolean DEFAULT false,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    military_unit_number character varying(50)
);


--
-- Name: TABLE service_places; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON TABLE krd.service_places IS 'Места службы военнослужащих';


--
-- Name: COLUMN service_places.id; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.service_places.id IS 'Идентификатор места службы';


--
-- Name: COLUMN service_places.krd_id; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.service_places.krd_id IS 'Ссылка на КРД';


--
-- Name: COLUMN service_places.place_name; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.service_places.place_name IS 'Наименование места службы';


--
-- Name: COLUMN service_places.military_unit_number; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.service_places.military_unit_number IS 'Номер воинской части (например, в/ч 12345)';


--
-- Name: service_places_id_seq; Type: SEQUENCE; Schema: krd; Owner: -
--

CREATE SEQUENCE krd.service_places_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: service_places_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: -
--

ALTER SEQUENCE krd.service_places_id_seq OWNED BY krd.service_places.id;


--
-- Name: soch_episodes; Type: TABLE; Schema: krd; Owner: -
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
    notification_number character varying(100),
    is_deleted boolean DEFAULT false,
    deleted_at timestamp without time zone,
    deleted_by integer
);


--
-- Name: TABLE soch_episodes; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON TABLE krd.soch_episodes IS 'Эпизоды самовольного оставления части (СОЧ)';


--
-- Name: COLUMN soch_episodes.id; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.soch_episodes.id IS 'Идентификатор эпизода самовольного оставления части (СОЧ)';


--
-- Name: COLUMN soch_episodes.krd_id; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.soch_episodes.krd_id IS 'Ссылка на КРД';


--
-- Name: soch_episodes_id_seq; Type: SEQUENCE; Schema: krd; Owner: -
--

CREATE SEQUENCE krd.soch_episodes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: soch_episodes_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: -
--

ALTER SEQUENCE krd.soch_episodes_id_seq OWNED BY krd.soch_episodes.id;


--
-- Name: social_data; Type: TABLE; Schema: krd; Owner: -
--

CREATE TABLE krd.social_data (
    id integer NOT NULL,
    krd_id integer NOT NULL,
    surname character varying(100),
    name character varying(100),
    patronymic character varying(100),
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
    social_media_account text,
    bank_card_number character varying(19),
    passport_series character varying(4),
    passport_number character varying(6),
    passport_issue_date date,
    passport_issued_by character varying(255),
    military_id_series character varying(8),
    military_id_number character varying(10),
    military_id_issue_date date,
    military_id_issued_by character varying(255),
    appearance_features text,
    personal_marks text,
    federal_search_info text,
    military_contacts text,
    relatives_info text,
    photo_civilian bytea,
    photo_military_headgear bytea,
    photo_military_no_headgear bytea,
    photo_distinctive_marks bytea,
    is_deleted boolean DEFAULT false,
    CONSTRAINT chk_bank_card CHECK (((bank_card_number)::text ~ '^[\d\s]{16,19}$'::text)),
    CONSTRAINT chk_mil_id_number CHECK (((military_id_number)::text ~ '^\d{5,10}$'::text)),
    CONSTRAINT chk_mil_id_series CHECK (((military_id_series)::text ~ '^[A-Za-z0-9\-]{1,10}$'::text)),
    CONSTRAINT chk_passport_number CHECK (((passport_number)::text ~ '^\d{6}$'::text)),
    CONSTRAINT chk_passport_series CHECK (((passport_series)::text ~ '^\d{4}$'::text)),
    CONSTRAINT chk_social_data_bank_card CHECK ((char_length((bank_card_number)::text) <= 19)),
    CONSTRAINT chk_social_data_military_id_number CHECK ((char_length((military_id_number)::text) <= 10)),
    CONSTRAINT chk_social_data_military_id_series CHECK ((char_length((military_id_series)::text) <= 8)),
    CONSTRAINT chk_social_data_passport_number CHECK ((char_length((passport_number)::text) <= 6)),
    CONSTRAINT chk_social_data_passport_series CHECK ((char_length((passport_series)::text) <= 4))
);


--
-- Name: TABLE social_data; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON TABLE krd.social_data IS 'Социально-демографические данные военнослужащих';


--
-- Name: COLUMN social_data.id; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.social_data.id IS 'Идентификатор записи социально-демографических данных';


--
-- Name: COLUMN social_data.krd_id; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.social_data.krd_id IS 'Ссылка на карточку розыска (КРД)';


--
-- Name: COLUMN social_data.surname; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.social_data.surname IS 'Фамилия военнослужащего (обязательное поле)';


--
-- Name: COLUMN social_data.name; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.social_data.name IS 'Имя военнослужащего';


--
-- Name: COLUMN social_data.patronymic; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.social_data.patronymic IS 'Отчество военнослужащего';


--
-- Name: COLUMN social_data.photo_civilian; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.social_data.photo_civilian IS 'Фотография в гражданской одежде (BYTEA)';


--
-- Name: COLUMN social_data.photo_military_headgear; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.social_data.photo_military_headgear IS 'Фотография в военной форме с головным убором (BYTEA)';


--
-- Name: COLUMN social_data.photo_military_no_headgear; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.social_data.photo_military_no_headgear IS 'Фотография в военной форме без головного убора (BYTEA)';


--
-- Name: COLUMN social_data.photo_distinctive_marks; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.social_data.photo_distinctive_marks IS 'Фотография отличительных примет: татуировки, шрамы, отсутствие зубов, пальцев и т.д. (BYTEA)';


--
-- Name: social_data_id_seq; Type: SEQUENCE; Schema: krd; Owner: -
--

CREATE SEQUENCE krd.social_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: social_data_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: -
--

ALTER SEQUENCE krd.social_data_id_seq OWNED BY krd.social_data.id;


--
-- Name: statuses; Type: TABLE; Schema: krd; Owner: -
--

CREATE TABLE krd.statuses (
    id integer NOT NULL,
    name character varying(20) NOT NULL
);


--
-- Name: TABLE statuses; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON TABLE krd.statuses IS 'Справочник статусов КРД';


--
-- Name: COLUMN statuses.id; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.statuses.id IS 'Идентификатор статуса';


--
-- Name: COLUMN statuses.name; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.statuses.name IS 'Статус КРД: «В розыске», «Разыскан»';


--
-- Name: statuses_id_seq; Type: SEQUENCE; Schema: krd; Owner: -
--

CREATE SEQUENCE krd.statuses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: statuses_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: -
--

ALTER SEQUENCE krd.statuses_id_seq OWNED BY krd.statuses.id;


--
-- Name: user_roles; Type: TABLE; Schema: krd; Owner: -
--

CREATE TABLE krd.user_roles (
    id integer NOT NULL,
    role_name character varying(50) NOT NULL,
    description text,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: user_roles_id_seq; Type: SEQUENCE; Schema: krd; Owner: -
--

CREATE SEQUENCE krd.user_roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_roles_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: -
--

ALTER SEQUENCE krd.user_roles_id_seq OWNED BY krd.user_roles.id;


--
-- Name: user_settings; Type: TABLE; Schema: krd; Owner: -
--

CREATE TABLE krd.user_settings (
    id integer NOT NULL,
    user_id integer NOT NULL,
    theme_name character varying(50) DEFAULT 'light'::character varying,
    config_json jsonb DEFAULT '{}'::jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE user_settings; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON TABLE krd.user_settings IS 'Настройки оформления пользователей';


--
-- Name: COLUMN user_settings.config_json; Type: COMMENT; Schema: krd; Owner: -
--

COMMENT ON COLUMN krd.user_settings.config_json IS 'JSON с настройками: {"theme": "light", "colors": {...}}';


--
-- Name: user_settings_id_seq; Type: SEQUENCE; Schema: krd; Owner: -
--

CREATE SEQUENCE krd.user_settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: -
--

ALTER SEQUENCE krd.user_settings_id_seq OWNED BY krd.user_settings.id;


--
-- Name: users; Type: TABLE; Schema: krd; Owner: -
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
    last_login timestamp without time zone,
    is_deleted boolean DEFAULT false,
    deleted_at timestamp without time zone
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: krd; Owner: -
--

CREATE SEQUENCE krd.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: krd; Owner: -
--

ALTER SEQUENCE krd.users_id_seq OWNED BY krd.users.id;


--
-- Name: addresses id; Type: DEFAULT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.addresses ALTER COLUMN id SET DEFAULT nextval('krd.addresses_id_seq'::regclass);


--
-- Name: audit_log id; Type: DEFAULT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.audit_log ALTER COLUMN id SET DEFAULT nextval('krd.audit_log_id_seq'::regclass);


--
-- Name: categories id; Type: DEFAULT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.categories ALTER COLUMN id SET DEFAULT nextval('krd.categories_id_seq'::regclass);


--
-- Name: document_templates id; Type: DEFAULT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.document_templates ALTER COLUMN id SET DEFAULT nextval('krd.document_templates_id_seq'::regclass);


--
-- Name: field_mappings id; Type: DEFAULT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.field_mappings ALTER COLUMN id SET DEFAULT nextval('krd.field_mappings_id_seq'::regclass);


--
-- Name: garrisons id; Type: DEFAULT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.garrisons ALTER COLUMN id SET DEFAULT nextval('krd.garrisons_id_seq'::regclass);


--
-- Name: incoming_orders id; Type: DEFAULT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.incoming_orders ALTER COLUMN id SET DEFAULT nextval('krd.incoming_orders_id_seq'::regclass);


--
-- Name: initiator_types id; Type: DEFAULT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.initiator_types ALTER COLUMN id SET DEFAULT nextval('krd.initiator_types_id_seq'::regclass);


--
-- Name: krd id; Type: DEFAULT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.krd ALTER COLUMN id SET DEFAULT nextval('krd.krd_id_seq'::regclass);


--
-- Name: krd_versions id; Type: DEFAULT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.krd_versions ALTER COLUMN id SET DEFAULT nextval('krd.krd_versions_id_seq'::regclass);


--
-- Name: military_units id; Type: DEFAULT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.military_units ALTER COLUMN id SET DEFAULT nextval('krd.military_units_id_seq'::regclass);


--
-- Name: outgoing_requests id; Type: DEFAULT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.outgoing_requests ALTER COLUMN id SET DEFAULT nextval('krd.outgoing_requests_id_seq'::regclass);


--
-- Name: positions id; Type: DEFAULT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.positions ALTER COLUMN id SET DEFAULT nextval('krd.positions_id_seq'::regclass);


--
-- Name: ranks id; Type: DEFAULT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.ranks ALTER COLUMN id SET DEFAULT nextval('krd.ranks_id_seq'::regclass);


--
-- Name: recipients id; Type: DEFAULT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.recipients ALTER COLUMN id SET DEFAULT nextval('krd.recipients_id_seq'::regclass);


--
-- Name: report_templates id; Type: DEFAULT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.report_templates ALTER COLUMN id SET DEFAULT nextval('krd.report_templates_id_seq'::regclass);


--
-- Name: request_types id; Type: DEFAULT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.request_types ALTER COLUMN id SET DEFAULT nextval('krd.request_types_id_seq'::regclass);


--
-- Name: service_places id; Type: DEFAULT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.service_places ALTER COLUMN id SET DEFAULT nextval('krd.service_places_id_seq'::regclass);


--
-- Name: soch_episodes id; Type: DEFAULT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.soch_episodes ALTER COLUMN id SET DEFAULT nextval('krd.soch_episodes_id_seq'::regclass);


--
-- Name: social_data id; Type: DEFAULT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.social_data ALTER COLUMN id SET DEFAULT nextval('krd.social_data_id_seq'::regclass);


--
-- Name: statuses id; Type: DEFAULT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.statuses ALTER COLUMN id SET DEFAULT nextval('krd.statuses_id_seq'::regclass);


--
-- Name: user_roles id; Type: DEFAULT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.user_roles ALTER COLUMN id SET DEFAULT nextval('krd.user_roles_id_seq'::regclass);


--
-- Name: user_settings id; Type: DEFAULT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.user_settings ALTER COLUMN id SET DEFAULT nextval('krd.user_settings_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.users ALTER COLUMN id SET DEFAULT nextval('krd.users_id_seq'::regclass);


--
-- Name: addresses addresses_pkey; Type: CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.addresses
    ADD CONSTRAINT addresses_pkey PRIMARY KEY (id);


--
-- Name: audit_log audit_log_pkey; Type: CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.audit_log
    ADD CONSTRAINT audit_log_pkey PRIMARY KEY (id);


--
-- Name: categories categories_pkey; Type: CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.categories
    ADD CONSTRAINT categories_pkey PRIMARY KEY (id);


--
-- Name: document_templates document_templates_pkey; Type: CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.document_templates
    ADD CONSTRAINT document_templates_pkey PRIMARY KEY (id);


--
-- Name: field_mappings field_mappings_pkey; Type: CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.field_mappings
    ADD CONSTRAINT field_mappings_pkey PRIMARY KEY (id);


--
-- Name: garrisons garrisons_pkey; Type: CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.garrisons
    ADD CONSTRAINT garrisons_pkey PRIMARY KEY (id);


--
-- Name: incoming_orders incoming_orders_pkey; Type: CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.incoming_orders
    ADD CONSTRAINT incoming_orders_pkey PRIMARY KEY (id);


--
-- Name: initiator_types initiator_types_pkey; Type: CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.initiator_types
    ADD CONSTRAINT initiator_types_pkey PRIMARY KEY (id);


--
-- Name: krd krd_pkey; Type: CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.krd
    ADD CONSTRAINT krd_pkey PRIMARY KEY (id);


--
-- Name: krd_versions krd_versions_krd_id_version_number_key; Type: CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.krd_versions
    ADD CONSTRAINT krd_versions_krd_id_version_number_key UNIQUE (krd_id, version_number);


--
-- Name: krd_versions krd_versions_pkey; Type: CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.krd_versions
    ADD CONSTRAINT krd_versions_pkey PRIMARY KEY (id);


--
-- Name: military_units military_units_pkey; Type: CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.military_units
    ADD CONSTRAINT military_units_pkey PRIMARY KEY (id);


--
-- Name: outgoing_requests outgoing_requests_pkey; Type: CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.outgoing_requests
    ADD CONSTRAINT outgoing_requests_pkey PRIMARY KEY (id);


--
-- Name: positions positions_pkey; Type: CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.positions
    ADD CONSTRAINT positions_pkey PRIMARY KEY (id);


--
-- Name: ranks ranks_pkey; Type: CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.ranks
    ADD CONSTRAINT ranks_pkey PRIMARY KEY (id);


--
-- Name: recipients recipients_pkey; Type: CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.recipients
    ADD CONSTRAINT recipients_pkey PRIMARY KEY (id);


--
-- Name: report_templates report_templates_pkey; Type: CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.report_templates
    ADD CONSTRAINT report_templates_pkey PRIMARY KEY (id);


--
-- Name: request_types request_types_pkey; Type: CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.request_types
    ADD CONSTRAINT request_types_pkey PRIMARY KEY (id);


--
-- Name: service_places service_places_pkey; Type: CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.service_places
    ADD CONSTRAINT service_places_pkey PRIMARY KEY (id);


--
-- Name: soch_episodes soch_episodes_pkey; Type: CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.soch_episodes
    ADD CONSTRAINT soch_episodes_pkey PRIMARY KEY (id);


--
-- Name: social_data social_data_pkey; Type: CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.social_data
    ADD CONSTRAINT social_data_pkey PRIMARY KEY (id);


--
-- Name: statuses statuses_pkey; Type: CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.statuses
    ADD CONSTRAINT statuses_pkey PRIMARY KEY (id);


--
-- Name: social_data uq_social_data_krd_id; Type: CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.social_data
    ADD CONSTRAINT uq_social_data_krd_id UNIQUE (krd_id);


--
-- Name: user_roles user_roles_pkey; Type: CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.user_roles
    ADD CONSTRAINT user_roles_pkey PRIMARY KEY (id);


--
-- Name: user_roles user_roles_role_name_key; Type: CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.user_roles
    ADD CONSTRAINT user_roles_role_name_key UNIQUE (role_name);


--
-- Name: user_settings user_settings_pkey; Type: CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.user_settings
    ADD CONSTRAINT user_settings_pkey PRIMARY KEY (id);


--
-- Name: user_settings user_settings_user_id_key; Type: CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.user_settings
    ADD CONSTRAINT user_settings_user_id_key UNIQUE (user_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: idx_addresses_krd_id; Type: INDEX; Schema: krd; Owner: -
--

CREATE INDEX idx_addresses_krd_id ON krd.addresses USING btree (krd_id);


--
-- Name: idx_audit_log_action_type; Type: INDEX; Schema: krd; Owner: -
--

CREATE INDEX idx_audit_log_action_type ON krd.audit_log USING btree (action_type);


--
-- Name: idx_audit_log_created_at; Type: INDEX; Schema: krd; Owner: -
--

CREATE INDEX idx_audit_log_created_at ON krd.audit_log USING btree (created_at);


--
-- Name: idx_audit_log_krd_id; Type: INDEX; Schema: krd; Owner: -
--

CREATE INDEX idx_audit_log_krd_id ON krd.audit_log USING btree (krd_id);


--
-- Name: idx_audit_log_table_name; Type: INDEX; Schema: krd; Owner: -
--

CREATE INDEX idx_audit_log_table_name ON krd.audit_log USING btree (table_name);


--
-- Name: idx_audit_log_user_id; Type: INDEX; Schema: krd; Owner: -
--

CREATE INDEX idx_audit_log_user_id ON krd.audit_log USING btree (user_id);


--
-- Name: idx_document_templates_is_deleted; Type: INDEX; Schema: krd; Owner: -
--

CREATE INDEX idx_document_templates_is_deleted ON krd.document_templates USING btree (is_deleted);


--
-- Name: idx_field_mappings_composite; Type: INDEX; Schema: krd; Owner: -
--

CREATE INDEX idx_field_mappings_composite ON krd.field_mappings USING btree (is_composite) WHERE (is_composite = true);


--
-- Name: idx_incoming_orders_krd_id; Type: INDEX; Schema: krd; Owner: -
--

CREATE INDEX idx_incoming_orders_krd_id ON krd.incoming_orders USING btree (krd_id);


--
-- Name: idx_incoming_orders_receipt_number; Type: INDEX; Schema: krd; Owner: -
--

CREATE INDEX idx_incoming_orders_receipt_number ON krd.incoming_orders USING btree (receipt_number);


--
-- Name: idx_krd_is_deleted; Type: INDEX; Schema: krd; Owner: -
--

CREATE INDEX idx_krd_is_deleted ON krd.krd USING btree (is_deleted);


--
-- Name: idx_krd_status_id; Type: INDEX; Schema: krd; Owner: -
--

CREATE INDEX idx_krd_status_id ON krd.krd USING btree (status_id);


--
-- Name: idx_krd_versions_created; Type: INDEX; Schema: krd; Owner: -
--

CREATE INDEX idx_krd_versions_created ON krd.krd_versions USING btree (created_at DESC);


--
-- Name: idx_krd_versions_krd_id; Type: INDEX; Schema: krd; Owner: -
--

CREATE INDEX idx_krd_versions_krd_id ON krd.krd_versions USING btree (krd_id);


--
-- Name: idx_outgoing_requests_is_deleted; Type: INDEX; Schema: krd; Owner: -
--

CREATE INDEX idx_outgoing_requests_is_deleted ON krd.outgoing_requests USING btree (is_deleted);


--
-- Name: idx_outgoing_requests_krd_id; Type: INDEX; Schema: krd; Owner: -
--

CREATE INDEX idx_outgoing_requests_krd_id ON krd.outgoing_requests USING btree (krd_id);


--
-- Name: idx_recipients_request_type; Type: INDEX; Schema: krd; Owner: -
--

CREATE INDEX idx_recipients_request_type ON krd.recipients USING btree (request_type_id);


--
-- Name: idx_report_templates_deleted; Type: INDEX; Schema: krd; Owner: -
--

CREATE INDEX idx_report_templates_deleted ON krd.report_templates USING btree (is_deleted);


--
-- Name: idx_report_templates_type; Type: INDEX; Schema: krd; Owner: -
--

CREATE INDEX idx_report_templates_type ON krd.report_templates USING btree (template_type);


--
-- Name: idx_service_places_krd_id; Type: INDEX; Schema: krd; Owner: -
--

CREATE INDEX idx_service_places_krd_id ON krd.service_places USING btree (krd_id);


--
-- Name: idx_soch_episodes_krd_id; Type: INDEX; Schema: krd; Owner: -
--

CREATE INDEX idx_soch_episodes_krd_id ON krd.soch_episodes USING btree (krd_id);


--
-- Name: idx_soch_episodes_soch_date; Type: INDEX; Schema: krd; Owner: -
--

CREATE INDEX idx_soch_episodes_soch_date ON krd.soch_episodes USING btree (soch_date);


--
-- Name: idx_social_data_krd_id; Type: INDEX; Schema: krd; Owner: -
--

CREATE INDEX idx_social_data_krd_id ON krd.social_data USING btree (krd_id);


--
-- Name: idx_social_data_personal_number; Type: INDEX; Schema: krd; Owner: -
--

CREATE INDEX idx_social_data_personal_number ON krd.social_data USING btree (personal_number);


--
-- Name: idx_social_data_photos; Type: INDEX; Schema: krd; Owner: -
--

CREATE INDEX idx_social_data_photos ON krd.social_data USING btree (krd_id) WHERE ((photo_civilian IS NOT NULL) OR (photo_military_headgear IS NOT NULL) OR (photo_military_no_headgear IS NOT NULL) OR (photo_distinctive_marks IS NOT NULL));


--
-- Name: idx_social_data_surname; Type: INDEX; Schema: krd; Owner: -
--

CREATE INDEX idx_social_data_surname ON krd.social_data USING btree (surname);


--
-- Name: idx_user_settings_user_id; Type: INDEX; Schema: krd; Owner: -
--

CREATE INDEX idx_user_settings_user_id ON krd.user_settings USING btree (user_id);


--
-- Name: idx_users_role_id; Type: INDEX; Schema: krd; Owner: -
--

CREATE INDEX idx_users_role_id ON krd.users USING btree (role_id);


--
-- Name: idx_users_username; Type: INDEX; Schema: krd; Owner: -
--

CREATE INDEX idx_users_username ON krd.users USING btree (username);


--
-- Name: addresses addresses_krd_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.addresses
    ADD CONSTRAINT addresses_krd_id_fkey FOREIGN KEY (krd_id) REFERENCES krd.krd(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: krd fk_last_service_place; Type: FK CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.krd
    ADD CONSTRAINT fk_last_service_place FOREIGN KEY (last_service_place_id) REFERENCES krd.service_places(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: report_templates fk_report_templates_deleted_by; Type: FK CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.report_templates
    ADD CONSTRAINT fk_report_templates_deleted_by FOREIGN KEY (deleted_by) REFERENCES krd.users(id);


--
-- Name: incoming_orders incoming_orders_initiator_type_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.incoming_orders
    ADD CONSTRAINT incoming_orders_initiator_type_id_fkey FOREIGN KEY (initiator_type_id) REFERENCES krd.initiator_types(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: incoming_orders incoming_orders_krd_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.incoming_orders
    ADD CONSTRAINT incoming_orders_krd_id_fkey FOREIGN KEY (krd_id) REFERENCES krd.krd(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: incoming_orders incoming_orders_military_unit_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.incoming_orders
    ADD CONSTRAINT incoming_orders_military_unit_id_fkey FOREIGN KEY (military_unit_id) REFERENCES krd.military_units(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: krd krd_locked_by_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.krd
    ADD CONSTRAINT krd_locked_by_fkey FOREIGN KEY (locked_by) REFERENCES krd.users(id);


--
-- Name: krd krd_status_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.krd
    ADD CONSTRAINT krd_status_id_fkey FOREIGN KEY (status_id) REFERENCES krd.statuses(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: krd_versions krd_versions_created_by_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.krd_versions
    ADD CONSTRAINT krd_versions_created_by_fkey FOREIGN KEY (created_by) REFERENCES krd.users(id) ON DELETE SET NULL;


--
-- Name: krd_versions krd_versions_krd_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.krd_versions
    ADD CONSTRAINT krd_versions_krd_id_fkey FOREIGN KEY (krd_id) REFERENCES krd.krd(id) ON DELETE CASCADE;


--
-- Name: outgoing_requests outgoing_requests_krd_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.outgoing_requests
    ADD CONSTRAINT outgoing_requests_krd_id_fkey FOREIGN KEY (krd_id) REFERENCES krd.krd(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: outgoing_requests outgoing_requests_military_unit_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.outgoing_requests
    ADD CONSTRAINT outgoing_requests_military_unit_id_fkey FOREIGN KEY (military_unit_id) REFERENCES krd.military_units(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: outgoing_requests outgoing_requests_recipient_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.outgoing_requests
    ADD CONSTRAINT outgoing_requests_recipient_id_fkey FOREIGN KEY (recipient_id) REFERENCES krd.recipients(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: outgoing_requests outgoing_requests_request_type_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.outgoing_requests
    ADD CONSTRAINT outgoing_requests_request_type_id_fkey FOREIGN KEY (request_type_id) REFERENCES krd.request_types(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: recipients recipients_request_type_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.recipients
    ADD CONSTRAINT recipients_request_type_id_fkey FOREIGN KEY (request_type_id) REFERENCES krd.request_types(id) ON DELETE SET NULL;


--
-- Name: service_places service_places_garrison_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.service_places
    ADD CONSTRAINT service_places_garrison_id_fkey FOREIGN KEY (garrison_id) REFERENCES krd.garrisons(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: service_places service_places_krd_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.service_places
    ADD CONSTRAINT service_places_krd_id_fkey FOREIGN KEY (krd_id) REFERENCES krd.krd(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: service_places service_places_military_unit_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.service_places
    ADD CONSTRAINT service_places_military_unit_id_fkey FOREIGN KEY (military_unit_id) REFERENCES krd.military_units(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: service_places service_places_position_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.service_places
    ADD CONSTRAINT service_places_position_id_fkey FOREIGN KEY (position_id) REFERENCES krd.positions(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: soch_episodes soch_episodes_deleted_by_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.soch_episodes
    ADD CONSTRAINT soch_episodes_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES krd.users(id);


--
-- Name: soch_episodes soch_episodes_krd_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.soch_episodes
    ADD CONSTRAINT soch_episodes_krd_id_fkey FOREIGN KEY (krd_id) REFERENCES krd.krd(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: social_data social_data_category_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.social_data
    ADD CONSTRAINT social_data_category_id_fkey FOREIGN KEY (category_id) REFERENCES krd.categories(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: social_data social_data_krd_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.social_data
    ADD CONSTRAINT social_data_krd_id_fkey FOREIGN KEY (krd_id) REFERENCES krd.krd(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: social_data social_data_rank_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.social_data
    ADD CONSTRAINT social_data_rank_id_fkey FOREIGN KEY (rank_id) REFERENCES krd.ranks(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: user_settings user_settings_user_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.user_settings
    ADD CONSTRAINT user_settings_user_id_fkey FOREIGN KEY (user_id) REFERENCES krd.users(id) ON DELETE CASCADE;


--
-- Name: users users_role_id_fkey; Type: FK CONSTRAINT; Schema: krd; Owner: -
--

ALTER TABLE ONLY krd.users
    ADD CONSTRAINT users_role_id_fkey FOREIGN KEY (role_id) REFERENCES krd.user_roles(id) ON DELETE RESTRICT;


--
-- PostgreSQL database dump complete
--

\unrestrict OzeazLUpjJjo4CU9mvebXjvMYc8sIaATU73uYD1h78PLzr97zVjKAxDOJ34KamF

