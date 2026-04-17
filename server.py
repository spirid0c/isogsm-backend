import os
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
import cfgrib

app = Flask(__name__)
CORS(app)  # Autorise le frontend Vercel à contacter cette API externe

@app.route('/decode', methods=['POST'])
def decode_grib():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded under key 'file'"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Uploaded file is empty"}), 400
        
    # Sauvegarde du fichier uploadé de façon temporaire
    temp_path = ""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".grib", dir="/tmp") as tf:
            file.save(tf.name)
            temp_path = tf.name
            
        # Ouverture avec cfgrib
        datasets = cfgrib.open_datasets(temp_path)
        
        # Extraction des valeurs pwat
        pwat_data = None
        for ds in datasets:
            # Chercher dans ds.data_vars
            pwat_keys = [v for v in ds.data_vars if 'pwat' in v.lower()]
            if pwat_keys:
                # Utiliser la première variable trouvée qui matche 'pwat'
                pwat_data = ds[pwat_keys[0]].values.flatten().tolist()
                break
                
        if pwat_data is None:
            return jsonify({"error": "Variable 'pwat' not found in GRIB file"}), 400
            
        return jsonify({"data": pwat_data}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to extract with cfgrib: {str(e)}"}), 500
        
    finally:
        # Nettoyage
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
