# -*- coding: utf-8 -*-

from __future__ import annotations

import base64
import ctypes
import csv
import json
import os
import random
import re
import shutil
import sys
import time
import traceback
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image, ImageOps

torch = None
nn = None
DataLoader = None
models = None
transforms = None
ERRO_TORCH: Exception | None = None
_TORCH_CARREGADO = False

from PyQt6.QtCore import QEvent, QRect, QSize, QThread, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QBrush, QColor, QFont, QIcon, QImage, QKeySequence, QPainter, QPen, QPixmap, QShortcut, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import (
    QAbstractSpinBox,
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QProgressBar,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QDoubleSpinBox,
)


if getattr(sys, "frozen", False):
    RAIZ = Path(sys.executable).resolve().parent
else:
    RAIZ = Path(__file__).resolve().parent
PASTA_RECURSOS = Path(getattr(sys, "_MEIPASS", RAIZ))
PASTA_APP = RAIZ / "BenaZub"
PASTA_LEGADA = RAIZ / "app_validador_auto_rotulos"
PASTA_UI = PASTA_APP / "ui"
PASTA_ENTRADA = PASTA_APP / "entrada" / "imagens"
PASTA_ROTULOS = PASTA_APP / "entrada" / "rotulos"
PASTA_SAIDA = PASTA_APP / "saida"
PASTA_MODELO = PASTA_SAIDA / "modelo_incremental"
PASTA_BACKUPS = PASTA_SAIDA / "backups_ciclo"
PASTA_TREINO = PASTA_SAIDA / "treino_base_atual"
PASTA_IMAGENS_TREINO = PASTA_TREINO / "imagens_rotuladas"
PASTA_ZIPS_EXTRAIDOS = PASTA_SAIDA / "zips_extraidos"

ARQUIVO_MODELO_BASE = RAIZ / "resultados" / "modelos" / "melhor_modelo.pt"
ARQUIVO_LIMIARES_BASE = RAIZ / "resultados" / "modelos" / "limiares.json"
ARQUIVO_MODELO_INCREMENTAL = PASTA_MODELO / "melhor_modelo.pt"
ARQUIVO_LIMIARES_INCREMENTAL = PASTA_MODELO / "limiares.json"
ARQUIVO_METRICAS_LIMIARES = PASTA_MODELO / "metricas_limiares.csv"
ARQUIVO_HISTORICO = PASTA_MODELO / "historico_treinamento.csv"
ARQUIVO_RESUMO_TREINO = PASTA_MODELO / "resumo_treinamento.json"

ARQUIVO_PREDICOES_JSON = PASTA_SAIDA / "predicoes_auto.json"
ARQUIVO_PREDICOES_CSV = PASTA_SAIDA / "predicoes_auto.csv"
ARQUIVO_REVISOES_JSON = PASTA_SAIDA / "revisoes.json"
ARQUIVO_CONFIRMADOS_CSV = PASTA_SAIDA / "rotulos_confirmados.csv"
ARQUIVO_CORRIGIR_CSV = PASTA_SAIDA / "rotulos_corrigir.csv"

CSV_BASE_ATUAL = PASTA_TREINO / "base_atual_rotulada.csv"
CSV_TREINO = PASTA_TREINO / "treino.csv"
CSV_VALIDACAO = PASTA_TREINO / "validacao.csv"
CSV_RESUMO_ROTULOS = PASTA_TREINO / "resumo_rotulos.csv"

ROTULOS_PADRAO = [
    "Digital Clara",
    "Digital Escura",
    "Dedo Fora Da Área",
    "Fiapos",
    "Fora de Foco",
    "Manchas",
    "Scanner Sujo",
    "Segmentação Boa",
    "Sem Padrão Visível",
]

MAPEAMENTO_BENAPRO = {
    "Manchas na Digital": "Manchas",
    "Fiapos na Digital": "Fiapos",
    "Dedo Fora da Área": "Dedo Fora Da Área",
}

EXTENSOES_IMAGEM = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}
CAMADAS = ["A", "B", "C", "D"]
SEMENTE = 42
TAMANHO_LOTE = 8
TAMANHO_LOTE_CALIBRACAO = 16
LIMIAR_PADRAO = 0.50
TELA_INICIAL_INDICE = 1


def agora() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def garantir_pastas() -> None:
    for pasta in [
        PASTA_UI,
        PASTA_ENTRADA,
        PASTA_ROTULOS,
        PASTA_SAIDA,
        PASTA_MODELO,
        PASTA_BACKUPS,
        PASTA_TREINO,
        PASTA_IMAGENS_TREINO,
        PASTA_ZIPS_EXTRAIDOS,
    ]:
        pasta.mkdir(parents=True, exist_ok=True)

    icones_ui = {
        "chevron-up.svg": '<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="#cfd7e6" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m18 15-6-6-6 6"/></svg>',
        "chevron-down.svg": '<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="#cfd7e6" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>',
    }

    for nome, conteudo in icones_ui.items():
        caminho = PASTA_UI / nome
        if not caminho.exists():
            caminho.write_text(conteudo, encoding="utf-8")


def caminho_icone_aplicativo() -> Path | None:
    candidatos = [
        RAIZ / "BenaZub_build.ico",
        RAIZ / "BenaZub.ico",
        PASTA_RECURSOS / "BenaZub_build.ico",
        PASTA_RECURSOS / "BenaZub.ico",
    ]

    for caminho in candidatos:
        if caminho.exists():
            return caminho

    return None


def configurar_app_user_model_id() -> None:
    if os.name != "nt":
        return

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("UTFPR.BenaZub.1.0")
    except Exception:
        pass


def aplicar_icone_aplicativo(app: QApplication | None = None, janela: QWidget | None = None) -> None:
    caminho = caminho_icone_aplicativo()
    if caminho is None:
        return

    icone = QIcon(str(caminho))
    if icone.isNull():
        return

    if app is not None:
        app.setWindowIcon(icone)

    if janela is not None:
        janela.setWindowIcon(icone)


