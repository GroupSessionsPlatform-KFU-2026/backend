from src.app import gunicorn_config

EXPECTED_WORKERS = 4
EXPECTED_TIMEOUT = 120


def test_gunicorn_config_matches_container_defaults():
    assert gunicorn_config.bind == '0.0.0.0:8000'
    assert gunicorn_config.workers == EXPECTED_WORKERS
    assert gunicorn_config.worker_class == 'uvicorn.workers.UvicornWorker'
    assert gunicorn_config.timeout == EXPECTED_TIMEOUT
    assert gunicorn_config.loglevel == 'info'
    assert gunicorn_config.accesslog == '-'
    assert gunicorn_config.errorlog == '-'
