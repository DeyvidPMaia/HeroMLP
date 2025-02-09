import os


caminho_env = os.path.join(os.path.dirname(os.getcwd()), ".env")
print(caminho_env)

if os.path.exists(caminho_env):
    with open(caminho_env, "r") as f:
        print(f.read())
else:
    print("Arquivo .env não encontrado ou sem permissão.")
