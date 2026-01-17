import sys
import logging

# Set up debug logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s %(message)s')

print("Step 1: Importing src.app...", flush=True)
sys.stdout.flush()

try:
    from src.app import create_app
    print("Step 2: create_app imported", flush=True)
    sys.stdout.flush()
except Exception as e:
    print(f"ERROR at Step 2: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("Step 3: Creating Flask app...", flush=True)
sys.stdout.flush()

try:
    app = create_app('development')
    print("Step 4: App created", flush=True)
    sys.stdout.flush()
except Exception as e:
    print(f"ERROR at Step 4: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("Step 5: Creating test client...", flush=True)
sys.stdout.flush()

try:
    with app.test_client() as client:
        print("Step 6: Test client created, making request to /health...", flush=True)
        sys.stdout.flush()
        
        result = client.get('/health')
        
        print(f"Step 7: Got response status {result.status_code}", flush=True)
        print(f"Response body (first 500 chars): {result.get_data(as_text=True)[:500]}", flush=True)
        sys.stdout.flush()
except Exception as e:
    print(f"ERROR at test_client: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("SUCCESS: Test completed", flush=True)
