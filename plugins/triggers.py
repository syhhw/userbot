"""
plugins/triggers.py
Sistema de Auto-Respostas Passivas (Gatilhos)
"""
import re
from pyrogram import filters, Client
from utils.helpers import cmd_filter, prefixo, carregar, salvar, tr

@Client.on_message(cmd_filter("addtrigger") & filters.me)
async def cmd_addtrigger(client, message):
    """Adiciona um gatilho de resposta automática."""
    p = prefixo(client)
    matches = re.findall(r'"([^"]*)"', message.text)
    if len(matches) < 2:
        return await message.edit_text(tr(client, f"⚠️ Use: `{p}addtrigger \"palavra\" \"resposta\"`", f"⚠️ Use: `{p}addtrigger \"word\" \"response\"`"))
    
    gatilho = matches[0].lower()
    resposta = matches[1]
    
    triggers = carregar("triggers.json", {})
    triggers[gatilho] = resposta
    salvar("triggers.json", triggers)
    
    await message.edit_text(tr(client, f"✅ **Trigger salvo!**\nSe disserem: `{gatilho}`\nResponderei: `{resposta}`", f"✅ **Trigger saved!**\nIf they say: `{gatilho}`\nI'll reply: `{resposta}`"))


@Client.on_message(cmd_filter("deltrigger") & filters.me)
async def cmd_deltrigger(client, message):
    """Remove um gatilho de resposta."""
    p = prefixo(client)
    matches = re.findall(r'"([^"]*)"', message.text)
    gatilho = matches[0].lower() if matches else message.text.split(" ", 1)[-1].strip().lower()
        
    triggers = carregar("triggers.json", {})
    if gatilho in triggers:
        del triggers[gatilho]
        salvar("triggers.json", triggers)
        await message.edit_text(tr(client, f"🗑️ **Trigger removido:** `{gatilho}`", f"🗑️ **Trigger removed:** `{gatilho}`"))
    else:
        await message.edit_text(tr(client, f"❌ **Trigger não encontrado:** `{gatilho}`", f"❌ **Trigger not found:** `{gatilho}`"))


@Client.on_message(cmd_filter("triggers") & filters.me)
async def cmd_triggers(client, message):
    """Lista todos os gatilhos ativos."""
    triggers = carregar("triggers.json", {})
    if not triggers:
        return await message.edit_text(tr(client, "⚠️ **Nenhum trigger configurado.**", "⚠️ **No triggers configured.**"))
        
    txt = tr(client, "⚡ **Meus Triggers:**\n\n", "⚡ **My Triggers:**\n\n") + "".join([f"• `{k}` ➡️ `{v}`\n" for k, v in triggers.items()])
    await message.edit_text(txt)


@Client.on_message(filters.incoming & ~filters.bot & ~filters.me, group=5)
async def trigger_handler(client, message):
    """Ouve mensagens e responde caso acerte o gatilho."""
    if message.text:
        for gatilho, resposta in carregar("triggers.json", {}).items():
            if gatilho in message.text.lower():
                return await message.reply_text(resposta)