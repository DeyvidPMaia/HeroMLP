# botstatus.py

import discord
from discord.ext import commands
from server_data import carregar_dados_guild
import globals  # Utilizado para valores padrão (caso a guild não tenha configurado algum parâmetro)
from funcoes import apenas_moderador

class BotStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="status", help="Exibe o estado atual do bot e suas configurações.")
    @apenas_moderador()
    async def exibir_status(self, ctx):
        guild_id = str(ctx.guild.id)
        dados = carregar_dados_guild(guild_id)

        total_personagens_disponiveis = len(dados.get("personagens", []))
        total_personagens_salvos = len(dados.get("personagens_salvos", []))
        total_usuarios_salvaram = len(dados.get("personagens_por_usuario", {}))
        tempo_impedimento = dados.get("tempo_impedimento", globals.tempo_impedimento)
        restricao = dados.get("restricao_usuario_unico", globals.restricao_usuario_unico)
        ultimo_usuario_salvador = dados.get("ultimo_usuario_salvador", None)

        # Processa o último usuário salvador para exibição
        if ultimo_usuario_salvador:
            try:
                membro = ctx.guild.get_member(int(ultimo_usuario_salvador)) if ctx.guild else None
                nome_usuario_salvador = membro.display_name if membro else None
                if not nome_usuario_salvador:
                    user = await self.bot.fetch_user(ultimo_usuario_salvador)
                    nome_usuario_salvador = f"{user.name}#{user.discriminator}"
            except Exception as e:
                nome_usuario_salvador = "Usuário desconhecido"
                print(f"Erro ao buscar o usuário: {e}")
        else:
            nome_usuario_salvador = "Nenhum usuário registrado"

        embed = discord.Embed(
            title="📊 Status Atual do Bot",
            color=discord.Color.blue()
        )
        embed.add_field(name="🌟 Personagens já resgatados", value=f"{total_personagens_salvos}", inline=True)
        embed.add_field(name="🚨 Personagens Não resgatados", value=f"{total_personagens_disponiveis}", inline=True)
        embed.add_field(name="🔒 Regra: Resgatar Apenas Um Por Vez", value=f"{'Ativada' if restricao else 'Desativada'}", inline=True)
        embed.add_field(name="👥 Usuários que Salvaram Personagens", value=f"{total_usuarios_salvaram}", inline=True)
        embed.add_field(name="⏳ Tempo de Impedimento", value=f"{tempo_impedimento} segundos", inline=True)
        embed.add_field(name="🏆 Último usuário salvador", value=nome_usuario_salvador, inline=False)
        embed.set_footer(text="Continue ajudando nossos amigos. Que a magia da amizade te ajude nobre herói!")

        await ctx.send(embed=embed)

        # Paginação para exibir os usuários que salvaram personagens
        personagens_por_usuario = dados.get("personagens_por_usuario", {})
        if personagens_por_usuario:
            paginas = []
            descricao_atual = ""
            for user_id, personagens in personagens_por_usuario.items():
                # Tenta buscar o usuário no servidor ou via API do Discord
                membro = ctx.guild.get_member(int(user_id)) if ctx.guild else None
                nome_usuario = membro.display_name if membro else None
                if not nome_usuario:
                    try:
                        user = await self.bot.fetch_user(user_id)
                        nome_usuario = f"{user.name}#{user.discriminator}"
                    except Exception:
                        nome_usuario = f"Usuário {user_id}"

                entrada = f"**{nome_usuario}** salvou {len(personagens)} personagem(ns)\n"
                if len(descricao_atual) + len(entrada) > 1024:  # Limite do campo de descrição do Embed
                    paginas.append(descricao_atual)
                    descricao_atual = entrada
                else:
                    descricao_atual += entrada

            if descricao_atual:
                paginas.append(descricao_atual)

            for i, pagina in enumerate(paginas, start=1):
                embed_pagina = discord.Embed(
                    title=f"👥 Usuários que Salvaram Personagens (Página {i}/{len(paginas)})",
                    description=pagina,
                    color=discord.Color.purple()
                )
                await ctx.send(embed=embed_pagina)
        else:
            await ctx.send("📜 Nenhum usuário salvou personagens ainda.")


# Setup para registrar o cog
async def setup(bot):
    await bot.add_cog(BotStatus(bot))
