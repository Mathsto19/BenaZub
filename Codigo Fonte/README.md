# BenaZub - Codigo Fonte

Este diretorio contem o codigo principal do BenaZub, software local para gerar sugestoes de rotulos em imagens biometricas, importar pacotes BENAPRO ja anotados, revisar predicoes e retreinar um modelo incremental.

A execucao documentada aqui e para Windows. O programa e iniciado por Python e abre uma interface grafica local desenvolvida com PyQt6.

Este diretorio trata apenas do software local para Windows.

---

## Estrutura Geral

A estrutura principal do codigo fonte e formada por:

- `BenaZub.py`: aplicacao principal.
- `requirements.txt`: dependencias necessarias para rodar pelo codigo fonte.
- `README.md`: documentacao de uso do codigo fonte.
- `BenaZub/`: pasta de trabalho padrao do software.

A pasta `BenaZub/` contem as subpastas principais usadas pelo programa:

- `entrada/imagens/`: local para colocar arquivos `.zip` ou imagens para predicao.
- `entrada/rotulos/`: local para colocar arquivos `.json` ou `.csv` com rotulos existentes.
- `saida/`: local onde o software salva predicoes, revisoes, modelos, backups e arquivos extraidos.
- `saida/backups_ciclo/`: backups criados antes de novos ciclos de treinamento.
- `saida/modelo_incremental/`: modelo treinado incrementalmente pelo software.
- `saida/treino_base_atual/`: base rotulada preparada para treinamento.
- `saida/zips_extraidos/`: imagens extraidas automaticamente de arquivos `.zip`.
- `ui/`: arquivos auxiliares da interface grafica.

A pasta interna `BenaZub/` deve permanecer ao lado do arquivo `BenaZub.py`, pois ela funciona como pasta de trabalho padrao do software.

---

## Requisitos

- Windows 10 ou Windows 11.
- Python 3.10 ou superior.
- Permissao de leitura nos pacotes de imagem.
- Permissao de escrita na pasta `BenaZub/saida/`.

Instale as dependencias com:

`python -m pip install -r requirements.txt`

Dependencias atuais:

- `PyQt6>=6.6.0`
- `numpy>=1.26.0`
- `Pillow>=10.0.0`
- `torch>=2.3.0`
- `torchvision>=0.18.0`

Observacao: `torch` e `torchvision` sao necessarios para gerar predicoes, treinar o modelo incremental e calibrar limiares. A interface pode abrir mesmo sem essas bibliotecas, mas as funcoes de modelo nao funcionarao corretamente sem elas.

---

## Modelo Ativo

O modelo ativo e escolhido nesta ordem:

1. `BenaZub/saida/modelo_incremental/melhor_modelo.pt`
2. `resultados/modelos/melhor_modelo.pt`

Os limiares tambem seguem a mesma logica:

1. `BenaZub/saida/modelo_incremental/limiares.json`
2. `resultados/modelos/limiares.json`

Se nenhum modelo existir, o aplicativo ainda pode abrir. No entanto, as funcoes de predicao dependem de um modelo disponivel ou de um ciclo de treinamento que consiga criar um modelo inicial.

---

## Como Executar

Entre nesta pasta:

`C:\Users\mathe\Downloads\BenaZub\Codigo Fonte`

Execute:

`python BenaZub.py`

O BenaZub abre automaticamente em tela cheia.

A tela principal possui tres partes importantes:

- `Base de revisao`: selecao da pasta ou ZIP de imagens, arquivo opcional de rotulos existentes e opcoes de importacao.
- `Treino`: configuracao de epocas, paciencia, taxa de aprendizado e fracao de validacao.
- `Acoes`: execucao do fluxo completo, atualizacao do modelo, geracao de predicoes e abertura da pasta de saida.

A interface tambem possui duas abas principais:

