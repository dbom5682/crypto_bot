import os
import shutil
import unicodedata
import re

# Pasta origem (onde estão os arquivos originais)
src_folder = r"C:\Users\Pedro\Music\PACKZÃO BASES FUNK\PACKZÃO BASES FUNK"

# Pasta destino (onde serão copiados e renomeados)
dst_folder = r"C:\Users\Pedro\Music\PACKZÃO BASES FUNK\python"

if not os.path.exists(dst_folder):
    os.makedirs(dst_folder)

def remover_acentos(texto):
    # Remove acentos e caracteres especiais
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    return texto

def limpar_nome(nome):
    nome_sem_acentos = remover_acentos(nome)
    # Remove tudo que não for letra, número, underline ou ponto
    nome_limpo = re.sub(r'[^A-Za-z0-9._-]', '_', nome_sem_acentos)
    return nome_limpo

for arquivo in os.listdir(src_folder):
    caminho_origem = os.path.join(src_folder, arquivo)
    if os.path.isfile(caminho_origem):
        novo_nome = limpar_nome(arquivo)
        caminho_destino = os.path.join(dst_folder, novo_nome)
        shutil.copy2(caminho_origem, caminho_destino)
        print(f"Copiado: {arquivo} -> {novo_nome}")

print("Pronto! Arquivos copiados e renomeados.")
