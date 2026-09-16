from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `article` ADD `is_pinned` BOOL NOT NULL COMMENT '是否置顶' DEFAULT 0;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `article` DROP COLUMN `is_pinned`;"""


MODELS_STATE = (
    "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"
)
