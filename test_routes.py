from campaign_engine.webapp import create_app
 
app = create_app()
client = app.test_client()

routes = [
    "/",
    "/budget",
    "/youtube",
    "/database",
    "/posts",
    "/comments",
    "/content",
    "/audience",
    "/anomalies",
    "/segments",
    "/recommendations"
]

all_ok = True
for r in routes:
    res = client.get(r)
    status = res.status_code
    print(f"Route {r:20} -> Status: {status}")
    if status != 200:
        all_ok = False

if all_ok:
    print("\n✅ All routes returned HTTP 200 OK!")
else:
    print("\n❌ Some routes failed!")

