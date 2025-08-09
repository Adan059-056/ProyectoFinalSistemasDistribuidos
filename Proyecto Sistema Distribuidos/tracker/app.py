from flask import Flask, jsonify, request
from flasgger import Swagger

app = Flask(__name__)
Swagger(app)

nodes = {}

@app.route('/register', methods=['POST'])
def register_node():
    """Registra un nuevo nodo
    ---
    parameters:
      - name: ip
        in: formData
        type: string
      - name: puerto
        in: formData
        type: integer
    responses:
      200:
        description: ID del nodo registrado
    """
    node_id = len(nodes) + 1
    nodes[node_id] = {
        'ip': request.form['ip'],
        'port': int(request.form['port']),
        'fragments': []
    }
    return jsonify({'node_id': node_id})

@app.route('/update-fragments', methods=['POST'])
def update_fragments():
    """Actualiza fragmentos de un nodo
    ---
    parameters:
      - name: id_nodo
        in: formData
        type: integer
      - name: fragmentos
        in: formData
        type: string
    """
    node_id = int(request.form['node_id'])
    fragments = request.form['fragments'].split(',')
    nodes[node_id]['fragments'] = [int(f) for f in fragments if f]
    return jsonify({'status': 'updated'})

@app.route('/get-nodes', methods=['GET'])
def get_nodes():
    """Obtiene todos los nodos registrados
    ---
    responses:
      200:
        description: Lista de nodos
    """
    return jsonify(nodes)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)