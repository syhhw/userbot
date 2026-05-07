"""
🚀 USERBOT PRO v2.1 - main.py
Núcleo central que carrega configurações, conecta ao Google Drive
e inicializa o cliente Pyrogram com os plugins.

Inteligência automática:
  - Detecta se está rodando dentro de uma venv; se não estiver, reinicia
    automaticamente usando o Python da venv local (./venv/).
  - Detecta se é novo usuário (config.json ausente) e redireciona para
    o setup.py interativo antes de iniciar.
  - Pergunta se o usuário quer rodar em segundo plano via nohup.
    Se sim, relança o processo com nohup e encerra o processo atual.
"""
import os
import sys

# ══════════════════════════════════════════════════════════════════════════════
# 🟡 BLOCO 1 — PASSO 1: DETECÇÃO E ATIVAÇÃO DA VENV
# Se não estiver na venv, reinicia com o Python dela via os.execv.
# os.execv substitui o processo atual — não cria filho, sem loop.
# ══════════════════════════════════════════════════════════════════════════════

AMARELO = "\033[93m"
VERDE   = "\033[92m"
AZUL    = "\033[94m"
VERMELHO = "\033[91m"
NEGRITO = "\033[1m"
RESET   = "\033[0m"

def _em_venv() -> bool:
    return (
        hasattr(sys, "real_prefix")
        or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
    )

if not _em_venv():
    _base        = os.path.dirname(os.path.abspath(__file__))
    _python_venv = os.path.join(_base, "venv", "bin", "python3")

    if os.path.isfile(_python_venv):
        print(f"{AMARELO}⚠️  Venv detectada. Reiniciando com: {_python_venv}{RESET}")
        os.execv(_python_venv, [_python_venv] + sys.argv)
        # os.execv substitui o processo — nada abaixo é executado
    else:
        print(f"{AMARELO}⚠️  Pasta venv/ não encontrada. Rodando com Python do sistema.{RESET}")
        print(f"   Crie com: {VERDE}python3 -m venv venv && source venv/bin/activate{RESET}")
        print(f"   Depois:   {VERDE}pip install -r requirements.txt{RESET}\n")

# ══════════════════════════════════════════════════════════════════════════════
# 🟡 BLOCO 1 — PASSO 2: SEGUNDO PLANO VIA NOHUP
# Pergunta se quer rodar em background. Se sim, relança com nohup e encerra.
# A flag --background evita que o processo filho pergunte de novo.
# ══════════════════════════════════════════════════════════════════════════════

def _ja_esta_em_screen() -> bool:
    """Detecta se já está dentro de uma sessão screen (para o aviso no log)."""
    return "STY" in os.environ or os.environ.get("TERM") == "screen"

if "--background" not in sys.argv:
    print(f"\n{AZUL}{NEGRITO}╔════════════════════════════════════════════╗{RESET}")
    print(f"{AZUL}{NEGRITO}║   🖥️  MODO DE EXECUÇÃO                      ║{RESET}")
    print(f"{AZUL}{NEGRITO}╚════════════════════════════════════════════╝{RESET}\n")
    print(f"  {VERDE}• Primeiro plano:{RESET} o bot para quando você fechar o terminal.")
    print(f"  {VERDE}• Segundo plano:{RESET}  o bot continua rodando mesmo após fechar o terminal.\n")

    _resp = input("  ❓ Rodar em segundo plano? (S/n): ").strip().lower()

    if _resp in ("", "s"):
        _script = os.path.abspath(__file__)
        _log    = os.path.join(os.path.dirname(_script), "userbot.log")
        _cmd    = f"nohup {sys.executable} {_script} --background > {_log} 2>&1 &"

        os.system(_cmd)
        print(f"\n{VERDE}✅ Bot iniciado em segundo plano!{RESET}")
        print(f"   Log em: {_log}")
        print(f"   Para parar: {AMARELO}kill $(pgrep -f 'python.*main.py'){RESET}\n")
        sys.exit(0)
    else:
        print(f"\n  {VERDE}▶ Rodando em primeiro plano...{RESET}\n")

