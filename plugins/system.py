"""
plugins/system.py
Comandos de sistema: versao, atualizar, restart, ping, speed, sysinfo, processos
"""
import os
import sys
import time
import signal
import asyncio
import psutil
import humanize
import speedtest
import subprocess
import platform
import pyrogram

from pyrogram import filters, Client
from utils.helpers import cmd_filter, salvar


def _git(*args, timeout=30):
    """Wrapper seguro para chamadas git. Retorna (codigo, stdout, stderr)."""
    try:
        proc = subprocess.run(
            ["git", *args], capture_output=True, text=True, timeout=timeout
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as e:
        return 1, "", str(e)


def _e_repositorio_git():
    cod, _, _ = _git("rev-parse", "--is-inside-work-tree", timeout=5)
    return cod == 0


def _reiniciar_processo():
    """
    Reinicia o bot de forma limpa usando subprocess.
    Evita o problema de múltiplos SIGINT causado pelo os.execl dentro de handlers async.
    """
    python = sys.executable
    args   = sys.argv[:]

    # Garante que o novo processo não entre no loop de perguntar sobre screen
    if "--no-screen" not in args:
        args.append("--no-screen")

    subprocess.Popen([python] + args)
    # Encerra o processo atual de forma limpa, sem propagar SIGINT
    os.kill(os.getpid(), signal.SIGTERM)


@Client.on_message(cmd_filter("versao") & filters.me)
async def cmd_versao(client, message):
    """Mostra a versão local, a remota e o último commit."""
    versao_local = getattr(client, "VERSAO", "?")
    if not _e_repositorio_git():
        return await message.edit_text(
            f"📦 **Userbot Pro v{versao_local}**\n"
            f"⚠️ Pasta não é um repositório Git — atualização automática desativada."
        )
    await message.edit_text("🔍 **Consultando GitHub...**")
    _git("fetch", "origin", timeout=20)
    _, branch, _ = _git("rev-parse", "--abbrev-ref", "HEAD")
    branch = branch or "main"
    _, hash_local, _ = _git("rev-parse", "--short", "HEAD")
    _, hash_remoto, _ = _git("rev-parse", "--short", f"origin/{branch}")
    _, msg_local, _ = _git("log", "-1", "--pretty=%s")
    _, autor_local, _ = _git("log", "-1", "--pretty=%an")
    _, atras, _ = _git("rev-list", "--count", f"HEAD..origin/{branch}")
    atras = atras or "0"
    status = "✅ atualizado" if atras == "0" else f"🔄 {atras} commit(s) atrás"
    await message.edit_text(
        f"📦 **Userbot Pro v{versao_local}**\n\n"
        f"🌿 Branch: `{branch}`\n"
        f"🔢 Local:  `{hash_local or 'n/a'}`\n"
        f"🌐 Remoto: `{hash_remoto or 'n/a'}`\n"
        f"📈 Status: {status}\n\n"
        f"💬 Último commit local: _{msg_local or 'n/a'}_\n"
        f"👤 Autor: `{autor_local or 'n/a'}`"
    )


@Client.on_message(cmd_filter("atualizar") & filters.me)
async def cmd_atualizar(client, message):
    """
    Auto-update via GitHub.
      ,atualizar        → sempre usa git reset --hard origin/main (sem conflitos)
      ,atualizar forcar → mesmo comportamento (mantido por compatibilidade)
    """
    versao_local = getattr(client, "VERSAO", "?")
    update_flag  = getattr(client, "UPDATE_FLAG", ".update_pending.json")

    if not _e_repositorio_git():
        return await message.edit_text(
            "❌ **Pasta não é um repositório Git.**\n"
            "Clone o repositório com:\n"
            "`git clone https://github.com/SEU_USER/userbot.git`"
        )

    msg = await message.edit_text("🔄 **Buscando atualizações no GitHub...**")

    # Fetch para atualizar as refs remotas
    cod, _, err = _git("fetch", "origin", timeout=30)
    if cod != 0:
        return await msg.edit_text(f"❌ **Falha no `git fetch`:**\n```\n{err[:300]}\n```")

    _, branch, _ = _git("rev-parse", "--abbrev-ref", "HEAD")
    branch = branch or "main"

    _, atras, _ = _git("rev-list", "--count", f"HEAD..origin/{branch}")
    atras = atras or "0"
    if atras == "0":
        return await msg.edit_text(
            f"✅ **Userbot já está na versão mais recente!**\n"
            f"📦 v{versao_local} | branch `{branch}`"
        )

    _, diff_arquivos, _ = _git("diff", "--name-only", f"HEAD..origin/{branch}")
    arquivos = [a for a in diff_arquivos.splitlines() if a.strip()]
    requirements_mudou = any("requirements.txt" in a for a in arquivos)

    await msg.edit_text(
        f"⬇️ **Aplicando atualização** ({len(arquivos)} arquivo(s))...\n"
        f"🔀 Modo: `RESET HARD → origin/{branch}`"
    )

    # Usa sempre reset --hard para evitar conflitos de diverging branches
    cod, _, err = _git("reset", "--hard", f"origin/{branch}")
    if cod != 0:
        return await msg.edit_text(
            f"❌ **Falha ao aplicar atualização:**\n```\n{err[:400]}\n```"
        )

    _, commit_hash, _ = _git("rev-parse", "--short", "HEAD")
    _, commit_msg, _ = _git("log", "-1", "--pretty=%s")
    _, commit_autor, _ = _git("log", "-1", "--pretty=%an")

    if requirements_mudou:
        await msg.edit_text("📦 **Atualizando dependências...**")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"],
                capture_output=True, text=True, timeout=180
            )
        except Exception as e:
            await msg.edit_text(f"⚠️ Update aplicado, mas falhou ao atualizar libs: `{e}`")
            await asyncio.sleep(2)

    try:
        salvar(update_flag, {
            "commit":    commit_hash,
            "mensagem":  commit_msg,
            "autor":     commit_autor,
            "arquivos":  arquivos,
            "timestamp": int(time.time()),
        })
    except Exception:
        pass

    await msg.edit_text("✅ **Atualização concluída! Reiniciando...**")
    await asyncio.sleep(2)

    # Reinicia de forma limpa (sem múltiplos SIGINT)
    _reiniciar_processo()


