from darelabdb.api_faircore_similarity_based_recs.routes import recommendations


def initialize_routes(app):
    app.include_router(recommendations.router)
