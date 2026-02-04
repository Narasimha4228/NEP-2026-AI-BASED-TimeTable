import sys
sys.path.insert(0, '.')

if __name__ == '__main__':
    from uvicorn import run
    run("app.main:app", reload=False, host="0.0.0.0", port=8000)