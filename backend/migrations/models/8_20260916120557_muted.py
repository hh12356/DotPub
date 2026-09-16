from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `useraccount` RENAME COLUMN `is_silence` TO `is_muted`;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `useraccount` RENAME COLUMN `is_muted` TO `is_silence`;"""


MODELS_STATE = (
    "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"
    "Naq8BaBVYWVFAhFfj8PxXghA4="
)
