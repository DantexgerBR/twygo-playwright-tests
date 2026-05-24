"""
Sobe evidências de teste (screenshots, traces, vídeos) para o Cloudinary
e imprime os links públicos prontos para colar no bug report.

Uso:
    # sobe tudo que houver em test-results/
    python scripts/upload_evidencias.py

    # sobe um arquivo ou pasta específica
    python scripts/upload_evidencias.py test-results/marca_dagua-test_desmarcar
    python scripts/upload_evidencias.py caminho/para/imagem.png

Credenciais: defina CLOUDINARY_URL no .env (formato do Dashboard):
    CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME
"""
import sys
from pathlib import Path

import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

# Extensões que fazem sentido subir como evidência.
EXTENSOES = {".png", ".jpg", ".jpeg", ".webm", ".zip"}
PASTA_PADRAO = "test-results"


def resource_type_para(ext: str) -> str:
    if ext in {".png", ".jpg", ".jpeg"}:
        return "image"
    if ext == ".webm":
        return "video"
    return "raw"  # trace.zip e afins


def coletar_arquivos(alvo: Path) -> list[Path]:
    if alvo.is_file():
        return [alvo]
    return sorted(p for p in alvo.rglob("*") if p.suffix.lower() in EXTENSOES)


def main() -> int:
    if not cloudinary.config().cloud_name:
        print("ERRO: CLOUDINARY_URL não configurado no .env.", file=sys.stderr)
        print("      Pegue no Dashboard do Cloudinary (campo 'API environment variable').", file=sys.stderr)
        return 1

    alvo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(PASTA_PADRAO)
    if not alvo.exists():
        print(f"ERRO: '{alvo}' não existe. Rode um teste primeiro ou aponte um caminho.", file=sys.stderr)
        return 1

    arquivos = coletar_arquivos(alvo)
    if not arquivos:
        print(f"Nenhuma evidência ({', '.join(sorted(EXTENSOES))}) encontrada em '{alvo}'.")
        return 0

    print(f"Subindo {len(arquivos)} arquivo(s) para o Cloudinary...\n")
    for arq in arquivos:
        ext = arq.suffix.lower()
        # public_id legível: pasta do teste + nome do arquivo, sem extensão.
        public_id = f"twygo-evidencias/{arq.parent.name}/{arq.stem}"
        try:
            res = cloudinary.uploader.upload(
                str(arq),
                public_id=public_id,
                resource_type=resource_type_para(ext),
                overwrite=True,
                tags=["twygo", "evidencia"],
            )
            print(f"  {arq}\n    -> {res['secure_url']}\n")
        except Exception as e:  # noqa: BLE001 - queremos seguir nos demais arquivos
            print(f"  {arq}\n    !! FALHA: {e}\n", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
