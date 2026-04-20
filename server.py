import os
import eccodes
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- INITIALISATION DE L'APPLICATION ---
app = Flask(__name__)
CORS(app) 

# --- ROUTE DE DÉCODAGE ---
@app.route('/decode', methods=['POST'])
def decode_grib():
    if 'file' not in request.files:
        return jsonify({"error": "Aucun fichier reçu"}), 400
        
    file = request.files['file']
    temp_path = "/tmp/temp_data.grib"
    file.save(temp_path)
    
    try:
        data_array = None
        
        # --- CIBLE EXACTE ---
        # D'après les logs, le Record 49 est le PWAT global.
        # Les traceurs JP et BZ sont dans les "unknown" suivants (51 ou 52).
        TARGET_RECORD = 51 
        
        f = open(temp_path, 'rb')
        current = 1
        while True:
            gid = eccodes.codes_grib_new_from_file(f)
            if gid is None: 
                break
                
            if current == TARGET_RECORD:
                data_array = eccodes.codes_get_values(gid).tolist()
                eccodes.codes_release(gid)
                break
                
            eccodes.codes_release(gid)
            current += 1
        f.close()

        if data_array is None:
            raise ValueError(f"Record {TARGET_RECORD} introuvable.")

        return jsonify({"data": data_array})
        
    except Exception as e:
        return jsonify({"error": f"Erreur interne : {str(e)}"}), 500
        
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# --- LANCEMENT DU SERVEUR ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
