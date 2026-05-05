"""
plugins/system.py
Comandos de sistema: versao, atualizar, restart, ping, speed, sysinfo, processos
"""
import os
import sys
import time
import asyncio
import psutil
import humanize
import speedtest
import subprocess

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
      ,atualizar          → git pull padrão (aborta em conflito local)
      ,atualizar forcar   → descarta alterações locais e força sincronia com origin
    """
    partes = message.text.split(None, 1)
    forcar = len(partes) > 1 and partes[1].strip().lower() in ("forcar", "forçar", "force", "-f")
    versao_local = getattr(client, "VERSAO", "?")
    update_flag = getattr(client, "UPDATE_FLAG", ".update_pending.json")

    if not _e_repositorio_git():
        return await message.edit_text(
            "❌ **Pasta não é um repositório Git.**\n"
            "Clone o repositório com:\n"
            "`git clone https://github.com/SEU_USER/userbot.git`"
        )

    msg = await message.edit_text("🔄 **Buscando atualizações no GitHub...**")

    cod, _, err = _git("fetch", "origin", timeout=30)
    if cod != 0:
        return await msg.edit_text(f"❌ **Falha no `git fetch`:**\n```\n{err[:300]}\n```")

    _, branch, _ = _git("rev-parse", "--abbrev-ref", "HEAD")
    branch = branch or "main"

    _, atras, _ = _git("rev-list", "--count", f"HEAD..origin/{branch}")
    atras = atras or "0"
    if atras == "0" and not forcar:
        return await msg.edit_text(
            f"✅ **Userbot já está na versão mais recente!**\n"
            f"📦 v{versao_local} | branch `{branch}`"
        )

    _, diff_arquivos, _ = _git("diff", "--name-only", f"HEAD..origin/{branch}")
    arquivos = [a for a in diff_arquivos.splitlines() if a.strip()]
    requirements_mudou = any("requirements.txt" in a for a in arquivos)

    await msg.edit_text(
        f"⬇️ **Aplicando atualização** ({len(arquivos)} arquivo(s))...\n"
        f"🔀 Modo: `{'FORÇADO' if forcar else 'normal'}`"
    )
    if forcar:
        cod, _, err = _git("reset", "--hard", f"origin/{branch}")
    else:
        cod, _, err = _git("pull", "--ff-only", "origin", branch)

    if cod != 0:
        return await msg.edit_text(
            f"❌ **Falha ao aplicar atualização:**\n```\n{err[:400]}\n```\n\n"
            f"💡 Dica: tente `,atualizar forcar` para descartar alterações locais."
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
            "commit": commit_hash,
            "mensagem": commit_msg,
            "autor": commit_autor,
            "arquivos": arquivos,
            "forcado": forcar,
            "timestamp": int(time.time()),
        })
    except:
        pass

    await msg.edit_text("✅ **Atualização concluída! Reiniciando...**")
    await asyncio.sleep(2)
    try:
        await client.stop()
    except:
        pass
    os.execl(sys.executable, sys.executable, *sys.argv)


@Client.on_message(cmd_filter("restart") & filters.me)
async def cmd_restart(client, message):
    """Reinicia o userbot."""
    await message.edit_text("🔄 **Reiniciando...**")
    await asyncio.sleep(1)
    try:
        await client.stop()
    except:
        pass
    os.execl(sys.executable, sys.executable, *sys.argv)


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
        s = speedtest.Speedtest()
        s.get_best_server()
        s.download()
        s.upload()
        r = s.results.dict()
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
    """Exibe informações de CPU, RAM e disco da VM."""
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disco = psutil.disk_usage('/')
    inicio = getattr(client, "tempo_inicio", time.time())
    uptime = humanize.precisedelta(time.time() - inicio, minimum_unit="seconds")
    await message.edit_text(
        f"🖥️ **Status da VM**\n\n"
        f"⏱️ Uptime do bot: `{uptime}`\n"
        f"📈 CPU: `{cpu}%`\n"
        f"💾 RAM: `{ram.percent}%` ({humanize.naturalsize(ram.used)} / {humanize.naturalsize(ram.total)})\n"
        f"💿 Disco: `{disco.percent}%` ({humanize.naturalsize(disco.used)} / {humanize.naturalsize(disco.total)})"
    )


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
