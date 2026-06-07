from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "bot" ADD "captcha_type" TEXT;
        ALTER TABLE "bot" ADD "captcha_tag" TEXT;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "bot" DROP COLUMN "captcha_type";
        ALTER TABLE "bot" DROP COLUMN "captcha_tag";"""


MODELS_STATE = (
    "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"
)
