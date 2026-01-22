import sys
import importlib
print('Python', sys.executable)
for name in ('bcrypt','passlib'):
    try:
        mod = importlib.import_module(name)
        print('MODULE', name)
        print('  file:', getattr(mod,'__file__',None))
        print('  about:', getattr(mod,'__about__',None))
        print('  version:', getattr(mod,'__version__',None))
        print('  dir sample:', [a for a in dir(mod) if a.startswith('__') or a in ('__about__','__version__')])
    except Exception as e:
        print('MODULE', name, 'IMPORT ERROR:', e)

# Try passlib CryptContext
try:
    from passlib.context import CryptContext
    ctx = CryptContext(schemes=['bcrypt'], deprecated='auto')
    print('Passlib CryptContext created')
    try:
        h = ctx.hash('Reddy1234')
        print('Hash OK, len:', len(h))
        v = ctx.verify('Reddy1234', h)
        print('Verify OK:', v)
    except Exception as e:
        print('ERROR during hash/verify:', e)
except Exception as e:
    print('Passlib CryptContext error:', e)
