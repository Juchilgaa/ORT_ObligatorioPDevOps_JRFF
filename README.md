# Parte 1 - Script BASH

Este script automatiza la creación de usuarios en Linux a partir de un archivo estructurado, realizando validaciones de sintaxis, control de parámetros y manejo seguro de campos opcionales. Permite asignar una contraseña común a los usuarios creados y cuenta con un modo informativo que detalla cada paso del proceso de creación.
***

## Validación de parámetros

- Procesa los modificadores -i y -c <pass> en dicho orden!

- Rechaza modificadores inválidos

- Exige exactamente 1 archivo de entrada tras procesar opciones

## Validación del archivo de entrada

- Verifica que el archivo exista

- Sea un archivo regular

- Tenga permisos de lectura

- Tenga exactamente 5 campos separados por “:”

- El nombre de usuario (campo 1) no puede estar vacío

- El campo “crear home” debe ser SI o NO

##  Valores por defecto aplicados

- Comentario > (`<valor por defecto>`)

- Directorio home > Depende de useradd

- Crear home > -M o -m según campo SI/NO

- Shell	> La shell por defecto del sistema si está vacía


### Reglas

- usuario > No puede estar vacío
 
- comentario > Puede estar vacío

- home > Si está vacío, useradd usa su valor por defecto

- crear home > Debe ser SI o NO (mayúsculas / minúsculas permitidas)

- shell > Puede estar vacío


#### Requisitos del sistema

***
Debe ejecutarse como #root, de lo contrario el script aborta

***


# Creación de usuarios

El script crea usuarios utilizando las siguientes opciones internas de `useradd`:

- Comentario (`-c`)
- Directorio home (`-d`)
- Creación o no del home (`-m` / `-M`)
- Shell de inicio (`-s`)

Además, el script cuenta con una opción propia:

- (``-c <contraseña>``) del **script** para asignar una contraseña común a todos los usuarios creados.

## Modo informativo (-i)

Despliega: 

- Comentario
- Directorio home
- SI/NO de creación del home
- Shell asignada
- Aviso si no se pudo asignar contraseña
- Aviso si el usuario no pudo ser creado


## Ejemplos válidos

juan:Usuario Juan:/home/juan:SI:/bin/bash

maria::/home/maria:NO:/bin/zsh

pedro:DevOps::SI:/bin/sh

lucas:::: 


## Uso del script

Ejecución básica:
```
sudo ./script_bash/ej1_crea_usuarios.sh archivo_usuarios.txt
```
Crear usuarios asignando la misma contraseña:
```
sudo ./script_bash/ej1_crea_usuarios.sh -c Contraseña123 archivo_usuarios.txt
```
Mostrar información detallada:
```
sudo ./script_bash/ej1_crea_usuarios.sh -i archivo_usuarios.txt
```
Modo combinado: información + contraseña:
```
sudo ./script_bash/ej1_crea_usuarios.sh -i -c 1234 archivo_usuarios.txt
```
Comportamiento si NO se especifica contraseña: 

El usuario se crea sin contraseña

Se podrá asignar posteriormente usando passwd usuario


# Reporte final

Al finalizar, si se usó -i, muestra la cantidad de usuarios creados con éxito.


# 🚦 Códigos de error

| Código | Descripción                                      |
|--------|--------------------------------------------------|
| 1      | Falta contraseña después de `-c`                 |
| 2      | Parámetro inválido                               |
| 3      | Uso incorrecto (cantidad de parámetros)          |
| 4      | Archivo inexistente                              |
| 5      | Archivo no regular                               |
| 6      | Sin permisos de lectura                          |
| 7      | Script no ejecutado como root                    |
| 8      | Sintaxis incorrecta en una línea del archivo     |
| 9      | Error durante la creación de uno o más usuarios  |
| 0      | Ejecución exitosa                                |

# Resultado final

**El script muestra: Se crearon (`<n>`) usuarios con éxito**

***

# Parte 2 - Automatización APP RRHH AWS

 📌 Despliegue de APP RRHH


## 🔐 Generar SSH Key en Linux
```
ssh-keygen -t ed25519 -C "tu_mail@fi.ort.edu.uy"
```

Presioná ENTER tres veces para aceptar los valores por defecto.

Mostrar la clave pública:
```
cat ~/.ssh/id_ed25519.pub
```

Copiá el texto completo (empieza con ssh-ed25519).

## 🔑 Agregar la SSH Key en GitHub

Ir a GitHub

Navegar a Settings → SSH and GPG Keys

Hacer clic en New SSH key, pegar la clave generada.

## 🛠️ Instalación de las herramientas GIT
```
git --version
sudo apt update && sudo apt install -y git
```
## 📥 Clonar el repositorio por SSH
```
git clone git@github.com:Juchilgaa/ORT_ObligatorioPDevOps_JRFF.git
cd ORT_ObligatorioPDevOps_JRFF/script_python
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


## Configurar AWS CLI (si corresponde)
```
aws configure
```
Aquí nos va a solicitar los datos para la conexión contra el AWS Academy, agregar:

aws_access_key_id=
aws_secret_access_key=
aws_session_token=
Region: [us-east-1]
Format: [json]

 Estos datos nos los encontramos en AWS Details, dentro del Lab. 

## 📂 Ubicarte dentro del proyecto

Debés estar en:

ORT_ObligatorioPDevOps_JRFF/script_python


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


¡¡ Automatismo ejecutado !!