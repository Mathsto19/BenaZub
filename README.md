# BenaZub - Repositorio Oficial

Bem-vindo ao **BenaZub**, um software local para predicao automatica, revisao e treinamento incremental de rotulos em imagens biometricas.

O BenaZub roda no Windows e abre uma interface grafica local desenvolvida com PyQt6. A ferramenta permite carregar imagens, gerar sugestoes automaticas de rotulos, revisar predicoes, importar pacotes BENAPRO ja anotados e atualizar incrementalmente um modelo de classificacao multirrotulo.

Este repositorio cobre apenas o aplicativo local para Windows.

Este repositorio reune:

- **Codigo fonte em Python** para execucao, manutencao e evolucao do projeto.
- **Area de aplicativo Windows** para distribuicao empacotada.
- **Pasta de trabalho padrao** usada pelo software para entrada, saida, modelos e arquivos auxiliares.

---

## Sobre o Projeto

O BenaZub foi desenvolvido para apoiar o processo de rotulagem, revisao e reaproveitamento de imagens biometricas em bases de pesquisa. Em vez de depender apenas de anotacao manual, a ferramenta permite usar um modelo de aprendizado de maquina para sugerir rotulos e, em seguida, permite que o avaliador revise os resultados.

A ferramenta permite:

- carregamento de imagens por arquivo `.zip` ou pasta local;
- leitura opcional de arquivos `.json` ou `.csv` com rotulos existentes;
- geracao automatica de predicoes multirrotulo;
- visualizacao das probabilidades por rotulo;
- revisao das sugestoes do modelo;
- importacao de pacotes BENAPRO ja anotados;
- treinamento incremental do modelo;
- calibracao de limiares;
- exportacao de predicoes, revisoes e bases consolidadas;
- execucao local sem envio de dados para servidor externo.

Com isso, o BenaZub auxilia na construcao e ampliacao de bases rotuladas, permitindo ciclos sucessivos de predicao, revisao e retreinamento.

---

## Compatibilidade

| Sistema Operacional | Execucao principal | Executavel |
|---------------------|-------------------|------------|
| Windows 10/11       | `BenaZub.py`      | `BenaZub.exe`, quando empacotado |

> Este projeto esta documentado apenas para Windows.

---

## Estrutura do Repositorio

A estrutura principal do repositorio e formada por:

- `Aplicativo/`: pasta destinada ao executavel Windows e aos arquivos de uso final.
- `Codigo Fonte/`: pasta com o codigo Python, dependencias e pasta de trabalho do software.
- `LICENSE`: arquivo de licenca.
- `README.md`: documentacao geral do repositorio.

Dentro de `Aplicativo/`, a estrutura esperada e:

- `BenaZub.exe`, quando a versao empacotada estiver disponivel.
- `README.md`, com instrucoes da versao de aplicativo.
- `Leia-me.txt`, com guia rapido para o usuario final.
- `BenaZub/`, pasta de trabalho usada pelo executavel.

Dentro de `Codigo Fonte/`, a estrutura principal e:

- `BenaZub.py`, aplicacao principal.
- `requirements.txt`, dependencias Python.
- `README.md`, manual especifico do codigo fonte.
- `BenaZub/`, pasta de trabalho usada durante a execucao pelo codigo fonte.

A pasta interna `BenaZub/` e essencial para o funcionamento do software. Ela contem entradas, saidas, modelos, backups, arquivos extraidos e recursos auxiliares de interface.

---

## Componentes

### 1. Codigo Fonte

Contem a implementacao principal do BenaZub.

Arquivos principais:

- `Codigo Fonte/BenaZub.py`: aplicacao principal.
- `Codigo Fonte/requirements.txt`: dependencias Python.
- `Codigo Fonte/README.md`: instrucoes especificas para execucao pelo codigo fonte.
- `Codigo Fonte/BenaZub/`: pasta de trabalho padrao do software.

Manual especifico:

- `Codigo Fonte/README.md`

### 2. Aplicativo

