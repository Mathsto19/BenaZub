# BenaZub - Aplicativo Windows

Esta pasta e destinada a versao empacotada do **BenaZub** para Windows e aos arquivos necessarios para uso final do software.

Se a distribuicao recebida incluir `BenaZub.exe`, use o executavel diretamente. Se o executavel ainda nao estiver presente, rode o sistema pelo codigo fonte em `..\Codigo Fonte\BenaZub.py`.

O BenaZub e um software local para gerar sugestoes automaticas de rotulos em imagens biometricas, revisar predicoes e atualizar incrementalmente um modelo de classificacao multirrotulo.

---

## Compatibilidade

| Sistema Operacional | Executavel |
|---------------------|------------|
| Windows 10/11       | `BenaZub.exe`, quando disponivel |

Esta documentacao cobre apenas o uso no Windows.

---

## Estrutura Esperada

A estrutura esperada da pasta `Aplicativo` e:

- `BenaZub.exe`: executavel do software, quando a versao empacotada for distribuida.
- `README.md`: documentacao de uso da versao de aplicativo.
- `Leia-me.txt`: guia rapido para o usuario final.
- `BenaZub/`: pasta de trabalho padrao do software.

A pasta `BenaZub/` deve permanecer no mesmo diretorio do executavel.

Subpastas principais:

- `BenaZub/entrada/imagens/`: local para colocar arquivos `.zip` ou imagens.
- `BenaZub/entrada/rotulos/`: local para colocar arquivos `.json` ou `.csv` com rotulos existentes.
- `BenaZub/saida/`: local onde o software salva predicoes, revisoes, modelos, backups e arquivos extraidos.
- `BenaZub/ui/`: arquivos auxiliares da interface grafica.

---

## Como Inicializar

### Usando o executavel

1. Abra a pasta `Aplicativo`.
2. Execute `BenaZub.exe`.
3. Se o Windows SmartScreen bloquear a abertura, clique em `Mais informacoes` e depois em `Executar assim mesmo`.
4. Aguarde a interface abrir em tela cheia.

### Sem executavel

Use a versao pelo codigo fonte:

`cd "..\Codigo Fonte"`

`python -m pip install -r requirements.txt`

`python BenaZub.py`

---

## Como Utilizar

### 1. Preparar imagens

Coloque as imagens ou um pacote `.zip` em:

`BenaZub/entrada/imagens/`

Tambem e possivel selecionar manualmente outro ZIP pela interface, no campo `Pasta ou ZIP de imagens`.

### 2. Preparar rotulos existentes

Se houver um arquivo de rotulos ja existentes, coloque em:

`BenaZub/entrada/rotulos/`

O arquivo pode estar em formato `.json` ou `.csv`.

Na interface, selecione esse arquivo no campo `Rotulos ja existentes`.

### 3. Gerar predicoes

Para gerar sugestoes automaticas com o modelo atual:

- selecione a pasta ou ZIP de imagens;
- selecione o arquivo de rotulos, se existir;
- marque `Recalcular predicoes`, se quiser forcar uma nova execucao;
- clique em `Gerar predicoes com modelo atual`.

As predicoes aparecem na aba `Predicoes`.

### 4. Revisar predicoes

Na aba `Predicoes`, o usuario pode:

- navegar entre imagens;
- visualizar probabilidades por rotulo;
- alternar entre camadas;
- conferir as sugestoes do modelo;
- salvar revisoes.

### 5. Atualizar modelo

Para atualizar o modelo incremental:

- ajuste `Epocas`, `Paciencia`, `Taxa de aprendizado` e `Fracao de validacao`;
- clique em `Atualizar modelo`.

Para treinar, calibrar e gerar predicoes em sequencia, use:

`Fluxo completo: treinar e gerar`

---

## Modelo Ativo

O BenaZub procura o modelo ativo nesta ordem:

1. `BenaZub/saida/modelo_incremental/melhor_modelo.pt`
2. `resultados/modelos/melhor_modelo.pt`

Os limiares seguem a mesma prioridade:

1. `BenaZub/saida/modelo_incremental/limiares.json`
2. `resultados/modelos/limiares.json`