@Client.on_message(cmd_filter("restart") & filters.me)
async def cmd_restart(client, message):
    """Reinicia o userbot."""
    await message.edit_text("🔄 **Reiniciando...**")
    await asyncio.sleep(1)
    _reiniciar_processo()


@Client.on_message(cmd_filter("ping") & filters.me)
async def cmd_ping(client, message):
    """Mede a latência do bot."""
    inicio = time.time()
    await message.edit_text("⏳")
    delta = (time.time() - inicio) * 1000
    await message.edit_text(f"🚀 **Pong!** `{delta:.0f}ms`")


@Client.on_message(cmd_filter("speed") & filters.me)
async def cmd_speed(client, message):
    """Testa a velocidade da internet da VM."""
    await message.edit_text("🚀 **Testando velocidade...**")
    try:
        def run_speedtest():
            st = speedtest.Speedtest()
            st.get_best_server()
            st.download()
            st.upload()
            return st.results.dict()
            
        r = await asyncio.to_thread(run_speedtest)
        await message.edit_text(
            f"🚀 **Velocidade da Rede**\n\n"
            f"⬇️ Download: `{r['download']/10**6:.2f} Mbps`\n"
            f"⬆️ Upload: `{r['upload']/10**6:.2f} Mbps`\n"
            f"📡 Ping: `{r['ping']:.1f} ms`\n"
            f"🌐 Servidor: `{r['server']['name']}`"
        )
    except Exception as e:
        await message.edit_text(f"❌ Erro: `{e}`")


@Client.on_message(cmd_filter("sysinfo") & filters.me)
async def cmd_sysinfo(client, message):
    """Exibe informações do sistema no estilo neofetch."""
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()
    disco = psutil.disk_usage('/')
    
    inicio = getattr(client, "tempo_inicio", time.time())
    uptime_bot = humanize.precisedelta(time.time() - inicio, minimum_unit="seconds")
    uptime_os = humanize.precisedelta(time.time() - psutil.boot_time(), minimum_unit="minutes")
    
    os_info = f"{platform.system()} {platform.release()} ({platform.machine()})"
    py_ver = platform.python_version()
    pyro_ver = pyrogram.__version__
    versao = getattr(client, "VERSAO", "1.0")

    texto = (
        f"💻 **System Info (Neofetch)**\n\n"
        f"```text\n"
        f"OS       : {os_info}\n"
        f"Bot Up   : {uptime_bot}\n"
        f"Sys Up   : {uptime_os}\n"
        f"CPU      : {psutil.cpu_count(logical=True)} Cores @ {cpu}%\n"
        f"RAM      : {humanize.naturalsize(ram.used)} / {humanize.naturalsize(ram.total)} ({ram.percent}%)\n"
        f"Disk     : {humanize.naturalsize(disco.used)} / {humanize.naturalsize(disco.total)} ({disco.percent}%)\n"
        f"Python   : {py_ver}\n"
        f"Pyrogram : {pyro_ver}\n"
        f"Userbot  : v{versao}\n"
        f"```"
    )
    await message.edit_text(texto)


@Client.on_message(cmd_filter("processos") & filters.me)
async def cmd_processos(client, message):
    """Lista os 5 processos que mais consomem CPU."""
    procs = sorted(
        psutil.process_iter(['pid', 'name', 'cpu_percent']),
        key=lambda x: x.info['cpu_percent'] or 0,
        reverse=True
    )[:5]
    txt = "🔍 **Top 5 Processos (CPU)**\n\n"
    for p in procs:
        txt += f"• `{p.info['name']}` | PID `{p.info['pid']}` | CPU `{p.info['cpu_percent']}%`\n"
    await message.edit_text(txt)
