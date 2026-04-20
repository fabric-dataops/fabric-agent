from azure.identity import ClientSecretCredential, UsernamePasswordCredential
from app import App


def build_credential():
    config = App.config
    mode = config.AUTHENTICATION_MODE.lower()

    if mode == "serviceprincipal":
        return ClientSecretCredential(
            tenant_id=config.TENANT_ID,
            client_id=config.CLIENT_ID,
            client_secret=config.CLIENT_SECRET,
        )
    if mode == "masteruser":
        return UsernamePasswordCredential(
            client_id=config.CLIENT_ID,
            username=config.POWER_BI_USER,
            password=config.POWER_BI_PASS,
            tenant_id=config.TENANT_ID,
        )
    raise ValueError(f"Unsupported AUTHENTICATION_MODE: {config.AUTHENTICATION_MODE}")
