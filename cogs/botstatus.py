#botstatus.py

import discord
from discord.ext import commands
from server_data import carregar_dados_guild, evento_esquecimento
import globals  # Utilizado para valores padrão (caso a guild não tenha configurado algum parâmetro)
from funcoes import apenas_moderador, maintenance_off, no_dm
import time
import datetime

class BotStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="status", help="Exibe o estado atual do bot e suas configurações.")
    @evento_esquecimento()
    @no_dm()
    @maintenance_off()
    @apenas_moderador()
    async def exibir_status(self, ctx):
        guild_id = str(ctx.guild.id)
        dados = carregar_dados_guild(guild_id)

        total_personagens_disponiveis = len(dados.get("personagens", []))
        total_personagens_salvos = len(dados.get("personagens_salvos", []))
        total_usuarios_salvaram = len(dados.get("personagens_por_usuario", {}))
        tempo_impedimento = dados.get("tempo_impedimento", globals.tempo_impedimento)
        # Novos parâmetros:
        tempo_dicas = dados.get("intervalo_dica_personagem", globals.intervalo_dica_personagem)
        tempo_sorte = dados.get("tempo_sorte", globals.tempo_sorte)
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
        embed.add_field(name="⏰ Tempo de Dicas", value=f"{tempo_dicas} segundos", inline=True)
        embed.add_field(name="🍀 Tempo de Sorte", value=f"{tempo_sorte} segundos", inline=True)
        embed.add_field(name="🏆 Último usuário salvador", value=nome_usuario_salvador, inline=False)
        embed.set_footer(text="Continue ajudando nossos amigos. Que a magia da amizade te ajude nobre herói!")

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(BotStatus(bot))
