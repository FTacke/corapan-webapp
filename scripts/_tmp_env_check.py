import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from src.app import create_app
app = create_app('development')
print('ENV:', app.config.get('ENV'))
print('DEBUG:', app.config.get('DEBUG'))
print('FLASK_ENV var:', __import__('os').environ.get('FLASK_ENV'))
