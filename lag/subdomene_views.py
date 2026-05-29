# lag/subdomene_views.py
import os
import socket
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from lag.models import Organisasjon
import ssl
from django.contrib.auth.models import User
import subprocess
from pathlib import Path

def opprett_nginx_subdomene(subdomene):

    nginx_fil = "/etc/nginx/sites-available/u3a.no"

    blokk = f"""

server {{
    listen 443 ssl;
    server_name {subdomene}.u3a.no;

    ssl_certificate /etc/letsencrypt/live/{subdomene}.u3a.no/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{subdomene}.u3a.no/privkey.pem;

    location / {{
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn_u3a_prod/gunicorn.sock;
    }}
}}
"""

    innhold = Path(nginx_fil).read_text()

    if f"server_name {subdomene}.u3a.no;" not in innhold:

        with open(nginx_fil, "a") as f:
            f.write(blokk)

#        subprocess.run(["sudo", "nginx", "-t"])
#        subprocess.run(["sudo", "systemctl", "reload", "nginx"])

@staff_member_required
def subdomene_start(request):
    resultat = None
    subdomene = ""

    if request.method == "POST":
        subdomene = request.POST.get("subdomene", "").strip().lower()

        if request.POST.get("opprett_lokallag") == "1":
            organisasjon = request.POST.get("organisasjon", "").strip()
            kommune = request.POST.get("kommune", "").strip()
            epost = request.POST.get("epost", "").strip()
            hjemmesidetype = request.POST.get("hjemmesidetype", "1").strip()

            org = Organisasjon.objects.create(
                organisasjon=organisasjon,
                subdomene=subdomene,
                kommune=kommune,
                epost=epost,
                status="Aktiv",
            )
#            opprett_nginx_subdomene(subdomene)

            resultat = {
                "modus": "opprettet",
                "melding": f"{org.organisasjon} er opprettet med subdomene {org.subdomene}.u3a.no.",
                "organisasjon": org,
                "dns_ok": True,
            }

            return render(request, "admin/lag/subdomene_start.html", {
                "subdomene": subdomene,
                "resultat": resultat,
            })
        org = Organisasjon.objects.filter(subdomene=subdomene).first()
        if org and request.POST.get("slett_subdomene") == "1":
            navn = org.organisasjon
            org.delete()

            resultat = {
                "modus": "slettet",
                "melding": f"Test-subdomenet '{subdomene}' og lokallaget '{navn}' er slettet.",
                "organisasjon": None,
                "dns_ok": False,
            }

            return render(request, "admin/lag/subdomene_start.html", {
                "subdomene": subdomene,
                "resultat": resultat,
            })

        if org:
            resultat = {
                "modus": "endre",
                "melding": f"Subdomenet '{subdomene}' finnes allerede og tilhører {org.organisasjon}.",
                "organisasjon": org,
            }
        else:

            dns_ok = False
            dns_ip = None

            try:
                dns_ip = socket.gethostbyname(f"{subdomene}.u3a.no")

                if dns_ip == "46.62.205.45":
                    dns_ok = True

            except Exception:
                pass

            if dns_ok:

                resultat = {
                    "modus": "opprett",
                    "melding": (
                        f"Subdomenet '{subdomene}.u3a.no' "
                        f"peker riktig mot {dns_ip}. "
                        f"Nytt lokallag kan opprettes."
                    ),
                    "organisasjon": None,
                    "dns_ok": True,
                    "dns_ip": dns_ip,
                }

            else:

                resultat = {
                    "modus": "feil",
                    "melding": (
                        f"DNS-test feilet. "
                        f"{subdomene}.u3a.no peker ikke mot 46.62.205.45."
                    ),
                    "organisasjon": None,
                    "dns_ok": False,
                    "dns_ip": dns_ip,
                }



    return render(request, "admin/lag/subdomene_start.html", {
        "subdomene": subdomene,
        "resultat": resultat,
    })

