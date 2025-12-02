# 📌 Despliegue de APP RRHH


## 🔐 Generar SSH Key en Linux
```
ssh-keygen -t ed25519 -C "tu_mail@fi.ort.edu.uy"
```

Presioná ENTER tres veces para aceptar los valores por defecto.

Tu clave pública queda en:
```
~/.ssh/id_ed25519.pub
```
Mostrar la clave pública

```
cat ~/.ssh/id_ed25519.pub
```

Copiá el texto completo (empieza con ssh-ed25519).

## 🔑 Agregar la SSH Key en GitHub

Ir a GitHub

Navegar a Settings → SSH and GPG Keys

Hacer clic en New SSH key, pegar la clave generada.

## Instalación de las herramientas Git
```
git --version
sudo apt update && sudo apt install -y git
```
## 📥 Clonar el repositorio por SSH
```
git clone git@github.com:Juchilgaa/ORT_ObligatorioPDevOps_JRFF.git
cd ORT_ObligatorioPDevOps_JRFF/automatismo_app
```

## 🛠️ Instalar herramientas necesarias
```
sudo apt update && sudo apt install python3 -y
sudo apt install python3-pip -y
sudo apt install python3-venv -y
```

## AWS CLI, lo separamos ya que es importante para el deploy
```
sudo apt update
sudo apt install -y unzip curl

curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```


Configurar AWS CLI (si corresponde)
```
aws configure
```
## 📂 Ubicarte dentro del proyecto

Debés estar en:

ORT_ObligatorioPDevOps_JRFF/automatismo_app/


Deberías ver:

automatismo_rrhh.py
obligatorio-main.zip

## 🧪 Crear entorno virtual
```
python3 -m venv .venv
source .venv/bin/activate
```
## 📦 Instalar dependencias
```
pip install boto3
```
## 🔧 Configurar variables de entorno

El script requiere:
```
export RDS_ADMIN_PASSWORD='ClaveSegura123!!'
export APP_USER='admin'
export APP_PASS='admin123'
```
## 🚀 Ejecutar el despliegue
```
python3 automatismo_rrhh.py
```
## 📄 Salida
=== DESPLIEGUE COMPLETADO ===
URL de la aplicación: http://X.X.X.X/index.php
APP_USER: admin
APP_PASS: admin123
