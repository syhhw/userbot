"""
plugins/tools.py
Ferramentas e diversão: hack, type, ghost, fake, tr, voz, print, encurtar, ipinfo, clima, specs, clone, reverter
"""
import os
import re
import asyncio
import random
import textwrap
import aiohttp

from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
from pyrogram import filters, enums, Client
from deep_translator import GoogleTranslator
from utils.helpers import cmd_filter, prefixo, resolver_alvo, carregar, salvar


@Client.on_message(cmd_filter("hack") & filters.me)
async def cmd_hack(client, message):
    """Simula um hack animado (diversão)."""
    alvo = message.reply_to_message.from_user.first_name if message.reply_to_message else "SISTEMA"
    passos = [
        f"💀 **INICIANDO ATAQUE DIRECIONADO**\n🎯 **Alvo:** `{alvo}`",
        f"🔍 `[▰▱▱▱▱▱▱▱▱▱]` 10%\nBuscando IP e rastreando conexão...",
        f"📡 `[▰▰▰▱▱▱▱▱▱▱]` 30%\nInterceptando tráfego MTProto do Telegram...",
        f"🔑 `[▰▰▰▰▰▱▱▱▱▱]` 50%\nQuebrando criptografia ponta-a-ponta (AES-256)...",
        f"📱 `[▰▰▰▰▰▰▰▱▱▱]` 70%\nClonando sessão e contornando 2FA...",
        f"📂 `[▰▰▰▰▰▰▰▰▰▱]` 90%\nBaixando histórico de mensagens, fotos e áudios...",
        f"☢️ `[▰▰▰▰▰▰▰▰▰▰]` 100%\nInjeção de rootkit finalizada.",
        f"💀 **HACK CONCLUÍDO COM SUCESSO** 💀\n\n🎯 Conta de `{alvo}` totalmente comprometida.\n📸 Todos os dados privados foram copiados para um servidor remoto.\n\n💸 **ATENÇÃO:** Envie **10 Bitcoins** para a carteira abaixo em 24h ou tudo será vazado:\n`bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh`"
    ]
    for passo in passos:
        try:
            await message.edit_text(passo)
            await asyncio.sleep(random.uniform(1.5, 2.5))
        except:
            pass


@Client.on_message(cmd_filter("type") & filters.me)
async def cmd_type(client, message):
    """Simula digitação letra por letra."""
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
            await asyncio.sleep(random.uniform(0.04, 0.15))
        except:
            pass
    await message.edit_text(digitado)


@Client.on_message(cmd_filter("ghost") & filters.me)
async def cmd_ghost(client, message):
    """Envia uma mensagem que se autodestrói após N segundos."""
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
    """Simula ação de digitação, gravação de áudio ou vídeo."""
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
    """Traduz uma mensagem respondida para o idioma especificado."""
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
    """Converte texto em voz. Sotaques: br, pt, en, es, ja, ru"""
    p = prefixo(client)
    
    sotaques_map = {
        "br": ("pt", "com.br"), "pt": ("pt", "pt"),
        "en": ("en", "com"), "es": ("es", "es"),
        "ja": ("ja", "co.jp"), "ru": ("ru", "ru")
    }
    
    lang, tld = "pt", "com.br"
    texto = ""
    
    partes = message.text.split()
    if len(partes) > 1 and partes[1].lower() in sotaques_map:
        lang, tld = sotaques_map[partes[1].lower()]
        texto = " ".join(partes[2:])
    elif len(partes) > 1:
        texto = " ".join(partes[1:])
        
    if not texto and message.reply_to_message:
        texto = message.reply_to_message.text or message.reply_to_message.caption
        
    if not texto:
        return await message.edit_text(f"⚠️ Use: `{p}voz [sotaque] [texto]`\nEx: `{p}voz pt Fala gajo!` ou `{p}voz en Ola amigo`")
        
    await message.edit_text("🎙️ **Gerando áudio...**")
    arquivo = "voz_temp.ogg"
    try:
        def gerar_tts():
            tts = gTTS(text=texto, lang=lang, tld=tld)
            tts.save(arquivo)
            
        await asyncio.to_thread(gerar_tts)
        await client.send_voice(message.chat.id, arquivo)
        os.remove(arquivo)
        await message.delete()
    except Exception as e:
        await message.edit_text(f"❌ Erro: `{e}`")
        if os.path.exists(arquivo):
            os.remove(arquivo)


def gerar_print_img(texto, autor, arquivo):
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

