"""
demo_client.py
--------------
A standalone mock "External Application" to demonstrate the OAuth2 integration flow.
This runs on port 3000 and simulates a completely separate application using AuthZen.

Run it with:
python demo_client.py
"""

import json
import urllib.request
import urllib.parse
from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
import uvicorn

app = FastAPI(title="Demo External App")

# ── Configuration ──────────────────────────────────────────────
# In a real app, these would come from .env
AUTHZEN_URL = "http://127.0.0.1:8000"
CLIENT_APP_ID = 1      # REPLACE with an actual App ID from AuthZen Dashboard
CLIENT_API_KEY = ""    # REPLACE with the actual API Key from AuthZen Dashboard
REDIRECT_URI = "http://localhost:3000/callback"

# ── HTML Templates (Inline for simplicity) ─────────────────────
HTML_BASE = """
<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
  <title>Demo External App</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
</head>
<body class="bg-dark text-light">
  <div class="container py-5" style="max-width:600px;">
    {content}
  </div>
</body>
</html>
"""

# ── Routes ─────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Landing Page of the External App"""
    token = request.cookies.get("demo_token")
    if token:
        return RedirectResponse("/dashboard")
        
    content = f"""
    <div class="text-center">
      <h2>Welcome to DemoApp</h2>
      <p class="text-secondary mb-4">This is a completely separate application integrating with AuthZen.</p>
      
      <div class="card bg-dark border-secondary p-4 text-start mb-4">
        <form method="POST" action="/setup">
          <label class="form-label text-warning"><i class="bi bi-gear-fill me-2"></i>Configure Integration</label>
          <input type="text" name="app_id" class="form-control mb-2" placeholder="App ID (e.g. 1)" value="{CLIENT_APP_ID}" required>
          <input type="text" name="api_key" class="form-control mb-3" placeholder="API Key (iam_...)" value="{CLIENT_API_KEY}" required>
          <button type="submit" class="btn btn-sm btn-outline-warning w-100">Save Configuration</button>
        </form>
      </div>

      <a href="/login" class="btn btn-primary btn-lg w-100 fw-bold">
        <i class="bi bi-shield-lock-fill me-2"></i> Login with AuthZen
      </a>
    </div>
    """
    return HTML_BASE.format(content=content)

@app.post("/setup")
def setup(app_id: int = Form(...), api_key: str = Form(...)):
    """Quick hack to set credentials without restarting the script."""
    global CLIENT_APP_ID, CLIENT_API_KEY
    CLIENT_APP_ID = app_id
    CLIENT_API_KEY = api_key
    return RedirectResponse("/", status_code=302)

@app.get("/login")
def login():
    """Step 1: Redirect user to AuthZen for authorization."""
    if not CLIENT_API_KEY:
        return HTMLResponse(HTML_BASE.format(content="<h3 class='text-danger'>Please configure API Key first!</h3><a href='/' class='btn btn-secondary mt-3'>Go Back</a>"))
        
    state = "random_xyz_state"
    auth_url = f"{AUTHZEN_URL}/authorize?app_id={CLIENT_APP_ID}&redirect_uri={REDIRECT_URI}&state={state}"
    return RedirectResponse(auth_url)

