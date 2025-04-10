# loja.py 20/03/2025 13:00 (atualizado para botões funcionais persistentes e correção de níveis de perfil por usuário)

import discord
from discord.ext import commands
import asyncio
import time
import random
from funcoes import maintenance_off, no_dm
from server_data import carregar_dados_guild, salvar_dados_guild, carregar_estatisticas_usuario, salvar_estatisticas_seguro_usuario, evento_esquecimento
from biscoitosorte import biscoito_sorte
from views import PaginatedSelectionView, ConfirmationView

DEFAULT_LOJA = {
    "reduzir 25%": 4,
    "reduzir 50%": 2,
    "zerar tempo": 1,
    "personagem aleatorio": 1,
    "enviar biscoito": 5,
    "receber nome": 1,
    "changeling": 2,
    "filme": 1
}

class Loja(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.store_items = {
            "reduzir 25%": {"cost": 15, "effect": "reduce", "percent": 25, "description": "Reduz o tempo de espera em 25%.", "visivel": True, "compravel": True},
            "reduzir 50%": {"cost": 20, "effect": "reduce", "percent": 50, "description": "Reduz o tempo de espera em 50%.", "visivel": True, "compravel": True},
            "zerar tempo": {"cost": 30, "effect": "reset", "description": "Zera o tempo de espera, permitindo resgate imediato.", "visivel": True, "compravel": True},
            "personagem aleatorio": {"cost": 40, "effect": "random_character", "description": "Receba automaticamente um personagem ainda não salvo. (Mínimo: 20 sobrando)", "visivel": True, "compravel": True},
            "enviar biscoito": {"cost": 20, "effect": "send_cookie", "description": "Envia um biscoito da sorte no chat.", "visivel": True, "compravel": True},
            "trevo": {"cost": 25, "effect": "trevo", "description": "Adiciona 1 trevo à sua coleção, máximo 3.", "visivel": True, "compravel": True},
            "receber nome": {"cost": 20, "effect": "receber_nome", "description": "Envia na DM o nome de um personagem ainda não salvo.", "visivel": True, "compravel": True},
            "changeling": {"cost": 20, "effect": "changeling", "description": "Adquire um changeling (máximo 10). Será salvo como cha1, cha2, etc.", "visivel": True, "compravel": True},
            "perfil nivel 1": {"cost": 50, "effect": "upgrade_profile", "description": "Define seu perfil como Nível 1.", "visivel": True, "compravel": True},
            "perfil nivel 2": {"cost": 100, "effect": "upgrade_profile", "description": "Define seu perfil como Nível 2.", "visivel": True, "compravel": True},
            "perfil nivel 3": {"cost": 150, "effect": "upgrade_profile", "description": "Define seu perfil como Nível 3.", "visivel": True, "compravel": True},
            "album de fotos": {"cost": 250, "effect": "album", "description": "Desbloqueia a capacidade de comprar filmes.", "visivel": False, "compravel": False}
        }

    def reset_loja_if_needed(self, user_data):
        current_time = time.time()
        last_reset = user_data.get("loja_reset_timestamp", 0)
        if current_time - last_reset >= 7200:
            user_data["loja"] = DEFAULT_LOJA.copy()
            user_data["loja_reset_timestamp"] = current_time
            user_data["resets_loja"] = user_data.get("resets_loja", 0) + 1
        return user_data

    async def aplicar_efeito(self, ctx, item, dados, user_data, user_id, estatisticas):
        item_data = self.store_items[item]
        effect_applied = ""
        current_time = time.time()

        if item_data["effect"] == "reduce":
            tempo_impedimento = dados.get("tempo_impedimento", 300)
            ultimo_resgate = dados.get("ultimo_resgate_por_usuario", {}).get(user_id, None)
            remaining = 0 if ultimo_resgate is None else max(tempo_impedimento - (current_time - ultimo_resgate), 0)
            percent = item_data["percent"]
            new_remaining = remaining * (1 - percent / 100)
            new_last_resgate = current_time - (tempo_impedimento - new_remaining)
            dados.setdefault("ultimo_resgate_por_usuario", {})[user_id] = new_last_resgate
            effect_applied = f"Seu tempo foi reduzido em {percent}%."
        elif item_data["effect"] == "reset":
            tempo_impedimento = dados.get("tempo_impedimento", 300)
            dados.setdefault("ultimo_resgate_por_usuario", {})[user_id] = current_time - tempo_impedimento
            effect_applied = "Seu tempo foi zerado, permitindo resgate imediato."
        elif item_data["effect"] == "random_character":
            if len(dados.get("personagens", [])) <= 20:
                await ctx.send("❌ **Os personagens disponíveis diminuíram e não há mais suficientes para comprar este item.**")
                estatisticas["loja"]["erros_aplicacao_efeito_loja"] += 1
                return None
            saved_names = {p["nome"].lower() for p in dados.get("personagens_salvos", [])}
            unsaved = [p for p in dados.get("personagens", []) if p.get("nome", "").lower() not in saved_names]
            if unsaved:
                personagem = random.choice(unsaved)
                dados["personagens"].remove(personagem)
                dados.setdefault("personagens_salvos", []).append(personagem)
                dados.setdefault("contador_personagens_salvos", {})[user_id] = (
                    dados.get("contador_personagens_salvos", {}).get(user_id, 0) + 1
                )
                dados.setdefault("personagens_por_usuario", {}).setdefault(user_id, []).append(personagem)
                effect_applied = f"Você recebeu o personagem **{personagem['nome']}** automaticamente."
            else:
                effect_applied = "Todos os personagens já foram salvos!"
        elif item_data["effect"] == "send_cookie":
            await biscoito_sorte(ctx.channel, 'loja')
            effect_applied = "Um biscoito da sorte foi enviado ao chat."
        elif item_data["effect"] == "trevo":
            user_data["trevo"] = min(user_data.get("trevo", 0) + 1, 3)
            effect_applied = "Você recebeu 1 trevo!"
        elif item_data["effect"] == "receber_nome":
            saved_names = {p["nome"].lower() for p in dados.get("personagens_salvos", [])}
            unsaved = [p for p in dados.get("personagens", []) if p.get("nome", "").lower() not in saved_names]
            if unsaved:
                personagem = random.choice(unsaved)
                effect_applied = f"Um personagem foi enviado para você por DM."
                try:
                    await ctx.author.send(f"{personagem['nome']} é um personagem ainda não salvo")
                    estatisticas.setdefault("estatisticas_meus_personagens", {})
                    personagem_stats = estatisticas["estatisticas_meus_personagens"].setdefault(personagem["nome"], {
                        "resgatado": 0,
                        "enviado": 0,
                        "recebido": 0,
                        "exibido": 0,
                        "receber_nome_loja": 0,
                        "uso_como_changeling_conquista": 0,
                        "sorteado_para_recompensa": 0,
                        "coracoes_concedidos_recompensa": 0,
                        "nome_no_biscoito": 0,
                        "salvo_por_trevo_por_chamado": {},
                        "perdido_por_chamado": {},
                        "uso_como_changeling_conquista": 0
                    })
                    personagem_stats["receber_nome_loja"] += 1
                except Exception as e:
                    await ctx.send(f"❌ Erro ao enviar DM: {e}")
                    estatisticas["loja"]["erros_aplicacao_efeito_loja"] += 1
                    return None
            else:
                await ctx.send("❌ **Não há personagens disponíveis para comprar este item!**")
                estatisticas["loja"]["erros_aplicacao_efeito_loja"] += 1
                return None
        elif item_data["effect"] == "changeling":
            user_changelings = user_data.setdefault("changeling", [])
            if len(user_changelings) >= 10:
                await ctx.send("❌ **Você já possui o máximo de changelings (10).**")
                estatisticas["loja"]["erros_aplicacao_efeito_loja"] += 1
                return None
            new_changeling_name = f"cha{len(user_changelings)+1}"
            user_changelings.append(new_changeling_name)
            effect_applied = f"Você recebeu um novo changeling: {new_changeling_name}."
        elif item_data["effect"] == "upgrade_profile":
            nivel_atual = user_data.get("nivel_perfil", 0)
            if item == "perfil nivel 1" and nivel_atual == 0:
                user_data["nivel_perfil"] = 1
                estatisticas["loja"]["niveis_perfil_comprados"] = estatisticas["loja"].get("niveis_perfil_comprados", 0) + 1
                estatisticas["loja"]["nivel_perfil_atual"] = 1
                effect_applied = "Seu perfil foi atualizado para Nível 1!"
            elif item == "perfil nivel 2" and nivel_atual == 1:
                user_data["nivel_perfil"] = 2
                estatisticas["loja"]["niveis_perfil_comprados"] = estatisticas["loja"].get("niveis_perfil_comprados", 0) + 1
                estatisticas["loja"]["nivel_perfil_atual"] = 2
                effect_applied = "Seu perfil foi atualizado para Nível 2!"
            elif item == "perfil nivel 3" and nivel_atual == 2:
                user_data["nivel_perfil"] = 3
                estatisticas["loja"]["niveis_perfil_comprados"] = estatisticas["loja"].get("niveis_perfil_comprados", 0) + 1
                estatisticas["loja"]["nivel_perfil_atual"] = 3
                effect_applied = "Seu perfil foi atualizado para Nível 3!"
            else:
                await ctx.send("❌ **Você não pode comprar este nível de perfil agora.**")
                estatisticas["loja"]["erros_aplicacao_efeito_loja"] += 1
                return None
        elif item_data["effect"] == "album":
            user_data["album"] = True
            estatisticas["loja"]["album_adquirido"] = True
            self.store_items["album de fotos"]["visivel"] = False
            self.store_items["filme"] = {
                "cost": 100,
                "effect": "filme",
                "description": "Adiciona 1 filme à sua coleção.",
                "visivel": True,
                "compravel": True
            }
            effect_applied = "Você adquiriu o Álbum de Fotos!"
        elif item_data["effect"] == "filme":
            if not user_data.get("album", False):
                await ctx.send("❌ **Você precisa do Álbum de Fotos para comprar Filmes.**")
                estatisticas["loja"]["erros_aplicacao_efeito_loja"] += 1
                return None
            user_data["filme"] = user_data.get("filme", 0) + 1
            estatisticas["loja"]["filmes_comprados"] = estatisticas["loja"].get("filmes_comprados", 0) + 1
            effect_applied = f"Você adicionou 1 Filme à sua coleção! Total: {user_data['filme']}."

        return effect_applied

    async def comprar_item(self, ctx, item):
        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)

        estatisticas = carregar_estatisticas_usuario(guild_id, user_id)
        estatisticas.setdefault("loja", {
            "uso_comando_loja": 0,
            "visualizacoes_loja": 0,
            "compras_tentadas_loja": 0,
            "compras_concluidas_loja": 0,
            "compras_canceladas_loja": 0,
            "itens_comprados_loja": {},
            "coracoes_gastos_loja": 0,
            "tentativas_sem_coracoes_loja": 0,
            "tentativas_item_esgotado_loja": 0,
            "resets_loja": 0,
            "erros_aplicacao_efeito_loja": 0,
            "niveis_perfil_comprados": 0,
            "nivel_perfil_atual": 0,
            "album_adquirido": False,
            "filmes_comprados": 0
        })
        estatisticas["loja"]["compras_tentadas_loja"] += 1

        if item not in self.store_items:
            await ctx.send("❌ **Item não encontrado na loja.**")
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)
            return

        item_data = self.store_items[item]
        if not item_data["compravel"]:
            await ctx.send("❌ **Este item não está disponível para compra no momento.**")
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)
            return

        dados = carregar_dados_guild(guild_id)
        usuarios = dados.setdefault("usuarios", {})
        user_data = usuarios.setdefault(user_id, {
            "coracao": 0,
            "quantidade_amor": 0,
            "trevo": 0,
            "nivel_perfil": 0,
            "album": False,
            "filme": 0
        })
        user_data = self.reset_loja_if_needed(user_data)
        current_hearts = int(user_data.get("coracao", 0))

        cost = item_data["cost"]

        if current_hearts < cost:
            estatisticas["loja"]["tentativas_sem_coracoes_loja"] += 1
            await ctx.send(f"❌ **Você não tem corações suficientes!** Você possui: {current_hearts} corações")
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)
            return

        if item in DEFAULT_LOJA:
            disponibilidade = user_data.setdefault("loja", DEFAULT_LOJA.copy())
            if disponibilidade.get(item, 0) <= 0:
                estatisticas["loja"]["tentativas_item_esgotado_loja"] += 1
                await ctx.send("❌ **Item esgotado no momento.**")
                await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)
                return

        if item_data["effect"] == "random_character" and len(dados.get("personagens", [])) <= 20:
            await ctx.send("❌ **Não há personagens suficientes disponíveis (mínimo: 20 restantes).**")
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)
            return
        if item_data["effect"] == "trevo" and user_data.get("trevo", 0) >= 3:
            await ctx.send("❌ **Você já possui o máximo de trevos (3).**")
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)
            return
        if item_data["effect"] == "changeling" and len(user_data.get("changeling", [])) >= 10:
            await ctx.send("❌ **Você já possui o máximo de changelings (10).**")
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)
            return

        title = "Confirmação de Compra"
        description = f"{ctx.author.mention}, deseja comprar **{item.title()}** por {cost} corações?\nClique em 'Aceitar' para confirmar ou 'Cancelar' para desistir."
        view = ConfirmationView(ctx, [ctx.author], title, description, discord.Color.blue())
        msg = await ctx.send(embed=view.get_embed(), view=view)
        await view.wait()

        if view.cancelled or len(view.confirmations) != 1:
            estatisticas["loja"]["compras_canceladas_loja"] += 1
            await ctx.send("❌ **Compra cancelada.**")
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)
            return

        dados = carregar_dados_guild(guild_id)
        usuarios = dados.setdefault("usuarios", {})
        user_data = usuarios.setdefault(user_id, {
            "coracao": 0,
            "quantidade_amor": 0,
            "trevo": 0,
            "nivel_perfil": 0,
            "album": False,
            "filme": 0
        })
        user_data = self.reset_loja_if_needed(user_data)

        if user_data.get("coracao", 0) < cost:
            estatisticas["loja"]["tentativas_sem_coracoes_loja"] += 1
            await ctx.send("❌ **Seus corações diminuíram e você não tem mais o suficiente para comprar!**")
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)
            return

        effect_applied = await self.aplicar_efeito(ctx, item, dados, user_data, user_id, estatisticas)
        if effect_applied is None:
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)
            return

        user_data["coracao"] -= cost
        if item in DEFAULT_LOJA:
            user_data["loja"][item] -= 1

        estatisticas["loja"]["compras_concluidas_loja"] += 1
        estatisticas["loja"]["itens_comprados_loja"][item] = (
            estatisticas["loja"]["itens_comprados_loja"].get(item, 0) + 1
        )
        estatisticas["loja"]["coracoes_gastos_loja"] += cost

        usuarios[user_id] = user_data
        dados["usuarios"] = usuarios
        salvar_dados_guild(guild_id, dados)
        await ctx.send(f"✅ **Você comprou '{item.title()}'!** {effect_applied} (Corações debitados: {cost}).")
        await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)

    @commands.command(name="loja", help="Exibe a loja para comprar com botões ou compra direto com !!loja <nome_item>.")
    @evento_esquecimento()
    @maintenance_off()
    @no_dm()
    async def loja(self, ctx, *, item: str = None):
        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)

        estatisticas = carregar_estatisticas_usuario(guild_id, user_id)
        estatisticas.setdefault("loja", {
            "uso_comando_loja": 0,
            "visualizacoes_loja": 0,
            "compras_tentadas_loja": 0,
            "compras_concluidas_loja": 0,
            "compras_canceladas_loja": 0,
            "itens_comprados_loja": {},
            "coracoes_gastos_loja": 0,
            "tentativas_sem_coracoes_loja": 0,
            "tentativas_item_esgotado_loja": 0,
            "resets_loja": 0,
            "erros_aplicacao_efeito_loja": 0,
            "niveis_perfil_comprados": 0,
            "nivel_perfil_atual": 0,
            "album_adquirerical": False,
            "filmes_comprados": 0
        })
        estatisticas.setdefault("estatisticas_meus_personagens", {})
        estatisticas["loja"]["uso_comando_loja"] += 1

        dados = carregar_dados_guild(guild_id)
        usuarios = dados.setdefault("usuarios", {})
        user_data = usuarios.setdefault(user_id, {
            "coracao": 0,
            "quantidade_amor": 0,
            "trevo": 0,
            "nivel_perfil": 0,
            "album": False,
            "filme": 0
        })
        user_data = self.reset_loja_if_needed(user_data)
        usuarios[user_id] = user_data
        dados["usuarios"] = usuarios
        salvar_dados_guild(guild_id, dados)

        if item:
            await self.comprar_item(ctx, item.strip().lower())
            return

        estatisticas["loja"]["visualizacoes_loja"] += 1
        items_list = []
        nivel_atual = user_data.get("nivel_perfil", 0)
        for item_name, item_data in self.store_items.items():
            if not item_data["visivel"]:
                continue
            # Filtra os itens de perfil para mostrar apenas o próximo nível disponível
            if item_name.startswith("perfil nivel"):
                nivel_item = int(item_name.split("nivel ")[1])
                if nivel_item != nivel_atual + 1:
                    continue  # Pula níveis que não são o próximo
            if item_name in DEFAULT_LOJA:
                disponibilidade = user_data.get("loja", DEFAULT_LOJA.copy()).get(item_name, DEFAULT_LOJA[item_name])
                description = f"Custo: {item_data['cost']} ❤️ | Disponível: {disponibilidade}\n{item_data['description']}"
            elif item_name == "trevo":
                current_trevos = user_data.get("trevo", 0)
                description = f"Custo: {item_data['cost']} ❤️\n{item_data['description']} (Você tem: {current_trevos}/3)"
            else:
                description = f"Custo: {item_data['cost']} ❤️\n{item_data['description']}"
            items_list.append({"nome": item_name.title(), "especie": description})

        title = "🏪 Loja"
        description = f"Corações disponíveis: {user_data['coracao']}\nClique em um número para comprar ou use !!loja <nome_item> diretamente.\nBotões ativos por 60 segundos."
        view = PaginatedSelectionView(ctx, ctx.author, items_list, title, description, discord.Color.green())
        msg = await ctx.send(embed=view.get_embed(), view=view)

        # Função assíncrona para gerenciar o timeout
        async def manage_timeout():
            await asyncio.sleep(60)
            await msg.edit(view=None)

        # Inicia o gerenciamento do timeout em segundo plano
        asyncio.create_task(manage_timeout())

        # Processa interações até o timeout
        start_time = time.time()
        while time.time() - start_time < 60:  # Limite de 60 segundos
            if view.result:
                selected_item = view.result["nome"].lower()
                await self.comprar_item(ctx, selected_item)
                # Recarrega os dados após a compra
                dados = carregar_dados_guild(guild_id)
                usuarios = dados.setdefault("usuarios", {})
                user_data = usuarios.setdefault(user_id, {
                    "coracao": 0,
                    "quantidade_amor": 0,
                    "trevo": 0,
                    "nivel_perfil": 0,
                    "album": False,
                    "filme": 0
                })
                user_data = self.reset_loja_if_needed(user_data)
                # Atualiza a lista de itens
                items_list = []
                nivel_atual = user_data.get("nivel_perfil", 0)
                for item_name, item_data in self.store_items.items():
                    if not item_data["visivel"]:
                        continue
                    if item_name.startswith("perfil nivel"):
                        nivel_item = int(item_name.split("nivel ")[1])
                        if nivel_item != nivel_atual + 1:
                            continue
                    if item_name in DEFAULT_LOJA:
                        disponibilidade = user_data.get("loja", DEFAULT_LOJA.copy()).get(item_name, DEFAULT_LOJA[item_name])
                        description = f"Custo: {item_data['cost']} ❤️ | Disponível: {disponibilidade}\n{item_data['description']}"
                    elif item_name == "trevo":
                        current_trevos = user_data.get("trevo", 0)
                        description = f"Custo: {item_data['cost']} ❤️\n{item_data['description']} (Você tem: {current_trevos}/3)"
                    else:
                        description = f"Custo: {item_data['cost']} ❤️\n{item_data['description']}"
                    items_list.append({"nome": item_name.title(), "especie": description})
                view.items = items_list
                view.description = f"Corações disponíveis: {user_data['coracao']}\nClique em um número para comprar ou use !!loja <nome_item> diretamente.\nBotões ativos por {int(60 - (time.time() - start_time))} segundos."
                await msg.edit(embed=view.get_embed(), view=view)
                view.result = None  # Reseta para próxima interação
            await asyncio.sleep(0.1)  # Pequena pausa para não sobrecarregar o loop

        await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)

async def setup(bot):
    await bot.add_cog(Loja(bot))