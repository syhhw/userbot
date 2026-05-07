"""
plugins/drive.py
Comandos do Google Drive: status, organizar, get, direto, procurar, apagar
"""
import os
import asyncio
import aiohttp
import humanize

from pyrogram import filters, Client
from utils.helpers import cmd_filter, prefixo, salvar, carregar, deletar_depois

CATEGORIAS = {
    '.apk': 'Apps', '.zip': 'Zips', '.rar': 'Zips', '.7z': 'Zips',
    '.exe': 'Windows', '.msi': 'Windows',
    '.mp4': 'Videos', '.mkv': 'Videos', '.avi': 'Videos',
    '.mp3': 'Audios', '.ogg': 'Audios', '.wav': 'Audios',
    '.pdf': 'Docs', '.docx': 'Docs', '.txt': 'Docs',
    '.jpg': 'Fotos', '.jpeg': 'Fotos', '.png': 'Fotos', '.gif': 'Fotos'
}

CACHE_PASTAS = {}
ULTIMA_BUSCA = {}


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


@Client.on_message(cmd_filter("status") & filters.me)
async def drive_status(client, message):
    """Exibe o uso de espaço do Google Drive."""
    deletar_depois(message, 15)
    drive = getattr(client, "drive", None)
    if not drive:
        return await message.edit_text("❌ Drive não conectado.")
    try:
        def fetch_status():
            return drive.GetAbout()
            
        sobre = await asyncio.to_thread(fetch_status)
        total = int(sobre.get('quotaBytesTotal', 1))
        usado = int(sobre.get('quotaBytesUsedAggregate', 0))
        pct = (usado / total) * 100 if total > 0 else 0
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
    """Organiza os arquivos da pasta raiz do bot no Drive em subpastas por categoria."""
    drive = getattr(client, "drive", None)
    if not drive:
        return await message.edit_text("❌ Drive não conectado.")
    msg = await message.edit_text("🗂️ **Organizando arquivos...**")
    try:
        def do_organize():
            cfg = getattr(client, "config", {})
            raiz = cfg.get("ID_PASTA_RAIZ_DRIVE")
            if not raiz:
                raise ValueError("ID da pasta raiz não configurado.")
            
            query = f"'{raiz}' in parents and trashed=false and mimeType != 'application/vnd.google-apps.folder'"
            arquivos = drive.ListFile({'q': query}).GetList()
            movidos = 0
            for arq in arquivos:
                ext = os.path.splitext(arq['title'])[1].lower()
                categoria = CATEGORIAS.get(ext, 'Outros')
                id_destino = obter_pasta(client, categoria)
                
                # Move o arquivo removendo as pastas pai anteriores (PyDrive API wrapper)
                old_parents = ",".join([p['id'] for p in arq.get('parents', [])])
                drive.auth.service.files().update(
                    fileId=arq['id'],
                    addParents=id_destino,
                    removeParents=old_parents,
                    fields='id, parents'
                ).execute()
                movidos += 1
            return movidos
            
        movidos = await asyncio.to_thread(do_organize)
        await msg.edit_text(f"✅ **Organização concluída!**\n📦 `{movidos}` arquivos movidos da raiz para subpastas.")
    except Exception as e:
        await msg.edit_text(f"❌ Erro: `{e}`")
    deletar_depois(msg, 15)


@Client.on_message(cmd_filter("get") & filters.me)
async def drive_get(client, message):
    """Baixa um arquivo de uma URL e envia para o Drive."""
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
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                r.raise_for_status()
                with open(local, "wb") as f:
                    async for chunk in r.content.iter_chunked(1024 * 1024):
                        f.write(chunk)
                        
        await msg.edit_text("☁️ **Enviando para o Google Drive...**")
        
        def do_upload():
            ext = os.path.splitext(nome)[1].lower()
            categoria = CATEGORIAS.get(ext, 'Outros')
            id_pasta = obter_pasta(client, categoria)
            f_drive = drive.CreateFile({'title': nome, 'parents': [{'id': id_pasta}]})
            f_drive.SetContentFile(local)
            f_drive.Upload()
            f_drive.InsertPermission({'type': 'anyone', 'value': 'anyone', 'role': 'reader'})
            return f_drive, categoria
            
        f_drive, categoria = await asyncio.to_thread(do_upload)
        os.remove(local)
        await msg.edit_text(
            f"✅ **Transferência Concluída!**\n"
            f"├ 📁 **Arquivo:** `{nome}`\n"
            f"├ 🗂️ **Categoria:** `{categoria}`\n"
            f"└ 🔗 [Acessar no Google Drive]({f_drive['alternateLink']})"
        )
    except Exception as e:
        await msg.edit_text(f"❌ Erro: `{e}`")
    deletar_depois(msg, 15)


@Client.on_message(cmd_filter("direto") & filters.me)
async def drive_direto(client, message):
    """Gera um link de download direto para um arquivo do Drive."""
    deletar_depois(message, 20)
    drive = getattr(client, "drive", None)
    if not drive:
        return await message.edit_text("❌ Drive não conectado.")
    partes = message.text.split(None, 1)
    if len(partes) < 2:
        return await message.edit_text(f"⚠️ Use: `{prefixo(client)}direto [nome do arquivo]`")
    termo = partes[1].strip()
    try:
        def do_search():
            return drive.ListFile({'q': f"title = '{termo}' and trashed=false"}).GetList()
            
        arquivos = await asyncio.to_thread(do_search)
        if not arquivos:
            return await message.edit_text("❌ Arquivo não encontrado.")
        f = arquivos[0]
        link = f"https://drive.google.com/uc?export=download&id={f['id']}"
        await message.edit_text(f"🔗 **Link Direto**\n\n📁 `{f['title']}`\n`{link}`")
    except Exception as e:
        await message.edit_text(f"❌ Erro: `{e}`")


@Client.on_message(cmd_filter("procurar") & filters.me)
async def drive_procurar(client, message):
    """Busca arquivos no Drive pelo nome."""
    deletar_depois(message, 30)
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
        def do_search():
            return drive.ListFile({'q': f"title contains '{termo}' and trashed=false"}).GetList()
            
        arquivos = await asyncio.to_thread(do_search)
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
    """Move um arquivo encontrado pelo procurar para a lixeira do Drive."""
    deletar_depois(message, 10)
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
        def do_trash():
            f = drive.CreateFile({'id': item['id']})
            f.Trash()
        await asyncio.to_thread(do_trash)
        await message.edit_text(f"🗑️ **Movido para a lixeira:**\n📁 `{item['title']}`")
        del ULTIMA_BUSCA[num]
    except Exception as e:
        await message.edit_text(f"❌ Erro: `{e}`")
