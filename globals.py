# globals.py

# Dicionário para contar quantos personagens foram salvos
contador_personagens_salvos = {}

# Dicionário para registrar quais personagens cada usuário salvou
personagens_por_usuario = {}

# Cache de nomes de usuários
user_cache = {}

# Dicionário de descrições dos personagens
descricoes_personagens = {}

# Lista de sortes disponíveis
sortes = []

# Controle de último resgate e salvamento
ultimo_resgate_por_usuario = {}
ultimo_usuario_salvador = None

# Lista de personagens disponíveis e salvos
personagens_inicial = []
personagens_disponiveis = []
personagens_salvos = []

# Restrição de usuário único
restricao_usuario_unico = False

# Variáveis de tempo em segundos
tempo_impedimento = 300  # 5 minutos
tempo_sorte = 2000
tempo_personagem_perdido = 86400
intervalo_dica_personagem = 1200
tempo_recompensa = 600

# IDs dos canais
ID_DO_CANAL_DICAS = 0
ID_DO_CANAL_SORTE = 0
ID_DO_CANAL_RECOMPENSA = 0

maintenance_mode = False

mostra_nomes_perdidos = False
mostrar_salvos_por_trevo = True
modo_teste_esquecimento = True

personagens_especiais_inicial = {
    "Lauren Faust": {
        "recompensa": 10,
        "ranking":2,
        "copiavel": True
    }
}