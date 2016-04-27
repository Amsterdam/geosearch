import os


DSN_ATLAS = 'postgresql://{}:{}@{}:{}/{}'.format(
    os.getenv('ATLAS_DB_USER', 'postgres'),
    os.getenv('ATLAS_DB_PASSWORD', 'insecure'),
    os.getenv('ATLAS_DB_HOST', 'localhost'),
    os.getenv('ATLAS_DB_PORT', 5434),
    os.getenv('ATLAS_DB_NAME', 'atlas'),
)

DSN_NAP = 'postgresql://{}:{}@{}:{}/{}'.format(
    os.getenv('NAP_DB_NAME', 'postgres'),
    os.getenv('NAP_DB_PASSWORD', 'insecure'),
    os.getenv('NAP_DB_HOST', 'localhost'),
    os.getenv('NAP_DB_PORT', 5405),
    os.getenv('NAP_DB_NAME', 'postgres'),
)
