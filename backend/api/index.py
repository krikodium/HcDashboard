from server import app

# Vercel serverless function entry point
def handler(request):
    return app(request.environ, request.start_response)

# For ASGI compatibility
application = app