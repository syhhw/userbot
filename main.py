"""
🚀 USERBOT PRO v1.0 - main.py
Núcleo central que carrega configurações, conecta ao Google Drive
e inicializa o cliente Pyrogram com os plugins.

Inteligência automática:
  - Detecta se está rodando dentro de uma venv; se não estiver, reinicia
    automaticamente usando o Python da venv local (./venv/).
  - Detecta se é novo usuário (config.json ausente) e redireciona para
    o setup.py interativo antes de iniciar.
  - Pergunta se o usuário quer rodar em segundo plano via screen.
    Se sim, cria/reutiliza uma sessão screen e avisa no canal de logs
    o comando para retornar à sessão.
"""
import os
import sys

# ══════════════════════════════════════════════════════════════════════════════
# 🟡 BLOCO 1 — DETECÇÃO E ATIVAÇÃO AUTOMÁTICA DA VENV
# Deve ser o PRIMEIRO bloco do arquivo, antes de qualquer outro import.
# ══════════════════════════════════════════════════════════════════════════════
def _esta_em_venv() -> bool:
    """Retorna True se o Python atual está rodando dentro de uma venv."""
    return (
        hasattr(sys, "real_prefix")
        or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
    )

def _reiniciar_em_venv():
    """Reinicia o script usando o Python da venv local (./venv/)."""
    VERDE   = "\033[92m"
    AMARELO = "\033[93m"
    RESET   = "\033[0m"

    candidatos = [
        os.path.join("venv", "bin", "python3"),
        os.path.join("venv", "bin", "python"),
        os.path.join("venv", "Scripts", "python.exe"),
    ]

    python_venv = next((c for c in candidatos if os.path.isfile(c)), None)

    if python_venv:
        print(f"{AMARELO}⚠️  Venv não ativa. Reiniciando com: {python_venv}{RESET}")
        os.execv(python_venv, [python_venv] + sys.argv)
    else:
        print(f"{AMARELO}⚠️  Pasta 'venv/' não encontrada. Rodando com Python do sistema.{RESET}")
        print(f"   Crie a venv com: {VERDE}python3 -m venv venv && source venv/bin/activate{RESET}")
        print(f"   E instale as dependências: {VERDE}pip install -r requirements.txt{RESET}\n")

if not _esta_em_venv():
    _reiniciar_em_venv()

# ══════════════════════════════════════════════════════════════════════════════
# 🟡 BLOCO 2 — DETECÇÃO DE NOVO USUÁRIO (config.json ausente)
# ══════════════════════════════════════════════════════════════════════════════
def _verificar_primeiro_uso():
    """Se config.json não existir, executa o setup.py interativo."""
    AZUL    = "\033[94m"
    VERDE   = "\033[92m"
    AMARELO = "\033[93m"
    NEGRITO = "\033[1m"
    RESET   = "\033[0m"

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
# 🟡 BLOCO 3 — OPÇÃO DE RODAR EM SEGUNDO PLANO VIA SCREEN
# Pergunta ao usuário se deseja rodar em background.
# Se sim, cria/reutiliza uma sessão screen e relança o processo dentro dela.
# ══════════════════════════════════════════════════════════════════════════════
SCREEN_NAME = "userbot"

def _verificar_screen_disponivel() -> bool:
    """Verifica se o comando 'screen' está instalado no sistema."""
    return os.system("which screen > /dev/null 2>&1") == 0

def _ja_esta_em_screen() -> bool:
    """Retorna True se o processo já está rodando dentro de uma sessão screen."""
    return "STY" in os.environ or os.environ.get("TERM") == "screen"

