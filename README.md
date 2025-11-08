# Impostômetro Irlandês (Python)

Projeto de referência para um "Impostômetro" que estima, em tempo quase real, quanto a Irlanda arrecada de impostos.

## Como funciona (fórmula)
Definimos:
- `YTD` = total arrecadado no ano até o último dado oficial publicado.
- `r` (taxa média por segundo) = receita média do período recente dividida pela quantidade de segundos do período.
- `t0` = instante de ancoragem (quando o servidor inicializa, ou o momento do último dado oficial).
- `t` = tempo atual.

O contador em tempo real é estimado por:
```
Imposto(t) = YTD(t0) + r * (t - t0)
```
onde `r` pode ser calculado de formas diferentes (configuráveis):
- **`monthly`**: usa o total do mês mais recente e divide pelos segundos daquele mês.
- **`rolling_3m`**: média dos últimos 3 meses, dividida pelos segundos combinados desses meses (suaviza sazonalidade).
- **`annualized`**: usa a média mensal do ano até a data e anualiza.

> **Observação:** Este projeto usa dados amostrais em `data/sample_monthly.csv`. Substitua pelo CSV oficial do Department of Finance da Irlanda (Databank) ou conecte a uma API para usar em produção.

## Rodando localmente
1. Crie um virtualenv e instale dependências:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Execute o servidor:
   ```bash
   python app.py
   ```
3. Abra `http://127.0.0.1:5000` no navegador para ver o contador.

## Configuração
Edite `config.yaml`:
- `data.csv_path`: caminho para o CSV com arrecadação mensal (colunas: year, month, net_receipts_eur).
- `estimation.method`: `monthly`, `rolling_3m`, ou `annualized`.
- `estimation.anchor`: `server_start` ou `month_end`.

## Formato do CSV
O arquivo deve conter:
```
year,month,net_receipts_eur
2025,1,9000000000
2025,2,8200000000
...
```
`net_receipts_eur` em **euros** (valor mensal).

## Pontos de melhoria
- Integração automática com o Databank (download mensal).
- Ajuste de sazonalidade por tipo de imposto (Income Tax, VAT, Corporation Tax).
- Intervalos de confiança e barras de erro no front-end.
- Cache e testes unitários.

---

Feito para demonstração: substitua os dados amostrais por dados oficiais para uso real.