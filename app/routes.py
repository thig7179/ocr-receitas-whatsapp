from flask import Blueprint, request
from twilio.twiml.messaging_response import MessagingResponse
from .services import salvar_arquivo, extrair_texto_azure
import json

webhook_bp = Blueprint("webhook", __name__)

# Simples armazenamento em memória para controle de conversa
conversas_em_andaamento = {}


@webhook_bp.route("/webhook-whatsapp", methods=["POST"])
def webhook_whatsapp():
    sender = request.form.get("From")
    body = (request.form.get("Body") or "").strip()
    media_url = request.form.get("MediaUrl0")

    response = MessagingResponse()
    message = response.message()

    # --------------------------------------------------------------------
    # SEÇÃO 1: Lógica para conversas já em andamento (pedindo quantidade)
    # --------------------------------------------------------------------
    if sender in conversas_em_andaamento:
        estado = conversas_em_andaamento[sender]
        json_receita = estado["json_receita"]
        med_nome = estado["aguardando_medicamento"]

        # Atualiza a quantidade informada pelo usuário
        for med in json_receita["medicamentos"]:
            if med["nome"] == med_nome:
                med["quantidade"] = body
                break

        # Verifica se há mais medicamentos sem quantidade
        proximo = next((m for m in json_receita["medicamentos"] if m["quantidade"] == "Não identificado"), None)

        if proximo:
            estado["aguardando_medicamento"] = proximo["nome"]
            message.body(
                f"⚠️ Não identificamos a quantidade para o medicamento: *{proximo['nome']}*. Por favor, informe a quantidade (ex: 30 comprimidos).")
        else:
            # Finaliza a conversa se não houver mais pendências
            message.body(
                f"✅ Receita finalizada:\n```json\n{json.dumps(json_receita, indent=2, ensure_ascii=False)}\n```")
            conversas_em_andaamento.pop(sender)

        return str(response)

    # --------------------------------------------------------------------
    # SEÇÃO 2: Lógica para novas mensagens
    # --------------------------------------------------------------------

    # Se for uma mensagem de texto sem imagem
    if not media_url:
        if any(word in body.lower() for word in ["oi", "olá", "receita"]):
            message.body("👋 Olá! Por favor, envie uma *foto da receita médica*.")
        else:
            message.body("Envie *Oi* ou *Receita* para começar.")
        return str(response)

    # Se for uma mensagem com imagem/PDF, inicia o processamento
    file_path = salvar_arquivo(media_url, sender)
    if not file_path:
        message.body("❌ Desculpe, tive um problema ao salvar seu arquivo. Tente novamente.")
        return str(response)

    texto_receita_json_str = extrair_texto_azure(file_path)
    dados_json = json.loads(texto_receita_json_str)
    # --- PONTO CRÍTICO DA CORREÇÃO ---
    # ✅ 1. VERIFICA SE A EXTRAÇÃO RETORNOU UM ERRO
    if "erro" in dados_json:
        # Envia uma mensagem amigável para o usuário e o erro técnico para debug
        error_message = dados_json['erro']
        print(f"ERRO TÉCNICO NA EXTRAÇÃO: {error_message}")
        message.body(
            "Desculpe, não consegui ler as informações da sua receita. Por favor, tente enviar uma foto mais nítida e bem iluminada.")
    else:
        # ✅ 2. SE NÃO HOUVE ERRO, PROSSEGUE COM A LÓGICA NORMAL
        medicamentos = dados_json.get("medicamentos", [])
        med_incompleto = next((m for m in medicamentos if m.get("quantidade") == "Não identificado"), None)
        if med_incompleto:
            # Inicia o fluxo de conversa para pedir a quantidade
            conversas_em_andaamento[sender] = {
                "json_receita": dados_json,
                "aguardando_medicamento": med_incompleto["nome"]
            }
            message.body(
                f"⚠️ Não identificamos a quantidade para o medicamento: *{med_incompleto['nome']}*. Por favor, informe a quantidade (ex: 30 ).")
        else:
            # Se tudo estiver completo, envia o resultado final
            message.body(
                f"✅ Receita recebida com sucesso:\n```json\n{json.dumps(dados_json, indent=2, ensure_ascii=False)}\n```")
    return str(response)