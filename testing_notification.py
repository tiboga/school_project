import json
import os
from pyfcm import FCMNotification
from google.oauth2 import service_account

gcp_json_credentials_dict = json.loads(os.getenv('GCP_CREDENTIALS', None))
credentials = service_account.Credentials.from_service_account_info(gcp_json_credentials_dict, scopes=['https://www.googleapis.com/auth/firebase.messaging'])
fcm = FCMNotification(service_account_file=None, credentials=credentials, project_id="<project-id>")

# Отправка уведомления на конкретное устройство
result = fcm.notify(
    fcm_token="fH2mM9mqSwyA66VcmvQyMv:APA91bFsRgTmKSCT-_h64M3RkIk6UYsUrmggyfYLlw-sh7NmG3gCDNLMPIeeJDQKDHBTKQVR2kYPyRHXc-_mMIgAhmVNP-IyEXSYD7W9R0iXruEi7_lT4bU",
    notification_title="Заголовок уведомления",
    notification_body="Текст уведомления",
)
