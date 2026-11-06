"""Progresso em JSON + detalhes incrementais, com retomada e lock local."""
import json
import os
from pathlib import Path
from datetime import datetime, timezone


class RelatorioOfertasService:
    CONTADORES = ('pecas', 'associadas', 'revisao', 'nao_encontradas', 'sem_ofertas',
        'falhas', 'requisicoes', 'ofertas_criadas', 'ofertas_atualizadas',
        'ofertas_inalteradas', 'ofertas_desativadas', 'historicos',
        'ignoradas_sem_minimos', 'consultas_reaproveitadas')

    def __init__(self, caminho, opcoes, *, retomar=False):
        self.caminho = Path(caminho)
        self.detalhes = self.caminho.with_suffix('.detalhes.jsonl')
        self.opcoes, self.retomar = opcoes, retomar
        self.anterior, self.cursores, self.emitidos = {}, {}, 0
        self.ultimo = None
        self.lock = None

    def __enter__(self):
        import fcntl
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self.lock = self.caminho.with_suffix('.lock').open('a')
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if self.retomar:
                dados = json.loads(self.caminho.read_text())
                if dados.get('versao_relatorio') != 1 or dados.get('opcoes') != self.opcoes:
                    raise ValueError('Banco ou filtros diferentes do relatório; use outro arquivo')
                if not self.detalhes.is_file():
                    raise ValueError('Arquivo de detalhes da execução ausente')
                self.anterior = dados
                self.cursores = dict(dados.get('cursores', {}))
            elif self.caminho.exists() or self.detalhes.exists():
                raise ValueError('Relatório já existe; use --retomar ou outro caminho')
            self.detalhes.touch(exist_ok=True)
            return self
        except BlockingIOError:
            self.lock.close()
            raise ValueError('Este relatório já está sendo usado por outra execução') from None
        except Exception:
            self.lock.close()
            raise

    def atualizar(self, resumo):
        linhas = resumo.get('detalhes', [])
        # Uma escrita por detalhe; nunca reescrever milhares de linhas por peça.
        novas = linhas if resumo.get('detalhes_incrementais') else linhas[self.emitidos:]
        if novas:
            with self.detalhes.open('a') as arquivo:
                for detalhe in novas:
                    arquivo.write(json.dumps(detalhe, ensure_ascii=False, default=str)+'\n')
            self.emitidos = len(linhas)
        resultado = {k:v for k,v in resumo.items() if k != 'detalhes'}
        if not resultado.get('ultima_peca_concluida'):
            resultado['ultima_peca_concluida'] = self.anterior.get('ultima_peca_concluida')
        for campo in self.CONTADORES:
            anterior = self.anterior.get(campo, 0)
            if campo == 'pecas':
                anterior -= self.anterior.get('falhas', 0)
            if campo == 'falhas':
                anterior = 0  # A peça falha é retomada; não contá-la duas vezes.
            resultado[campo] = anterior + resumo.get(campo, 0)
        resultado.update(versao_relatorio=1, opcoes=self.opcoes,
            atualizado_em=datetime.now(timezone.utc).isoformat(),
            falhas_anteriores=self.anterior.get('falhas_anteriores', 0)+self.anterior.get('falhas', 0),
            arquivo_detalhes=str(self.detalhes))
        temporario = self.caminho.with_suffix('.tmp')
        try:
            temporario.write_text(json.dumps(resultado, ensure_ascii=False, indent=2, default=str))
            os.replace(temporario, self.caminho)
        finally:
            if temporario.exists():temporario.unlink()
        self.ultimo = resultado

    def __exit__(self, *args):
        if self.lock:self.lock.close()
