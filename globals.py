# globals.py

contador_personagens_salvos = {}

personagens_por_usuario = {}  # Dicionário para registrar quais personagens cada usuário salvou

user_cache = {}  # Cache de nomes de usuários

descricoes_personagens = {}

sortes = [] 

ultimo_resgate_por_usuario = {}
personagens_inicial = []
personagens_disponiveis = personagens_inicial.copy()
personagens_salvos = []

ultimo_usuario_salvador = None

restricao_usuario_unico = False

personagens_disponiveis = []
personagens_salvos = []
contador_personagens_salvos = {}
personagens_por_usuario = {}

# Variáveis de tempo em segundos. Por exemplo, 300 segundos (5 minutos)
tempo_impedimento = 300
tempo_sorte = 2000
intervalo_dica_personagem = 1200

ID_DO_CANAL_DICAS = 0
ID_DO_CANAL_SORTE = 0
