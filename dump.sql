--
-- PostgreSQL database dump
--

-- Dumped from database version 14.0
-- Dumped by pg_dump version 14.0

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
-- Name: exchangeraterubusd; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.exchangeraterubusd (
    id integer NOT NULL,
    rate double precision NOT NULL
);


ALTER TABLE public.exchangeraterubusd OWNER TO postgres;

--
-- Name: exchangeraterubusd_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.exchangeraterubusd_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.exchangeraterubusd_id_seq OWNER TO postgres;

--
-- Name: exchangeraterubusd_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.exchangeraterubusd_id_seq OWNED BY public.exchangeraterubusd.id;


--
-- Name: orders; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.orders (
    num integer NOT NULL,
    ordernum integer NOT NULL,
    costusd double precision NOT NULL,
    shipmentdate date NOT NULL,
    costrub double precision NOT NULL
);


ALTER TABLE public.orders OWNER TO postgres;

--
-- Name: exchangeraterubusd id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.exchangeraterubusd ALTER COLUMN id SET DEFAULT nextval('public.exchangeraterubusd_id_seq'::regclass);




SELECT pg_catalog.setval('public.exchangeraterubusd_id_seq', 1, true);


--
-- Name: exchangeraterubusd exchangeraterubusd_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.exchangeraterubusd
    ADD CONSTRAINT exchangeraterubusd_pkey PRIMARY KEY (id);


--
-- Name: orders orders_ordernum_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_ordernum_key UNIQUE (ordernum);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (num);


--
-- PostgreSQL database dump complete
--

