# gerenciamento.py atualizado 17/03/2025

import io
from PIL import Image
import discord
from discord.ext import commands
import os
import random
from paginacaoPersonagens import PaginacaoPersonagens
from funcoes import apenas_moderador, maintenance_off, no_dm
from server_data import carregar_dados_guild, salvar_dados_guild, evento_esquecimento
import globals
import json
import asyncio
import time
from utils import personagem_perdido


class Gerenciamento(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="reiniciar", help="Reinicia a lista de personagens disponíveis e limpa o progresso. Uso: !!reiniciar sgbestpony")
    @evento_esquecimento()
    @maintenance_off()
    @no_dm()
    @apenas_moderador()
    async def reiniciar_personagens(self, ctx, confirmacao: str):
        if confirmacao.lower() != "sgbestpony":
            embed = discord.Embed(
                title="❌ Confirmação Inválida",
                description="Para reiniciar a lista de personagens, use `!!reiniciar sgbestpony`.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="🔔 Confirmação Necessária",
            description="Deseja reiniciar os personagens e dados relacionados? Responda com **`sim apagar`** ou **`cancelar`** em 30 segundos.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["sim apagar", "cancelar"]

        try:
            resposta = await self.bot.wait_for("message", timeout=30.0, check=check)
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="⏰ Tempo Expirado",
                description="Operação cancelada por inatividade.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if resposta.content.lower() != "sim apagar":
            embed = discord.Embed(
                title="❌ Cancelado",
                description="Operação de reinício abortada.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        guild_id = str(ctx.guild.id)
        dados = carregar_dados_guild(guild_id)

        # Primeiro reset: personagens e dados relacionados
        dados["personagens"] = globals.personagens_inicial.copy()
        dados["personagens_salvos"] = []
        dados["contador_personagens_salvos"] = {}
        dados["ultimo_usuario_salvador"] = None
        dados["personagens_por_usuario"] = {}  # Isso já reseta recompensa_exibir
        dados["ultimo_resgate_por_usuario"] = {}  # Reset de resgates por usuário
        dados["loja_reset_timestamp"] = 0  # Reset do timestamp da loja (assumindo que é global)
        dados["ultimo_auto_reiniciar"] = 0  # Reset do último auto-reinício
        dados["ultimo_personagem_perdido"] = 0 # reset do horario de último personagem perdido
        dados["bolsa_acalentar"] = {} # Reseta os dados da bolsa do acalentar
        dados["horario_personagem_sem_rumo"] = {} # Elimina os horarios para personagem sem rumo ocorrer
        dados["personagem_escondido"] = [{"nome": "Lightly Unicorn", "especie": "Unicorn", "cor": "#8ce1ff", "alinhamento": "1"}] # Esvazia a lista de personagens escondidos mantendo apenas o Lightly Unicorn
        dados["evento_esquecimento_ocorrendo"] = False
        dados["personagens_especiais"] = globals.personagens_especiais_inicial.copy() # Inicia os personagens especiais
        dados["lar_do_unicornio"] = []

        if "usuarios" in dados:
            for user_id in dados["usuarios"]:
                # Reset de dados específicos do usuário
                dados["usuarios"][user_id]["changeling"] = []
                dados["usuarios"][user_id]["quantidade_recompensa"] = 0
                dados["usuarios"][user_id]["ultimo_reset_recompensa"] = 0
                dados["usuarios"][user_id]["loja"] = {}  # Reset da loja por usuário
                dados["usuarios"][user_id]["resgatou_personagem"] = False  # Reset da loja por usuário

        salvar_dados_guild(guild_id, dados)
        embed = discord.Embed(
            title="🌀 Personagens e Dados Reiniciados",
            description="A lista de personagens, recompensas, loja e resgates foram reiniciados!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

        # Pergunta se quer zerar corações e trevos
        embed = discord.Embed(
            title="🔔 Zerar Corações e Trevos?",
            description="Deseja também zerar os corações e trevos dos usuários? Responda com **`sim apagar tudo`** ou **`cancelar`** em 30 segundos.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

        def check_extra(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["sim apagar tudo", "cancelar"]

        try:
            resposta_extra = await self.bot.wait_for("message", timeout=30.0, check=check_extra)
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="⏰ Tempo Expirado",
                description="Corações e trevos foram preservados.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if resposta_extra.content.lower() == "sim apagar tudo":
            if "usuarios" in dados:
                for user_id in dados["usuarios"]:
                    dados["usuarios"][user_id]["coracao"] = 0
                    dados["usuarios"][user_id]["quantidade_amor"] = 0
                    dados["usuarios"][user_id]["trevo"] = 0
            salvar_dados_guild(guild_id, dados)
            embed = discord.Embed(
                title="🗑️ Tudo Zerado",
                description="Corações e trevos dos usuários foram zerados!",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Cancelado",
                description="Corações e trevos foram preservados.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(help="Salva aleatoriamente uma certa quantidade de personagens.")
    @evento_esquecimento()
    @maintenance_off()
    @no_dm()
    @apenas_moderador()
    async def salvar_aleatorio(self, ctx, quantidade: int):
        guild_id = str(ctx.guild.id)
        bot_id = str(ctx.bot.user.id)
        dados = carregar_dados_guild(guild_id)

        if quantidade <= 0 or quantidade > len(dados["personagens"]):
            embed = discord.Embed(
                title="❌ Quantidade Inválida",
                description=f"Escolha um número entre 1 e {len(dados['personagens'])}.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        personagens_selecionados = random.sample(dados["personagens"], quantidade)
        contador_personagens_salvos = 0

        for personagem in personagens_selecionados:
            dados["personagens"].remove(personagem)
            dados["personagens_salvos"].append(personagem)
            contador_personagens_salvos += 1
            dados.setdefault("personagens_por_usuario", {}).setdefault(bot_id, []).append(personagem)

        salvar_dados_guild(guild_id, dados)

        embed = discord.Embed(
            title="✅ Salvamento Aleatório",
            description=f"{contador_personagens_salvos} personagens foram salvos e associados ao bot.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        view = PaginacaoPersonagens(personagens_selecionados, ctx)
        await view.send_pagina()

    @commands.command(name="restricao", help="Habilita ou desabilita a regra de um usuário salvar apenas um personagem por vez.")
    @evento_esquecimento()
    @maintenance_off()
    @no_dm()
    @apenas_moderador()
    async def alterar_restricao(self, ctx):
        guild_id = str(ctx.guild.id)
        dados = carregar_dados_guild(guild_id)
        dados.setdefault("restricao_usuario_unico", False)
        dados["restricao_usuario_unico"] = not dados["restricao_usuario_unico"]
        estado = "habilitada" if dados["restricao_usuario_unico"] else "desabilitada"
        mensagem = "só pode resgatar **um personagem por vez**" if dados["restricao_usuario_unico"] else "pode **resgatar personagens à vontade**"
        salvar_dados_guild(guild_id, dados)

        embed = discord.Embed(
            title="⚖️ Restrição Alterada",
            description=f"A regra foi **{estado}**. Agora você {mensagem}.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command(name="personagens", help="Lista todos os personagens disponíveis.")
    @evento_esquecimento()
    @maintenance_off()
    @no_dm()
    @apenas_moderador()
    async def listar_personagens(self, ctx):
        guild_id = str(ctx.guild.id)
        dados = carregar_dados_guild(guild_id)
        
        # Aplica o tempo de impedimento ao gerenciador
        user_id = str(ctx.author.id)
        tempo_impedimento = dados.get("tempo_impedimento", globals.tempo_impedimento)
        dados.setdefault("ultimo_resgate_por_usuario", {})[user_id] = time.time()
        salvar_dados_guild(guild_id, dados)

        if dados["personagens"]:
            embed = discord.Embed(
                title="📜 Personagens Disponíveis",
                description="Aqui estão os personagens ainda disponíveis para salvar.\n*Seu tempo de impedimento foi ativado.*",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            view = PaginacaoPersonagens(dados["personagens"], ctx)
            await view.send_pagina()
        else:
            embed = discord.Embed(
                title="🎉 Todos Salvos!",
                description="Todos os personagens foram salvos com sucesso!\n*Seu tempo de impedimento foi ativado.*",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed, file=discord.File("resources/fim.png"))

    @commands.command(name="salvos", help="Lista todos os personagens salvos até agora.")
    @evento_esquecimento()
    @maintenance_off()
    @no_dm()
    @apenas_moderador()
    async def listar_salvos(self, ctx):
        guild_id = str(ctx.guild.id)
        dados = carregar_dados_guild(guild_id)
        personagens_salvos = dados.get("personagens_salvos", [])
        if personagens_salvos:
            embed = discord.Embed(
                title="🏠 Personagens Salvos",
                description="Estes personagens já estão em segurança.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            view = PaginacaoPersonagens(personagens_salvos, ctx)
            await view.send_pagina()
        else:
            embed = discord.Embed(
                title="📭 Nenhum Salvo",
                description="Nenhum personagem foi salvo ainda.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)

    @commands.command(name="tempo", help="Altera os tempos para 'dicas', 'impedimento', 'sorte', 'recompensa' ou 'perdido'. Exemplo: !!tempo dicas 150")
    @evento_esquecimento()
    @maintenance_off()
    @no_dm()
    @apenas_moderador()
    async def tempo(self, ctx, tipo: str, valor: int):
        if valor < 0:
            embed = discord.Embed(
                title="❌ Valor Inválido",
                description="O valor deve ser um número positivo.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        tipo = tipo.lower()
        guild_id = str(ctx.guild.id)
        dados = carregar_dados_guild(guild_id)

        tempos = {
            "dicas": "intervalo_dica_personagem",
            "impedimento": "tempo_impedimento",
            "sorte": "tempo_sorte",
            "recompensa": "tempo_recompensa",
            "perdido": "tempo_personagem_perdido"
        }
        valores_padrao = {
            "intervalo_dica_personagem": globals.intervalo_dica_personagem,
            "tempo_impedimento": globals.tempo_impedimento,
            "tempo_sorte": globals.tempo_sorte,
            "tempo_recompensa": globals.tempo_recompensa,
            "tempo_personagem_perdido": globals.tempo_personagem_perdido
        }

        if tipo not in tempos:
            embed = discord.Embed(
                title="❌ Tipo Inválido",
                description="Use 'dicas', 'impedimento', 'sorte', 'recompensa' ou 'perdido'.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        chave = tempos[tipo]
        dados.setdefault(chave, valores_padrao[chave])
        dados[chave] = valor
        salvar_dados_guild(guild_id, dados)

        embed = discord.Embed(
            title="⏱️ Tempo Alterado",
            description=f"O tempo de **{tipo}** foi alterado para {valor} segundos.",
            color=discord.Color.green()
        )
        if tipo in ["dicas", "sorte", "recompensa"]:
            embed.set_footer(text="A task será reiniciada na próxima execução.")
            canal_cog = self.bot.get_cog("CanalMensagens")
            if canal_cog:
                canal_cog.reiniciar_task(tipo, guild_id)
            else:
                embed.add_field(name="Aviso", value="Cog de canal não encontrado.", inline=False)
        elif tipo == "perdido":
            embed.set_footer(text="Aplicado na próxima verificação.")
        await ctx.send(embed=embed)

    @commands.command(help="Adiciona um novo personagem com nome, espécie e uma imagem. Exemplo: !!adicionar_personagem <nome> <espécie>")
    @evento_esquecimento()
    @no_dm()
    @maintenance_off()
    @apenas_moderador()
    async def adicionar_personagem(self, ctx, nome: str, especie: str):
        guild_id = str(ctx.guild.id)
        dados = carregar_dados_guild(guild_id)

        if not ctx.message.attachments:
            embed = discord.Embed(
                title="❌ Sem Imagem",
                description="Anexe uma imagem para o personagem.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        attachment = ctx.message.attachments[0]
        diretorio = os.path.join("resources", "poneis")
        os.makedirs(diretorio, exist_ok=True)

        extensao = attachment.filename.split('.')[-1].lower()
        if extensao not in ["png", "jpg", "jpeg"]:
            embed = discord.Embed(
                title="❌ Formato Inválido",
                description="Use apenas imagens .png, .jpg ou .jpeg.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        nome_sanitizado = nome.replace(" ", "_")
        caminho_imagem = os.path.join(diretorio, f"{nome_sanitizado}.{extensao}")

        try:
            image_bytes = await attachment.read()
            image = Image.open(io.BytesIO(image_bytes))
            width, height = image.size
            if width != 500:
                new_height = int(height * (500 / width))
                image = image.resize((500, new_height), Image.Resampling.LANCZOS)
            image.save(caminho_imagem, quality=95)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erro ao Processar Imagem",
                description=f"Ocorreu um erro: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if any(p["nome"].lower() == nome.lower() for p in dados["personagens"]):
            embed = discord.Embed(
                title="❌ Personagem Existente",
                description=f"'{nome}' já existe na lista de personagens.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        novo_personagem = {"nome": nome, "especie": especie}
        dados["personagens"].append(novo_personagem)
        dados.setdefault("personagens_inicial", []).append(novo_personagem)

        salvar_dados_guild(guild_id, dados)
        embed = discord.Embed(
            title="✅ Personagem Adicionado",
            description=f"'{nome}' ({especie}) foi adicionado com sucesso!",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=f"attachment://{nome_sanitizado}.{extensao}")
        await ctx.send(embed=embed, file=discord.File(caminho_imagem))

async def setup(bot):
    await bot.add_cog(Gerenciamento(bot))