import os
from app import app

PORT = int(os.environ.get('PORT', 5000))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=False)
