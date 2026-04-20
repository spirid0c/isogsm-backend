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
        pwat_found = False
        
        print(f"\n--- ANALYSE DU FICHIER : {file.filename} ---")
        current = 1
        
        # 1. On scanne TOUT le fichier pour voir ce qu'il contient
        while True:
            gid = eccodes.codes_grib_new_from_file(f)
            if gid is None:
                break  # Fin du fichier
            
            try:
                # On récupère les infos de la variable
                short_name = eccodes.codes_get_string(gid, 'shortName')
                name = eccodes.codes_get_string(gid, 'name')
                level = eccodes.codes_get_long(gid, 'level')
                
                # On affiche la variable dans les logs de Render !
                print(f"Record {current} | shortName: '{short_name}' | name: '{name}' | level: {level}")
                
                # Si c'est un nom standard, on le garde
                if short_name.lower() in ['pwat', 'tcwv', 'prw'] and not pwat_found:
                    print(f"✅ PWAT STANDARD TROUVÉ AU RECORD {current} ! Extraction...")
                    data_array = eccodes.codes_get_values(gid).tolist()
                    pwat_found = True
                    
            except Exception as e:
                print(f"Record {current} | Méta-données illisibles.")
                
            eccodes.codes_release(gid)
            current += 1
            
        f.close()
        print("--- FIN DE L'ANALYSE ---\n")
        
        # 2. PLAN B : Si on n'a pas trouvé de nom standard
        if not pwat_found:
            TARGET_RECORD = 38 # <-- C'est lui qu'il faudra changer après avoir lu les logs !
            print(f"⚠️ Traceur introuvable par nom. Application du Plan B : Extraction du Record {TARGET_RECORD}...")
            
            f = open(temp_path, 'rb')
            current = 1
            while True:
                gid = eccodes.codes_grib_new_from_file(f)
                if gid is None: break
                if current == TARGET_RECORD:
                    data_array = eccodes.codes_get_values(gid).tolist()
                    eccodes.codes_release(gid)
                    break
                eccodes.codes_release(gid)
                current += 1
            f.close()

        if data_array is None:
            raise ValueError("Impossible d'extraire les données.")

        return jsonify({"data": data_array})
        
    except Exception as e:
        print(f"ERREUR CRITIQUE : {str(e)}")
        return jsonify({"error": f"Erreur interne : {str(e)}"}), 500
        
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
