from fastapi.responses import JSONResponse

def custom_exception(message):

    return JSONResponse(
        status_code=500,
        content={
            "error": message
        }
    )