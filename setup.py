"""
🚀 USERBOT PRO v2.0 - setup.py
Configurador interativo inteligente:
  - Detecta e ativa a venv automaticamente antes de qualquer verificação.
  - Instala dependências faltantes automaticamente dentro da venv.
  - Google Drive é totalmente opcional.
  - Qualquer erro inesperado durante o setup é reportado ao canal de logs do dono.
"""
import os
import sys
import json
import subprocess
import importlib

# ══════════════════════════════════════════════════════════════════════════════
# 🎨 CORES DO TERMINAL
# ══════════════════════════════════════════════════════════════════════════════
VERDE   = "\033[92m"
VERMELHO = "\033[91m"
AMARELO = "\033[93m"
AZUL    = "\033[94m"
CIANO   = "\033[96m"
NEGRITO = "\033[1m"
RESET   = "\033[0m"

# ══════════════════════════════════════════════════════════════════════════════
# 🟡 BLOCO 1 — DETECÇÃO E ATIVAÇÃO AUTOMÁTICA DA VENV
# Deve ser o PRIMEIRO bloco, antes de qualquer verificação de bibliotecas.
# ══════════════════════════════════════════════════════════════════════════════
def _esta_em_venv() -> bool:
    return (
        hasattr(sys, "real_prefix")
        or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
    )

def _garantir_venv():
    """Cria a venv se não existir e reinicia o setup dentro dela."""
    if _esta_em_venv():
        return  # Já está na venv, tudo certo

    venv_dir = "venv"
    candidatos = [
        os.path.join(venv_dir, "bin", "python3"),
        os.path.join(venv_dir, "bin", "python"),
        os.path.join(venv_dir, "Scripts", "python.exe"),
    ]
    python_venv = next((c for c in candidatos if os.path.isfile(c)), None)

    if not python_venv:
        print(f"\n{AMARELO}⚠️  Ambiente virtual não encontrado. Criando venv...{RESET}")
        ret = subprocess.run([sys.executable, "-m", "venv", venv_dir])
        if ret.returncode != 0:
            print(f"{VERMELHO}❌ Falha ao criar venv. Verifique se python3-venv está instalado:{RESET}")
            print(f"   {AMARELO}sudo apt install python3-venv{RESET}\n")
            sys.exit(1)
        print(f"{VERDE}✅ Venv criada em '{venv_dir}/'!{RESET}\n")
        python_venv = next((c for c in candidatos if os.path.isfile(c)), None)

    if python_venv:
        print(f"{AMARELO}⚠️  Reiniciando setup dentro da venv...{RESET}\n")
        os.execv(python_venv, [python_venv] + sys.argv)
    else:
        print(f"{VERMELHO}❌ Não foi possível encontrar o Python da venv.{RESET}\n")
        sys.exit(1)

_garantir_venv()

# ══════════════════════════════════════════════════════════════════════════════
# 🟢 FUNÇÕES AUXILIARES
# ══════════════════════════════════════════════════════════════════════════════
def cabecalho():
    print(f"\n{AZUL}{NEGRITO}╔════════════════════════════════════════════╗{RESET}")
    print(f"{AZUL}{NEGRITO}║   🚀 USERBOT PRO v2.0 - SETUP INTELIGENTE  ║{RESET}")
    print(f"{AZUL}{NEGRITO}╚════════════════════════════════════════════╝{RESET}\n")
    print(f"  {CIANO}Python:{RESET} {sys.executable}")
    print(f"  {CIANO}Venv ativa:{RESET} {VERDE}Sim ✅{RESET}\n")


def checar_arquivo(arq, descricao, critico=True):
    if os.path.exists(arq):
        print(f"  {VERDE}✅{RESET} {descricao}: {VERDE}encontrado{RESET}")
        return True
    cor   = VERMELHO if critico else AMARELO
    icone = "❌" if critico else "⚠️"
    print(f"  {cor}{icone}{RESET} {descricao}: {cor}não encontrado{RESET}")
    return False


