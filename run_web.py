"""Standalone launcher for the TitanSafe officer web interface."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from TitanSafe.app import app

print("\033[96m>> TitanSafe Officer Interface\033[0m")
print("\033[92m>> http://localhost:5000\033[0m\n")
app.run(host="0.0.0.0", port=5000, debug=False, threaded=True, use_reloader=False)