def ler_json(caminho: Path, padrao):
    if not caminho.exists():
        return padrao

    try:
        with caminho.open("r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except Exception:
        return padrao


def salvar_json(caminho: Path, dados) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)

    with caminho.open("w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)


def ler_csv(caminho: Path) -> list[dict]:
    if not caminho.exists():
        return []

    with caminho.open("r", newline="", encoding="utf-8-sig") as arquivo:
        return list(csv.DictReader(arquivo))


def salvar_csv(caminho: Path, linhas: list[dict], campos: list[str]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)

    with caminho.open("w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(linhas)


def caminho_relativo(caminho: Path) -> str:
    try:
        return str(caminho.resolve().relative_to(RAIZ))
    except ValueError:
        return str(caminho.resolve())


def resolver_caminho(valor: str | Path | None) -> Path | None:
    if not valor:
        return None

    texto = str(valor).strip()

    if not texto:
        return None

    caminho = Path(texto)

    if caminho.exists():
        return caminho

    if not caminho.is_absolute():
        for base in [RAIZ, PASTA_APP]:
            candidato = (base / caminho).resolve()

            if candidato.exists():
                return candidato

    partes = list(caminho.parts)

    if "app_validador_auto_rotulos" in partes:
        indice = partes.index("app_validador_auto_rotulos")
        restante = partes[indice + 1:]

        candidato_novo = RAIZ.joinpath(*restante).resolve()
        if candidato_novo.exists():
            return candidato_novo

        candidato_antigo = PASTA_LEGADA.joinpath(*restante).resolve()
        if candidato_antigo.exists():
            return candidato_antigo

    return caminho


def caminho_modelo_ativo() -> Path:
    if ARQUIVO_MODELO_INCREMENTAL.exists():
        return ARQUIVO_MODELO_INCREMENTAL

    return ARQUIVO_MODELO_BASE


def caminho_limiares_ativo() -> Path:
    if ARQUIVO_LIMIARES_INCREMENTAL.exists():
        return ARQUIVO_LIMIARES_INCREMENTAL

    return ARQUIVO_LIMIARES_BASE


def carregar_limiares(rotulos: list[str]) -> dict[str, float]:
    caminho = caminho_limiares_ativo()
    dados = ler_json(caminho, {})

    return {rotulo: float(dados.get(rotulo, LIMIAR_PADRAO)) for rotulo in rotulos}


def detectar_rotulos() -> list[str]:
    predicoes = ler_json(ARQUIVO_PREDICOES_JSON, [])

    if isinstance(predicoes, list):
        for item in predicoes:
            probabilidades = item.get("probabilidades") if isinstance(item, dict) else None

            if isinstance(probabilidades, dict) and probabilidades:
                return list(probabilidades.keys())

    for caminho in [CSV_BASE_ATUAL, ARQUIVO_CONFIRMADOS_CSV]:
        linhas = ler_csv(caminho)

        if linhas:
            campos = list(linhas[0].keys())
            rotulos = [campo for campo in campos if campo in ROTULOS_PADRAO]

            if rotulos:
                return rotulos

    limiares = ler_json(caminho_limiares_ativo(), {})

    if isinstance(limiares, dict) and limiares:
        return list(limiares.keys())

    return list(ROTULOS_PADRAO)


def normalizar_rotulo_benapro(nome: str) -> str:
    return MAPEAMENTO_BENAPRO.get(nome, nome)


def chave_sem_camada(caminho: Path) -> str:
    match = re.match(r"(.+)_([ABCD])$", caminho.stem, flags=re.IGNORECASE)
    return match.group(1) if match else caminho.stem


def camada_do_arquivo(caminho: Path) -> str:
    match = re.match(r".+_([ABCD])$", caminho.stem, flags=re.IGNORECASE)
    return match.group(1).upper() if match else "A"


def arquivo_eh_imagem(caminho: Path) -> bool:
    return caminho.is_file() and caminho.suffix.lower() in EXTENSOES_IMAGEM


def id_da_imagem(caminho: Path) -> str:
    texto = caminho_relativo(caminho)
    return base64.urlsafe_b64encode(texto.encode("utf-8")).decode("ascii").rstrip("=")


def aplicar_regras_predicao(detectados: list[str], probabilidades: dict[str, float], rotulos: list[str]) -> list[str]:
    finais = set(detectados)

    if "Digital Clara" in finais and "Digital Escura" in finais:
        if probabilidades.get("Digital Clara", 0.0) >= probabilidades.get("Digital Escura", 0.0):
            finais.discard("Digital Escura")
        else:
            finais.discard("Digital Clara")

    if "Segmentação Boa" in finais and len(finais) > 1:
        finais.discard("Segmentação Boa")

    return [rotulo for rotulo in rotulos if rotulo in finais]


def carregar_imagem_modelo(caminho: Path) -> Image.Image:
    with Image.open(caminho) as imagem:
        if imagem.mode == "RGBA":
            return imagem.getchannel("A").convert("RGB")

        return ImageOps.grayscale(imagem).convert("RGB")


def carregar_imagem_tela(caminho: Path, camada: str) -> Image.Image:
    with Image.open(caminho) as imagem:
        if imagem.mode == "RGBA":
            canal = "R" if camada == "R" else "A"
            return imagem.getchannel(canal).convert("RGB")

        return ImageOps.grayscale(imagem).convert("RGB")


def pil_para_pixmap(imagem: Image.Image) -> QPixmap:
    imagem = imagem.convert("RGB")
    largura, altura = imagem.size
    dados = imagem.tobytes("raw", "RGB")
    qimg = QImage(dados, largura, altura, largura * 3, QImage.Format.Format_RGB888).copy()
    return QPixmap.fromImage(qimg)


def requer_torch() -> None:
    global torch, nn, DataLoader, models, transforms, ERRO_TORCH, _TORCH_CARREGADO

    if _TORCH_CARREGADO:
        if ERRO_TORCH is not None:
            raise RuntimeError(f"Torch/TorchVision nÃ£o carregou: {ERRO_TORCH}") from ERRO_TORCH

        return

    try:
        import torch as torch_modulo
        from torch import nn as nn_modulo
        from torch.utils.data import DataLoader as DataLoader_modulo
        from torchvision import models as models_modulo, transforms as transforms_modulo
    except Exception as erro:  # pragma: no cover - a interface ainda deve abrir sem treino.
        ERRO_TORCH = erro
        _TORCH_CARREGADO = True
        raise RuntimeError(f"Torch/TorchVision nÃ£o carregou: {erro}") from erro

    torch = torch_modulo
    nn = nn_modulo
    DataLoader = DataLoader_modulo
    models = models_modulo
    transforms = transforms_modulo
    ERRO_TORCH = None
    _TORCH_CARREGADO = True
    if ERRO_TORCH is not None:
        raise RuntimeError(f"Torch/TorchVision não carregou: {ERRO_TORCH}")


def carregar_checkpoint(caminho: Path, dispositivo):
    requer_torch()

    try:
        return torch.load(caminho, map_location=dispositivo, weights_only=False)
    except TypeError:
        return torch.load(caminho, map_location=dispositivo)


def criar_modelo(
    numero_rotulos: int,
    usar_pesos_pre_treinados: bool = False,
    congelar_extrator: bool = False,
):
    requer_torch()

    pesos = None

    if usar_pesos_pre_treinados:
        try:
            pesos = models.EfficientNet_B0_Weights.DEFAULT
        except Exception:
            pesos = None

    try:
        modelo = models.efficientnet_b0(weights=pesos)
    except Exception:
        modelo = models.efficientnet_b0(weights=None)

    if congelar_extrator:
        for parametro in modelo.features.parameters():
            parametro.requires_grad = False

    entrada = modelo.classifier[1].in_features
    modelo.classifier[1] = nn.Linear(entrada, numero_rotulos)
    return modelo


def carregar_modelo(log: Callable[[str], None] | None = None, criar_se_nao_existir: bool = False):
    requer_torch()

    caminho = caminho_modelo_ativo()
    dispositivo = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if not caminho.exists():
        if not criar_se_nao_existir:
            raise FileNotFoundError(f"Modelo não encontrado: {caminho}")

        rotulos = detectar_rotulos()
        tamanho = 224
        modelo = criar_modelo(
            len(rotulos),
            usar_pesos_pre_treinados=True,
            congelar_extrator=True,
        )
        modelo.to(dispositivo)

        checkpoint = {
            "rotulos": rotulos,
            "tamanho_imagem": tamanho,
            "macro_f1_validacao": None,
            "observacao": "Modelo inicial criado do zero pelo BenaZub.",
        }

        if log:
            log("Modelo base não encontrado. Criando modelo inicial do zero.\n")
            log(f"Dispositivo: {dispositivo}\n")
            log(f"Quantidade de rótulos: {len(rotulos)}\n")

        return modelo, rotulos, tamanho, checkpoint, dispositivo, None

    if log:
        log(f"Carregando modelo: {caminho}\n")
        log(f"Dispositivo: {dispositivo}\n")

    checkpoint = carregar_checkpoint(caminho, dispositivo)
    rotulos = list(checkpoint.get("rotulos") or detectar_rotulos())
    modelo = criar_modelo(len(rotulos))
    modelo.load_state_dict(checkpoint["modelo_estado"])
    modelo.to(dispositivo)
    modelo.eval()
    tamanho = int(checkpoint.get("tamanho_imagem", 224))

    return modelo, rotulos, tamanho, checkpoint, dispositivo, caminho


def criar_transform(tamanho: int, treino: bool = False):
    requer_torch()

    if treino:
        return transforms.Compose([
            transforms.Resize((tamanho, tamanho)),
            transforms.RandomRotation(degrees=6),
            transforms.ColorJitter(brightness=0.10, contrast=0.10),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    return transforms.Compose([
        transforms.Resize((tamanho, tamanho)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])


def chaves_ja_rotuladas(caminho_rotulos: Path | None) -> set[str]:
    if caminho_rotulos is None or not caminho_rotulos.exists():
        return set()

    chaves: set[str] = set()

    if caminho_rotulos.suffix.lower() == ".csv":
        for linha in ler_csv(caminho_rotulos):
            for campo in ["chave_amostra", "chave", "id"]:
                if linha.get(campo):
                    chaves.add(str(linha[campo]))

            if linha.get("caminho_imagem"):
                chaves.add(Path(linha["caminho_imagem"]).stem)

        return chaves

    dados = ler_json(caminho_rotulos, [])
    itens = dados.values() if isinstance(dados, dict) else dados

    for item in itens:
        if isinstance(item, list):
            for subitem in item:
                if isinstance(subitem, dict):
                    nome = subitem.get("arquivo") or subitem.get("caminho_imagem") or subitem.get("chave")

                    if nome:
                        chaves.add(Path(str(nome)).stem)
        elif isinstance(item, dict):
            nome = item.get("arquivo") or item.get("caminho_imagem") or item.get("chave")

            if nome:
                chaves.add(Path(str(nome)).stem)

    return chaves


def listar_grupos_imagens(pasta_imagens: Path, chaves_pular: set[str]) -> list[dict]:
    if not pasta_imagens.exists():
        return []

    grupos: dict[str, dict] = {}

    for caminho in sorted(pasta_imagens.rglob("*")):
        if not arquivo_eh_imagem(caminho):
            continue

        chave = chave_sem_camada(caminho)

        if chave in chaves_pular or caminho.stem in chaves_pular:
            continue

        grupo = grupos.setdefault(chave, {"chave": chave, "arquivos": {}, "principal": caminho})
        grupo["arquivos"][camada_do_arquivo(caminho)] = caminho

        if camada_do_arquivo(caminho) == "A":
            grupo["principal"] = caminho

    return list(grupos.values())


def extrair_membro_zip_seguro(arquivo_zip: zipfile.ZipFile, membro: zipfile.ZipInfo, destino_base: Path) -> Path | None:
    partes = [parte for parte in re.split(r"[\\/]+", membro.filename) if parte and parte not in [".", ".."]]

    if not partes:
        return None

    destino_base = destino_base.resolve()
    destino = destino_base.joinpath(*partes).resolve()

    if not str(destino).startswith(str(destino_base)):
        return None

    destino.parent.mkdir(parents=True, exist_ok=True)

    if destino.exists() and destino.stat().st_size == membro.file_size:
        return destino

    with arquivo_zip.open(membro) as origem, destino.open("wb") as saida:
        shutil.copyfileobj(origem, saida, length=1024 * 1024)

    return destino


def caminho_eh_zip(caminho: Path) -> bool:
    return caminho.is_file() and caminho.suffix.lower() == ".zip"


def nome_seguro_para_pasta(texto: str) -> str:
    nome = re.sub(r"[^A-Za-z0-9._-]+", "_", texto).strip("._-")
    return nome or "zip_extraido"


def destino_extracao_zip(zip_path: Path) -> Path:
    try:
        relativo = zip_path.resolve().relative_to(RAIZ)
        base = nome_seguro_para_pasta(str(relativo.with_suffix("")))
    except ValueError:
        base = nome_seguro_para_pasta(zip_path.stem)

    return PASTA_ZIPS_EXTRAIDOS / base


def extrair_zip_imagens(zip_path: Path, log: Callable[[str], None]) -> Path:
    destino = destino_extracao_zip(zip_path)
    destino.mkdir(parents=True, exist_ok=True)
    total = 0

    log(f"Extraindo ZIP de imagens: {zip_path}\n")

    with zipfile.ZipFile(zip_path, "r") as arquivo_zip:
        for membro in arquivo_zip.infolist():
            if membro.is_dir() or Path(membro.filename).suffix.lower() not in EXTENSOES_IMAGEM:
                continue

            if extrair_membro_zip_seguro(arquivo_zip, membro, destino):
                total += 1

    log(f"ZIP extraído para: {destino} | {total} imagem(ns) encontrada(s).\n")
    return destino


def combinar_grupos_imagens(grupos_lista: list[dict]) -> list[dict]:
    combinados: dict[str, dict] = {}

    for grupo in grupos_lista:
        chave = str(grupo.get("chave", ""))
        if not chave:
            continue

        atual = combinados.setdefault(
            chave,
            {
                "chave": chave,
                "arquivos": {},
                "principal": grupo.get("principal"),
            },
        )

        arquivos = grupo.get("arquivos", {})
        if isinstance(arquivos, dict):
            atual["arquivos"].update(arquivos)

            if "A" in arquivos:
                atual["principal"] = arquivos["A"]

        if atual.get("principal") is None:
            atual["principal"] = grupo.get("principal")

    return list(combinados.values())


def listar_grupos_imagens_com_zip(origem: Path, chaves_pular: set[str], log: Callable[[str], None]) -> list[dict]:
    if caminho_eh_zip(origem):
        pasta_extraida = extrair_zip_imagens(origem, log)
        return listar_grupos_imagens(pasta_extraida, chaves_pular)

    if not origem.exists():
        return []

    grupos = listar_grupos_imagens(origem, chaves_pular)

    if origem.is_dir():
        zips = sorted(
            caminho
            for caminho in origem.rglob("*.zip")
            if caminho.is_file()
        )

        for zip_path in zips:
            pasta_extraida = extrair_zip_imagens(zip_path, log)
            grupos.extend(listar_grupos_imagens(pasta_extraida, chaves_pular))

    return combinar_grupos_imagens(grupos)


def importar_pacotes_benapro(destino: Path, log: Callable[[str], None], somente_nao_rotuladas: bool = True) -> int:
    total = 0

    for json_resultado in sorted(PASTA_APP.glob("*/BENAPRO/resultado.json")):
        pasta_pacote = json_resultado.parent.parent
        zips = sorted(pasta_pacote.glob("*.zip"))

        if not zips:
            continue

        dados = ler_json(json_resultado, {})
        rotuladas = set()

        for itens in dados.values():
            if not isinstance(itens, list):
                continue

            for item in itens:
                if isinstance(item, dict) and item.get("arquivo"):
                    rotuladas.add(Path(str(item["arquivo"])).name)

        for zip_path in zips:
            log(f"Importando pacote BENAPRO: {zip_path.name}\n")
            destino_zip = destino / pasta_pacote.name / zip_path.stem

            with zipfile.ZipFile(zip_path, "r") as arquivo_zip:
                for membro in arquivo_zip.infolist():
                    if membro.is_dir() or Path(membro.filename).suffix.lower() not in EXTENSOES_IMAGEM:
                        continue

                    if somente_nao_rotuladas and Path(membro.filename).name in rotuladas:
                        continue

                    if extrair_membro_zip_seguro(arquivo_zip, membro, destino_zip):
                        total += 1

    return total


def predizer_imagem(modelo, transform, dispositivo, caminho: Path, rotulos: list[str], limiares: dict[str, float]) -> dict:
    requer_torch()

    inicio = time.perf_counter()
    imagem = carregar_imagem_modelo(caminho)
    tensor = transform(imagem).unsqueeze(0).to(dispositivo)

    with torch.no_grad():
        logits = modelo(tensor)
        probs = torch.sigmoid(logits).cpu().numpy()[0]

    probabilidades = {rotulo: float(probs[indice]) for indice, rotulo in enumerate(rotulos)}
    detectados_brutos = [
        rotulo
        for rotulo in rotulos
        if probabilidades[rotulo] >= float(limiares.get(rotulo, LIMIAR_PADRAO))
    ]
    detectados = aplicar_regras_predicao(detectados_brutos, probabilidades, rotulos)

    if detectados:
        margem = min(probabilidades[rotulo] - limiares.get(rotulo, LIMIAR_PADRAO) for rotulo in detectados)
    else:
        margem = max(probabilidades[rotulo] - limiares.get(rotulo, LIMIAR_PADRAO) for rotulo in rotulos)

    return {
        "rotulos_detectados": detectados,
        "rotulos_detectados_brutos": detectados_brutos,
        "probabilidades": probabilidades,
        "limiares": limiares,
        "maior_probabilidade": float(max(probabilidades.values()) if probabilidades else 0.0),
        "margem_minima_limiar": float(margem),
        "latencia_inferencia_segundos": float(time.perf_counter() - inicio),
    }


def carregar_revisoes() -> dict[str, dict]:
    dados = ler_json(ARQUIVO_REVISOES_JSON, {})

    if isinstance(dados, list):
        return {str(item.get("id")): item for item in dados if isinstance(item, dict) and item.get("id")}

    if isinstance(dados, dict):
        return {str(chave): valor for chave, valor in dados.items() if isinstance(valor, dict)}

    return {}


def aplicar_revisoes(predicoes: list[dict], revisoes: dict[str, dict]) -> list[dict]:
    saida = []

    for item in predicoes:
        novo = dict(item)
        revisao = revisoes.get(str(item.get("id", "")))

        if revisao:
            novo["status_revisao"] = revisao.get("status", item.get("status_revisao", "pendente"))
            novo["rotulos_confirmados"] = list(revisao.get("rotulos_confirmados", []))
        else:
            novo.setdefault("status_revisao", "pendente")
            novo.setdefault("rotulos_confirmados", [])

        saida.append(novo)

    return saida


def salvar_predicoes_csv(predicoes: list[dict], rotulos: list[str]) -> None:
    campos = ["id", "chave", "caminho_imagem", "rotulos_detectados", "status_revisao", "margem_minima_limiar"]

    for rotulo in rotulos:
        campos.extend([f"{rotulo}_probabilidade", f"{rotulo}_limiar", rotulo])

    linhas = []

    for item in predicoes:
        detectados = set(item.get("rotulos_detectados", []))
        linha = {
            "id": item.get("id", ""),
            "chave": item.get("chave", ""),
            "caminho_imagem": item.get("caminho_imagem", ""),
            "rotulos_detectados": "; ".join(item.get("rotulos_detectados", [])),
            "status_revisao": item.get("status_revisao", "pendente"),
            "margem_minima_limiar": item.get("margem_minima_limiar", ""),
        }

        probabilidades = item.get("probabilidades", {})
        limiares = item.get("limiares", {})

        for rotulo in rotulos:
            linha[f"{rotulo}_probabilidade"] = probabilidades.get(rotulo, "")
            linha[f"{rotulo}_limiar"] = limiares.get(rotulo, "")
            linha[rotulo] = "1" if rotulo in detectados else "0"

        linhas.append(linha)

    salvar_csv(ARQUIVO_PREDICOES_CSV, linhas, campos)


def exportar_resultados(predicoes: list[dict], revisoes: dict[str, dict], rotulos: list[str]) -> None:
    campos = [
        "id",
        "chave_amostra",
        "caminho_imagem",
        "status_revisao",
        "rotulos_confirmados",
        "quantidade_rotulos",
    ] + rotulos
    confirmados = []
    corrigir = []

    for item in predicoes:
        revisao = revisoes.get(str(item.get("id", "")))

        if not revisao:
            continue

        status = revisao.get("status", "corrigir")
        selecionados = list(revisao.get("rotulos_confirmados", []))
        valores = {rotulo: "1" if rotulo in selecionados else "0" for rotulo in rotulos}
        linha = {
            "id": item.get("id", ""),
            "chave_amostra": item.get("chave", ""),
            "caminho_imagem": item.get("caminho_imagem", ""),
            "status_revisao": status,
            "rotulos_confirmados": "; ".join(selecionados),
            "quantidade_rotulos": str(len(selecionados)),
            **valores,
        }

        if status == "confirmado":
            confirmados.append(linha)
        elif status == "corrigir":
            corrigir.append(linha)

    salvar_csv(ARQUIVO_CONFIRMADOS_CSV, confirmados, campos)
    salvar_csv(ARQUIVO_CORRIGIR_CSV, corrigir, campos)


def gerar_predicoes(
    pasta_imagens: Path,
    arquivo_rotulos: Path | None,
    importar_benapro: bool,
    forcar: bool,
    log: Callable[[str], None],
    deve_parar: Callable[[], bool],
) -> tuple[list[dict], list[str]]:
    garantir_pastas()

    if importar_benapro:
        qtd = importar_pacotes_benapro(pasta_imagens, log)
        log(f"Pacotes BENAPRO: {qtd} imagem(ns) verificadas/importadas.\n")

    if ARQUIVO_PREDICOES_JSON.exists() and not forcar:
        predicoes = ler_json(ARQUIVO_PREDICOES_JSON, [])
        rotulos = detectar_rotulos()
        revisoes = carregar_revisoes()
        predicoes = aplicar_revisoes(predicoes, revisoes)
        salvar_predicoes_csv(predicoes, rotulos)
        exportar_resultados(predicoes, revisoes, rotulos)
        log("Predições carregadas do cache. Marque 'Recalcular predições' para rodar o modelo de novo.\n")
        return predicoes, rotulos

    modelo, rotulos, tamanho, _checkpoint, dispositivo, caminho_modelo = carregar_modelo(log)
    limiares = carregar_limiares(rotulos)
    transform = criar_transform(tamanho)
    chaves_pular = chaves_ja_rotuladas(arquivo_rotulos)
    grupos = listar_grupos_imagens_com_zip(pasta_imagens, chaves_pular, log)

    log(f"Modelo ativo: {caminho_modelo}\n")
    log(f"Origem das imagens: {pasta_imagens}\n")
    log(f"Imagens/grupos na fila: {len(grupos)}\n")

    predicoes = []

    for indice, grupo in enumerate(grupos, start=1):
        if deve_parar():
            raise InterruptedError("Geração de predições interrompida.")

        caminho = grupo["principal"]
        resultado = predizer_imagem(modelo, transform, dispositivo, caminho, rotulos, limiares)
        item = {
            "id": id_da_imagem(caminho),
            "indice": indice - 1,
            "chave": grupo["chave"],
            "caminho_imagem": caminho_relativo(caminho),
            "arquivos": {camada: caminho_relativo(valor) for camada, valor in grupo["arquivos"].items()},
            "status_revisao": "pendente",
            "rotulos_confirmados": [],
            **resultado,
        }
        predicoes.append(item)

        if indice == 1 or indice % 25 == 0 or indice == len(grupos):
            log(f"Predições: {indice}/{len(grupos)}\n")

    revisoes = carregar_revisoes()
    predicoes = aplicar_revisoes(predicoes, revisoes)
    salvar_json(ARQUIVO_PREDICOES_JSON, predicoes)
    salvar_predicoes_csv(predicoes, rotulos)
    exportar_resultados(predicoes, revisoes, rotulos)
    log(f"Predições salvas: {ARQUIVO_PREDICOES_JSON}\n")
    return predicoes, rotulos


def linha_rotulos(rotulos_linha: dict[str, int], rotulos: list[str]) -> dict[str, str]:
    return {rotulo: str(int(rotulos_linha.get(rotulo, 0))) for rotulo in rotulos}


def linhas_benapro(rotulos: list[str], log: Callable[[str], None]) -> list[dict]:
    linhas = []

    for json_resultado in sorted(PASTA_APP.glob("*/BENAPRO/resultado.json")):
        pasta_pacote = json_resultado.parent.parent
        zips = sorted(pasta_pacote.glob("*.zip"))

        if not zips:
            continue

        dados = ler_json(json_resultado, {})

        for zip_path in zips:
            itens = dados.get(zip_path.name)

            if not itens and len(dados) == 1:
                itens = next(iter(dados.values()))

            if not isinstance(itens, list):
                continue

            destino_zip = PASTA_IMAGENS_TREINO / pasta_pacote.name / zip_path.stem

            log(f"Preparando rótulos BENAPRO: {zip_path.name}\n")

            with zipfile.ZipFile(zip_path, "r") as arquivo_zip:
                indice_zip = {
                    Path(membro.filename).name: membro
                    for membro in arquivo_zip.infolist()
                    if not membro.is_dir()
                }

                for item in itens:
                    nome_arquivo = str(item.get("arquivo", ""))
                    membro = indice_zip.get(Path(nome_arquivo).name)

                    if membro is None:
                        continue

                    caminho = extrair_membro_zip_seguro(arquivo_zip, membro, destino_zip)

                    if caminho is None:
                        continue

                    valores = {rotulo: 0 for rotulo in rotulos}

                    for erro in item.get("erros", []):
                        nome = normalizar_rotulo_benapro(str(erro.get("nome", "")))

                        if nome in valores:
                            valores[nome] = 1

                    qtd = sum(valores.values())

                    linhas.append({
                        "id": f"{pasta_pacote.name}__{Path(nome_arquivo).stem}",
                        "chave_amostra": Path(nome_arquivo).stem,
                        "conjunto": pasta_pacote.name,
                        "origem_rotulo": "benapro_resultado_json",
                        "caminho_imagem": caminho_relativo(caminho),
                        "quantidade_rotulos": str(qtd),
                        **linha_rotulos(valores, rotulos),
                    })

    return linhas

def linhas_rotulos_arquivo_interface(
    origem_imagens: Path,
    arquivo_rotulos: Path | None,
    rotulos: list[str],
    log: Callable[[str], None],
) -> list[dict]:
    if arquivo_rotulos is None or not arquivo_rotulos.exists():
        return []

    if arquivo_rotulos.suffix.lower() != ".json":
        log("Arquivo de rótulos selecionado não é JSON. Ele será ignorado no treino inicial.\n")
        return []

    dados = ler_json(arquivo_rotulos, {})
    if not isinstance(dados, dict):
        log("Arquivo JSON de rótulos inválido. Esperado: objeto com nome do ZIP como chave.\n")
        return []

    if caminho_eh_zip(origem_imagens):
        zips = [origem_imagens]
    elif origem_imagens.is_dir():
        zips = sorted(caminho for caminho in origem_imagens.rglob("*.zip") if caminho.is_file())
    else:
        zips = []

    if not zips:
        log("Nenhum ZIP encontrado para cruzar com o JSON de rótulos selecionado.\n")
        return []

    linhas = []

    for zip_path in zips:
        itens = dados.get(zip_path.name)

        if not itens and len(dados) == 1:
            itens = next(iter(dados.values()))

        if not isinstance(itens, list):
            continue

        destino_zip = PASTA_IMAGENS_TREINO / "arquivo_interface" / zip_path.stem

        log(f"Preparando rótulos do arquivo selecionado: {zip_path.name}\n")

        with zipfile.ZipFile(zip_path, "r") as arquivo_zip:
            indice_zip = {
                Path(membro.filename).name: membro
                for membro in arquivo_zip.infolist()
                if not membro.is_dir()
            }

            for item in itens:
                if not isinstance(item, dict):
                    continue

                nome_arquivo = str(item.get("arquivo", ""))
                if not nome_arquivo:
                    continue

                membro = indice_zip.get(Path(nome_arquivo).name)

                if membro is None:
                    log(f"Imagem anotada não encontrada no ZIP: {nome_arquivo}\n")
                    continue

                caminho = extrair_membro_zip_seguro(arquivo_zip, membro, destino_zip)

                if caminho is None:
                    continue

                valores = {rotulo: 0 for rotulo in rotulos}

                for erro in item.get("erros", []):
                    if not isinstance(erro, dict):
                        continue

                    nome = normalizar_rotulo_benapro(str(erro.get("nome", "")))

                    if nome in valores:
                        valores[nome] = 1

                qtd = sum(valores.values())

                linhas.append({
                    "id": f"arquivo_interface__{zip_path.stem}__{Path(nome_arquivo).stem}",
                    "chave_amostra": Path(nome_arquivo).stem,
                    "conjunto": f"arquivo_interface_{zip_path.stem}",
                    "origem_rotulo": "arquivo_json_interface",
                    "caminho_imagem": caminho_relativo(caminho),
                    "quantidade_rotulos": str(qtd),
                    **linha_rotulos(valores, rotulos),
                })

    log(f"Rótulos carregados do arquivo selecionado: {len(linhas)} imagem(ns).\n")
    return linhas

def linhas_confirmadas_app(rotulos: list[str]) -> list[dict]:
    linhas = []

    for linha in ler_csv(ARQUIVO_CONFIRMADOS_CSV):
        if linha.get("status_revisao") != "confirmado":
            continue

        valores = {rotulo: int(float(linha.get(rotulo, 0) or 0)) for rotulo in rotulos}
        qtd = sum(valores.values())

        linhas.append({
            "id": linha.get("id", ""),
            "chave_amostra": linha.get("chave_amostra", ""),
            "conjunto": "confirmado_app",
            "origem_rotulo": "confirmado_app",
            "caminho_imagem": linha.get("caminho_imagem", ""),
            "quantidade_rotulos": str(qtd),
            **linha_rotulos(valores, rotulos),
        })

    return linhas


def preparar_base_treino(
    fracao_validacao: float,
    rotulos: list[str],
    log: Callable[[str], None],
    origem_imagens: Path | None = None,
    arquivo_rotulos: Path | None = None,
) -> tuple[list[dict], list[dict], list[dict]]:
    garantir_pastas()

    linhas = []

    if origem_imagens is not None and arquivo_rotulos is not None:
        linhas.extend(linhas_rotulos_arquivo_interface(origem_imagens, arquivo_rotulos, rotulos, log))

    linhas.extend(linhas_benapro(rotulos, log))
    linhas.extend(linhas_confirmadas_app(rotulos))

    vistos = set()
    unicas = []

    for linha in linhas:
        chave = (linha.get("conjunto", ""), linha.get("chave_amostra", ""), linha.get("origem_rotulo", ""))

        if chave in vistos:
            continue

        vistos.add(chave)
        unicas.append(linha)

    rng = random.Random(SEMENTE)
    rng.shuffle(unicas)

    if len(unicas) < 2:
        raise RuntimeError("Base rotulada insuficiente para treino.")

    if len(unicas) < 10:
        log("Base pequena detectada. Usando todas as imagens em treino e validação apenas para demonstração.\n")
        treino = list(unicas)
        validacao = list(unicas)
    else:
        qtd_validacao = max(1, min(len(unicas) - 1, int(round(len(unicas) * fracao_validacao))))
        validacao = unicas[:qtd_validacao]
        treino = unicas[qtd_validacao:]
    campos = ["id", "chave_amostra", "conjunto", "origem_rotulo", "caminho_imagem", "quantidade_rotulos"] + rotulos

    salvar_csv(CSV_BASE_ATUAL, unicas, campos)
    salvar_csv(CSV_TREINO, treino, campos)
    salvar_csv(CSV_VALIDACAO, validacao, campos)

    resumo = [
        {"item": "total_imagens_rotuladas", "valor": len(unicas)},
        {"item": "origem_benapro_resultado_json", "valor": sum(1 for linha in unicas if linha["origem_rotulo"] == "benapro_resultado_json")},
        {"item": "origem_confirmado_app", "valor": sum(1 for linha in unicas if linha["origem_rotulo"] == "confirmado_app")},
    ]

    for rotulo in rotulos:
        resumo.append({"item": f"quantidade_{rotulo}", "valor": sum(int(linha.get(rotulo, 0) or 0) for linha in unicas)})

    salvar_csv(CSV_RESUMO_ROTULOS, resumo, ["item", "valor"])
    return unicas, treino, validacao


class BaseRotulada:
    def __init__(self, caminho_csv: Path, rotulos: list[str], transform=None):
        self.linhas = ler_csv(caminho_csv)
        self.rotulos = rotulos
        self.transform = transform

        if not self.linhas:
            raise RuntimeError(f"CSV vazio: {caminho_csv}")

    def __len__(self):
        return len(self.linhas)

    def __getitem__(self, indice):
        linha = self.linhas[indice]
        caminho = resolver_caminho(linha.get("caminho_imagem", ""))

        if caminho is None or not caminho.exists():
            raise FileNotFoundError(f"Imagem não encontrada: {linha.get('caminho_imagem', '')}")

        imagem = carregar_imagem_modelo(caminho)

        if self.transform:
            imagem = self.transform(imagem)

        y = torch.tensor([float(linha.get(rotulo, 0) or 0) for rotulo in self.rotulos], dtype=torch.float32)
        return imagem, y


def calcular_pos_weight(caminho_csv: Path, rotulos: list[str]):
    requer_torch()

    linhas = ler_csv(caminho_csv)
    total = len(linhas)
    pesos = []

    for rotulo in rotulos:
        positivos = sum(int(float(linha.get(rotulo, 0) or 0)) for linha in linhas)
        negativos = total - positivos
        pesos.append(1.0 if positivos == 0 else negativos / positivos)

    return torch.tensor(pesos, dtype=torch.float32)


def calcular_metricas(y_true, y_prob, rotulos: list[str], limiar: float = LIMIAR_PADRAO):
    y_pred_bruto = (y_prob >= limiar).astype(np.int32)
    y_pred = np.zeros_like(y_pred_bruto)

    for indice_linha in range(y_pred_bruto.shape[0]):
        detectados = [
            rotulo
            for indice_rotulo, rotulo in enumerate(rotulos)
            if y_pred_bruto[indice_linha, indice_rotulo] == 1
        ]
        probabilidades = {rotulo: float(y_prob[indice_linha, indice]) for indice, rotulo in enumerate(rotulos)}
        finais = aplicar_regras_predicao(detectados, probabilidades, rotulos)

        for indice_rotulo, rotulo in enumerate(rotulos):
            y_pred[indice_linha, indice_rotulo] = int(rotulo in finais)

    y_true = y_true.astype(np.int32)
    f1s = []

    for indice in range(y_true.shape[1]):
        verdadeiro = y_true[:, indice]
        predito = y_pred[:, indice]
        tp = np.sum((verdadeiro == 1) & (predito == 1))
        fp = np.sum((verdadeiro == 0) & (predito == 1))
        fn = np.sum((verdadeiro == 1) & (predito == 0))
        precisao = tp / (tp + fp + 1e-8)
        revocacao = tp / (tp + fn + 1e-8)
        f1s.append(2 * precisao * revocacao / (precisao + revocacao + 1e-8))

    macro_f1 = float(np.mean(f1s))
    tp_total = np.sum((y_true == 1) & (y_pred == 1))
    fp_total = np.sum((y_true == 0) & (y_pred == 1))
    fn_total = np.sum((y_true == 1) & (y_pred == 0))
    precisao_micro = tp_total / (tp_total + fp_total + 1e-8)
    revocacao_micro = tp_total / (tp_total + fn_total + 1e-8)
    micro_f1 = float(2 * precisao_micro * revocacao_micro / (precisao_micro + revocacao_micro + 1e-8))
    return macro_f1, micro_f1


def executar_epoca(modelo, loader, criterio, dispositivo, rotulos: list[str], otimizador=None, deve_parar: Callable[[], bool] | None = None):
    requer_torch()

    treinando = otimizador is not None
    modelo.train(treinando)
    perdas = []
    y_true_lista = []
    y_prob_lista = []

    with torch.set_grad_enabled(treinando):
        for imagens, y in loader:
            if deve_parar and deve_parar():
                raise InterruptedError("Treino interrompido.")

            imagens = imagens.to(dispositivo)
            y = y.to(dispositivo)

            if treinando:
                otimizador.zero_grad()

            logits = modelo(imagens)
            perda = criterio(logits, y)

            if treinando:
                perda.backward()
                otimizador.step()

            perdas.append(float(perda.item()))
            y_true_lista.append(y.detach().cpu().numpy())
            y_prob_lista.append(torch.sigmoid(logits).detach().cpu().numpy())

    y_true = np.vstack(y_true_lista)
    y_prob = np.vstack(y_prob_lista)
    macro_f1, micro_f1 = calcular_metricas(y_true, y_prob, rotulos)
    return float(np.mean(perdas)), macro_f1, micro_f1


def criar_backup(log: Callable[[str], None]) -> None:
    arquivos = [
        ARQUIVO_MODELO_INCREMENTAL,
        ARQUIVO_LIMIARES_INCREMENTAL,
        ARQUIVO_METRICAS_LIMIARES,
        ARQUIVO_HISTORICO,
        ARQUIVO_RESUMO_TREINO,
        ARQUIVO_PREDICOES_JSON,
        ARQUIVO_PREDICOES_CSV,
        ARQUIVO_REVISOES_JSON,
        ARQUIVO_CONFIRMADOS_CSV,
        ARQUIVO_CORRIGIR_CSV,
    ]
    existentes = [caminho for caminho in arquivos if caminho.exists()]

    if not existentes:
        log("Backup: nenhum arquivo anterior encontrado.\n")
        return

    destino_base = PASTA_BACKUPS / time.strftime("%Y%m%d_%H%M%S")

    for caminho in existentes:
        try:
            relativo = caminho.resolve().relative_to(RAIZ)
        except ValueError:
            relativo = Path(caminho.name)

        destino = destino_base / relativo
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(caminho, destino)

    log(f"Backup criado: {destino_base}\n")


def treinar_modelo(
    epocas: int,
    paciencia: int,
    taxa: float,
    validacao: float,
    log: Callable[[str], None],
    deve_parar: Callable[[], bool],
    origem_imagens: Path | None = None,
    arquivo_rotulos: Path | None = None,
) -> list[str]:
    requer_torch()
    random.seed(SEMENTE)
    np.random.seed(SEMENTE)
    torch.manual_seed(SEMENTE)
    garantir_pastas()
    criar_backup(log)

    modelo, rotulos, tamanho, checkpoint_base, dispositivo, caminho_inicial = carregar_modelo(
        log,
        criar_se_nao_existir=True,
    )

    base, treino, val = preparar_base_treino(
        validacao,
        rotulos,
        log,
        origem_imagens=origem_imagens,
        arquivo_rotulos=arquivo_rotulos,
    )

    transform_treino = criar_transform(tamanho, treino=True)
    transform_val = criar_transform(tamanho, treino=False)
    dataset_treino = BaseRotulada(CSV_TREINO, rotulos, transform_treino)
    dataset_val = BaseRotulada(CSV_VALIDACAO, rotulos, transform_val)
    loader_treino = DataLoader(dataset_treino, batch_size=TAMANHO_LOTE, shuffle=True, num_workers=0)
    loader_val = DataLoader(dataset_val, batch_size=TAMANHO_LOTE, shuffle=False, num_workers=0)
    pos_weight = calcular_pos_weight(CSV_TREINO, rotulos).to(dispositivo)
    criterio = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    parametros_treinaveis = [
        parametro
        for parametro in modelo.parameters()
        if parametro.requires_grad
    ]

    otimizador = torch.optim.AdamW(parametros_treinaveis, lr=taxa)

    melhor_macro_f1 = -1.0
    melhor_epoca = 0
    sem_melhora = 0
    historico = []

    log("\nTreino iniciado.\n")
    log(f"Base rotulada: {len(base)} | treino: {len(treino)} | validação: {len(val)}\n")
    origem_modelo = caminho_relativo(caminho_inicial) if caminho_inicial is not None else "modelo_inicial_do_zero"
    log(f"Modelo inicial: {origem_modelo}\n")

    for epoca in range(1, epocas + 1):
        if deve_parar():
            raise InterruptedError("Treino interrompido.")

        inicio = time.time()
        perda_treino, _, _ = executar_epoca(modelo, loader_treino, criterio, dispositivo, rotulos, otimizador, deve_parar)
        perda_val, macro_f1, micro_f1 = executar_epoca(modelo, loader_val, criterio, dispositivo, rotulos, None, deve_parar)
        duracao = time.time() - inicio

        historico.append({
            "epoca": epoca,
            "perda_treino": perda_treino,
            "perda_validacao": perda_val,
            "macro_f1_validacao": macro_f1,
            "micro_f1_validacao": micro_f1,
            "tempo_segundos": duracao,
        })

        log(
            f"Época {epoca}/{epocas} | perda treino={perda_treino:.4f} | "
            f"perda val={perda_val:.4f} | macro-F1={macro_f1:.4f} | "
            f"micro-F1={micro_f1:.4f} | {duracao:.1f}s\n"
        )

        if macro_f1 > melhor_macro_f1:
            melhor_macro_f1 = macro_f1
            melhor_epoca = epoca
            sem_melhora = 0
            PASTA_MODELO.mkdir(parents=True, exist_ok=True)
            torch.save(
                {
                    "modelo_estado": modelo.state_dict(),
                    "rotulos": rotulos,
                    "tamanho_imagem": tamanho,
                    "macro_f1_validacao": melhor_macro_f1,
                    "epoca": epoca,
                    "limiar_padrao": LIMIAR_PADRAO,
                    "num_epocas_configurado": epocas,
                    "paciencia": paciencia,
                    "modelo_base": origem_modelo,
                    "total_rotulado_correto": len(base),
                    "treino": len(treino),
                    "validacao": len(val),
                    "observacao": "Modelo treinado pelo aplicativo PyQt6 independente.",
                },
                ARQUIVO_MODELO_INCREMENTAL,
            )
            log(f"  Modelo salvo: {ARQUIVO_MODELO_INCREMENTAL}\n")
        else:
            sem_melhora += 1
            log(f"  Sem melhora por {sem_melhora} época(s).\n")

            if sem_melhora >= paciencia:
                log("Early stopping.\n")
                break

    salvar_csv(
        ARQUIVO_HISTORICO,
        historico,
        ["epoca", "perda_treino", "perda_validacao", "macro_f1_validacao", "micro_f1_validacao", "tempo_segundos"],
    )
    salvar_json(
        ARQUIVO_RESUMO_TREINO,
        {
            "total_rotulado_correto": len(base),
            "treino": len(treino),
            "validacao": len(val),
            "melhor_epoca": melhor_epoca,
            "melhor_macro_f1_validacao": melhor_macro_f1,
            "modelo_saida": str(ARQUIVO_MODELO_INCREMENTAL),
            "historico": str(ARQUIVO_HISTORICO),
            "base_atual_csv": str(CSV_BASE_ATUAL),
            "modelo_base_macro_f1": checkpoint_base.get("macro_f1_validacao"),
        },
    )
    log(f"Treino concluído. Melhor época: {melhor_epoca} | macro-F1: {melhor_macro_f1:.4f}\n")
    return rotulos


def coletar_predicoes_validacao(modelo, loader, dispositivo, deve_parar: Callable[[], bool]):
    requer_torch()

    y_true_lista = []
    y_prob_lista = []
    modelo.eval()

    with torch.no_grad():
        for imagens, y in loader:
            if deve_parar():
                raise InterruptedError("Calibração interrompida.")

            imagens = imagens.to(dispositivo)
            logits = modelo(imagens)
            y_true_lista.append(y.numpy())
            y_prob_lista.append(torch.sigmoid(logits).cpu().numpy())

    return np.vstack(y_true_lista).astype(np.int32), np.vstack(y_prob_lista).astype(np.float32)


def metricas_binarias(y_true_col, y_pred_col):
    tp = np.sum((y_true_col == 1) & (y_pred_col == 1))
    fp = np.sum((y_true_col == 0) & (y_pred_col == 1))
    fn = np.sum((y_true_col == 1) & (y_pred_col == 0))
    tn = np.sum((y_true_col == 0) & (y_pred_col == 0))
    precisao = tp / (tp + fp + 1e-8)
    revocacao = tp / (tp + fn + 1e-8)
    f1 = 2 * precisao * revocacao / (precisao + revocacao + 1e-8)
    return {
        "tp": int(tp),
        "fp": int(fp),
        "fn": int(fn),
        "tn": int(tn),
        "precisao": float(precisao),
        "revocacao": float(revocacao),
        "f1": float(f1),
    }


def calibrar_limiar(y_true_col, y_prob_col):
    suporte = int(np.sum(y_true_col))

    if suporte < 5:
        y_pred = (y_prob_col >= LIMIAR_PADRAO).astype(np.int32)
        return {
            "limiar": LIMIAR_PADRAO,
            "estrategia": "padrao_baixo_suporte",
            "motivo": f"suporte_{suporte}",
            **metricas_binarias(y_true_col, y_pred),
        }

    melhor = None

    for limiar in np.arange(0.05, 0.951, 0.01):
        y_pred = (y_prob_col >= limiar).astype(np.int32)
        metricas = metricas_binarias(y_true_col, y_pred)

        if metricas["precisao"] < 0.20:
            continue

        candidato = {
            "limiar": float(round(limiar, 2)),
            "estrategia": "otimizado_por_f1",
            "motivo": "ok",
            **metricas,
        }

        if (
            melhor is None
            or candidato["f1"] > melhor["f1"]
            or (
                abs(candidato["f1"] - melhor["f1"]) < 1e-12
                and candidato["precisao"] >= melhor["precisao"]
                and candidato["limiar"] > melhor["limiar"]
            )
        ):
            melhor = candidato

    if melhor is not None:
        return melhor

    y_pred = (y_prob_col >= LIMIAR_PADRAO).astype(np.int32)
    return {
        "limiar": LIMIAR_PADRAO,
        "estrategia": "padrao_sem_candidato",
        "motivo": "nenhum_limiar_com_precisao_minima",
        **metricas_binarias(y_true_col, y_pred),
    }


def calibrar_limiares(log: Callable[[str], None], deve_parar: Callable[[], bool]) -> list[str]:
    modelo, rotulos, tamanho, _checkpoint, dispositivo, _caminho = carregar_modelo(log)
    dataset_val = BaseRotulada(CSV_VALIDACAO, rotulos, criar_transform(tamanho, treino=False))
    loader = DataLoader(dataset_val, batch_size=TAMANHO_LOTE_CALIBRACAO, shuffle=False, num_workers=0)
    y_true, y_prob = coletar_predicoes_validacao(modelo, loader, dispositivo, deve_parar)

    limiares = {}
    linhas = []

    log("\nCalibrando limiares.\n")

    for indice, rotulo in enumerate(rotulos):
        resultado = calibrar_limiar(y_true[:, indice], y_prob[:, indice])
        limiares[rotulo] = resultado["limiar"]
        linhas.append({
            "rotulo": rotulo,
            "limiar": resultado["limiar"],
            "f1": resultado["f1"],
            "precisao": resultado["precisao"],
            "revocacao": resultado["revocacao"],
            "tp": resultado["tp"],
            "fp": resultado["fp"],
            "fn": resultado["fn"],
            "tn": resultado["tn"],
            "suporte_positivo": int(np.sum(y_true[:, indice])),
            "estrategia": resultado["estrategia"],
            "motivo": resultado["motivo"],
        })
        log(
            f"{rotulo}: limiar={resultado['limiar']:.2f} | "
            f"F1={resultado['f1']:.3f} | P={resultado['precisao']:.3f} | "
            f"R={resultado['revocacao']:.3f} | {resultado['motivo']}\n"
        )

    salvar_json(ARQUIVO_LIMIARES_INCREMENTAL, limiares)
    salvar_csv(
        ARQUIVO_METRICAS_LIMIARES,
        linhas,
        ["rotulo", "limiar", "f1", "precisao", "revocacao", "tp", "fp", "fn", "tn", "suporte_positivo", "estrategia", "motivo"],
    )
    log(f"Limiares salvos: {ARQUIVO_LIMIARES_INCREMENTAL}\n")
    return rotulos


@dataclass
class ConfigExecucao:
    pasta_imagens: Path
    arquivo_rotulos: Path | None
    importar_benapro: bool
    recalcular_predicoes: bool
    epocas: int
    paciencia: int
    taxa: float
    validacao: float


class TarefaLonga(QThread):
    log = pyqtSignal(str)
    terminou = pyqtSignal(bool, str)

    def __init__(self, funcao: Callable[[Callable[[str], None], Callable[[], bool]], None]):
        super().__init__()
        self.funcao = funcao
        self._parar = False

    def parar(self) -> None:
        self._parar = True

    def deve_parar(self) -> bool:
        return self._parar

    def run(self) -> None:
        try:
            self.funcao(self.log.emit, self.deve_parar)
        except InterruptedError as erro:
            self.terminou.emit(False, str(erro))
            return
        except Exception:
            self.log.emit("\nErro durante a execução:\n")
            self.log.emit(traceback.format_exc())
            self.terminou.emit(False, "A tarefa terminou com erro.")
            return

        self.terminou.emit(True, "Tarefa concluída.")


ICONES = {
    "minus": '<path d="M5 12h14"/>',
    "square": '<rect x="7" y="7" width="10" height="10" rx="1.5"/>',
    "x": '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    "sliders": (
        '<path d="M4 6h5"/><path d="M15 6h5"/><circle cx="12" cy="6" r="2"/>'
        '<path d="M4 12h9"/><path d="M19 12h1"/><circle cx="16" cy="12" r="2"/>'
        '<path d="M4 18h1"/><path d="M11 18h9"/><circle cx="8" cy="18" r="2"/>'
    ),
    "predict": (
        '<path d="M7 3H5a2 2 0 0 0-2 2v2"/>'
        '<path d="M17 3h2a2 2 0 0 1 2 2v2"/>'
        '<path d="M7 21H5a2 2 0 0 1-2-2v-2"/>'
        '<path d="M17 21h2a2 2 0 0 0 2-2v-2"/>'
        '<path d="M12 8v8"/><path d="M8 12h8"/>'
    ),
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "hourglass": (
        '<path d="M7 4h10"/><path d="M7 20h10"/>'
        '<path d="M8.5 4c0 4.4 7 4.7 7 8s-7 3.6-7 8"/>'
        '<path d="M15.5 4c0 4.4-7 4.7-7 8s7 3.6 7 8"/>'
        '<path d="M9.8 8.7h4.4"/><path d="M10.4 15.8h3.2"/>'
    ),
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5"/>',
    "chart": '<path d="m4 17 5-5 4 4 7-9"/><path d="M15 7h5v5"/><path d="M4 21h16"/>',
    "zap": '<path d="M13 2 4 14h7l-1 8 9-12h-7l1-8z"/>',
    "sparkles": '<path d="m12 3 1.8 4.2L18 9l-4.2 1.8L12 15l-1.8-4.2L6 9l4.2-1.8L12 3z"/><path d="m5 15 .9 2.1L8 18l-2.1.9L5 21l-.9-2.1L2 18l2.1-.9L5 15z"/><path d="m19 13 .8 1.8 1.7.7-1.7.7-.8 1.8-.8-1.8-1.7-.7 1.7-.7.8-1.8z"/>',
    "stop": '<path d="M8 3h8l5 5v8l-5 5H8l-5-5V8z"/><circle cx="12" cy="12" r="3.2"/>',
    "folder": '<path d="M3 7a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "trash": '<path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v5"/><path d="M14 11v5"/>',
    "download": '<path d="M12 3v11"/><path d="m7 10 5 5 5-5"/><path d="M5 19h14"/>',
    "grid": '<rect x="4" y="4" width="6" height="6" rx="1.5"/><rect x="14" y="4" width="6" height="6" rx="1.5"/><rect x="4" y="14" width="6" height="6" rx="1.5"/><rect x="14" y="14" width="6" height="6" rx="1.5"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="m8 12 2.6 2.6L16.5 9"/>',
    "alert": '<path d="m12 3 10 18H2L12 3z"/><path d="M12 9v5"/><path d="M12 17h.01"/>',
    "cube": '<path d="m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3z"/><path d="M12 12 4 7.5"/><path d="m12 12 8-4.5"/><path d="M12 12v9"/>',
    "line-chart": '<path d="M3 19h18"/><path d="m5 15 4-4 4 3 6-8"/><path d="M15 6h4v4"/>',
    "chevrons": '<path d="m8 7 4-4 4 4"/><path d="m8 17 4 4 4-4"/>',
}


def icone_pixmap(nome: str, cor: str = "#e8edf7", tamanho: int = 22, largura_linha: float = 2.0) -> QPixmap:
    caminhos = ICONES.get(nome, "")
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{tamanho}" height="{tamanho}" viewBox="0 0 24 24" '
        f'fill="none" stroke="{cor}" stroke-width="{largura_linha}" stroke-linecap="round" stroke-linejoin="round">'
        f"{caminhos}</svg>"
    )
    pixmap = QPixmap()
    pixmap.loadFromData(svg.encode("utf-8"), "SVG")
    return pixmap


def icone_svg(nome: str, cor: str = "#e8edf7", tamanho: int = 22, largura_linha: float = 2.0) -> QIcon:
    return QIcon(icone_pixmap(nome, cor, tamanho, largura_linha))


def aplicar_icone_botao(botao: QPushButton, nome: str, cor: str = "#f8fafc", tamanho: int = 18) -> None:
    botao.setIcon(icone_svg(nome, cor, tamanho))
    botao.setIconSize(QSize(tamanho, tamanho))


class SecaoPainel(QFrame):
    def __init__(self, titulo: str) -> None:
        super().__init__()
        self.setObjectName("secaoPainel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        cabecalho = QHBoxLayout()
        cabecalho.setContentsMargins(0, 0, 0, 0)
        cabecalho.setSpacing(10)

        marcador = QFrame()
        marcador.setObjectName("marcadorSecao")
        marcador.setFixedSize(4, 26)

        label = QLabel(titulo)
        label.setObjectName("tituloSecao")

        cabecalho.addWidget(marcador)
        cabecalho.addWidget(label)
        cabecalho.addStretch(1)
        layout.addLayout(cabecalho)

        self.conteudo = QVBoxLayout()
        self.conteudo.setContentsMargins(0, 0, 0, 0)
        self.conteudo.setSpacing(10)
        layout.addLayout(self.conteudo)


class CartaoEstado(QFrame):
    def __init__(
        self,
        titulo: str,
        valor: str = "0",
        subtitulo: str = "",
        icone: str = "●",
        cor: str = "#8b5cf6",
        destaque: bool = False,
    ) -> None:
        super().__init__()
        self.setObjectName("cartaoEstado")
        self.setMinimumHeight(126)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setProperty("cor", cor)
        self.setProperty("destaque", "true" if destaque else "false")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18 if destaque else 16, 14, 18 if destaque else 14, 14)
        layout.setSpacing(14 if destaque else 12)

        self.label_icone = QLabel(icone)
        self.label_icone.setObjectName("iconeCartao")
        self.label_icone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tamanho_icone = 58 if destaque else 52
        self.label_icone.setFixedSize(tamanho_icone, tamanho_icone)
        self.label_icone.setProperty("cor", cor)
        fundo = self._cor_com_alpha(cor, 0.22)
        self.label_icone.setStyleSheet(
            f"QLabel#iconeCartao {{ color: {cor}; background: {fundo}; border-radius: {tamanho_icone // 2}px; "
            f"font-size: {24 if destaque else 22}px; font-weight: 800; }}"
        )
        if icone in ICONES:
            self.label_icone.setPixmap(icone_pixmap(icone, cor, 30 if destaque else 27, 2.2))

        textos = QVBoxLayout()
        textos.setContentsMargins(0, 0, 0, 0)
        textos.setSpacing(3)

        self.label_titulo = QLabel(titulo)
        self.label_titulo.setObjectName("tituloCartao")
        self.label_titulo.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.label_valor = QLabel(valor)
        self.label_valor.setObjectName("valorCartao")
        self.label_valor.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.label_valor.setWordWrap(not destaque)
        self.label_subtitulo = QLabel(subtitulo)
        self.label_subtitulo.setObjectName("subtituloCartao")
        self.label_subtitulo.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.label_subtitulo.setWordWrap(True)

        textos.addStretch(1)
        textos.addWidget(self.label_titulo)
        textos.addWidget(self.label_valor)
        textos.addWidget(self.label_subtitulo)
        textos.addStretch(1)

        layout.addWidget(self.label_icone, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(textos, 1)

    def setValor(self, valor: str) -> None:
        self.label_valor.setText(valor)

    def setSubtitulo(self, texto: str) -> None:
        self.label_subtitulo.setText(texto)

    @staticmethod
    def _cor_com_alpha(cor: str, alpha: float) -> str:
        cor_limpa = cor.lstrip("#")
        if len(cor_limpa) != 6:
            return "#22183b"

        r = int(cor_limpa[0:2], 16)
        g = int(cor_limpa[2:4], 16)
        b = int(cor_limpa[4:6], 16)
        return f"rgba({r}, {g}, {b}, {int(max(0, min(1, alpha)) * 255)})"


class VisualizadorImagem(QLabel):
    zoom_solicitado = pyqtSignal(float)
    reset_zoom_solicitado = pyqtSignal()

    def __init__(self, texto: str = "") -> None:
        super().__init__(texto)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)

    def wheelEvent(self, evento) -> None:
        delta = evento.angleDelta().y()

        if delta:
            fator = 1.15 ** (delta / 120.0)
        else:
            delta = evento.pixelDelta().y()
            fator = 1.0015 ** delta if delta else 1.0

        if fator != 1.0:
            self.zoom_solicitado.emit(fator)
            evento.accept()
            return

        super().wheelEvent(evento)

    def mouseDoubleClickEvent(self, evento) -> None:
        self.reset_zoom_solicitado.emit()
        evento.accept()

class CheckBoxBase(QCheckBox):
    def __init__(self, texto: str) -> None:
        super().__init__(texto)
        self.setObjectName("checkBase")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(24)

    def sizeHint(self) -> QSize:
        largura_texto = self.fontMetrics().horizontalAdvance(self.text())
        return QSize(largura_texto + 34, 24)

    def enterEvent(self, evento) -> None:
        self.update()
        super().enterEvent(evento)

    def leaveEvent(self, evento) -> None:
        self.update()
        super().leaveEvent(evento)

    def paintEvent(self, evento) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        topo_caixa = int((self.height() - 16) / 2)
        caixa = QRect(1, topo_caixa + 1, 14, 14)

        if self.isChecked():
            fundo = QColor("#7c3aed")
        else:
            fundo = QColor("#0b111d")

        if self.underMouse():
            borda = QColor("#c4b5fd")
        else:
            borda = QColor("#ffffff")

        painter.setBrush(QBrush(fundo))
        painter.setPen(QPen(borda, 1.8))
        painter.drawRoundedRect(caixa, 3, 3)

        if self.isChecked():
            caneta_check = QPen(QColor("#ffffff"), 2.0)
            caneta_check.setCapStyle(Qt.PenCapStyle.RoundCap)
            caneta_check.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(caneta_check)

            x = caixa.left()
            y = caixa.top()
            painter.drawLine(x + 3, y + 7, x + 6, y + 10)
            painter.drawLine(x + 6, y + 10, x + 11, y + 4)

        fonte = painter.font()
        fonte.setBold(True)
        painter.setFont(fonte)
        painter.setPen(QColor("#e5e7eb"))

        area_texto = QRect(28, 0, self.width() - 28, self.height())
        painter.drawText(area_texto, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.text())

def resumo_modelo_ativo_interface() -> dict:
    caminho = caminho_modelo_ativo()

    if not caminho.exists():
        return {
            "tipo": "Faltando",
            "subtitulo": "Nenhum modelo encontrado",
            "valor_treino": "-",
        }

    tipo = "Incremental" if caminho == ARQUIVO_MODELO_INCREMENTAL else "Base"

    resumo = ler_json(ARQUIVO_RESUMO_TREINO, {})
    usar_resumo_json = False

    if isinstance(resumo, dict) and resumo:
        modelo_saida = str(resumo.get("modelo_saida", ""))
        resumo_aponta_modelo = (
            not modelo_saida
            or Path(modelo_saida).name == caminho.name
            or str(caminho) == modelo_saida
        )

        try:
            resumo_mais_novo = ARQUIVO_RESUMO_TREINO.stat().st_mtime >= caminho.stat().st_mtime
        except OSError:
            resumo_mais_novo = False

        usar_resumo_json = resumo_aponta_modelo and resumo_mais_novo

    if usar_resumo_json:
        macro = resumo.get("melhor_macro_f1_validacao")
        macro_txt = f"{macro:.4f}" if isinstance(macro, (float, int)) else "-"
        epoca = resumo.get("melhor_epoca", "-")

        return {
            "tipo": tipo,
            "subtitulo": caminho_relativo(caminho),
            "valor_treino": f"Época {epoca} | F1 {macro_txt}",
        }

    try:
        requer_torch()
        dispositivo = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        checkpoint = carregar_checkpoint(caminho, dispositivo)

        macro = checkpoint.get("macro_f1_validacao")
        macro_txt = f"{macro:.4f}" if isinstance(macro, (float, int)) else "-"

        epoca = checkpoint.get("epoca", "-")

        return {
            "tipo": tipo,
            "subtitulo": caminho_relativo(caminho),
            "valor_treino": f"Época {epoca} | F1 {macro_txt}",
        }

    except Exception:
        return {
            "tipo": tipo,
            "subtitulo": caminho_relativo(caminho),
            "valor_treino": "modelo encontrado",
        }

def escolher_tela_inicial(app: QApplication):
    telas = app.screens()

    if not telas:
        return app.primaryScreen()

    # Abre na tela onde o cursor do mouse está atualmente
    from PyQt6.QtGui import QCursor
    pos_mouse = QCursor.pos()
    for tela in telas:
        if tela.geometry().contains(pos_mouse):
            return tela

    # Fallback: índice fixo ou tela primária
    if len(telas) > TELA_INICIAL_INDICE:
        return telas[TELA_INICIAL_INDICE]

    return app.primaryScreen() or telas[0]


def mostrar_fullscreen_na_tela(janela: QMainWindow, tela) -> None:
    if tela is None:
        janela.showFullScreen()
        return

    geometria = tela.geometry()
    janela.setGeometry(geometria)
    janela.move(geometria.topLeft())
    janela.show()

    handle = janela.windowHandle()
    if handle is not None:
        handle.setScreen(tela)

    janela.showFullScreen()

class JanelaPrincipal(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        garantir_pastas()
        self.rotulos = detectar_rotulos()
        self.predicoes: list[dict] = []
        self.predicoes_filtradas: list[dict] = []
        self.revisoes: dict[str, dict] = {}
        self.item_atual: dict | None = None
        self.pixmap_atual: QPixmap | None = None
        self._cache_pixmap: dict[str, QPixmap] = {}
        self.zoom_imagem = 1.0
        self.camada_atual = "A"
        self.tarefa: TarefaLonga | None = None
        self.checkboxes_rotulos: dict[str, QCheckBox] = {}
        self.labels_rotulos: dict[str, QLabel] = {}
        self.barras_probabilidade: dict[str, QProgressBar] = {}
        self._log_no_inicio_linha = True

        self.setWindowTitle("BenaZub")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.resize(1920, 1080)
        self.setMinimumSize(960, 620)
        self._montar_interface()
        self._instalar_atalhos()
        self._carregar_dados()
        self._atualizar_estado()
        self._log("Aplicativo PyQt6 pronto.\n")
        self._log(f"Pasta base: {RAIZ}\n")

    def _montar_interface(self) -> None:
        self._aplicar_estilo()
        central = QWidget()
        raiz_layout = QVBoxLayout(central)
        raiz_layout.setContentsMargins(0, 0, 0, 0)
        raiz_layout.setSpacing(0)

        topo = self._criar_topo()
        raiz_layout.addWidget(topo)

        corpo = QWidget()
        corpo_layout = QVBoxLayout(corpo)
        corpo_layout.setContentsMargins(16, 0, 16, 18)
        corpo_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("divisorPrincipal")
        splitter.setHandleWidth(18)
        splitter.addWidget(self._criar_painel_esquerdo())
        splitter.addWidget(self._criar_painel_principal())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([320, 1280])
        corpo_layout.addWidget(splitter, 1)
        raiz_layout.addWidget(corpo, 1)

        self.setCentralWidget(central)
        self._aplicar_feedback_botoes()

    def _aplicar_feedback_botoes(self) -> None:
        for botao in self.findChildren(QPushButton):
            self._preparar_botao_responsivo(botao)
            botao.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
            botao.setCursor(
                Qt.CursorShape.PointingHandCursor if botao.isEnabled() else Qt.CursorShape.ArrowCursor
            )
            botao.installEventFilter(self)
        # ✅ ADICIONADO: cursor pointer nas abas
        from PyQt6.QtWidgets import QTabBar
        for tab_bar in self.findChildren(QTabBar):
            tab_bar.setCursor(Qt.CursorShape.PointingHandCursor)

    def _preparar_botao_responsivo(self, botao: QPushButton) -> None:
        nome = botao.objectName()
        botao.setAutoDefault(False)

        if nome in {"botaoTopo", "botaoFechar"}:
            botao.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            return

        botao.setMinimumHeight(max(botao.minimumHeight(), 36))
        botao.setMaximumWidth(16777215)

        if nome in {"primario", "acaoSecundaria", "perigo"}:
            botao.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            return

        if nome in {"botaoCompacto", "segmento", "botaoGhost"}:
            botao.setMinimumWidth(min(max(botao.sizeHint().width(), 96), 150))
            botao.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            return

        if nome in {"botaoPequeno", "botaoEscolherImagem"}:
            botao.setMinimumWidth(min(max(botao.sizeHint().width(), 74), 118))

        botao.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def eventFilter(self, objeto, evento):
        if isinstance(objeto, QPushButton) and evento.type() == QEvent.Type.EnabledChange:
            objeto.setCursor(
                Qt.CursorShape.PointingHandCursor
                if objeto.isEnabled()
                else Qt.CursorShape.ArrowCursor
            )

        return super().eventFilter(objeto, evento)

    def _aplicar_estilo(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #090e18;
                color: #e8edf7;
                font-family: "Segoe UI", Arial;
                font-size: 12px;
            }
            QFrame#barraSuperior {
                background: #090d17;
                border: none;
            }
            QSplitter#divisorPrincipal::handle {
                background: transparent;
                width: 18px;
            }
            QFrame#secaoPainel,
            QFrame#painelPrincipal,
            QFrame#painelConteudo,
            QFrame#painelLog,
            QFrame#painelLista,
            QFrame#painelRotulos,
            QFrame#painelDetalhes {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #151f31, stop:1 #101827);
                border: 1px solid #253149;
                border-radius: 7px;
            }
            QFrame#secaoPainel QLabel,
            QFrame#painelPrincipal QLabel,
            QFrame#painelConteudo QLabel,
            QFrame#painelLog QLabel,
            QFrame#painelLista QLabel,
            QFrame#painelRotulos QLabel,
            QFrame#painelDetalhes QLabel,
            QFrame#cartaoEstado QLabel {
                background: transparent;
            }
            QFrame#marcadorSecao {
                background: #8b5cf6;
                border-radius: 2px;
            }
            QLabel#tituloSecao {
                color: #f7f9ff;
                font-size: 14px;
                font-weight: 600;
            }
            QLabel#rotuloCampo {
                color: #c8d0dd;
                font-size: 12px;
                font-weight: 500;
            }
            QWidget#campoIconeTexto {
                background: transparent;
            }
            QWidget#abaConteudo,
            QWidget#painelRevisao {
                background: transparent;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                border: 1px solid #26344a;
                border-radius: 6px;
                padding: 7px 10px;
                background: #0b111d;
                color: #e9eef8;
                selection-background-color: #6d3ddb;
            }
            QSpinBox, QDoubleSpinBox {
                min-height: 22px;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #6d3ddb;
            }
            QCheckBox {
                color: #d7deeb;
                spacing: 7px;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 2px;
                border: 1px solid #a0aec0;
                background: #111827;
            }
            QCheckBox::indicator:checked {
                background: #7c3aed;
                border-color: #a78bfa;
            }
            QCheckBox#checkBase {
                color: #e5e7eb;
                spacing: 10px;
                font-weight: 600;
                background: transparent;
            }
            QPushButton {
                border: 1px solid #34425a;
                border-radius: 6px;
                padding: 8px 13px;
                background: #1d2738;
                color: #eef3fb;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #2b3952;
                border-color: #7c8aa3;
            }
            QPushButton:pressed {
                padding: 8px 13px;
                background: #111827;
                border-color: #9aa8c0;
            }
            QPushButton:focus {
                border-color: #a78bfa;
            }
            QPushButton#botaoTopo {
                min-width: 56px;
                max-width: 56px;
                min-height: 44px;
                max-height: 44px;
                padding: 0;
                border-radius: 0;
                background: #090d17;
                border: none;
                color: #cfd7e6;
            }
            QPushButton#botaoTopo:hover {
                background: #1c2940;
            }
            QPushButton#botaoTopo:pressed {
                padding: 0;
                background: #0f1726;
            }
            QPushButton#botaoFechar {
                min-width: 56px;
                max-width: 56px;
                min-height: 44px;
                max-height: 44px;
                padding: 0;
                border-radius: 0;
                background: #090d17;
                border: none;
                color: #ffffff;
            }
            QPushButton#botaoFechar:hover {
                background: #b52536;
            }
            QPushButton#botaoFechar:pressed {
                padding: 0;
                background: #751925;
            }
            QPushButton#primario {
                color: #f4f7fb;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6b46d9, stop:1 #5520b8);
                border-color: #7048db;
                font-weight: 800;
            }
            QPushButton#primario:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c5af0, stop:1 #6833d1);
                border-color: #a78bfa;
            }
            QPushButton#primario:pressed {
                padding: 8px 13px;
                background: #4b1d95;
                border-color: #c4b5fd;
            }
            QPushButton#confirmar {
                color: #ffffff;
                background: #2f5f51;
                border-color: #5f8e80;
                font-weight: 800;
            }
            QPushButton#confirmar:hover {
                background: #3a7463;
                border-color: #8bb9aa;
            }
            QPushButton#confirmar:pressed {
                padding: 8px 13px;
                background: #21473d;
                border-color: #a7d0c2;
            }
            QPushButton#corrigir {
                color: #ffffff;
                background: #75501f;
                border-color: #9b7541;
                font-weight: 800;
            }
            QPushButton#corrigir:hover {
                background: #92632a;
                border-color: #c79a5a;
            }
            QPushButton#corrigir:pressed {
                padding: 8px 13px;
                background: #5b3c18;
                border-color: #d7ad72;
            }
            QPushButton#perigo {
                color: #ffffff;
                background: #8d2431;
                border-color: #a83a46;
                font-weight: 800;
            }
            QPushButton#perigo:hover {
                background: #b12c3d;
                border-color: #d45a68;
            }
            QPushButton#perigo:pressed {
                background: #6e1b27;
                border-color: #ef8791;
                padding-top: 9px;
                padding-bottom: 7px;
                padding-left: 13px;
                padding-right: 13px;
            }
            QPushButton#acaoSecundaria {
                color: #e7ebf1;
                background: #1d2738;
                border-color: #34425a;
                font-weight: 700;
            }
            QPushButton#acaoSecundaria:hover {
                background: #2b3952;
                border-color: #7c8aa3;
            }
            QPushButton#acaoSecundaria:pressed {
                padding: 8px 13px;
                background: #111827;
                border-color: #9aa8c0;
            }
            QPushButton#botaoCompacto,
            QPushButton#segmento {
                min-height: 36px;
                padding: 0 18px;
                background: #1c2638;
                border-color: #34425a;
            }
            QPushButton#botaoCompacto:hover,
            QPushButton#segmento:hover {
                background: #2a3851;
                border-color: #7c8aa3;
            }
            QPushButton#botaoCompacto:pressed,
            QPushButton#segmento:pressed {
                padding: 0 18px;
                background: #121927;
                border-color: #9aa8c0;
            }
            QPushButton#botaoPequeno {
                min-height: 34px;
                padding: 0 8px;
                background: #1d2738;
                border-color: #34425a;
            }
            QPushButton#botaoPequeno:hover {
                background: #2b3952;
                border-color: #7c8aa3;
            }
            QPushButton#botaoPequeno:pressed {
                padding: 0 8px;
                background: #111827;
                border-color: #9aa8c0;
            }
            QPushButton#botaoEscolherImagem {
                min-height: 34px;
                padding: 0 8px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6b46d9, stop:1 #5520b8);
                border-color: #7048db;
            }
            QPushButton#botaoEscolherImagem:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c5af0, stop:1 #6833d1);
                border-color: #a78bfa;
            }
            QPushButton#botaoEscolherImagem:pressed {
                padding: 0 8px;
                background: #4b1d95;
                border-color: #c4b5fd;
            }
            QPushButton#segmento[ativo="true"] {
                background: #24324b;
                border-color: #7c3aed;
                color: #ffffff;
            }
            QPushButton#segmento[ativo="true"]:hover {
                background: #30415f;
                border-color: #a78bfa;
            }
            QPushButton#segmento[ativo="true"]:pressed {
                padding: 0 18px;
                background: #1b2740;
                border-color: #c4b5fd;
            }
            QPushButton#botaoGhost {
                min-height: 38px;
                min-width: 118px;
                background: #151d2d;
                border-color: #2b3851;
                border-radius: 6px;
                padding: 0 14px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton#botaoGhost:hover {
                background: #22304a;
                border-color: #7c8aa3;
            }
            QPushButton#botaoGhost:pressed {
                padding: 0 14px;
                background: #101827;
                border-color: #9aa8c0;
            }
            QPushButton:focus {
                border-color: #a78bfa;
            }
            QPushButton#botaoTopo:focus,
            QPushButton#botaoFechar:focus {
                border: 1px solid #a78bfa;
            }
            QPushButton:disabled {
                color: #6d7480;
                background: #121927;
                border-color: #27344b;
                padding: 8px 13px;
            }
            QListWidget {
                border: none;
                border-radius: 0;
                background: #111827;
                color: #dbe4f2;
                padding: 0;
                outline: none;
            }
            QListWidget::item {
                padding: 11px 14px;
                border-bottom: 1px solid #21304a;
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5a2fc0, stop:1 #3b2391);
                color: #ffffff;
            }
            QLabel#visualizador {
                background: #070b14;
                border-radius: 7px;
                color: #dce4f2;
                border: 1px solid #253149;
            }
            QLabel#rotuloPredito {
                color: #d7deeb;
                background: transparent;
                padding: 2px 0;
            }
            QLabel#rotuloPredito[ativo="true"] {
                color: #f5f7fa;
                font-weight: 700;
            }
            QLabel#contadorPredicoes {
                color: #eff4ff;
                font-weight: 700;
                font-size: 15px;
                padding: 0;
            }
            QLabel#tituloPainel {
                color: #f8fafc;
                font-size: 17px;
                font-weight: 600;
            }
            QLabel#statusPronto {
                color: #dbe5f4;
                font-weight: 500;
            }
            QLabel#valorProbabilidade {
                color: #dbe5f4;
            }
            QTextEdit {
                background: #070b14;
                color: #f4f6fb;
                border: 1px solid #253149;
                border-radius: 7px;
                padding: 13px;
                font-family: Consolas, monospace;
                font-size: 12px;
            }
            QFrame#cartaoEstado {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #131c2d, stop:1 #101725);
                border: 1px solid #253149;
                border-radius: 7px;
            }
            QFrame#cartaoEstado[destaque="true"] {
                border-color: #31405c;
            }
            QLabel#tituloCartao {
                color: #c3ccdb;
                font-size: 12px;
                font-weight: 600;
            }
            QLabel#valorCartao {
                color: #f8fafc;
                font-size: 21px;
                font-weight: 800;
            }
            QLabel#subtituloCartao {
                color: #9ba8ba;
                font-size: 11px;
            }
            QFrame#cartaoEstado[destaque="true"] QLabel#tituloCartao {
                font-size: 13px;
            }
            QFrame#cartaoEstado[destaque="true"] QLabel#valorCartao {
                font-size: 22px;
            }
            QFrame#cartaoEstado[destaque="true"] QLabel#subtituloCartao {
                font-size: 12px;
            }
            QLabel#iconeCartao {
                color: #8b5cf6;
                background: #22183b;
                border-radius: 29px;
                font-size: 25px;
                font-weight: 800;
            }
            QTabWidget#abasPrincipais {
                background: transparent;
                border: none;
            }
            QTabWidget#abasPrincipais::pane {
                border: none;
                border-top: 1px solid #253149;
                background: transparent;
                top: 0;
            }
            QTabWidget#abasPrincipais::tab-bar {
                left: 0;
                top: 0;
            }
            QTabBar {
                background: transparent;
                border: none;
            }
            QTabBar::base {
                background: transparent;
                border: none;
            }
            QTabBar::tab {
                background: transparent;
                color: #f4f7fb;
                padding: 0 24px;
                min-width: 112px;
                min-height: 49px;
                border: none;
                border-right: 1px solid #253149;
                border-bottom: 3px solid transparent;
                margin: 0;
                font-weight: 700;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background: #151e2f;
                color: #ffffff;
                border-right: 1px solid #253149;
                border-bottom: 3px solid #8b5cf6;
            }
            QTabBar::tab:hover {
                color: #d8b4fe;
                background: #1e1535;
                border-bottom: 3px solid #6d3ddb;
            }
            QTabBar::tab:pressed {
                background: #0f1726;
                color: #c4b5fd;
                border-bottom: 3px solid #a78bfa;
                padding-top: 2px;
            }
            QProgressBar {
                border: 1px solid #2d3b55;
                border-radius: 4px;
                height: 12px;
                background: #111827;
                text-align: center;
            }
            QProgressBar::chunk {
                border-radius: 3px;
                background: #42527a;
            }
            QProgressBar[ativo="true"]::chunk {
                background: #7c3aed;
            }
            QScrollBar:vertical {
                background: #111827;
                width: 12px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #53617a;
                border-radius: 5px;
                min-height: 34px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
                background: transparent;
            }
            """
        )

    def _criar_topo(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("barraSuperior")
        frame.setFixedHeight(54)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 12, 0)
        layout.setSpacing(0)

        self.status_execucao = QLabel("")

        self.botao_minimizar = QPushButton("−")
        self.botao_minimizar.setObjectName("botaoTopo")
        self.botao_atualizar_tela = QPushButton("")
        self.botao_atualizar_tela.setObjectName("botaoTopo")
        self.botao_fechar = QPushButton("")
        self.botao_fechar.setObjectName("botaoFechar")
        self.botao_minimizar.setText("")
        aplicar_icone_botao(self.botao_minimizar, "minus", "#cfd7e6", 16)
        aplicar_icone_botao(self.botao_atualizar_tela, "square", "#cfd7e6", 16)
        aplicar_icone_botao(self.botao_fechar, "x", "#cfd7e6", 17)

        for botao in [self.botao_minimizar, self.botao_atualizar_tela, self.botao_fechar]:
            fonte = botao.font()
            fonte.setPointSize(15)
            fonte.setBold(False)
            botao.setFont(fonte)

        self.botao_minimizar.setToolTip("Minimizar")
        self.botao_atualizar_tela.setToolTip("Alternar tela")
        self.botao_fechar.setToolTip("Fechar")

        self.botao_minimizar.clicked.connect(self.showMinimized)
        self.botao_atualizar_tela.clicked.connect(self._alternar_tela)
        self.botao_fechar.clicked.connect(self.close)

        layout.addWidget(self.botao_minimizar)
        layout.addWidget(self.botao_atualizar_tela)
        layout.addWidget(self.botao_fechar)
        layout.insertStretch(0, 1)
        # Remove o foco dos botões do topo para não ficarem "selecionados" ao abrir
        for botao in (self.botao_minimizar, self.botao_atualizar_tela, self.botao_fechar):
            botao.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        return frame

    def _criar_painel_esquerdo(self) -> QWidget:
        painel = QWidget()
        painel.setMinimumWidth(280)
        painel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(painel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(11)

        grupo_base = self._grupo_base()
        grupo_treino = self._grupo_treino()
        grupo_acoes = self._grupo_acoes()

        grupo_base.setMinimumHeight(365)
        grupo_base.setMaximumHeight(365)
        grupo_base.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        grupo_acoes.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout.addWidget(grupo_base)
        layout.addWidget(grupo_treino)

        layout.addWidget(grupo_acoes, 1)

        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.Shape.NoFrame)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        area.setMinimumWidth(300)
        area.setMaximumWidth(430)
        area.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        area.setWidget(painel)

        return area

    def _grupo_base(self) -> QWidget:
        grupo = SecaoPainel("Base de revisão")
        grupo.setMinimumHeight(365)
        grupo.setMaximumHeight(365)
        grupo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = grupo.conteudo
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(8)

        self.campo_imagens = QLineEdit(self._texto_caminho(PASTA_ENTRADA))
        self.campo_imagens.setCursorPosition(0)

        botao_imagens = QPushButton("Escolher")
        botao_imagens.setObjectName("botaoEscolherImagem")
        botao_imagens.setMinimumWidth(74)
        botao_imagens.clicked.connect(self._escolher_pasta_imagens)

        self.campo_rotulos = QLineEdit("")
        self.campo_rotulos.setPlaceholderText("Opcional: CSV/JSON para reaproveitar rótulos")

        botao_rotulos = QPushButton("Escolher")
        botao_rotulos.setObjectName("botaoPequeno")
        botao_rotulos.clicked.connect(self._escolher_arquivo_rotulos)

        botao_limpar = QPushButton("Limpar")
        botao_limpar.setObjectName("botaoPequeno")
        botao_limpar.clicked.connect(lambda: self.campo_rotulos.setText(""))

        for campo in [self.campo_imagens, self.campo_rotulos]:
            campo.setMinimumHeight(37)
            campo.setMaximumHeight(37)

        self.check_importar_benapro = CheckBoxBase("Importar pacotes BENAPRO")
        self.check_importar_benapro.setChecked(True)

        self.check_recalcular = CheckBoxBase("Recalcular predições")
        self.check_recalcular.setChecked(False)

        label_imagens = QLabel("Pasta ou ZIP de imagens")
        label_imagens.setObjectName("rotuloCampo")

        linha_imagens = QHBoxLayout()
        linha_imagens.setContentsMargins(0, 0, 0, 0)
        linha_imagens.setSpacing(7)
        linha_imagens.addWidget(self.campo_imagens, 1)
        linha_imagens.addWidget(botao_imagens)

        label_rotulos = QLabel("Rótulos já existentes")
        label_rotulos.setObjectName("rotuloCampo")

        linha_rotulos = QHBoxLayout()
        linha_rotulos.setContentsMargins(0, 0, 0, 0)
        linha_rotulos.setSpacing(8)
        linha_rotulos.addWidget(botao_rotulos, 1)
        linha_rotulos.addWidget(botao_limpar, 1)

        bloco_checks = QVBoxLayout()
        bloco_checks.setContentsMargins(0, 4, 0, 0)
        bloco_checks.setSpacing(12)
        bloco_checks.addWidget(self.check_importar_benapro)
        bloco_checks.addWidget(self.check_recalcular)

        layout.addWidget(label_imagens)
        layout.addSpacing(6)                  # ← uniforme entre label e campo
        layout.addLayout(linha_imagens)

        layout.addSpacing(14)

        layout.addWidget(label_rotulos)
        layout.addSpacing(6)                  # ← uniforme
        layout.addWidget(self.campo_rotulos)
        layout.addSpacing(8)                  # ← campo e botões agrupados juntos
        layout.addLayout(linha_rotulos)

        layout.addSpacing(12)
        layout.addLayout(bloco_checks)
        layout.addSpacing(12)
        layout.addStretch(1)

        return grupo

    def _campo_com_icone(self, icone: str, texto: str, cor: str = "#a78bfa") -> QWidget:
        linha = QWidget()
        linha.setObjectName("campoIconeTexto")
        linha.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(linha)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(9)

        label_icone = QLabel()
        label_icone.setFixedSize(18, 18)
        label_icone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_icone.setPixmap(icone_pixmap(icone, cor, 18, 2.0))

        label_texto = QLabel(texto)
        label_texto.setObjectName("rotuloCampo")

        layout.addWidget(label_icone)
        layout.addWidget(label_texto)
        layout.addStretch(1)
        return linha

    def _aplicar_setas_spinbox(self, campo: QSpinBox | QDoubleSpinBox) -> None:
        seta_cima = (PASTA_UI / "chevron-up.svg").as_posix()
        seta_baixo = (PASTA_UI / "chevron-down.svg").as_posix()
        campo.setStyleSheet(
            f"""
            QSpinBox, QDoubleSpinBox {{
                padding-right: 24px;
            }}
            QSpinBox::up-button, QDoubleSpinBox::up-button {{
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 22px;
                height: 18px;
                border-left: 1px solid #26344a;
                border-bottom: 1px solid #172235;
                background: #0b111d;
                border-top-right-radius: 6px;
            }}
            QSpinBox::down-button, QDoubleSpinBox::down-button {{
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 22px;
                height: 18px;
                border-left: 1px solid #26344a;
                background: #0b111d;
                border-bottom-right-radius: 6px;
            }}
            QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
                image: url({seta_cima});
                width: 8px;
                height: 8px;
            }}
            QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
                image: url({seta_baixo});
                width: 8px;
                height: 8px;
            }}
            """
        )

    def _grupo_treino(self) -> QWidget:
        grupo = SecaoPainel("Treino")
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(10)
        layout.setColumnStretch(0, 1)
        self.campo_epocas = QSpinBox()
        self.campo_epocas.setRange(1, 500)
        self.campo_epocas.setValue(5)
        self.campo_paciencia = QSpinBox()
        self.campo_paciencia.setRange(1, 100)
        self.campo_paciencia.setValue(2)
        self.campo_taxa = QDoubleSpinBox()
        self.campo_taxa.setDecimals(8)
        self.campo_taxa.setRange(0.00000001, 1.0)
        self.campo_taxa.setSingleStep(0.00001)
        self.campo_taxa.setValue(0.00005)
        self.campo_validacao = QDoubleSpinBox()
        self.campo_validacao.setDecimals(2)
        self.campo_validacao.setRange(0.05, 0.50)
        self.campo_validacao.setSingleStep(0.05)
        self.campo_validacao.setValue(0.20)

        campos = [
            self.campo_epocas,
            self.campo_paciencia,
            self.campo_taxa,
            self.campo_validacao,
        ]

        for campo in campos:
            campo.setMinimumHeight(37)
            campo.setMinimumWidth(118)
            self._aplicar_setas_spinbox(campo)

        labels = [
            self._campo_com_icone("clock", "Épocas", "#8b5cf6"),
            self._campo_com_icone("hourglass", "Paciência", "#cbd5e1"),
            self._campo_com_icone("target", "Taxa de aprendizado", "#cbd5e1"),
            self._campo_com_icone("chart", "Fração de validação", "#8b5cf6"),
        ]

        layout.addWidget(labels[0], 0, 0)
        layout.addWidget(self.campo_epocas, 0, 1)
        layout.addWidget(labels[1], 1, 0)
        layout.addWidget(self.campo_paciencia, 1, 1)
        layout.addWidget(labels[2], 2, 0)
        layout.addWidget(self.campo_taxa, 2, 1)
        layout.addWidget(labels[3], 3, 0)
        layout.addWidget(self.campo_validacao, 3, 1)
        grupo.conteudo.addLayout(layout)
        return grupo

    def _grupo_acoes(self) -> QWidget:
        grupo = SecaoPainel("Ações")
        grupo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = grupo.conteudo
        layout.setSpacing(0)

        self.botao_ciclo = QPushButton("Fluxo completo: treinar e gerar")
        self.botao_ciclo.setObjectName("primario")
        aplicar_icone_botao(self.botao_ciclo, "sparkles", "#ffffff", 20)

        self.botao_predicoes = QPushButton("Gerar predições com modelo atual")
        self.botao_predicoes.setObjectName("acaoSecundaria")
        aplicar_icone_botao(self.botao_predicoes, "zap", "#f8fafc", 18)

        self.botao_treinar = QPushButton("Atualizar modelo")
        self.botao_treinar.setObjectName("acaoSecundaria")
        aplicar_icone_botao(self.botao_treinar, "sliders", "#f8fafc", 18)

        self.botao_saida = QPushButton("Abrir pasta de saída")
        self.botao_saida.setObjectName("acaoSecundaria")
        aplicar_icone_botao(self.botao_saida, "folder", "#f8fafc", 18)

        self.botao_parar = QPushButton("Parar tarefa")
        self.botao_parar.setObjectName("perigo")
        aplicar_icone_botao(self.botao_parar, "stop", "#ffffff", 18)
        self.botao_parar.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.botao_parar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.botao_parar.setToolTip("Clique para parar uma tarefa em execução")
        self.botao_parar.installEventFilter(self)
        self.botao_parar.setEnabled(True)

        self.botao_predicoes.clicked.connect(self._acao_gerar_predicoes)
        self.botao_treinar.clicked.connect(self._acao_treinar)
        self.botao_ciclo.clicked.connect(self._acao_ciclo)
        self.botao_parar.clicked.connect(self._parar_tarefa)
        self.botao_saida.clicked.connect(self._abrir_saida)

        botoes = [
            self.botao_ciclo,
            self.botao_treinar,
            self.botao_predicoes,
            self.botao_saida,
            self.botao_parar,
        ]

        for botao in botoes:
            botao.setMinimumHeight(48)
            botao.setMaximumHeight(48)
            botao.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout.addStretch(1)
        for indice, botao in enumerate(botoes):
            layout.addWidget(botao)
            if indice < len(botoes) - 1:
                layout.addStretch(1)
        layout.addStretch(1)

        return grupo

        return grupo

    def _criar_painel_principal(self) -> QWidget:
        painel = QFrame()
        painel.setObjectName("painelPrincipal")
        layout = QVBoxLayout(painel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        tabs = QTabWidget()
        tabs.setObjectName("abasPrincipais")
        tabs.setDocumentMode(False)
        tabs.setIconSize(QSize(18, 18))
        tabs.addTab(self._aba_estado_logs(), icone_svg("sliders", "#8b5cf6", 18), "Estado e logs")
        tabs.addTab(self._aba_validador(), icone_svg("predict", "#8b5cf6", 18), "Predições")
        layout.addWidget(tabs, 1)
        return painel

    def _aba_validador(self) -> QWidget:
        aba = QWidget()
        aba.setObjectName("abaConteudo")
        layout = QVBoxLayout(aba)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(0)

        conteudo = QHBoxLayout()
        conteudo.setContentsMargins(0, 0, 0, 0)
        conteudo.setSpacing(14)

        coluna_lista = QFrame()
        coluna_lista.setObjectName("painelLista")
        coluna_lista.setMinimumWidth(240)
        coluna_lista.setMaximumWidth(360)
        coluna_lista.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        lista_layout = QVBoxLayout(coluna_lista)
        lista_layout.setContentsMargins(16, 16, 0, 0)
        lista_layout.setSpacing(14)
        self.label_contagem = QLabel("0 predições")
        self.label_contagem.setObjectName("contadorPredicoes")
        self.lista_imagens = QListWidget()
        self.lista_imagens.setUniformItemSizes(True)
        self.lista_imagens.currentRowChanged.connect(self._selecionar_por_linha)
        lista_layout.addWidget(self.label_contagem)
        lista_layout.addWidget(self.lista_imagens, 1)
        conteudo.addWidget(coluna_lista)
        conteudo.addWidget(self._painel_revisao(), 1)
        layout.addLayout(conteudo, 1)
        return aba

    def _painel_revisao(self) -> QWidget:
        painel = QWidget()
        painel.setObjectName("painelRevisao")
        layout = QVBoxLayout(painel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(9)

        barra = QHBoxLayout()
        barra.setContentsMargins(0, 0, 0, 0)
        barra.setSpacing(8)
        self.label_imagem = VisualizadorImagem("Nenhuma imagem carregada")
        self.label_imagem.setObjectName("visualizador")
        self.label_imagem.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_imagem.setMinimumHeight(398)
        self.label_imagem.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Ignored)
        self.label_imagem.zoom_solicitado.connect(self._ajustar_zoom_imagem)
        self.label_imagem.reset_zoom_solicitado.connect(self._resetar_zoom_imagem)

        self.botao_camada1 = QPushButton("Camada 1")
        self.botao_camada2 = QPushButton("Camada 2")
        self.botao_anterior = QPushButton("Anterior")
        self.botao_proxima = QPushButton("Próxima")
        self.botao_camada1.setObjectName("segmento")
        self.botao_camada2.setObjectName("segmento")
        self.botao_anterior.setObjectName("botaoCompacto")
        self.botao_proxima.setObjectName("botaoCompacto")
        self.botao_camada1.setProperty("ativo", "true")
        self.botao_camada2.setProperty("ativo", "false")
        self.botao_camada1.clicked.connect(lambda: self._trocar_camada("A"))
        self.botao_camada2.clicked.connect(lambda: self._trocar_camada("R"))
        self.botao_anterior.clicked.connect(self._item_anterior)
        self.botao_proxima.clicked.connect(self._proximo_item)
        barra.addWidget(self.botao_anterior)
        barra.addWidget(self.botao_proxima)
        barra.addWidget(self.botao_camada1)
        barra.addWidget(self.botao_camada2)

        grupo_rotulos = QFrame()
        grupo_rotulos.setObjectName("painelRotulos")
        painel_rotulos_layout = QVBoxLayout(grupo_rotulos)
        painel_rotulos_layout.setContentsMargins(12, 12, 12, 14)
        painel_rotulos_layout.setSpacing(10)
        titulo_rotulos = QLabel("Rótulos")
        titulo_rotulos.setObjectName("rotuloCampo")
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(9)
        grid.setVerticalSpacing(7)
        grid.setColumnStretch(1, 1)
        painel_rotulos_layout.addWidget(titulo_rotulos)
        painel_rotulos_layout.addLayout(grid)

        for indice, rotulo in enumerate(self.rotulos):
            label_rotulo = QLabel(rotulo)
            label_rotulo.setObjectName("rotuloPredito")
            label_rotulo.setProperty("ativo", False)
            barra_prob = QProgressBar()
            barra_prob.setRange(0, 100)
            barra_prob.setFormat("")
            barra_prob.setProperty("ativo", "false")
            valor = QLabel("0.00")
            valor.setObjectName("valorProbabilidade")
            valor.setMinimumWidth(82)
            valor.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.labels_rotulos[rotulo] = label_rotulo
            self.barras_probabilidade[rotulo] = barra_prob
            grid.addWidget(label_rotulo, indice, 0)
            grid.addWidget(barra_prob, indice, 1)
            grid.addWidget(valor, indice, 2)
            barra_prob.label_valor = valor  # type: ignore[attr-defined]

        layout.addLayout(barra)
        layout.addWidget(self.label_imagem, 1)
        layout.addWidget(grupo_rotulos)
        return painel

    def _aba_estado_logs(self) -> QWidget:
        aba = QWidget()
        aba.setObjectName("abaConteudo")
        layout = QVBoxLayout(aba)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(16)

        painel_log = QFrame()
        painel_log.setObjectName("painelLog")
        painel_log_layout = QVBoxLayout(painel_log)
        painel_log_layout.setContentsMargins(18, 16, 18, 16)
        painel_log_layout.setSpacing(12)

        cabecalho = QHBoxLayout()
        cabecalho.setContentsMargins(0, 0, 0, 0)
        cabecalho.setSpacing(10)
        titulo = QLabel("Logs do sistema")
        titulo.setObjectName("tituloPainel")
        self.botao_limpar_logs = QPushButton("  Limpar logs")
        self.botao_limpar_logs.setObjectName("botaoGhost")
        aplicar_icone_botao(self.botao_limpar_logs, "trash", "#e5edf8", 17)
        self.botao_limpar_logs.clicked.connect(self._limpar_logs)
        cabecalho.addWidget(titulo)
        cabecalho.addStretch(1)
        cabecalho.addWidget(self.botao_limpar_logs)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.document().setMaximumBlockCount(5000)

        rodape = QHBoxLayout()
        rodape.setContentsMargins(0, 0, 0, 0)
        self.status_rodape = QLabel("<span style='color:#22c55e'>●</span>  Sistema pronto")
        self.status_rodape.setObjectName("statusPronto")
        self.botao_salvar_logs = QPushButton("  Salvar logs")
        self.botao_salvar_logs.setObjectName("botaoGhost")
        aplicar_icone_botao(self.botao_salvar_logs, "download", "#e5edf8", 17)
        self.botao_salvar_logs.clicked.connect(self._salvar_logs)
        rodape.addWidget(self.status_rodape)
        rodape.addStretch(1)
        rodape.addWidget(self.botao_salvar_logs)

        painel_log_layout.addLayout(cabecalho)
        painel_log_layout.addWidget(self.log, 1)
        painel_log_layout.addLayout(rodape)

        self.cartao_total = CartaoEstado("Total", "0", "Imagens processadas", "grid", "#7c3aed")
        self.cartao_pendentes = CartaoEstado("A revisar", "0", "Predições geradas", "hourglass", "#facc15")
        self.cartao_modelo = CartaoEstado("Modelo", "faltando", "Tipo de modelo", "cube", "#0ea5e9")
        self.cartao_treino = CartaoEstado("Último treino", "-", "Melhor desempenho", "line-chart", "#8b5cf6", destaque=True)

        cartoes = [
            self.cartao_total,
            self.cartao_pendentes,
            self.cartao_modelo,
            self.cartao_treino,
        ]

        linha_cartoes = QHBoxLayout()
        linha_cartoes.setContentsMargins(2, 0, 2, 0)
        linha_cartoes.setSpacing(14)

        linha_cartoes.addWidget(self.cartao_total, 7)
        linha_cartoes.addWidget(self.cartao_pendentes, 7)
        linha_cartoes.addWidget(self.cartao_modelo, 8)
        linha_cartoes.addWidget(self.cartao_treino, 8)

        layout.addWidget(painel_log, 1)
        layout.addLayout(linha_cartoes)
        return aba

    def _instalar_atalhos(self) -> None:
        atalhos = [
            (QKeySequence(Qt.Key.Key_Right), self._proximo_item),
            (QKeySequence(Qt.Key.Key_Left), self._item_anterior),
            (QKeySequence("1"), lambda: self._trocar_camada("A")),
            (QKeySequence("2"), lambda: self._trocar_camada("R")),
        ]

        for sequencia, acao in atalhos:
            QShortcut(sequencia, self, activated=acao)

        atualizar = QAction("Atualizar estado", self)
        atualizar.setShortcut(QKeySequence.StandardKey.Refresh)
        atualizar.triggered.connect(self._atualizar_tela)
        self.addAction(atualizar)

    def _texto_caminho(self, caminho: Path) -> str:
        try:
            return f".\\{caminho.relative_to(RAIZ)}"
        except ValueError:
            return str(caminho)

    def _resolver_caminho_digitado(self, texto: str) -> Path:
        texto_limpo = texto.strip()
        caminho = Path(texto_limpo)
        if caminho.is_absolute():
            return caminho

        if texto_limpo in {".", ""}:
            return RAIZ

        if texto_limpo.startswith(".\\") or texto_limpo.startswith("./"):
            texto_limpo = texto_limpo[2:]

        return (RAIZ / texto_limpo).resolve()

    def _config(self) -> ConfigExecucao:
        pasta_imagens = self._resolver_caminho_digitado(self.campo_imagens.text().strip() or str(PASTA_ENTRADA))
        arquivo_txt = self.campo_rotulos.text().strip()
        arquivo_rotulos = self._resolver_caminho_digitado(arquivo_txt) if arquivo_txt else None

        if not pasta_imagens.exists():
            raise ValueError(f"Pasta ou ZIP de imagens não encontrado: {pasta_imagens}")

        if pasta_imagens.is_file() and pasta_imagens.suffix.lower() != ".zip":
            raise ValueError(f"Arquivo de entrada inválido. Selecione uma pasta ou um arquivo .zip: {pasta_imagens}")

        if arquivo_rotulos is not None and not arquivo_rotulos.exists():
            raise ValueError(f"Arquivo de rótulos não encontrado: {arquivo_rotulos}")

        return ConfigExecucao(
            pasta_imagens=pasta_imagens,
            arquivo_rotulos=arquivo_rotulos,
            importar_benapro=self.check_importar_benapro.isChecked(),
            recalcular_predicoes=self.check_recalcular.isChecked(),
            epocas=int(self.campo_epocas.value()),
            paciencia=int(self.campo_paciencia.value()),
            taxa=float(self.campo_taxa.value()),
            validacao=float(self.campo_validacao.value()),
        )

    def _escolher_pasta_imagens(self) -> None:
        caminho, _ = QFileDialog.getOpenFileName(
            self,
            "Escolher ZIP de imagens",
            str(PASTA_ENTRADA),
            "Arquivo ZIP (*.zip);;Todos os arquivos (*.*)",
        )

        if caminho:
            self.campo_imagens.setText(caminho)

    def _escolher_arquivo_rotulos(self) -> None:
        caminho, _ = QFileDialog.getOpenFileName(
            self,
            "Escolher arquivo de rótulos",
            str(PASTA_ROTULOS),
            "CSV ou JSON (*.csv *.json);;Todos os arquivos (*.*)",
        )

        if caminho:
            self.campo_rotulos.setText(caminho)

    def _abrir_saida(self) -> None:
        PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
        os.startfile(str(PASTA_SAIDA))

    def _limpar_logs(self) -> None:
        self.log.clear()
        self._log_no_inicio_linha = True

    def _salvar_logs(self) -> None:
        PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
        caminho = PASTA_SAIDA / f"logs_benazub_{time.strftime('%Y%m%d_%H%M%S')}.txt"
        caminho.write_text(self.log.toPlainText(), encoding="utf-8")
        self._log(f"Logs salvos: {caminho}\n")

    def _log(self, texto: str) -> None:
        formato_texto = QTextCharFormat()
        formato_texto.setForeground(QColor("#f4f6fb"))
        formato_tempo = QTextCharFormat()
        formato_tempo.setForeground(QColor("#22c55e"))
        formato_tempo.setFontWeight(700)

        cursor = self.log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        for parte in texto.splitlines(True):
            conteudo = parte.rstrip("\r\n")

            if self._log_no_inicio_linha and conteudo:
                cursor.insertText(f"[{time.strftime('%H:%M:%S')}]  ", formato_tempo)
                self._log_no_inicio_linha = False

            if conteudo:
                cursor.insertText(conteudo, formato_texto)

            if parte.endswith("\n") or parte.endswith("\r"):
                cursor.insertText("\n", formato_texto)
                self._log_no_inicio_linha = True

        self.log.setTextCursor(cursor)
        self.log.ensureCursorVisible()

    def _rodando(self, valor: bool, texto: str = "Pronto") -> None:
        self.status_execucao.setText(texto)
        if hasattr(self, "status_rodape"):
            cor = "#60a5fa" if valor else "#22c55e"
            self.status_rodape.setText(f"<span style='color:{cor}'>●</span>  {texto if valor else 'Sistema pronto'}")

        for botao in [self.botao_predicoes, self.botao_treinar, self.botao_ciclo]:
            botao.setEnabled(not valor)

        self.botao_parar.setEnabled(True)
        self.botao_parar.setCursor(Qt.CursorShape.PointingHandCursor)

        if valor:
            self.botao_parar.setToolTip("Parar tarefa em execução")
        else:
            self.botao_parar.setToolTip("Nenhuma tarefa em execução no momento")

    def _iniciar_tarefa(self, nome: str, funcao: Callable[[Callable[[str], None], Callable[[], bool]], None]) -> None:
        if self.tarefa is not None and self.tarefa.isRunning():
            QMessageBox.warning(self, "Tarefa em execução", "Já existe uma tarefa em andamento.")
            return

        self._rodando(True, nome)
        self._log(f"\n### {nome} - {agora()}\n")
        self.tarefa = TarefaLonga(funcao)
        self.tarefa.log.connect(self._log)
        self.tarefa.terminou.connect(self._tarefa_finalizada)
        self.tarefa.start()

    def _tarefa_finalizada(self, sucesso: bool, mensagem: str) -> None:
        self._rodando(False, "Pronto" if sucesso else "Verifique os logs")
        self._log(f"\n{mensagem}\n")
        self._carregar_dados()
        self._atualizar_estado()

    def _parar_tarefa(self) -> None:
        if self.tarefa is not None and self.tarefa.isRunning():
            self._log("Parada da tarefa...\n")
            self.tarefa.parar()
        else:
            self._log("Nenhuma tarefa em execução para parar.\n")

    def _acao_gerar_predicoes(self) -> None:
        try:
            cfg = self._config()
        except ValueError as erro:
            QMessageBox.warning(self, "Configuração inválida", str(erro))
            return

        def tarefa(log, deve_parar):
            gerar_predicoes(
                cfg.pasta_imagens,
                cfg.arquivo_rotulos,
                cfg.importar_benapro,
                cfg.recalcular_predicoes,
                log,
                deve_parar,
            )

        self._iniciar_tarefa("Gerando predições", tarefa)

    def _acao_treinar(self) -> None:
        try:
            cfg = self._config()
        except ValueError as erro:
            QMessageBox.warning(self, "Configuração inválida", str(erro))
            return

        def tarefa(log, deve_parar):
            treinar_modelo(
                cfg.epocas,
                cfg.paciencia,
                cfg.taxa,
                cfg.validacao,
                log,
                deve_parar,
                origem_imagens=cfg.pasta_imagens,
                arquivo_rotulos=cfg.arquivo_rotulos,
            )
            calibrar_limiares(log, deve_parar)

        self._iniciar_tarefa("Treinando e calibrando", tarefa)

    def _acao_ciclo(self) -> None:
        try:
            cfg = self._config()
        except ValueError as erro:
            QMessageBox.warning(self, "Configuração inválida", str(erro))
            return

        def tarefa(log, deve_parar):
            treinar_modelo(
                cfg.epocas,
                cfg.paciencia,
                cfg.taxa,
                cfg.validacao,
                log,
                deve_parar,
                origem_imagens=cfg.pasta_imagens,
                arquivo_rotulos=cfg.arquivo_rotulos,
            )
            calibrar_limiares(log, deve_parar)
            gerar_predicoes(cfg.pasta_imagens, cfg.arquivo_rotulos, cfg.importar_benapro, True, log, deve_parar)

        self._iniciar_tarefa("Treinando, calibrando e gerando predições", tarefa)

    def _carregar_dados(self) -> None:
        self._cache_pixmap.clear()
        self.rotulos = detectar_rotulos()
        self.revisoes = carregar_revisoes()
        predicoes = ler_json(ARQUIVO_PREDICOES_JSON, [])

        if not isinstance(predicoes, list):
            predicoes = []

        self.predicoes = aplicar_revisoes(predicoes, self.revisoes)
        self._aplicar_filtro()

    def _aplicar_filtro(self) -> None:
        self.predicoes_filtradas = list(self.predicoes)
        self.lista_imagens.blockSignals(True)
        self.lista_imagens.clear()

        for item in self.predicoes_filtradas:
            rotulos = item.get("rotulos_detectados", [])
            texto_item = f"{item.get('chave', '')}\n{'; '.join(rotulos[:3])}"
            entrada = QListWidgetItem(texto_item)
            entrada.setData(Qt.ItemDataRole.UserRole, item.get("id"))
            entrada.setSizeHint(QSize(0, 68))
            self.lista_imagens.addItem(entrada)

        self.lista_imagens.blockSignals(False)
        self.label_contagem.setText(f"{len(self.predicoes_filtradas)} predição(ões)")

        if self.predicoes_filtradas:
            self.lista_imagens.setCurrentRow(0)
            self._mostrar_item(self.predicoes_filtradas[0])
        else:
            self.item_atual = None
            self.label_imagem.setText("Nenhuma predição gerada")
            self.pixmap_atual = None

    def _selecionar_por_linha(self, linha: int) -> None:
        if 0 <= linha < len(self.predicoes_filtradas):
            self._mostrar_item(self.predicoes_filtradas[linha])

    def _mostrar_item(self, item: dict) -> None:
        self.item_atual = item
        self._atualizar_botoes_camada()
        self._atualizar_imagem()
        self._preencher_rotulos()

    def _caminho_item_atual(self) -> Path | None:
        if not self.item_atual:
            return None

        arquivos = self.item_atual.get("arquivos", {})
        caminho = arquivos.get("A") if isinstance(arquivos, dict) else None

        if not caminho:
            caminho = self.item_atual.get("caminho_imagem")

        return resolver_caminho(caminho)

    def _atualizar_imagem(self) -> None:
        caminho = self._caminho_item_atual()
        if caminho is None or not caminho.exists():
            self.pixmap_atual = None
            self.label_imagem.setText("Arquivo de imagem não encontrado")
            return
        chave_cache = f"{caminho}|{self.camada_atual}"
        if chave_cache in self._cache_pixmap:
            self.pixmap_atual = self._cache_pixmap[chave_cache]
            self.zoom_imagem = 1.0
            self._redimensionar_pixmap()
            return
        try:
            imagem = carregar_imagem_tela(caminho, self.camada_atual)
            self.pixmap_atual = pil_para_pixmap(imagem)
            # Limita o cache a 60 imagens para não explodir a RAM
            if len(self._cache_pixmap) > 60:
                self._cache_pixmap.pop(next(iter(self._cache_pixmap)))
            self._cache_pixmap[chave_cache] = self.pixmap_atual
            self.zoom_imagem = 1.0
            self._redimensionar_pixmap()
        except Exception as erro:
            self.pixmap_atual = None
            self.label_imagem.setText(f"Falha ao carregar imagem: {erro}")

    def _redimensionar_pixmap(self) -> None:
        if self.pixmap_atual is None:
            return

        tamanho = self.label_imagem.contentsRect().size()
        tamanho.setWidth(max(1, int((tamanho.width() - 24) * self.zoom_imagem)))
        tamanho.setHeight(max(1, int((tamanho.height() - 32) * self.zoom_imagem)))
        pixmap = self.pixmap_atual.scaled(
            tamanho,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )
        self.label_imagem.setPixmap(pixmap)

    def _ajustar_zoom_imagem(self, fator: float) -> None:
        if self.pixmap_atual is None:
            return

        self.zoom_imagem = max(0.35, min(8.0, self.zoom_imagem * fator))
        self._redimensionar_pixmap()

    def _resetar_zoom_imagem(self) -> None:
        if self.pixmap_atual is None:
            return

        self.zoom_imagem = 1.0
        self._redimensionar_pixmap()

    def resizeEvent(self, evento) -> None:
        super().resizeEvent(evento)
        self._redimensionar_pixmap()

    def _preencher_rotulos(self) -> None:
        if not self.item_atual:
            return

        selecionados = set(self.item_atual.get("rotulos_detectados", []))
        probabilidades = self.item_atual.get("probabilidades", {})
        limiares = self.item_atual.get("limiares", {})

        for rotulo in self.rotulos:
            label_rotulo = self.labels_rotulos.get(rotulo)
            barra = self.barras_probabilidade.get(rotulo)

            if label_rotulo is not None:
                ativo = rotulo in selecionados
                marcador = "<span style='color:#8b5cf6'>●</span>" if ativo else "<span style='color:#8fa0b8'>○</span>"
                label_rotulo.setText(f"{marcador}  {rotulo}")
                label_rotulo.setProperty("ativo", "true" if ativo else "false")
                label_rotulo.style().unpolish(label_rotulo)
                label_rotulo.style().polish(label_rotulo)

            if barra is not None:
                prob = float(probabilidades.get(rotulo, 0.0) or 0.0)
                limiar = float(limiares.get(rotulo, LIMIAR_PADRAO) or LIMIAR_PADRAO)
                barra.setValue(max(0, min(100, int(round(prob * 100)))))
                barra.setProperty("ativo", "true" if rotulo in selecionados else "false")
                barra.style().unpolish(barra)
                barra.style().polish(barra)

                if hasattr(barra, "label_valor"):
                    barra.label_valor.setText(f"{prob:.4f} / {limiar:.2f}")  # type: ignore[attr-defined]

    def _trocar_camada(self, camada: str) -> None:
        self.camada_atual = camada
        self._atualizar_botoes_camada()
        self._atualizar_imagem()

    def _atualizar_botoes_camada(self) -> None:
        if not hasattr(self, "botao_camada1"):
            return

        for botao, ativo in [
            (self.botao_camada1, self.camada_atual == "A"),
            (self.botao_camada2, self.camada_atual == "R"),
        ]:
            botao.setProperty("ativo", "true" if ativo else "false")
            botao.style().unpolish(botao)
            botao.style().polish(botao)

    def _rotulos_selecionados(self) -> list[str]:
        return [rotulo for rotulo, checkbox in self.checkboxes_rotulos.items() if checkbox.isChecked()]

    def _limpar_rotulos(self) -> None:
        for checkbox in self.checkboxes_rotulos.values():
            checkbox.setChecked(False)

    def _usar_sugestao(self) -> None:
        if not self.item_atual:
            return

        sugestao = set(self.item_atual.get("rotulos_detectados", []))

        for rotulo, checkbox in self.checkboxes_rotulos.items():
            checkbox.setChecked(rotulo in sugestao)

    def _salvar_revisao(self, status: str) -> None:
        if not self.item_atual:
            return

        selecionados = self._rotulos_selecionados()
        item_id = str(self.item_atual.get("id", ""))

        if not item_id:
            return

        revisao = {
            "id": item_id,
            "chave": self.item_atual.get("chave", ""),
            "caminho_imagem": self.item_atual.get("caminho_imagem", ""),
            "status": status,
            "rotulos_sugeridos": list(self.item_atual.get("rotulos_detectados", [])),
            "rotulos_confirmados": selecionados,
            "observacao": "",
            "revisado_em": agora(),
        }
        self.revisoes[item_id] = revisao
        salvar_json(ARQUIVO_REVISOES_JSON, self.revisoes)
        self.predicoes = aplicar_revisoes(self.predicoes, self.revisoes)
        salvar_json(ARQUIVO_PREDICOES_JSON, self.predicoes)
        salvar_predicoes_csv(self.predicoes, self.rotulos)
        exportar_resultados(self.predicoes, self.revisoes, self.rotulos)
        self._log(f"Revisao salva: {self.item_atual.get('chave', '')} -> {status}\n")

        atual = self.lista_imagens.currentRow()
        self._aplicar_filtro()

        if self.predicoes_filtradas:
            self.lista_imagens.setCurrentRow(min(atual + 1, len(self.predicoes_filtradas) - 1))

        self._atualizar_estado()

    def _proximo_item(self) -> None:
        linha = self.lista_imagens.currentRow()

        if linha < self.lista_imagens.count() - 1:
            self.lista_imagens.setCurrentRow(linha + 1)

    def _item_anterior(self) -> None:
        linha = self.lista_imagens.currentRow()

        if linha > 0:
            self.lista_imagens.setCurrentRow(linha - 1)

    def _alternar_tela(self) -> None:
        if self.isFullScreen() or self.isMaximized():
            self.showNormal()
            return

        tela = self.screen() or QApplication.primaryScreen()

        if tela is not None:
            geometria = tela.geometry()
            self.setGeometry(geometria)
            self.move(geometria.topLeft())

        self.showFullScreen()

    def _atualizar_tela(self) -> None:
        item_id = str(self.item_atual.get("id", "")) if self.item_atual else ""
        self._carregar_dados()

        if item_id:
            for indice, item in enumerate(self.predicoes_filtradas):
                if str(item.get("id", "")) == item_id:
                    self.lista_imagens.setCurrentRow(indice)
                    break

        self._atualizar_estado()
        self._log("Tela atualizada.\n")

    def _atualizar_estado(self) -> None:
        predicoes = self.predicoes
        total = len(predicoes)
        pendentes = sum(1 for item in predicoes if item.get("status_revisao", "pendente") == "pendente")

        self.cartao_total.setValor(str(total))
        self.cartao_pendentes.setValor(str(pendentes))

        resumo_modelo = resumo_modelo_ativo_interface()

        self.cartao_modelo.setValor(resumo_modelo["tipo"])
        self.cartao_modelo.setSubtitulo(resumo_modelo["subtitulo"])
        self.cartao_treino.setValor(resumo_modelo["valor_treino"])

    def closeEvent(self, evento) -> None:
        if self.tarefa is not None and self.tarefa.isRunning():
            resposta = QMessageBox.question(
                self,
                "Fechar",
                "Existe uma tarefa em execução. Deseja pedir a parada e fechar?",
            )

            if resposta != QMessageBox.StandardButton.Yes:
                evento.ignore()
                return

            self.tarefa.parar()

        evento.accept()


def main() -> None:
    configurar_app_user_model_id()

    app = QApplication(sys.argv)
    app.setApplicationName("BenaZub")
    app.setOrganizationName("UTFPR")

    fonte = QFont("Segoe UI", 9)
    app.setFont(fonte)

    aplicar_icone_aplicativo(app=app)

    janela = JanelaPrincipal()
    aplicar_icone_aplicativo(janela=janela)

    tela = escolher_tela_inicial(app)
    mostrar_fullscreen_na_tela(janela, tela)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
