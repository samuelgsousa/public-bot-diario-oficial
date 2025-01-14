--
-- PostgreSQL database dump
--

-- Dumped from database version 17.2
-- Dumped by pg_dump version 17.2

-- Started on 2025-01-08 09:39:05

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 853 (class 1247 OID 16553)
-- Name: status_tipo; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.status_tipo AS ENUM (
    'concluído',
    'interrompido',
    'não concluído'
);


ALTER TYPE public.status_tipo OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 224 (class 1259 OID 24582)
-- Name: contas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.contas (
    id integer NOT NULL,
    usuario character varying(50),
    senha character varying(50),
    limite_atingido boolean DEFAULT false,
    data_limite date
);


ALTER TABLE public.contas OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 24581)
-- Name: contas_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.contas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.contas_id_seq OWNER TO postgres;

--
-- TOC entry 4888 (class 0 OID 0)
-- Dependencies: 223
-- Name: contas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.contas_id_seq OWNED BY public.contas.id;


--
-- TOC entry 217 (class 1259 OID 16559)
-- Name: dje_process_numbers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dje_process_numbers (
    id integer NOT NULL,
    cod_processo character varying(38),
    range_ini timestamp without time zone,
    range_end timestamp without time zone,
    num_req integer DEFAULT 0,
    last_req integer DEFAULT 1,
    processado boolean DEFAULT false
);


ALTER TABLE public.dje_process_numbers OWNER TO postgres;

--
-- TOC entry 218 (class 1259 OID 16565)
-- Name: dje_process_numbers_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.dje_process_numbers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dje_process_numbers_id_seq OWNER TO postgres;

--
-- TOC entry 4889 (class 0 OID 0)
-- Dependencies: 218
-- Name: dje_process_numbers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.dje_process_numbers_id_seq OWNED BY public.dje_process_numbers.id;


--
-- TOC entry 219 (class 1259 OID 16566)
-- Name: historico_exec; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.historico_exec (
    id integer NOT NULL,
    palavra_chave text,
    prec_encontrados integer,
    data_inicio timestamp without time zone,
    data_fim timestamp without time zone,
    status public.status_tipo DEFAULT 'não concluído'::public.status_tipo,
    pagina_atual integer DEFAULT 1,
    mensagens_erro text,
    data_exec timestamp with time zone DEFAULT now(),
    paginacao_conc boolean DEFAULT false
);


ALTER TABLE public.historico_exec OWNER TO postgres;

--
-- TOC entry 220 (class 1259 OID 16575)
-- Name: historico_exec_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.historico_exec_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.historico_exec_id_seq OWNER TO postgres;

--
-- TOC entry 4890 (class 0 OID 0)
-- Dependencies: 220
-- Name: historico_exec_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.historico_exec_id_seq OWNED BY public.historico_exec.id;


--
-- TOC entry 221 (class 1259 OID 16576)
-- Name: req_pagamentos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.req_pagamentos (
    id integer NOT NULL,
    nome_req character varying(150),
    cpf_req character varying(150),
    cod_processo character varying(38),
    seq integer,
    advogado character varying(150),
    valor_processo numeric,
    data_doc date,
    "data_emissão_termo_dec" date,
    ent_devedora character varying(250),
    princ_liq numeric,
    link text,
    exportado boolean DEFAULT false
);


ALTER TABLE public.req_pagamentos OWNER TO postgres;

--
-- TOC entry 222 (class 1259 OID 16582)
-- Name: req_pagamentos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.req_pagamentos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.req_pagamentos_id_seq OWNER TO postgres;

--
-- TOC entry 4891 (class 0 OID 0)
-- Dependencies: 222
-- Name: req_pagamentos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.req_pagamentos_id_seq OWNED BY public.req_pagamentos.id;


--
-- TOC entry 4724 (class 2604 OID 24585)
-- Name: contas id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contas ALTER COLUMN id SET DEFAULT nextval('public.contas_id_seq'::regclass);


--
-- TOC entry 4713 (class 2604 OID 16583)
-- Name: dje_process_numbers id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dje_process_numbers ALTER COLUMN id SET DEFAULT nextval('public.dje_process_numbers_id_seq'::regclass);


--
-- TOC entry 4717 (class 2604 OID 16584)
-- Name: historico_exec id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.historico_exec ALTER COLUMN id SET DEFAULT nextval('public.historico_exec_id_seq'::regclass);


--
-- TOC entry 4722 (class 2604 OID 16585)
-- Name: req_pagamentos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.req_pagamentos ALTER COLUMN id SET DEFAULT nextval('public.req_pagamentos_id_seq'::regclass);


--
-- TOC entry 4737 (class 2606 OID 24588)
-- Name: contas contas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contas
    ADD CONSTRAINT contas_pkey PRIMARY KEY (id);


--
-- TOC entry 4727 (class 2606 OID 16587)
-- Name: dje_process_numbers dje_process_numbers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dje_process_numbers
    ADD CONSTRAINT dje_process_numbers_pkey PRIMARY KEY (id);


--
-- TOC entry 4731 (class 2606 OID 16589)
-- Name: historico_exec historico_exec_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.historico_exec
    ADD CONSTRAINT historico_exec_pkey PRIMARY KEY (id);


--
-- TOC entry 4733 (class 2606 OID 16591)
-- Name: req_pagamentos req_pagamentos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.req_pagamentos
    ADD CONSTRAINT req_pagamentos_pkey PRIMARY KEY (id);


--
-- TOC entry 4729 (class 2606 OID 16593)
-- Name: dje_process_numbers unique_cod_processo; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dje_process_numbers
    ADD CONSTRAINT unique_cod_processo UNIQUE (cod_processo);


--
-- TOC entry 4735 (class 2606 OID 16595)
-- Name: req_pagamentos unique_cod_processo_seq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.req_pagamentos
    ADD CONSTRAINT unique_cod_processo_seq UNIQUE (cod_processo, seq);


-- Completed on 2025-01-08 09:39:05

--
-- PostgreSQL database dump complete
--

