"""
AquaCrop AI - Google Earth Engine (GEE) Authentication & Initialization
================================================================================
Prompts browser authorization, saves credentials to ~/.config/earthengine/credentials,
and initializes Earth Engine with your Google Cloud Project.
================================================================================
"""

import os
import sys
import ee

PROJECT_ID = os.getenv('GEE_PROJECT_ID', 'gen-lang-client-0784106715')

print("=" * 80)
print(" AQUACROP AI: INITIALIZING GOOGLE EARTH ENGINE AUTHENTICATION")
print("=" * 80)
print(f"Target Google Cloud Project: {PROJECT_ID}\n")
print("A browser window will open automatically asking you to log into Google and approve Earth Engine access.")
print("If the browser does not open automatically, copy and paste the authorization URL into your browser.\n")

try:
    # Trigger authentication flow
    ee.Authenticate(auth_mode='localhost')
    print("\n[SUCCESS] Authentication authorization received!")
except Exception as e:
    print(f"\n[Notice] Localhost auth mode note: {e}. Falling back to standard notebook mode...")
    try:
        ee.Authenticate(auth_mode='notebook')
    except Exception as e2:
        print(f"[ERROR] Could not authenticate: {e2}")
        sys.exit(1)

# Now attempt initialization
print(f"\nInitializing Earth Engine with project: {PROJECT_ID}...")
try:
    ee.Initialize(project=PROJECT_ID)
    print(f"\n==================================================================")
    print(f" [SUCCESS] Google Earth Engine is Fully Initialized & Authenticated!")
    print(f" Project: {PROJECT_ID}")
    print(f"==================================================================\n")
except Exception as init_err:
    print(f"\nNotice: Project '{PROJECT_ID}' could not be initialized directly: {init_err}")
    print("Trying default project initialization...")
    try:
        ee.Initialize()
        print("\n[SUCCESS] Google Earth Engine Initialized with Default User Project!\n")
    except Exception as init_err2:
        print(f"\n[ACTION REQUIRED] Please specify your Google Cloud Project ID with Earth Engine API enabled:")
        print(f"Error: {init_err2}")
