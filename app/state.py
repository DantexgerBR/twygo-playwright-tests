"""Estado compartilhado do app entre as abas.

Implementa um observer pattern simples: views se inscrevem em eventos
via `state.on("documentacao_changed", callback)` e são notificadas
quando algo muda.

Persistência leve em `app/state.json` (gitignored).
"""
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Literal, Optional

from app.services.credentials import Credenciais


Modo = Literal["retrabalho", "caso_teste"]


@dataclass
class Documento:
    path: Path
    nome: str
    tipo: Literal["md", "txt", "pdf", "imagem"]
    conteudo: str = ""  # vazio para imagens
    tokens_estimados: int = 0


@dataclass
class Evidencia:
    path: Path
    nome: str
    tipo: Literal["print", "video", "link"]
    origem: Literal["upload", "paste", "jam"]


Laudo = Literal["corrigido", "ainda_quebrado", "inconclusivo"]


@dataclass
class ResultadoExecucao:
    laudo: Laudo
    justificativa: str
    screenshots: list[Path] = field(default_factory=list)
    log: list[str] = field(default_factory=list)
    iteracoes: int = 0
    # Evidência usada como referência (pra mostrar lado a lado no Resultado)
    evidencia_referencia: Optional[Path] = None
    # SHA do commit das evidências (preenchido após auto-commit)
    commit_sha: Optional[str] = None
    commit_url: Optional[str] = None


@dataclass
class CasoParseado:
    """Wrapper agnóstico ao Caso do ui/parser.py."""
    objetivo: str = ""
    pre_condicoes: list[str] = field(default_factory=list)
    passos: list[dict] = field(default_factory=list)
    perfil: Optional[str] = None
    plataforma: Optional[str] = None
    ambiente: Optional[str] = None
    texto_bruto: str = ""

    @property
    def tem_passos(self) -> bool:
        return len(self.passos) > 0


class AppState:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.modo: Modo = "retrabalho"
        self.credenciais: Credenciais = Credenciais()
        self.projeto_ativo: Optional[str] = None
        self.documentacao: list[Documento] = []
        self.caso: Optional[CasoParseado] = None
        self.evidencias: list[Evidencia] = []
        self.resultado: Optional[ResultadoExecucao] = None
        self._listeners: dict[str, list[Callable]] = defaultdict(list)

    # ---- Observer pattern ----

    def on(self, evento: str, callback: Callable) -> None:
        self._listeners[evento].append(callback)

    def emit(self, evento: str, *args, **kwargs) -> None:
        for cb in self._listeners.get(evento, []):
            try:
                cb(*args, **kwargs)
            except Exception as e:
                # Não derruba o app se um listener falhar
                print(f"[state] listener de '{evento}' falhou: {e}")

    # ---- Setters que disparam eventos ----

    def set_modo(self, modo: Modo) -> None:
        if modo == self.modo:
            return
        self.modo = modo
        self.persistir()
        self.emit("modo_changed", modo)

    def set_credenciais(self, cred: Credenciais) -> None:
        self.credenciais = cred
        self.emit("credenciais_changed", cred)

    def set_projeto_ativo(self, projeto: Optional[str]) -> None:
        self.projeto_ativo = projeto
        self.carregar_docs_do_projeto()
        self.persistir()
        self.emit("projeto_changed", projeto)

    def set_caso(self, caso: Optional[CasoParseado]) -> None:
        self.caso = caso
        self.emit("caso_changed", caso)

    def set_resultado(self, resultado: Optional[ResultadoExecucao]) -> None:
        self.resultado = resultado
        self.emit("resultado_changed", resultado)

    # ---- Documentação ----

    def pasta_do_projeto(self, projeto: str) -> Path:
        return self.project_root / "docs" / "projetos" / projeto

    def listar_projetos(self) -> list[str]:
        base = self.project_root / "docs" / "projetos"
        if not base.exists():
            return []
        return sorted([p.name for p in base.iterdir() if p.is_dir()])

    def criar_projeto(self, nome: str) -> bool:
        nome = nome.strip()
        if not nome:
            return False
        pasta = self.pasta_do_projeto(nome)
        if pasta.exists():
            return False
        pasta.mkdir(parents=True)
        self.emit("projetos_lista_changed", self.listar_projetos())
        return True

    def carregar_docs_do_projeto(self) -> None:
        from app.services.doc_loader import load_doc

        if not self.projeto_ativo:
            self.documentacao = []
            self.emit("documentacao_changed", self.documentacao)
            return

        pasta = self.pasta_do_projeto(self.projeto_ativo)
        if not pasta.exists():
            self.documentacao = []
        else:
            docs = []
            for p in sorted(pasta.iterdir()):
                if not p.is_file():
                    continue
                if p.name.startswith("_") or p.name.startswith("."):
                    continue
                try:
                    docs.append(load_doc(p))
                except Exception as e:
                    print(f"[state] falhou carregar {p.name}: {e}")
            self.documentacao = docs

        self.emit("documentacao_changed", self.documentacao)

    def adicionar_doc(self, source_path: Path) -> Optional[Documento]:
        """Copia o arquivo para a pasta do projeto e adiciona ao state."""
        from app.services.doc_loader import load_doc
        import shutil

        if not self.projeto_ativo:
            return None
        pasta = self.pasta_do_projeto(self.projeto_ativo)
        pasta.mkdir(parents=True, exist_ok=True)
        destino = pasta / source_path.name
        if not destino.exists():
            shutil.copy2(source_path, destino)
        doc = load_doc(destino)
        # Substitui se já existia (por nome)
        self.documentacao = [d for d in self.documentacao if d.nome != doc.nome]
        self.documentacao.append(doc)
        self.emit("documentacao_changed", self.documentacao)
        return doc

    def remover_doc(self, doc: Documento) -> None:
        if doc.path.exists():
            doc.path.unlink()
        self.documentacao = [d for d in self.documentacao if d.path != doc.path]
        self.emit("documentacao_changed", self.documentacao)

    # ---- Evidências (não persistem em disco; vivem só durante a execução) ----

    def adicionar_evidencia(
        self,
        path: Path,
        tipo: Literal["print", "video", "link"],
        origem: Literal["upload", "paste", "jam"],
    ) -> Evidencia:
        ev = Evidencia(path=path, nome=path.name, tipo=tipo, origem=origem)
        self.evidencias.append(ev)
        self.emit("evidencias_changed", self.evidencias)
        return ev

    def remover_evidencia(self, ev: Evidencia) -> None:
        self.evidencias = [e for e in self.evidencias if e.path != ev.path]
        self.emit("evidencias_changed", self.evidencias)

    def limpar_evidencias(self) -> None:
        self.evidencias = []
        self.emit("evidencias_changed", self.evidencias)

    def total_tokens_docs(self) -> int:
        return sum(d.tokens_estimados for d in self.documentacao)

    # ---- Persistência ----

    def _state_path(self) -> Path:
        return self.project_root / "app" / "state.json"

    def persistir(self) -> None:
        data = {
            "modo": self.modo,
            "projeto_ativo": self.projeto_ativo,
        }
        try:
            self._state_path().write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            print(f"[state] falhou persistir: {e}")

    def restaurar(self) -> None:
        sp = self._state_path()
        if not sp.exists():
            return
        try:
            data = json.loads(sp.read_text(encoding="utf-8"))
            self.modo = data.get("modo", "retrabalho")
            projeto = data.get("projeto_ativo")
            if projeto and projeto in self.listar_projetos():
                self.projeto_ativo = projeto
                self.carregar_docs_do_projeto()
        except Exception as e:
            print(f"[state] falhou restaurar: {e}")
