"""
🚀 USERBOT PRO v1.0 - setup.py
Configurador interativo: verifica ambiente, sessão, Drive e bibliotecas
antes de gerar o config.json.
"""
import os
import json
import importlib

VERDE = "\033[92m"
VERMELHO = "\033[91m"
AMARELO = "\033[93m"
AZUL = "\033[94m"
NEGRITO = "\033[1m"
RESET = "\033[0m"


def cabecalho():
    print(f"\n{AZUL}{NEGRITO}╔════════════════════════════════════════════╗{RESET}")
    print(f"{AZUL}{NEGRITO}║   🚀 USERBOT PRO v1.0 - SETUP INTELIGENTE  ║{RESET}")
    print(f"{AZUL}{NEGRITO}╚════════════════════════════════════════════╝{RESET}\n")


def checar_arquivo(arq, descricao, critico=True):
    if os.path.exists(arq):
        print(f"  {VERDE}✅{RESET} {descricao}: {VERDE}encontrado{RESET}")
        return True
    cor = VERMELHO if critico else AMARELO
    icone = "❌" if critico else "⚠️"
    print(f"  {cor}{icone}{RESET} {descricao}: {cor}não encontrado{RESET}")
    return False


def verificar_bibliotecas():
    print(f"\n{NEGRITO}📦 Verificando dependências do Python...{RESET}\n")
    libs = [
        ("pyrogram", "pyrogram"),
        ("pydrive2", "PyDrive2"),
        ("requests", "requests"),
        ("humanize", "humanize"),
        ("speedtest", "speedtest-cli"),
        ("PIL", "Pillow"),
        ("gtts", "gTTS"),
        ("deep_translator", "deep-translator"),
        ("psutil", "psutil"),
        ("tgcrypto", "TgCrypto"),
    ]
    faltando = []
    for lib_import, lib_name in libs:
        try:
            importlib.import_module(lib_import)
            print(f"  {VERDE}✅{RESET} {lib_name}")
        except ImportError:
            print(f"  {VERMELHO}❌{RESET} {lib_name}")
            faltando.append(lib_name)
    return faltando


def main():
    cabecalho()

    # --- VERIFICAÇÃO DE AMBIENTE ---
    print(f"{NEGRITO}🔍 [1/4] Verificando arquivos do ambiente...{RESET}\n")
    sessao = checar_arquivo("meu_userbot.session", "Sessão Pyrogram", critico=False)
    drive_creds = checar_arquivo("meu_drive.json", "Credenciais Google Drive", critico=False)
    drive_secrets = checar_arquivo("client_secrets.json", "Client Secrets do Drive", critico=False)
    req = checar_arquivo("requirements.txt", "requirements.txt", critico=False)

    if sessao:
        print(f"\n  {VERDE}🎉 Sessão do Telegram já está ativa! Não precisará logar.{RESET}")
    else:
        print(f"\n  {AMARELO}ℹ️  Você fará login no Telegram na primeira execução do bot.{RESET}")

    if not (drive_creds and drive_secrets):
        print(f"\n  {AMARELO}⚠️  Coloque os arquivos do Drive na pasta antes de iniciar:{RESET}")
        print(f"     - {AMARELO}meu_drive.json{RESET}")
        print(f"     - {AMARELO}client_secrets.json{RESET}")

    # --- VERIFICAÇÃO DE BIBLIOTECAS ---
    print(f"\n{NEGRITO}📦 [2/4] Verificando bibliotecas...{RESET}")
    faltando = verificar_bibliotecas()
    if faltando:
        print(f"\n  {VERMELHO}❌ Faltam bibliotecas. Instale com:{RESET}")
        print(f"     {AMARELO}pip install -r requirements.txt{RESET}")
        if not req:
            print(f"  {AMARELO}⚠️  requirements.txt não encontrado!{RESET}")
        resp = input(f"\n  ❓ Continuar mesmo assim? (s/N): ").strip().lower()
        if resp != "s":
            print(f"\n{VERMELHO}Setup interrompido.{RESET}\n")
            return
    else:
        print(f"\n  {VERDE}✅ Todas as bibliotecas estão prontas!{RESET}")

    # --- VERIFICAÇÃO DE CONFIG EXISTENTE ---
    print(f"\n{NEGRITO}⚙️  [3/4] Verificando configuração existente...{RESET}\n")
    if os.path.exists("config.json"):
        print(f"  {AMARELO}⚠️  Já existe um config.json.{RESET}")
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                atual = json.load(f)
            print(f"     • API_ID: {atual.get('API_ID', '?')}")
            print(f"     • Prefixo: '{atual.get('PREFIXO', ',')}'")
        except:
            print(f"     {VERMELHO}(arquivo malformado, será sobrescrito){RESET}")
        resp = input(f"\n  ❓ Deseja sobrescrever? (s/N): ").strip().lower()
        if resp != "s":
            print(f"\n  {VERDE}✅ Mantendo configurações atuais. Setup encerrado.{RESET}\n")
            return

    # --- COLETA DE DADOS ---
    print(f"\n{NEGRITO}📝 [4/4] Configuração das credenciais...{RESET}\n")
    print(f"  {AMARELO}ℹ️  Obtenha API_ID e API_HASH em: https://my.telegram.org{RESET}\n")

    config = {}
    try:
        config['API_ID'] = int(input(f"  🔑 API_ID: ").strip())
        config['API_HASH'] = input(f"  🔐 API_HASH: ").strip()
        config['ID_CANAL_LOGS'] = int(input(f"  📡 ID do canal de logs (com -100): ").strip())
        config['ID_PASTA_RAIZ_DRIVE'] = input(f"  📁 ID da pasta raiz do Google Drive: ").strip()
        config['PREFIXO'] = input(f"  ⌨️  Prefixo dos comandos (padrão ','): ").strip() or ","
        limite = input(f"  📦 Limite auto-upload em MB (padrão 20): ").strip() or "20"
        config['LIMITE_AUTO_UPLOAD'] = int(limite) * 1024 * 1024

        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

        print(f"\n{VERDE}{NEGRITO}✅ config.json criado com sucesso!{RESET}\n")
        print(f"{AZUL}🚀 Próximos passos:{RESET}")
        if faltando:
            print(f"   1. Instale dependências: {AMARELO}pip install -r requirements.txt{RESET}")
            print(f"   2. Inicie o bot: {AMARELO}python3 main.py{RESET}")
        else:
            print(f"   • Inicie o bot: {AMARELO}python3 main.py{RESET}")
        print()

    except ValueError:
        print(f"\n{VERMELHO}❌ Erro: API_ID e ID do Canal devem ser apenas números.{RESET}\n")
    except KeyboardInterrupt:
        print(f"\n\n{AMARELO}Cancelado pelo usuário.{RESET}\n")
    except Exception as e:
        print(f"\n{VERMELHO}❌ Erro inesperado: {e}{RESET}\n")


if __name__ == "__main__":
    main()
