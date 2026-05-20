"""Valida o parser com o caso da marca d'água (texto original colado pelo usuário)."""
import json
from ui.parser import parse_caso

TEXTO = """Verificar que ao desmarcar o checkbox 'Habilitar marca d'água no vídeo' em uma atividade previamente configurada e salvar, a marca d'água deixa de ser exibida no Aprender.
Pré-condições
Usuário logado como Admin Feature flag de marca d'água habilitada Atividade de vídeo previamente cadastrada com marca d'água habilitada Aluno previamente matriculado e capaz de acessar o conteúdo no Aprender

Perfil de usuário:
Tipo de ambiente:
#\tAções do Passo\tResultados Esperados:\tExecução\tNotas da Execução Limpar todas as notas\tStatus da Execução Limpar todos os estados
1\tAcessar a atividade de vídeo previamente cadastrada para editar\tFormulário de edição é exibido com o checkbox 'Habilitar marca d'água no vídeo' marcado\tManual
Testado na org: https://twygo1772627238.stage.twygoead.com/

19/05/2026

Passou

Arquivo: O tamanho máximo do arquivo é: 1048576 Bytes) Filename must verify this regexp:/^[a-zA-Z0-9_-]{1,20}\\.[a-zA-Z0-9]{1,10}$/ Allowed files:doc,xls,gif,png,jpg,xlsx,csvNo file chosen

2\tDesmarcar o checkbox 'Habilitar marca d'água no vídeo'\tCheckbox 'Habilitar marca d'água no vídeo' fica desmarcado. Todos os campos de configuração e preview são ocultados\tManual
Testado na org: https://twygo1772627238.stage.twygoead.com/

19/05/2026

Passou

Arquivo: ...

3\tClicar no botão 'Salvar'\tToast de sucesso exibida com o texto 'Alterações salvas com sucesso.'\tManual
Testado na org: https://twygo1772627238.stage.twygoead.com/

19/05/2026

Passou

4\tLogar como o aluno e acessar a atividade no Aprender\tVídeo é reproduzido. Marca d'água NÃO é exibida sobre o vídeo\tManual

Passou

ATENÇÃO: Ao guardar Passos da Execução Em Suspenso, os Anexos não serão guardados


Tipo de Execução : Manual
Estimação da duração da Execução (min) :
Perfil de usuário testado:
Administrador
Plataforma testada:
Desktop
Tipo ambiente testado:
Principal
"""


caso = parse_caso(TEXTO)
print(json.dumps(caso.to_dict(), indent=2, ensure_ascii=False))
print(f"\n→ Objetivo OK: {bool(caso.objetivo)}")
print(f"→ Pré-condições: {len(caso.pre_condicoes)} item(s)")
print(f"→ Passos: {len(caso.passos)}")
print(f"→ Perfil: {caso.perfil}")
print(f"→ Plataforma: {caso.plataforma}")
print(f"→ Ambiente: {caso.ambiente}")
