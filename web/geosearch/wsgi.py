import argparse

from datapunt_geosearch import create_app

app = create_app("datapunt_geosearch.config")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument("--reload", dest="reload", action="store_true")
    args = parser.parse_args()
    app.run(debug=args.reload)
