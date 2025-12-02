📌 Despliegue de APP RRHH


1. 🔐 Generar SSH Key en Linux
ssh-keygen -t ed25519 -C "tu_mail@fi.ort.edu.uy"


Presioná ENTER tres veces para aceptar los valores por defecto.

Tu clave pública queda en:

~/.ssh/id_ed25519.pub

Mostrar la clave pública
cat ~/.ssh/id_ed25519.pub


Copiá el texto completo (empieza con ssh-ed25519).

2. 🔑 Agregar la SSH Key en GitHub

Ir a GitHub

Navegar a Settings → SSH and GPG Keys

Hacer clic en New SSH key

Pegar la clave generada

Confirmar con Add SSH key

3. 📥 Clonar el repositorio por SSH
git clone git@github.com:Juchilgaa/ORT_ObligatorioPDevOps_JRFF.git
cd ORT_ObligatorioPDevOps_JRFF/automatismo_app

4. 🛠️ Instalar herramientas necesarias
sudo apt update && sudo apt install python3 -y
sudo apt install python3-pip -y
sudo apt install python3-venv -y
sudo apt install awscli -y

Configurar AWS CLI (si corresponde)
aws configure

5. 📂 Ubicarte dentro del proyecto

Debés estar en:

ORT_ObligatorioPDevOps_JRFF/automatismo_app/


Deberías ver:

automatismo_rrhh.py
obligatorio-main.zip

6. 🧪 Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate

7. 📦 Instalar dependencias
pip install boto3

8. 🔧 Configurar variables de entorno

El script requiere:

export RDS_ADMIN_PASSWORD='ClaveSegura123!!'
export APP_USER='admin'
export APP_PASS='admin123'

9. 🚀 Ejecutar el despliegue
python3 automatismo_rrhh.py

10. 📄 Salida típica
=== DESPLIEGUE COMPLETADO ===
URL de la aplicación: http://X.X.X.X/index.php
APP_USER: admin
APP_PASS: admin123
