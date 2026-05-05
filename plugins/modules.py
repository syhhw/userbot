"""
🚀 USERBOT PRO v1.0 - plugins/modules.py
Módulo único contendo TODOS os comandos do userbot.
Arquitetura: cada handler usa um filtro de prefixo dinâmico
que lê o PREFIXO do cliente em tempo real.
"""
import os
import re
import sys
import time
import json
import psutil
import requests
import humanize
import asyncio
import random
import textwrap
import speedtest
import subprocess

from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
from pyrogram import filters, enums, Client
from pyrogram.types import ChatPermissions
from pyrogram.errors import FloodWait
from deep_translator import GoogleTranslator

# ==========================================
# 🛠️ FUNÇÕES AUXILIARES
# ==========================================

def salvar(arquivo, dados):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

def carregar(arquivo, padrao):
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return padrao

def prefixo(client):
    return getattr(client, "PREFIXO", ",")

def cmd_filter(nome):
    """
    Cria um filtro que valida dinamicamente o prefixo do cliente.
    O filtro é assíncrono e recebe (flt, client, message).
    """
    async def func(flt, client, message):
        if not message.text:
            return False
        p = prefixo(client)
        # Aceita: ",cmd" ou ",cmd argumento"
        return message.text == f"{p}{nome}" or message.text.startswith(f"{p}{nome} ")
    return filters.create(func)

# ==========================================
# 🛡️ CACHE DE ADMIN E AUDITORIA
# ==========================================

async def verificar_admin(client, chat_id):
    """Verifica se o userbot é admin no chat. Cache de 15 dias."""
    agora = time.time()
    cid = str(chat_id)
    cache = carregar("admin_cache.json", {})
    if cid in cache and agora - cache[cid].get("checado_em", 0) < 1296000:
        return cache[cid].get("is_admin", False)
    try:
        m = await client.get_chat_member(chat_id, "me")
        is_admin = m.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
        cache[cid] = {"is_admin": is_admin, "checado_em": agora, "era_admin": is_admin}
        salvar("admin_cache.json", cache)
        return is_admin
    except:
        return False

async def auditoria(client, acao, user, chat, motivo=None, msg_orig=None):
    """Envia log detalhado de moderação para o canal de logs."""
    cfg = getattr(client, "config", {})
    log_id = cfg.get("ID_CANAL_LOGS")
    if not log_id:
        return
    nome = getattr(user, "first_name", "Desconhecido") if user else "Desconhecido"
    uid = getattr(user, "id", "?") if user else "?"
    chat_titulo = getattr(chat, "title", "Chat Privado")
    txt = (
        f"🛡️ **AUDITORIA DE MODERAÇÃO**\n\n"
        f"⚙️ **Ação:** `{acao}`\n"
        f"👤 **Alvo:** {nome} (`{uid}`)\n"
        f"📍 **Chat:** {chat_titulo}\n"
    )
    if motivo:
        txt += f"📝 **Motivo:** `{motivo}`\n"
    if msg_orig:
        conteudo = msg_orig.text or msg_orig.caption or "[Mídia]"
        txt += f"\n💬 **Mensagem original:**\n`{conteudo[:400]}`"
    try:
        await client.send_message(log_id, txt)
    except:
        pass

# ==========================================
# 📂 GOOGLE DRIVE - HELPERS
# ==========================================

CATEGORIAS = {
    '.apk': 'Apps', '.zip': 'Zips', '.rar': 'Zips', '.7z': 'Zips',
    '.exe': 'Windows', '.msi': 'Windows',
    '.mp4': 'Videos', '.mkv': 'Videos', '.avi': 'Videos',
    '.mp3': 'Audios', '.ogg': 'Audios', '.wav': 'Audios',
    '.pdf': 'Docs', '.docx': 'Docs', '.txt': 'Docs',
    '.jpg': 'Fotos', '.jpeg': 'Fotos', '.png': 'Fotos', '.gif': 'Fotos'
}

CACHE_PASTAS = {}

def obter_pasta(client, nome):
    """Retorna ID da pasta no Drive, criando se não existir. Usa cache."""
    if nome in CACHE_PASTAS:
        return CACHE_PASTAS[nome]
    drive = getattr(client, "drive", None)
    cfg = getattr(client, "config", {})
    raiz = cfg.get("ID_PASTA_RAIZ_DRIVE")
    if not drive:
        return raiz
    query = f"'{raiz}' in parents and title = '{nome}' and trashed = false"
    pastas = drive.ListFile({'q': query}).GetList()
    if pastas:
        CACHE_PASTAS[nome] = pastas[0]['id']
        return pastas[0]['id']
    nova = drive.CreateFile({
        'title': nome,
        'parents': [{'id': raiz}],
        'mimeType': 'application/vnd.google-apps.folder'
    })
    nova.Upload()
    CACHE_PASTAS[nome] = nova['id']
    return nova['id']

# Estado Global
ULTIMA_BUSCA = {}
AFK_ATIVO = False
AFK_MOTIVO = ""

