import os
import sqlite3
from pathlib import Path

import pytest

from migrations.budget_usuario import migrar_budget


def test_migracao_preserva_dados_cria_backup_e_e_idempotente(tmp_path):
    caminho = tmp_path / "antigo.db"
    with sqlite3.connect(caminho) as conexao:
        conexao.execute("CREATE TABLE usuario (id INTEGER PRIMARY KEY, nome TEXT, email TEXT, senha TEXT)")
        conexao.execute("INSERT INTO usuario VALUES (1, 'Teste', 'teste@example.test', 'hash-preservado')")
    resultado = migrar_budget(caminho)
    assert set(resultado["colunas"]) == {"budget", "usar_budget", "login_google"}
    assert Path(resultado["backup"]).is_file()
    if os.name == "posix":
        assert Path(resultado["backup"]).stat().st_mode & 0o077 == 0
    with sqlite3.connect(resultado["backup"]) as backup:
        assert backup.execute("SELECT * FROM usuario").fetchone() == (1, "Teste", "teste@example.test", "hash-preservado")
    with sqlite3.connect(caminho) as conexao:
        assert conexao.execute("SELECT id,nome,email,senha,budget,usar_budget,login_google FROM usuario").fetchone() == (1, "Teste", "teste@example.test", "hash-preservado", None, 0, 0)
        conexao.execute("UPDATE usuario SET budget=1234.56, usar_budget=1")
    assert migrar_budget(caminho) == {"colunas": [], "backup": None}
    with sqlite3.connect(caminho) as conexao:
        assert conexao.execute("SELECT budget,usar_budget FROM usuario").fetchone() == (1234.56, 1)
    assert len(list(tmp_path.glob("*.antes-budget-*.db"))) == 1


def test_migracao_parcial_nao_altera_coluna_existente(tmp_path):
    caminho = tmp_path / "parcial.db"
    with sqlite3.connect(caminho) as conexao:
        conexao.execute("CREATE TABLE usuario (id INTEGER, budget NUMERIC, login_google BOOLEAN)")
        conexao.execute("INSERT INTO usuario VALUES (1, 50.25, 1)")
    assert migrar_budget(caminho)["colunas"] == ["usar_budget"]
    with sqlite3.connect(caminho) as conexao:
        assert conexao.execute("SELECT budget,login_google,usar_budget FROM usuario").fetchone() == (50.25, 1, 0)


def test_nao_cria_banco_por_engano_nem_migra_tabela_ausente(tmp_path):
    with pytest.raises(sqlite3.OperationalError):
        migrar_budget(tmp_path / "nao-existe.db")
    assert not (tmp_path / "nao-existe.db").exists()
    caminho = tmp_path / "vazio.db"
    sqlite3.connect(caminho).close()
    with pytest.raises(ValueError, match="Tabela usuario"):
        migrar_budget(caminho)
    assert not list(tmp_path.glob("*.antes-budget-*.db"))
