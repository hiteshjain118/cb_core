from builder_package.core.cb_user import CBUser
import os
import sys
from dotenv import load_dotenv

# Add the qbo directory to sys.path to allow imports  
current_dir = os.path.dirname(os.path.abspath(__file__))
qbo_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), 'qbo')
if qbo_dir not in sys.path:
    sys.path.append(qbo_dir)

from .database import is_prod_environment

class QBOUser(CBUser):

    def __init__(self, realm_id: str, user_timezone: str):
        base_url_template = "https://quickbooks.api.intuit.com" if is_prod_environment() else "https://sandbox-quickbooks.api.intuit.com"
        base_url = f"{base_url_template}/v3/company/{realm_id}"
        
        super().__init__(base_url, user_timezone)
        self.realm_id = realm_id