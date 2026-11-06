from starlette.middleware.base import BaseHTTPMiddleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response=await call_next(request)
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['X-Frame-Options']='DENY'
        response.headers['Referrer-Policy']='no-referrer'
        response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=(self)'
        response.headers['Cross-Origin-Resource-Policy']='same-site'
        response.headers['Content-Security-Policy']="default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        if request.url.scheme=='https': response.headers['Strict-Transport-Security']='max-age=31536000; includeSubDomains'
        response.headers['Cache-Control']='no-store' if request.url.path.startswith('/v1/identity') or request.url.path.startswith('/v1/trust') else response.headers.get('Cache-Control','')
        return response
