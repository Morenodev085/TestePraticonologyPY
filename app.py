import os 
import psycopg2
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv


app = Flask(__name__)
CORS(app)
# Config de variáveis de ambiente

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn
#Fim de configurações

def inicializador_banco():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS historico_cashback (
                id SERIAL PRIMARY KEY,
                ip_usuario VARCHAR(50),
                tipo_cliente BOOLEAN,
                valor_compra DECIMAL(10, 2),
                valor_chashback DECIMAL(10, 2),
                data_consulta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("Banco de dados verificado/criado com sucesso!")
    except Exception as e:
        print(f"Erro ao inicializar o banco: {e}")

        inicializador_banco()

@app.route('/api/cashback', methods=['POST'])
def calcular():
    dados = request.json
    valor_bruto = float(dados.get('valor', 0))
    cupom_procentagem = float(dados.get('cupom', 0))
    is_vip = dados.get('vip', False)
    ip_usuario = request.remote_addr

    valor_com_desconto = valor_bruto * (1 - cupom_procentagem / 100)
    
    cashback = valor_com_desconto * 0.05

    if is_vip:
        cashback += (cashback * 0.10) 

    if valor_com_desconto > 500: 
        cashback *= 2

    try: 
        conn = get_db_connection()
        cur = conn.cursor()
        query = """
            INSERT INTO historico_cashback (ip_usuario, tipo_cliente, valor_compra, valor_chashback)
            VALUES (%s, %s, %s, %s)
        """
        cur.execute(query, (ip_usuario, is_vip, valor_com_desconto, round(cashback, 2)))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro ao salvar no banco: {e}")

    return jsonify({
        "valorFinal": round(valor_com_desconto, 2),
        "cashback": round(cashback, 2)
    })

@app.route('/api/historico', methods=['GET'])
def ver_historico():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT ip_usuario, tipo_cliente, valor_compra, valor_chashback, data_consulta FROM historico_cashback ORDER BY data_consulta DESC LIMIT 10")
        rows = cur.fetchall()
        
        historico = []
        for row in rows:
            historico.append({
                "ip": row[0],
                "vip": row[1],
                "valor": float(row[2]),
                "cashback": float(row[3]),
                "data": row[4].strftime("%d/%m/%Y %H:%M")
            })
        
        cur.close()
        conn.close()
        return jsonify(historico)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)