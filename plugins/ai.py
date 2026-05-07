"""
plugins/ai.py
Integração com Google Gemini (Inteligência Artificial)
"""
import asyncio
from pyrogram import filters, Client
from utils.helpers import cmd_filter

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


@Client.on_message(cmd_filter("ask") & filters.me)
async def cmd_ask(client, message):
    """Faz uma pergunta para a IA (Gemini)."""
    if not HAS_GEMINI:
        return await message.edit_text("❌ Biblioteca `google-generativeai` não instalada.")
    
    api_key = getattr(client, "config", {}).get("GEMINI_API_KEY")
    if not api_key:
        return await message.edit_text("❌ Chave `GEMINI_API_KEY` não configurada no `config.json`.")
    
    partes = message.text.split(None, 1)
    pergunta = partes[1].strip() if len(partes) > 1 else ""
    if message.reply_to_message and not pergunta:
        pergunta = message.reply_to_message.text or message.reply_to_message.caption
    
    if not pergunta:
        return await message.edit_text("⚠️ Use: `,ask [pergunta]` ou responda a algo.")
    
    await message.edit_text("🤖 **Pensando...**")
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        resposta = await asyncio.to_thread(lambda: model.generate_content(pergunta).text)
        await message.edit_text(f"🤖 **Resposta:**\n\n{resposta}")
    except Exception as e:
        await message.edit_text(f"❌ Erro na IA: `{e}`")


@Client.on_message(cmd_filter("resumir") & filters.me)
async def cmd_resumir(client, message):
    """Lê as últimas 50 mensagens do chat e pede um resumo em tópicos para a IA."""
    api_key = getattr(client, "config", {}).get("GEMINI_API_KEY")
    if not HAS_GEMINI or not api_key:
        return await message.edit_text("❌ IA não configurada (faltando chave ou biblioteca).")
    
    await message.edit_text("🤖 **Lendo as últimas mensagens...**")
    try:
        msgs = []
        async for m in client.get_chat_history(message.chat.id, limit=50):
            if m.text or m.caption:
                autor = m.from_user.first_name if m.from_user else "Usuário"
                msgs.append(f"{autor}: {m.text or m.caption}")
        
        if not msgs:
            return await message.edit_text("⚠️ Poucas mensagens para resumir.")
        
        conversa = "\n".join(reversed(msgs))
        prompt = f"Aqui estão as últimas mensagens de um chat. Crie um resumo conciso e em bullet points sobre os principais tópicos discutidos:\n\n{conversa}"
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        resposta = await asyncio.to_thread(lambda: model.generate_content(prompt).text)
        await message.edit_text(f"📝 **Resumo do Chat:**\n\n{resposta}")
    except Exception as e:
        await message.edit_text(f"❌ Erro ao resumir: `{e}`")