# ==========================================
# 🔄 ATUALIZAÇÃO & SISTEMA
# ==========================================

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
    Auto-update via GitHub. Uso:
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

    # 1) fetch para conhecer o estado remoto
    cod, _, err = _git("fetch", "origin", timeout=30)
    if cod != 0:
        return await msg.edit_text(f"❌ **Falha no `git fetch`:**\n```\n{err[:300]}\n```")

    # 2) descobrir branch atual
    _, branch, _ = _git("rev-parse", "--abbrev-ref", "HEAD")
    branch = branch or "main"

    # 3) quantos commits estamos atrás
    _, atras, _ = _git("rev-list", "--count", f"HEAD..origin/{branch}")
    atras = atras or "0"
    if atras == "0" and not forcar:
        return await msg.edit_text(
            f"✅ **Userbot já está na versão mais recente!**\n"
            f"📦 v{versao_local} | branch `{branch}`"
        )

    # 4) lista de arquivos que serão alterados
    _, diff_arquivos, _ = _git("diff", "--name-only", f"HEAD..origin/{branch}")
    arquivos = [a for a in diff_arquivos.splitlines() if a.strip()]
    requirements_mudou = any("requirements.txt" in a for a in arquivos)

    # 5) aplicar atualização
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

    # 6) coletar metadados do commit aplicado
    _, commit_hash, _ = _git("rev-parse", "--short", "HEAD")
    _, commit_msg, _ = _git("log", "-1", "--pretty=%s")
    _, commit_autor, _ = _git("log", "-1", "--pretty=%an")

    # 7) atualizar dependências se requirements.txt mudou
    if requirements_mudou:
        await msg.edit_text("📦 **Atualizando dependências (`pip install -r requirements.txt`)...**")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"],
                capture_output=True, text=True, timeout=180
            )
        except Exception as e:
            await msg.edit_text(
                f"⚠️ Update aplicado, mas falhou ao atualizar libs: `{e}`\n\nReiniciando mesmo assim..."
            )
            await asyncio.sleep(2)

    # 8) gravar flag para o main.py mandar relatório rico após o restart
    try:
        salvar(update_flag, {
            "commit": commit_hash,
            "mensagem": commit_msg,
            "autor": commit_autor,
            "arquivos": arquivos,
            "forcado": forcar,
            "timestamp": int(time.time()),
        })
    except Exception:
        pass

    # 9) preview no chat e aviso no canal de logs
    preview = "\n".join([f"  • `{a}`" for a in arquivos[:8]])
    if len(arquivos) > 8:
        preview += f"\n  • ... e mais {len(arquivos) - 8}"
    await msg.edit_text(
        f"✅ **Atualização aplicada!**\n\n"
        f"🔢 Commit: `{commit_hash}`\n"
        f"💬 _{commit_msg}_\n"
        f"👤 `{commit_autor}`\n"
        f"📁 Arquivos ({len(arquivos)}):\n{preview}\n\n"
        f"🔄 **Reiniciando em 2s...**"
    )

    cfg = getattr(client, "config", {})
    log_id = cfg.get("ID_CANAL_LOGS")
    if log_id:
        try:
            await client.send_message(
                log_id,
                f"🔄 **AUTO-UPDATE INICIADO**\n"
                f"Commit `{commit_hash}` por `{commit_autor}`\n"
                f"Reiniciando processo..."
            )
        except:
            pass

    await asyncio.sleep(2)
    try:
        await client.stop()
    except:
        pass
    os.execl(sys.executable, sys.executable, *sys.argv)


@Client.on_message(cmd_filter("restart") & filters.me)
async def cmd_restart(client, message):
    await message.edit_text("🔄 **Reiniciando...**")
    await asyncio.sleep(1)
    try:
        await client.stop()
    except:
        pass
    os.execl(sys.executable, sys.executable, *sys.argv)

@Client.on_message(cmd_filter("ping") & filters.me)
async def cmd_ping(client, message):
    inicio = time.time()
    await message.edit_text("⏳")
    delta = (time.time() - inicio) * 1000
    await message.edit_text(f"🚀 **Pong!** `{delta:.0f}ms`")

@Client.on_message(cmd_filter("speed") & filters.me)
async def cmd_speed(client, message):
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
    procs = sorted(
        psutil.process_iter(['pid', 'name', 'cpu_percent']),
        key=lambda x: x.info['cpu_percent'] or 0,
        reverse=True
    )[:5]
    txt = "🔍 **Top 5 Processos (CPU)**\n\n"
    for p in procs:
        txt += f"• `{p.info['name']}` | PID `{p.info['pid']}` | CPU `{p.info['cpu_percent']}%`\n"
    await message.edit_text(txt)

# ==========================================
# 📂 GOOGLE DRIVE - COMANDOS
# ==========================================

