"""
plugins/ai.py
Integração com Google Gemini (Inteligência Artificial)
"""
import asyncio
from pyrogram import filters, Client
from utils.helpers import cmd_filter, tr

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


def obter_modelo_otimizado(api_key: str) -> str:
    """Consulta a API do Google para descobrir qual modelo gratuito está liberado para a chave do usuário."""
    genai.configure(api_key=api_key)
    best_model = None
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                name = m.name.replace("models/", "")
                if "flash" in name.lower():
                    best_model = name
                    break
        if not best_model:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    return m.name.replace("models/", "")
    except Exception:
        pass
    return best_model or "gemini-1.5-flash"


@Client.on_message(cmd_filter("ask") & filters.me)
async def cmd_ask(client, message):
    """Faz uma pergunta para a IA (Gemini)."""
    if not HAS_GEMINI:
        return await message.edit_text(tr(client, "❌ Biblioteca `google-generativeai` não instalada.", "❌ Library `google-generativeai` not installed."))
    
    api_key = getattr(client, "config", {}).get("GEMINI_API_KEY")
    if not api_key:
        return await message.edit_text(tr(client, "❌ Chave `GEMINI_API_KEY` não configurada no `config.json`.", "❌ `GEMINI_API_KEY` not configured in `config.json`."))
    
    partes = message.text.split(None, 1)
    pergunta = partes[1].strip() if len(partes) > 1 else ""
    if message.reply_to_message and not pergunta:
        pergunta = message.reply_to_message.text or message.reply_to_message.caption
    
    if not pergunta:
        return await message.edit_text(tr(client, "⚠️ Use: `,ask [pergunta]` ou responda a algo.", "⚠️ Use: `,ask [question]` or reply to something."))
    
    await message.edit_text(tr(client, "🧠 **Processando consulta...**", "🧠 **Processing query...**"))
    try:
        def run_ai():
            modelo_nome = obter_modelo_otimizado(api_key)
            model = genai.GenerativeModel(modelo_nome)
            return model.generate_content(pergunta).text
            
        resposta = await asyncio.to_thread(run_ai)
        await message.edit_text(f"🧠 **Gemini AI:**\n\n{resposta}")
    except Exception as e:
        await message.edit_text(tr(client, f"❌ Erro na IA: `{e}`", f"❌ AI Error: `{e}`"))


@Client.on_message(cmd_filter("resumir") & filters.me)
async def cmd_resumir(client, message):
    """Lê as últimas 50 mensagens do chat e pede um resumo em tópicos para a IA."""
    api_key = getattr(client, "config", {}).get("GEMINI_API_KEY")
    if not HAS_GEMINI or not api_key:
        return await message.edit_text(tr(client, "❌ IA não configurada (faltando chave ou biblioteca).", "❌ AI not configured (missing key or library)."))
    
    await message.edit_text(tr(client, "📚 **Analisando últimas mensagens...**", "📚 **Analyzing recent messages...**"))
    try:
        msgs = []
        async for m in client.get_chat_history(message.chat.id, limit=50):
            if m.text or m.caption:
                autor = m.from_user.first_name if m.from_user else "Usuário"
                msgs.append(f"{autor}: {m.text or m.caption}")
        
        if not msgs:
            return await message.edit_text(tr(client, "⚠️ Poucas mensagens para resumir.", "⚠️ Not enough messages to summarize."))
        
        conversa = "\n".join(reversed(msgs))
        prompt = tr(client,
            "Aqui estão as últimas mensagens de um chat. Crie um resumo conciso e em bullet points sobre os principais tópicos discutidos:\n\n",
            "Here are the last messages of a chat. Create a concise bullet-point summary of the main topics discussed:\n\n"
        ) + conversa
        
        def run_summary():
            modelo_nome = obter_modelo_otimizado(api_key)
            model = genai.GenerativeModel(modelo_nome)
            return model.generate_content(prompt).text
            
        resposta = await asyncio.to_thread(run_summary)
        await message.edit_text(tr(client, f"📚 **Resumo Analítico:**\n\n{resposta}", f"📚 **Analytical Summary:**\n\n{resposta}"))
    except Exception as e:
        await message.edit_text(tr(client, f"❌ Erro ao resumir: `{e}`", f"❌ Error summarizing: `{e}`"))