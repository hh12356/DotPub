from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `article` (
    `art_id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `art_title` VARCHAR(32) NOT NULL COMMENT '文章标题',
    `art_pub_date` DATE NOT NULL COMMENT '文章发布时间',
    `art_content` LONGTEXT NOT NULL COMMENT '文章内容',
    `art_author_id` INT NOT NULL COMMENT '文章作者id',
    CONSTRAINT `fk_article_useracco_893c0478` FOREIGN KEY (`art_author_id`) REFERENCES `useraccount` (`user_id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `article`;"""


MODELS_STATE = (
    "eJztmFtvmzAUx78K8lMnZROXEEje0tvWtUukNpsqjQkZcBJUsFNjr426fPfJhgQCJA3dpW"
    "nVR87x8eX3h3OOeQAxCVCUfPiaINr3fcIxAz3lAWAYI9BT6twtBcDZLHcKA4NeJMfzBFFY"
    "GOgljEJfzDmGUYJaCghQ4tNwxkKCQU/BPIqEkfgJoyGe5CaOw1uOXEYmiE0RBT3l+4+WAk"
    "IcoHuULB9nN+44RFGwtmmxCTcMxAak02XzmXScYXYqR4slPdcnEY9xKWI2Z1OCVyFhepAJ"
    "wohChsRCjHJxELHP7NjLs6V7zoekmy3EBGgMecQKB/fc3AZcdzAcuVcnI9cFDVD5BAvMIW"
    "aCywOYiC2817W21baNTttuKUBuc2WxFunSOZ00UDIajMBC+iGD6QhJu4RXPlQAH00h3UJ4"
    "GVRinDBaZrwkug3y0pBTzt+xp2MGDrdM3XZ4Rzcsh5ttNT3M49hjeO9GCE/YFPQUQ9/C+F"
    "v/8uhT//LA0N+JuQmFfvr5DDKPLl1ChhL22V3QmHoW85Kge37H4ZatavuEfkpw81d+FfWC"
    "8Hf0tufwjmVAh5vG2HqKCJq2gwiatlEE4VosRIofZyl+lfM96N/cQRq4a55cLUhZ6EcoqW"
    "p1mEWenl+iCMrDV5XJSl4/nWWvROqYtuVwCyLV4e2x6TvcVlUzrVuPC5QJkluzuiQpE51s"
    "wlx1xXpctkAMJ/KoYm2x0hIjoqE/respMs/WdgLmY56lk2jURLz1D7v1Dz8RTbJPb9dUWg"
    "jZ5zy6O+K1XKmb5g7JUjfNjdlS+tZrlvioGhDOhr9Cupqq7lKKVHVzLRK+dbo+wQyln/Y6"
    "4c9Xw0E94UJIiXIQ+kz5pURhwl4g7S1wBQwxc5wkt1GR6cGX/nUZ99HF8FDCIQmbUDmLnO"
    "CwWR/wT4tZ1hPUVbO8XdhSzgqDnqWeQcqaXYzzgLe69lhdE6xYyFJ9d867xaB9zr6l9rNj"
    "q5bDu3bX3o8rmuA4454bQFbD/xgytJl/Ma6cmiFDLIzRh6V/L8UwjUBzuIlUQ9jHHYd3zX"
    "G70a2gTojj/uikBvPG2jdC91vSyOb6t8/vuanZpvgh4XX/GOfo5Hq0vRrG88xzMRx8XA4v"
    "l8iqIJCzKWn4x7MS93h+f8FX37+R+is9SJ0IVQVOCUXhBJ+juRTiDCcMYr8u19T/a3/lPx"
    "9aCqDwbtWqVN9Lgt0ARYildbR/ddQ/PgFSjP/V/y1+A33wB3g="
)
