"""
plugins/account.py
Comandos de conta e monitoramento: afk, unafk, permit + handlers passivos (pm_permit, auto_unafk, monitor)
"""
import os
import asyncio

from pyrogram import filters, enums, Client
from utils.helpers import cmd_filter, prefixo, carregar, salvar, verificar_admin, tr

# Estado global do AFK (compartilhado dentro deste módulo)
AFK_ATIVO = False
AFK_MOTIVO = ""
CAPTCHA_PENDENTE = {}

CATEGORIAS = {
    '.apk': 'Apps', '.zip': 'Zips', '.rar': 'Zips', '.7z': 'Zips',
    '.exe': 'Windows', '.msi': 'Windows',
    '.mp4': 'Videos', '.mkv': 'Videos', '.avi': 'Videos',
    '.mp3': 'Audios', '.ogg': 'Audios', '.wav': 'Audios',
    '.pdf': 'Docs', '.docx': 'Docs', '.txt': 'Docs',
    '.jpg': 'Fotos', '.jpeg': 'Fotos', '.png': 'Fotos', '.gif': 'Fotos'
}


def obter_pasta(client, nome):
    from plugins.drive import obter_pasta as _obter_pasta
    return _obter_pasta(client, nome)


@Client.on_message(cmd_filter("afk") & filters.me)
async def cmd_afk(client, message):
    """Ativa o modo AFK com motivo opcional."""
    global AFK_ATIVO, AFK_MOTIVO
    partes = message.text.split(None, 1)
    AFK_MOTIVO = partes[1].strip() if len(partes) > 1 else tr(client, "Ausente.", "Away.")
    AFK_ATIVO = True
    await message.edit_text(tr(client, f"💤 **Modo AFK Ativado**\n└ 📝 **Motivo:** `{AFK_MOTIVO}`", f"💤 **AFK Mode Activated**\n└ 📝 **Reason:** `{AFK_MOTIVO}`"))


@Client.on_message(cmd_filter("unafk") & filters.me)
async def cmd_unafk(client, message):
    """Desativa o modo AFK manualmente."""
    global AFK_ATIVO
    AFK_ATIVO = False
    await message.edit_text(tr(client, "✅ **Modo AFK desativado.**", "✅ **AFK Mode deactivated.**"))


@Client.on_message(cmd_filter("permit") & filters.me)
async def cmd_permit(client, message):
    """Autoriza um usuário a enviar mensagens privadas."""
    if message.reply_to_message:
        uid = message.reply_to_message.from_user.id
    elif message.chat.type == enums.ChatType.PRIVATE:
        uid = message.chat.id
    else:
        return await message.edit_text(tr(client, "⚠️ Use em PV ou responda a alguém.", "⚠️ Use in PM or reply to someone."))
    permitidos = carregar("permitidos.json", [])
    if uid not in permitidos:
        permitidos.append(uid)
        salvar("permitidos.json", permitidos)
    await message.edit_text(tr(client, f"✅ **PV autorizado para `{uid}`**", f"✅ **PM authorized for `{uid}`**"))


# ==========================================
# 📡 HANDLERS PASSIVOS (Monitoramento)
# ==========================================

@Client.on_message(filters.private & ~filters.me & ~filters.bot, group=-2)
async def pm_permit_checker(client, message):
    """Bloqueia mensagens privadas de usuários não autorizados."""
    permitidos = carregar("permitidos.json", [])
    uid = message.from_user.id if message.from_user else message.chat.id
    
    if uid not in permitidos:
        if uid in CAPTCHA_PENDENTE:
            esperado = CAPTCHA_PENDENTE[uid]["resposta"]
            if message.text and message.text.strip() == str(esperado):
                permitidos.append(uid)
                salvar("permitidos.json", permitidos)
                del CAPTCHA_PENDENTE[uid]
                await message.reply_text(tr(client, "✅ **Verificação concluída!** Você agora pode me enviar mensagens.", "✅ **Verification complete!** You can now send me messages."))
                message.stop_propagation()
                return
            else:
                await message.reply_text(tr(client, "❌ **Resposta incorreta.** Tente novamente.", "❌ **Incorrect answer.** Try again."))
                message.stop_propagation()
                return
                
        import random
        n1 = random.randint(1, 10)
        n2 = random.randint(1, 10)
        CAPTCHA_PENDENTE[uid] = {"resposta": n1 + n2}
        
        try:
            await message.reply_text(tr(client,
                f"🛡️ **Firewall de Segurança**\n\nMensagens restritas. Para provar que é humano, resolva a conta:\n👉 **{n1} + {n2} = ?**",
                f"🛡️ **Security Firewall**\n\nRestricted messages. To prove you are human, solve this:\n👉 **{n1} + {n2} = ?**"
            ))
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
    """Desativa o AFK automaticamente quando o usuário envia uma mensagem."""
    global AFK_ATIVO
    if AFK_ATIVO and message.text:
        p = prefixo(client)
        if not message.text.startswith(f"{p}afk"):
            AFK_ATIVO = False
            try:
                aviso = await message.reply_text(tr(client, "✅ **AFK desativado automaticamente.**", "✅ **AFK automatically deactivated.**"))
                await asyncio.sleep(3)
                await aviso.delete()
            except:
                pass


@Client.on_message((filters.private | filters.mentioned) & ~filters.me)
async def monitor_central(client, message):
    """Monitora menções, PVs, perda de admin e faz auto-upload de arquivos."""
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
                        tr(client, f"⚠️ **PERDA DE CARGO**\n\nVocê não é mais admin em:\n**{message.chat.title}** (`{message.chat.id}`)",
                                   f"⚠️ **DEMOTION**\n\nYou are no longer an admin in:\n**{message.chat.title}** (`{message.chat.id}`)")
                    )
                except:
                    pass
                cache[cid]["era_admin"] = False
                salvar("admin_cache.json", cache)

    # Auto-resposta AFK
    global AFK_ATIVO, AFK_MOTIVO
    if AFK_ATIVO:
        try:
            await message.reply_text(tr(client, f"💤 **Estou AFK:** `{AFK_MOTIVO}`", f"💤 **I'm AFK:** `{AFK_MOTIVO}`"))
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
            
            def upload_drive_sync():
                from plugins.drive import obter_pasta
                id_pasta = obter_pasta(client, cat)
                f_drive = drive.CreateFile({'title': os.path.basename(path), 'parents': [{'id': id_pasta}]})
                f_drive.SetContentFile(path)
                f_drive.Upload()
                
            await asyncio.to_thread(upload_drive_sync)
            os.remove(path)
    except:
        pass
