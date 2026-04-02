import json
from app.api.main import app

routes = []
for r in app.routes:
    if hasattr(r, 'methods'):
        routes.append({
            'path': r.path,
            'methods': list(r.methods)
        })

with open('routes.json', 'w') as f:
    json.dump(routes, f, indent=2)

# Also dump openapi.json for complete spec
with open('openapi.json', 'w') as f:
    json.dump(app.openapi(), f, indent=2)
