# trocar.py 21/03/2025 11:00 (atualizado para cancelar timeout após seleção)

import discord
from discord.ext import commands
from server_data import carregar_dados_guild, salvar_dados_guild, carregar_estatisticas_usuario, salvar_estatisticas_seguro_usuario, evento_esquecimento
from funcoes import no_dm, maintenance_off, normalize
import asyncio
import time
from views import PaginatedSelectionView, ConfirmationView

class TrocaCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def escolher_personagem(self, ctx, user, personagens):
        title = "Trocar - Escolha seu personagem"
        description = "Clique em um número para selecionar (60 segundos para escolher):"
        color = discord.Color.green() if user == ctx.author else discord.Color.orange()
        view = PaginatedSelectionView(ctx, user, personagens, title, description, color)
        msg = await ctx.send(embed=view.get_embed(), view=view)

        # Gerencia o timeout em segundo plano
        timeout_task = None
        async def manage_timeout():
            await asyncio.sleep(60)
            await msg.edit(view=None)
            await ctx.send(f"⏰ Tempo esgotado para {user.name} escolher um personagem.")

        # Inicia a tarefa e armazena a referência
        timeout_task = asyncio.create_task(manage_timeout())

        # Aguarda a seleção por até 60 segundos
        start_time = time.time()
        while time.time() - start_time < 60:
            if view.result:
                timeout_task.cancel()  # Cancela a tarefa de timeout
                await msg.edit(view=None)  # Remove os botões após a seleção
                return view.result
            await asyncio.sleep(0.1)  # Pequena pausa para não sobrecarregar
        
        # Se o loop terminar (timeout), a tarefa já enviou a mensagem, então apenas retorna None
        return None

    @commands.command(name="trocar", help="Troca um personagem seu por outro de outro usuário. Use !!trocar <ID ou @usuário> e siga as instruções.")
    @evento_esquecimento()
    @no_dm()
    @maintenance_off()
    async def trocar(self, ctx, target_arg: str):
        required_hearts = 5

        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)
        estatisticas_autor = carregar_estatisticas_usuario(guild_id, user_id)
        estatisticas_autor.setdefault("trocar", {
            "uso_comando_troca": 0,
            "trocas_iniciadas_troca": 0,
            "trocas_concluidas_troca": 0,
            "trocas_canceladas_troca": 0,
            "coracoes_gastos_troca": 0,
            "tentativas_sem_coracoes_troca": 0,
            "tentativas_sem_personagens_troca": 0,
            "timeout_escolha_troca": 0,
            "usuarios_trocados_troca": {}
        })
        estatisticas_autor.setdefault("estatisticas_meus_personagens", {})
        estatisticas_autor["trocar"]["uso_comando_troca"] += 1

        try:
            if target_arg.startswith("<@") and target_arg.endswith(">"):
                target_id = target_arg[2:-1].replace("!", "")
                target = await self.bot.fetch_user(int(target_id))
            else:
                target = await self.bot.fetch_user(int(target_arg))
        except (discord.NotFound, ValueError):
            await ctx.send("❌ **ID ou menção inválida. Use @usuário ou o ID correto.**")
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas_autor)
            return

        target_id = str(target.id)
        estatisticas_alvo = carregar_estatisticas_usuario(guild_id, target_id)
        estatisticas_alvo.setdefault("trocar", {
            "uso_comando_troca": 0,
            "trocas_iniciadas_troca": 0,
            "trocas_concluidas_troca": 0,
            "trocas_canceladas_troca": 0,
            "coracoes_gastos_troca": 0,
            "tentativas_sem_coracoes_troca": 0,
            "tentativas_sem_personagens_troca": 0,
            "timeout_escolha_troca": 0,
            "usuarios_trocados_troca": {}
        })
        estatisticas_alvo.setdefault("estatisticas_meus_personagens", {})

        if target.id == ctx.author.id:
            await ctx.send("❌ Você não pode trocar com você mesmo.")
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas_autor)
            return

        estatisticas_autor["trocar"]["trocas_iniciadas_troca"] += 1
        estatisticas_alvo["trocar"]["trocas_iniciadas_troca"] += 1

        dados = carregar_dados_guild(guild_id)
        usuarios = dados.get("usuarios", {})
        autor_data = usuarios.get(user_id, {"coracao": 0, "quantidade_amor": 0})
        target_data = usuarios.get(target_id, {"coracao": 0, "quantidade_amor": 0})

        if autor_data.get("coracao", 0) < required_hearts:
            estatisticas_autor["trocar"]["tentativas_sem_coracoes_troca"] += 1
            estatisticas_alvo["trocar"]["tentativas_sem_coracoes_troca"] += 1
            await ctx.send(f"❌ Você precisa de pelo menos {required_hearts} ❤️ para realizar a troca.")
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas_autor)
            await salvar_estatisticas_seguro_usuario(guild_id, target_id, estatisticas_alvo)
            return
        if target_data.get("coracao", 0) < required_hearts:
            estatisticas_autor["trocar"]["tentativas_sem_coracoes_troca"] += 1
            estatisticas_alvo["trocar"]["tentativas_sem_coracoes_troca"] += 1
            await ctx.send(f"❌ {target.name} precisa de pelo menos {required_hearts} ❤️ para realizar a troca.")
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas_autor)
            await salvar_estatisticas_seguro_usuario(guild_id, target_id, estatisticas_alvo)
            return

        personagens_por_usuario = dados.get("personagens_por_usuario", {})
        autor_personagens = personagens_por_usuario.get(user_id, [])
        target_personagens = personagens_por_usuario.get(target_id, [])

        if not autor_personagens:
            estatisticas_autor["trocar"]["tentativas_sem_personagens_troca"] += 1
            estatisticas_alvo["trocar"]["tentativas_sem_personagens_troca"] += 1
            await ctx.send("❌ Você não possui personagens para trocar.")
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas_autor)
            await salvar_estatisticas_seguro_usuario(guild_id, target_id, estatisticas_alvo)
            return
        if not target_personagens:
            estatisticas_autor["trocar"]["tentativas_sem_personagens_troca"] += 1
            estatisticas_alvo["trocar"]["tentativas_sem_personagens_troca"] += 1
            await ctx.send(f"❌ {target.name} não possui personagens para trocar.")
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas_autor)
            await salvar_estatisticas_seguro_usuario(guild_id, target_id, estatisticas_alvo)
            return

        # Passo 1: Escolha do personagem do autor
        meu_personagem_obj = await self.escolher_personagem(ctx, ctx.author, autor_personagens)
        if meu_personagem_obj is None:
            estatisticas_autor["trocar"]["timeout_escolha_troca"] += 1
            estatisticas_alvo["trocar"]["timeout_escolha_troca"] += 1
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas_autor)
            await salvar_estatisticas_seguro_usuario(guild_id, target_id, estatisticas_alvo)
            return

        # Passo 2: Escolha do personagem do alvo
        personagem_alvo_obj = await self.escolher_personagem(ctx, target, target_personagens)
        if personagem_alvo_obj is None:
            estatisticas_autor["trocar"]["timeout_escolha_troca"] += 1
            estatisticas_alvo["trocar"]["timeout_escolha_troca"] += 1
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas_autor)
            await salvar_estatisticas_seguro_usuario(guild_id, target_id, estatisticas_alvo)
            return

        # Passo 3: Confirmação final de ambos
        title = "Confirmação de Troca"
        description = (
            f"Proposta de troca:\n"
            f"**{meu_personagem_obj['nome']}** (dado por {ctx.author.name}) ↔ **{personagem_alvo_obj['nome']}** (dado por {target.name})\n\n"
            f"{ctx.author.mention} e {target.mention}, ambos devem clicar em 'Aceitar' para confirmar.\n"
            f"Se um de vocês clicar em 'Cancelar', a troca será cancelada."
        )
        view = ConfirmationView(ctx, [ctx.author, target], title, description, discord.Color.blue())
        msg_confirm = await ctx.send(embed=view.get_embed(), view=view)
        await view.wait()

        if view.cancelled:
            estatisticas_autor["trocar"]["trocas_canceladas_troca"] += 1
            estatisticas_alvo["trocar"]["trocas_canceladas_troca"] += 1
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas_autor)
            await salvar_estatisticas_seguro_usuario(guild_id, target_id, estatisticas_alvo)
            return

        if len(view.confirmations) != 2:
            estatisticas_autor["trocar"]["trocas_canceladas_troca"] += 1
            estatisticas_alvo["trocar"]["trocas_canceladas_troca"] += 1
            await ctx.send("❌ Troca não foi confirmada por ambos os usuários.")
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas_autor)
            await salvar_estatisticas_seguro_usuario(guild_id, target_id, estatisticas_alvo)
            return

        # Recarrega os dados para evitar inconsistências
        dados = carregar_dados_guild(guild_id)
        usuarios = dados.get("usuarios", {})
        personagens_por_usuario = dados.get("personagens_por_usuario", {})
        autor_personagens = personagens_por_usuario.get(user_id, [])
        target_personagens = personagens_por_usuario.get(target_id, [])

        meu_idx = next((i for i, p in enumerate(autor_personagens) if p["nome"] == meu_personagem_obj["nome"]), None)
        alvo_idx = next((i for i, p in enumerate(target_personagens) if p["nome"] == personagem_alvo_obj["nome"]), None)

        if meu_idx is None or alvo_idx is None:
            estatisticas_autor["trocar"]["trocas_canceladas_troca"] += 1
            estatisticas_alvo["trocar"]["trocas_canceladas_troca"] += 1
            await ctx.send("❌ Um dos personagens selecionados não está mais disponível.")
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas_autor)
            await salvar_estatisticas_seguro_usuario(guild_id, target_id, estatisticas_alvo)
            return

        autor_data = usuarios.get(user_id, {"coracao": 0})
        target_data = usuarios.get(target_id, {"coracao": 0})
        if autor_data.get("coracao", 0) < required_hearts or target_data.get("coracao", 0) < required_hearts:
            estatisticas_autor["trocar"]["tentativas_sem_coracoes_troca"] += 1
            estatisticas_alvo["trocar"]["tentativas_sem_coracoes_troca"] += 1
            await ctx.send("❌ Um dos usuários não possui corações suficientes no momento.")
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas_autor)
            await salvar_estatisticas_seguro_usuario(guild_id, target_id, estatisticas_alvo)
            return

        # Realiza a troca
        autor_data["coracao"] -= required_hearts
        target_data["coracao"] -= required_hearts

        meu_personagem_nome = meu_personagem_obj["nome"]
        personagem_alvo_nome = personagem_alvo_obj["nome"]

        for user, personagem_enviado, personagem_recebido, outro_user, estatisticas in [
            (user_id, meu_personagem_nome, personagem_alvo_nome, target.name, estatisticas_autor),
            (target_id, personagem_alvo_nome, meu_personagem_nome, ctx.author.name, estatisticas_alvo)
        ]:
            estatisticas["estatisticas_meus_personagens"].setdefault(personagem_enviado, {
                "resgatado": 0,
                "enviado": 0,
                "recebido": 0,
                "exibido": 0,
                "uso_como_changeling_conquista": 0,
                "sorteado_para_recompensa": 0,
                "coracoes_concedidos_recompensa": 0,
                "nome_no_biscoito": 0,
                "salvo_por_trevo_por_chamado": {},
                "perdido_por_chamado": {},
                "receber_nome_loja": 0
            })
            estatisticas["estatisticas_meus_personagens"].setdefault(personagem_recebido, {
                "resgatado": 0,
                "enviado": 0,
                "recebido": 0,
                "exibido": 0,
                "uso_como_changeling_conquista": 0,
                "sorteado_para_recompensa": 0,
                "coracoes_concedidos_recompensa": 0,
                "nome_no_biscoito": 0,
                "salvo_por_trevo_por_chamado": {},
                "perdido_por_chamado": {},
                "receber_nome_loja": 0
            })
            estatisticas["estatisticas_meus_personagens"][personagem_enviado]["enviado"] += 1
            estatisticas["estatisticas_meus_personagens"][personagem_recebido]["recebido"] += 1
            estatisticas["trocar"]["usuarios_trocados_troca"][outro_user] = (
                estatisticas["trocar"]["usuarios_trocados_troca"].get(outro_user, 0) + 1
            )

        estatisticas_autor["trocar"]["trocas_concluidas_troca"] += 1
        estatisticas_alvo["trocar"]["trocas_concluidas_troca"] += 1
        estatisticas_autor["trocar"]["coracoes_gastos_troca"] += required_hearts
        estatisticas_alvo["trocar"]["coracoes_gastos_troca"] += required_hearts

        autor_personagens[meu_idx], target_personagens[alvo_idx] = target_personagens[alvo_idx], autor_personagens[meu_idx]

        personagens_por_usuario[user_id] = autor_personagens
        personagens_por_usuario[target_id] = target_personagens
        usuarios[user_id] = autor_data
        usuarios[target_id] = target_data

        dados["usuarios"] = usuarios
        dados["personagens_por_usuario"] = personagens_por_usuario

        salvar_dados_guild(guild_id, dados)
        await ctx.send(f"✅ Troca realizada! {ctx.author.name} deu **{meu_personagem_obj['nome']}** e recebeu **{personagem_alvo_obj['nome']}** de {target.name}. (-{required_hearts} ❤️ cada)")
        await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas_autor)
        await salvar_estatisticas_seguro_usuario(guild_id, target_id, estatisticas_alvo)

async def setup(bot):
    await bot.add_cog(TrocaCommands(bot))