# ══════════════════════════════════════════════════════════════════════════════
# 🟡 BLOCO 2 — DETECÇÃO DE NOVO USUÁRIO (config.json ausente)
# ══════════════════════════════════════════════════════════════════════════════
def _verificar_primeiro_uso():
    if not os.path.exists("config.json"):
        print(f"\n{AZUL}{NEGRITO}╔════════════════════════════════════════════╗{RESET}")
        print(f"{AZUL}{NEGRITO}║   🚀 USERBOT PRO — PRIMEIRO USO DETECTADO  ║{RESET}")
        print(f"{AZUL}{NEGRITO}╚════════════════════════════════════════════╝{RESET}\n")
        print(f"  {AMARELO}⚠️  config.json não encontrado.{RESET}")
        print(f"  {AMARELO}    É necessário configurar o bot antes de iniciá-lo.{RESET}\n")

        if not os.path.exists("setup.py"):
            print(f"  {AMARELO}❌ setup.py também não encontrado. Baixe o projeto completo.{RESET}\n")
            sys.exit(1)

        resp = input(f"  ❓ Deseja executar o setup agora? (S/n): ").strip().lower()
        if resp in ("", "s"):
            print(f"\n{VERDE}▶ Iniciando setup...{RESET}\n")
            import runpy
            runpy.run_path("setup.py", run_name="__main__")

            if not os.path.exists("config.json"):
                print(f"\n  {AMARELO}⚠️  Setup encerrado sem criar config.json. Bot não iniciado.{RESET}\n")
                sys.exit(0)

            print(f"\n{VERDE}✅ Setup concluído! Iniciando o bot...{RESET}\n")
        else:
            print(f"\n  {AMARELO}Setup cancelado. Execute 'python3 setup.py' quando estiver pronto.{RESET}\n")
            sys.exit(0)

_verificar_primeiro_uso()

# ══════════════════════════════════════════════════════════════════════════════
# 🟡 BLOCO 3 — DETECÇÃO AUTOMÁTICA E AUTO-REPAIR DE DEPENDÊNCIAS
# ══════════════════════════════════════════════════════════════════════════════
def _garantir_dependencias():
    import importlib
    import subprocess
    import sys
    import os
    import json

    libs = [
        ("pyrogram",            "pyrogram>=2.0.106"),
        ("requests",            "requests"),
        ("humanize",            "humanize"),
        ("speedtest",           "speedtest-cli"),
        ("PIL",                 "Pillow"),
        ("gtts",                "gTTS"),
        ("deep_translator",     "deep-translator"),
        ("psutil",              "psutil"),
        ("tgcrypto",            "TgCrypto"),
        ("pyromod",             "pyromod"),
        ("aiofiles",            "aiofiles"),
        ("aiohttp",             "aiohttp"),
        ("google.generativeai", "google-generativeai"),
        ("yt_dlp",              "yt-dlp"),
        ("pydrive2",            "PyDrive2")
    ]
    faltando = []
    for lib_import, lib_name in libs:
        try:
            importlib.import_module(lib_import)
        except ImportError:
            faltando.append(lib_name)
            
    if faltando:
        print(f"\n{AMARELO}⚠️  Dependências ausentes detectadas: {', '.join(faltando)}{RESET}")
        print(f"{AZUL}▶  Baixando e instalando em background (isso pode levar alguns segundos)...{RESET}")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", *faltando, "-q"], check=True)
            print(f"{VERDE}✅ Instalação concluída! Reiniciando o bot...{RESET}\n")
            with open(".deps_updated.json", "w", encoding="utf-8") as f:
                json.dump(faltando, f)
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            print(f"{VERMELHO}❌ Falha crítica ao tentar instalar pacotes automaticamente: {e}{RESET}")
            sys.exit(1)

_garantir_dependencias()

# ══════════════════════════════════════════════════════════════════════════════
# 🟢 IMPORTS PRINCIPAIS
# ══════════════════════════════════════════════════════════════════════════════
import json
import time
import logging
import asyncio

