# extras.py

import discord
from discord.ext import commands
import json
import os
import random
import time
import globals


class Extras(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="criador", help="Mensagem especial do criador para os fãs de My Little Pony.")
    async def criador(self, ctx):
        # Caminho da imagem local
        imagem_path = os.path.join("resources", "My_Little_Pony_Friendship_is_Magic_logo_2017.png")

        # Verifica se o arquivo existe
        if not os.path.exists(imagem_path):
            await ctx.send("🔴 Não consegui encontrar a imagem do logo. Verifique se ela está na pasta 'resources'.")
            return

        # Mensagem de agradecimento para os fãs de My Little Pony
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
        
        # Espaçamento antes da imagem para "ajustar" visualmente
        embed.add_field(name="\u200b", value="\u200b")  # Campo vazio

        # Envia a imagem local junto ao embed
        embed.set_image(url="attachment://My_Little_Pony_Friendship_is_Magic_logo_2017.png")
        embed.set_footer(text="Com carinho, Deyvid Pinto Maia 💖")
        
        # Envia o embed com a imagem local
        await ctx.send(
            embed=embed,
            file=discord.File(imagem_path, "My_Little_Pony_Friendship_is_Magic_logo_2017.png")
        )


    @commands.command(help="Envia uma mensagem carinhosa para o usuário.")
    async def amor(self, ctx):
        """Responde com uma mensagem carinhosa sorteada de um arquivo JSON."""

        mensagem = ""
        # Caminho do arquivo JSON
        caminho_arquivo = "resources/mensagens_carinhosas.json"
        
        # Criando o Embed para a mensagem carinhosa
        embed = discord.Embed(color=discord.Color.purple())  # Cor de fundo do embed

        # Verifica se o arquivo existe
        if os.path.exists(caminho_arquivo):
            # Abre o arquivo JSON e carrega os dados
            with open(caminho_arquivo, "r", encoding="utf-8") as f:
                dados = json.load(f)
            
            # Verifica se há mensagens no arquivo
            if "mensagens" in dados:
                # Sorteia uma mensagem carinhosa
                mensagem = random.choice(dados["mensagens"])  # Sorteia uma mensagem
                embed.add_field(name="Mensagem Carinhosa", value=mensagem, inline=False)
            else:
                embed.add_field(name="Erro", value="Ops! Não há mensagens carinhosas disponíveis no momento.", inline=False)
        else:
            embed.add_field(name="Erro", value="Erro: O arquivo de mensagens carinhosas não foi encontrado.", inline=False)

        # Verifica se a restrição de um salvamento por vez está habilitada
        if globals.restricao_usuario_unico:
            # Se a restrição estiver habilitada, verifica se o usuário foi o último a resgatar um personagem
            if globals.ultimo_usuario_salvador == ctx.author.id:
                embed.add_field(name="Aviso", value="❗ Você foi o Último a resgatar um personagem. Poderá resgatar novamente após alguém.", inline=False)
            else:
                # Envia a quantidade de tempo que falta para o usuário poder salvar
                tempo_restante = globals.tempo_impedimento - (time.time() - globals.ultimo_resgate_por_usuario.get(ctx.author.id, 0))
                if tempo_restante > 0:
                    minutos = int(tempo_restante // 60)
                    segundos = int(tempo_restante % 60)
                    embed.add_field(name="Tempo Restante", value=f"⏳ **{ctx.author.name}, você pode resgatar outro personagem em {minutos}m {segundos}s!**", inline=False)
                else:
                    embed.add_field(name="Resgate Liberado", value=f"✅ **{ctx.author.name}, você pode resgatar um personagem agora!**", inline=False)
        else:
            # Se a restrição estiver desabilitada, verifica o tempo de impedimento
            tempo_restante = globals.tempo_impedimento - (time.time() - globals.ultimo_resgate_por_usuario.get(ctx.author.id, 0))
            if tempo_restante > 0:
                minutos = int(tempo_restante // 60)
                segundos = int(tempo_restante % 60)
                embed.add_field(name="Tempo Restante", value=f"⏳ **{ctx.author.name}, você pode resgatar outro personagem em {minutos}m {segundos}s!**", inline=False)
            else:
                embed.add_field(name="Resgate Liberado", value=f"✅ **{ctx.author.name}, você pode resgatar um personagem agora!**", inline=False)

        # Envia o embed com as mensagens
        await ctx.send(embed=embed)



# Setup para registrar o cog
async def setup(bot):
    await bot.add_cog(Extras(bot))
