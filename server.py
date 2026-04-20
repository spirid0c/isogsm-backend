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
        # On ignore le PWAT global (49) et on vise les traceurs inconnus
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