Pasta destinada a versao empacotada para Windows. Se a distribuicao recebida incluir `BenaZub.exe`, ele deve ser executado diretamente por essa pasta. Caso contrario, use a execucao pelo codigo fonte.

Manual especifico:

- `Aplicativo/README.md`
- `Aplicativo/Leia-me.txt`

---

## Funcionalidades Principais

- **Predicao automatica**: usa um modelo treinado para sugerir rotulos para imagens biometricas.
- **Classificacao multirrotulo**: uma mesma imagem pode receber mais de um rotulo.
- **Revisao assistida**: permite conferir as sugestoes do modelo e validar os resultados.
- **Importacao BENAPRO**: reaproveita pacotes anotados no formato BENAPRO.
- **Treinamento incremental**: atualiza o modelo com dados confirmados e dados importados.
- **Calibracao de limiares**: ajusta limiares por rotulo com base na validacao.
- **Camadas de visualizacao**: permite alternar entre camadas da imagem quando disponiveis.
- **Logs locais**: registra o andamento das tarefas na interface.
- **Backups automaticos**: cria backups antes de novos ciclos de treinamento.
- **Exportacao estruturada**: gera arquivos JSON e CSV para auditoria, revisao e treinamento posterior.

---

## Rotulos Padrao

Rotulos reconhecidos pelo BenaZub:

| Rotulo | Finalidade |
|--------|------------|
| Digital Clara | Indica imagem clara, com cristas pouco evidentes. |
| Digital Escura | Indica imagem escura, com excesso de contraste ou pressao. |
| Dedo Fora Da Area | Indica posicionamento inadequado do dedo na area de captura. |
| Fiapos | Indica presenca de fibras ou fiapos na imagem. |
| Fora de Foco | Indica perda de nitidez. |
| Manchas | Indica manchas, residuos ou artefatos na digital. |
| Scanner Sujo | Indica sujeira ou interferencia associada ao sensor. |
| Segmentacao Boa | Indica imagem adequada quanto a segmentacao. |
| Sem Padrao Visivel | Indica ausencia de padrao de cristas confiavel. |

### Regras de consistencia

O BenaZub aplica regras automaticas para reduzir contradicoes nas predicoes. Por exemplo:

- `Segmentacao Boa` nao deve permanecer junto com outros erros detectados.
- Quando `Digital Clara` e `Digital Escura` aparecem juntas, o sistema preserva a classe com maior probabilidade.
- Os rotulos vindos de pacotes BENAPRO podem ser normalizados para manter consistencia com o catalogo do BenaZub.

---

## Como Executar pelo Codigo Fonte

### 1. Entrar na pasta do codigo

```powershell
cd "C:\Users\mathe\Downloads\BenaZub\Codigo Fonte"
```

### 2. Instalar dependencias

```powershell
python -m pip install -r requirements.txt
```

### 3. Executar o BenaZub

```powershell
python BenaZub.py
```

O aplicativo abre automaticamente em tela cheia.

---

## Como Executar pelo Aplicativo

Quando a versao empacotada estiver disponivel:

1. Abra a pasta `Aplicativo`.
2. Execute `BenaZub.exe`.
3. Se o Windows SmartScreen bloquear a abertura, clique em `Mais informacoes` e depois em `Executar assim mesmo`.
4. Aguarde a interface abrir.

A pasta `BenaZub/` deve permanecer junto ao executavel.

---

## Uso Basico

### 1. Preparar imagens

Coloque as imagens ou um pacote `.zip` em:

- `BenaZub/entrada/imagens/`

Tambem e possivel selecionar outro arquivo `.zip` diretamente pela interface.

### 2. Preparar rotulos existentes

Se houver um arquivo de rotulos ja existentes, coloque em:

- `BenaZub/entrada/rotulos/`

Formatos aceitos:

- `.json`
- `.csv`

### 3. Gerar predicoes

Na interface:

1. Selecione a pasta ou ZIP de imagens.
2. Selecione o arquivo de rotulos existentes, se houver.
3. Marque `Recalcular predicoes` quando quiser forcar nova execucao.
4. Clique em `Gerar predicoes com modelo atual`.

As predicoes serao exibidas na aba `Predicoes`.

### 4. Revisar resultados

Na aba `Predicoes`, e possivel:

- navegar entre imagens;
- alternar camadas;
- visualizar probabilidades por rotulo;
- conferir limiares;
- revisar as sugestoes do modelo.

### 5. Atualizar modelo

Para atualizar o modelo incremental:

1. Ajuste `Epocas`, `Paciencia`, `Taxa de aprendizado` e `Fracao de validacao`.
2. Clique em `Atualizar modelo`.

Para executar tudo em sequencia, use:

- `Fluxo completo: treinar e gerar`

---

## Modelo Ativo

O BenaZub procura o modelo ativo nesta ordem:

1. `BenaZub/saida/modelo_incremental/melhor_modelo.pt`
2. `resultados/modelos/melhor_modelo.pt`

Os limiares seguem a mesma prioridade:

1. `BenaZub/saida/modelo_incremental/limiares.json`
2. `resultados/modelos/limiares.json`

Se nenhum modelo existir, o aplicativo pode abrir. No entanto, a geracao de predicoes depende de um modelo disponivel ou de um ciclo de treinamento inicial.

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

## Entradas

O BenaZub aceita:

- arquivo `.zip` contendo imagens;
- pasta local contendo imagens;
- arquivo `.json` com rotulos existentes;
- arquivo `.csv` com rotulos existentes;
- imagens nos formatos `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tif`, `.tiff` e `.webp`.

---

## Saida de Dados

O BenaZub grava os principais resultados em:

- `BenaZub/saida/`

Arquivos principais:

| Arquivo | Conteudo |
|---------|----------|
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
- `treino_base_atual/`: base rotulada consolidada e divisao de treino/validacao.
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

- Sistema operacional: Windows 10 ou Windows 11.
- Python: 3.10 ou superior, para execucao pelo codigo fonte.
- Memoria RAM recomendada: 8 GB ou mais.
- Armazenamento suficiente para imagens, arquivos extraidos, modelos e backups.
- Dependencias Python principais:
  - PyQt6
  - NumPy
  - Pillow
  - PyTorch
  - TorchVision

Quando estiver usando `BenaZub.exe`, nao e necessario instalar Python manualmente. Quando estiver usando o codigo fonte, instale as dependencias com `requirements.txt`.

---

## Observacoes de Desenvolvimento

- O aplicativo usa interface grafica local em PyQt6.
- O treinamento usa PyTorch e TorchVision.
- O modelo utilizado no treinamento incremental e baseado em EfficientNet-B0.
- A pasta `BenaZub/` e a pasta de trabalho padrao do software.
- As pastas obrigatorias sao criadas automaticamente durante a execucao.
- Os arquivos de saida nao devem ser editados manualmente enquanto o software estiver aberto.
- Para empacotar ou distribuir o aplicativo, mantenha `BenaZub.exe` e a pasta `BenaZub/` juntos.

---

## Compatibilidade com Estrutura Antiga

Versoes anteriores do projeto usavam a pasta `app_validador_auto_rotulos`.

A estrutura atual usa a pasta `BenaZub`.

O codigo ainda possui compatibilidade parcial com caminhos antigos para facilitar migracao, mas a estrutura recomendada para entrega e documentacao e a pasta `BenaZub`.

---

## Suporte e Contato

Para duvidas, suporte tecnico ou colaboracoes:

- Matheus Augusto - [matheusaugustooliveira@alunos.utfpr.edu.br](mailto:matheusaugustooliveira@alunos.utfpr.edu.br)

---

## Agradecimentos

Este projeto foi desenvolvido na UTFPR com apoio do projeto de pesquisa em biometria neonatal.

---

## Licença

Distribuicao autorizada apenas para fins academicos, cientificos e de pesquisa. Uso comercial ou redistribuicao sem permissao nao e permitido.