def instalar_dependencias(faltando: list) -> bool:
    """Tenta instalar as dependências faltantes via pip dentro da venv."""
    req_file = "requirements.txt"
    if os.path.exists(req_file):
        print(f"\n  {AMARELO}▶ Instalando dependências de requirements.txt...{RESET}")
        ret = subprocess.run([sys.executable, "-m", "pip", "install", "-r", req_file, "-q"])
        if ret.returncode == 0:
            print(f"  {VERDE}✅ Dependências instaladas com sucesso!{RESET}")
            return True
        else:
            print(f"  {VERMELHO}❌ Falha na instalação via requirements.txt.{RESET}")
    else:
        # Instala uma por uma se não tiver requirements.txt
        print(f"\n  {AMARELO}▶ Instalando dependências manualmente...{RESET}")
        pacotes_pip = {
            "pyrogram": "pyrogram", "pydrive2": "PyDrive2", "requests": "requests",
            "humanize": "humanize", "speedtest": "speedtest-cli", "PIL": "Pillow",
            "gtts": "gTTS", "deep_translator": "deep-translator",
            "psutil": "psutil", "tgcrypto": "TgCrypto", "pyromod": "pyromod",
            "aiofiles": "aiofiles", "aiohttp": "aiohttp",
            "google.generativeai": "google-generativeai"
        }
        for lib in faltando:
            pkg = pacotes_pip.get(lib, lib)
            ret = subprocess.run([sys.executable, "-m", "pip", "install", pkg, "-q"])
            icone = f"{VERDE}✅{RESET}" if ret.returncode == 0 else f"{VERMELHO}❌{RESET}"
            print(f"  {icone} {pkg}")
    return False


def verificar_bibliotecas() -> list:
    """Verifica quais bibliotecas estão faltando (Drive excluído — é opcional)."""
    print(f"\n{NEGRITO}📦 [2/5] Verificando dependências do Python...{RESET}\n")
    libs = [
        ("pyrogram",        "pyrogram"),
        ("requests",        "requests"),
        ("humanize",        "humanize"),
        ("speedtest",       "speedtest-cli"),
        ("PIL",             "Pillow"),
        ("gtts",            "gTTS"),
        ("deep_translator", "deep-translator"),
        ("psutil",          "psutil"),
        ("tgcrypto",        "TgCrypto"),
        ("pyromod",         "pyromod"),
        ("aiofiles",        "aiofiles"),
        ("aiohttp",         "aiohttp"),
        ("google.generativeai", "google-generativeai"),
    ]
    faltando = []
    for lib_import, lib_name in libs:
        try:
            importlib.import_module(lib_import)
            print(f"  {VERDE}✅{RESET} {lib_name}")
        except ImportError:
            print(f"  {VERMELHO}❌{RESET} {lib_name}")
            faltando.append(lib_import)
    return faltando


def notificar_log_telegram(canal_id, texto: str):
    """
    Tenta enviar uma mensagem ao canal de logs do dono via API HTTP
    do Telegram (sem precisar do Pyrogram completo).
    Usado para notificar movimentações e erros durante o setup.
    """
    try:
        import requests as req
        # Usa o bot @userinfobot como fallback não funciona — precisamos de um bot token.
        # Se o usuário configurou BOT_TOKEN no config.json, usamos ele.
        config_path = "config.json"
        if not os.path.exists(config_path):
            return
        with open(config_path) as f:
            cfg = json.load(f)
        bot_token = cfg.get("BOT_TOKEN")
        canal = canal_id or cfg.get("ID_CANAL_LOGS")
        if not bot_token or not canal:
            return
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        req.post(url, json={"chat_id": canal, "text": texto, "parse_mode": "Markdown"}, timeout=5)
    except Exception:
        pass  # Silencioso — não deve travar o setup


