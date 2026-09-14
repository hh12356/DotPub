from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `useraccount` ADD `user_bio` VARCHAR(100) NOT NULL COMMENT '用户简介' DEFAULT '';
        ALTER TABLE `useraccount` ADD `user_join_date` DATETIME(6) COMMENT '加入时间' DEFAULT NULL;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `useraccount` DROP COLUMN `user_bio`;
        ALTER TABLE `useraccount` DROP COLUMN `user_join_date`;"""


MODELS_STATE = (
    "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"
    "VBhRVigbP/ARBaGQc="
)
