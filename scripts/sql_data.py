from aiosqlite import connect, Row
from asyncinit import asyncinit


@asyncinit
class Database:
    async def __init__(self, db_file):
        self.db_file = db_file
        async with connect(self.db_file) as db:
            await db.execute("""CREATE TABLE IF NOT EXISTS jokes (
                                user_id INTEGER,
                                joke TEXT,
                                author TEXT
                            )""")
            await db.execute("""CREATE TABLE IF NOT EXISTS newJokes (
                                user_id INTEGER,
                                joke TEXT,
                                author TEXT
                            )""")
            await db.execute("""CREATE TABLE IF NOT EXISTS users (
                                user_id INTEGER
                            )""")

    async def recordJoke(self, joke, author, user_id):
        """Запись шутки"""
        async with connect(self.db_file) as db:
            rowid = await self.rowid(user_id)
            moreShows = [(rowid, joke, author)]
            await db.executemany(
                "INSERT INTO jokes (user_id,joke,author) VALUES (?, ?, ?)", moreShows)
            await db.executemany(
                "INSERT INTO newJokes (user_id,joke,author) VALUES (?, ?, ?)", moreShows)
            await db.commit()

    async def randomJoke(self):
        """Отправка рандомной шутки от пользователей бота"""
        async with connect(self.db_file) as db:
            db.row_factory = Row
            async with db.execute(
                    "SELECT joke, author FROM jokes ORDER BY RANDOM() LIMIT 1") as cursor:
                async for row in cursor:
                    if not bool(len(row)):
                        return "Нету шуток 😞, но ты можешь записать свою шутку 😉"
                    return f'{row["joke"]} Автор: {row["author"]}'

    async def myJoke(self, user_id):
        """Просмотр своих шуток"""
        async with connect(self.db_file) as db:
            db.row_factory = Row
            rowid = await self.rowid(user_id)
            async with db.execute(
                    f"SELECT joke, author FROM jokes WHERE user_id = '%s'" % rowid) as cursor:
                msg = ''
                async for row in cursor:
                    msg += f'{row["joke"]}\n\n'
        if not bool(len(msg)):
            return "Нету шуток 😞, но ты можешь записать свою шутку 😉"
        return msg

    async def newsJoke(self):
        """Вывод последней шутки"""
        async with connect(self.db_file) as db:
            db.row_factory = Row
            async with db.execute(
                    "SELECT * FROM newJokes LIMIT 1") as cursor:
                async for row in cursor:
                    return row

    async def deleteOldJoke(self):
        """Удаление старой шутки"""
        async with connect(self.db_file) as db:
            await db.execute(
                "DELETE FROM newJokes where ROWID = 1")
            await db.commit()

    async def newsJokesExists(self):
        """Проверка шуток"""
        async with connect(self.db_file) as db:
            db.row_factory = Row
            async with db.execute(
                    "SELECT count(*) FROM newJokes") as cursor:
                async for row in cursor:
                    if row["count(*)"] < 1:
                        return False
                    return True

    async def quantityUsers(self):
        """Количество пользователей"""
        async with connect(self.db_file) as db:
            db.row_factory = Row
            async with db.execute("SELECT count(*) FROM users") as cursor:
                async for row in cursor:
                    return row["count(*)"]

    async def quantityJokesUser(self, user_id):
        """Количество шуток у пользователя"""
        async with connect(self.db_file) as db:
            db.row_factory = Row
            rowid = await self.rowid(user_id)
            async with db.execute("SELECT count(*) FROM jokes WHERE user_id = ?", (rowid,)) as cursor:
                async for row in cursor:
                    return row["count(*)"]

    async def userExists(self, user_id):
        """Проверка пользовотеля"""
        async with connect(self.db_file) as db:
            db.row_factory = Row
            async with db.execute(
                    "SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                async for row in cursor:
                    return bool(len(row))

    async def userAdd(self, user_id):
        """Добавление пользователя"""
        async with connect(self.db_file) as db:
            await db.execute(
                "INSERT INTO users (user_id) VALUES (?)", (user_id,))
            await db.commit()

    async def infoId(self, id):
        """Просмотр пользователя"""
        async with connect(self.db_file) as db:
            db.row_factory = Row
            async with db.execute("SELECT * FROM users WHERE ROWID = ?", (id,)) as cursor:
                async for row in cursor:
                    return row["user_id"]

    async def rowid(self, user_id):
        """Поиск пользователя"""
        async with connect(self.db_file) as db:
            db.row_factory = Row
            if not await self.userExists(user_id):
                await self.userAdd(user_id)
            async with db.execute(
                    f"SELECT rowid FROM users WHERE user_id = '%s'" % user_id) as cursor:
                async for row in cursor:
                    return row["rowid"]

    async def deleteJokesUser(self, user_id):
        """Удаление своих шуток"""
        async with connect(self.db_file) as db:
            rowid = await self.rowid(user_id)
            await db.execute(
                f"DELETE FROM jokes WHERE user_id = '%s'" % rowid)
            await db.commit()


@asyncinit
class AdminDatabase(Database):
    async def __init__(self, db_file):
        await super(AdminDatabase, self).__init__(db_file)
        async with connect(self.db_file) as db:
            await db.execute("""CREATE TABLE IF NOT EXISTS admins (
                                user_id INTEGER,
                                name TEXT,
                                inviting INTEGER
                            )""")

    async def deleteJokes(self):
        """Удаление всех шуток"""
        async with connect(self.db_file) as db:
            await db.executescript("""DELETE FROM jokes;
                                        DELETE FROM newJokes
                                    """)
            await db.commit()

    async def dump(self, user_id):
        """Дамп бд"""
        async with connect(self.db_file) as db:
            with open(f"{user_id}.sql", "w", encoding='utf 8') as file:
                async for sql in db.iterdump():
                    file.write(sql)

    async def adminExists(self, user_id):
        """Проверка админа"""
        async with connect(self.db_file) as db:
            db.row_factory = Row
            async with db.execute(
                    "SELECT * FROM admins WHERE user_id = ?", (user_id,)) as cursor:
                async for row in cursor:
                    return bool(len(row))

    async def nameAdminExists(self, name):
        """Проверка имени админа"""
        async with connect(self.db_file) as db:
            db.row_factory = Row
            async with db.execute(
                    "SELECT * FROM admins WHERE name = ?", (name,)) as cursor:
                async for row in cursor:
                    return bool(len(row))

    async def adminAdd(self, user_id,  name, inviting):
        """Добавление админа"""
        async with connect(self.db_file) as db:
            await db.execute(
                "INSERT INTO admins (user_id, name, inviting) VALUES (?, ?, ?)", (user_id, name, inviting,))
            await db.commit()

    async def adminDel(self, user_id):
         """Удаление админа"""
         async with connect(self.db_file) as db:
            await db.execute(
                f"DELETE FROM admins WHERE user_id = '%s'" % user_id)
            await db.commit()

    async def allAdmins(self):
        """Просмотр список админов"""
        async with connect(self.db_file) as db:
            db.row_factory = Row
            async with db.execute(
                    f"SELECT user_id, name, inviting FROM admins") as cursor:
                msg = ''
                async for row in cursor:
                    msg += f'id: {row["user_id"]}, name: {row["name"]}, inviting: {row["inviting"]}\n\n'
        if not bool(len(msg)):
            return "Нету админов"
        return msg