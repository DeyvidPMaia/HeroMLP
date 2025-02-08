# gerenciamento.py

import discord
from discord.ext import commands
import os
import random
from discord import Embed, Interaction, ui
from paginacaoPersonagens import PaginacaoPersonagens
from funcoes import apenas_moderador, salvar_dados
import globals
import json


class Gerenciamento(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(name = "reiniciar", help="Reinicia a lista de personagens disponíveis e limpa o progresso.")
    @apenas_moderador()
    async def reiniciar_personagens(self, ctx):
        global globals
        globals.personagens_disponiveis = globals.personagens_inicial.copy()
        globals.personagens_salvos = []
        globals.contador_personagens_salvos.clear()
        globals.ultimo_usuario_salvador = None
        globals.personagens_por_usuario = {}
        salvar_dados(globals.personagens_disponiveis, globals.personagens_salvos, globals.contador_personagens_salvos, globals.personagens_por_usuario)  # Salvar dados após reiniciar
        await ctx.send("🌀 **A lista de personagens foi reiniciada e todo o progresso foi apagado!**")


    @commands.command(help="Salva aleatoriamente uma certa quantidade de personagens.")
    @apenas_moderador()
    async def salvar_aleatorio(self, ctx, quantidade: int):
        global globals

        if quantidade <= 0 or quantidade > len(globals.personagens_disponiveis):
            await ctx.send("❌ Quantidade inválida!")
            return

        personagens_selecionados = random.sample(globals.personagens_disponiveis, quantidade)

        for personagem in personagens_selecionados:
            globals.personagens_disponiveis.remove(personagem)
            globals.personagens_salvos.append(personagem)

        await ctx.send(f"✅ Os seguintes {quantidade} personagens salvos aleatoriamente.")
        view = PaginacaoPersonagens(personagens_selecionados, ctx)
        await view.send_pagina()
        

    @commands.command(name="restricao", help="Habilita ou desabilita a regra de um usuário salvar apenas um personagem por vez.")
    @apenas_moderador()
    async def alterar_restricao(self, ctx):
        global globals

        """Alterna a restrição na qual um usuário pode salvar apenas um personagem por vez."""
        globals.restricao_usuario_unico = not globals.restricao_usuario_unico  # Alternando o valor
        estado = "**habilitada**" if globals.restricao_usuario_unico else "**desabilitada**"
        mensagem = "só pode resgatar **um personagem por vez**" if globals.restricao_usuario_unico else "pode **resgatar personagens à vontade**"
        
        await ctx.send(f"⚖️ *A regra de restrição foi {estado}.* Agora você {mensagem}")



    @commands.command(name="personagens",help="Lista todos os personagens disponíveis.")
    @apenas_moderador()
    async def listar_personagens(self, ctx):
        if globals.personagens_disponiveis:
            view = PaginacaoPersonagens(globals.personagens_disponiveis, ctx)
            await view.send_pagina()
        else:
            await ctx.send("🎉 **Todos os personagens foram salvos!** 🎉", file=discord.File("resources/fim.png"))


    @commands.command(name="salvos", help="Lista todos os personagens salvos até agora.")
    @apenas_moderador()
    async def listar_salvos(self, ctx):
        try:
            with open("resources/dados.json", "r", encoding="utf-8") as f:
                dados = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            await ctx.send("❌ **Erro ao carregar os dados.**")
            return

        personagens_salvos = dados.get("personagens_salvos", [])

        if personagens_salvos:
            view = PaginacaoPersonagens(personagens_salvos, ctx)
            await ctx.send("**Estes personagens já estão na segurança de sua casa.**")
            await view.send_pagina()
        else:
            await ctx.send("🎉 **Nenhum personagem foi salvo ainda.**")



    @commands.command(name="tempo", help="Altera os tempos para 'dicas', 'impedimento' ou 'sorte'. Exemplo: !!tempo dicas 150")
    async def tempo(self, ctx, tipo: str, valor: int):
        # Verifica se o valor é positivo
        if valor < 0:
            await ctx.send("❌ O valor deve ser um número positivo.")
            return

        tipo = tipo.lower()
        if tipo == "dicas":
            globals.intervalo_dica_personagem = valor
            await ctx.send(f"✅ Tempo de dicas alterado para {valor} segundos.")
        elif tipo == "impedimento":
            globals.tempo_impedimento = valor
            await ctx.send(f"✅ Tempo de impedimento alterado para {valor} segundos.")
        elif tipo == "sorte":
            globals.tempo_sorte = valor
            await ctx.send(f"✅ Tempo de sorte alterado para {valor} segundos.")
        else:
            await ctx.send("❌ Tipo inválido! Use 'dicas', 'impedimento' ou 'sorte'.")


    @commands.command(help="Adiciona um novo personagem com nome, espécie e uma imagem. Exemplo: !!adicionar_personagem <nome> <espécie>")
    @apenas_moderador()
    async def adicionar_personagem(self, ctx, nome: str, especie: str):
        global globals

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
        nome_sanitizado = nome.replace(" ", "_")  # substitui espaços por underline para evitar problemas
        nome_arquivo = f"{nome_sanitizado}.{extensao}"
        caminho_imagem = os.path.join(diretorio, nome_arquivo)

        try:
            # Salva o anexo localmente
            await attachment.save(caminho_imagem)
        except Exception as e:
            await ctx.send(f"❌ **Erro ao salvar a imagem: {e}**")
            return

        # Verifica se o personagem já existe na lista de disponíveis
        if any(p["nome"].lower() == nome.lower() for p in globals.personagens_disponiveis):
            await ctx.send(f"❌ **O personagem '{nome}' já existe no jogo!**")
            return

        # Cria o novo personagem e adiciona às listas globais
        novo_personagem = {"nome": nome, "especie": especie}
        globals.personagens_disponiveis.append(novo_personagem)
        globals.personagens_inicial.append(novo_personagem)

        # Salva os dados atualizados (certifique-se de que a função salvar_dados aceita o parâmetro personagens_por_usuario, se for o caso)
        salvar_dados(globals.personagens_disponiveis, globals.personagens_salvos, globals.contador_personagens_salvos, globals.personagens_por_usuario)

        await ctx.send(f"✅ **Personagem '{nome}' ({especie}) foi adicionado com sucesso!**")


# Setup para registrar o cog
async def setup(bot):
    await bot.add_cog(Gerenciamento(bot))
