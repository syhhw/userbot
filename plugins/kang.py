"""
plugins/kang.py
Comando ,kang — Rouba figurinhas e adiciona automaticamente ao pacote do usuário.

Dependência extra necessária na VM:
    pip install pyromod

Fluxo de criação (pacote novo):
    /newpack → título → figurinha → emoji → /publish → /skip → nome_do_pack

Fluxo de adição (pacote existente):
    /addsticker → nome_do_pack → figurinha → emoji → /done
"""
import os
import math
import asyncio

from PIL import Image
from pyrogram import filters, Client, raw
from pyrogram.raw.types import InputStickerSetShortName
from pyrogram.errors import StickersetInvalid
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import cmd_filter, prefixo

STICKER_BOT = "Stickers"
PACK_FULL_MSG = "Whoa! That's probably enough stickers for one pack"
TMP_WEBP = "/tmp/kang_temp.webp"
TMP_PNG  = "/tmp/kang_temp.png"


# ─── Utilitários ──────────────────────────────────────────────────────────────

async def pack_exists(client, packname: str) -> bool:
    """Verifica se o pacote existe via API Pyrogram raw."""
    try:
        await client.invoke(
            raw.functions.messages.GetStickerSet(
                stickerset=InputStickerSetShortName(short_name=packname),
                hash=0
            )
        )
        return True
    except StickersetInvalid:
        return False
    except Exception:
        return False


async def resize_image(src: str, dst: str) -> str:
    """Redimensiona a imagem para caber em 512x512 mantendo proporção."""
    image = Image.open(src).convert("RGBA")
    w, h = image.size
    if w > h:
        new_w, new_h = 512, math.floor(h * 512 / w)
    elif h > w:
        new_w, new_h = math.floor(w * 512 / h), 512
    else:
        new_w, new_h = 512, 512
    image = image.resize((new_w, new_h), Image.LANCZOS)
    image.save(dst, "PNG")
    return dst


def limpar_tmp():
    for p in [TMP_WEBP, TMP_PNG]:
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass


# ─── Comando ,kang ────────────────────────────────────────────────────────────

