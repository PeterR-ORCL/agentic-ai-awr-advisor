--------------------------------------------------------------------------------
-- ddlv9_parser_vector_layer.sql
--
-- Additive parser-evolution persistence layer for agentic-ai-awr-advisor.
--
-- Notes:
--   * AWR_REPORT already contains OBJECT_STORE_URI, which this phase reuses as
--     the persisted raw-source Object Storage URI field. No AWR_REPORT ALTER is
--     required for this pass.
--   * VECTOR columns use flexible FLOAT32 storage so externally generated
--     embeddings can evolve without schema churn.
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
-- 1. PARSER UNKNOWNS
--------------------------------------------------------------------------------
CREATE TABLE AWR_PARSER_UNKNOWN (
    UNKNOWN_ID               NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    AWR_ID                   NUMBER                NOT NULL,
    PARSER_STAGE             VARCHAR2(128)         NOT NULL,
    RAW_TEXT                 VARCHAR2(4000)        NOT NULL,
    CONTEXT_BEFORE           JSON,
    CONTEXT_AFTER            JSON,
    DETECTED_AT              TIMESTAMP(6) DEFAULT SYSTIMESTAMP NOT NULL,
    STATUS                   VARCHAR2(32) DEFAULT 'NEW' NOT NULL,
    EMBEDDING                VECTOR(*, FLOAT32),
    CONSTRAINT FK_AWR_PARSER_UNKNOWN_AWR
        FOREIGN KEY (AWR_ID)
        REFERENCES AWR_REPORT (AWR_ID),
    CONSTRAINT CK_AWR_PARSER_UNKNOWN_STATUS
        CHECK (STATUS IN ('NEW', 'REVIEWED', 'PROMOTED'))
);

CREATE INDEX IX_AWR_PARSER_UNKNOWN_AWR
    ON AWR_PARSER_UNKNOWN (AWR_ID, DETECTED_AT);

CREATE INDEX IX_AWR_PARSER_UNKNOWN_STATUS
    ON AWR_PARSER_UNKNOWN (STATUS, DETECTED_AT);

--------------------------------------------------------------------------------
-- 2. PARSER KNOWLEDGE
--------------------------------------------------------------------------------
CREATE TABLE AWR_PARSER_KNOWLEDGE (
    KNOWLEDGE_ID             NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    CONCEPT_TYPE             VARCHAR2(64)          NOT NULL,
    CANONICAL_NAME           VARCHAR2(256)         NOT NULL,
    ALIASES_JSON             JSON,
    DESCRIPTION              VARCHAR2(4000),
    CREATED_AT               TIMESTAMP(6) DEFAULT SYSTIMESTAMP NOT NULL,
    UPDATED_AT               TIMESTAMP(6) DEFAULT SYSTIMESTAMP NOT NULL,
    EMBEDDING                VECTOR(*, FLOAT32),
    CONSTRAINT UK_AWR_PARSER_KNOWLEDGE_01
        UNIQUE (CONCEPT_TYPE, CANONICAL_NAME),
    CONSTRAINT CK_AWR_PARSER_KNOWLEDGE_TYPE
        CHECK (CONCEPT_TYPE IN ('SECTION', 'METRIC', 'LABEL'))
);

CREATE INDEX IX_AWR_PARSER_KNOWLEDGE_TYPE
    ON AWR_PARSER_KNOWLEDGE (CONCEPT_TYPE, CANONICAL_NAME);

--------------------------------------------------------------------------------
-- 3. VECTOR INDEXES (HNSW)
--------------------------------------------------------------------------------
CREATE VECTOR INDEX VIDX_AWR_PARSER_UNKNOWN_HNSW
    ON AWR_PARSER_UNKNOWN (EMBEDDING)
    ORGANIZATION INMEMORY NEIGHBOR GRAPH
    DISTANCE COSINE
    WITH TARGET ACCURACY 90;

CREATE VECTOR INDEX VIDX_AWR_PARSER_KNOWLEDGE_HNSW
    ON AWR_PARSER_KNOWLEDGE (EMBEDDING)
    ORGANIZATION INMEMORY NEIGHBOR GRAPH
    DISTANCE COSINE
    WITH TARGET ACCURACY 90;
