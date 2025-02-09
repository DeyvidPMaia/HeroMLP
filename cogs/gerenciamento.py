# gerenciamento.py

import discord
from discord.ext import commands
import os
import random
from discord import Embed
from paginacaoPersonagens import PaginacaoPersonagens
from funcoes import apenas_moderador
from server_data import carregar_dados_guild, salvar_dados_guild
import globals  # Utilizado para acessar a lista global de personagens_inicial
import json

class Gerenciamento(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="reiniciar", help="Reinicia a lista de personagens disponíveis e limpa o progresso.")
    @apenas_moderador()
    async def reiniciar_personagens(self, ctx):
        guild_id = str(ctx.guild.id)
        dados = carregar_dados_guild(guild_id)
        # Reinicia os dados para este servidor
        dados["personagens"] = globals.personagens_inicial.copy()
        dados["personagens_salvos"] = []
        dados["contador_personagens_salvos"] = {}
        dados["ultimo_usuario_salvador"] = None
        dados["personagens_por_usuario"] = {}
        # Se houver configurações de tempo ou outras, pode-se reiniciá-las também aqui se desejar.
        salvar_dados_guild(guild_id, dados)
        await ctx.send("🌀 **A lista de personagens foi reiniciada e todo o progresso foi apagado!**")

    @commands.command(help="Salva aleatoriamente uma certa quantidade de personagens.")
    @apenas_moderador()
    async def salvar_aleatorio(self, ctx, quantidade: int):
        guild_id = str(ctx.guild.id)
        dados = carregar_dados_guild(guild_id)

        if quantidade <= 0 or quantidade > len(dados["personagens"]):
            await ctx.send("❌ Quantidade inválida!")
            return

        personagens_selecionados = random.sample(dados["personagens"], quantidade)
        for personagem in personagens_selecionados:
            dados["personagens"].remove(personagem)
            dados["personagens_salvos"].append(personagem)

        salvar_dados_guild(guild_id, dados)
        await ctx.send(f"✅ Os seguintes {quantidade} personagens foram salvos aleatoriamente:")
        view = PaginacaoPersonagens(personagens_selecionados, ctx)
        await view.send_pagina()

    @commands.command(name="restricao", help="Habilita ou desabilita a regra de um usuário salvar apenas um personagem por vez.")
    @apenas_moderador()
    async def alterar_restricao(self, ctx):
        guild_id = str(ctx.guild.id)
        dados = carregar_dados_guild(guild_id)
        # Inicializa a chave se não existir
        if "restricao_usuario_unico" not in dados:
            dados["restricao_usuario_unico"] = False
        dados["restricao_usuario_unico"] = not dados["restricao_usuario_unico"]
        estado = "**habilitada**" if dados["restricao_usuario_unico"] else "**desabilitada**"
        mensagem = "só pode resgatar **um personagem por vez**" if dados["restricao_usuario_unico"] else "pode **resgatar personagens à vontade**"
        salvar_dados_guild(guild_id, dados)
        await ctx.send(f"⚖️ *A regra de restrição foi {estado}.* Agora você {mensagem}")

    @commands.command(name="personagens", help="Lista todos os personagens disponíveis.")
    @apenas_moderador()
    async def listar_personagens(self, ctx):
        guild_id = str(ctx.guild.id)
        dados = carregar_dados_guild(guild_id)
        if dados["personagens"]:
            view = PaginacaoPersonagens(dados["personagens"], ctx)
            await view.send_pagina()
        else:
            await ctx.send("🎉 **Todos os personagens foram salvos!** 🎉", file=discord.File("resources/fim.png"))

    @commands.command(name="salvos", help="Lista todos os personagens salvos até agora.")
    @apenas_moderador()
    async def listar_salvos(self, ctx):
        guild_id = str(ctx.guild.id)
        dados = carregar_dados_guild(guild_id)
        personagens_salvos = dados.get("personagens_salvos", [])
        if personagens_salvos:
            view = PaginacaoPersonagens(personagens_salvos, ctx)
            await ctx.send("**Estes personagens já estão na segurança de sua casa.**")
            await view.send_pagina()
        else:
            await ctx.send("🎉 **Nenhum personagem foi salvo ainda.**")

    @commands.command(name="tempo", help="Altera os tempos para 'dicas', 'impedimento' ou 'sorte'. Exemplo: !!tempo dicas 150")
    @apenas_moderador()
    async def tempo(self, ctx, tipo: str, valor: int):
        if valor < 0:
            await ctx.send("❌ O valor deve ser um número positivo.")
            return

        tipo = tipo.lower()
        guild_id = str(ctx.guild.id)
        dados = carregar_dados_guild(guild_id)
        # Inicializa os tempos se não estiverem definidos
        if "intervalo_dica_personagem" not in dados:
            dados["intervalo_dica_personagem"] = globals.intervalo_dica_personagem
        if "tempo_impedimento" not in dados:
            dados["tempo_impedimento"] = globals.tempo_impedimento
        if "tempo_sorte" not in dados:
            dados["tempo_sorte"] = globals.tempo_sorte

        if tipo == "dicas":
            dados["intervalo_dica_personagem"] = valor
            await ctx.send(f"✅ Tempo de dicas alterado para {valor} segundos.")
        elif tipo == "impedimento":
            dados["tempo_impedimento"] = valor
            await ctx.send(f"✅ Tempo de impedimento alterado para {valor} segundos.")
        elif tipo == "sorte":
            dados["tempo_sorte"] = valor
            await ctx.send(f"✅ Tempo de sorte alterado para {valor} segundos.")
        else:
            await ctx.send("❌ Tipo inválido! Use 'dicas', 'impedimento' ou 'sorte'.")
            return

        salvar_dados_guild(guild_id, dados)

    @commands.command(help="Adiciona um novo personagem com nome, espécie e uma imagem. Exemplo: !!adicionar_personagem <nome> <espécie>")
    @apenas_moderador()
    async def adicionar_personagem(self, ctx, nome: str, especie: str):
        guild_id = str(ctx.guild.id)
        dados = carregar_dados_guild(guild_id)

        # Verifica se há um anexo (imagem) na mensagem
        if not ctx.message.attachments:
            await ctx.send("❌ **Você deve anexar uma imagem para o personagem.**")
            return

        # Obtém o primeiro anexo (esperando que seja a imagem)
        attachment = ctx.message.attachments[0]

        # Define a pasta e o nome do arquivo a ser salvo
        diretorio = os.path.join("resources", "poneis")
        if not os.path.exists(diretorio):
            os.makedirs(diretorio)

        # Extrai a extensão do arquivo e define o nome final, por exemplo: "NomeDoPersonagem.png"
        extensao = attachment.filename.split('.')[-1]
        nome_sanitizado = nome.replace(" ", "_")
        nome_arquivo = f"{nome_sanitizado}.{extensao}"
        caminho_imagem = os.path.join(diretorio, nome_arquivo)

        try:
            # Salva o anexo localmente
            await attachment.save(caminho_imagem)
        except Exception as e:
            await ctx.send(f"❌ **Erro ao salvar a imagem: {e}**")
            return

        # Verifica se o personagem já existe na lista de disponíveis
        if any(p["nome"].lower() == nome.lower() for p in dados["personagens"]):
            await ctx.send(f"❌ **O personagem '{nome}' já existe no jogo!**")
            return

        # Cria o novo personagem e adiciona às listas do servidor
        novo_personagem = {"nome": nome, "especie": especie}
        dados["personagens"].append(novo_personagem)
        # Se ainda não existir a lista de personagens_inicial para este servidor, inicializa-a
        if "personagens_inicial" not in dados:
            dados["personagens_inicial"] = []
        dados["personagens_inicial"].append(novo_personagem)

        salvar_dados_guild(guild_id, dados)
        await ctx.send(f"✅ **Personagem '{nome}' ({especie}) foi adicionado com sucesso!**")

# Setup para registrar o cog
async def setup(bot):
    await bot.add_cog(Gerenciamento(bot))
