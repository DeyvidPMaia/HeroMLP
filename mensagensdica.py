import random
import asyncio
import globals
import json

async def enviar_dica_personagem(bot):
    """
    Aguarda um intervalo especificado em globals.intervalo_dica_personagem e, 
    em seguida, envia uma dica de personagem no canal configurado em globals.ID_DO_CANAL_DICAS.
    Se o canal não estiver configurado (None) ou não for encontrado, a dica não é enviada.
    """
    while True:
        await asyncio.sleep(globals.intervalo_dica_personagem)
        try:
            # Verifica se o canal de dicas foi configurado
            if globals.ID_DO_CANAL_DICAS is None:
                print("[DICA] Canal para dicas não configurado.")
                continue

            canal = bot.get_channel(globals.ID_DO_CANAL_DICAS)
            if canal is None:
                print(f"[DICA] Canal para dicas com ID {globals.ID_DO_CANAL_DICAS} não encontrado.")
                continue

            # Se não houver personagens disponíveis, pula a dica
            if not globals.personagens_disponiveis:
                print("[DICA] Nenhum personagem disponível.")
                continue

            # Seleciona aleatoriamente um personagem disponível
            personagem = random.choice(globals.personagens_disponiveis)
            nome_personagem = personagem["nome"]

            # Carrega as descrições diretamente do arquivo descricoes.json
            descricoes = carregar_descricoes()

            # Procura a descrição correspondente ao nome do personagem
            if nome_personagem in descricoes:
                descricao = descricoes[nome_personagem]
            else:
                descricao = "Tenho uma dica, mas o personagem sumiu."

            mensagem = f"💡 **Dica:** Um personagem ainda não salvo é descrito como:\n*'{descricao}'*"
            await canal.send(mensagem)
            print("[DICA] Dica enviada com sucesso.")

        except Exception as e:
            print(f"[ERRO] Falha ao enviar dica: {e}")

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
