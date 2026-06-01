# Integrante do grupo:
# Mariana Alves da Silva - @himarialves
#
# Nome do grupo no Canvas: RA3_15
#
# Professor Frank Coelho de Alcantara
# Projeto acadêmico para a disciplina Linguagens Formais e Compiladores (2026-1).
# Instituição: Pontifícia Universidade Católica do Paraná - PUC/PR — 2026-1

'''
 test_05_integracao.py — Testes de integração end-to-end.

 Executa AnalisadorSemantico.py via subprocess com os arquivos de fixture,
 verificando: código de saída, artefatos gerados, relatório de erros.

'''

from __future__ import annotations
import os
import re
import subprocess
import sys
import tempfile

import pytest

# Raiz do projeto (pai de tests/)
PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(PROJETO, "tests", "fixtures")
COMPILADOR = os.path.join(PROJETO, "AnalisadorSemantico.py")
OUTPUT = os.path.join(PROJETO, "output")


def _rodar(arquivo: str) -> tuple[int, str, str]:
    # Executa o compilador e retorna (returncode, stdout, stderr).
    # capture_output=True evita que o output do subprocesso apareça no terminal pytest.
    res = subprocess.run(
        [sys.executable, COMPILADOR, arquivo],
        capture_output=True, text=True,
        cwd=PROJETO,
    )
    return res.returncode, res.stdout, res.stderr

def _nome_base(arquivo: str) -> str:
    return os.path.splitext(os.path.basename(arquivo))[0]

##
# Programa válido
# Usa tests/fixtures/prog_valido.txt — programa sem erros semânticos.
# Verifica: exit 0, assembly gerado, todos os artefatos em output/ criados.
class TestProgramaValido:
    @pytest.fixture(autouse=True)
    def _setup(self):
        self.arquivo = os.path.join(FIXTURES, "prog_valido.txt")
        self.base = _nome_base(self.arquivo)
        self.code, self.out, self.err = _rodar(self.arquivo)

    def test_exit_code_zero(self):
        assert self.code == 0, f"Esperado exit 0, stderr: {self.err}"

    def test_mensagem_sucesso(self):
        assert "bem-sucedida" in self.out.lower() or "sucesso" in self.out.lower()

    def test_assembly_gerado(self):
        assert "Assembly gerado" in self.out or ".asm" in self.out

    def test_arquivo_asm_criado(self):
        asm_path = os.path.join(OUTPUT, f"{self.base}.asm")
        assert os.path.exists(asm_path), f"Arquivo {self.base}.asm não criado"

    def test_tabela_simbolos_criada(self):
        path = os.path.join(OUTPUT, f"{self.base}_tabela_simbolos.json")
        assert os.path.exists(path)

    def test_arvore_atribuida_criada(self):
        path = os.path.join(OUTPUT, f"{self.base}_arvore_atribuida.json")
        assert os.path.exists(path)

    def test_relatorio_erros_criado(self):
        path = os.path.join(OUTPUT, f"{self.base}_relatorio_erros.txt")
        assert os.path.exists(path)

    def test_relatorio_erros_indica_nenhum_erro(self):
        path = os.path.join(OUTPUT, f"{self.base}_relatorio_erros.txt")
        with open(path, encoding="utf-8") as f:
            conteudo = f.read()
        assert "nenhum erro" in conteudo.lower() or "0 erro" in conteudo.lower()

    def test_asm_tem_start_e_end(self):
        asm_path = os.path.join(OUTPUT, f"{self.base}.asm")
        with open(asm_path, encoding="utf-8") as f:
            conteudo = f.read()
        assert "_start:" in conteudo
        assert "_end:" in conteudo


