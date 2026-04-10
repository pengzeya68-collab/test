import sys
import os

PROJECT_ROOT = r'c:\Users\lenovo\Desktop\TestMasterProject'
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

# Set environment variables from .env (but NOT DATABASE_URL which uses relative path)
with open(os.path.join(PROJECT_ROOT, '.env'), 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"\'')
            # Don't override DATABASE_URL - let app.py handle it with its absolute path logic
            if key != 'DATABASE_URL':
                os.environ[key] = value

print("Environment loaded", flush=True)
print(f"SECRET_KEY: {os.environ.get('SECRET_KEY', 'NOT SET')[:10]}...", flush=True)

try:
    from backend.app import create_app
    print("Import successful", flush=True)
    app = create_app()
    print("App created", flush=True)
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
except Exception as e:
    print(f"ERROR: {e}", flush=True)
    import traceback
    traceback.print_exc()