Se nenhum modelo existir, o aplicativo pode abrir, mas a geracao de predicoes depende de um modelo disponivel ou de um ciclo de treinamento inicial.

---

## Pacotes BENAPRO

O BenaZub pode importar automaticamente pacotes BENAPRO quando a opcao `Importar pacotes BENAPRO` estiver marcada.

Formato esperado:

- `BenaZub/nome-do-pacote/nome-do-pacote.zip`
- `BenaZub/nome-do-pacote/BENAPRO/resultado.json`

Ao importar um pacote BENAPRO:

- imagens ja anotadas no `resultado.json` entram como base rotulada para treinamento;
- imagens do ZIP que nao aparecem no JSON podem entrar na fila de predicao e revisao.

Para impedir essa importacao, desmarque `Importar pacotes BENAPRO` ou mova esses pacotes para fora da pasta `BenaZub/`.

---

## Rotulos Reconhecidos

Rotulos padrao do BenaZub:

- Digital Clara
- Digital Escura
- Dedo Fora Da Area
- Fiapos
- Fora de Foco
- Manchas
- Scanner Sujo
- Segmentacao Boa
- Sem Padrao Visivel

O software aplica regras automaticas de consistencia entre alguns rotulos. Por exemplo, `Segmentacao Boa` nao deve permanecer junto com outros erros detectados.

---

## Saidas Geradas

O BenaZub salva os principais resultados em:

`BenaZub/saida/`

Arquivos principais:

| Arquivo | Finalidade |
|---------|------------|
| `predicoes_auto.json` | Predicoes completas em formato JSON. |
| `predicoes_auto.csv` | Predicoes em formato CSV. |
| `revisoes.json` | Revisoes feitas pelo usuario. |
| `rotulos_confirmados.csv` | Imagens confirmadas para uso no treinamento. |
| `rotulos_corrigir.csv` | Imagens marcadas para correcao. |
| `modelo_incremental/melhor_modelo.pt` | Melhor modelo salvo pelo treinamento incremental. |
| `modelo_incremental/limiares.json` | Limiares usados nas proximas predicoes. |
| `modelo_incremental/historico_treinamento.csv` | Historico das epocas de treinamento. |
| `modelo_incremental/resumo_treinamento.json` | Resumo do ultimo treinamento. |
| `modelo_incremental/metricas_limiares.csv` | Metricas usadas na calibracao dos limiares. |

Pastas auxiliares:

- `backups_ciclo/`: backups criados antes de novos ciclos de treinamento.
- `treino_base_atual/`: base rotulada consolidada, divisao de treino e validacao.
- `zips_extraidos/`: conteudo extraido automaticamente de arquivos `.zip`.

---

## Atalhos

| Atalho | Acao |
|--------|------|
| `Seta direita` | Proxima imagem. |
| `Seta esquerda` | Imagem anterior. |
| `1` | Camada 1. |
| `2` | Camada 2. |
| `F5` | Atualizar estado da tela. |
| `Scroll do mouse` | Aumentar ou diminuir zoom. |
| `Duplo clique na imagem` | Resetar zoom. |

---

## Requisitos Tecnicos

- Windows 10 ou Windows 11.
- Memoria RAM recomendada: 8 GB ou mais.
- Espaco em disco suficiente para extrair pacotes `.zip`, salvar predicoes, backups e modelos.
- Quando estiver usando `BenaZub.exe`, nao e necessario instalar Python manualmente.
- Quando estiver usando o codigo fonte, instale Python 3.10+ e as dependencias de `requirements.txt`.

---

## Observacoes Importantes

- Nao apague a pasta `BenaZub/`, pois ela e usada pelo software durante a execucao.
- Os arquivos da pasta `saida/` sao gerados automaticamente.
- Evite editar manualmente arquivos de saida enquanto o software estiver aberto.
- Para empacotar ou distribuir o aplicativo, mantenha `BenaZub.exe` e a pasta `BenaZub/` juntos.

---

## Suporte

Em caso de duvidas, sugestoes ou problemas tecnicos:

- matheusaugustooliveira@alunos.utfpr.edu.br
