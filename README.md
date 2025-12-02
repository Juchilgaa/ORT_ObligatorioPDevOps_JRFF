#  Despliegue de APP RRHH



## Generar una SSH key en Linux
ssh-keygen -t ed25519 -C "tu_mail@fiort.edu.uy"

Presioná ENTER tres veces.

Tu clave pública queda en:

~/.ssh/id_ed25519.pub

## Mostrar la clave pública
cat ~/.ssh/id_ed25519.pub


Copiá el texto completo (empieza con ssh-ed25519).

## Agregar la SSH key en GitHub

Ir a GitHub

Ir a: Settings → SSH and GPG Keys

Clic en New SSH key

Pegás tu key → Add SSH key

***** Clonar el repo por SSH
En la terminal:

$git clone git@github.com:Juchilgaa/ORT_ObligatorioPDevOps_JRFF.git
$cd ORT_ObligatorioPDevOps_JRFF/automatismo_app

Requisitos

## Instalar herramientas necesarias: Python 3, Pip, venv, AWS CLI

$sudo apt update && sudo apt install python3 -y
$sudo apt install python3-pip -y
$sudo apt install python3-venv -y
$sudo apt install awscli -y

### Si en AWS CLI necesitás configurar claves:

$aws configure

Ubicate en:

ORT_ObligatorioPDevOps_JRFF/automatismo_app/

Deberías ver:

automatismo_rrhh.py
obligatorio-main.zip

## Crear entorno virtual
$python3 -m venv .venv
$source .venv/bin/activate

## Instalar dependencias boto3:
$pip install boto3

Configurar variables de entorno:

El script requiere tres variables:

export RDS_ADMIN_PASSWORD='ClaveSegura123!!'
export APP_USER='admin'
export APP_PASS='admin123'


Si falta alguna, el script se detiene.

## Ejecutar el despliegue

Desde la carpeta automatismo_app con el venv activado:

$python3 automatismo_rrhh.py


Salida típica:

=== DESPLIEGUE COMPLETADO ===
URL de la aplicación: http://X.X.X.X/index.php
APP_USER: admin
APP_PASS: admin123

Estructura del proyecto
 
ORT_ObligatorioPDevOps_JRFF/
│
├── automatismo_app/
│     ├── automatismo_rrhh.py
│     ├── obligatorio-main.zip
│     └── (archivos generados por el script)
│
├── script_bash.sh
├── archivo.txt
└── README.md