@Client.on_message(cmd_filter("print") & filters.me)
async def cmd_print(client, message):
    """Gera um print estilizado de uma mensagem respondida."""
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
            async with aiohttp.ClientSession() as session:
                async with session.get("https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Medium.ttf") as r:
                    conteudo = await r.read()
            with open("Roboto-Medium.ttf", "wb") as f:
                f.write(conteudo)
                
        await asyncio.to_thread(gerar_print_img, texto, autor, arquivo)
        await client.send_document(message.chat.id, arquivo, file_name="Print.png")
        os.remove(arquivo)
        await message.delete()
    except Exception as e:
        await message.edit_text(f"❌ Erro: `{e}`")
        if os.path.exists(arquivo):
            os.remove(arquivo)


@Client.on_message(cmd_filter("encurtar") & filters.me)
async def cmd_encurtar(client, message):
    """Encurta uma URL usando o TinyURL."""
    p = prefixo(client)
    partes = message.text.split(None, 1)
    if len(partes) < 2:
        return await message.edit_text(f"⚠️ Use: `{p}encurtar [URL]`")
    url = partes[1].strip()
    await message.edit_text("🔗 **Encurtando...**")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://tinyurl.com/api-create.php?url={url}") as r:
                texto_url = await r.text()
        await message.edit_text(f"🔗 **Encurtado:**\n`{texto_url}`")
    except Exception as e:
        await message.edit_text(f"❌ Erro: `{e}`")


@Client.on_message(cmd_filter("ipinfo") & filters.me)
async def cmd_ipinfo(client, message):
    """Exibe informações sobre um endereço IP."""
    partes = message.text.split(None, 1)
    ip = partes[1].strip() if len(partes) > 1 else ""
    await message.edit_text("🌐 **Buscando dados do IP...**")
    try:
        url = f"https://ipinfo.io/{ip}/json" if ip else "https://ipinfo.io/json"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as res:
                r = await res.json()
        await message.edit_text(
            f"🌐 **IP Info** (`{r.get('ip', 'N/A')}`)\n"
            f"├ 🏙️ **Cidade:** `{r.get('city', 'N/A')}`\n"
            f"├ 🗺️ **Região:** `{r.get('region', 'N/A')}`\n"
            f"├ 🌍 **País:** `{r.get('country', 'N/A')}`\n"
            f"├ 🏢 **Org:** `{r.get('org', 'N/A')}`\n"
            f"└ ⏰ **Fuso:** `{r.get('timezone', 'N/A')}`"
        )
    except Exception as e:
        await message.edit_text(f"❌ Erro: `{e}`")


@Client.on_message(cmd_filter("clima") & filters.me)
async def cmd_clima(client, message):
    """Exibe o clima atual de uma cidade."""
    partes = message.text.split(None, 1)
    cidade = partes[1].strip() if len(partes) > 1 else "Sao Paulo"
    await message.edit_text(f"🌤️ **Buscando clima de `{cidade}`...**")
    try:
        cidade_url = cidade.replace(" ", "+")
        async with aiohttp.ClientSession(headers={"User-Agent": "curl/7.68.0"}) as session:
            async with session.get(f"https://wttr.in/{cidade_url}?format=%l:+%C+%t+%h+%w&lang=pt") as r:
                status = r.status
                texto = await r.text()
                
        if status == 200 and "Unknown location" not in texto and "ERROR" not in texto:
            await message.edit_text(f"🌍 **Clima:**\n`{texto.strip()}`")
        else:
            await message.edit_text("❌ Localidade não encontrada.")
    except asyncio.TimeoutError:
        await message.edit_text("❌ Tempo esgotado (Timeout).")
    except Exception as e:
        await message.edit_text(f"❌ Erro: `{e}`")


