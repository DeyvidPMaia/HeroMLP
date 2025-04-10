# extras.py 21/03/2025 01:00 (atualizado para nova estrutura de estatísticas, changelings no formato dicionário e Lightly Unicorn)

import discord
from discord.ext import commands
import json
import os
import random
import time
import asyncio
from server_data import carregar_dados_guild, salvar_dados_guild, carregar_estatisticas_usuario, salvar_estatisticas_seguro_usuario, require_resgate
from funcoes import maintenance_off, no_dm

class Extras(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lock = asyncio.Lock()  # Lock para evitar race conditions

    @commands.command(help="Envia uma mensagem carinhosa para o usuário.")
    @maintenance_off()
    @no_dm()
    @require_resgate
    async def amor(self, ctx):
        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)

        async with self.lock:  # Usa o lock para proteger acesso concorrente
            # Carrega os dados específicos da guilda
            dados_guild = carregar_dados_guild(guild_id)
            if dados_guild is None:
                embed = discord.Embed(color=discord.Color.red())
                embed.add_field(name="Erro", value="Não foi possível carregar os dados da guilda.", inline=False)
                await ctx.send(embed=embed)
                return

            # Carrega e inicializa estatísticas do usuário para o comando "amor"
            estatisticas = carregar_estatisticas_usuario(guild_id, user_id)
            estatisticas.setdefault("amor", {
                "uso_comando_amor": 0,
                "erros_carregamento_mensagens": 0,
                "coracoes_ganhos_amor": 0,
                "recompensado_comando_amor": 0,
                "uso_amor_em_cooldown": 0,
                "uso_amor_bloqueio_ultimo_salvador": 0
            })
            estatisticas["amor"]["uso_comando_amor"] += 1

            embed = discord.Embed(color=discord.Color.purple())
            caminho_arquivo = "resources/mensagens_carinhosas.json"
            
            # Verifica se o usuário possui "Lightly Unicorn"
            personagens_usuario = dados_guild.get("personagens_por_usuario", {}).get(user_id, [])
            possui_lightly_unicorn = any(p["nome"] == "Lightly Unicorn" for p in personagens_usuario)
            titulo = "Mensagem Carinhosa 🦄" if possui_lightly_unicorn else "Mensagem Carinhosa"
            
            # Carrega as mensagens carinhosas do arquivo JSON com tratamento de erro
            try:
                if os.path.exists(caminho_arquivo):
                    with open(caminho_arquivo, "r", encoding="utf-8") as f:
                        dados_mensagens = json.load(f)
                    if "mensagens" in dados_mensagens:
                        mensagem = random.choice(dados_mensagens["mensagens"])
                        embed.add_field(name=titulo, value=mensagem, inline=False)
                    else:
                        embed.add_field(name="Erro", value="Ops! Não há mensagens carinhosas disponíveis no momento.", inline=False)
                        estatisticas["amor"]["erros_carregamento_mensagens"] += 1
                else:
                    embed.add_field(name="Erro", value="Erro: O arquivo de mensagens carinhosas não foi encontrado.", inline=False)
                    estatisticas["amor"]["erros_carregamento_mensagens"] += 1
            except json.JSONDecodeError as e:
                embed.add_field(name="Erro", value=f"Erro ao ler o arquivo de mensagens: {e}", inline=False)
                estatisticas["amor"]["erros_carregamento_mensagens"] += 1

            # Atualiza os dados do usuário com inicialização completa
            usuarios = dados_guild.setdefault("usuarios", {})
            user_data = usuarios.setdefault(user_id, {
                "coracao": 0,
                "quantidade_amor": 0,
                "trevo": 0,
                "changeling": [],
                "quantidade_recompensa": 0,
                "ultimo_reset_recompensa": 0
            })

            # Incrementa a quantidade de amor e gerencia recompensa (sem reset aqui)
            user_data["quantidade_amor"] += 1
            if user_data["quantidade_amor"] == 4:
                user_data["coracao"] += 5
                estatisticas["amor"]["recompensado_comando_amor"] += 1
                estatisticas["amor"]["coracoes_ganhos_amor"] += 5
                await ctx.send(f"💕 **{ctx.author.mention}, obrigado por espalhar seu amor. Você recebeu 5 corações!**")

            # Exibição dos corações
            heart_field = f"❤️ {user_data['coracao']}"
            
            # Exibição dos trevos
            trevo_count = user_data.get("trevo", 0)
            max_trevos = 3
            filled_trevos = "🍀 " * trevo_count
            empty_trevos = "⚪ " * (max_trevos - trevo_count) if trevo_count < max_trevos else ""
            trevos_display = filled_trevos + empty_trevos

            # Exibição dos changelings (corrigido para formato dicionário)
            changelings = user_data.get("changeling", [])
            total_changelings = len(changelings)
            transformed_changelings = sum(1 for c in changelings if isinstance(c, dict) and c["nome"].startswith("cha") and not c["nome"][3:].isdigit())
            changelings_display = f"{total_changelings}/{transformed_changelings}"

            # Total de personagens do usuário
            personagens = dados_guild.get("personagens_por_usuario", {}).get(user_id, [])
            total_personagens = len(personagens)

            # Formata a mensagem em uma única linha
            linha_info = (f"**Corações:** {user_data['coracao']} | **Trevos:** {trevos_display} | "
                          f"**Changelings:** {changelings_display} | **Personagens:** {total_personagens}")
            embed.add_field(name="", value=linha_info, inline=False)

            # Verifica a restrição de resgate
            restricao_usuario_unico = dados_guild.get("restricao_usuario_unico", False)
            ultimo_usuario_salvador = dados_guild.get("ultimo_usuario_salvador", None)
            tempo_impedimento = max(dados_guild.get("tempo_impedimento", 3600), 60)  # Mínimo de 60 segundos
            ultimo_resgate_por_usuario = dados_guild.get("ultimo_resgate_por_usuario", {})

            tempo_restante = tempo_impedimento - (time.time() - ultimo_resgate_por_usuario.get(user_id, 0))
            if restricao_usuario_unico and ultimo_usuario_salvador == user_id:
                estatisticas["amor"]["uso_amor_bloqueio_ultimo_salvador"] += 1
                embed.add_field(name="Aviso", value="❗ Você foi o último a resgatar um personagem. Poderá resgatar novamente após alguém.", inline=False)
            elif tempo_restante > 0:
                estatisticas["amor"]["uso_amor_em_cooldown"] += 1
                minutos = int(tempo_restante // 60)
                segundos = int(tempo_restante % 60)
                embed.add_field(name="Tempo Restante", value=f"⏳ **{ctx.author.name}, você pode resgatar outro personagem em {minutos}m {segundos}s!**", inline=False)
            else:
                embed.add_field(name="Resgate Liberado", value=f"✅ **{ctx.author.name}, você está podendo resgatar personagens agora!**", inline=False)

            # Adiciona a quantidade de personagens escondidos no rodapé
            personagens_escondidos = len(dados_guild.get("personagem_escondido", []))
            embed.set_footer(text=f"Personagens escondidos: {personagens_escondidos}")

            # Salva as alterações nos dados da guilda
            salvar_dados_guild(guild_id, dados_guild)
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)
        
        # Envia o embed (fora do lock para não bloquear a resposta)
        await ctx.send(embed=embed)


    @commands.command(name="criador", help="Mensagem especial do criador para os fãs de My Little Pony.")
    @maintenance_off()
    async def criador(self, ctx):
        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)

        # Carrega e inicializa estatísticas do usuário para o comando "criador"
        estatisticas = carregar_estatisticas_usuario(guild_id, user_id)
        estatisticas.setdefault("criador", {
            "uso_comando_criador": 0,
            "erros_imagem_criador": 0
        })
        estatisticas["criador"]["uso_comando_criador"] += 1

        imagem_path = os.path.join("resources", "My_Little_Pony_Friendship_is_Magic_logo_2017.png")
        
        if not os.path.exists(imagem_path):
            estatisticas["criador"]["erros_imagem_criador"] += 1
            await ctx.send("🔴 Não consegui encontrar a imagem do logo. Verifique se ela está na pasta 'resources'.")
            await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)
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
        await salvar_estatisticas_seguro_usuario(guild_id, user_id, estatisticas)

async def setup(bot):
    await bot.add_cog(Extras(bot))