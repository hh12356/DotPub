from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `article` (
    `art_id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `art_title` VARCHAR(32) NOT NULL COMMENT '文章标题',
    `art_pub_datetime` DATETIME(6) NOT NULL COMMENT '文章发布时间',
    `art_content` LONGTEXT NOT NULL COMMENT '文章内容',
    `art_author_id` INT NOT NULL COMMENT '文章作者id',
    CONSTRAINT `fk_article_useracco_893c0478` FOREIGN KEY (`art_author_id`) REFERENCES `useraccount` (`user_id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `article`;"""


MODELS_STATE = (
    "eJztmW1zmzgQx78Ko1fpjK8D2DzE70jiXHNt7JuEPkxLhxEg20yx5ArpEk/q796RAIMBOy"
    "Zzd3E6feldrZB+f7S7wg9gQSKUpK/fp4g6YUg4ZmCoPAAMFwgMlTZ3TwFwuSydwsBgkMjx"
    "PEUUVgYGKaMwFHNOYZKingIilIY0XrKYYDBUME8SYSRhymiMZ6WJ4/g7Rz4jM8TmiIKh8u"
    "VrTwExjtA9Soufy2/+NEZJtLVosQg/jsQCpNNnq6V0XGF2KUeLRwZ+SBK+wLWI5YrNCd6E"
    "xNlGZggjChkSD2KUi42IdebbLvaWrbkcki22EhOhKeQJq2w88Esb8P3xxPVvR67vgw6oQo"
    "IF5hgzweUBzMQS/tC1gTWw++bA7ilALnNjsdbZo0s6WaBkNHbBWvohg9kISbuGV/5oAD6f"
    "Q7qHcBFUY5wyWmdcEN0HuTCUlMt37OmYgcctQ7c9bup9y+PGQM028zj2Bbz3E4RnbA6GSl"
    "/fw/iDc3P+xrk56euvxNyEwjA7PuPco0uXkKGGfXkXdaaex7wk6EFoetyyVe2Y0M8J7v7K"
    "b6JeEH5THwQeN60+9LjRn1pPEUHTDhBB03aKIFzrtUjx0zzFb3J+AMNvd5BG/panVAtSFo"
    "cJSptaneWRl29vUALl5pvK5CXPyWY5KpFMw7Y8bkGkenwwNUKP26pqZHXrcYFyQUprXpck"
    "ZaKTXZibroW+qFsghjO5VfFs8aQCI6JxOG/rKXLP3nYClmOepZPo1ET87h8O6x/+QTTNj9"
    "6hqbQScsx59HDEW7lSN4wDkqVuGDuzpfRt1yxxqDoQzof/gnQ1VT2kFKnq7lokfNt0Q4IZ"
    "yo72NuG/bifjdsKVkBrlKA6Z8kNJ4pS9QNp74AoYYuZFmn5PqkxPrp1Pddzn7yZnEg5J2Y"
    "zKWeQEZ936gP+0mOU9QVs1K9uFPeWsMuhZ6hmkrNvFuAz4Xdceq2uCFYtZpu/BebcadMzZ"
    "t9Z+mrZqefzUPrWP44omOC554EeQIRa3fZu4yD27dajH19N07npdHXOU4hj9SPO4gdS+sE"
    "9Nj58a08GBQlEEowlOVsXtYLdQ7tX16NZ1rv/eyvEXjjsSHl1aVzXriVkTdTOJ8vHKfaOI"
    "n8rnyXhULwWbce5nINYEOSM+Jnc+jCqJpLAWXBvvyM7C7aL7PTlwd/E+5kNqaLYhvqYEp5"
    "1uiK1ajz65+0v5Rup3k/GfxfB6fW8eWsjZnHT8XNuIe7w4veB7+79RtxoNVJsITQUuCUXx"
    "DL9FKynEFU4ZxGFbcmz/o+AX/3LSUwCFd5s+q/leEuxHKEEsawKc23PnYgSkGP9X87r+CS"
    "sTQeA="
)