# pyromod DEVE ser importado antes do Client para injetar client.listen()
try:
    import pyromod
except ImportError:
    pass  # instale com: pip install pyromod

from pyrogram import Client, idle

# Google Drive é opcional
drive = None
try:
    from pydrive2.auth import GoogleAuth
    from pydrive2.drive import GoogleDrive
    _DRIVE_DISPONIVEL = True
except ImportError:
    _DRIVE_DISPONIVEL = False

# ══════════════════════════════════════════════════════════════════════════════
# 🟢 IDENTIDADE DO PROJETO
# ══════════════════════════════════════════════════════════════════════════════
__VERSAO__ = "2.1"
UPDATE_FLAG = ".update_pending.json"

# ══════════════════════════════════════════════════════════════════════════════
# 🟢 LOGS COLORIDOS NO TERMINAL
# ══════════════════════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("UserbotCore")
logging.getLogger("pyrogram").setLevel(logging.WARNING)

# ══════════════════════════════════════════════════════════════════════════════
# 🟢 CARREGAMENTO DE CONFIGURAÇÕES
# ══════════════════════════════════════════════════════════════════════════════
try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
except json.JSONDecodeError as e:
    logger.error(f"❌ config.json está malformado: {e}")
    sys.exit(1)

PREFIXO = config.get("PREFIXO", ",")
logger.info(f"🔧 Prefixo carregado: '{PREFIXO}'")

# ══════════════════════════════════════════════════════════════════════════════
# 🟢 AUTENTICAÇÃO GOOGLE DRIVE (opcional)
# ══════════════════════════════════════════════════════════════════════════════
# Ativa Drive automaticamente se: pydrive2 instalado + credenciais existem + pasta configurada
_drive_configurado = (
    config.get("ID_PASTA_RAIZ_DRIVE")
    and os.path.exists("meu_drive.json")
)

if _DRIVE_DISPONIVEL and _drive_configurado:
    try:
        gauth = GoogleAuth()
        gauth.LoadCredentialsFile("meu_drive.json")
        if gauth.credentials is None:
            logger.warning("⚠️ Credenciais do Drive não encontradas em meu_drive.json")
        elif gauth.access_token_expired:
            gauth.Refresh()
            gauth.SaveCredentialsFile("meu_drive.json")
        else:
            gauth.Authorize()
        drive = GoogleDrive(gauth)
        logger.info("✅ Google Drive conectado.")
    except Exception as e:
        logger.error(f"❌ Falha ao conectar Drive: {e}")
elif _drive_configurado and not _DRIVE_DISPONIVEL:
    logger.warning("⚠️ pydrive2 não instalado. Instale com: pip install pydrive2")
else:
    logger.info("ℹ️  Google Drive não configurado (opcional).")

# ══════════════════════════════════════════════════════════════════════════════
# 🟢 INICIALIZAÇÃO DO CLIENTE PYROGRAM
# ══════════════════════════════════════════════════════════════════════════════
os.makedirs("plugins", exist_ok=True)

app = Client(
    "meu_userbot",
    api_id=config["API_ID"],
    api_hash=config["API_HASH"],
    device_model="Samsung Galaxy S25",
    system_version="Android 14",
    plugins=dict(root="plugins")
)

app.config       = config
app.drive        = drive
app.tempo_inicio = time.time()
app.PREFIXO      = PREFIXO
app.VERSAO       = __VERSAO__
app.UPDATE_FLAG  = UPDATE_FLAG

# ══════════════════════════════════════════════════════════════════════════════
# 🟢 TRATAMENTO SILENCIOSO DE ERROS COMUNS
# ══════════════════════════════════════════════════════════════════════════════
def manipulador_erros(loop, context):
    erro = str(context.get("exception", ""))
    if any(x in erro for x in ["Peer id invalid", "Message to delete not found", "MESSAGE_NOT_MODIFIED"]):
        return
    try:
        app.loop.create_task(app.send_message(config["ID_CANAL_LOGS"], f"⚠️ **ALERTA DO SISTEMA:**\nErro interno detectado em uma das tarefas de execução:\n`{erro}`"))
    except Exception:
        pass
    loop.default_exception_handler(context)

