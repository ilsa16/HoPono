import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app

app = create_app()

if __name__ == "__main__":
    is_dev = os.environ.get("FLASK_ENV", "development") != "production"
    app.run(host="0.0.0.0", port=5000, debug=is_dev)
