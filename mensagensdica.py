import random
import asyncio
import json
import globals  # Usado como fallback para valores padrão
from server_data import carregar_dados_guild  # Certifique-se de que essa função está implementada

async def enviar_dica_personagem(bot, guild_id):
    """
    Aguarda um intervalo especificado no JSON de dados do servidor e, 
    em seguida, envia uma dica de personagem no canal configurado para dicas naquele servidor.
    Se o canal não estiver configurado ou não for encontrado, a dica não é enviada.
    """
    while True:
        # Carrega os dados específicos do servidor
        dados = carregar_dados_guild(guild_id)
        # Obtém o intervalo de dicas do JSON ou usa o valor padrão em globals
        intervalo = dados.get("intervalo_dica_personagem", globals.intervalo_dica_personagem)
        await asyncio.sleep(intervalo)
        try:
            canal_id = dados.get("ID_DO_CANAL_DICAS")
            if canal_id is None:
                print(f"[DICA] Canal para dicas não configurado para a guild {guild_id}.")
                continue

            canal = bot.get_channel(canal_id)
            if canal is None:
                print(f"[DICA] Canal para dicas com ID {canal_id} não encontrado na guild {guild_id}.")
                continue

            # Obtém a lista de personagens disponíveis para esta guild
            personagens = dados.get("personagens", [])
            if not personagens:
                print(f"[DICA] Nenhum personagem disponível na guild {guild_id}.")
                continue

            # Seleciona aleatoriamente um personagem disponível
            personagem = random.choice(personagens)
            nome_personagem = personagem["nome"]

            # Carrega as descrições dos personagens a partir do arquivo
            descricoes = carregar_descricoes()
            if nome_personagem in descricoes:
                descricao = descricoes[nome_personagem]
            else:
                descricao = "Tenho uma dica, mas o personagem sumiu."

            mensagem = f"💡 **Dica:** Um personagem ainda não salvo é descrito como:\n*'{descricao}'*"
            await canal.send(mensagem)
            print(f"[DICA] Dica enviada com sucesso para a guild {guild_id}.")
        except Exception as e:
            print(f"[ERRO] Falha ao enviar dica para a guild {guild_id}: {e}")

def carregar_descricoes():
    """
    Carrega o dicionário de descrições dos personagens a partir do arquivo
    resources/descricoes.json.

    O arquivo descricoes.json deve ter o seguinte formato:
        {
            "Twilight Sparkle": "Princesa da Amizade e amante de livros, sempre em busca de conhecimento.",
            "Screwball": "Pônei caótico com uma personalidade peculiar, filha de Discord em algumas versões."
            ...
        }

    Retorna:
        dict: Dicionário com as descrições dos personagens.
    """
    caminho = "resources/descricoes.json"
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            descricoes = json.load(f)
        return descricoes
    except Exception as e:
        print(f"Erro ao carregar descrições dos personagens: {e}")
        return {}
