import os
import eccodes
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app) 

@app.route('/decode', methods=['POST'])
def decode_grib():
    if 'file' not in request.files:
        return jsonify({"error": "Aucun fichier reçu"}), 400
        
    file = request.files['file']
    temp_path = "/tmp/temp_data.grib"
    file.save(temp_path)
    
    try:
        data_array = None
        
        # --- LA CIBLE DYNAMIQUE ---
        # Le serveur écoute ce que le site JS demande (150 ou 151).
        # Si rien n'est précisé, il prend 150 (Japon) par défaut.
        TARGET_PARAM_ID = int(request.form.get('param_id', 150))
        
        f = open(temp_path, 'rb')
        while True:
            gid = eccodes.codes_grib_new_from_file(f)
            if gid is None: 
                break
            
            try:
                # On lit l'identifiant numérique officiel du GRIB1
                param_id = eccodes.codes_get_long(gid, 'indicatorOfParameter')
                
                if param_id == TARGET_PARAM_ID:
                    data_array = eccodes.codes_get_values(gid).tolist()
                    eccodes.codes_release(gid)
                    break
            except Exception:
                pass
                
            eccodes.codes_release(gid)
            
        f.close()

        if data_array is None:
            raise ValueError(f"La variable ID {TARGET_PARAM_ID} est introuvable dans ce fichier.")

        return jsonify({"data": data_array})
        
    except Exception as e:
        return jsonify({"error": f"Erreur interne : {str(e)}"}), 500
        
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)


