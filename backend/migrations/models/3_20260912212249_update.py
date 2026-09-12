from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `comment` (
    `cmt_id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `cmt_pub_datetime` DATETIME(6) NOT NULL COMMENT '评论发布时间',
    `cmt_content` LONGTEXT NOT NULL COMMENT '评论内容',
    `cmt_art_id` INT NOT NULL COMMENT '评论文章id',
    `cmt_user_id` INT NOT NULL COMMENT '评论作者id',
    CONSTRAINT `fk_comment_article_9c6357b9` FOREIGN KEY (`cmt_art_id`) REFERENCES `article` (`art_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_comment_useracco_439ff682` FOREIGN KEY (`cmt_user_id`) REFERENCES `useraccount` (`user_id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `articlelike` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL COMMENT '点赞时间',
    `art_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    UNIQUE KEY `uid_articlelike_user_id_fd6a92` (`user_id`, `art_id`),
    CONSTRAINT `fk_articlel_article_f51457b0` FOREIGN KEY (`art_id`) REFERENCES `article` (`art_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_articlel_useracco_15405f1c` FOREIGN KEY (`user_id`) REFERENCES `useraccount` (`user_id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `articlestar` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL COMMENT '收藏时间',
    `art_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    UNIQUE KEY `uid_articlestar_user_id_e5ba57` (`user_id`, `art_id`),
    CONSTRAINT `fk_articles_article_cbf46f4e` FOREIGN KEY (`art_id`) REFERENCES `article` (`art_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_articles_useracco_5b48f613` FOREIGN KEY (`user_id`) REFERENCES `useraccount` (`user_id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `articlestar`;
        DROP TABLE IF EXISTS `comment`;
        DROP TABLE IF EXISTS `articlelike`;"""


MODELS_STATE = (
    "eJztW11vozgU/SuIp67UHRESCOlb2qY73WmTVZvdHc0wQgacBJWYjLGnrbr57ysbCB+BBN"
    "pkSjK8VIqvrzHnmnvPudAXce7Z0PU//O1D3LcsjyIingkvIgJzKJ4JeeZTQQSLRWxkAwSY"
    "Lp9PfYhBYqLpEwwstuYEuD48FUQb+hZ2FsTxkHgmIOq6bNCzfIIdNI2HKHK+U2gQbwrJDG"
    "LxTPj67VQQHWTDJ+hHPxcPxsSBrp3aNNuE4dhsA9xokOcFN1wjcsVns0uahuW5dI4yHotn"
    "MvPQysUJbmQKEcSAQHYhgim7EbbP8Lajewv2HE8JNpvwseEEUJckbtw04jHRMIajsXE/GB"
    "uGWAEqy0MMZgcRhsuLOGVb+F1udbodra12tFNB5NtcjXSXwaVjdAJHjtFwLC65HRAQzOBo"
    "Z+DlP9YAvpgBvAHhyCmDsU9wFuMI0U0gRwMxyvEZez3Mok67iqzpVJXbXZ0qHSm4me2wz8"
    "GT4UI0JTPxTGjLGzD+p3938bF/d9KWf2NrexhYweMzDC0yN7EwZGBfPNqVUQ99Dgl001J1"
    "2tWkVp2gn3mo+pFfeR0Q/KrcMXWqdttAp0p70n1NEFqtEkFotQqDwEzLJUvxkzDFr3K+Ca"
    "yHR4BtI2WJowUwcSwX+uuxOg89rz7dQRfwm1+PTFjy+sEqtQqSqmhdnXYBlHTamSiWTjVJ"
    "UoK6tT1AYUDi0bAupY665c3nkDm8CbyLYJVagaeZVof9NcHewHOdB2hgaHnY3s3pu3Eean"
    "QCSzOQUmD5BOCdgnVPAD4msFiu82SvKPutm+byPDsCEJjyW2LXZleKIIPYsWZ5VD+0bGT5"
    "IJ7zLgS/ErdvaH05Wv8DYj98zMoynIRLnelNeYhTFEZWlBIcRlaUQhLDbWkqyR6qCgiH04"
    "8Q3ZYklWGIklRMEZktja7lIRLyjjTCf96PhvkIJ1wyKNuORYT/BNfxyeGWlTxwGRhs5bnv"
    "f3eTmJ7c9j9n4b64GZ1zcDyfTDFfhS9wXo2e77WYhVQ9r5rFLH5DOUtMepd6BjCp1q+KHZ"
    "q6tq2uMayIQ4L4ls67Sac6Z9+MKlQ1qavTntbT6tE5YTguqGnYgEDi5LUML0NLcRyy/tk0"
    "HZo+JOfUMjhK227pVIFSm41PVJ32lEmnZKAwBPYIuc+xlCoK1Pj6dnA/7t/+lcrxl/3xgF"
    "lkPvqcGT1RM0FdLSL8ez3+KLCfwpfRcJAtBat54y8i2xOgxDOQ92gAO5FIotEI17UzUli4"
    "x/BpQw4sLt51fkiVlqawJqfZq9R7yI314PN4cylfhfpmNPwjmp6t7+sPLaBk5lV8i7Lmt7"
    "041SYm1TtCu6hbawQqLwjrEbjyMHSm6BN85oG4Rj4ByMpLjvnv744kAkWdk1NBxOBxxbPW"
    "z6WHDBu6kAQkoH9/0b8ciMsyveVfoz0ah6Vpjzbt0ZqCtU9FGT2gOYoy8ewWK8owTbyfor"
    "TmFRVl7NAoym2KkmH1FlGT539QoiZZKxpRkytqWIxfIWoybjUXNalzUHNRw5Ct3GdLO9Vc"
    "zryNwe0maabxrv4hXsbrgBCvnYCMoDxi+bifTzqy8jFzJvPFY06q2QHwdfwIaT9CMQ/0OP"
    "NWFew/4W0T157Fb5wiabr1rRMTxbvXCV/514d8XUzEb82HFe8pFzBkSBiAVBYKKc+Dkghd"
    "yezpVLMV2MiCn/Wm9wC6ObtmmXv+V49fBNENLPKYGeSbe5BZ0lKJJR4pQ9w5qLVmgbypXs"
    "wCo577VhbIuv0NC2xY4JGxQFVpqzrVFGvSsMCGBTYssNaINiywYYG1BRXUiAUu/wc5F/k2"
)
