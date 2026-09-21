from company_website import create_app

app = create_app()

if __name__ == "__main__":
    import os
    debug_mode = os.environ.get('FLASK_DEBUG', 'true').lower() not in ('0', 'false', 'no')
    app.run(debug=debug_mode, port=7000)
