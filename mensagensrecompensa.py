# mensagensrecompensa.py 21/03/2025 23:30 (atualizado para mensagens por alinhamento, incluindo 0, e embeds)

import discord
import random
import asyncio
import time
import math
import json
import os
from server_data import carregar_dados_guild, salvar_dados_guild, carregar_estatisticas_guild, salvar_estatisticas_seguro, carregar_estatisticas_usuario, salvar_estatisticas_seguro_usuario

# Funções auxiliares para conquistas
def carregar_conquistas():
    path = "resources/conquistas.json"
    if not os.path.exists(path):
        return {"conquistas": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def carregar_conquistas_usuarios(guild_id):
    path = f"resources/servidores/{guild_id}_conquistas_usuarios.json"
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# Mensagens por nível de alinhamento
MENSAGENS_ALINHAMENTO = {
    0: [
        "🎉 **A amizade nos conecta!** {personagem} te agradece por fazer parte disso!",
        "🌟 **Um momento especial!** {personagem} está feliz por estar com você!",
        "💌 **Obrigado por tudo!** {personagem} te dá um sorriso caloroso!",
        "🌈 **Juntos é melhor!** {personagem} celebra sua companhia!",
        "✨ **Um amigo é um tesouro!** {personagem} te saúda com alegria!"
    ],
    1: [
        "🌟 **A luz da bondade brilha forte!** {personagem} está orgulhoso de fazer parte da sua jornada!",
        "✨ **Um coração puro nunca falha!** {personagem} agradece sua amizade verdadeira!",
        "🌈 **A harmonia guia seus passos!** {personagem} celebra sua bondade infinita!",
        "💖 **A esperança vive em você!** {personagem} te presenteia com gratidão sincera!",
        "🌼 **A amizade é sua força!** {personagem} te honra com um sorriso radiante!"
    ],
    2: [
        "⚡ **A coragem ilumina o caminho!** {personagem} reconhece seu espírito heroico!",
        "🛡️ **Um verdadeiro defensor!** {personagem} está ao seu lado com orgulho!",
        "🌟 **Sua bondade inspira!** {personagem} te agradece por nunca desistir!",
        "💪 **A força do bem prevalece!** {personagem} te dá um salve de gratidão!",
        "🎉 **Um herói entre nós!** {personagem} comemora sua dedicação!"
    ],
    3: [
        "🔥 **Mesmo com falhas, você brilha!** {personagem} valoriza sua determinação!",
        "🌠 **Um herói em construção!** {personagem} te agradece por tentar sempre!",
        "⚔️ **A luta te define!** {personagem} reconhece seu esforço constante!",
        "💡 **A bondade guia suas escolhas!** {personagem} te dá um aceno de apoio!",
        "🏆 **Cada passo conta!** {personagem} celebra sua jornada imperfeita!"
    ],
    4: [
        "🎈 **A amizade é seu dom!** {personagem} te agradece por estar por perto!",
        "🌻 **Um coração gentil!** {personagem} sorri com sua companhia leal!",
        "🎁 **Você faz a diferença!** {personagem} te presenteia com carinho!",
        "🌞 **Dias melhores com você!** {personagem} aprecia suas boas intenções!",
        "🍎 **Simples e verdadeiro!** {personagem} te dá um abraço de gratidão!"
    ],
    5: [
        "☁️ **Equilíbrio é sua marca!** {personagem} te agradece por ser quem é!",
        "🌙 **Um amigo confiável!** {personagem} valoriza sua presença constante!",
        "⚖️ **Nem herói, nem vilão!** {personagem} te dá um aceno respeitoso!",
        "🌿 **A calma te guia!** {personagem} aprecia sua natureza tranquila!",
        "🔔 **Sempre no meio-termo!** {personagem} te oferece um gesto amigável!"
    ],
    6: [
        "🌫️ **Mistério te envolve!** {personagem} te observa com um sorriso esperto!",
        "🌓 **Luz e sombra dançam!** {personagem} te agradece de um jeito peculiar!",
        "🔮 **Quem sabe o que pensa?** {personagem} te dá um olhar intrigante!",
        "🎭 **Duas faces, um coração!** {personagem} reconhece sua complexidade!",
        "🕊️ **Nem bom, nem mau!** {personagem} te saúda com curiosidade!"
    ],
    7: [
        "💰 **Um truque bem jogado!** {personagem} te agradece com um riso esperto!",
        "🃏 **A malícia tem seu charme!** {personagem} pisca com cumplicidade!",
        "🔧 **Você conserta seus erros!** {personagem} te dá um tapinha nas costas!",
        "🎲 **Um jogo arriskado!** {personagem} aprecia sua audácia redimível!",
        "🕸️ **Trapaças com coração!** {personagem} te oferece um aceno travesso!"
    ],
    8: [
        "🌋 **O caos te chama!** {personagem} te agradece com um brilho sombrio!",
        "🖤 **Um vilão com potencial!** {personagem} sorri com um toque de redenção!",
        "⚡ **A escuridão não é tudo!** {personagem} te dá um olhar desafiador!",
        "🔥 **Fogo que pode mudar!** {personagem} reconhece sua chama oculta!",
        "🌩️ **Tempestades com esperança!** {personagem} te saúda com respeito!"
    ],
    9: [
        "💥 **O caos é sua arte!** {personagem} te parabeniza com um riso maligno!",
        "👑 **Mestre da discórdia!** {personagem} te oferece um brinde sombrio!",
        "🌑 **A sombra te define!** {personagem} te saúda com frieza calculada!",
        "🗡️ **Sem remorso, só poder!** {personagem} te dá um aceno cruel!",
        "⚙️ **Vilania em seu auge!** {personagem} te encara com admiração gélida!"
    ],
    10: [
        "🔥 **A destruição é sua essência!** {personagem} te glorifica com terror!",
        "💀 **O mal absoluto reina!** {personagem} te saúda com um riso macabro!",
        "🌌 **Nenhuma luz escapa!** {personagem} te celebra como um pesadelo vivo!",
        "🩸 **O horror te abraça!** {personagem} te oferece um brinde sangrento!",
        "☄️ **Fim de tudo em você!** {personagem} te exalta com frieza eterna!"
    ]
}


def get_primeira_cor(cor_string):
    """Extrai a primeira cor de uma string no formato '#XXXXXX/#YYYYYY' ou '#XXXXXX'."""
    if "/" in cor_string:
        return cor_string.split("/")[0].strip()
    return cor_string.strip()

async def enviar_recompensa_automatico(bot, guild_id):
    while True:
        dados = carregar_dados_guild(guild_id)
        tempo_recompensa = dados.get("tempo_recompensa", 3600)
        await asyncio.sleep(tempo_recompensa + random.randint(0, int(tempo_recompensa / 8)))
        
        dados = carregar_dados_guild(guild_id)
        
        estatisticas_bot = carregar_estatisticas_guild(guild_id)
        bot_default = {
            "recompensas_enviadas": 0
        }
        if "ponymemories" not in estatisticas_bot:
            estatisticas_bot["ponymemories"] = bot_default
        else:
            estatisticas_bot["ponymemories"] = {**bot_default, **estatisticas_bot["ponymemories"]}
        estatisticas_bot.setdefault("estatisticas_meus_personagens", {})
        
        personagens_salvos = dados.get("personagens_salvos", [])
        personagens_por_usuario = dados.get("personagens_por_usuario", {})
        if not personagens_salvos or not personagens_por_usuario:
            await salvar_estatisticas_seguro(guild_id, estatisticas_bot)
            continue
        
        personagem = random.choice(personagens_salvos)
        personagem_nome = personagem["nome"]
        
        dono_id = None
        for user_id, lista in personagens_por_usuario.items():
            for p in lista:
                if p["nome"].lower() == personagem_nome.lower():
                    dono_id = str(user_id)
                    break
            if dono_id:
                break
        if not dono_id:
            await salvar_estatisticas_seguro(guild_id, estatisticas_bot)
            continue
        
        estatisticas_usuario = carregar_estatisticas_usuario(guild_id, dono_id)
        usuario_default = {
            "uso_comando_recompensa": 0
        }
        if "recompensa" not in estatisticas_usuario:
            estatisticas_usuario["recompensa"] = usuario_default
        else:
            estatisticas_usuario["recompensa"] = {**usuario_default, **estatisticas_usuario["recompensa"]}
        estatisticas_usuario.setdefault("estatisticas_meus_personagens", {})
        
        n = len(personagens_por_usuario.get(dono_id, []))
        half = math.ceil(n / 2)
        if half > 30:
            recompensa_base = 1
        else:
            recompensa_base = 30 // half
            if recompensa_base < 1:
                recompensa_base = 1

        usuarios = dados.setdefault("usuarios", {})
        user_data = usuarios.setdefault(dono_id, {"coracao": 0, "quantidade_amor": 0})
        user_data["coracao"] = int(user_data.get("coracao", 0))
        
        total_recompensa = recompensa_base
        
        conquistas_usuario = carregar_conquistas_usuarios(guild_id)
        user_conquistas = conquistas_usuario.get(dono_id, [])
        conquistas_def = carregar_conquistas().get("conquistas", [])
        conquistas_dict = {c["id"].lower(): c for c in conquistas_def}
        
        extra_bonus = 0
        for cid in user_conquistas:
            conq = conquistas_dict.get(cid.lower())
            if conq:
                for cond in conq.get("condicoes", []):
                    if cond.get("tipo") == "incluir":
                        if cond.get("personagem", "").lower() == personagem_nome.lower():
                            extra_bonus += 2
                            break
        total_recompensa += extra_bonus
        
        user_data["coracao"] += total_recompensa
        usuarios[dono_id] = user_data
        dados["usuarios"] = usuarios
        salvar_dados_guild(guild_id, dados)
        
        guild = bot.get_guild(int(guild_id))
        canal = None
        canal_id = dados.get("ID_DO_CANAL_RECOMPENSA")
        if canal_id:
            try:
                canal = guild.get_channel(int(canal_id))
            except Exception:
                canal = None
        if not canal:
            canal = guild.system_channel
        if not canal:
            for ch in guild.text_channels:
                if ch.permissions_for(guild.me).send_messages:
                    canal = ch
                    break
        if not canal:
            await salvar_estatisticas_seguro(guild_id, estatisticas_bot)
            await salvar_estatisticas_seguro_usuario(guild_id, dono_id, estatisticas_usuario)
            continue
        
        estatisticas_bot["ponymemories"]["recompensas_enviadas"] += 1
        personagem_stats_bot = estatisticas_bot["estatisticas_meus_personagens"].setdefault(personagem_nome, {
            "resgatado": 0,
            "sorteado_para_recompensa": 0,
            "coracoes_concedidos_recompensa": 0
        })
        personagem_stats_bot["sorteado_para_recompensa"] += 1
        personagem_stats_bot["coracoes_concedidos_recompensa"] += total_recompensa
        
        personagem_stats_usuario = estatisticas_usuario["estatisticas_meus_personagens"].setdefault(personagem_nome, {
            "resgatado": 0,
            "enviado": 0,
            "recebido": 0,
            "exibido": 0,
            "uso_como_changeling_conquista": 0,
            "sorteado_para_recompensa": 0,
            "coracoes_concedidos_recompensa": 0
        })
        personagem_stats_usuario["sorteado_para_recompensa"] = personagem_stats_usuario.get("sorteado_para_recompensa", 0) + 1
        personagem_stats_usuario["coracoes_concedidos_recompensa"] = personagem_stats_usuario.get("coracoes_concedidos_recompensa", 0) + total_recompensa
        
        # Correção: Converte alinhamento para inteiro
        alinhamento = int(personagem.get("alinhamento", 0))
        mensagem_base = random.choice(MENSAGENS_ALINHAMENTO[alinhamento])
        mensagem = mensagem_base.format(personagem=personagem_nome)
        
        # Obtém a primeira cor do campo "cor"
        cor_string = personagem.get("cor", "#800080")  # Roxo padrão caso não haja cor
        primeira_cor = get_primeira_cor(cor_string)
        try:
            cor_embed = discord.Color.from_str(primeira_cor)
        except ValueError:
            cor_embed = discord.Color.purple()  # Fallback para roxo se a cor for inválida
        
        # Cria o embed com a cor do personagem
        embed = discord.Embed(
            title="Recompensa da Amizade",
            description=f"{mensagem}\n\n"
                        f"Você recebeu **{recompensa_base}** coração(ões) "
                        f"**+{extra_bonus}** por conquistas com o personagem.\n"
                        f"**Total: {total_recompensa} ❤️**",
            color=cor_embed  # Usa a primeira cor do personagem
        )
        embed.set_footer(text="Que a magia da amizade continue!")

        await salvar_estatisticas_seguro(guild_id, estatisticas_bot)
        await salvar_estatisticas_seguro_usuario(guild_id, dono_id, estatisticas_usuario)
        
        await canal.send(embed=embed)
        