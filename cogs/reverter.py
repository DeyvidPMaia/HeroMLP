import discord
from discord.ext import commands
import random
import json
import os

class Reverter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def carregar_dados_servidor(self, guild_id):
        """Carrega os dados do servidor a partir do arquivo JSON correspondente."""
        caminho = f"resources/servidores/{guild_id}.json"
        if not os.path.exists(caminho):
            return {
                "personagens_salvos": [],
                "personagens": [],
                "personagens_por_usuario": {},
                "contador_personagens_salvos": {}
            }

        try:
            with open(caminho, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "personagens_salvos": [],
                "personagens": [],
                "personagens_por_usuario": {},
                "contador_personagens_salvos": {}
            }

    def salvar_dados_servidor(self, guild_id, dados):
        """Salva os dados do servidor no arquivo JSON correspondente."""
        caminho = f"resources/servidores/{guild_id}.json"
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        try:
            with open(caminho, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Erro ao salvar dados para o servidor {guild_id}: {e}")

    @commands.command(
        name="perdido",
        help=("Remove aleatoriamente um personagem dos salvos e o adiciona de volta aos disponíveis. "
              "Uma mensagem será enviada informando: 'um amigo que tentava ajudar foi perdido novamente.'")
    )
    async def perdido(self, ctx):
        guild_id = ctx.guild.id
        dados = self.carregar_dados_servidor(guild_id)

        personagens_salvos = dados["personagens_salvos"]
        personagens_disponiveis = dados["personagens"]
        personagens_por_usuario = dados["personagens_por_usuario"]
        contador_personagens_salvos = dados["contador_personagens_salvos"]

        if not personagens_salvos:
            await ctx.send("❌ Nenhum personagem foi salvo para ser perdido novamente.")
            return

        personagem = random.choice(personagens_salvos)

        personagens_salvos.remove(personagem)
        personagens_disponiveis.append(personagem)

        user_found = None
        for user_id, lista in personagens_por_usuario.items():
            for p in lista:
                if p["nome"].lower() == personagem["nome"].lower():
                    lista.remove(p)
                    user_found = user_id
                    break
            if user_found:
                break

        if user_found:
            contador_personagens_salvos[user_found] = max(contador_personagens_salvos.get(user_found, 1) - 1, 0)

        dados["personagens"] = personagens_disponiveis
        dados["personagens_salvos"] = personagens_salvos
        dados["personagens_por_usuario"] = personagens_por_usuario
        dados["contador_personagens_salvos"] = contador_personagens_salvos

        self.salvar_dados_servidor(guild_id, dados)

        await ctx.send("❗ **Um amigo que tentava ajudar foi perdido novamente.**")

async def setup(bot):
    await bot.add_cog(Reverter(bot))
