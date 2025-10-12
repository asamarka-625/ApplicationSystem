from web_app import app, write_data_in_db
import asyncio


if __name__ == "__main__":
    # asyncio.run(write_data_in_db())
    import uvicorn
    uvicorn.run(app, port=8000, reload=False)