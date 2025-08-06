# 🤖 OCR Receitas Médicas via WhatsApp

Este projeto realiza a leitura automatizada de receitas médicas enviadas por WhatsApp. Ele utiliza a API de OCR do Azure para extrair informações como nome do paciente, CPF, data da receita, medicamentos prescritos e quantidades.

---

## 🚀 Funcionalidades

- Recebe imagens ou PDFs de receitas via WhatsApp (Twilio)
- Realiza pré-processamento da imagem (binarização, contraste)
- Usa o Azure OCR para extrair texto
- Corrige erros comuns de OCR automaticamente
- Extrai dados estruturados em JSON
- Identifica e calcula quantidades de medicamentos com base na posologia
- Consulta base de princípios ativos (CSV)
- Interage com o usuário caso alguma informação esteja ausente

---

## 📦 Estrutura do Projeto

```
Projeto_IHST/
│
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── services.py
│   ├── webhook.py
│   ├── principios_ativos.csv  ← base de dados local de medicamentos
│
├── receitas/
│   ├── ... arquivos recebidos por WhatsApp
│
├── .gitignore
├── requirements.txt
├── README.md
```

---

## ⚙️ Como Executar Localmente

1. Clone o repositório:
   ```bash
   git clone https://github.com/thig7179/ocr-receitas-whatsapp.git
   cd ocr-receitas-whatsapp
   ```

2. Crie e ative o ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate        # Linux/Mac
   venv\Scripts\activate.bat     # Windows
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure variáveis no `.env` ou `config.py`:
   ```
   TWILIO_SID=SEU_SID
   TWILIO_AUTH=SEU_AUTH_TOKEN
   AZURE_KEY=SUA_CHAVE_OCR
   AZURE_ENDPOINT=SUA_URL_DO_ENDPOINT
   ```

5. Execute o servidor local:
   ```bash
   flask run
   ```

---

## 💬 Exemplo de JSON de saída

```json
{
  "nome": "João da Silva",
  "cpf": "12345678910",
  "medicamentos": [
    {
      "nome": "Losartana 50mg",
      "quantidade": "30 comprimidos"
    },
    {
      "nome": "Metformina 850mg",
      "quantidade": "90 comprimidos"
    }
  ],
  "data_receita": "08 de Abril de 2020",
  "crm_medico": "RS 47384"
}
```

---

## 📩 Contato

Este projeto é mantido por **Thiago Henrique**

- GitHub: [@thig7179](https://github.com/thig7179)
- Email: thiagodosantos64@gmail.com

---

## 📄 Licença

Distribuído sob a licença **MIT**. Consulte o arquivo `LICENSE` para mais informações.