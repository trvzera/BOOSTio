"""Boas-vindas privadas com registro persistente para evitar duplicação."""

import sqlite3
from contextlib import closing
from datetime import datetime, timezone

import discord

SITE_URL = "https://boostio.com.br/"
INSTAGRAM_URL = "https://www.instagram.com/boostiooficial/"


def joined_at_key(value):
    # Gateway preserva microssegundos; REST pode devolver só milissegundos.
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds")


class WelcomeStore:
    def __init__(self, path):
        self.path = path
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("""CREATE TABLE IF NOT EXISTS welcomes (
                guild_id TEXT, member_id TEXT, joined_at TEXT, status TEXT,
                PRIMARY KEY (guild_id, member_id, joined_at))""")
            if db.execute("PRAGMA user_version").fetchone()[0] < 1:
                rows = db.execute("SELECT guild_id, member_id, joined_at, status FROM welcomes").fetchall()
                for guild_id, member_id, joined_at, status in rows:
                    normalized = joined_at_key(datetime.fromisoformat(joined_at))
                    if normalized == joined_at:
                        continue
                    # Uma tentativa já reservada ou concluída nunca volta a waiting.
                    db.execute("""INSERT INTO welcomes VALUES (?, ?, ?, ?)
                        ON CONFLICT(guild_id, member_id, joined_at) DO UPDATE SET
                        status=CASE WHEN welcomes.status='waiting' THEN excluded.status
                                    ELSE welcomes.status END""",
                               (guild_id, member_id, normalized, status))
                    db.execute("DELETE FROM welcomes WHERE guild_id=? AND member_id=? AND joined_at=?",
                               (guild_id, member_id, joined_at))
                db.execute("PRAGMA user_version=1")

    def key(self, member):
        return (str(member.guild.id), str(member.id), joined_at_key(member.joined_at))

    def track(self, member):
        if member.joined_at is None:
            return
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("DELETE FROM welcomes WHERE guild_id=? AND member_id=? AND joined_at<>?", self.key(member))
            db.execute("INSERT OR IGNORE INTO welcomes VALUES (?, ?, ?, 'waiting')", self.key(member))

    def forget(self, guild_id, member_id):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("PRAGMA secure_delete=ON")
            db.execute("DELETE FROM welcomes WHERE guild_id=? AND member_id=?", (str(guild_id), str(member_id)))

    def prune(self, guild_id, member_ids):
        # Executado somente após uma listagem completa e bem-sucedida.
        active = {str(value) for value in member_ids}
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("PRAGMA secure_delete=ON")
            rows = db.execute("SELECT DISTINCT member_id FROM welcomes WHERE guild_id=?", (str(guild_id),)).fetchall()
            db.executemany("DELETE FROM welcomes WHERE guild_id=? AND member_id=?",
                           [(str(guild_id), row[0]) for row in rows if row[0] not in active])

    def claim(self, member):
        if member.joined_at is None:
            return False
        with closing(sqlite3.connect(self.path)) as db, db:
            result = db.execute(
                "UPDATE welcomes SET status='claimed' WHERE guild_id=? AND member_id=? AND joined_at=? AND status='waiting'",
                self.key(member),
            )
            return result.rowcount == 1

    def finish(self, member, status):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("UPDATE welcomes SET status=? WHERE guild_id=? AND member_id=? AND joined_at=?",
                       (status, *self.key(member)))


def welcome_message(member):
    embed = discord.Embed(
        title="Boas-vindas à BOOSTio!",
        description=(
            f"Olá, **{discord.utils.escape_markdown(member.display_name)}**! Bom ter você aqui. 👋\n\n"
            "Seu acesso à comunidade está liberado. Aqui você pode tirar dúvidas, "
            "compartilhar seu setup e trocar experiências sobre **hardware, tecnologia e games**.\n\n"
            "Passe no **geral** e conte qual PC você usa ou gostaria de montar.\n\n"
            f"**Conheça a BOOSTio**\n[Nosso site]({SITE_URL}) · [Instagram @boostiooficial]({INSTAGRAM_URL})"
            "\n\nUse **/privacidade** no servidor para conhecer os dados usados pelo BOTio."
        ),
        color=0x0088FF,
    )
    embed.set_footer(text="BOOSTio · Menos dúvidas, mais desempenho.")
    if member.guild.icon:
        embed.set_thumbnail(url=member.guild.icon.url)
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Abrir server", url=f"https://discord.com/channels/{member.guild.id}"))
    view.add_item(discord.ui.Button(label="Site BOOSTio", url=SITE_URL))
    view.add_item(discord.ui.Button(label="Instagram", url=INSTAGRAM_URL))
    return embed, view


async def send_welcome(member, store, logger):
    # Reserva antes do envio: em resultado incerto ou reinício não repete a DM.
    if not store.claim(member):
        return
    embed, view = welcome_message(member)
    try:
        await member.send(embed=embed, view=view, allowed_mentions=discord.AllowedMentions.none())
    except discord.Forbidden:
        store.finish(member, "blocked")
        logger.info("Boas-vindas privadas bloqueadas; acesso preservado.")
    except discord.HTTPException as error:
        store.finish(member, "failed")
        logger.warning("Falha nas boas-vindas privadas: status=%s", error.status)
    else:
        store.finish(member, "sent")
        logger.info("Boas-vindas privadas enviadas.")