# ══════════════════════════════════════════════════════════════════════════════
# 🟢 FUNÇÃO PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
def main():
    cabecalho()

    # ── [1/5] VERIFICAÇÃO DE ARQUIVOS ────────────────────────────────────────
    print(f"{NEGRITO}🔍 [1/5] Verificando arquivos do ambiente...{RESET}\n")
    sessao = checar_arquivo("meu_userbot.session", "Sessão Pyrogram", critico=False)
    req    = checar_arquivo("requirements.txt",    "requirements.txt", critico=False)

    if sessao:
        print(f"\n  {VERDE}🎉 Sessão do Telegram já está ativa! Não precisará logar novamente.{RESET}")
    else:
        print(f"\n  {AMARELO}ℹ️  Você fará login no Telegram na primeira execução do bot.{RESET}")

    # ── [2/5] VERIFICAÇÃO DE BIBLIOTECAS ─────────────────────────────────────
    faltando = verificar_bibliotecas()
    if faltando:
        print(f"\n  {AMARELO}⚠️  Bibliotecas faltando: {', '.join(faltando)}{RESET}")
        resp = input(f"\n  ❓ Instalar automaticamente agora? (S/n): ").strip().lower()
        if resp in ("", "s"):
            instalar_dependencias(faltando)
        else:
            resp2 = input(f"  ❓ Continuar mesmo assim? (s/N): ").strip().lower()
            if resp2 != "s":
                print(f"\n{VERMELHO}Setup interrompido.{RESET}\n")
                return
    else:
        print(f"\n  {VERDE}✅ Todas as bibliotecas estão prontas!{RESET}")

    # ── [3/5] GOOGLE DRIVE (OPCIONAL) ────────────────────────────────────────
    print(f"\n{NEGRITO}📂 [3/5] Google Drive (opcional)...{RESET}\n")
    print(f"  O Google Drive permite que o bot faça backup e organize seus arquivos.")
    print(f"  {AMARELO}Você pode pular esta etapa e configurar depois.{RESET}\n")

    usar_drive = input(f"  ❓ Deseja configurar o Google Drive? (s/N): ").strip().lower()
    drive_ativo = usar_drive == "s"

    if drive_ativo:
        drive_creds   = checar_arquivo("meu_drive.json",       "Credenciais Google Drive", critico=False)
        drive_secrets = checar_arquivo("client_secrets.json",  "Client Secrets do Drive",  critico=False)
        if not (drive_creds and drive_secrets):
            print(f"\n  {AMARELO}⚠️  Coloque os arquivos na pasta antes de iniciar o bot:{RESET}")
            print(f"     - {AMARELO}meu_drive.json{RESET}")
            print(f"     - {AMARELO}client_secrets.json{RESET}")
            print(f"  {AMARELO}O Drive ficará como OFFLINE até os arquivos serem adicionados.{RESET}")
    else:
        print(f"  {CIANO}ℹ️  Google Drive ignorado. Pode ser ativado depois editando config.json.{RESET}")

    # ── [4/5] VERIFICAÇÃO DE CONFIG EXISTENTE ────────────────────────────────
    print(f"\n{NEGRITO}⚙️  [4/5] Verificando configuração existente...{RESET}\n")
    if os.path.exists("config.json"):
        print(f"  {AMARELO}⚠️  Já existe um config.json.{RESET}")
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                atual = json.load(f)
            print(f"     • API_ID:  {atual.get('API_ID', '?')}")
            print(f"     • Prefixo: '{atual.get('PREFIXO', ',')}'")
            print(f"     • Drive:   {'Ativo' if atual.get('DRIVE_ATIVO') else 'Inativo'}")
        except Exception:
            print(f"     {VERMELHO}(arquivo malformado, será sobrescrito){RESET}")
        resp = input(f"\n  ❓ Deseja sobrescrever? (s/N): ").strip().lower()
        if resp != "s":
            print(f"\n  {VERDE}✅ Mantendo configurações atuais. Setup encerrado.{RESET}\n")
            return

    # ── [5/5] COLETA DE DADOS ─────────────────────────────────────────────────
    print(f"\n{NEGRITO}📝 [5/5] Configuração das credenciais...{RESET}\n")
    print(f"  {AMARELO}ℹ️  Obtenha API_ID e API_HASH em: https://my.telegram.org{RESET}\n")

    config = {}
    api_id_raw = None
    canal_id   = None

    try:
        api_id_raw              = input(f"  🔑 API_ID: ").strip()
        config['API_ID']        = int(api_id_raw)
        config['API_HASH']      = input(f"  🔐 API_HASH: ").strip()
        canal_raw               = input(f"  📡 ID do canal de logs (com -100): ").strip()
        config['ID_CANAL_LOGS'] = int(canal_raw)
        canal_id                = config['ID_CANAL_LOGS']
        config['PREFIXO']       = input(f"  ⌨️  Prefixo dos comandos (padrão ','): ").strip() or ","
        config['DRIVE_ATIVO']   = drive_ativo

        if drive_ativo:
            pasta = input(f"  📁 ID da pasta raiz do Google Drive: ").strip()
            config['ID_PASTA_RAIZ_DRIVE'] = pasta
            limite = input(f"  📦 Limite auto-upload em MB (padrão 20): ").strip() or "20"
            config['LIMITE_AUTO_UPLOAD'] = int(limite) * 1024 * 1024

        # BOT_TOKEN opcional — usado para reportar erros de outros usuários
        print(f"\n  {CIANO}ℹ️  (Opcional) Token de um bot para reportar erros de outros usuários ao seu canal.{RESET}")
        bot_token = input(f"  🤖 BOT_TOKEN (Enter para pular): ").strip()
        if bot_token:
            config['BOT_TOKEN'] = bot_token
            
        print(f"\n  {CIANO}ℹ️  (Opcional) Chave API do Google Gemini para comandos de Inteligência Artificial.{RESET}")
        print(f"  {AMARELO}Pegue a sua chave grátis em: https://aistudio.google.com/app/apikey{RESET}")
        gemini_key = input(f"  🤖 GEMINI_API_KEY (Enter para pular): ").strip()
        if gemini_key:
            config['GEMINI_API_KEY'] = gemini_key

        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

        print(f"\n{VERDE}{NEGRITO}✅ config.json criado com sucesso!{RESET}\n")
        
        notificar_log_telegram(canal_id, "✅ **SETUP CONCLUÍDO**\nAs configurações do Userbot foram geradas ou atualizadas com sucesso!")
        print(f"{AZUL}🚀 Próximos passos:{RESET}")
        print(f"   • Inicie o bot: {VERDE}python3 main.py{RESET}")
        print()

    except ValueError as e:
        msg = f"API_ID e ID do Canal devem ser apenas números. Detalhe: {e}"
        print(f"\n{VERMELHO}❌ Erro: {msg}{RESET}\n")
        texto_erro = f"🚨 **ERRO NO SETUP**\n\n👤 API_ID: `{api_id_raw}`\n❌ Erro: `{msg}`"
        notificar_log_telegram(canal_id, texto_erro)

    except KeyboardInterrupt:
        print(f"\n\n{AMARELO}Cancelado pelo usuário.{RESET}\n")
        notificar_log_telegram(canal_id, "⚠️ **SETUP CANCELADO**\nO usuário interrompeu a configuração pelo terminal.")

    except Exception as e:
        print(f"\n{VERMELHO}❌ Erro inesperado: {e}{RESET}\n")
        texto_erro = f"🚨 **ERRO INESPERADO NO SETUP**\n\n👤 API_ID: `{api_id_raw}`\n❌ Erro: `{e}`"
        notificar_log_telegram(canal_id, texto_erro)


if __name__ == "__main__":
    main()
