import discord
from discord.ext import commands
from server_data import carregar_dados_guild, salvar_dados_guild
import os
import shutil
import zipfile
from funcoes import no_dm

def is_master(ctx):
    """Permite a execução somente se o autor for o usuário master."""
    return ctx.author.id == 476536045526056962

class CarregarPersonagens(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.arquivo_zip = "maisimagens.zip"
        self.pasta_extracao = "maisimagens_temp"
        self.pasta_destino = "resources/poneis"
        self.mais_personagens = {
            "personagens": [

            ]
        }

    @commands.command(
        name="carregar_mais_personagens",
        hidden=True,
        help="Adiciona novos personagens à lista de personagens em todos os servidores."
    )
    @no_dm()
    @commands.check(is_master)
    async def carregar_mais_personagens(self, ctx):
        novos_personagens = self.mais_personagens.get("personagens", [])
        if not novos_personagens:
            await ctx.send("❌ **Nenhum novo personagem disponível para carregar.**")
            return

        adicionados = []

        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            dados_guild = carregar_dados_guild(guild_id)

            if "personagens" not in dados_guild:
                dados_guild["personagens"] = []

            existentes = dados_guild["personagens"]
            existentes_lower = {p["nome"].lower() for p in existentes}

            for personagem in novos_personagens:
                nome = personagem["nome"].strip()
                especie = personagem["especie"].strip()
                if nome.lower() not in existentes_lower:
                    novos_dados = {"nome": nome, "especie": especie}
                    existentes.append(novos_dados)
                    adicionados.append(nome)

            dados_guild["personagens"] = existentes
            salvar_dados_guild(guild_id, dados_guild)

        if adicionados:
            await ctx.send(f"✅ **Personagens adicionados:** {', '.join(sorted(set(adicionados)))}")
        else:
            await ctx.send("❌ **Nenhum personagem novo foi adicionado (todos já existiam).**")


async def setup(bot):
    await bot.add_cog(CarregarPersonagens(bot))
