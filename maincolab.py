# main.py

import discord
from discord import Embed, Interaction, ui
from discord.ext import commands
import json
from paginacaoPersonagens import PaginacaoPersonagens
import asyncio
from dotenv import load_dotenv
import os
import globals
from funcoes import carregar_estado, carregar_personagens

globals.personagens_inicial = carregar_personagens()
globals.personagens_disponiveis, globals.personagens_salvos, globals.contador_personagens_salvos, globals.personagens_por_usuario = carregar_estado()


from google.colab import userdata
TOKEN = userdata.get('DISCORD_TOKEN')

# Configurações do Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!!', intents=intents)

# Função para carregar os dados do arquivo JSON
def carregar_dados():
    try:
        with open("resources/dados.json", "r", encoding="utf-8") as f:
            dados = json.load(f)
            return dados
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Erro ao carregar dados: {e}")
        return None
    

async def load_extensions():
    await bot.load_extension("cogs.gerenciamento")
    await bot.load_extension("cogs.usuario")
    await bot.load_extension("cogs.ajuda")
    await bot.load_extension("cogs.extras")
    await bot.load_extension("cogs.resgatar")
    await bot.load_extension("cogs.botstatus")
    await bot.load_extension("cogs.canalmensagens")
    await bot.load_extension("cogs.botcontrol")
    await bot.load_extension("cogs.historia")

@bot.event
async def on_ready():
    # Atualiza o cache de usuários
    for guild in bot.guilds:
        for member in guild.members:
            globals.user_cache[member.id] = member
    
    print(f"Bot conectado como {bot.user}")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        # Envia mensagem de permissão negada
        await ctx.send("❌ **Você não tem permissão para usar este comando.**")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ **Comando não encontrado. Use !!help para ver os comandos disponíveis.**")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ **Faltando argumentos no comando. Use !!help para ver os comandos disponíveis.**")
    else:
        await ctx.send("⚠️ **Ocorreu um erro inesperado. Tente novamente mais tarde.**")
        print(error)
        raise error


# Inicia o bot com tratamento de erros
async def main():
    async with bot:
        try:
            await load_extensions()
            await bot.start(TOKEN)
        except discord.LoginFailure:
            print("Erro: Token inválido. Verifique o Token")
        except Exception as e:
            print(f"Erro inesperado: {e}")

asyncio.run(main())
