# C:\CapStone\Identity_service\src\api\main.py
def main() -> None:
    import uvicorn

    uvicorn.run("src.api.rest.app:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
