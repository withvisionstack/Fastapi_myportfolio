import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

def send_email_notification(msg):
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = os.getenv("BREVO_API_KEY")

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": "stafproject125bpm@gmail.com"}],  # para onde você quer receber
        sender={"email": "stafproject125bpm@gmail.com", "name": "Mensageria API"},
        subject="Nova mensagem recebida",
        html_content=f"""
            <h3>Nova mensagem recebida</h3>
            <p><strong>Nome:</strong> {msg.sender_name}</p>
            <p><strong>Email:</strong> {msg.sender_email}</p>
            <p><strong>Mensagem:</strong> {msg.content}</p>
        """
    )

    try:
        api_instance.send_transac_email(email)
    except ApiException as e:
        print("Erro ao enviar email:", e)

