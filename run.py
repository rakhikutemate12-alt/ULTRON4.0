from backend import create_app

app = create_app()

if __name__ == "__main__":
    print("ULTRON AI 4.0 is starting...")
    print("Open http://127.0.0.1:5000 in your browser")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )