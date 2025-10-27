"""
Script para descobrir o PHONE_NUMBER_ID do WhatsApp Business (WABA)
Autor: Thiago Henrique dos Santos
"""

import os
import sys
import requests

# ======================================================
# CONFIGURAÇÕES (preencha seus dados aqui)
# ======================================================
WABA_ID = "721620457574899"  # Seu WABA ID
TOKEN = (
    "EAAY3hmiQ44IBPkuMf1upl9BEcYGFBB3lcyKl4ZBPzyhiNTxeglHlf3DwqZCn9xbc9vSMULe6wBJe3NmIGrC5eZC9dJNEPqEDIvUIbO6qZBs7ElZAqxYGKnzOOfJGfZAleRcZA6HpZAI9t6sk8gys6mf3fXhUVtZBAH3HZAYWmMy8xiN5NbxnjSEpKh4P2RIhAHbivFoG6XGEsiZAVrV3TN7si8r3OJZCVEUtvOYPWnFHQ7DSsxlPLAZDZD"
)
# ======================================================


def get_phone_numbers():
    """Consulta a API do Facebook e retorna os números vinculados à WABA"""
    url = f"https://graph.facebook.com/v18.0/{WABA_ID}/phone_numbers"
    headers = {"Authorization": f"Bearer {TOKEN}"}

    print("🔍 Consultando números vinculados à WABA...")
    try:
        response = requests.get(url, headers=headers, timeout=(5, 30))
        response.raise_for_status()
        data = response.json()

        if "data" not in data or not data["data"]:
            print("⚠️ Nenhum número encontrado. Verifique se o número está validado no WhatsApp Manager.")
            print(data)
            return

        print("✅ Resultado encontrado:\n")
        for item in data["data"]:
            print(f"📱 Número: {item.get('display_phone_number')}")
            print(f"🆔 PHONE_NUMBER_ID: {item.get('id')}")
            print(f"🔎 Status de verificação: {item.get('code_verification_status')}")
            print("-" * 60)

    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")
        sys.exit(1)


if __name__ == "__main__":
    get_phone_numbers()
