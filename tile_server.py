from flask import Flask, send_file, abort
import requests, os, time

app = Flask(__name__)

WORK_DIR = os.path.dirname(__file__)
CACHE_DIR = os.path.join(WORK_DIR, "data/tile_cache")
TILE_URL = "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"

HEADERS = {
    "User-Agent": "Valencia-Local-Dashboard/1.0"
}

@app.route("/tiles/<int:z>/<int:x>/<int:y>.png")
def tiles(z, x, y):
    tile_path = f"{CACHE_DIR}/{z}/{x}/{y}.png"
    # Crea el directorio si no existe
    os.makedirs(os.path.dirname(tile_path), exist_ok=True)

    # Si el tile no existe en la caché
    if not os.path.exists(tile_path):
        try:
            # Obtiene el tile del servidor
            r = requests.get(
                TILE_URL.format(z=z, x=x, y=y),
                headers=HEADERS,
                timeout=10
            )
            # Si el código de estado no es 200, aborta
            if r.status_code != 200:
                abort(404)
            
            # Guarda el tile en la caché
            with open(tile_path, "wb") as f:
                f.write(r.content)
            
            # Delay para no saturar el servidor
            time.sleep(0.05)
        
        except Exception:
            # Si hay un error, aborta
            abort(500)
    
    return send_file(tile_path, mimetype="image/png")

def arrancar_proxy_tiles():
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )

if __name__ == "__main__":
    arrancar_proxy_tiles()
