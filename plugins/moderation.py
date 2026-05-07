"""
plugins/moderation.py
Comandos de moderação: ban, unban, mute, unmute, del, purge, admins, zombies, gban, fban, addfed, delfed, feds
"""
import asyncio

from pyrogram import filters, enums, Client
from pyrogram.types import ChatPermissions
from pyrogram.errors import FloodWait
from utils.helpers import cmd_filter, prefixo, resolver_alvo, auditoria, verificar_admin, carregar, salvar, deletar_depois


@Client.on_message(cmd_filter("ban") & filters.me)
async def cmd_ban(client, message):
    """Bane um usuário do grupo."""
    deletar_depois(message, 10)
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
    """Desbane um usuário do grupo."""
    deletar_depois(message, 10)
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
    """Silencia um usuário no grupo."""
    deletar_depois(message, 10)
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
    """Remove o silêncio de um usuário."""
    deletar_depois(message, 10)
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
    """Apaga a mensagem respondida (e o comando)."""
    if not message.reply_to_message:
        return await message.delete()
    try:
        await message.reply_to_message.delete()
        await message.delete()
    except:
        pass


@Client.on_message(cmd_filter("purge") & filters.me)
async def cmd_purge(client, message):
    """Apaga todas as mensagens desde a mensagem respondida até o comando."""
    if not message.reply_to_message:
        return await message.edit_text("⚠️ Responda à mensagem inicial para apagar a partir dela.")
    chat_id = message.chat.id
    msg_id_inicio = message.reply_to_message.id
    msg_id_fim = message.id
    try:
        ids = list(range(msg_id_inicio, msg_id_fim + 1))
        for i in range(0, len(ids), 100):
            await client.delete_messages(chat_id, ids[i:i+100])
        aviso = await client.send_message(chat_id, f"🧹 **Purge:** {len(ids)} mensagens apagadas.")
        await asyncio.sleep(3)
        await aviso.delete()
    except Exception as e:
        await message.edit_text(f"❌ Erro: `{e}`")


@Client.on_message(cmd_filter("admins") & filters.me)
async def cmd_admins(client, message):
    """Lista todos os administradores do grupo."""
    deletar_depois(message, 20)
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
    """Remove contas deletadas do grupo."""
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
    deletar_depois(msg, 15)


@Client.on_message(cmd_filter("gban") & filters.me)
async def cmd_gban(client, message):
    """Bane um usuário em todos os grupos onde o bot é admin."""
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
    deletar_depois(aviso, 15)


@Client.on_message(cmd_filter("fban") & filters.me)
async def cmd_fban(client, message):
    """Bane um usuário em todos os grupos da federação."""
    user_obj, motivo, msg_orig = await resolver_alvo(client, message)
    if not user_obj:
        return await message.edit_text(
            f"⚠️ Use: responda à mensagem, ou `{prefixo(client)}fban @user [motivo]`"
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
    deletar_depois(message, 15)


@Client.on_message(cmd_filter("addfed") & filters.me)
async def cmd_addfed(client, message):
    """Adiciona o grupo atual à federação."""
    deletar_depois(message, 10)
    feds = carregar("feds.json", [])
    if message.chat.id in feds:
        return await message.edit_text("⚠️ Este grupo já está cadastrado.")
    feds.append(message.chat.id)
    salvar("feds.json", feds)
    await message.edit_text(f"✅ **Grupo adicionado à federação.**\n📍 ID: `{message.chat.id}`")


@Client.on_message(cmd_filter("delfed") & filters.me)
async def cmd_delfed(client, message):
    """Remove o grupo atual da federação."""
    deletar_depois(message, 10)
    feds = carregar("feds.json", [])
    if message.chat.id not in feds:
        return await message.edit_text("⚠️ Este grupo não está cadastrado.")
    feds.remove(message.chat.id)
    salvar("feds.json", feds)
    await message.edit_text("✅ **Grupo removido da federação.**")


@Client.on_message(cmd_filter("feds") & filters.me)
async def cmd_feds(client, message):
    """Lista todos os grupos da federação."""
    deletar_depois(message, 20)
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
