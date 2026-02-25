# Célula 1 - Criar estrutura de pacotes
import os

# Criar diretórios se não existirem
os.makedirs('Func_dash/populacao', exist_ok=True)

# Criar __init__.py vazios
open('Func_dash/__init__.py', 'a').close()
open('Func_dash/populacao/__init__.py', 'a').close()

print("✅ Estrutura de pacotes criada!")