import discord
from discord.ext import commands
from funcoes import maintenance_off, no_dm
import discord.utils
import asyncio

class Ajuda(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def paginate(self, ctx, comandos_gerais, comandos_adm):
        """Função de paginação para exibir comandos com navegação por reações."""
        items_per_page = 10
        total_gerais = len(comandos_gerais)
        total_adm = len(comandos_adm)
        pages_gerais = (total_gerais + items_per_page - 1) // items_per_page
        total_pages = pages_gerais + (total_adm + items_per_page - 1) // items_per_page
        current_page = [0]  # Usamos lista para modificação

        def get_embed(page):
            if page < pages_gerais:  # Páginas de comandos gerais
                start = page * items_per_page
                end = min(start + items_per_page, total_gerais)
                embed = discord.Embed(
                    title="📜 Comandos Gerais",
                    description="\n".join(comandos_gerais[start:end]) if comandos_gerais[start:end] else "Nenhum comando geral disponível.",
                    color=discord.Color.blue()
                )
            else:  # Páginas de comandos administrativos
                adm_page = page - pages_gerais
                start = adm_page * items_per_page
                end = min(start + items_per_page, total_adm)
                embed = discord.Embed(
                    title="🔒 Comandos Administrativos",
                    description="\n".join(comandos_adm[start:end]) if comandos_adm[start:end] else "Nenhum comando administrativo disponível.",
                    color=discord.Color.red()
                )
            embed.set_footer(text=f"Página {page + 1}/{total_pages}")
            return embed

        message = await ctx.send(embed=get_embed(current_page[0]))
        if total_pages <= 1:
            return

        navigation_emojis = ["⏪", "◀", "▶", "⏩"]
        for emoji in navigation_emojis:
            await message.add_reaction(emoji)

        def check(reaction, user):
            return (
                user == ctx.author and 
                reaction.message.id == message.id and 
                str(reaction.emoji) in navigation_emojis
            )

        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                if str(reaction.emoji) == "⏪":
                    current_page[0] = 0
                elif str(reaction.emoji) == "◀" and current_page[0] > 0:
                    current_page[0] -= 1
                elif str(reaction.emoji) == "▶" and current_page[0] < total_pages - 1:
                    current_page[0] += 1
                elif str(reaction.emoji) == "⏩":
                    current_page[0] = total_pages - 1
                await message.edit(embed=get_embed(current_page[0]))
                await message.remove_reaction(reaction.emoji, user)
            except asyncio.TimeoutError:
                await message.clear_reactions()
                break

    @commands.command(name="comandos", help="Lista todos os comandos disponíveis com paginação.")
    @no_dm()
    @maintenance_off()
    async def comandos(self, ctx):
        # Verifica se o usuário possui privilégios administrativos ou o cargo "MagoMLP"
        is_admin = ctx.author.guild_permissions.administrator or (discord.utils.get(ctx.author.roles, name="MagoMLP") is not None)
        
        comandos_gerais = []
        comandos_adm = []

        for command in self.bot.commands:
            if command.hidden:  # Ignora comandos ocultos
                continue

            # Se o comando possui uma verificação associada a "moderador", trata-o como admin
            if any("moderador" in str(check) for check in command.checks):
                if is_admin:
                    comandos_adm.append(f"**!!{command.name}**: {command.help}")
            else:
                comandos_gerais.append(f"**!!{command.name}**: {command.help}")

        # Exibe os comandos com paginação, mantendo a separação
        if not comandos_gerais and (not is_admin or not comandos_adm):
            await ctx.send(embed=discord.Embed(
                title="📜 Comandos Gerais",
                description="Nenhum comando disponível.",
                color=discord.Color.blue()
            ))
            return

        await self.paginate(ctx, comandos_gerais, comandos_adm if is_admin else [])

async def setup(bot):
    await bot.add_cog(Ajuda(bot))