@Client.on_message(cmd_filter("kang") & filters.me)
async def cmd_kang(client, message):
    """
    Rouba a figurinha respondida e adiciona ao pacote automaticamente.
    Uso: ,kang [emoji opcional]
    """
    p = prefixo(client)
    reply = message.reply_to_message

    if not reply or not (reply.sticker or reply.photo or reply.document):
        return await message.edit_text(
            f"⚠️ Responda a uma **figurinha** ou **foto** com `{p}kang [emoji opcional]`"
        )

    await message.edit_text("🔄 **Kanging...**")

    me = await client.get_me()
    username = me.username or str(me.id)

    # ── Detecta tipo e emoji ───────────────────────────────────────────────────
    is_anim  = False
    is_video = False
    emoji    = "⭐"
    file_to_send = None

    try:
        if reply.sticker:
            is_anim  = reply.sticker.is_animated
            is_video = reply.sticker.is_video
            emoji    = reply.sticker.emoji or "⭐"
            if not is_anim and not is_video:
                await client.download_media(reply, file_name=TMP_WEBP)
                file_to_send = await resize_image(TMP_WEBP, TMP_PNG)
        elif reply.photo:
            tmp = await client.download_media(reply, file_name=TMP_WEBP)
            file_to_send = await resize_image(tmp, TMP_PNG)
        elif reply.document and reply.document.mime_type and "image" in reply.document.mime_type:
            tmp = await client.download_media(reply, file_name=TMP_WEBP)
            file_to_send = await resize_image(tmp, TMP_PNG)
        else:
            return await message.edit_text("❌ Tipo de arquivo não suportado para kang.")
    except Exception as e:
        limpar_tmp()
        return await message.edit_text(f"❌ Erro ao processar arquivo: `{e}`")

    # ── Lê emoji personalizado do argumento ───────────────────────────────────
    partes = message.text.split(None, 1)
    pack_num = 1
    if len(partes) > 1:
        arg = partes[1].strip()
        if arg.isnumeric():
            pack_num = int(arg)
        else:
            emoji = arg

    # ── Monta nomes do pacote ─────────────────────────────────────────────────
    def build_names(num):
        if is_anim:
            pname = f"a{me.id}_by_{username}_{num}_anim"
            pnick = f"@{username} animated pack {num}"
            cmd   = "/newanimated"
        elif is_video:
            pname = f"a{me.id}_by_{username}_{num}_vid"
            pnick = f"@{username} video pack {num}"
            cmd   = "/newvideo"
        else:
            pname = f"a{me.id}_by_{username}_{num}"
            pnick = f"@{username} userbot pack {num}"
            cmd   = "/newpack"
        return pname, pnick, cmd

    packname, packnick, cmd_new = build_names(pack_num)
    pack_url = f"https://t.me/addstickers/{packname}"

    # ── Helpers de conversa com @Stickers ─────────────────────────────────────
    bot_id = (await client.get_users(STICKER_BOT)).id

    async def sw(text: str, timeout: int = 30):
        """Envia mensagem ao @Stickers e aguarda resposta."""
        await client.send_message(STICKER_BOT, text)
        return await client.listen(chat_id=bot_id, timeout=timeout)

    async def fw(timeout: int = 30):
        """Envia a figurinha ao @Stickers e aguarda resposta."""
        if is_anim or is_video:
            await client.forward_messages(STICKER_BOT, message.chat.id, reply.id)
        else:
            await client.send_document(STICKER_BOT, file_to_send, force_document=True)
        return await client.listen(chat_id=bot_id, timeout=timeout)

    # ─────────────────────────────────────────────────────────────────────────
    # FLUXO CORRETO DO @Stickers bot:
    #
    # CRIAÇÃO:
    #   /newpack → (bot pede título) → título
    #   → (bot pede figurinha) → envia figurinha
    #   → (bot pede emoji) → emoji
    #   → (bot diz "Congratulations, send /publish") → /publish
    #   → (bot pede ícone ou /skip) → /skip
    #   → (bot pede nome curto) → nome_do_pack
    #   → PRONTO ✅
    #
    # ADIÇÃO:
    #   /addsticker → (bot pede nome do pack) → nome_do_pack
    #   → (bot pede figurinha) → envia figurinha
    #   → (bot pede emoji) → emoji
    #   → (bot diz "send /done") → /done
    #   → PRONTO ✅
    # ─────────────────────────────────────────────────────────────────────────

    try:
        exists = await pack_exists(client, packname)

        if exists:
            # ── Adiciona ao pacote existente ──────────────────────────────────
            resp = await sw("/addsticker")
            resp = await sw(packname)

            # Pacote cheio → incrementa e cria novo
            while PACK_FULL_MSG in (resp.text or ""):
                pack_num += 1
                packname, packnick, cmd_new = build_names(pack_num)
                pack_url = f"https://t.me/addstickers/{packname}"
                await message.edit_text(f"📦 Pack cheio! Criando pack **#{pack_num}**...")

                if await pack_exists(client, packname):
                    # Próximo pack também existe, tenta adicionar nele
                    resp = await sw(packname)
                else:
                    # Cria o próximo pack do zero
                    resp = await sw(cmd_new)          # /newpack
                    resp = await sw(packnick)          # título
                    resp = await fw()                  # figurinha
                    resp = await sw(emoji)             # emoji
                    resp = await sw("/publish")        # /publish
                    await sw("/skip")                  # /skip (ícone)
                    await sw(packname)                 # nome curto
                    resp = None
                    break

            # Pack aceitou a figurinha normalmente
            if resp is not None:
                resp = await fw()                      # figurinha
                resp = await sw(emoji)                 # emoji
                await sw("/done")                      # /done

        else:
            # ── Cria o pacote do zero ─────────────────────────────────────────
            await message.edit_text("📦 **Criando novo pacote...**")
            await sw(cmd_new)                          # /newpack
            await sw(packnick)                         # título
            await fw()                                 # figurinha
            await sw(emoji)                            # emoji
            await sw("/publish")                       # /publish
            await sw("/skip")                          # /skip (pula ícone)
            await sw(packname)                         # nome curto

        # ── Sucesso ───────────────────────────────────────────────────────────
        limpar_tmp()
        tipo = "Animada 🎞️" if is_anim else ("Vídeo 🎬" if is_video else "Estática 🖼️")
        await message.edit_text(
            f"✅ **Figurinha roubada!**\n\n"
            f"🎭 Tipo: `{tipo}`\n"
            f"😀 Emoji: `{emoji}`\n"
            f"📦 Pack: [{packname}]({pack_url})",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📦 Ver pacote", url=pack_url)]
            ]),
            disable_web_page_preview=True
        )

    except asyncio.TimeoutError:
        limpar_tmp()
        await message.edit_text(
            "⏰ **Timeout:** O @Stickers demorou demais para responder.\n"
            "Tente novamente em alguns segundos."
        )
    except Exception as e:
        limpar_tmp()
        await message.edit_text(f"❌ **Erro no kang:**\n`{e}`")


# ─── Comando ,packinfo ────────────────────────────────────────────────────────

@Client.on_message(cmd_filter("packinfo") & filters.me)
async def cmd_packinfo(client, message):
    """Exibe o link dos seus pacotes de figurinhas."""
    me = await client.get_me()
    username = me.username or str(me.id)
    p = prefixo(client)

    await message.edit_text("🔍 **Buscando seus pacotes...**")

    linhas = []
    for num in range(1, 11):
        for suffix, label in [("", "Estático"), ("_anim", "Animado"), ("_vid", "Vídeo")]:
            packname = f"a{me.id}_by_{username}_{num}{suffix}"
            if await pack_exists(client, packname):
                url = f"https://t.me/addstickers/{packname}"
                linhas.append(f"**{label} #{num}:** [{packname}]({url})")

    if not linhas:
        return await message.edit_text(
            f"⚠️ Nenhum pacote encontrado.\n"
            f"Use `{p}kang` respondendo a uma figurinha para criar o primeiro!"
        )

    await message.edit_text(
        f"📦 **Seus pacotes** (`@{username}`):\n\n" + "\n".join(linhas),
        disable_web_page_preview=True
    )