- `Estado e logs`: exibe logs, total de imagens, imagens a revisar e informacoes do modelo.
- `Predicoes`: exibe as imagens, as camadas disponiveis e os rotulos sugeridos pelo modelo.

---

## Comecar Limpo

Se o BenaZub parecer que ja iniciou com dados prontos, normalmente e porque encontrou arquivos antigos em `BenaZub/saida`.

Para uma entrega limpa, mantenha o modelo em `BenaZub/saida/modelo_incremental`, se desejar preservar o treinamento, mas remova ou mova estes arquivos de execucao:

- `BenaZub/saida/predicoes_auto.json`
- `BenaZub/saida/predicoes_auto.csv`
- `BenaZub/saida/revisoes.json`
- `BenaZub/saida/rotulos_confirmados.csv`
- `BenaZub/saida/rotulos_corrigir.csv`
- arquivos dentro de `BenaZub/entrada/imagens/`
- arquivos dentro de `BenaZub/saida/zips_extraidos/`

Tambem existe importacao automatica de pacotes BENAPRO. Qualquer pasta neste formato, se estiver diretamente dentro de `BenaZub/`, pode ser lida pelo app quando `Importar pacotes BENAPRO` estiver marcado:

- `BenaZub/nome-do-pacote/nome-do-pacote.zip`
- `BenaZub/nome-do-pacote/BENAPRO/resultado.json`

Para impedir essa importacao, desmarque `Importar pacotes BENAPRO` ou mova os pacotes para fora da pasta `BenaZub/`.

---

## Usar com Imagens Soltas

1. Coloque as imagens ou um pacote `.zip` em `BenaZub/entrada/imagens/`.

2. Ou clique em `Escolher` no campo `Pasta ou ZIP de imagens` e selecione outro arquivo `.zip`.

3. Se quiser ignorar imagens ja rotuladas, informe um arquivo `.csv` ou `.json` no campo `Rotulos ja existentes`.

4. Marque `Recalcular predicoes` quando quiser forcar uma nova execucao do modelo.

5. Clique em `Gerar predicoes com modelo atual`.

As predicoes aparecem na aba `Predicoes`.

Use os botoes `Anterior` e `Proxima` ou as setas do teclado para navegar entre as imagens.

Use `Camada 1` e `Camada 2` ou os atalhos `1` e `2` para alternar a visualizacao da imagem.

---

## Usar com Pacote BENAPRO

O pacote BENAPRO precisa ter um ZIP de imagens e um JSON de resultado.

Formato esperado:

- `BenaZub/Meu Pacote/meu_pacote.zip`
- `BenaZub/Meu Pacote/BENAPRO/resultado.json`

O `resultado.json` deve apontar para o nome do ZIP. Exemplo:

{
  "meu_pacote.zip": [
    {
      "arquivo": "imagem_001.png",
      "erros": [
        { "nome": "Scanner Sujo", "avaliacao": 1 },
        { "nome": "Manchas na Digital", "avaliacao": 3 }
      ]
    }
  ]
}

Rotulos reconhecidos pelo BenaZub:

- `Digital Clara`
- `Digital Escura`
- `Dedo Fora Da Area`
- `Fiapos`
- `Fora de Foco`
- `Manchas`
- `Scanner Sujo`
- `Segmentacao Boa`
- `Sem Padrao Visivel`

Ao importar um pacote BENAPRO:

- imagens que ja aparecem no `resultado.json` entram como base rotulada para treino;
- imagens do ZIP que nao aparecem no `resultado.json` sao extraidas para a fila de revisao e predicao.

---

## Exemplo Incluido

Este projeto pode incluir arquivos de exemplo em:

- `BenaZub/entrada/imagens/exemplo.zip`
- `BenaZub/entrada/rotulos/exemplo.json`

Para testar o fluxo com exemplo:

1. Execute `python BenaZub.py`.

2. No campo `Pasta ou ZIP de imagens`, selecione `BenaZub/entrada/imagens/exemplo.zip`.

