# jl_generators/views.py
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
import hmac, hashlib, os, subprocess

@csrf_exempt
def github_webhook(request):
    secret = os.environ.get("JL_GH_WEBHOOK_SECRET","")
    sig = request.headers.get("X-Hub-Signature-256","")
    if secret:
        expected = "sha256=" + hmac.new(secret.encode(), request.body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, sig):
            return HttpResponseForbidden("Bad signature")

    # Pull latest generators
    repo_dir = os.environ.get("JL_GEN_REPO_DIR", "/srv/judaicalink-generators")
    subprocess.run(f"git -C {repo_dir} pull --ff-only", shell=True, check=False)

    # Optional: kickoff run_all (idempotent, da Output nur überschreibt)
    subprocess.run("python manage.py jlgen run_all", shell=True, check=False)
    return HttpResponse("ok")
