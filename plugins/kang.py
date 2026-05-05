"""
plugins/kang.py
Comando ,kang — Rouba figurinhas (estáticas, animadas e vídeo) e adiciona ao pacote do usuário.

Lógica 100% automática (sem interação manual):
  1. Verifica se o pacote já existe acessando t.me/addstickers/{packname}
  2. Se existir → /addsticker → nome do pack → figurinha → emoji → /done
     - Se o pacote estiver CHEIO (120) → incrementa número e cria novo automaticamente
  3. Se não existir → /newpack ou /newanimated → título → figurinha → emoji → /publish → nome

Baseado na implementação clássica dos userbots Telegram-Paperplane e UserBot.
"""
import io
import os
import math
import urllib.request

from PIL import Image
from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import cmd_filter, prefixo

STICKER_BOT = "Stickers"
PACK_FULL_MSG = "Whoa! That's probably enough stickers for one pack"
TMP_FILE = "/tmp/kang_sticker_temp"


async def resize_image(path: str) -> str:
    """Redimensiona a imagem para 512x512 mantendo proporção e salva como PNG."""
    image = Image.open(path)
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
    out_path = TMP_FILE + ".png"
    image.save(out_path, "PNG")
    return out_path


def pack_exists(packname: str) -> bool:
    """Verifica se o pacote já existe no Telegram acessando a URL pública."""
    try:
        url = f"http://t.me/addstickers/{packname}"
        response = urllib.request.urlopen(urllib.request.Request(url), timeout=10)
        html = response.read().decode("utf8")
        return "A <strong>Telegram</strong> user has created the <strong>Sticker&nbsp;Set</strong>." in html
    except:
        return False


def limpar_tmp():
    """Remove arquivos temporários do kang."""
    for ext in [".png", ".webp", ".tgs", ".webm", ""]:
        path = TMP_FILE + ext
        if os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass


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
    file_path = None

    try:
        if reply.sticker:
            sticker = reply.sticker
            is_anim = sticker.is_animated
            is_video = sticker.is_video
            emoji = sticker.emoji or "⭐"

            if not is_anim and not is_video:
                # Figurinha estática: baixa e redimensiona
                raw_path = await client.download_media(reply, file_name=TMP_FILE + ".webp")
                file_path = await resize_image(raw_path)
            # Animadas e vídeo serão encaminhadas diretamente

        elif reply.photo:
            raw_path = await client.download_media(reply, file_name=TMP_FILE + ".jpg")
            file_path = await resize_image(raw_path)

        elif reply.document and reply.document.mime_type and "image" in reply.document.mime_type:
            raw_path = await client.download_media(reply, file_name=TMP_FILE + ".jpg")
            file_path = await resize_image(raw_path)

        else:
            return await message.edit_text("❌ Tipo de arquivo não suportado para kang.")

    except Exception as e:
        limpar_tmp()
        return await message.edit_text(f"❌ Erro ao baixar/processar arquivo: `{e}`")

    # Emoji personalizado passado como argumento
    partes = message.text.split(None, 1)
    if len(partes) > 1 and not partes[1].strip().isnumeric():
        emoji = partes[1].strip()

    # Número do pacote (padrão 1, pode ser passado como argumento numérico)
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

    pack_url = f"https://t.me/addstickers/{packname}"

    async def enviar_figurinha(conv):
        """Envia a figurinha correta para o @Stickers dentro de uma conversa."""
        if is_anim or is_video:
            await client.forward_messages(STICKER_BOT, reply.id, message.chat.id)
        else:
            await conv.send_file(file_path, force_document=True)
        await conv.get_response()

    try:
        async with client.conversation(STICKER_BOT, timeout=30) as conv:

            if pack_exists(packname):
                # ── Pacote já existe: tenta adicionar ──────────────────────────
                await conv.send_message("/addsticker")
                await conv.get_response()

                await conv.send_message(packname)
                resp = await conv.get_response()

                # Pacote cheio → incrementa automaticamente
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
                        f"📦 Pack {pack_num - 1} cheio! Criando pack **{pack_num}**..."
                    )

                    if pack_exists(packname):
                        await conv.send_message(packname)
                        resp = await conv.get_response()
                    else:
                        # Novo número ainda não existe → cria
                        await conv.send_message(cmd_new)
                        await conv.get_response()
                        await conv.send_message(packnick)
                        await conv.get_response()
                        await enviar_figurinha(conv)
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

                # Pack aceitou (não estava cheio)
                if PACK_FULL_MSG not in (resp.text or ""):
                    if resp.text and "Invalid pack selected." in resp.text:
                        # Pack sumiu → cria do zero
                        await conv.send_message(cmd_new)
                        await conv.get_response()
                        await conv.send_message(packnick)
                        await conv.get_response()
                        await enviar_figurinha(conv)
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
                        # Pack existe e tem espaço → envia figurinha normalmente
                        await enviar_figurinha(conv)
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
                await enviar_figurinha(conv)
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
        limpar_tmp()
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
        limpar_tmp()
        await message.edit_text(
            f"❌ **Erro no kang:**\n`{e}`\n\n"
            f"💡 Certifique-se de que o bot @Stickers está acessível e tente novamente."
        )


@Client.on_message(cmd_filter("packinfo") & filters.me)
async def cmd_packinfo(client, message):
    """Exibe o link dos seus pacotes de figurinhas detectados automaticamente."""
    me = await client.get_me()
    username = me.username or str(me.id)
    p = prefixo(client)

    await message.edit_text("🔍 **Buscando seus pacotes...**")

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
