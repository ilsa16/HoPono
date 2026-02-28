import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

from app import create_app

app = create_app()

if __name__ == "__main__":
    is_dev = os.environ.get("FLASK_ENV", "development") != "production"
    app.run(host="0.0.0.0", port=5000, debug=is_dev)
