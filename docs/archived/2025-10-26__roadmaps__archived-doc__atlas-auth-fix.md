"""
ATLAS AUTHENTICATION FIX
========================

Problem:
--------
Atlas page was showing "Autenticación requerida" message even though Atlas data
should be publicly accessible. Only Player/Media access should require authentication.

Root Cause:
-----------
1. Frontend atlas/index.js line 167 was showing login prompt whenever user was not authenticated
2. Frontend loadFiles() catch block (lines 318-321) showed login prompt for ANY error, not just 401

Solution:
---------
1. Removed login prompt from renderCityTables() - Atlas data is public
2. Updated loadFiles() catch block to show generic error instead of login prompt
3. Kept login check in attachPlayerHandlers() - clicking player links still requires auth

Changes Made:
-------------
File: static/js/modules/atlas/index.js

1. Line ~167 (renderCityTables):
   BEFORE: const loginNotice = !isAuthenticated ? renderLoginPrompt() : '';
   AFTER:  // Atlas data is public - no login prompt needed here

2. Line ~320 (loadFiles catch block):
   BEFORE: filesContainer.innerHTML = renderLoginPrompt();
   AFTER:  filesContainer.innerHTML = '<div class="alert alert-warning">Error cargando archivos...</div>';

3. Line ~153-156 (attachPlayerHandlers):
   UNCHANGED: if (!isAuthenticated) { openLoginSheet(); return; }
   This is correct - player access still requires authentication

Backend Verification:
---------------------
✅ /api/v1/atlas/overview - Public (200 OK)
✅ /api/v1/atlas/countries - Public (200 OK)
✅ /api/v1/atlas/files - Public (200 OK)
✅ /player - Protected (302 Redirect to login)

Test Results:
-------------
All backend routes correctly configured:
- Atlas API endpoints return 200 without authentication
- Player route redirects to login (302) without authentication

Expected Behavior After Fix:
-----------------------------
1. Atlas page loads WITHOUT showing "Autenticación requerida"
2. Atlas overview, country list, and file metadata visible to all users
3. When clicking on a player link WITHOUT being logged in:
   - Login sheet opens
   - After login, user is redirected to intended player URL
4. When clicking on a player link WHILE logged in:
   - Directly opens player with transcription and audio

Testing Instructions:
---------------------
1. Logout from application
2. Navigate to /atlas page
3. Verify: Overview metrics and file list are visible (no auth prompt)
4. Click on any player link
5. Verify: Login sheet opens
6. Login with valid credentials
7. Verify: Redirected to player with correct transcription/audio
"""
