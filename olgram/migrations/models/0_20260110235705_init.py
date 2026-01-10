from tortoise import BaseDBAsyncClient


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
