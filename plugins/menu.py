"""
plugins/menu.py
Comando de menu: exibe todos os comandos disponíveis.
"""
from pyrogram import filters, Client
from utils.helpers import cmd_filter, prefixo


@Client.on_message(cmd_filter("menu") & filters.me)
async def cmd_menu(client, message):
    """Exibe o menu completo com todos os comandos disponíveis."""
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