@Client.on_message(cmd_filter("status") & filters.me)
async def drive_status(client, message):
    drive = getattr(client, "drive", None)
    if not drive:
        return await message.edit_text("❌ Drive não conectado.")
    try:
        sobre = drive.GetAbout()
        total = int(sobre['quotaBytesTotal'])
        usado = int(sobre['quotaBytesUsedAggregate'])
        pct = (usado / total) * 100
        barras = "".join(["🟥" if i < int(pct // 10) else "🟩" for i in range(10)])
        await message.edit_text(
            f"📊 **Google Drive**\n\n"
            f"`[{barras}]` {pct:.1f}%\n"
            f"☁️ `{humanize.naturalsize(usado)}` / `{humanize.naturalsize(total)}`"
        )
    except Exception as e:
        await message.edit_text(f"❌ Erro: `{e}`")

@Client.on_message(cmd_filter("organizar") & filters.me)
async def drive_organizar(client, message):
    drive = getattr(client, "drive", None)
    if not drive:
        return await message.edit_text("❌ Drive não conectado.")
    cfg = getattr(client, "config", {})
    raiz = cfg.get("ID_PASTA_RAIZ_DRIVE")
    msg = await message.edit_text("📂 **Organizando arquivos no Drive...**")
    try:
        query = f"'{raiz}' in parents and trashed=false and mimeType != 'application/vnd.google-apps.folder'"
        arquivos = drive.ListFile({'q': query}).GetList()
        movidos = 0
        for arq in arquivos:
            ext = os.path.splitext(arq['title'])[1].lower()
            categoria = CATEGORIAS.get(ext, 'Outros')
            id_destino = obter_pasta(client, categoria)
            arq['parents'] = [{'id': id_destino}]
            arq.Upload()
            movidos += 1
        await msg.edit_text(f"✅ **Organização concluída!**\n📦 `{movidos}` arquivos movidos.")
    except Exception as e:
        await msg.edit_text(f"❌ Erro: `{e}`")

@Client.on_message(cmd_filter("get") & filters.me)
async def drive_get(client, message):
    drive = getattr(client, "drive", None)
    if not drive:
        return await message.edit_text("❌ Drive não conectado.")
    partes = message.text.split(None, 1)
    if len(partes) < 2:
        return await message.edit_text(f"⚠️ Use: `{prefixo(client)}get [URL]`")
    url = partes[1].strip()
    msg = await message.edit_text("📥 **Baixando arquivo da URL...**")
    try:
        nome = url.split("/")[-1].split("?")[0] or "arquivo"
        local = os.path.join("/tmp", nome)
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(local, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)
        ext = os.path.splitext(nome)[1].lower()
        categoria = CATEGORIAS.get(ext, 'Outros')
        id_pasta = obter_pasta(client, categoria)
        f_drive = drive.CreateFile({'title': nome, 'parents': [{'id': id_pasta}]})
        f_drive.SetContentFile(local)
        f_drive.Upload()
        f_drive.InsertPermission({'type': 'anyone', 'value': 'anyone', 'role': 'reader'})
        os.remove(local)
        await msg.edit_text(
            f"✅ **Upload concluído!**\n"
            f"📁 `{nome}` → `{categoria}`\n"
            f"🔗 [Abrir no Drive]({f_drive['alternateLink']})"
        )
    except Exception as e:
        await msg.edit_text(f"❌ Erro: `{e}`")

@Client.on_message(cmd_filter("direto") & filters.me)
async def drive_direto(client, message):
    drive = getattr(client, "drive", None)
    if not drive:
        return await message.edit_text("❌ Drive não conectado.")
    partes = message.text.split(None, 1)
    if len(partes) < 2:
        return await message.edit_text(f"⚠️ Use: `{prefixo(client)}direto [nome do arquivo]`")
    termo = partes[1].strip()
    try:
        arquivos = drive.ListFile({'q': f"title = '{termo}' and trashed=false"}).GetList()
        if not arquivos:
            return await message.edit_text("❌ Arquivo não encontrado.")
        f = arquivos[0]
        link = f"https://drive.google.com/uc?export=download&id={f['id']}"
        await message.edit_text(f"🔗 **Link Direto**\n\n📁 `{f['title']}`\n`{link}`")
    except Exception as e:
        await message.edit_text(f"❌ Erro: `{e}`")

@Client.on_message(cmd_filter("procurar") & filters.me)
async def drive_procurar(client, message):
    drive = getattr(client, "drive", None)
    if not drive:
        return await message.edit_text("❌ Drive não conectado.")
    p = prefixo(client)
    partes = message.text.split(None, 1)
    if len(partes) < 2:
        return await message.edit_text(f"⚠️ Use: `{p}procurar [termo]`")
    termo = partes[1].strip()
    await message.edit_text(f"🔎 **Procurando:** `{termo}`...")
    try:
        arquivos = drive.ListFile({'q': f"title contains '{termo}' and trashed=false"}).GetList()
        if not arquivos:
            return await message.edit_text("❌ Nenhum arquivo encontrado.")
        global ULTIMA_BUSCA
        ULTIMA_BUSCA = {}
        txt = f"🔎 **Resultados para '{termo}':**\n\n"
        for i, arq in enumerate(arquivos[:10], 1):
            ULTIMA_BUSCA[str(i)] = {'id': arq['id'], 'title': arq['title']}
            tam = humanize.naturalsize(int(arq.get('fileSize', 0))) if arq.get('fileSize') else "Pasta"
            txt += f"**[{i}]** `{arq['title']}` ({tam})\n"
        txt += f"\n💡 Use `{p}apagar [N]` para excluir."
        await message.edit_text(txt)
    except Exception as e:
        await message.edit_text(f"❌ Erro: `{e}`")

@Client.on_message(cmd_filter("apagar") & filters.me)
async def drive_apagar(client, message):
    drive = getattr(client, "drive", None)
    if not drive:
        return await message.edit_text("❌ Drive não conectado.")
    p = prefixo(client)
    partes = message.text.split(None, 1)
    if len(partes) < 2:
        return await message.edit_text(f"⚠️ Use: `{p}apagar [N]` (após `{p}procurar`)")
    num = partes[1].strip()
    global ULTIMA_BUSCA
    if num not in ULTIMA_BUSCA:
        return await message.edit_text("❌ Número inválido. Faça uma busca primeiro.")
    item = ULTIMA_BUSCA[num]
    try:
        f = drive.CreateFile({'id': item['id']})
        f.Trash()
        await message.edit_text(f"🗑️ **Movido para a lixeira:**\n📁 `{item['title']}`")
        del ULTIMA_BUSCA[num]
    except Exception as e:
        await message.edit_text(f"❌ Erro: `{e}`")

# ==========================================
# 👮 MODERAÇÃO
# ==========================================

async def resolver_alvo(client, message):
    """
    Resolve o alvo de um comando de moderação aceitando 3 formatos:
      1. Resposta a uma mensagem (reply)
      2. @username como argumento
      3. ID numérico como argumento
    Retorna (user_obj, motivo, msg_origem) ou (None, None, None) se não encontrar.
    """
    partes = message.text.split(None, 2)
    user_obj = None
    motivo = None
    msg_origem = None

    if message.reply_to_message and message.reply_to_message.from_user:
        user_obj = message.reply_to_message.from_user
        msg_origem = message.reply_to_message
        if len(partes) > 1:
            motivo = " ".join(partes[1:])
    elif len(partes) > 1:
        alvo = partes[1].strip()
        if len(partes) > 2:
            motivo = partes[2]
        try:
            if alvo.startswith("@"):
                user_obj = await client.get_users(alvo)
            else:
                user_obj = await client.get_users(int(alvo))
        except (ValueError, Exception):
            return None, None, None
    return user_obj, motivo, msg_origem

@Client.on_message(cmd_filter("ban") & filters.me)
async def cmd_ban(client, message):
    user, motivo, msg_orig = await resolver_alvo(client, message)
    if not user:
        return await message.edit_text(
            f"⚠️ Use: responda à mensagem, ou `{prefixo(client)}ban @user` ou `{prefixo(client)}ban 12345678`"
        )
    try:
        await client.ban_chat_member(message.chat.id, user.id)
        txt = f"🔨 **Banido:** {user.first_name} (`{user.id}`)"
        if motivo:
            txt += f"\n📝 Motivo: `{motivo}`"
        await message.edit_text(txt)
        await auditoria(client, "BAN", user, message.chat, motivo=motivo, msg_orig=msg_orig)
    except Exception as e:
        await message.edit_text(f"❌ Erro: `{e}`")

@Client.on_message(cmd_filter("unban") & filters.me)
async def cmd_unban(client, message):
    user, _, _ = await resolver_alvo(client, message)
    if not user:
        return await message.edit_text(
            f"⚠️ Use: responda à mensagem, ou `{prefixo(client)}unban @user` ou `{prefixo(client)}unban 12345678`"
        )
    try:
        await client.unban_chat_member(message.chat.id, user.id)
        await message.edit_text(f"✅ **Desbanido:** {user.first_name} (`{user.id}`)")
    except Exception as e:
        await message.edit_text(f"❌ Erro: `{e}`")

@Client.on_message(cmd_filter("mute") & filters.me)
async def cmd_mute(client, message):
    user, motivo, msg_orig = await resolver_alvo(client, message)
    if not user:
        return await message.edit_text(
            f"⚠️ Use: responda à mensagem, ou `{prefixo(client)}mute @user` ou `{prefixo(client)}mute 12345678`"
        )
    try:
        await client.restrict_chat_member(
            message.chat.id, user.id,
            ChatPermissions(can_send_messages=False)
        )
        txt = f"🔇 **Silenciado:** {user.first_name} (`{user.id}`)"
        if motivo:
            txt += f"\n📝 Motivo: `{motivo}`"
        await message.edit_text(txt)
        await auditoria(client, "MUTE", user, message.chat, motivo=motivo, msg_orig=msg_orig)
    except Exception as e:
        await message.edit_text(f"❌ Erro: `{e}`")

@Client.on_message(cmd_filter("unmute") & filters.me)
async def cmd_unmute(client, message):
    user, _, _ = await resolver_alvo(client, message)
    if not user:
        return await message.edit_text(
            f"⚠️ Use: responda à mensagem, ou `{prefixo(client)}unmute @user` ou `{prefixo(client)}unmute 12345678`"
        )
    try:
        await client.restrict_chat_member(
            message.chat.id, user.id,
            ChatPermissions(
                can_send_messages=True, can_send_media_messages=True,
                can_send_other_messages=True, can_add_web_page_previews=True
            )
        )
        await message.edit_text(f"🔊 **Desmutado:** {user.first_name} (`{user.id}`)")
    except Exception as e:
        await message.edit_text(f"❌ Erro: `{e}`")

@Client.on_message(cmd_filter("del") & filters.me)
async def cmd_del(client, message):
    if not message.reply_to_message:
        return await message.delete()
    try:
        await message.reply_to_message.delete()
        await message.delete()
    except:
        pass

@Client.on_message(cmd_filter("purge") & filters.me)
async def cmd_purge(client, message):
    if not message.reply_to_message:
        return await message.edit_text("⚠️ Responda à mensagem inicial para apagar a partir dela.")
    chat_id = message.chat.id
    msg_id_inicio = message.reply_to_message.id
    msg_id_fim = message.id
    try:
        ids = list(range(msg_id_inicio, msg_id_fim + 1))
        # Apaga em lotes de 100 (limite do Telegram)
        for i in range(0, len(ids), 100):
            await client.delete_messages(chat_id, ids[i:i+100])
        aviso = await client.send_message(chat_id, f"🧹 **Purge:** {len(ids)} mensagens apagadas.")
        await asyncio.sleep(3)
        await aviso.delete()
    except Exception as e:
        await message.edit_text(f"❌ Erro: `{e}`")

@Client.on_message(cmd_filter("admins") & filters.me)
async def cmd_admins(client, message):
    await message.edit_text("👮 **Listando administradores...**")
    try:
        txt = f"👮 **Admins de {message.chat.title}:**\n\n"
        async for m in client.get_chat_members(message.chat.id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
            cargo = "👑" if m.status == enums.ChatMemberStatus.OWNER else "🛡️"
            txt += f"{cargo} **{m.user.first_name}** (`{m.user.id}`)\n"
        await message.edit_text(txt)
    except Exception as e:
        await message.edit_text(f"❌ Erro: `{e}`")

@Client.on_message(cmd_filter("zombies") & filters.me)
async def cmd_zombies(client, message):
    msg = await message.edit_text("🧟 **Iniciando varredura de contas excluídas...**")
    if not await verificar_admin(client, message.chat.id):
        return await msg.edit_text("⚠️ Você não é admin neste grupo.")
    removidos, total = 0, 0
    try:
        async for m in client.get_chat_members(message.chat.id):
            total += 1
            if m.user.is_deleted:
                try:
                    await client.ban_chat_member(message.chat.id, m.user.id)
                    await asyncio.sleep(0.3)
                    await client.unban_chat_member(message.chat.id, m.user.id)
                    removidos += 1
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                except:
                    pass
        await msg.edit_text(
            f"🧟 **Limpeza Concluída!**\n\n"
            f"👥 Membros analisados: `{total}`\n"
            f"🗑️ Zumbis removidos: `{removidos}`"
        )
    except Exception as e:
        await msg.edit_text(f"❌ Erro: `{e}`")

@Client.on_message(cmd_filter("gban") & filters.me)
async def cmd_gban(client, message):
    user, motivo, msg_orig = await resolver_alvo(client, message)
    if not user:
        return await message.edit_text(
            f"⚠️ Use: responda à mensagem, ou `{prefixo(client)}gban @user` ou `{prefixo(client)}gban 12345678`"
        )
    aviso = await message.edit_text(f"🌍 **GBAN em andamento:** {user.first_name} (`{user.id}`)")
    sucesso = 0
    async for d in client.get_dialogs():
        if d.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            if await verificar_admin(client, d.chat.id):
                try:
                    await client.ban_chat_member(d.chat.id, user.id)
                    sucesso += 1
                    if sucesso % 5 == 0:
                        await asyncio.sleep(1)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                except:
                    pass
    await auditoria(client, "GBAN", user, message.chat, motivo or "Banimento Global", msg_orig)
    await aviso.edit_text(
        f"☢️ **GBAN concluído!**\n"
        f"👤 Alvo: {user.first_name} (`{user.id}`)\n"
        f"🔨 Banido em `{sucesso}` grupos."
    )

@Client.on_message(cmd_filter("fban") & filters.me)
async def cmd_fban(client, message):
    user_obj, motivo, msg_orig = await resolver_alvo(client, message)
    if not user_obj:
        return await message.edit_text(
            f"⚠️ Use: responda à mensagem, ou `{prefixo(client)}fban @user [motivo]` ou `{prefixo(client)}fban 12345678 [motivo]`"
        )
    user_id = user_obj.id
    if not motivo:
        motivo = "Spam / Violação de regras"
    feds = carregar("feds.json", [])
    if not feds:
        return await message.edit_text("⚠️ Nenhuma federação cadastrada. Use `,addfed` em grupos administrativos.")
    await message.edit_text(f"📡 **Executando FBAN em `{user_id}`...**")
    sucesso = 0
    for fid in feds:
        try:
            await client.send_message(fid, f"/fban {user_id} {motivo}")
            sucesso += 1
            await asyncio.sleep(0.5)
        except:
            pass
    await message.edit_text(
        f"☢️ **FBAN concluído.**\n"
        f"👤 Alvo: `{user_id}`\n"
        f"📝 Motivo: `{motivo}`\n"
        f"📡 Federações: `{sucesso}`"
    )
    if user_obj:
        await auditoria(client, "FBAN", user_obj, message.chat, motivo, msg_orig)

@Client.on_message(cmd_filter("addfed") & filters.me)
async def cmd_addfed(client, message):
    feds = carregar("feds.json", [])
    if message.chat.id in feds:
        return await message.edit_text("⚠️ Este grupo já está cadastrado.")
    feds.append(message.chat.id)
    salvar("feds.json", feds)
    await message.edit_text(f"✅ **Grupo adicionado à federação.**\n📍 ID: `{message.chat.id}`")

@Client.on_message(cmd_filter("delfed") & filters.me)
async def cmd_delfed(client, message):
    feds = carregar("feds.json", [])
    if message.chat.id not in feds:
        return await message.edit_text("⚠️ Este grupo não está cadastrado.")
    feds.remove(message.chat.id)
    salvar("feds.json", feds)
    await message.edit_text("✅ **Grupo removido da federação.**")

@Client.on_message(cmd_filter("feds") & filters.me)
async def cmd_feds(client, message):
    feds = carregar("feds.json", [])
    if not feds:
        return await message.edit_text("⚠️ Nenhuma federação cadastrada.")
    txt = f"📡 **Federações ({len(feds)}):**\n\n"
    for fid in feds:
        try:
            chat = await client.get_chat(fid)
            txt += f"• **{chat.title}** (`{fid}`)\n"
        except:
            txt += f"• `{fid}` (inacessível)\n"
    await message.edit_text(txt)

# ==========================================
# 🛠️ FERRAMENTAS & DIVERSÃO
# ==========================================

@Client.on_message(cmd_filter("hack") & filters.me)
async def cmd_hack(client, message):
    alvo = message.reply_to_message.from_user.first_name if message.reply_to_message else "SISTEMA"
    passos = [
        f"💀 **TARGET LOCKED:** `{alvo}`\n🔍 Scanning open ports...",
        f"🌐 `[▰▰▱▱▱▱▱▱▱▱]` 20%\n🔓 Bypassing firewall...",
        f"🔑 `[▰▰▰▰▱▱▱▱▱▱]` 40%\n💉 Injecting SQL payload...",
        f"🔥 `[▰▰▰▰▰▰▱▱▱▱]` 60%\n🔐 Brute-forcing SSH...",
        f"⚡ `[▰▰▰▰▰▰▰▰▱▱]` 80%\n🖥️ Root access granted!",
        f"☢️ `[▰▰▰▰▰▰▰▰▰▰]` 100%\n\n💀 **HACK COMPLETO**\n🎯 `{alvo}` comprometido.\n🔒 Sistema sob controle."
    ]
    for passo in passos:
        try:
            await message.edit_text(passo)
            await asyncio.sleep(random.uniform(0.9, 1.5))
        except:
            pass

@Client.on_message(cmd_filter("type") & filters.me)
async def cmd_type(client, message):
    p = prefixo(client)
    partes = message.text.split(None, 1)
    if len(partes) < 2:
        return await message.edit_text(f"⚠️ Use: `{p}type [texto]`")
    texto = partes[1]
    digitado = ""
    for ch in texto:
        digitado += ch
        try:
            await message.edit_text(f"{digitado}▌")
            await asyncio.sleep(0.07)
        except:
            pass
    await message.edit_text(digitado)

@Client.on_message(cmd_filter("ghost") & filters.me)
async def cmd_ghost(client, message):
    p = prefixo(client)
    partes = message.text.split(None, 2)
    if len(partes) < 3:
        return await message.edit_text(f"⚠️ Use: `{p}ghost [segundos] [texto]`")
    if not partes[1].isdigit():
        return await message.edit_text(f"⚠️ Tempo inválido. Ex: `{p}ghost 10 Olá`")
    tempo = int(partes[1])
    texto = partes[2]
    await message.edit_text(f"👻 **[Autodestrutiva em {tempo}s]**\n\n{texto}")
    await asyncio.sleep(tempo)
    try:
        await message.delete()
    except:
        pass

@Client.on_message(cmd_filter("fake") & filters.me)
async def cmd_fake(client, message):
    p = prefixo(client)
    partes = message.text.split(None, 1)
    if len(partes) < 2:
        return await message.edit_text(f"⚠️ Use: `{p}fake [audio|video|typing]`")
    tipo = partes[1].strip().lower()
    try:
        await message.delete()
    except:
        pass
    if tipo == "audio":
        acao = enums.ChatAction.RECORD_AUDIO
    elif tipo == "video":
        acao = enums.ChatAction.RECORD_VIDEO
    else:
        acao = enums.ChatAction.TYPING
    for _ in range(4):
        try:
            await client.send_chat_action(message.chat.id, acao)
            await asyncio.sleep(5)
        except:
            break

@Client.on_message(cmd_filter("tr") & filters.me)
async def cmd_tr(client, message):
    if not message.reply_to_message:
        return await message.edit_text("⚠️ Responda ao texto a traduzir.")
    partes = message.text.split(None, 1)
    alvo = partes[1].strip() if len(partes) > 1 else "pt"
    texto = message.reply_to_message.text or message.reply_to_message.caption
    if not texto:
        return await message.edit_text("⚠️ Mensagem sem texto.")
    await message.edit_text(f"🌐 **Traduzindo para `{alvo}`...**")
    try:
        res = GoogleTranslator(source='auto', target=alvo).translate(texto)
        await message.edit_text(f"🌐 **Tradução ({alvo.upper()}):**\n\n{res}")
    except Exception as e:
        await message.edit_text(f"❌ Erro: `{e}`")

@Client.on_message(cmd_filter("voz") & filters.me)
async def cmd_voz(client, message):
    p = prefixo(client)
    partes = message.text.split(None, 1)
    if len(partes) > 1:
        texto = partes[1]
    elif message.reply_to_message and (message.reply_to_message.text or message.reply_to_message.caption):
        texto = message.reply_to_message.text or message.reply_to_message.caption
    else:
        return await message.edit_text(f"⚠️ Use: `{p}voz [texto]` ou responda a uma mensagem.")
    await message.edit_text("🎙️ **Gerando áudio...**")
    arquivo = "voz_temp.ogg"
    try:
        tts = gTTS(text=texto, lang='pt')
        tts.save(arquivo)
        await client.send_voice(message.chat.id, arquivo)
        os.remove(arquivo)
        await message.delete()
    except Exception as e:
        await message.edit_text(f"❌ Erro: `{e}`")
        if os.path.exists(arquivo):
            os.remove(arquivo)

@Client.on_message(cmd_filter("print") & filters.me)
async def cmd_print(client, message):
    if not message.reply_to_message:
        return await message.edit_text("⚠️ Responda à mensagem para gerar o print.")
    await message.edit_text("📸 **Gerando print...**")
    arquivo = "print_temp.png"
    try:
        texto = message.reply_to_message.text or message.reply_to_message.caption or "[Mídia sem texto]"
        autor = "Usuário"
        if message.reply_to_message.from_user:
            autor = message.reply_to_message.from_user.first_name
        if not os.path.exists("Roboto-Medium.ttf"):
            r = requests.get(
                "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Medium.ttf",
                timeout=15
            )
            with open("Roboto-Medium.ttf", "wb") as f:
                f.write(r.content)
        ft = ImageFont.truetype("Roboto-Medium.ttf", 26)
        fa = ImageFont.truetype("Roboto-Medium.ttf", 22)
        linhas = textwrap.wrap(texto, width=38)
        altura = 100 + (len(linhas) * 35)
        img = Image.new('RGBA', (600, altura), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([(10, 10), (590, altura - 10)], radius=15, fill=(33, 45, 59))
        d.text((30, 25), autor, fill=(100, 181, 239), font=fa)
        y = 65
        for linha in linhas:
            d.text((30, y), linha, fill=(255, 255, 255), font=ft)
            y += 35
        img.save(arquivo)
        await client.send_document(message.chat.id, arquivo, file_name="Print.png")
        os.remove(arquivo)
        await message.delete()
    except Exception as e:
        await message.edit_text(f"❌ Erro: `{e}`")
        if os.path.exists(arquivo):
            os.remove(arquivo)

@Client.on_message(cmd_filter("encurtar") & filters.me)
async def cmd_encurtar(client, message):
    p = prefixo(client)
    partes = message.text.split(None, 1)
    if len(partes) < 2:
        return await message.edit_text(f"⚠️ Use: `{p}encurtar [URL]`")
    url = partes[1].strip()
    await message.edit_text("🔗 **Encurtando...**")
    try:
        r = requests.get(f"https://tinyurl.com/api-create.php?url={url}", timeout=10)
        await message.edit_text(f"🔗 **Encurtado:**\n`{r.text}`")
    except Exception as e:
        await message.edit_text(f"❌ Erro: `{e}`")

@Client.on_message(cmd_filter("ipinfo") & filters.me)
async def cmd_ipinfo(client, message):
    partes = message.text.split(None, 1)
    ip = partes[1].strip() if len(partes) > 1 else ""
    await message.edit_text("🌐 **Buscando dados do IP...**")
    try:
        url = f"https://ipinfo.io/{ip}/json" if ip else "https://ipinfo.io/json"
        r = requests.get(url, timeout=10).json()
        await message.edit_text(
            f"🌐 **IP Info**\n\n"
            f"📍 IP: `{r.get('ip', 'N/A')}`\n"
            f"🏙️ Cidade: `{r.get('city', 'N/A')}`\n"
            f"🗺️ Região: `{r.get('region', 'N/A')}`\n"
            f"🌍 País: `{r.get('country', 'N/A')}`\n"
            f"🏢 Org: `{r.get('org', 'N/A')}`\n"
            f"⏰ Fuso: `{r.get('timezone', 'N/A')}`"
        )
    except Exception as e:
        await message.edit_text(f"❌ Erro: `{e}`")

@Client.on_message(cmd_filter("clima") & filters.me)
async def cmd_clima(client, message):
    partes = message.text.split(None, 1)
    cidade = partes[1].strip() if len(partes) > 1 else "Sao Paulo"
    await message.edit_text(f"🌤️ **Buscando clima de `{cidade}`...**")
    try:
        cidade_url = cidade.replace(" ", "+")
        r = requests.get(
            f"https://wttr.in/{cidade_url}?format=%l:+%C+%t+%h+%w&lang=pt",
            timeout=10,
            headers={"User-Agent": "curl/7.68.0"}
        )
        if r.status_code == 200 and "Unknown location" not in r.text and "ERROR" not in r.text:
            await message.edit_text(f"🌍 **Clima:**\n`{r.text.strip()}`")
        else:
            await message.edit_text("❌ Localidade não encontrada.")
    except requests.Timeout:
        await message.edit_text("❌ Tempo esgotado. Tente novamente.")
    except Exception as e:
        await message.edit_text(f"❌ Erro: `{e}`")

@Client.on_message(cmd_filter("specs") & filters.me)
async def cmd_specs(client, message):
    p = prefixo(client)
    partes = message.text.split(None, 1)
    if len(partes) < 2:
        return await message.edit_text(f"⚠️ Use: `{p}specs [modelo do celular]`")
    modelo = partes[1].strip()
    await message.edit_text(f"📱 **Buscando specs de `{modelo}`...**")
    try:
        termo = modelo.replace(" ", "+")
        headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 14)"}
        r = requests.get(
            f"https://www.gsmarena.com/results.php3?sQuickSearch=yes&sName={termo}",
            headers=headers, timeout=15
        )
        links = re.findall(r'href="([a-z0-9_]+-\d+\.php)"', r.text)
        if links:
            url_ficha = f"https://www.gsmarena.com/{links[0]}"
            r2 = requests.get(url_ficha, headers=headers, timeout=15)
            html = r2.text
            nome = re.search(r'<h1 class="specs-phone-name-title">(.*?)</h1>', html)
            proc = re.search(r'data-spec="chipset">(.*?)</td>', html, re.DOTALL)
            ram = re.search(r'data-spec="internalmemory">(.*?)</td>', html, re.DOTALL)
            bat = re.search(r'data-spec="batdescription1">(.*?)</td>', html, re.DOTALL)
            disp = re.search(r'data-spec="displaysize">(.*?)</td>', html, re.DOTALL)
            cam = re.search(r'data-spec="cam1modules">(.*?)</td>', html, re.DOTALL)
            limpar = lambda t: re.sub('<.*?>', '', t).strip() if t else "N/A"
            await message.edit_text(
                f"📱 **{nome.group(1).strip() if nome else modelo.upper()}**\n\n"
                f"⚙️ Processador: `{limpar(proc.group(1)) if proc else 'N/A'}`\n"
                f"💾 Memória: `{limpar(ram.group(1)) if ram else 'N/A'}`\n"
                f"📺 Tela: `{limpar(disp.group(1)) if disp else 'N/A'}`\n"
                f"📷 Câmera: `{limpar(cam.group(1))[:60] if cam else 'N/A'}`\n"
                f"🔋 Bateria: `{limpar(bat.group(1))[:60] if bat else 'N/A'}`\n\n"
                f"🔗 [Ficha completa]({url_ficha})"
            )
        else:
            await message.edit_text(
                f"📱 **{modelo.upper()}**\n\n"
                f"⚠️ Modelo não encontrado no GSMArena.\n"
                f"🔗 [Buscar no Google](https://www.google.com/search?q={termo}+specs)"
            )
    except Exception as e:
        await message.edit_text(f"❌ Erro: `{e}`")

# ==========================================
# 👤 CONTA & AFK
# ==========================================

@Client.on_message(cmd_filter("afk") & filters.me)
async def cmd_afk(client, message):
    global AFK_ATIVO, AFK_MOTIVO
    partes = message.text.split(None, 1)
    AFK_MOTIVO = partes[1].strip() if len(partes) > 1 else "Ausente."
    AFK_ATIVO = True
    await message.edit_text(f"💤 **Modo AFK ativado**\n📝 Motivo: `{AFK_MOTIVO}`")

@Client.on_message(cmd_filter("unafk") & filters.me)
async def cmd_unafk(client, message):
    global AFK_ATIVO
    AFK_ATIVO = False
    await message.edit_text("✅ **Modo AFK desativado.**")

@Client.on_message(cmd_filter("permit") & filters.me)
async def cmd_permit(client, message):
    if message.reply_to_message:
        uid = message.reply_to_message.from_user.id
    elif message.chat.type == enums.ChatType.PRIVATE:
        uid = message.chat.id
    else:
        return await message.edit_text("⚠️ Use em PV ou responda a alguém.")
    permitidos = carregar("permitidos.json", [])
    if uid not in permitidos:
        permitidos.append(uid)
        salvar("permitidos.json", permitidos)
    await message.edit_text(f"✅ **PV autorizado para `{uid}`**")

# ==========================================
# 📖 MENU INTELIGENTE
# ==========================================

@Client.on_message(cmd_filter("menu") & filters.me)
async def cmd_menu(client, message):
    p = prefixo(client)
    menu = (
        f"💎 **USERBOT PRO v1.0**\n"
        f"🔧 Prefixo ativo: `{p}`\n\n"
        f"📂 **DRIVE**\n"
        f"`{p}status` `{p}organizar` `{p}get` `{p}direto`\n"
        f"`{p}procurar` `{p}apagar`\n\n"
        f"👮 **MODERAÇÃO**\n"
        f"`{p}ban` `{p}unban` `{p}mute` `{p}unmute`\n"
        f"`{p}del` `{p}purge` `{p}admins` `{p}zombies`\n"
        f"`{p}gban` `{p}fban` `{p}addfed` `{p}delfed` `{p}feds`\n\n"
        f"🛠️ **FERRAMENTAS**\n"
        f"`{p}hack` `{p}type` `{p}ghost` `{p}fake`\n"
        f"`{p}tr` `{p}voz` `{p}print` `{p}encurtar`\n"
        f"`{p}ipinfo` `{p}clima` `{p}specs`\n\n"
        f"🖥️ **SISTEMA**\n"
        f"`{p}ping` `{p}speed` `{p}sysinfo` `{p}processos`\n"
        f"`{p}restart` `{p}atualizar` `{p}versao`\n\n"
        f"👤 **CONTA**\n"
        f"`{p}afk` `{p}unafk` `{p}permit`"
    )
    await message.edit_text(menu)

# ==========================================
# 📡 MONITORAMENTO (LOGS, AFK, PERMIT, AUTO-UPLOAD)
# ==========================================

@Client.on_message(filters.private & ~filters.me & ~filters.bot, group=-2)
async def pm_permit_checker(client, message):
    permitidos = carregar("permitidos.json", [])
    if message.from_user and message.from_user.id not in permitidos:
        try:
            await message.reply_text("🛡️ **Acesso restrito.** Aguarde autorização.")
        except:
            pass
        cfg = getattr(client, "config", {})
        log_id = cfg.get("ID_CANAL_LOGS")
        if log_id:
            try:
                await message.forward(log_id)
            except:
                pass
        message.stop_propagation()

@Client.on_message(filters.me, group=-1)
async def auto_unafk(client, message):
    global AFK_ATIVO
    if AFK_ATIVO and message.text:
        p = prefixo(client)
        if not message.text.startswith(f"{p}afk"):
            AFK_ATIVO = False
            try:
                aviso = await message.reply_text("✅ **AFK desativado automaticamente.**")
                await asyncio.sleep(3)
                await aviso.delete()
            except:
                pass

@Client.on_message((filters.private | filters.mentioned) & ~filters.me)
async def monitor_central(client, message):
    cfg = getattr(client, "config", {})
    log_id = cfg.get("ID_CANAL_LOGS")
    if not log_id:
        return
    if message.chat and message.chat.id == log_id:
        return

    # Verifica perda de admin
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        cache = carregar("admin_cache.json", {})
        cid = str(message.chat.id)
        if cid in cache and cache[cid].get("era_admin"):
            is_admin_atual = await verificar_admin(client, message.chat.id)
            if cache[cid].get("era_admin") and not is_admin_atual:
                try:
                    await client.send_message(
                        log_id,
                        f"⚠️ **PERDA DE CARGO**\n\nVocê não é mais admin em:\n**{message.chat.title}** (`{message.chat.id}`)"
                    )
                except:
                    pass
                cache[cid]["era_admin"] = False
                salvar("admin_cache.json", cache)

    # Auto-resposta AFK
    global AFK_ATIVO, AFK_MOTIVO
    if AFK_ATIVO:
        try:
            await message.reply_text(f"💤 **Estou AFK:** `{AFK_MOTIVO}`")
        except:
            pass

    # Encaminha para logs + auto-upload de arquivos pequenos
    try:
        await message.forward(log_id)
        limite = cfg.get("LIMITE_AUTO_UPLOAD", 20971520)
        drive = getattr(client, "drive", None)
        if drive and message.document and message.document.file_size and message.document.file_size <= limite:
            nome = message.document.file_name or f"doc_{message.id}"
            ext = os.path.splitext(nome)[1].lower()
            cat = CATEGORIAS.get(ext, 'Outros')
            path = await message.download()
            id_pasta = obter_pasta(client, cat)
            f_drive = drive.CreateFile({'title': os.path.basename(path), 'parents': [{'id': id_pasta}]})
            f_drive.SetContentFile(path)
            f_drive.Upload()
            os.remove(path)
    except:
        pass