# ══════════════════════════════════════════════════════════════════════════════
# 🟢 ROTINA PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
async def iniciar():
    logger.info(f"🚀 INICIANDO USERBOT PRO v{__VERSAO__}...")
    await app.start()

    em_background = "--background" in sys.argv or _ja_esta_em_screen()
    if em_background:
        screen_info = "\n🖥️ Rodando em **segundo plano**"
    else:
        screen_info = "\n🖥️ Rodando em **primeiro plano** (terminal aberto)"

    try:
        if os.path.exists(UPDATE_FLAG):
            try:
                with open(UPDATE_FLAG, "r", encoding="utf-8") as f:
                    info_update = json.load(f)
                arquivos = info_update.get("arquivos", [])
                lista_arq = "\n".join([f"  • `{a}`" for a in arquivos[:15]]) or "  • (sem detalhes)"
                if len(arquivos) > 15:
                    lista_arq += f"\n  • ... e mais {len(arquivos) - 15} arquivo(s)"
                texto_update = (
                    f"✅ **AUTO-UPDATE CONCLUÍDO**\n\n"
                    f"📦 Versão: `v{__VERSAO__}`\n"
                    f"🔢 Commit: `{info_update.get('commit', 'n/a')}`\n"
                    f"👤 Autor: `{info_update.get('autor', 'n/a')}`\n"
                    f"💬 Mensagem: _{info_update.get('mensagem', 'n/a')}_\n"
                    f"📁 Arquivos alterados ({len(arquivos)}):\n{lista_arq}\n\n"
                    f"🔧 Prefixo: `{PREFIXO}` | 📂 Drive: {'Conectado' if drive else 'OFFLINE'}"
                    f"{screen_info}"
                )
                await app.send_message(config["ID_CANAL_LOGS"], texto_update)
            except Exception as e:
                logger.warning(f"⚠️ Falha ao ler flag de update: {e}")
            finally:
                try:
                    os.remove(UPDATE_FLAG)
                except:
                    pass
        elif os.path.exists(".deps_updated.json"):
            try:
                with open(".deps_updated.json", "r", encoding="utf-8") as f:
                    libs_instaladas = json.load(f)
                lista_libs = "\n".join([f"📦 `{lib}`" for lib in libs_instaladas])
                await app.send_message(
                    config["ID_CANAL_LOGS"],
                    f"🛠️ **AUTO-REPAIR DETECTADO:**\n\nDetectei que bibliotecas vitais estavam faltando e as instalei automaticamente antes de dar boot:\n{lista_libs}\n\n🚀 **Userbot v{__VERSAO__} ONLINE!**"
                )
            except Exception as e:
                logger.warning(f"⚠️ Falha ao notificar libs instaladas: {e}")
            finally:
                try:
                    os.remove(".deps_updated.json")
                except:
                    pass
        else:
            await app.send_message(
                config["ID_CANAL_LOGS"],
                f"🚀 **Userbot v{__VERSAO__} ONLINE!**\n\n"
                f"✅ Sistema sincronizado.\n"
                f"🔧 Prefixo: `{PREFIXO}`\n"
                f"📂 Drive: {'Conectado' if drive else 'OFFLINE'}"
                f"{screen_info}"
            )
    except Exception as e:
        logger.warning(f"⚠️ Falha ao avisar no canal de logs: {e}")

    logger.info(f"✅ USERBOT ONLINE | Prefixo: '{PREFIXO}' | Aguardando comandos...")
    await idle()
    try:
        await app.send_message(config["ID_CANAL_LOGS"], "🛑 **USERBOT OFFLINE**\nO processo foi encerrado de forma segura.")
    except Exception:
        pass
    await app.stop()
    logger.info("👋 Userbot encerrado.")


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(manipulador_erros)
        loop.run_until_complete(iniciar())
    except KeyboardInterrupt:
        logger.info("👋 Encerrado pelo usuário.")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        sys.exit(1)
