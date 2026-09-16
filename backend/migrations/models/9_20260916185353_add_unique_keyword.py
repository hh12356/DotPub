from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `useraccount` ADD UNIQUE INDEX `user_phone` (`user_phone`);
        ALTER TABLE `useraccount` ADD UNIQUE INDEX `user_name` (`user_name`);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `useraccount` DROP INDEX `user_name`;
        ALTER TABLE `useraccount` DROP INDEX `user_phone`;"""


MODELS_STATE = (
    "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"
    "uNaM0CaxZYWVBBhVjg8/+4n4Li"
)
