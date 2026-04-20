import pytest
from unittest.mock import patch, MagicMock
from azure.identity import ClientSecretCredential, UsernamePasswordCredential


def _make_config(mode, tenant="t1", client_id="c1", secret="s1", user="u1", pw="p1"):
    cfg = MagicMock()
    cfg.AUTHENTICATION_MODE = mode
    cfg.TENANT_ID = tenant
    cfg.CLIENT_ID = client_id
    cfg.CLIENT_SECRET = secret
    cfg.POWER_BI_USER = user
    cfg.POWER_BI_PASS = pw
    return cfg


def test_service_principal_returns_client_secret_credential():
    cfg = _make_config("ServicePrincipal")
    with patch("services.fabriccredential.App") as mock_app:
        mock_app.config = cfg
        from services.fabriccredential import build_credential
        cred = build_credential()
    assert isinstance(cred, ClientSecretCredential)


def test_master_user_returns_username_password_credential():
    cfg = _make_config("MasterUser")
    with patch("services.fabriccredential.App") as mock_app:
        mock_app.config = cfg
        from services.fabriccredential import build_credential
        cred = build_credential()
    assert isinstance(cred, UsernamePasswordCredential)


def test_unknown_mode_raises_value_error():
    cfg = _make_config("Unknown")
    with patch("services.fabriccredential.App") as mock_app:
        mock_app.config = cfg
        from services.fabriccredential import build_credential
        with pytest.raises(ValueError, match="Unsupported AUTHENTICATION_MODE"):
            build_credential()


def test_service_principal_case_insensitive():
    cfg = _make_config("serviceprincipal")
    with patch("services.fabriccredential.App") as mock_app:
        mock_app.config = cfg
        from services.fabriccredential import build_credential
        cred = build_credential()
    assert isinstance(cred, ClientSecretCredential)
