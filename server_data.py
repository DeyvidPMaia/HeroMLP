import os
import json
from funcoes import carregar_personagens  # Certifique-se de que essa função está disponível

def caminho_dados_guild(guild_id):
    return f"resources/servidores/{guild_id}.json"

def carregar_dados_guild(guild_id):
    caminho = caminho_dados_guild(guild_id)
    
    # Se o arquivo não existe, cria um novo com valores padrão
    if not os.path.exists(caminho):
        print(f"[INFO] Criando novo arquivo de dados para a guild {guild_id}.")
        dados_iniciais = criar_dados_iniciais()
        salvar_dados_guild(guild_id, dados_iniciais)
        return dados_iniciais

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"[ERRO] Arquivo {caminho} corrompido. Criando um novo.")
        dados_iniciais = criar_dados_iniciais()
        salvar_dados_guild(guild_id, dados_iniciais)
        return dados_iniciais
    except Exception as e:
        print(f"[ERRO] Falha ao carregar dados da guild {guild_id}: {e}")
        return criar_dados_iniciais()  # Retorna um dicionário padrão para evitar erros no código

def criar_dados_iniciais():
    return {
        "personagens": carregar_personagens(),
        "personagens_salvos": [],
        "contador_personagens_salvos": {},
        "personagens_por_usuario": {},
        "tempo_impedimento": 300
    }

def salvar_dados_guild(guild_id, dados):
    caminho = caminho_dados_guild(guild_id)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)

    # Criar backup antes de salvar
    if os.path.exists(caminho):
        backup_caminho = f"{caminho}.bak"
        os.replace(caminho, backup_caminho)

    try:
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"[ERRO] Falha ao salvar dados da guild {guild_id}: {e}")
