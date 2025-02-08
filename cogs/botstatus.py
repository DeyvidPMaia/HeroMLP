# botstatus.py

import discord
from discord.ext import commands
import globals

class BotStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="status", help="Exibe o estado atual do bot e suas configurações.")
    async def exibir_status(self, ctx):
        total_personagens_disponiveis = len(globals.personagens_disponiveis)
        total_personagens_salvos = len(globals.personagens_salvos)
        total_usuarios_salvaram = len(globals.personagens_por_usuario)

        # Verificar se ultimo_usuario_salvador não é None antes de tentar buscar o usuário
        if globals.ultimo_usuario_salvador:
            try:
                # Buscar membro no servidor atual
                membro = ctx.guild.get_member(int(globals.ultimo_usuario_salvador)) if ctx.guild else None
                nome_usuario_salvador = membro.display_name if membro else None

                # Caso não encontre o membro no servidor, tenta buscar globalmente
                if not nome_usuario_salvador:
                    user = await self.bot.fetch_user(globals.ultimo_usuario_salvador)
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
        embed.add_field(name="🔒 Regra: Resgatar Apenas Um Por Vez", value=f"{'Ativada' if globals.restricao_usuario_unico else 'Desativada'}", inline=True)
        embed.add_field(name="👥 Usuários que Salvaram Personagens", value=f"{total_usuarios_salvaram}", inline=True)
        embed.add_field(name="⏳ Tempo de Impedimento", value=f"{globals.tempo_impedimento} segundos", inline=True)
        embed.add_field(name="🏆 Último usuário salvador", value=nome_usuario_salvador, inline=False)
        embed.set_footer(text="Continue ajudando nossos amigos. Que a magia da amizade te ajude nobre herói!")

        await ctx.send(embed=embed)

        # Paginação para exibir os usuários que salvaram personagens
        if globals.personagens_por_usuario:
            paginas = []
            descricao_atual = ""

            for user_id, personagens in globals.personagens_por_usuario.items():
                # Buscar membro no servidor atual ou globalmente
                membro = ctx.guild.get_member(int(user_id)) if ctx.guild else None
                nome_usuario = membro.display_name if membro else None

                if not nome_usuario:
                    try:
                        user = await self.bot.fetch_user(user_id)
                        nome_usuario = f"{user.name}#{user.discriminator}"
                    except Exception:
                        nome_usuario = f"Usuário {user_id}"

                entrada = f"**{nome_usuario}** salvou {len(personagens)} personagem(ns)\n"
                if len(descricao_atual) + len(entrada) > 1024:  # Limite de campo do Embed
                    paginas.append(descricao_atual)
                    descricao_atual = entrada
                else:
                    descricao_atual += entrada

            if descricao_atual:  # Adicionar a última página
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