@app.get("/callback")
def callback(code: str, state: str = None):
    """Step 2: Receive Auth Code from AuthZen redirect, and securely exchange it for a JWT token."""
    
    # 1. Prepare secure POST request to AuthZen's /token endpoint
    payload = json.dumps({
        "code": code,
        "app_id": CLIENT_APP_ID,
        "redirect_uri": REDIRECT_URI,
        "api_key": CLIENT_API_KEY
    }).encode("utf-8")
    
    req = urllib.request.Request(
        f"{AUTHZEN_URL}/token",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    
    try:
        # 2. Exchange code for JWT
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            access_token = data.get("access_token")
            
            # 3. Store the JWT securely in a cookie for this external app
            res = RedirectResponse("/dashboard", status_code=302)
            res.set_cookie("demo_token", access_token, httponly=True)
            return res
            
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode()
        return HTMLResponse(HTML_BASE.format(content=f"<h3 class='text-danger'>Token Exchange Failed</h3><pre>{error_msg}</pre><a href='/' class='btn btn-outline-secondary mt-3'>Start Over</a>"))


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    """Step 3: Authenticated Dashboard. Uses AuthZen IAM endpoints to verify identity and permissions."""
    token = request.cookies.get("demo_token")
    if not token:
        return RedirectResponse("/")
        
    try:
        # Validate Token via AuthZen IAM
        val_req = urllib.request.Request(
            f"{AUTHZEN_URL}/auth/validate-token",
            data=json.dumps({"token": token}).encode(),
            headers={"Content-Type": "application/json", "x-api-key": CLIENT_API_KEY}
        )
        with urllib.request.urlopen(val_req) as response:
            user_data = json.loads(response.read().decode())
            
        # Check specific permission via AuthZen IAM for this specific app context
        perm_req = urllib.request.Request(
            f"{AUTHZEN_URL}/auth/check-permission",
            data=json.dumps({
                "token": token, 
                "permission": "read", 
                "app_id": CLIENT_APP_ID
            }).encode(),
            headers={"Content-Type": "application/json", "x-api-key": CLIENT_API_KEY}
        )
        with urllib.request.urlopen(perm_req) as response:
            perm_data = json.loads(response.read().decode())
            
    except urllib.error.HTTPError as e:
        res = RedirectResponse("/")
        res.delete_cookie("demo_token")
        return res

    content = f"""
    <div class="card bg-dark border-secondary">
      <div class="card-header border-secondary d-flex justify-content-between align-items-center">
        <h5 class="mb-0">DemoApp Dashboard</h5>
        <a href="/logout" class="btn btn-sm btn-outline-danger">Logout</a>
      </div>
      <div class="card-body">
        <h6 class="text-success"><i class="bi bi-check-circle-fill me-2"></i>Successfully Authenticated via AuthZen!</h6>
        
        <div class="mt-4">
          <label class="text-secondary" style="font-size:0.8rem;">IAM User Profile</label>
          <pre class="bg-black text-info p-3 rounded" style="font-size:0.85rem;">{json.dumps(user_data['user'], indent=2)}</pre>
        </div>
        
        <div class="mt-3">
          <label class="text-secondary" style="font-size:0.8rem;">IAM Contextual Permission Check</label>
          <div class="p-2 rounded mb-2 {'bg-success bg-opacity-10 text-success' if perm_data['has_permission'] else 'bg-danger bg-opacity-10 text-danger'}">
            <i class="bi bi-shield-lock-fill me-2"></i>Has 'read' permission for App ID {CLIENT_APP_ID}: <strong>{perm_data['has_permission']}</strong>
          </div>
        </div>

        <hr class="border-secondary my-4">
        
        <h6 class="mb-3">Protected Action Test</h6>
        <p class="text-secondary" style="font-size:0.85rem;">This action requires the <strong>'write'</strong> permission scoped specifically to this App ID.</p>
        <form method="POST" action="/perform-action">
          <button type="submit" class="btn btn-warning"><i class="bi bi-pencil-square me-2"></i>Execute Write Action</button>
        </form>
        
      </div>
    </div>
    """
    return HTML_BASE.format(content=content)

@app.post("/perform-action", response_class=HTMLResponse)
def perform_protected_action(request: Request):
    """Step 4: Strict RBAC Enforcement. External app calls IAM BEFORE allowing action."""
    token = request.cookies.get("demo_token")
    if not token:
        return RedirectResponse("/")

    # CALL IAM TO VERIFY IF USER HAS 'write' PERMISSION IN THIS APP'S CONTEXT
    try:
        perm_req = urllib.request.Request(
            f"{AUTHZEN_URL}/auth/check-permission",
            data=json.dumps({
                "token": token, 
                "permission": "write", 
                "app_id": CLIENT_APP_ID
            }).encode(),
            headers={"Content-Type": "application/json", "x-api-key": CLIENT_API_KEY}
        )
        with urllib.request.urlopen(perm_req) as response:
            perm_data = json.loads(response.read().decode())
            
        if not perm_data.get("has_permission"):
            # Action Blocked!
            content = f"""
            <div class="text-center mt-5">
              <h1 class="text-danger"><i class="bi bi-shield-slash-fill"></i></h1>
              <h3 class="text-light">Access Denied</h3>
              <p class="text-secondary">AuthZen IAM denied your request. You lack the 'write' permission for App ID {CLIENT_APP_ID}.</p>
              <a href="/dashboard" class="btn btn-outline-secondary mt-3">Back to Dashboard</a>
            </div>
            """
            return HTML_BASE.format(content=content)
            
        # Action Allowed!
        content = f"""
        <div class="text-center mt-5">
          <h1 class="text-success"><i class="bi bi-check-circle-fill"></i></h1>
          <h3 class="text-light">Action Successful!</h3>
          <p class="text-secondary">AuthZen IAM verified your 'write' permission for App ID {CLIENT_APP_ID}. The action was performed.</p>
          <a href="/dashboard" class="btn btn-outline-secondary mt-3">Back to Dashboard</a>
        </div>
        """
        return HTML_BASE.format(content=content)
        
    except urllib.error.HTTPError as e:
        return HTMLResponse(HTML_BASE.format(content=f"<h3 class='text-danger'>AuthZen IAM Error</h3><pre>{e.read().decode()}</pre>"))

@app.get("/logout")
def logout():
    res = RedirectResponse("/")
    res.delete_cookie("demo_token")
    return res

if __name__ == "__main__":
    print("🚀 Starting Demo External App on http://localhost:3000")
    uvicorn.run(app, host="127.0.0.1", port=3000)
