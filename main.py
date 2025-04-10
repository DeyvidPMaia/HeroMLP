import discord
from discord import Embed
from discord.ext import commands
import json
import asyncio
import os
import time
import globals
from funcoes import carregar_personagens, carregar_imagens_naoencontrado, carregar_token
from server_data import carregar_dados_guild
import logging

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Inicializa variáveis globais
globals.personagens_inicial = carregar_personagens()
globals.user_cache = {}

BOT_TOKEN = ""


# Configure os intents
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!!", intents=intents)

def carregar_dados():
    try:
        with open("resources/dados.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Erro ao carregar dados: {e}")
        return {}

async def load_extensions():
    extensoes = [
        "cogs.resgatar",
        "cogs.usuario",
        "cogs.ajuda",
        "cogs.extras",
        "cogs.gerenciamento",
        "cogs.botstatus",
        "cogs.canalmensagens",
        "cogs.botcontrol",
        "cogs.historia",
        "cogs.instrucoes",
        "cogs.exibir",
        "cogs.carregarmais",
        "cogs.loja",
        "cogs.conquistas",
        "cogs.perdidomanual",
        "cogs.trocar",
        "cogs.acalentar",
        "cogs.perfil",
        "cogs.taskperdido",
        #"cogs.personagemsemrumo",
        "cogs.taskcorrecaodados",
        #"cogs.eventoesquecimento",
    ]
    
    for ext in extensoes:
        try:
            await bot.load_extension(ext)
            logger.info(f"✅ Extensão carregada: {ext}")
        except Exception as e:
            logger.error(f"⚠️ Erro ao carregar {ext}: {e}")

@bot.event
async def on_ready():
    for guild in bot.guilds:
        for member in guild.members:
            globals.user_cache[member.id] = member

    if not hasattr(bot, "start_time"):
        bot.start_time = time.time()

    logger.info(f"Bot conectado como {bot.user}")
    carregar_imagens_naoencontrado()

    for guild in bot.guilds:
        guild_id = str(guild.id)
        dados = carregar_dados_guild(guild_id)
        if "ID_DO_CANAL_PRINCIPAL" not in dados:
            canal = None
            for ch in guild.text_channels:
                if ch.permissions_for(guild.me).send_messages:
                    canal = ch
                    break
            if canal:
                await canal.send("⚠️ **Configure um canal principal com !!canal principal**")
        else:
            canalMensagensCog = bot.get_cog("CanalMensagens")
            if canalMensagensCog:
                if "ID_DO_CANAL_DICAS" in dados:
                    canalMensagensCog.reiniciar_task("dicas", guild_id)
                if "ID_DO_CANAL_RECOMPENSA" in dados:
                    canalMensagensCog.reiniciar_task("recompensa", guild_id)
                if "ID_DO_CANAL_SORTE" in dados:
                    canalMensagensCog.reiniciar_task("sorte", guild_id)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("❌ **Você não tem permissão para usar este comando.**")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ **Comando não encontrado. Use !!comandos para ver os comandos disponíveis.**")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ **Faltando argumentos no comando. Use !!comandos para ver os comandos disponíveis.**")
    else:
        await ctx.send("⚠️ **Ocorreu um erro inesperado. Tente novamente mais tarde.**")
        logger.error(f"Erro no comando {ctx.command}: {error}")
        raise error

async def main():
    async with bot:
        try:
            await load_extensions()
            await bot.start(BOT_TOKEN)
        except discord.LoginFailure:
            logger.error("Erro: Token inválido. Verifique o Token")
        except Exception as e:
            logger.error(f"Erro inesperado ao iniciar o bot: {e}")
        finally:
            logger.info("Encerrando o bot...")
            await bot.close()  # Garante que o bot seja fechado corretamente

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Bot encerrado manualmente com Ctrl+C.")
        loop.run_until_complete(bot.close())  # Fecha o bot no caso de Ctrl+C
    except Exception as e:
        logger.error(f"Erro crítico no programa: {e}")
    finally:
        loop.close()  # Fecha o event loop