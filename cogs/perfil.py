# perfil.py 22/03/2025 23:30 (adicionados totais na primeira página, limite de mensagem informado)

import discord
from discord.ext import commands
import math
from server_data import carregar_dados_guild, salvar_dados_guild, carregar_estatisticas_usuario, salvar_estatisticas_seguro_usuario

class ProfilePaginator(discord.ui.View):
    def __init__(self, embeds, user_id, guild_id, nivel_perfil, owner_id):
        super().__init__(timeout=180)
        self.embeds = embeds
        self.current_page = 0
        self.user_id = user_id
        self.guild_id = guild_id
        self.nivel_perfil = nivel_perfil
        self.owner_id = owner_id
        self.update_buttons()

    def update_buttons(self):
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == len(self.embeds) - 1

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.grey)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != int(self.owner_id):
            await interaction.response.send_message("Você não pode interagir com este perfil!", ephemeral=True)
            return
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.grey)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != int(self.owner_id):
            await interaction.response.send_message("Você não pode interagir com este perfil!", ephemeral=True)
            return
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

class ColorModal(discord.ui.Modal, title="Personalizar Cor do Perfil"):
    def __init__(self, bot, guild_id, user_id):
        super().__init__()
        self.bot = bot
        self.guild_id = guild_id
        self.user_id = user_id
        self.hex_color = discord.ui.TextInput(
            label="Cor Hexadecimal",
            placeholder="Insira um valor como #FF5733",
            default="#FFFFFF",
            max_length=7
        )
        self.add_item(self.hex_color)

    async def on_submit(self, interaction: discord.Interaction):
        color_str = self.hex_color.value.strip()
        if not color_str.startswith("#"):
            color_str = "#" + color_str
        try:
            color = int(color_str[1:], 16)
            if 0 <= color <= 0xFFFFFF:
                dados = carregar_dados_guild(self.guild_id)
                usuarios = dados.setdefault("usuarios", {})
                user_data = usuarios.setdefault(self.user_id, {"nivel_perfil": 0, "cor_perfil": "#FFFFFF"})
                user_data["cor_perfil"] = color_str
                usuarios[self.user_id] = user_data
                dados["usuarios"] = usuarios
                salvar_dados_guild(self.guild_id, dados)
                estatisticas = carregar_estatisticas_usuario(self.guild_id, self.user_id)
                estatisticas.setdefault("perfil", {"visualizacoes": {"nivel_1": 0, "nivel_2": 0, "nivel_3": 0}, "alteracoes_cor": 0})
                estatisticas["perfil"]["alteracoes_cor"] += 1
                await salvar_estatisticas_seguro_usuario(self.guild_id, self.user_id, estatisticas)
                await interaction.response.send_message(f"Cor do perfil alterada para `{color_str}`!", ephemeral=True)
            else:
                await interaction.response.send_message("Valor hexadecimal fora do intervalo válido (0 a FFFFFF)!", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Por favor, insira um valor hexadecimal válido (ex.: #FF5733)!", ephemeral=True)

class MessageModal(discord.ui.Modal, title="Personalizar Mensagem do Perfil"):
    def __init__(self, bot, guild_id, user_id):
        super().__init__()
        self.bot = bot
        self.guild_id = guild_id
        self.user_id = user_id
        self.message = discord.ui.TextInput(
            label="Mensagem Personalizada (máx. 100 caracteres)",
            placeholder="Insira sua mensagem aqui",
            max_length=100
        )
        self.add_item(self.message)

    async def on_submit(self, interaction: discord.Interaction):
        mensagem = self.message.value.strip()
        if mensagem:
            dados = carregar_dados_guild(self.guild_id)
            usuarios = dados.setdefault("usuarios", {})
            user_data = usuarios.setdefault(self.user_id, {"nivel_perfil": 0, "cor_perfil": "#FFFFFF", "mensagem_perfil": "Ajudando Nossos Amigos de Equestria"})
            user_data["mensagem_perfil"] = mensagem
            usuarios[self.user_id] = user_data
            dados["usuarios"] = usuarios
            salvar_dados_guild(self.guild_id, dados)
            estatisticas = carregar_estatisticas_usuario(self.guild_id, self.user_id)
            estatisticas.setdefault("perfil", {"visualizacoes": {"nivel_1": 0, "nivel_2": 0, "nivel_3": 0}, "alteracoes_cor": 0, "alteracoes_mensagem": 0})
            estatisticas["perfil"]["alteracoes_mensagem"] += 1
            await salvar_estatisticas_seguro_usuario(self.guild_id, self.user_id, estatisticas)
            await interaction.response.send_message(f"Mensagem do perfil alterada para: `{mensagem}`!", ephemeral=True)
        else:
            await interaction.response.send_message("A mensagem não pode estar vazia!", ephemeral=True)

class Perfil(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="perfil")
    async def perfil(self, ctx, target: discord.Member = None):
        guild_id = str(ctx.guild.id)
        owner_id = str(ctx.author.id)
        user = target if target else ctx.author
        user_id = str(user.id)

        dados = carregar_dados_guild(guild_id)
        usuarios = dados.setdefault("usuarios", {})
        user_data = usuarios.get(user_id, {})
        user_data.setdefault("nivel_perfil", 0)
        user_data.setdefault("cor_perfil", "#FFFFFF")
        user_data.setdefault("mensagem_perfil", "Ajudando Nossos Amigos de Equestria")
        usuarios[user_id] = user_data
        dados["usuarios"] = usuarios
        salvar_dados_guild(guild_id, dados)

        nivel_perfil = user_data["nivel_perfil"]
        cor_perfil = int(user_data["cor_perfil"][1:], 16)
        mensagem_perfil = user_data["mensagem_perfil"]

        estatisticas = carregar_estatisticas_usuario(guild_id, user_id)
        estatisticas.setdefault("perfil", {"visualizacoes": {"nivel_1": 0, "nivel_2": 0, "nivel_3": 0}, "alteracoes_cor": 0, "alteracoes_mensagem": 0})

        if nivel_perfil == 0:
            if user_id == owner_id:
                await ctx.send("Você ainda não pode usar este comando.")
            else:
                await ctx.send(f"{user.name} ainda não tem um perfil visível.")
            return

        if user_id == owner_id:
            estatisticas["perfil"]["visualizacoes"][f"nivel_{nivel_perfil}"] = estatisticas["perfil"]["visualizacoes"].get(f"nivel_{nivel_perfil}", 0) + 1
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)

        estrelas = "⭐" * nivel_perfil + "🌙" * (5 - nivel_perfil)
        embeds = []

        # Calcula totais para a primeira página
        total_coracoes = (
            estatisticas.get("amor", {}).get("coracoes_ganhos_amor", 0) +
            estatisticas.get("resgatar", {}).get("coracoes_ganhos_resgatar", 0) +
            estatisticas.get("exibir", {}).get("coracoes_ganhos_exibir", 0)
        )
        personagens = estatisticas.get("estatisticas_meus_personagens", {})
        total_resgatados = sum(stats.get("resgatado", 0) for stats in personagens.values())
        total_trevos = sum(sum(stats.get("salvo_por_trevo_por_chamado", {}).values()) for stats in personagens.values())
        total_gasto_loja = estatisticas.get("loja", {}).get("coracoes_gastos_loja", 0)

        # Nível 1: Perfil básico com totais
        if nivel_perfil >= 1:
            embed_n1 = discord.Embed(
                title=f"Perfil de {user.name}",
                description=f"*{mensagem_perfil}*",
                color=cor_perfil
            )
            embed_n1.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
            embed_n1.add_field(name="Nome", value=user.mention, inline=False)
            embed_n1.add_field(name="Nível do Perfil", value=estrelas, inline=False)
            embed_n1.add_field(name="Corações Ganhos", value=total_coracoes, inline=True)
            embed_n1.add_field(name="Personagens Resgatados", value=total_resgatados, inline=True)
            embed_n1.add_field(name="Trevos Usados", value=total_trevos, inline=True)
            embed_n1.add_field(name="Corações Gastos na Loja", value=total_gasto_loja, inline=True)
            embed_n1.set_footer(text=f"Visualizações: {estatisticas['perfil']['visualizacoes']['nivel_1']}")
            embeds.append(embed_n1)

        # Nível 2: Estatísticas por comando em páginas separadas
        if nivel_perfil >= 2:
            secoes = ["usuario", "amor", "resgatar", "loja", "exibir", "trocar"]
            pagina_atual = len(embeds)
            total_paginas_nivel_2 = 0

            for secao in secoes:
                stats = estatisticas.get(secao, {})
                campos_nao_nulos = {k: v for k, v in stats.items() if v != 0 and isinstance(v, (int, float))}
                if not campos_nao_nulos:
                    continue

                campos_lista = list(campos_nao_nulos.items())
                itens_por_pagina = 25
                total_paginas_secao = math.ceil(len(campos_lista) / itens_por_pagina)

                for pagina_secao in range(total_paginas_secao):
                    embed_n2 = discord.Embed(
                        title=f"📊 Estatísticas: {secao.capitalize()}{' (Comandos Base)' if secao == 'usuario' else ''}",
                        description="Aqui estão suas contribuições em Equestria!",
                        color=cor_perfil
                    )
                    embed_n2.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
                    inicio = pagina_secao * itens_por_pagina
                    fim = inicio + itens_por_pagina
                    for chave, valor in campos_lista[inicio:fim]:
                        nome_campo = chave.replace("_", " ").capitalize()
                        embed_n2.add_field(name=nome_campo, value=valor, inline=False)
                    total_paginas_nivel_2 += 1
                    pagina_atual += 1
                    embed_n2.set_footer(text=f"Página {pagina_atual}/{len(embeds) + total_paginas_nivel_2 + (nivel_perfil >= 3)} | Visualizações: {estatisticas['perfil']['visualizacoes']['nivel_2']} | Alterações de Cor: {estatisticas['perfil']['alteracoes_cor']}")
                    embeds.append(embed_n2)

        # Nível 3: Legenda e Estatísticas de Personagens
        if nivel_perfil >= 3:
            embed_legenda = discord.Embed(
                title="🐴 Legenda para Estatísticas de Personagens",
                description=(
                    "📤 **Enviado**: Personagens enviados\n"
                    "📥 **Recebido**: Personagens recebidos\n"
                    "📺 **Exibido**: Vezes exibido\n"
                    "🍀 **Salvo por Trevo**: Salvo em personagem perdido\n"
                    "🥀 **Perdido**: Perdido em personagem perdido\n"
                    "⭐ **Resgatado**: Resgatado do esquecimento\n"
                    "🎁 **Recompensa**: Sorteado para recompensa\n"
                    "🍪 **Biscoito**: Nome no biscoito da sorte"
                ),
                color=cor_perfil
            )
            embed_legenda.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
            embed_legenda.set_footer(text=f"Página {len(embeds) + 1}/{len(embeds) + 1 + math.ceil(len(personagens) / 5)} | Visualizações: {estatisticas['perfil']['visualizacoes']['nivel_3']}")
            embeds.append(embed_legenda)

            personagens_lista = list(personagens.items())
            itens_por_pagina = 5
            total_paginas = math.ceil(len(personagens_lista) / itens_por_pagina)

            for pagina in range(total_paginas):
                embed_n3 = discord.Embed(
                    title="🐴 Estatísticas de Personagens",
                    color=cor_perfil
                )
                embed_n3.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
                inicio = pagina * itens_por_pagina
                fim = inicio + itens_por_pagina
                for nome, stats in personagens_lista[inicio:fim]:
                    valor = (
                        f"📤 {stats.get('enviado', 0)} | 📥 {stats.get('recebido', 0)} | 📺 {stats.get('exibido', 0)}\n"
                        f"🍀 {sum(stats.get('salvo_por_trevo_por_chamado', {}).values())} | 🥀 {sum(stats.get('perdido_por_chamado', {}).values())}\n"
                        f"⭐ {stats.get('resgatado', 0)} | 🎁 {stats.get('sorteado_para_recompensa', 0)} | 🍪 {stats.get('nome_no_biscoito', 0)}"
                    )
                    embed_n3.add_field(name=nome, value=valor, inline=False)
                embed_n3.set_footer(text=f"Página {len(embeds) + 1}/{len(embeds) + total_paginas} | Visualizações: {estatisticas['perfil']['visualizacoes']['nivel_3']} | Alterações de Mensagem: {estatisticas['perfil']['alteracoes_mensagem']}")
                embeds.append(embed_n3)

        view = ProfilePaginator(embeds, user_id, guild_id, nivel_perfil, owner_id)

        if user_id == owner_id:
            if nivel_perfil >= 2:
                async def color_callback(interaction: discord.Interaction):
                    if interaction.user.id != int(user_id):
                        await interaction.response.send_message("Você não pode alterar a cor deste perfil!", ephemeral=True)
                        return
                    await interaction.response.send_modal(ColorModal(self.bot, guild_id, user_id))

                color_button = discord.ui.Button(label="🎨", style=discord.ButtonStyle.blurple, custom_id="alterar_cor")
                color_button.callback = color_callback
                view.add_item(color_button)

            if nivel_perfil >= 3:
                async def message_callback(interaction: discord.Interaction):
                    if interaction.user.id != int(user_id):
                        await interaction.response.send_message("Você não pode alterar a mensagem deste perfil!", ephemeral=True)
                        return
                    await interaction.response.send_modal(MessageModal(self.bot, guild_id, user_id))

                message_button = discord.ui.Button(label="✍️", style=discord.ButtonStyle.green, custom_id="alterar_mensagem")
                message_button.callback = message_callback
                view.add_item(message_button)

        await ctx.send(embed=embeds[0], view=view)

async def setup(bot):
    await bot.add_cog(Perfil(bot))