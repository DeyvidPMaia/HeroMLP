# resgatar.py

import discord
from discord.ext import commands
import time
from server_data import carregar_dados_guild, salvar_dados_guild  # Certifique-se de que essas funções estão implementadas
from funcoes import verificar_imagem, sortear_naoencontrado  # Funções auxiliares para imagens
from PIL import Image
from io import BytesIO

def redimensionar_imagem(caminho_imagem, novo_tamanho=(500, 500)):
    with Image.open(caminho_imagem) as img:
        img.thumbnail(novo_tamanho)
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)
        return img_byte_arr

class Resgatar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="r", help="Salva um personagem desaparecido.")
    async def resgatar(self, ctx, *, nome):
        nome = nome.strip()
        if not nome:
            embed = discord.Embed(
                description="❌ **Por favor, insira o nome de um personagem para salvar.**",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Obtém o ID da guilda e carrega os dados específicos deste servidor
        guild_id = str(ctx.guild.id)
        dados = carregar_dados_guild(guild_id)

        # Garante que as chaves adicionais estejam presentes
        if "ultimo_resgate_por_usuario" not in dados:
            dados["ultimo_resgate_por_usuario"] = {}
        if "ultimo_usuario_salvador" not in dados:
            dados["ultimo_usuario_salvador"] = None
        if "restricao_usuario_unico" not in dados:
            dados["restricao_usuario_unico"] = False

        # Define o tempo de bloqueio (impedimento) conforme configuração global
        tempo_bloqueio = dados["tempo_impedimento"]
        agora = time.time()
        user_id = str(ctx.author.id)

        # Verifica se o usuário já resgatou recentemente
        if user_id in dados["ultimo_resgate_por_usuario"]:
            tempo_passado = agora - dados["ultimo_resgate_por_usuario"][user_id]
            if tempo_passado < tempo_bloqueio:
                tempo_restante = int(tempo_bloqueio - tempo_passado)
                minutos = tempo_restante // 60
                segundos = tempo_restante % 60
                embed = discord.Embed(
                    description=f"❌ **Você deve esperar {minutos} minuto(s) e {segundos} segundo(s) para resgatar outro personagem.**",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

        # Verifica se não há mais personagens disponíveis
        if not dados["personagens"]:
            embed = discord.Embed(
                description="❌ **Todos os personagens já foram salvos!**",
                color=discord.Color.red()
            )
            embed.set_image(url="attachment://fim.png")
            await ctx.send(embed=embed, file=discord.File(verificar_imagem("resources/fim.png")))
            return

        # Verifica a regra de restrição de usuário único
        if dados["restricao_usuario_unico"] and dados["ultimo_usuario_salvador"] == user_id:
            embed = discord.Embed(
                description="❌ **Você foi o último a salvar um personagem. Espere que mais alguém salve outro personagem!**",
                color=discord.Color.red()
            )
            embed.set_image(url="attachment://naoencontrado.gif")
            await ctx.send(embed=embed, file=discord.File(verificar_imagem("resources/naoencontrado.gif")))
            return

        # Verifica se o personagem já foi resgatado
        personagem_resgatado = next(
            (p for p in dados["personagens_salvos"] if p["nome"].lower() == nome.lower()), None
        )
        if personagem_resgatado:
            embed = discord.Embed(
                description=f"❌ **O personagem '{nome}' já foi resgatado!**",
                color=discord.Color.red()
            )
            embed.set_image(url="attachment://nao.gif")
            await ctx.send(embed=embed, file=discord.File(verificar_imagem("resources/nao.gif")))
            return

        # Procura o personagem na lista de disponíveis
        personagem = next(
            (p for p in dados["personagens"] if p["nome"].lower() == nome.lower()), None
        )
        if personagem:
            # Remove da lista de disponíveis e adiciona à lista de salvos
            dados["personagens"].remove(personagem)
            dados["personagens_salvos"].append(personagem)
            dados["ultimo_usuario_salvador"] = user_id

            # Atualiza o contador para o usuário
            dados["contador_personagens_salvos"][user_id] = dados["contador_personagens_salvos"].get(user_id, 0) + 1

            # Registra o personagem no dicionário de personagens por usuário
            if user_id not in dados["personagens_por_usuario"]:
                dados["personagens_por_usuario"][user_id] = []
            dados["personagens_por_usuario"][user_id].append(personagem)

            # Atualiza o timestamp do último resgate do usuário
            dados["ultimo_resgate_por_usuario"][user_id] = agora

            # Prepara o embed com mensagem de sucesso e imagem do personagem
            imagem = verificar_imagem(f"resources/poneis/{personagem['nome']}.png")
            imagem_redimensionada = redimensionar_imagem(imagem)
            nome_imagem = personagem['nome'].replace(" ", "_").lower()

            embed = discord.Embed(
                title=f"✅ **'{personagem['nome']}' foi salvo!**",
                description=f"**{ctx.author.name}** resgatou o personagem '{personagem['nome']}' com sucesso!",
                color=discord.Color.green()
            )
            embed.set_image(url=f"attachment://{nome_imagem}.png")

            await ctx.send(embed=embed, file=discord.File(imagem_redimensionada, f"{nome_imagem}.png"))
            
            # Se este for o último personagem disponível, envia uma mensagem especial
            if not dados["personagens"]:
                embed = discord.Embed(
                    description=f"🎉 **'{personagem['nome']}' foi o último personagem salvo! Todos estão seguros agora!** 🎉",
                    color=discord.Color.gold()
                )
                embed.set_image(url="attachment://fim.png")
                await ctx.send(embed=embed, file=discord.File(verificar_imagem("resources/fim.png")))
            
            # Salva os dados atualizados para este servidor
            salvar_dados_guild(guild_id, dados)
        else:
            embed = discord.Embed(
                description=f"❌ **O personagem '{nome}' não foi encontrado!**",
                color=discord.Color.red()
            )
            embed.set_image(url="attachment://naoencontrado.gif")
            await ctx.send(embed=embed, file=discord.File(sortear_naoencontrado()))

# Setup para registrar o cog
async def setup(bot):
    await bot.add_cog(Resgatar(bot))
