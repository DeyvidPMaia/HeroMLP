import discord
from discord.ext import commands
import random
import json

class Reverter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="perdido",
        help=("Remove aleatoriamente um personagem dos salvos e o adiciona de volta aos disponíveis. "
              "Uma mensagem será enviada informando: 'um amigo que tentava ajudar foi perdido novamente.'")
    )
    async def perdido(self, ctx):
        # Tenta carregar os dados do arquivo JSON
        try:
            with open("resources/dados.json", "r", encoding="utf-8") as f:
                dados = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            await ctx.send("❌ Erro ao carregar os dados. Verifique se o arquivo 'dados.json' existe e está correto.")
            return

        # Obtém as listas e dicionários do JSON
        personagens_salvos = dados.get("personagens_salvos", [])
        personagens_disponiveis = dados.get("personagens", [])
        personagens_por_usuario = dados.get("personagens_por_usuario", {})
        contador_personagens_salvos = dados.get("contador_personagens_salvos", {})

        # Verifica se há personagens salvos para remover
        if not personagens_salvos:
            await ctx.send("❌ Nenhum personagem foi salvo para ser perdido novamente.")
            return

        # Seleciona aleatoriamente um personagem da lista de salvos
        personagem = random.choice(personagens_salvos)

        # Remove o personagem da lista de salvos e adiciona-o à lista de disponíveis
        personagens_salvos.remove(personagem)
        personagens_disponiveis.append(personagem)

        # Procura o personagem no dicionário de personagens por usuário
        user_found = None
        for user_id, lista in personagens_por_usuario.items():
            # Se houver duplicata no mesmo usuário, removemos apenas uma ocorrência
            for p in lista:
                if p["nome"].lower() == personagem["nome"].lower():
                    lista.remove(p)
                    user_found = user_id
                    break
            if user_found:
                break

        # Se o personagem estava associado a algum usuário, decrementa o contador correspondente
        if user_found:
            contador_personagens_salvos[user_found] = max(contador_personagens_salvos.get(user_found, 1) - 1, 0)

        # Atualiza os dados no dicionário geral
        dados["personagens"] = personagens_disponiveis
        dados["personagens_salvos"] = personagens_salvos
        dados["personagens_por_usuario"] = personagens_por_usuario
        dados["contador_personagens_salvos"] = contador_personagens_salvos

        # Salva os dados atualizados de volta em dados.json
        try:
            with open("resources/dados.json", "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=4)
        except Exception as e:
            await ctx.send("❌ Erro ao salvar os dados atualizados.")
            return

        await ctx.send("❗ **Um amigo que tentava ajudar foi perdido novamente.**")

async def setup(bot):
    await bot.add_cog(Reverter(bot))
