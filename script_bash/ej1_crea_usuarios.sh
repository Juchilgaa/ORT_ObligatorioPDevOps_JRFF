#!/bin/bash

# ej1_crea_usuarios.sh

# Obligatorio DevOps 2025 - Ejercicio 1 (Bash)

# Autores: Fabian Ferreira, Juan Recalde

# Sintaxis:
#   ej1_crea_usuarios.sh [-i] [-c contraseña] Archivo_con_los_usuarios_a_crear

# Descripción general:
#   - Lee un archivo de texto donde cada línea tiene el formato:
#       usuario:comentario:home:crear_home(SI/NO):shell

#   - Para cada línea válida:
#       * Valida la sintaxis (exactamente 4 ":" por línea).
#       * Construye dinámicamente el comando useradd.
#       * Crea el usuario con los parámetros indicados.
#       * Opcionalmente asigna una contraseña común para los usuarios creados (-c).
#       * Opcionalmente informa el resultado detallado (-i).

# Comportamientos por defecto:

#   - Campo comentario:
#         Si está vacío, no se agrega opción -c a useradd, quedando el valor por defecto.

#   - Campo home:
#         Si está vacío:
#             No se especifica -d.
#             El script usa el comportamiento por defecto definido por nosotros para crear_home,
#             que es "NO", por lo que se agrega -M y NO se crea el directorio home.
#         Si tiene valor:
#             Se agrega -d <ruta>.

#   - Campo crear_home (SI/NO):
#         Si contiene:
#             "SI"  → se usa -m  (crear el directorio home si no existe).
#             "NO"  → se usa -M  (no crear el directorio home).
#             vacío → el script asume "NO" por defecto, por lo que se utiliza -M.

#   - Campo shell_def:
#         Si está vacía, no se agrega -s y useradd aplicará la shell por defecto del sistema.

# Códigos de salida:
#   0  -> ejecución exitosa
#   1  -> opción -c sin contraseña válida.
#   2  -> parámetro inválido (distinto de -i o -c).
#   3  -> cantidad de parámetros incorrecta.
#   4  -> archivo con los usuarios inexistente.
#   5  -> archivo no es regular.
#   6  -> sin permisos de lectura sobre el archivo.
#   7  -> el script no se ejecuta como root.
#   8  -> error de sintaxis en alguna linea del archivo con los usuarios.
#   9  -> error en la creación de el/los usuarios o asignación de contraseña.




# Bloque 1 - Procesamiento de parámetros (modificadores -i, -c y archivo con los usuarios)

# En este bloque recorremos los argumentos que recibe el script, dejando a propósito
# el archivo con los usuarios en $1 para validarlo en el siguiente bloque. Para esto
# usamos un while que itera mientras queden parámetros, y dentro del bucle aplicamos
# un case sobre el contenido de $1.

# Si el argumento es "-i", activamos la información detallada asignando "SI" a la
# variable informar (inicialmente vale "NO"), y usamos shift para descartarlo y avanzar.

# Si aparece "-c", esperamos que el siguiente valor sea la contraseña para los
# usuarios, y validamos que exista y que no sea un archivo. Si falla la validación,
# mostramos el error por stderr y salimos con código 1. Si está todo bien, guardamos la
# contraseña en la variable contrasena (inicializada como cadena vacía) y hacemos
# shift 2 para descartar tanto "-c" como su valor.

# Si encontramos cualquier otro argumento que empiece con "-", lo tomamos como
# inválido, lo informamos por stderr y salimos con código 2.

# Cuando el parámetro actual no empieza con "-", asumimos que es el archivo con los
# usuarios. En ese momento salimos del while con break y dejamos ese valor en $1 para
# validarlo en el bloque siguiente.


informar="NO"
contrasena=""

while [ $# -gt 0 ]; do
    case "$1" in
        -i)
            informar="SI"
            shift
            ;;
        -c)
            if [ -z "$2" ] || [ -f "$2" ]; then
                echo "Error: -c requiere contraseña" >&2
                exit 1
            fi
            
            contrasena="$2"
            shift 2
            ;;
        -*)
            echo "Parámetro inválido: $1" >&2
            exit 2
            ;;
        *)
            break
            ;;
    esac
done

