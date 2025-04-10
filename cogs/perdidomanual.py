#perdido_manual


import discord
from discord.ext import commands
from utils import personagem_perdido
from funcoes import apenas_moderador, maintenance_off, no_dm


class PerdidoManual(commands.Cog):
    def init(self, bot):
        self.bot = bot


    @commands.command(name="perdido_manual", help="Executa manualmente o evento de personagem perdido com a quantidade especificada.")
    @no_dm()
    @maintenance_off()
    @apenas_moderador()
    async def perdido_manual(self, ctx, quantidade: int):
        """Comando para executar manualmente o evento de personagem perdido."""
        guild = ctx.guild
        guild_id = str(guild.id)

        if quantidade <= 0:
            await ctx.send("❌ **A quantidade deve ser um número positivo.**")
            return

        try:
            # Chama a função personagem_perdido com "perdido_manual" como chamado_por
            embeds = await personagem_perdido(guild, "perdido_manual", quantidade=quantidade, usar_trevo=False, dm=True, cor_chamado=discord.Colour.blue())
            
            if embeds is None:
                await ctx.send("❌ **Erro ao processar o evento de personagem perdido. Verifique os logs para mais detalhes.**")
            else:
                if isinstance(embeds, list):
                    for emb in embeds:
                        await ctx.send(embed=emb)
                else:
                    await ctx.send(embed=embeds)
        
        except Exception as e:
            print(f"Erro inesperado no comando perdido_manual para guild {guild_id}: {e}")
            await ctx.send("⚠️ **Ocorreu um erro inesperado ao executar o comando. Tente novamente mais tarde.**")

async def setup(bot):
    await bot.add_cog(PerdidoManual(bot))