3. No campo `Rotulos ja existentes`, selecione `BenaZub/entrada/rotulos/exemplo.json`.

4. Clique em `Atualizar modelo` para treinar e calibrar.

5. Clique em `Gerar predicoes com modelo atual` para gerar predicoes.

Se todas as imagens do exemplo ja estiverem anotadas no arquivo JSON, a geracao de predicoes pode retornar poucas ou nenhuma imagem nova para revisar. Isso e esperado quando o exemplo representa uma base ja rotulada.

---

## Treinar e Calibrar

Pela interface:

1. Ajuste `Epocas`, `Paciencia`, `Taxa de aprendizado` e `Fracao de validacao`.

2. Clique em `Atualizar modelo` para treinar e calibrar o modelo.

3. Clique em `Fluxo completo: treinar e gerar` para treinar, calibrar e gerar predicoes em sequencia.

Durante o treinamento, o software cria backups dos arquivos importantes em `BenaZub/saida/backups_ciclo/`.

O treinamento gera arquivos principalmente em:

- `BenaZub/saida/modelo_incremental/`
- `BenaZub/saida/treino_base_atual/`

---

## Arquivos de Saida

O BenaZub grava os principais resultados em `BenaZub/saida/`.

Arquivos principais:

- `predicoes_auto.json`: predicoes completas em formato JSON.
- `predicoes_auto.csv`: predicoes em formato CSV.
- `revisoes.json`: revisoes feitas pelo usuario.
- `rotulos_confirmados.csv`: imagens confirmadas para uso no treinamento.
- `rotulos_corrigir.csv`: imagens marcadas para correcao.
- `treino_base_atual/base_atual_rotulada.csv`: base rotulada consolidada.
- `treino_base_atual/treino.csv`: divisao usada para treino.
- `treino_base_atual/validacao.csv`: divisao usada para validacao.
- `modelo_incremental/melhor_modelo.pt`: melhor modelo salvo pelo treinamento incremental.
- `modelo_incremental/limiares.json`: limiares usados nas proximas predicoes.
- `modelo_incremental/historico_treinamento.csv`: historico das epocas de treinamento.
- `modelo_incremental/resumo_treinamento.json`: resumo do ultimo treinamento.
- `modelo_incremental/metricas_limiares.csv`: metricas usadas na calibracao dos limiares.

`modelo_incremental/melhor_modelo.pt` e `modelo_incremental/limiares.json` sao os arquivos usados nas proximas predicoes.

---

## Atalhos da Interface

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

## Observacoes de Desenvolvimento

- O aplicativo usa interface grafica local em PyQt6.
- A pasta `BenaZub/` e a pasta de trabalho padrao do software.
- A funcao de inicializacao cria automaticamente as pastas obrigatorias quando elas nao existem.
- Os arquivos `chevron-up.svg` e `chevron-down.svg` ficam em `BenaZub/ui/` e sao usados na interface.
- As imagens podem ser lidas a partir de uma pasta ou diretamente de arquivos `.zip`.
- O treinamento usa PyTorch e TorchVision.
- O modelo utilizado no treinamento incremental e baseado em EfficientNet-B0.
- Os arquivos de saida nao devem ser editados manualmente durante a execucao do software.
- Para empacotar como executavel, mantenha a pasta `BenaZub/` junto ao `.exe`.

---

## Compatibilidade com Estrutura Antiga

Versoes anteriores do projeto usavam a pasta `app_validador_auto_rotulos`.

A estrutura atual usa a pasta `BenaZub`.

O codigo ainda possui compatibilidade parcial com caminhos antigos para facilitar migracao, mas a estrutura recomendada para entrega e documentacao e a pasta `BenaZub`.

---

## Suporte

Em caso de duvidas, sugestoes ou problemas tecnicos:

- matheusaugustooliveira@alunos.utfpr.edu.br
