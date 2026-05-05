"""
plugins/kang.py
Comando ,kang — Rouba figurinhas (estáticas e animadas) e adiciona ao pacote do usuário.

Lógica 100% automática (sem interação manual):
  1. Verifica se o pacote já existe acessando t.me/addstickers/{packname}
  2. Se existir → /addsticker → envia nome do pack → envia figurinha → emoji → /done
     - Se o pacote estiver CHEIO (120) → incrementa número do pack e cria um novo automaticamente
     - Se o pack não existir nesse número → cria um novo automaticamente
  3. Se não existir → /newpack ou /newanimated → título → figurinha → emoji → /publish → nome

Baseado na implementação clássica dos userbots Telegram-Paperplane e UserBot.
"""
import io
import math
import urllib.request

from PIL import Image
from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import cmd_filter, prefixo

STICKER_BOT = "Stickers"
PACK_FULL_MSG = "Whoa! That's probably enough stickers for one pack"


async def resize_image(photo_bytes: io.BytesIO) -> io.BytesIO:
    """Redimensiona a imagem para 512x512 mantendo proporção, salva como PNG."""
    image = Image.open(photo_bytes)
    maxsize = (512, 512)
    if image.width < 512 and image.height < 512:
        if image.width > image.height:
            scale = 512 / image.width
            new_size = (512, math.floor(image.height * scale))
        else:
            scale = 512 / image.height
            new_size = (math.floor(image.width * scale), 512)
        image = image.resize(new_size)
    else:
        image.thumbnail(maxsize)
    output = io.BytesIO()
    output.name = "sticker.png"
    image.save(output, "PNG")
    output.seek(0)
    return output


def pack_exists(packname: str) -> bool:
    """Verifica se o pacote já existe no Telegram acessando a URL pública."""
    try:
        url = f"http://t.me/addstickers/{packname}"
        response = urllib.request.urlopen(urllib.request.Request(url), timeout=10)
        html = response.read().decode("utf8")
        return "A <strong>Telegram</strong> user has created the <strong>Sticker&nbsp;Set</strong>." in html
    except:
        return False


