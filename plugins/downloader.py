"""
plugins/downloader.py
Baixador universal de vídeos usando yt-dlp (YouTube, Instagram, TikTok, etc.)
"""
import os
import asyncio
from pyrogram import filters, Client
from utils.helpers import cmd_filter, prefixo

try:
    import yt_dlp
    HAS_YTDLP = True
except ImportError:
    HAS_YTDLP = False

@Client.on_message(cmd_filter("dl") & filters.me)
async def cmd_dl(client, message):
    """Baixa um vídeo de quase qualquer rede social (Instagram, TikTok, YouTube)."""
    if not HAS_YTDLP:
        return await message.edit_text("❌ Biblioteca `yt-dlp` não instalada.")
        
    p = prefixo(client)
    partes = message.text.split(None, 1)
    if len(partes) < 2:
        return await message.edit_text(f"⚠️ Use: `{p}dl [link do vídeo]`")
    
    url = partes[1].strip()
    msg = await message.edit_text("📥 **Analisando link e baixando vídeo...**\nIsso pode demorar dependendo do tamanho.")
    
    def baixar_video():
        opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': '/tmp/vid_%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'max_filesize': 1500 * 1024 * 1024, # Limita arquivos absurdos
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if 'requested_downloads' in info:
                arquivo = info['requested_downloads'][0]['filepath']
            else:
                arquivo = ydl.prepare_filename(info)
            return arquivo, info.get('title', 'Video')
            
    try:
        arquivo, titulo = await asyncio.to_thread(baixar_video)
        await msg.edit_text("☁️ **Enviando para o Telegram...**")
        await client.send_video(message.chat.id, arquivo, caption=f"🎥 **{titulo}**\n🔗 Link Original")
        os.remove(arquivo)
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ Erro ao baixar:\n`{str(e)[:300]}`")