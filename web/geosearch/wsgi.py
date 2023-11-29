from datapunt_geosearch import create_app

app = create_app("datapunt_geosearch.config")


if __name__ == "__main__":
    app.run()