@Client.on_message(cmd_filter("specs") & filters.me)
async def cmd_specs(client, message):
    """Busca as especificações técnicas de um celular no GSMArena."""
    p = prefixo(client)
    partes = message.text.split(None, 1)
    if len(partes) < 2:
        return await message.edit_text(f"⚠️ Use: `{p}specs [modelo do celular]`")
    modelo = partes[1].strip()
    await message.edit_text(f"📱 **Buscando specs de `{modelo}`...**")
    try:
        termo = modelo.replace(" ", "+")
        headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 14)"}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(f"https://www.gsmarena.com/results.php3?sQuickSearch=yes&sName={termo}") as r:
                html_busca = await r.text()
        links = re.findall(r'href="([a-z0-9_]+-\d+\.php)"', html_busca)
        if links:
            url_ficha = f"https://www.gsmarena.com/{links[0]}"
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url_ficha) as r2:
                    html = await r2.text()
            nome = re.search(r'<h1 class="specs-phone-name-title">(.*?)</h1>', html)
            proc = re.search(r'data-spec="chipset">(.*?)</td>', html, re.DOTALL)
            ram = re.search(r'data-spec="internalmemory">(.*?)</td>', html, re.DOTALL)
            bat = re.search(r'data-spec="batdescription1">(.*?)</td>', html, re.DOTALL)
            disp = re.search(r'data-spec="displaysize">(.*?)</td>', html, re.DOTALL)
            cam = re.search(r'data-spec="cam1modules">(.*?)</td>', html, re.DOTALL)
            limpar = lambda t: re.sub('<.*?>', '', t).strip() if t else "N/A"
            await message.edit_text(
                f"📱 **{nome.group(1).strip() if nome else modelo.upper()}**\n"
                f"├ ⚙️ **CPU:** `{limpar(proc.group(1)) if proc else 'N/A'}`\n"
                f"├ 💾 **RAM:** `{limpar(ram.group(1)) if ram else 'N/A'}`\n"
                f"├ 📺 **Tela:** `{limpar(disp.group(1)) if disp else 'N/A'}`\n"
                f"├ 📷 **Câmera:** `{limpar(cam.group(1))[:60] if cam else 'N/A'}`\n"
                f"└ 🔋 **Bateria:** `{limpar(bat.group(1))[:60] if bat else 'N/A'}`\n\n"
                f"🔗 Ficha completa no GSMArena"
            )
        else:
            await message.edit_text(
                f"📱 **{modelo.upper()}**\n\n"
                f"⚠️ Modelo não encontrado no GSMArena.\n"
                f"🔗 [Buscar no Google](https://www.google.com/search?q={termo}+specs)"
            )
    except Exception as e:
        await message.edit_text(f"❌ Erro: `{e}`")


@Client.on_message(cmd_filter("clone") & filters.me)
async def cmd_clone(client, message):
    """Clona o nome, bio e foto de um usuário."""
    user, _, _ = await resolver_alvo(client, message)
    if not user:
        return await message.edit_text(f"⚠️ Responda a alguém ou use `{prefixo(client)}clone @user`")
        
    msg = await message.edit_text("🎭 **Iniciando clonagem...**")
    
    backup = carregar("clone_backup.json", {})
    if not backup.get("cloned"):
        me = await client.get_me()
        me_full = await client.get_chat("me")
        backup = {
            "cloned": True,
            "first_name": me.first_name or "",
            "last_name": me.last_name or "",
            "bio": me_full.bio or "",
            "photos_added": 0
        }
        salvar("clone_backup.json", backup)
        
    target = await client.get_users(user.id)
    target_full = await client.get_chat(user.id)
    
    first = target.first_name or ""
    last = target.last_name or ""
    bio = target_full.bio[:70] if target_full.bio else ""
    
    try:
        await client.update_profile(first_name=first, last_name=last, bio=bio)
    except Exception as e:
        return await msg.edit_text(f"❌ Erro ao atualizar perfil: `{e}`")
        
    if target.photo:
        await msg.edit_text("🎭 **Baixando foto de perfil...**")
        photo_path = None
        try:
            photo_path = await client.download_media(target.photo.big_file_id)
            await client.set_profile_photo(photo=photo_path)
            backup["photos_added"] = backup.get("photos_added", 0) + 1
            salvar("clone_backup.json", backup)
        except Exception:
            pass
        finally:
            if photo_path and os.path.exists(photo_path):
                os.remove(photo_path)
                
    await msg.edit_text(f"✅ **Clone de `{first}` ativado!**\nUse `{prefixo(client)}reverter` para voltar ao normal.")


@Client.on_message(cmd_filter("reverter") & filters.me)
async def cmd_reverter(client, message):
    """Restaura o perfil original após um clone."""
    backup = carregar("clone_backup.json", {})
    if not backup.get("cloned"):
        return await message.edit_text("⚠️ Você não está clonando ninguém no momento.")
        
    msg = await message.edit_text("🔄 **Revertendo para o perfil original...**")
    
    try:
        await client.update_profile(
            first_name=backup.get("first_name", ""),
            last_name=backup.get("last_name", ""),
            bio=backup.get("bio", "")
        )
    except Exception:
        pass
        
    added = backup.get("photos_added", 0)
    if added > 0:
        try:
            photos = []
            async for p in client.get_chat_photos("me", limit=added):
                photos.append(p.file_id)
            if photos:
                await client.delete_profile_photos(photos)
        except Exception:
            pass
            
    salvar("clone_backup.json", {})
    await msg.edit_text("✅ **Perfil original restaurado com sucesso!**")
