import sys
c=open('dummy_app.py').read()
c=c.replace('"endpoint": request.url.path', '"endpoint": str(request.url)')
open('dummy_app.py', 'w').write(c)

