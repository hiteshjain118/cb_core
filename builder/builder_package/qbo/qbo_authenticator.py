from builder_package.core.iauthenticator import IHTTPConnection
from .oauth_manager import QBOOAuthManager
from .qbo_user import QBOUser
from .qbo_request_auth_params import QBORequestAuthParams
from typing import Dict, Any

class QBOHTTPConnection(IHTTPConnection):
    def __init__(self, auth_params: QBORequestAuthParams, qbo_user: QBOUser):
        self.oauth_manager = QBOOAuthManager(auth_params)
        self.qbo_user = qbo_user

    def authenticate(self) -> str:
        pass
    
    def is_authorized(self) -> bool:
        return self.oauth_manager.is_company_connected(self.qbo_user.realm_id)
    
    def get_cbid(self) -> str:
        return self.qbo_user.realm_id
    
    def get_valid_access_token_not_throws(self) -> str:
        return self.oauth_manager.get_valid_access_token_not_throws(self.qbo_user.realm_id)
    
    def get_platform_name(self) -> str:
        return "QBO"
    
    def get_remote_user(self) -> QBOUser:
        return self.qbo_user