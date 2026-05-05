"""
🚀 USERBOT PRO v1.0 - main.py
Núcleo central que carrega configurações, conecta ao Google Drive
e inicializa o cliente Pyrogram com os plugins.
"""
import os
import sys
import json
import time
import logging
import asyncio

from pyrogram import Client, idle
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# ==========================================
# 🟢 IDENTIDADE DO PROJETO
# ==========================================
__VERSAO__ = "1.0"
UPDATE_FLAG = ".update_pending.json"

# ==========================================
# 🟢 LOGS COLORIDOS NO TERMINAL
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("UserbotCore")

# Silencia logs verbosos do Pyrogram
logging.getLogger("pyrogram").setLevel(logging.WARNING)

# ==========================================
# 🟢 CARREGAMENTO DE CONFIGURAÇÕES
# ==========================================
if not os.path.exists("config.json"):
    logger.error("❌ config.json não encontrado! Execute: python3 setup.py")
    sys.exit(1)

try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
except json.JSONDecodeError as e:
    logger.error(f"❌ config.json está malformado: {e}")
    sys.exit(1)

PREFIXO = config.get("PREFIXO", ",")
logger.info(f"🔧 Prefixo carregado: '{PREFIXO}'")

# ==========================================
# 🟢 AUTENTICAÇÃO GOOGLE DRIVE
# ==========================================
drive = None
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

# ==========================================
# 🟢 INICIALIZAÇÃO DO CLIENTE PYROGRAM
# ==========================================
os.makedirs("plugins", exist_ok=True)

app = Client(
    "meu_userbot",
    api_id=config["API_ID"],
    api_hash=config["API_HASH"],
    device_model="Samsung Galaxy S25",
    system_version="Android 14",
    plugins=dict(root="plugins")  # Carrega automaticamente todos os arquivos da pasta plugins/
)

# Anexa objetos globais ao cliente para que os plugins possam acessá-los
app.config = config
app.drive = drive
app.tempo_inicio = time.time()
app.PREFIXO = PREFIXO
app.VERSAO = __VERSAO__
app.UPDATE_FLAG = UPDATE_FLAG

# ==========================================
# 🟢 TRATAMENTO SILENCIOSO DE ERROS COMUNS
# ==========================================
def manipulador_erros(loop, context):
    erro = str(context.get("exception", ""))
    if any(x in erro for x in ["Peer id invalid", "Message to delete not found", "MESSAGE_NOT_MODIFIED"]):
        return
    loop.default_exception_handler(context)

# ==========================================
# 🟢 ROTINA PRINCIPAL
# ==========================================
async def iniciar():
    logger.info(f"🚀 INICIANDO USERBOT PRO v{__VERSAO__}...")
    await app.start()

    # Aviso de inicialização no canal de logs
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
