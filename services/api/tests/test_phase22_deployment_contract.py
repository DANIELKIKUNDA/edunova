from pathlib import Path


ROOT = Path(__file__).parents[3]


def test_deployment_runs_config_gate_before_build_and_migration():
    deploy = (ROOT / "scripts" / "deploy_production.sh").read_text()
    gate = deploy.index("run --rm config-gate")
    build = deploy.index("build --pull")
    migrate = deploy.index("run --rm migrate")
    start = deploy.index("up -d --remove-orphans")
    assert gate < build < migrate < start
    assert "/app/../scripts/migrate_production.sh" not in deploy


def test_api_is_bound_to_loopback_by_default_for_host_readiness():
    compose = (ROOT / "docker-compose.production.yml").read_text()
    assert '${EDUNOVA_API_BIND:-127.0.0.1}:8000:8000' in compose
    assert "run --rm config-gate" in (ROOT / "scripts" / "deploy_production.sh").read_text()


def test_migrations_run_from_postgres_client_with_read_only_mount():
    compose = (ROOT / "docker-compose.production.yml").read_text()
    assert "./services/api/migrations:/migrations:ro" in compose
    assert "--set=ON_ERROR_STOP=1" in compose


def test_api_image_explicitly_installs_security_updated_zlib():
    dockerfile = (ROOT / "services" / "api" / "Dockerfile").read_text()
    assert "apt-get update" in dockerfile
    assert "zlib1g" in dockerfile
