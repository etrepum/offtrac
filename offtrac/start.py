import os
import sys

def main():
    from offtrac.wsgi import app
    app.run(debug=True)

if __name__ == '__main__':
    # Workaround for reloader config
    sys.path.insert(0, os.getcwd())
    main()
