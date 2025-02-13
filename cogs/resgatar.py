import discord
from discord.ext import commands
import time
from server_data import carregar_dados_guild, salvar_dados_guild  # Certifique-se de que essas funções estão implementadas
from funcoes import verificar_imagem, sortear_naoencontrado  # Funções auxiliares para imagens
from PIL import Image
from io import BytesIO
import asyncio
import logging

# Configura o logger (pode ser ajustado conforme sua necessidade)
logger = logging.getLogger(__name__)

# Dicionário global de locks por guilda para evitar condições de corrida
guild_locks = {}

def get_guild_lock(guild_id: str) -> asyncio.Lock:
    if guild_id not in guild_locks:
        guild_locks[guild_id] = asyncio.Lock()
    return guild_locks[guild_id]

def redimensionar_imagem(caminho_imagem, novo_tamanho=(500, 500)):
    try:
        with Image.open(caminho_imagem) as img:
            img.thumbnail(novo_tamanho)
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format="PNG")
            img_byte_arr.seek(0)
            return img_byte_arr
    except Exception as e:
        logger.error(f"Erro ao redimensionar a imagem {caminho_imagem}: {e}")
        raise

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

        guild_id = str(ctx.guild.id)
        lock = get_guild_lock(guild_id)

        async with lock:
            # Carrega os dados da guilda de forma segura
            try:
                dados = carregar_dados_guild(guild_id)
            except Exception as e:
                logger.error(f"Erro ao carregar dados da guild {guild_id}: {e}")
                await ctx.send("❌ **Erro ao carregar os dados do servidor.**")
                return

            # Garante que as chaves necessárias existam
            if "ultimo_resgate_por_usuario" not in dados:
                dados["ultimo_resgate_por_usuario"] = {}
            if "ultimo_usuario_salvador" not in dados:
                dados["ultimo_usuario_salvador"] = None
            if "restricao_usuario_unico" not in dados:
                dados["restricao_usuario_unico"] = False

            tempo_bloqueio = dados.get("tempo_impedimento", 300)
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
            if not dados.get("personagens", []):
                embed = discord.Embed(
                    description="❌ **Todos os personagens já foram salvos!**",
                    color=discord.Color.red()
                )
                embed.set_image(url="attachment://fim.png")
                await ctx.send(embed=embed, file=discord.File(verificar_imagem("resources/fim.png")))
                return

            # Verifica a regra de restrição de usuário único
            if dados.get("restricao_usuario_unico", False) and dados.get("ultimo_usuario_salvador") == user_id:
                embed = discord.Embed(
                    description="❌ **Você foi o último a salvar um personagem. Espere que mais alguém salve outro personagem!**",
                    color=discord.Color.red()
                )
                embed.set_image(url="attachment://naoencontrado.gif")
                await ctx.send(embed=embed, file=discord.File(verificar_imagem("resources/naoencontrado.gif")))
                return

            # Verifica se o personagem já foi resgatado
            personagem_resgatado = next(
                (p for p in dados.get("personagens_salvos", []) if p["nome"].lower() == nome.lower()), None
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
                (p for p in dados.get("personagens", []) if p["nome"].lower() == nome.lower()), None
            )
            if personagem:
                # Remove da lista de disponíveis e adiciona à lista de salvos
                try:
                    dados["personagens"].remove(personagem)
                except ValueError as e:
                    logger.error(f"Erro ao remover personagem: {e}")
                    await ctx.send("❌ **Erro ao processar o personagem. Tente novamente.**")
                    return

                dados.setdefault("personagens_salvos", []).append(personagem)
                dados["ultimo_usuario_salvador"] = user_id
                dados["contador_personagens_salvos"][user_id] = dados.get("contador_personagens_salvos", {}).get(user_id, 0) + 1
                dados.setdefault("personagens_por_usuario", {}).setdefault(user_id, []).append(personagem)
                dados["ultimo_resgate_por_usuario"][user_id] = agora

                # Processa a imagem do personagem com tratamento de exceção
                imagem_path = f"resources/poneis/{personagem['nome']}.png"
                try:
                    imagem = verificar_imagem(imagem_path)
                    imagem_redimensionada = redimensionar_imagem(imagem)
                except Exception as e:
                    logger.error(f"Erro ao processar imagem para {personagem['nome']}: {e}")
                    await ctx.send("❌ **Erro ao processar a imagem do personagem.**")
                    return

                nome_imagem = personagem['nome'].replace(" ", "_").lower()

                embed = discord.Embed(
                    title=f"✅ **'{personagem['nome']}' foi salvo!**",
                    description=f"**{ctx.author.name}** resgatou o personagem '{personagem['nome']}' com sucesso!",
                    color=discord.Color.green()
                )
                embed.set_image(url=f"attachment://{nome_imagem}.png")
                try:
                    await ctx.send(embed=embed, file=discord.File(imagem_redimensionada, f"{nome_imagem}.png"))
                except Exception as e:
                    logger.error(f"Erro ao enviar mensagem para {personagem['nome']}: {e}")
                    await ctx.send("❌ **Erro ao enviar a mensagem de sucesso.**")
                    return

                # Se este for o último personagem disponível, envia uma mensagem especial
                if not dados.get("personagens"):
                    embed_final = discord.Embed(
                        description=f"🎉 **'{personagem['nome']}' foi o último personagem salvo! Todos estão seguros agora!** 🎉",
                        color=discord.Color.gold()
                    )
                    embed_final.set_image(url="attachment://fim.png")
                    try:
                        await ctx.send(embed=embed_final, file=discord.File(verificar_imagem("resources/fim.png")))
                    except Exception as e:
                        logger.error(f"Erro ao enviar mensagem final: {e}")

                # Salva os dados atualizados para este servidor
                try:
                    salvar_dados_guild(guild_id, dados)
                except Exception as e:
                    logger.error(f"Erro ao salvar dados da guild {guild_id}: {e}")
                    await ctx.send("❌ **Erro ao salvar os dados do servidor.**")
                    return
            else:
                embed = discord.Embed(
                    description=f"❌ **O personagem '{nome}' não foi encontrado!**",
                    color=discord.Color.red()
                )
                embed.set_image(url="attachment://naoencontrado.gif")
                try:
                    await ctx.send(embed=embed, file=discord.File(sortear_naoencontrado()))
                except Exception as e:
                    logger.error(f"Erro ao enviar mensagem de personagem não encontrado: {e}")
                    await ctx.send("❌ **Erro ao enviar mensagem de personagem não encontrado.**")
                    return

# Setup para registrar o cog
async def setup(bot):
    await bot.add_cog(Resgatar(bot))