##
# Programa com erros semânticos
# Usa tests/fixtures/prog_erros_semanticos.txt.
# Verifica: exit != 0, .asm não gerado, relatório e artefatos de diagnóstico
# sempre gerados — o programador precisa ver o que deu errado mesmo sem assembly.
class TestProgramaComErros:

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.arquivo = os.path.join(FIXTURES, "prog_erros_semanticos.txt")
        self.base = _nome_base(self.arquivo)
        self.code, self.out, self.err = _rodar(self.arquivo)

    def test_exit_code_nao_zero(self):
        assert self.code != 0, "Erros semânticos devem resultar em exit != 0"

    def test_assembly_nao_gerado(self):
        assert "não gerado" in self.out.lower() or \
               "nao gerado" in self.out.lower() or \
               "Assembly gerado" not in self.out, \
               "Assembly não deve ser gerado quando há erros"

    def test_asm_nao_criado(self):
        asm_path = os.path.join(OUTPUT, f"{self.base}.asm")
        assert not os.path.exists(asm_path), \
            f"Arquivo {self.base}.asm não deve existir com erros semânticos"

    def test_stdout_menciona_erros(self):
        assert "erro" in self.out.lower()

    def test_stdout_indica_numero_de_linha(self):
        assert re.search(r"linha\s+\d+", self.out, re.IGNORECASE), \
            "Deve indicar número de linha dos erros"

    def test_relatorio_erros_criado_mesmo_com_falha(self):
        # Artefatos de diagnóstico são sempre gerados, independente de erros
        path = os.path.join(OUTPUT, f"{self.base}_relatorio_erros.txt")
        assert os.path.exists(path), "Relatório de erros deve ser criado mesmo com falha"

    def test_relatorio_lista_erros(self):
        path = os.path.join(OUTPUT, f"{self.base}_relatorio_erros.txt")
        with open(path, encoding="utf-8") as f:
            conteudo = f.read()
        assert "erro" in conteudo.lower()
        assert len(conteudo.strip()) > 0

    def test_tabela_simbolos_criada_mesmo_com_erros(self):
        path = os.path.join(OUTPUT, f"{self.base}_tabela_simbolos.json")
        assert os.path.exists(path)

    def test_arvore_atribuida_criada_mesmo_com_erros(self):
        path = os.path.join(OUTPUT, f"{self.base}_arvore_atribuida.json")
        assert os.path.exists(path)

    def test_multiplos_erros_reportados(self):
        # Decisão de design: coleta todos os erros antes de retornar — o programador
        # vê todos os problemas de uma vez, não um por vez a cada recompilação
        assert re.search(r"[2-9]\d*\s+erro", self.out, re.IGNORECASE), \
            "Deve reportar múltiplos erros"


##
# Programa complexo
# Usa tests/fixtures/prog_complexo.txt — estruturas aninhadas (IF dentro de WHILE,
# expressões compostas, múltiplas variáveis). Verifica que o gerador não quebra
# com programas mais elaborados que os testes unitários cobrem.
class TestProgramaComplexo:

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.arquivo = os.path.join(FIXTURES, "prog_complexo.txt")
        self.base = _nome_base(self.arquivo)
        self.code, self.out, self.err = _rodar(self.arquivo)

    def test_compilacao_bem_sucedida(self):
        assert self.code == 0, \
            f"Programa complexo deve compilar sem erros. stdout: {self.out}, stderr: {self.err}"

    def test_asm_gerado_e_valido(self):
        asm_path = os.path.join(OUTPUT, f"{self.base}.asm")
        assert os.path.exists(asm_path)
        with open(asm_path, encoding="utf-8") as f:
            conteudo = f.read()
        assert ".data" in conteudo
        assert ".text" in conteudo
        assert "_start:" in conteudo

    def test_asm_tem_estruturas_de_controle(self):
        asm_path = os.path.join(OUTPUT, f"{self.base}.asm")
        with open(asm_path, encoding="utf-8") as f:
            conteudo = f.read()
        assert "WHILE" in conteudo or "IF_FIM" in conteudo, \
            "Programa complexo deve gerar estruturas de controle"


##
# Uso incorreto da CLI
def test_sem_argumento_imprime_uso():
    res = subprocess.run(
        [sys.executable, COMPILADOR],
        capture_output=True, text=True,
        cwd=PROJETO,
    )
    assert res.returncode != 0
    assert "uso" in res.stderr.lower() or "uso" in res.stdout.lower() or \
           "usage" in res.stderr.lower()

def test_arquivo_inexistente_termina_com_erro():
    code, out, err = _rodar("arquivo_que_nao_existe.txt")
    assert code != 0


##
# Validador de assembly (validar_assembly.py)
# Testa a integração entre o compilador e o validador estático.
# O validador deve aprovar o assembly gerado por programas válidos e rejeitar
# assembly malformado antes que chegue ao CPulator.
VALIDADOR = os.path.join(PROJETO, "validar_assembly.py")

def test_validador_aprova_assembly_valido():
    # Assembly gerado de programa válido deve passar na validação estática
    arquivo = os.path.join(FIXTURES, "prog_valido.txt")
    _rodar(arquivo)  # garante que o .asm existe em output/
    base = _nome_base(arquivo)
    asm_path = os.path.join(OUTPUT, f"{base}.asm")
    if not os.path.exists(asm_path):
        pytest.skip("Assembly não gerado — verifique compilação do fixture")
    res = subprocess.run(
        [sys.executable, VALIDADOR, asm_path],
        capture_output=True, text=True, cwd=PROJETO,
    )
    assert res.returncode == 0, f"Validador rejeitou assembly válido: {res.stdout}"

def test_validador_rejeita_assembly_sem_start():
    # Assembly sem _start: deve falhar na validação — label obrigatório no CPulator
    asm_invalido = ".data\nFOO: .word 0\n.text\n@ sem _start\n_end:\n    B _end\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".asm",
                                     delete=False, encoding="utf-8") as f:
        f.write(asm_invalido)
        path = f.name
    try:
        res = subprocess.run(
            [sys.executable, VALIDADOR, path],
            capture_output=True, text=True, cwd=PROJETO,
        )
        assert res.returncode != 0
    finally:
        os.unlink(path)
