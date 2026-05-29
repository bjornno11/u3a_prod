import requests
from django.utils import timezone
from lag.models import SmsLogg


def send_sms_logg(logg, leverandor):
    """
    Sender én SMS-logg via Sveve.

    Sikkerhetsregel:
    Hvis testmodus er på, sendes ingen ekte SMS.
    """

    if leverandor.testmodus:
        logg.status = SmsLogg.STATUS_TEST
        logg.leverandor_svar = "TESTMODUS: SMS ble ikke sendt eksternt."
        logg.sendt_tid = timezone.now()
        logg.save()
        return True

    if not leverandor.aktiv:
        logg.status = SmsLogg.STATUS_FEIL
        logg.leverandor_svar = "FEIL: SMS-leverandør er ikke aktivert."
        logg.save()
        return False

    if not leverandor.api_url or not leverandor.api_key or not leverandor.api_secret:
        logg.status = SmsLogg.STATUS_FEIL
        logg.leverandor_svar = "FEIL: API URL, brukernavn eller API-passord mangler."
        logg.save()
        return False

    try:
        response = requests.get(
            leverandor.api_url,
            params={
                "user": leverandor.api_key,
                "passwd": leverandor.api_secret,
                "to": logg.telefon,
                "msg": logg.melding,
                "from": leverandor.avsender,
            },
            timeout=15,
        )

        logg.leverandor_svar = response.text[:1000]
        logg.sendt_tid = timezone.now()

        if response.status_code == 200:
            logg.status = SmsLogg.STATUS_SENDT
            logg.save()
            return True

        logg.status = SmsLogg.STATUS_FEIL
        logg.save()
        return False

    except Exception as e:
        logg.status = SmsLogg.STATUS_FEIL
        logg.leverandor_svar = f"FEIL: {e}"
        logg.save()
        return False

