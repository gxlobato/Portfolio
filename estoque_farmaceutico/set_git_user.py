import subprocess

nome = input("Seu nome: ").strip()
email = input("Seu email do GitHub: ").strip()

subprocess.run(f'git config --global user.name "{nome}"', shell=True)
subprocess.run(f'git config --global user.email "{email}"', shell=True)

print("Pronto. Configuração global atualizada.")
