import os
import json
from funcoes import carregar_personagens  # Certifique-se de que essa função está disponível

def caminho_dados_guild(guild_id):
    return f"resources/servidores/{guild_id}.json"

def carregar_dados_guild(guild_id):
    caminho = caminho_dados_guild(guild_id)
    if not os.path.exists(caminho):
        # Se o arquivo não existe, cria dados iniciais para o servidor
        dados_iniciais = {
            "personagens": carregar_personagens(),
            "personagens_salvos": [],
            "contador_personagens_salvos": {},
            "personagens_por_usuario": {},
            "tempo_impedimento": 300
        }
        salvar_dados_guild(guild_id, dados_iniciais)
        return dados_iniciais
    else:
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar dados para a guild {guild_id}: {e}")
            return None

def salvar_dados_guild(guild_id, dados):
    caminho = caminho_dados_guild(guild_id)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    try:
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Erro ao salvar dados para a guild {guild_id}: {e}")
