import socket
import threading
import requests
import os
import time
import shutil
from flask import Flask, request, jsonify

# Configuración
TRACKER_URL = "http://tracker:5000"
NODE_IP = os.getenv('NODE_IP', 'localhost')
NODE_PORT = int(os.getenv('NODE_PORT', 6000))
FRAGMENTS_DIR = "fragments"

app = Flask(__name__)
node_id = None
fragments = []

def register_with_tracker():
    global node_id
    try:
        print(f"[Tracker] Registrando nodo en {TRACKER_URL}...")
        response = requests.post(
            f"{TRACKER_URL}/register",
            data={'ip': NODE_IP, 'port': NODE_PORT}
        )
        node_id = response.json()['node_id']
        print(f"[Tracker] Registrado como Nodo {node_id}")
    except Exception as e:
        print(f"[Tracker] Error registrando nodo: {e}")

def update_tracker_fragments():
    try:
        print(f"[Tracker] Actualizando fragmentos: {fragments}")
        requests.post(
            f"{TRACKER_URL}/update-fragments",
            data={
                'node_id': node_id,
                'fragments': ','.join(map(str, fragments))
            }
        )
        print(f"[Tracker] Fragmentos actualizados")
    except Exception as e:
        print(f"[Tracker] Error actualizando fragmentos: {e}")

def download_fragment(owner, fragment_id):
    print(f"[P2P] Solicitando fragmento {fragment_id} a {owner['ip']}:{owner['port']}")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((owner['ip'], owner['port'] + 1000))
            print(f"[P2P] Conexión establecida con {owner['ip']}")
            
            s.sendall(f"GET {fragment_id}".encode())
            print(f"[P2P] Enviada solicitud para fragmento {fragment_id}")

            data = b""
            while True:
                chunk = s.recv(4096)
                if not chunk: 
                    break
                data += chunk
            
            if data.startswith(b"FRAGMENT:"):
                file_path = f"{FRAGMENTS_DIR}/fragment_{fragment_id}.mp4"
                with open(file_path, 'wb') as f:
                    f.write(data[9:])
                
                fragments.append(fragment_id)
                update_tracker_fragments()
                print(f"[P2P] Fragmento {fragment_id} DESCARGADO y guardado! Tamaño: {len(data)} bytes")
            else:
                print(f"[P2P] Error recibido: {data.decode()}")
    except Exception as e:
        print(f"[P2P] ERROR descargando fragmento {fragment_id}: {e}")

def handle_client(conn):
    try:
        addr = conn.getpeername()
        data = conn.recv(1024).decode()
        
        if data.startswith("GET "):
            fragment_id = int(data.split()[1])
            fragment_path = f"{FRAGMENTS_DIR}/fragment_{fragment_id}.mp4"

            print(f"[P2P] Solicitud de fragmento {fragment_id} desde {addr}")

            if os.path.exists(fragment_path):
                print(f"[P2P] Enviando fragmento {fragment_id} a {addr}")
                with open(fragment_path, 'rb') as f:
                    fragment_data = f.read()
                conn.sendall(b"FRAGMENT:" + fragment_data)
                print(f"[P2P] Fragmento {fragment_id} enviado! Tamaño: {len(fragment_data)} bytes")
            else:
                conn.sendall(b"ERROR: Fragment not found")
                print(f"[P2P] Fragmento {fragment_id} solicitado pero no encontrado")
    finally:
        conn.close()

def start_data_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((NODE_IP, NODE_PORT + 1000))
    server.listen(5)
    print(f"[P2P] Servidor de datos escuchando en {NODE_IP}:{NODE_PORT+1000}")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn,)).start()

@app.route('/request-fragment', methods=['POST'])
def request_fragment():
    fragment_id = int(request.form['fragment_id'])
    print(f"[API] Solicitud recibida para fragmento {fragment_id}")

    try:
        nodes_resp = requests.get(f"{TRACKER_URL}/get-nodes").json()
        print(f"[Tracker] Consultando nodos disponibles...")

        for nid, info in nodes_resp.items():
            if int(nid) != node_id and fragment_id in info['fragments']:
                print(f"[Tracker] Nodo {nid} tiene el fragmento {fragment_id}")
                print(f"[API] Iniciando descarga desde nodo {nid}")

                threading.Thread(
                    target=download_fragment,
                    args=(info, fragment_id)
                ).start()
                
                return jsonify({
                    'status': 'downloading',
                    'message': f"Descargando fragmento {fragment_id} desde nodo {nid}"
                })
        
        return jsonify({'error': 'Fragment not available'}), 404
    except Exception as e:
        print(f"[API] Error: {e}")
        return jsonify({'error': str(e)}), 500

def load_initial_fragments():
    global fragments
    if not os.path.exists(FRAGMENTS_DIR):
        os.makedirs(FRAGMENTS_DIR)
    
    # Determinar tipo de nodo por puerto
    node_type = "Nodo1" if NODE_PORT == 6000 else "Nodo2"
    fragments_range = range(1, 6) if node_type == "Nodo1" else range(6, 11)
    
    fragments = []
    for i in fragments_range:
        src = f"/shared/fragments/fragment_{i}.mp4"
        dst = f"{FRAGMENTS_DIR}/fragment_{i}.mp4"
        
        if os.path.exists(src):
            if not os.path.exists(dst):
                shutil.copy(src, dst)
                print(f"[INIT] Copiado fragmento {i} a {node_type}")
            fragments.append(i)

    print(f"[INIT] Fragmentos iniciales en {node_type}: {fragments}")
    return fragments

if __name__ == '__main__':
    print("\n" + "="*50)
    print(f"[P2P] INICIANDO NODO P2P | Puerto: {NODE_PORT}")
    print("="*50 + "\n")
    
    load_initial_fragments()
    register_with_tracker()
    update_tracker_fragments()
    
    threading.Thread(target=start_data_server, daemon=True).start()
    
    print("\n" + "="*50)
    print(f"[API] Servidor API iniciado en puerto {NODE_PORT}")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=NODE_PORT)