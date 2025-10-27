# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import msal
try:
    from flask import current_app
    flask_available = True
except ImportError:
    flask_available = False

from app import App
from utils import Utils


class AadService:

    def get_access_token():
        ''' Generates and returns Access token

        Returns:
            string: Access token
        '''
        
        # Try to use Flask app context first, fallback to App config
        try:
            if flask_available:
                app_config = current_app.config
                config_result = Utils.validate_config(current_app)
            else:
                raise RuntimeError("Flask not available")
        except (RuntimeError, Exception):
            # Running outside Flask context, use App config
            app_config = App.config
            config_result = Utils.validate_config(App.config)
        
        if config_result:
            raise Exception(config_result)

        # Handle different config types
        if hasattr(app_config, '__getitem__'):
            # Flask config dict
            authenticate_mode = app_config['AUTHENTICATION_MODE']
            tenant_id = app_config['TENANT_ID']
            client_id = app_config['CLIENT_ID']
            username = app_config['POWER_BI_USER']
            password = app_config['POWER_BI_PASS']
            client_secret = app_config['CLIENT_SECRET']
            scope = app_config['SCOPE_BASE']
            authority = app_config['AUTHORITY_URL']
        else:
            # BaseConfig class attributes
            authenticate_mode = app_config.AUTHENTICATION_MODE
            tenant_id = app_config.TENANT_ID
            client_id = app_config.CLIENT_ID
            username = app_config.POWER_BI_USER
            password = app_config.POWER_BI_PASS
            client_secret = app_config.CLIENT_SECRET
            scope = app_config.SCOPE_BASE
            authority = app_config.AUTHORITY_URL
        response = None

        try:
            if authenticate_mode.lower() == 'masteruser':

                # Create a public client to authorize the app with the AAD app
                clientapp = msal.PublicClientApplication(client_id, authority=authority)

                # Make a client call if Access token is not available in cache
                response = clientapp.acquire_token_by_username_password(username, password, scopes=scope)

            # Service Principal auth is recommended by Microsoft to achieve App Owns Data Power BI embedding
            else:
                authority = authority.replace('organizations', tenant_id)
                clientapp = msal.ConfidentialClientApplication(client_id, client_credential=client_secret, authority=authority)

                # Make a client call if Access token is not available in cache
                response = clientapp.acquire_token_for_client(scopes=scope)

            return response['access_token']

        except KeyError:
            raise Exception(response['error_description'])
        except Exception as ex:
            raise Exception('Error retrieving Access token\n' + str(ex))
