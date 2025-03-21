import uvicorn
from darelabdb.api_faircore_similarity_based_recs.config_reader import app_config
from darelabdb.api_faircore_similarity_based_recs.routes.add_routes import (
    initialize_routes,
)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    openapi_url=app_config["FASTAPI"]["BASE_URL"] + "/openapi.json",
    docs_url=app_config["FASTAPI"]["BASE_URL"] + "/docs",
    redoc_url=app_config["FASTAPI"]["BASE_URL"] + "/redoc",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


initialize_routes(app)


@app.get(f"{app_config['FASTAPI']['BASE_URL']}/health/")
def health_check():
    return {"message": "App has initialised and is healthy."}


def main():
    uvicorn.run(
        "darelabdb.api_faircore_similarity_based_recs.main:app",
        host=app_config["FASTAPI"]["HOST"],
        port=app_config["FASTAPI"]["PORT"],
        reload=app_config["FASTAPI"]["DEBUG"],
        workers=app_config["FASTAPI"]["WORKERS"],
        reload_dirs=["bases/darelabdb/api_faircore_similarity_based_recs/"],
    )


if __name__ == "__main__":
    main()