@staff_member_required
def subdomene_detalj(request, subdomene):

    org = Organisasjon.objects.filter(subdomene=subdomene).first()

    if not org:
        return render(request, "admin/lag/subdomene_detalj.html", {
            "feil": f"Subdomenet '{subdomene}' finnes ikke."
        })
    if request.method == "POST":

        if request.POST.get("aktiver_https") == "1":

            hostname = f"{subdomene}.u3a.no"
            nginx_fil = "/etc/nginx/sites-available/u3a.no"

            serverblokk = f"""

server {{
    listen 443 ssl http2;
    server_name {hostname};

    ssl_certificate /etc/letsencrypt/live/{hostname}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{hostname}/privkey.pem;

    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    location /static/ {{
        alias /srv/u3a_prod/staticfiles/;
    }}

    location /media/ {{
        alias /srv/u3a_prod/media/;
    }}

    location / {{
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn_u3a_prod/gunicorn.sock;
    }}
}}
"""

            try:
                certbot = subprocess.run(
                    [
                        "sudo", "certbot", "certonly",
                        "--nginx",
                        "-d", hostname,
                        "--non-interactive",
                        "--agree-tos",
                        "-m", "post@u3a.no",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

                if certbot.returncode != 0:
                    https_melding = (
                        "Certbot feilet:\n\n"
                        + certbot.stdout
                        + "\n\n"
                        + certbot.stderr
                    )

                else:
                    grep = subprocess.run(
                        ["sudo", "grep", "-q", f"server_name {hostname};", nginx_fil],
                        capture_output=True,
                        text=True,
                    )

                    if grep.returncode != 0:
                        subprocess.run(
                            ["sudo", "tee", "-a", nginx_fil],
                            input=serverblokk,
                            capture_output=True,
                            text=True,
                            timeout=30,
                        )

                    nginx_test = subprocess.run(
                        ["sudo", "nginx", "-t"],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )

                    if nginx_test.returncode != 0:
                        https_melding = (
                            "Nginx-test feilet etter oppdatering:\n\n"
                            + nginx_test.stdout
                            + "\n\n"
                            + nginx_test.stderr
                        )

                    else:
                        reload_nginx = subprocess.run(
                            ["sudo", "systemctl", "reload", "nginx"],
                            capture_output=True,
                            text=True,
                            timeout=30,
                        )

                        if reload_nginx.returncode != 0:
                            https_melding = (
                                "Reload av nginx feilet:\n\n"
                                + reload_nginx.stdout
                                + "\n\n"
                                + reload_nginx.stderr
                            )
                        else:
                            https_melding = f"HTTPS er aktivert for {hostname}."

            except Exception as e:
                https_melding = f"HTTPS-aktivering ga teknisk feil: {e}"
        if request.POST.get("fjern_admin") == "1":

            bruker_id = request.POST.get("bruker_id")

            bruker = User.objects.filter(id=bruker_id).first()

            if bruker:
                org.redaktorer.remove(bruker)

        if request.POST.get("opprett_admin") == "1":

            brukernavn = request.POST.get("brukernavn", "").strip()
            epost = request.POST.get("admin_epost", "").strip()
            passord = request.POST.get("passord", "").strip()

            if brukernavn and passord:

                user = User.objects.filter(username=brukernavn).first()

                if not user:
                    user = User.objects.create_user(
                        username=brukernavn,
                        email=epost,
                        password=passord,
                        is_staff=True,
                    )

                org.redaktorer.add(user)
                org.save()

        if request.POST.get("lagre_organisasjon") == "1":

            org.organisasjon = request.POST.get("organisasjon", "").strip()
            org.epost = request.POST.get("epost", "").strip()
            org.telefon = request.POST.get("telefon", "").strip()
            org.status = request.POST.get("status", "").strip()
            org.kommune = request.POST.get("kommune", "").strip()
            org.orgnummer = request.POST.get("orgnummer", "").strip()
            org.hjemmesidetype = request.POST.get("hjemmesidetype", "1")

            org.save()
    
    https_ok = False
    if "https_melding" not in locals():
        https_melding = ""
    hostname = f"{subdomene}.u3a.no"

    try:
        context = ssl.create_default_context()

        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname):
                https_ok = True
                https_melding = "HTTPS og sertifikat er OK."

    except Exception as e:

        cert_path = f"/etc/letsencrypt/live/{hostname}/fullchain.pem"

        if os.path.exists(cert_path):
            https_ok = True
            https_melding = (
                "HTTPS er aktivert og sertifikat finnes. "
                "DNS/SSL kan være under oppdatering."
            )
        else:
            https_ok = False
            https_melding = f"HTTPS / sertifikat feiler: {e}"

    return render(request, "admin/lag/subdomene_detalj.html", {
        "organisasjon": org,
        "subdomene": subdomene,
        "https_ok": https_ok,
        "https_melding": https_melding,
    })

