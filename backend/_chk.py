from app.main import app
print("IMPORT OK, routes:", len(app.routes))
paths = sorted({getattr(r, "path", "") for r in app.routes})
for p in paths:
    print(p)
