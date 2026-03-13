# AutomacaoIPTU
Pipeline de ETL em Python para processamento massivo de dados tributários (IPTU/ISS) e geração automatizada de documentos em lote (Batching) com ReportLab e Pandas."
📄 ETL e Automação de Carnês Tributários (ReportLab & Pandas)

Este repositório contém o código-fonte de um pipeline de ETL desenvolvido em Python para automatizar a geração de mais de 12.000 carnês de IPTU e ISS (totalizando mais de +160 mil páginas).

⚠️ Nota de Privacidade: Por questões de LGPD e confidencialidade contratual, os arquivos de dados (.csv) e os templates visuais de impressão (.png) não foram incluídos neste repositório. O código serve como demonstração de lógica de estruturação, batching e uso das bibliotecas.
🛠️ Tecnologias Utilizadas

    Python 3

    Pandas: Para extração (E), transformação (T) dos dados brutos e ordenação/triagem logística.

    ReportLab: Para a carga (L) no PDF e geração nativa de Códigos de Barras (padrão FEBRABAN).

🧠 Principais Desafios Resolvidos

    Arquitetura de Batching: Para evitar estouro de memória e travamento de impressoras gráficas, o script simula o tamanho do documento final e fatia automaticamente a geração em lotes de no máximo 21.000 páginas.

    Roteirização: O código aplica regras de negócio para preenchimento de páginas em branco (para fechar o lote físico da gráfica).
