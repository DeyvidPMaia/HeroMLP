import discord
from discord.ext import commands
import json
import os
import random
import time
from server_data import carregar_dados_guild

class Extras(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="criador", help="Mensagem especial do criador para os fãs de My Little Pony.")
    async def criador(self, ctx):
        imagem_path = os.path.join("resources", "My_Little_Pony_Friendship_is_Magic_logo_2017.png")
        
        if not os.path.exists(imagem_path):
            await ctx.send("🔴 Não consegui encontrar a imagem do logo. Verifique se ela está na pasta 'resources'.")
            return
        
        mensagem = """
        🦄 **Saudações, fãs de My Little Pony!** 🦄

        Eu, **o criador deste bot**, queria dedicar um momento para expressar o quanto sou grato por todos vocês, 
        amantes da magia e amizade que MLP nos ensina! 

        💖 A amizade é mágica, e por isso que estamos aqui, criando um espaço onde podemos compartilhar essa magia 
        através de personagens incríveis e histórias emocionantes. 🏰✨
        Que todos nós continuemos a espalhar bondade e alegria, e que o amor sempre nos inspire! 🌈

        **Lembre-se:** Quando as amizades se unem, a magia não há limites! 🌟
        """
        
        embed = discord.Embed(
            title="🦄 Mensagem Especial do Criador 🦄",
            description=mensagem,
            color=discord.Color.purple()
        )
        
        embed.add_field(name="\u200b", value="\u200b")  # Espaço visual antes da imagem
        embed.set_image(url="attachment://My_Little_Pony_Friendship_is_Magic_logo_2017.png")
        embed.set_footer(text="Com carinho, Deyvid Pinto Maia 💖")
        
        await ctx.send(
            embed=embed,
            file=discord.File(imagem_path, "My_Little_Pony_Friendship_is_Magic_logo_2017.png")
        )

    @commands.command(help="Envia uma mensagem carinhosa para o usuário.")
    async def amor(self, ctx):
        # Carregar dados específicos da guilda
        dados_guild = carregar_dados_guild(ctx.guild.id)
        
        if dados_guild is None:
            embed = discord.Embed(color=discord.Color.red())
            embed.add_field(name="Erro", value="Não foi possível carregar os dados da guilda.", inline=False)
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(color=discord.Color.purple())

        caminho_arquivo = "resources/mensagens_carinhosas.json"
        
        # Carregar as mensagens carinhosas do arquivo JSON
        if os.path.exists(caminho_arquivo):
            with open(caminho_arquivo, "r", encoding="utf-8") as f:
                dados = json.load(f)
            
            if "mensagens" in dados:
                mensagem = random.choice(dados["mensagens"])
                embed.add_field(name="Mensagem Carinhosa", value=mensagem, inline=False)
            else:
                embed.add_field(name="Erro", value="Ops! Não há mensagens carinhosas disponíveis no momento.", inline=False)
        else:
            embed.add_field(name="Erro", value="Erro: O arquivo de mensagens carinhosas não foi encontrado.", inline=False)

        # Verificar a restrição de resgate com base nos dados carregados
        restricao_usuario_unico = dados_guild.get("restricao_usuario_unico", False)
        ultimo_usuario_salvador = dados_guild.get("ultimo_usuario_salvador", None)
        tempo_impedimento = dados_guild.get("tempo_impedimento", 3600)  # 1 hora de exemplo
        ultimo_resgate_por_usuario = dados_guild.get("ultimo_resgate_por_usuario", {})

        # Verificação de resgates com restrição
        if restricao_usuario_unico == True:
            if ultimo_usuario_salvador == str(ctx.author.id):
                embed.add_field(name="Aviso", value="❗ Você foi o último a resgatar um personagem. Poderá resgatar novamente após alguém.", inline=False)
            else:
                # Verificar o tempo restante para o usuário resgatar outro personagem
                tempo_restante = tempo_impedimento - (time.time() - ultimo_resgate_por_usuario.get(str(ctx.author.id), 0))
                if tempo_restante > 0:
                    minutos = int(tempo_restante // 60)
                    segundos = int(tempo_restante % 60)
                    embed.add_field(name="Tempo Restante", value=f"⏳ **{ctx.author.name}, você pode resgatar outro personagem em {minutos}m {segundos}s!**", inline=False)
                else:
                    # Resgate liberado
                    embed.add_field(name="Resgate Liberado", value=f"✅ **{ctx.author.name}, você pode resgatar um personagem agora!**", inline=False)
        else:
            # Se a restrição não estiver ativada, sempre permite o resgate, mas verifica o tempo de espera
            tempo_restante = tempo_impedimento - (time.time() - ultimo_resgate_por_usuario.get(str(ctx.author.id), 0))
            if tempo_restante > 0:
                minutos = int(tempo_restante // 60)
                segundos = int(tempo_restante % 60)
                embed.add_field(name="Tempo Restante", value=f"⏳ **{ctx.author.name}, você pode resgatar outro personagem em {minutos}m {segundos}s!**", inline=False)
            else:
                embed.add_field(name="Resgate Liberado", value=f"✅ **{ctx.author.name}, você está podendo resgatar personagens agora!**", inline=False)

        # Enviar o embed com a mensagem carinhosa e informações sobre o resgate
        await ctx.send(embed=embed)

# Setup para registrar o cog
async def setup(bot):
    await bot.add_cog(Extras(bot))
