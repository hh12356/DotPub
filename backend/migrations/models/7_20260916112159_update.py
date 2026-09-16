from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `useraccount` ADD `is_silence` BOOL NOT NULL COMMENT '禁言' DEFAULT 0;
        ALTER TABLE `useraccount` ADD `is_banned` BOOL NOT NULL COMMENT '封号' DEFAULT 0;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `useraccount` DROP COLUMN `is_silence`;
        ALTER TABLE `useraccount` DROP COLUMN `is_banned`;"""


MODELS_STATE = (
    "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"
    "Ya0VoF1iqwsqCCCqnA5/8ByDqFlg=="
)