def _perguntar_segundo_plano():
    """Pergunta se o usuário quer rodar em segundo plano e relança via screen se sim."""
    AZUL    = "\033[94m"
    VERDE   = "\033[92m"
    AMARELO = "\033[93m"
    NEGRITO = "\033[1m"
    RESET   = "\033[0m"

    # Não pergunta se já está dentro do screen ou se foi iniciado com flag --no-screen
    if _ja_esta_em_screen() or "--no-screen" in sys.argv:
        return

    if not _verificar_screen_disponivel():
        print(f"  {AMARELO}ℹ️  'screen' não encontrado. Rodando em primeiro plano.{RESET}")
        print(f"     Instale com: {VERDE}sudo apt install screen{RESET}\n")
        return

    print(f"\n{AZUL}{NEGRITO}╔════════════════════════════════════════════╗{RESET}")
    print(f"{AZUL}{NEGRITO}║   🖥️  MODO DE EXECUÇÃO                      ║{RESET}")
    print(f"{AZUL}{NEGRITO}╚════════════════════════════════════════════╝{RESET}\n")
    print(f"  {VERDE}• Primeiro plano:{RESET} o bot para quando você fechar o terminal.")
    print(f"  {VERDE}• Segundo plano (screen):{RESET} o bot continua rodando mesmo após fechar o terminal.\n")

    resp = input(f"  ❓ Rodar em segundo plano? (S/n): ").strip().lower()

    if resp in ("", "s"):
        # Monta o comando para relançar dentro do screen
        python_exec = sys.executable
        script_path = os.path.abspath(sys.argv[0])
        pasta       = os.path.dirname(script_path)

        # Encerra sessão screen antiga com o mesmo nome, se existir
        os.system(f"screen -S {SCREEN_NAME} -X quit > /dev/null 2>&1")

        cmd = (
            f"screen -dmS {SCREEN_NAME} "
            f"bash -c 'cd {pasta} && {python_exec} {script_path} --no-screen; exec bash'"
        )
        ret = os.system(cmd)

        if ret == 0:
            print(f"\n{VERDE}✅ Bot iniciado em segundo plano na sessão screen '{SCREEN_NAME}'!{RESET}")
            print(f"\n{AZUL}{NEGRITO}  Para retornar à sessão:{RESET}")
            print(f"  {VERDE}screen -r {SCREEN_NAME}{RESET}")
            print(f"\n{AZUL}{NEGRITO}  Para sair sem encerrar o bot:{RESET}")
            print(f"  {VERDE}Ctrl+A depois D{RESET}\n")
        else:
            print(f"\n{AMARELO}⚠️  Falha ao criar sessão screen. Rodando em primeiro plano.{RESET}\n")
            return

        sys.exit(0)
    else:
        print(f"\n  {VERDE}▶ Rodando em primeiro plano...{RESET}\n")

_perguntar_segundo_plano()

# ══════════════════════════════════════════════════════════════════════════════
# 🟢 IMPORTS PRINCIPAIS (só chegam aqui se venv, config.json e screen estão OK)
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
__VERSAO__ = "1.0"
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
if _DRIVE_DISPONIVEL and config.get("DRIVE_ATIVO", False):
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
else:
    if config.get("DRIVE_ATIVO", False):
        logger.warning("⚠️ pydrive2 não instalado. Google Drive desativado.")
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

app.config      = config
app.drive       = drive
app.tempo_inicio = time.time()
app.PREFIXO     = PREFIXO
app.VERSAO      = __VERSAO__
app.UPDATE_FLAG = UPDATE_FLAG

# ══════════════════════════════════════════════════════════════════════════════
# 🟢 TRATAMENTO SILENCIOSO DE ERROS COMUNS
# ══════════════════════════════════════════════════════════════════════════════
def manipulador_erros(loop, context):
    erro = str(context.get("exception", ""))
    if any(x in erro for x in ["Peer id invalid", "Message to delete not found", "MESSAGE_NOT_MODIFIED"]):
        return
    loop.default_exception_handler(context)

# ══════════════════════════════════════════════════════════════════════════════
# 🟢 ROTINA PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
async def iniciar():
    logger.info(f"🚀 INICIANDO USERBOT PRO v{__VERSAO__}...")
    await app.start()

    # Monta texto de status do screen para o canal de logs
    em_screen = _ja_esta_em_screen()
    if em_screen:
        screen_info = (
            f"\n🖥️ **Rodando em segundo plano** (screen)\n"
            f"↩️ Para retornar: `screen -r {SCREEN_NAME}`\n"
            f"🔇 Para sair sem parar: `Ctrl+A` depois `D`"
        )
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
    await app.stop()
    logger.info("👋 Userbot encerrado.")


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(manipulador_erros)
        loop.run_until_complete(iniciar())
    except KeyboardInterrupt:
        logger.info("👋 Encerrado pelo usuário (Ctrl+C).")
