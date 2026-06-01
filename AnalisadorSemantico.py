# Integrante do grupo:
# Mariana Alves da Silva - @himarialves
#
# Nome do grupo no Canvas: RA3_15
#
# Professor Frank Coelho de Alcantara
# Projeto acadêmico para a disciplina Linguagens Formais e Compiladores (2026-1).
# Instituição: Pontifícia Universidade Católica do Paraná - PUC/PR — 2026-1
'''
AnalisadorSemantico.py — Entry point do compilador Fase 3.

Uso:
     python AnalisadorSemantico.py <arquivo.txt>

'''

from __future__ import annotations
import json
import os
import sys

from lexer import prepararEntradaSemantica
from tabela_simbolos import construirTabelaSimbolos
from verificar_tipos import verificarTipos
from gerador import gerarArvoreAtribuida, gerarAssembly
from CONTRACTS import ErroSemantico, NoAtribuido

##
# Serialização de artefatos 
def _salvar_tabela(tabela: dict, caminho: str) -> None:
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(tabela, f, indent=2, ensure_ascii=False)

def _serializar_no(no: NoAtribuido) -> dict:
    # Converte NoAtribuido para dict serializável em JSON.
    # NoAtribuido é TypedDict (dict em runtime), mas get() com default garante
    # que campos opcionais não causem KeyError ao serializar árvores parciais.
    return {
        "tipo": no["tipo"],
        "valor": no["valor"],
        "linha": no["linha"],
        "tipo_semantico": no.get("tipo_semantico", ""),
        "categoria_semantica": no.get("categoria_semantica", ""),
        "reg_resultado": no.get("reg_resultado", ""),
        "label": no.get("label", ""),
        "filhos": [_serializar_no(f) for f in no.get("filhos", [])],
    }

def _salvar_arvore_atribuida(arvore: NoAtribuido, caminho: str) -> None:
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(_serializar_no(arvore), f, indent=2, ensure_ascii=False)

def _salvar_relatorio_erros(erros: list[ErroSemantico], caminho: str) -> None:
    with open(caminho, "w", encoding="utf-8") as f:
        if erros:
            f.write(f"{len(erros)} erro(s) semântico(s) encontrado(s):\n\n")
            for e in erros:
                f.write(f"  [{e['tipo_erro']}] {e['mensagem']}\n")
        else:
            f.write("Nenhum erro semântico encontrado.\n")

def _salvar_assembly(assembly: str, caminho: str) -> None:
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(assembly)

##
#  Main 
def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python AnalisadorSemantico.py <arquivo.txt>", file=sys.stderr)
        sys.exit(1)

    arquivo = sys.argv[1]
    base = os.path.splitext(os.path.basename(arquivo))[0]

    # Garante que output/ existe sem precisar criá-lo manualmente
    pasta_saida = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(pasta_saida, exist_ok=True)

    # Etapa 1: preparar entrada — encerra com exit(1) se houver erros léx/sint.
    tokens, arvore = prepararEntradaSemantica(arquivo)

    # Etapa 2: tabela de símbolos
    tabela, erros_decl = construirTabelaSimbolos(arvore)

    # Etapa 3: verificação de tipos
    tipos, erros_tipo = verificarTipos(arvore, tabela)

    erros_semanticos = erros_decl + erros_tipo

    # Etapa 4: árvore atribuída (sempre gerada, mesmo com erros — útil para diagnóstico)
    arvore_atribuida = gerarArvoreAtribuida(arvore, tabela, tipos)

    # Salvar artefatos em output/
    caminho_tabela = os.path.join(pasta_saida, f"{base}_tabela_simbolos.json")
    caminho_arvore = os.path.join(pasta_saida, f"{base}_arvore_atribuida.json")
    caminho_erros  = os.path.join(pasta_saida, f"{base}_relatorio_erros.txt")

    _salvar_tabela(tabela, caminho_tabela)
    _salvar_arvore_atribuida(arvore_atribuida, caminho_arvore)
    _salvar_relatorio_erros(erros_semanticos, caminho_erros)

    print(f"Tabela de símbolos : {caminho_tabela}")
    print(f"Árvore atribuída   : {caminho_arvore}")
    print(f"Relatório de erros : {caminho_erros}")

    # Etapa 5: assembly apenas se sem erros semânticos
    if not erros_semanticos:
        assembly = gerarAssembly(arvore_atribuida)
        caminho_asm = os.path.join(pasta_saida, f"{base}.asm")
        _salvar_assembly(assembly, caminho_asm)
        print(f"Assembly gerado    : {caminho_asm}")
        print("\nCompilação bem-sucedida.")
    else:
        print(f"\n{len(erros_semanticos)} erro(s) semântico(s) encontrado(s):")
        for e in erros_semanticos:
            print(f"  Linha {e['linha']}: [{e['tipo_erro']}] {e['mensagem']}")
        print("\nAssembly não gerado.")
        sys.exit(1)

if __name__ == "__main__":
    main()