@Client.on_message(cmd_filter("kang") & filters.me)
async def cmd_kang(client, message):
    """
    Rouba a figurinha respondida e adiciona ao pacote do usuário automaticamente.
    Uso: responda a uma figurinha com ,kang [emoji opcional]
    """
    p = prefixo(client)
    reply = message.reply_to_message

    if not reply or not (reply.sticker or reply.photo or reply.document):
        return await message.edit_text(
            f"⚠️ Responda a uma **figurinha** ou **foto** com `{p}kang [emoji opcional]`"
        )

    await message.edit_text("🔄 **Kanging...**")

    # Obtém dados do usuário
    me = await client.get_me()
    username = me.username or str(me.id)

    # Detecta tipo e emoji
    is_anim = False
    is_video = False
    emoji = "⭐"
    photo = None

    if reply.sticker:
        sticker = reply.sticker
        is_anim = sticker.is_animated
        is_video = sticker.is_video
        emoji = sticker.emoji or "⭐"
        if is_anim or is_video:
            photo = None  # Será encaminhado diretamente
        else:
            raw = io.BytesIO()
            await client.download_media(reply, file_name=raw)
            raw.seek(0)
            photo = raw
    elif reply.photo:
        raw = io.BytesIO()
        await client.download_media(reply, file_name=raw)
        raw.seek(0)
        photo = raw
    elif reply.document and reply.document.mime_type and "image" in reply.document.mime_type:
        raw = io.BytesIO()
        await client.download_media(reply, file_name=raw)
        raw.seek(0)
        photo = raw
    else:
        return await message.edit_text("❌ Tipo de arquivo não suportado para kang.")

    # Emoji personalizado passado como argumento
    partes = message.text.split(None, 1)
    if len(partes) > 1 and not partes[1].strip().isnumeric():
        emoji = partes[1].strip()

    # Número do pacote (padrão 1, pode ser passado como argumento)
    pack_num = 1
    if len(partes) > 1 and partes[1].strip().isnumeric():
        pack_num = int(partes[1].strip())

    # Monta nomes do pacote
    if is_anim:
        packname = f"a{me.id}_by_{username}_{pack_num}_anim"
        packnick = f"@{username}'s animated pack {pack_num}"
        cmd_new = "/newanimated"
    elif is_video:
        packname = f"a{me.id}_by_{username}_{pack_num}_vid"
        packnick = f"@{username}'s video pack {pack_num}"
        cmd_new = "/newvideo"
    else:
        packname = f"a{me.id}_by_{username}_{pack_num}"
        packnick = f"@{username}'s userbot pack {pack_num}"
        cmd_new = "/newpack"

    # Redimensiona imagem estática
    file = None
    if not is_anim and not is_video and photo:
        try:
            file = await resize_image(photo)
        except Exception as e:
            return await message.edit_text(f"❌ Erro ao processar imagem: `{e}`")

    pack_url = f"https://t.me/addstickers/{packname}"

    try:
        async with client.conversation(STICKER_BOT, timeout=30) as conv:

            if pack_exists(packname):
                # ── Pacote já existe: tenta adicionar ──────────────────────────
                await conv.send_message("/addsticker")
                await conv.get_response()

                await conv.send_message(packname)
                resp = await conv.get_response()

                # Pacote cheio → incrementa automaticamente até achar um com espaço
                while PACK_FULL_MSG in (resp.text or ""):
                    pack_num += 1
                    if is_anim:
                        packname = f"a{me.id}_by_{username}_{pack_num}_anim"
                        packnick = f"@{username}'s animated pack {pack_num}"
                    elif is_video:
                        packname = f"a{me.id}_by_{username}_{pack_num}_vid"
                        packnick = f"@{username}'s video pack {pack_num}"
                    else:
                        packname = f"a{me.id}_by_{username}_{pack_num}"
                        packnick = f"@{username}'s userbot pack {pack_num}"
                    pack_url = f"https://t.me/addstickers/{packname}"

                    await message.edit_text(
                        f"📦 Pack {pack_num - 1} cheio! Mudando para pack **{pack_num}**..."
                    )

                    if pack_exists(packname):
                        await conv.send_message(packname)
                        resp = await conv.get_response()
                    else:
                        # Novo número de pack não existe ainda → cria
                        await conv.send_message(cmd_new)
                        await conv.get_response()
                        await conv.send_message(packnick)
                        await conv.get_response()

                        if is_anim or is_video:
                            await client.forward_messages(STICKER_BOT, reply.id, message.chat.id)
                        else:
                            file.seek(0)
                            await conv.send_file(file, force_document=True)
                        await conv.get_response()

                        await conv.send_message(emoji)
                        await conv.get_response()
                        await conv.send_message("/publish")

                        if is_anim or is_video:
                            await conv.get_response()
                            await conv.send_message(f"<{packnick}>")
                            await conv.get_response()
                            await conv.send_message("/skip")
                            await conv.get_response()

                        await conv.send_message(packname)
                        await conv.get_response()
                        break

                # Se o pack ainda aceitou (resp não é "pack cheio")
                if PACK_FULL_MSG not in (resp.text or ""):
                    if resp.text and "Invalid pack selected." in resp.text:
                        # Pack não existe mais → cria do zero
                        await conv.send_message(cmd_new)
                        await conv.get_response()
                        await conv.send_message(packnick)
                        await conv.get_response()

                        if is_anim or is_video:
                            await client.forward_messages(STICKER_BOT, reply.id, message.chat.id)
                        else:
                            file.seek(0)
                            await conv.send_file(file, force_document=True)
                        await conv.get_response()

                        await conv.send_message(emoji)
                        await conv.get_response()
                        await conv.send_message("/publish")

                        if is_anim or is_video:
                            await conv.get_response()
                            await conv.send_message(f"<{packnick}>")
                            await conv.get_response()
                            await conv.send_message("/skip")
                            await conv.get_response()

                        await conv.send_message(packname)
                        await conv.get_response()
                    else:
                        # Pack existe e tem espaço → envia figurinha
                        if is_anim or is_video:
                            await client.forward_messages(STICKER_BOT, reply.id, message.chat.id)
                        else:
                            file.seek(0)
                            await conv.send_file(file, force_document=True)
                        await conv.get_response()

                        await conv.send_message(emoji)
                        await conv.get_response()
                        await conv.send_message("/done")
                        await conv.get_response()

            else:
                # ── Pacote não existe: cria do zero ────────────────────────────
                await message.edit_text("📦 Criando novo pacote de figurinhas...")

                await conv.send_message(cmd_new)
                await conv.get_response()

                await conv.send_message(packnick)
                await conv.get_response()

                if is_anim or is_video:
                    await client.forward_messages(STICKER_BOT, reply.id, message.chat.id)
                else:
                    file.seek(0)
                    await conv.send_file(file, force_document=True)
                await conv.get_response()

                await conv.send_message(emoji)
                await conv.get_response()
                await conv.send_message("/publish")

                if is_anim or is_video:
                    await conv.get_response()
                    await conv.send_message(f"<{packnick}>")
                    await conv.get_response()
                    await conv.send_message("/skip")
                    await conv.get_response()

                await conv.send_message(packname)
                await conv.get_response()

        # ── Sucesso ────────────────────────────────────────────────────────────
        tipo = "Animada 🎞️" if is_anim else ("Vídeo 🎬" if is_video else "Estática 🖼️")
        await message.edit_text(
            f"✅ **Figurinha roubada com sucesso!**\n\n"
            f"🎭 Tipo: `{tipo}`\n"
            f"😀 Emoji: `{emoji}`\n"
            f"📦 Pack: `{packname}`\n"
            f"🔗 [Abrir pacote]({pack_url})",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📦 Abrir pacote", url=pack_url)]
            ]),
            disable_web_page_preview=True
        )

    except Exception as e:
        await message.edit_text(
            f"❌ **Erro no kang:**\n`{e}`\n\n"
            f"💡 Certifique-se de que o bot @Stickers está acessível e tente novamente."
        )


@Client.on_message(cmd_filter("packinfo") & filters.me)
async def cmd_packinfo(client, message):
    """Exibe o link dos seus pacotes de figurinhas."""
    me = await client.get_me()
    username = me.username or str(me.id)
    p = prefixo(client)

    txt = f"📦 **Seus pacotes de figurinhas** (`@{username}`):\n\n"
    encontrou = False
    for num in range(1, 11):
        for suffix, label in [("", "Estático"), ("_anim", "Animado"), ("_vid", "Vídeo")]:
            packname = f"a{me.id}_by_{username}_{num}{suffix}"
            if pack_exists(packname):
                url = f"https://t.me/addstickers/{packname}"
                txt += f"**{label} #{num}:** [{packname}]({url})\n"
                encontrou = True

    if not encontrou:
        txt = (
            f"⚠️ Nenhum pacote encontrado ainda.\n"
            f"Use `{p}kang` respondendo a uma figurinha para criar o primeiro!"
        )

    await message.edit_text(txt, disable_web_page_preview=True)
