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
    action = request.form.get('action', 'decode') # 'scan' ou 'decode'
    temp_path = "/tmp/temp_data.grib"
    file.save(temp_path)
    
    try:
        f = open(temp_path, 'rb')
        
        # --- ACTION : SCAN ---
        # On lit juste les métadonnées pour créer le menu
        if action == 'scan':
            variables = []
            while True:
                gid = eccodes.codes_grib_new_from_file(f)
                if gid is None: break
                
                try:
                    param_id = eccodes.codes_get_long(gid, 'indicatorOfParameter')
                    short_name = eccodes.codes_get_string(gid, 'shortName')
                    name = eccodes.codes_get_string(gid, 'name')
                    level = eccodes.codes_get_long(gid, 'level')
                    
                    # On évite les doublons (si le fichier a plusieurs time steps)
                    var_info = {"id": param_id, "shortName": short_name, "name": name, "level": level}
                    if var_info not in variables:
                        variables.append(var_info)
                        
                except Exception:
                    pass
                eccodes.codes_release(gid)
                
            f.close()
            return jsonify({"variables": variables})
            
        # --- ACTION : DECODE ---
        # On extrait les données 3D pour un paramètre précis
        elif action == 'decode':
            data_array = None
            TARGET_PARAM_ID = int(request.form.get('param_id', 150))
            
            while True:
                gid = eccodes.codes_grib_new_from_file(f)
                if gid is None: break
                
                try:
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
                raise ValueError(f"ID {TARGET_PARAM_ID} introuvable.")
                
            return jsonify({"data": data_array})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
