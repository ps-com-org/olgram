from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "group_chat" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "chat_id" BIGINT NOT NULL UNIQUE,
    "name" VARCHAR(255) NOT NULL
);
CREATE INDEX IF NOT EXISTS "idx_group_chat_chat_id_5da32d" ON "group_chat" ("chat_id");
CREATE TABLE IF NOT EXISTS "_custom_meta_info" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" INT NOT NULL  DEFAULT 0
);
CREATE TABLE IF NOT EXISTS "user" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "telegram_id" BIGINT NOT NULL UNIQUE
);
CREATE INDEX IF NOT EXISTS "idx_user_telegra_66ffbd" ON "user" ("telegram_id");
CREATE TABLE IF NOT EXISTS "bot" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "token" VARCHAR(200) NOT NULL UNIQUE,
    "name" VARCHAR(33) NOT NULL,
    "code" UUID NOT NULL,
    "start_text" TEXT NOT NULL,
    "second_text" TEXT,
    "incoming_messages_count" BIGINT NOT NULL  DEFAULT 0,
    "outgoing_messages_count" BIGINT NOT NULL  DEFAULT 0,
    "enable_threads" BOOL NOT NULL  DEFAULT False,
    "enable_additional_info" BOOL NOT NULL  DEFAULT False,
    "enable_olgram_text" BOOL NOT NULL  DEFAULT True,
    "enable_antiflood" BOOL NOT NULL  DEFAULT False,
    "enable_always_second_message" BOOL NOT NULL  DEFAULT False,
    "enable_thread_interrupt" BOOL NOT NULL  DEFAULT True,
    "enable_mailing" BOOL NOT NULL  DEFAULT False,
    "enable_tags" BOOL NOT NULL  DEFAULT False,
    "last_mailing_at" TIMESTAMPTZ,
    "group_chat_id" INT REFERENCES "group_chat" ("id") ON DELETE CASCADE,
    "owner_id" INT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_bot_code_a43015" ON "bot" ("code");
CREATE TABLE IF NOT EXISTS "bot_banned_user" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "telegram_id" BIGINT NOT NULL,
    "username" VARCHAR(100),
    "bot_id" INT NOT NULL REFERENCES "bot" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_bot_banned__telegra_915aca" ON "bot_banned_user" ("telegram_id");
CREATE TABLE IF NOT EXISTS "bot_second_message" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "locale" VARCHAR(15) NOT NULL,
    "text" TEXT NOT NULL,
    "bot_id" INT NOT NULL REFERENCES "bot" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_bot_second__bot_id_432892" UNIQUE ("bot_id", "locale")
);
CREATE TABLE IF NOT EXISTS "bot_start_message" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "locale" VARCHAR(15) NOT NULL,
    "text" TEXT NOT NULL,
    "bot_id" INT NOT NULL REFERENCES "bot" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_bot_start_m_bot_id_871cd1" UNIQUE ("bot_id", "locale")
);
CREATE TABLE IF NOT EXISTS "defaultanswer" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "text" TEXT NOT NULL,
    "bot_id" INT NOT NULL REFERENCES "bot" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "mailinguser" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "telegram_id" BIGINT NOT NULL,
    "bot_id" INT NOT NULL REFERENCES "bot" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_mailinguser_bot_id_906a76" UNIQUE ("bot_id", "telegram_id")
);
CREATE INDEX IF NOT EXISTS "idx_mailinguser_telegra_55de60" ON "mailinguser" ("telegram_id");
CREATE TABLE IF NOT EXISTS "promo" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "code" UUID NOT NULL,
    "date" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "owner_id" INT REFERENCES "user" ("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "idx_promo_code_9b981a" ON "promo" ("code");
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "bot_group_chat" (
    "bot_id" INT NOT NULL REFERENCES "bot" ("id") ON DELETE CASCADE,
    "groupchat_id" INT NOT NULL REFERENCES "group_chat" ("id") ON DELETE CASCADE
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
    "M1fMvJmZn/8Do7b97Q=="
)
