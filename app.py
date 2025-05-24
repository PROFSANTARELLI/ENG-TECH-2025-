import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import numpy_financial as npf
import json

# Inicializar Firebase usando secrets
if not firebase_admin._apps:
    try:
        firebase_config = st.secrets["FIREBASE_CONFIG"]
        firebase_config_dict = json.loads(firebase_config)
        cred = credentials.Certificate(firebase_config_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Erro ao inicializar o Firebase: {e}")
        st.stop()

# Conectar ao Firestore
db = firestore.client()

# Função para calcular a taxa efetiva mensal
def calcular_taxa_efetiva(valor_veiculo, entrada, parcelas, valor_parcela):
    fluxo = [- (valor_veiculo - entrada)] + [valor_parcela] * parcelas
    try:
        tir_mensal = npf.irr(fluxo)
        return round(tir_mensal * 100, 4) if tir_mensal else 0.0
    except Exception as e:
        st.error(f"Erro no cálculo: {e}")
        return 0.0

# Interface principal
def main():
    st.set_page_config(page_title="Calculadora de Financiamento", page_icon="🚗")
    st.title("🚗 Calculadora de Financiamento de Veículos")
    
    st.header("📋 Preencha os dados do financiamento")
    valor_veiculo = st.number_input("Valor do veículo (R$)", min_value=0.0, step=1000.0, format="%.2f")
    entrada = st.number_input("Valor da entrada (R$)", min_value=0.0, step=1000.0, format="%.2f")
    parcelas = st.number_input("Número de parcelas", min_value=1, step=1)
    valor_parcela = st.number_input("Valor da parcela (R$)", min_value=0.0, step=100.0, format="%.2f")

    if st.button("Calcular Taxa Efetiva"):
        if valor_veiculo <= 0:
            st.warning("⚠️ O valor do veículo deve ser maior que zero.")
        elif entrada >= valor_veiculo:
            st.warning("⚠️ A entrada não pode ser maior ou igual ao valor do veículo.")
        elif valor_parcela * parcelas <= (valor_veiculo - entrada):
            st.warning("⚠️ O total das parcelas deve ser maior que o valor financiado.")
        else:
            taxa = calcular_taxa_efetiva(valor_veiculo, entrada, parcelas, valor_parcela)
            st.success(f"💰 Taxa efetiva mensal estimada: *{taxa}%*")
            
            try:
                db.collection("financiamentos").add({
                    "valor_veiculo": valor_veiculo,
                    "entrada": entrada,
                    "parcelas": parcelas,
                    "valor_parcela": valor_parcela,
                    "taxa_calculada": taxa
                })
                st.info("✅ Dados salvos no Firebase!")
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

    st.markdown("---")
    st.subheader("📄 Histórico de cálculos")
    try:
        docs = db.collection("financiamentos").stream()
        for doc in docs:
            dados = doc.to_dict()
            st.write(f"""🔹 *Veículo:* R${dados['valor_veiculo']:.2f}  
                     | *Entrada:* R${dados['entrada']:.2f}  
                     | *Parcelas:* {dados['parcelas']}x R${dados['valor_parcela']:.2f}  
                     | *Taxa:* {dados['taxa_calculada']}%""")
    except Exception as e:
        st.warning(f"Erro ao carregar histórico: {e}")

if __name__ == "__main__":
    main()
