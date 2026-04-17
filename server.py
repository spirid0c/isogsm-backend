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
        f = open(temp_path, 'rb')
        data_array = None
        
        # 1. On parcourt les messages GRIB pour chercher la vapeur d'eau par son nom
        while True:
            gid = eccodes.codes_grib_new_from_file(f)
            if gid is None:
                break  # Fin du fichier
            
            try:
                short_name = eccodes.codes_get_string(gid, 'shortName')
            except Exception:
                short_name = ""
                
            # 'pwat', 'tcwv' et 'prw' sont les noms GRIB standards pour Precipitable Water
            if short_name.lower() in ['pwat', 'tcwv', 'prw']:
                data_array = eccodes.codes_get_values(gid).tolist()
                eccodes.codes_release(gid)
                break
                
            eccodes.codes_release(gid)
            
        f.close()
        
        # 2. PLAN B : Si le nom n'est pas trouvé, on extrait le 38ème record
        if data_array is None:
            f = open(temp_path, 'rb')
            target_record = 38
            current = 1
            while True:
                gid = eccodes.codes_grib_new_from_file(f)
                if gid is None:
                    break
                    
                if current == target_record:
                    data_array = eccodes.codes_get_values(gid).tolist()
                    eccodes.codes_release(gid)
                    break
                    
                eccodes.codes_release(gid)
                current += 1
            f.close()

        if data_array is None:
            raise ValueError("Impossible de trouver les données de vapeur d'eau dans le fichier GRIB.")

        return jsonify({"data": data_array})
        
    except Exception as e:
        return jsonify({"error": f"Erreur interne ecCodes : {str(e)}"}), 500
        
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
