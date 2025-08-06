# 🤖 OCR de Receitas Médicas via WhatsApp – Projeto IHST

Este projeto realiza a **extração automatizada de dados de receitas médicas** enviadas por WhatsApp (imagem ou PDF), utilizando a **API OCR da Azure Cognitive Services**. Ele identifica nome do paciente, CPF, medicamentos prescritos, quantidade e posologia, e retorna as informações estruturadas em JSON.

---

## 🚀 Funcionalidades

- ✅ Recebimento de receitas via WhatsApp
- 📸 Suporte a imagens e PDFs
- 🔎 Extração de:
  - Nome do paciente
  - CPF
  - Medicamentos + dose (mg/ml/g)
  - Quantidade (ex: 30 comprimidos)
  - Data da receita
  - Nome do médico e CRM
- 📥 Correção de erros comuns de OCR
- 📚 Validação de nomes de medicamentos via base de dados `.csv`
- 📡 API OpenFDA como fallback
- 🤖 Comunicação com paciente via WhatsApp para dados incompletos

---

## 🧰 Tecnologias Utilizadas

- Python 3.11+
- Flask
- Twilio (WhatsApp API)
- OpenCV
- Azure Cognitive Services – OCR
- pdf2image, Pillow
- CSV como base de dados de medicamentos

---

## 📦 Estrutura do Projeto