# Bloque 2 - Validación del archivo de entrada y verificación de permisos

# En este bloque verificamos que después de procesar los modificadores del bloque
# anterior, quede exactamente un parámetro: el archivo con los usuarios. Si la cantidad
# es distinta de 1, mostramos el formato correcto de uso y salimos con código 3.

# Guardamos ese valor en la variable "archivo" y validamos tres cosas:
#   - que exista en el sistema (! -e)
#   - que sea un archivo regular (! -f)
#   - que tengamos permisos de lectura sobre él (! -r)
# Si alguna de estas condiciones falla, mostramos un mensaje de error por stderr y #terminamos con el código correspondiente.

# Además verificamos que el script se ejecute como root, ya que para crear usuarios
# es obligatorio tener privilegios. Si $EUID es distinto de 0, avisamos al usuario y salimos con código 7.


if [ $# -ne 1 ]; then
    echo "Uso correcto: $0 [-i] [-c pass] archivo" >&2
    exit 3
fi

archivo="$1"

if [ ! -e "$archivo" ]; then
    echo "No existe $archivo" >&2
    exit 4
elif [ ! -f "$archivo" ]; then
    echo "$archivo no es archivo regular" >&2
    exit 5
elif [ ! -r "$archivo" ]; then
    echo "Sin permiso de lectura" >&2
    exit 6
fi

if [ "$EUID" -ne 0 ]; then
    echo "Debe ejecutarse como root" >&2
    exit 7
fi



# Bloque 3 - Procesamiento línea a línea del archivo:

# validamos formato, creamos usuarios, asignamos contraseña, mostramos información (si se pidió) y llevamos el registro de aciertos y errores.

# Bloque 3.1 - Inicialización de contadores e indicadores de estado

# En este subbloque inicializamos las variables que vamos a usar a lo largo del while principal:
#   - cant_creados: lleva la cuenta de cuántos usuarios se crearon con éxito.
#   - hubo_error: indica si en algún momento del proceso ocurrió al menos un error (de creación o de contraseña).
#   - creado_ok: se usa como indicador temporal por cada usuario para saber si la ejecución de useradd fue correcta (1) o falló (0).
#   - home_defecto: la ruta base que usa el sistema para crear los directorios home. Si el archivo no indica un home explícito, mostramos este valor.
#   - shell_defecto: shell por defecto que asigna el sistema a los usuarios nuevos, en nuestro caso /bin/bash.
#   - crear_home_defecto: valor que asumimos cuando el campo crear_home está vacío.Nosotros tomamos "NO" como comportamiento por defecto,
# siguiendo la consigna del obligatorio.

cant_creados=0
hubo_error=0
creado_ok=0 
home_defecto="/home"
shell_defecto="/bin/bash"
crear_home_defecto="NO"

# Bloque 3.2 - Lectura del archivo línea por línea

# En este bloque recorremos el archivo usando un while que lee una línea por vez.
# Al usar "IFS= read" hacemos que: 
# - tome la línea completa sin descartar espacios, es decir, la recibe exactamente como está en el archivo.
# - Con "-r" logramos que read no interprete las contrabarras (\). 
# - Que cada línea completa se guarde tal cual en la variable "linea".

# Si la línea viene vacía (por ejemplo, líneas en blanco), simplemente la saltamos usando "continue" y seguimos con la siguiente.

while IFS= read -r linea; do

    if [ -z "$linea" ]; then
        continue
    fi



# Bloque 3.3 - Validación de la sintaxis y extracción de campos.

# En este bloque empezamos validando que la línea tenga el formato correcto.
# Para eso tomamos el contenido de "linea" y lo pasamos por un pipe al comando "tr".
# Usamos "tr -cd ':'" para que deje solamente los caracteres ":" y elimine todo lo demás.
# Ese resultado lo mandamos a "wc -c", que cuenta cuántos ":" quedaron.
# Si esa cantidad es distinta de 4, significa que la línea no tiene los 5 campos
# esperados separados por ":", por lo que consideramos que la sintaxis es incorrecta, mostramos el error y salimos con código 8.

# Una vez que la línea pasa esa validación, usamos "cut" para separar los campos usando ":" como delimitador. Cada campo se guarda en una variable:

#   - usuario      (campo 1)
#   - comentario   (campo 2)
#   - home         (campo 3)
#   - crear_home   (campo 4)
#   - shell_def    (campo 5)
#
# Luego verificamos que el nombre de usuario no esté vacío, ya que es el único campo 
# obligatorio para poder crear el usuario. Si está vacío, o contiene espacios, informamos el error y terminamos con código 8.

# Por último, procesamos el campo "crear_home". Si trae algún valor, lo convertimos
# a mayúsculas con "tr" para normalizar(por ejemplo, “si”, “Si” “sI” ->"SI") y comprobamos
# que sea "SI" o "NO". Si es distinto de esos dos valores, lo consideramos inválido,
# mostramos el mensaje correspondiente y salimos también con código 8.


    if [ "$(echo "$linea" | tr -cd ':' | wc -c)" -ne 4 ]; then
        echo "Sintaxis incorrecta: $linea" >&2
        exit 8
    fi

    usuario=$(echo "$linea" | cut -d: -f1)
    comentario=$(echo "$linea" | cut -d: -f2)
    home=$(echo "$linea" | cut -d: -f3)
    crear_home=$(echo "$linea" | cut -d: -f4)
    shell_def=$(echo "$linea" | cut -d: -f5)

    if [ -z "$usuario" ]; then
        echo "Usuario vacío: $linea" >&2
        exit 8
    fi

    if echo "$usuario" | grep -q " "; then
    echo "Nombre de usuario inválido (contiene espacios): $usuario" >&2
    exit 8

    fi


    crear_mayus=""
    if [ -n "$crear_home" ]; then
        crear_mayus=$(echo "$crear_home" | tr a-z A-Z)
        if [ "$crear_mayus" != "SI" ] && [ "$crear_mayus" != "NO" ]; then
            echo "Valor inválido en crear_home: $crear_home" >&2
            exit 8
        fi
    fi

    # Bloque 3.4 - Construcción y ejecución de useradd
    
    # En este bloque armamos el comando useradd usando un array llamado
    # "creacion_usuario". La idea es ir agregando opciones según los campos que hayan venido
    # en la línea del archivo, y al final ejecutar el comando completo.
    
    # Empezamos cargando el nombre del comando ("useradd") como primer elemento del array. A partir de ahí:
    
    #   - Si "comentario" tiene contenido, agregamos la opción -c y el texto del comentario.
    #   - Si "home" tiene contenido, agregamos la opción -d con la ruta indicada.
    #   - Si "crear_mayus" vale "SI", agregamos -m para crear el home si no existe.
    #     En cualquier otro caso (incluyendo "NO" o vacío), usamos -M para no crearlo.
    #   - Si "shell_def" viene definida, agregamos la opción -s con la shell indicada.
    #   - Por último, agregamos el nombre de usuario, que siempre va como último argumento.
    
    # Al ejecutar "${creacion_usuario[@]}", cada elemento del array se pasa como un argumento
    # separado, lo que nos permite manejar correctamente valores con espacios.
    # Redirigimos la salida de error a /dev/null para no mostrar mensajes de useradd en pantalla.
    
    # Si useradd termina bien, marcamos creado_ok=1 e incrementamos el contador de usuarios creados. 
    # Si falla, seteamos creado_ok=0 y dejamos constancia de que hubo al menos un error cambiando hubo_error a 1.

  
    creacion_usuario=("useradd")

    if [ -n "$comentario" ]; then
    creacion_usuario+=("-c" "$comentario")
    fi

    if [ -n "$home" ]; then
    creacion_usuario+=("-d" "$home")
    fi

    if [ "$crear_mayus" = "SI" ]; then
    creacion_usuario+=("-m")
    else
    creacion_usuario+=("-M")
    fi

    if [ -n "$shell_def" ]; then
    creacion_usuario+=("-s" "$shell_def")
    fi

    creacion_usuario+=("$usuario")


    if "${creacion_usuario[@]}" 2>/dev/null; then
        creado_ok=1
        cant_creados=$((cant_creados + 1))

    else
	creado_ok=0
	hubo_error=1
    fi	
    
       # Bloque 3.5 - Asignación de contraseña
       
    # En este subbloque manejamos la contraseña opcional que puede venir por el modificador -c.
    # Definimos "pass_correcta" como un indicador temporal para saber si chpasswd funcionó correctamente (1 = éxito, 0 = fallo).
    
    # Solo intentamos asignar la contraseña si el usuario se creó sin errores (creado_ok = 1)
    # y además se definió una contraseña en la variable "contrasena". Para asignarla usamos
    # el comando "chpasswd", enviándole por stdin el formato "usuario:contraseña".
    
    # Redirigimos los mensajes de error a /dev/null para no mostrar la salida del comando.
    
    # Si chpasswd devuelve un código distinto de 0, interpretamos que hubo un problema, por lo que
    # marcamos pass_correcta=0 y registramos que hubo al menos un error en el proceso seteando la variable global hubo_error a 1.

    
    pass_correcta=1
    
    if [ "$creado_ok" -eq 1 ] && [ -n "$contrasena" ]; then
        echo "$usuario:$contrasena" | chpasswd 2>/dev/null
        if [ $? -ne 0 ]; then
            pass_correcta=0
            hubo_error=1
        fi
    fi
    
    # Bloque 3.6 - Información opcional (-i)
    
    # En este subbloque manejamos la opción "-i". Si el script se ejecuta con este
    # modificador, mostramos en pantalla información detallada del resultado para cada usuario procesado.
    
    # Primero verificamos si "informar" vale "SI". En ese caso:
    #   - Si "creado_ok" es 1, mostramos un resumen de los datos usados para crear
    #     el usuario. Para cada campo opcional (comentario, home, crear_home y shell)
    #     usamos una variable auxiliar. Si el campo viene con contenido, mostramos
    #     ese valor; si está vacío, mostramos el valor por defecto que usa nuestro script (home_defecto, shell_defecto y crear_home_defecto)
    
    #   - También verificamos el indicador "pass_correcta". Si vale 0, avisamos por
    #     pantalla que no se pudo asignar la contraseña, aunque el usuario haya sido
    #     creado.
    
    #   - Si "creado_ok" es 0, informamos que no se pudo crear el usuario.
    
    # Al final de cada usuario mostramos una línea en blanco para separar visualmente la información de cada uno.

    
    if [ "$informar" = SI ]; then
    	if [ "$creado_ok" -eq 1 ]; then
        	echo "Usuario $usuario creado:"

        	if [ -n "$comentario" ]; then
            	valor_comentario="$comentario"
        	else
            	valor_comentario="(vacío)"
        	fi
        	echo "Comentario: $valor_comentario"

        	if [ -n "$home" ]; then
            	valor_home="$home"
        	else
            	valor_home="$home_defecto/$usuario"
        	fi
        	echo "Dir home: $valor_home"

        	if [ -n "$crear_mayus" ]; then
            	valor_crear="$crear_mayus"
        	else
            	valor_crear="$crear_home_defecto"
        	fi
        	echo "Asegura home: $valor_crear"

        	if [ -n "$shell_def" ]; then
            	valor_shell="$shell_def"
        	else
            	valor_shell="$shell_defecto"
        	fi
        	echo "Shell: $valor_shell"

        	if [ "$pass_correcta" -eq 0 ]; then
            	echo "ATENCION: no se pudo asignar contraseña" >&2
        	fi
	else
		echo "ATENCION: no se pudo crear $usuario" >&2
	fi
	echo
    fi 

done < "$archivo"

# Bloque 4 - Finalización del script

# Al terminar de procesar todas las líneas del archivo, revisamos si se había
# solicitado la opción "-i". De ser así, mostramos cuántos usuarios fueron creados
# correctamente acumulados en "cant_creados".

# Después comprobamos si durante el proceso hubo algún error. Para eso usamos la
# variable "hubo_error", que fuimos actualizando en los bloques anteriores.  
# Si vale 1, sabemos que al menos un usuario no se pudo crear o no se le pudo
# asignar contraseña, por lo que finalizamos el script con código 9.

# Si no hubo errores, simplemente terminamos con código 0 indicando una ejecución exitosa.


if [ "$informar" = SI ]; then
    echo "Se crearon $cant_creados usuarios con éxito."
fi

if [ "$hubo_error" -eq 1 ]; then
    exit 9
fi

exit 0