"""
plugins/menu.py
Comando ,menu — Detecta automaticamente todos os comandos registrados
em qualquer arquivo .py da pasta plugins/ e exibe o menu organizado por módulo.

Como funciona:
  - Lê todos os arquivos .py da pasta plugins/ em tempo real
  - Extrai os nomes dos comandos usando regex no padrão cmd_filter("nome")
  - Lê a docstring de cada função para usar como descrição
  - Agrupa os comandos por arquivo (módulo) e exibe no menu
  - Qualquer novo plugin adicionado aparece automaticamente no próximo ,menu
"""
import os
import re
import ast

from pyrogram import filters, Client
from utils.helpers import cmd_filter, prefixo, deletar_depois, tr, EN_ALIASES


def extrair_comandos_do_arquivo(filepath: str) -> list[dict]:
    """
    Lê um arquivo .py e extrai todos os comandos registrados via cmd_filter("nome").
    Retorna uma lista de dicts com 'cmd' e 'desc' (docstring da função, se houver).
    """
    comandos = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()

        # Faz o parse da AST para extrair funções e suas docstrings
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return []

        # Mapa: nome_da_função → docstring
        docstrings = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                doc = ast.get_docstring(node)
                if doc:
                    # Pega só a primeira linha da docstring
                    docstrings[node.name] = doc.splitlines()[0].strip()

        # Regex para encontrar cmd_filter("nome") associado a uma função
        # Padrão: @Client.on_message(cmd_filter("nome") ...)\nasync def func_name
        pattern = re.compile(
            r'cmd_filter\(["\'](\w+)["\']\).*?\n'   # cmd_filter("nome")
            r'(?:.*?\n)*?'                            # linhas intermediárias (decoradores extras)
            r'async def (\w+)',                       # nome da função
            re.MULTILINE
        )

        for match in pattern.finditer(source):
            cmd_name = match.group(1)
            func_name = match.group(2)
            desc = docstrings.get(func_name, "")
            # Ignora o próprio menu para não criar recursão
            if cmd_name == "menu":
                continue
            comandos.append({"cmd": cmd_name, "desc": desc})

    except Exception:
        pass

    return comandos


def nome_modulo(client, filename: str) -> str:
    """Converte o nome do arquivo em um título legível para o menu."""
    if getattr(client, "LANG", "pt") == "en":
        nomes = {
            "system.py":     "🖥️ System",
            "moderation.py": "👮 Moderation",
            "drive.py":      "📂 Google Drive",
            "tools.py":      "🛠️ Tools",
            "account.py":    "👤 Account & AFK",
            "kang.py":       "🎭 Stickers",
        }
    else:
        nomes = {
            "system.py":     "🖥️ Sistema",
            "moderation.py": "👮 Moderação",
            "drive.py":      "📂 Google Drive",
            "tools.py":      "🛠️ Ferramentas",
            "account.py":    "👤 Conta & AFK",
            "kang.py":       "🎭 Figurinhas",
        }
    return nomes.get(filename, f"🔌 {filename.replace('.py', '').capitalize()}")


@Client.on_message(cmd_filter("menu") & filters.me)
async def cmd_menu(client, message):
    """Exibe todos os comandos disponíveis detectados automaticamente nos plugins."""
    deletar_depois(message, 30)
    p = prefixo(client)

    # Detecta o diretório plugins/ relativo ao local do main.py
    plugins_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))

    secoes = []
    total_cmds = 0

    # Ordena os arquivos para exibição consistente
    arquivos = sorted([
        f for f in os.listdir(plugins_dir)
        if f.endswith(".py") and f != "menu.py" and not f.startswith("_")
    ])

    for filename in arquivos:
        filepath = os.path.join(plugins_dir, filename)
        comandos = extrair_comandos_do_arquivo(filepath)

        if not comandos:
            continue

        titulo = nome_modulo(client, filename)
        
        lang = getattr(client, "LANG", "pt")
        cmds_list = []
        for c in comandos:
            nome_cmd = EN_ALIASES.get(c['cmd'], c['cmd']) if lang == "en" else c['cmd']
            cmds_list.append(f"`{p}{nome_cmd}`")
            
        linha_cmds = " ".join(cmds_list)
        secoes.append(f"**{titulo}**\n{linha_cmds}")
        total_cmds += len(comandos)

    if not secoes:
        return await message.edit_text(
            tr(client, f"⚠️ Nenhum comando encontrado.", f"⚠️ No commands found in plugins.")
        )

    versao = getattr(client, "VERSAO", "1.0")
    header = (
        f"⚡ **USERBOT PRO v{versao}**\n"
        f"├ 🔧 **Prefixo:** `{p}`\n"
        f"└ 📦 **{tr(client, 'Comandos', 'Commands')}:** `{total_cmds}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    menu_text = header + "\n\n".join(secoes)

    await message.edit_text(menu_text)
