#!/bin/bash

informar="NO"
contrasena=""


# Bloque 1 - Se procesan los parámetros que se le dan al script, excepto el archivo con los nombres de usuarios.

# Con el while se inicia un bucle que itera sobre cada argumento, mientras haya al menos 1.
# Utilizamos un case para decidir que hacer según el valor de $1 (primer argumento)
# en -i se encuentra la primer coicidencia, y se le asigna el valor "SI" a la variable informar, y usamos shift para eliminar $1 de la lista, por lo que en la próxima iteración del while, se hara sobre $2 que pasará a ser $1
# En la siguiente iteración, si $1 es -c, se verifica que $2 exista y no sea un archivo. Si estas condiciones se cumple, se muestra un error en pantalla y se sale del script. Sino, se asigna $2 a la variable "contrasena".
# También hacemos shift 2 para eliminar tanto $1 como $2 de la lista de argumentos, o sea -c y la contraseña.
# En la siguiente iteración, si $1 empieza con un guión y no coicide con -i o -c se considera un modificador inválido, por lo que muestra el error en pantalla y sale del script.
# Por último, si $1 no empieza con guión (se da por hecho que es el archivo con los nombres de usuarios), se sale del bucle while con un break.
# Esto deja el archivo pendiente en $1 para procesarlo mas adelante.


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

# Bloque 2 - Se valida que el archivo con los usuarios exista, sea un archivo regular y tenga permisos de lectura, y además verifica que el script se esté ejecutando como root.

# Primero, se verifica que quede exactamente un argumento en la lista luego de procesar -i y -c. Ese argumento debe ser el archivo de usuarios. En caso de quedar un número distinto de 1, se muestra un mensaje al usuario de como utilizar le script y sale del mismo.
# Luego se le asigna a la variable "archivo" el argumento restante ($1), que es el archivo de entrada con los usuarios.
# A continuación, con una estructura if anidada evaluamos: si el archivo no existe (! -e), si el archivo existe pero no es regular (! -f), si el archivo existe pero no tiene permisos de lectura (! -r) cada uno con su respectiva salida del script.
# Por último, con otro if, verificamos que el script se esté ejecutando como root, lo cual es necesario para crear usuarios. Si el EUID no es 0 (root) se muestra el error en pantalla y se sale del script.

if [ $# -ne 1 ]; then
    echo "Uso correcto: $0 [-i] [-c pass] archivo" >&2
    exit 3
fi

archivo="$1"

# ---------- Validaciones de archivo ----------
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



# Bloque 3 - procesa cada línea del archivo, valida el formato, crea usuarios con useradd, asigna contraseña si corresponde, muestra información si se pidió y lleva registro de aciertos y errores.

# Bloque 3.1 - Se inicializan las variables que van a llevar el contador de usuarios creados y un indicador de si hubo errores. Se van a utilizar a lo largo del While. También se crea una variable que actua como indicador temporal de si el usuario actual se creó correctamente

cant_creados=0
hubo_error=0
creado_ok=0 

# Bloque 3.2 - Se lee el archivo línea por línea.

# Se inicia un bucle con While que va a iterar sobre cada línea del archivo que se le pase como entrada al read. 
# En este caso, el read permite leer una linea por iteración, con la opción -r escapea la \ y la lee tal cual sin darle un significado especial, y "linea" es la variable donde se van a cargar todas las lineas que lee read.
# Luego con un if, verifica si la línea está vacía, si lo está se "salta" la iteración actual, y pasa a la siguiente línea.

while IFS= read -r linea; do

    if [ -z "$linea" ]; then
        continue
    fi


# Bloque 3.3 - Se valida el formato y se extraen los campos.

# Primero se utiliza una estructura if, en la que se envía el contenido de linea (linea del archivo con los usuarios) a través del pipe, al comando tr.
# La opción -c va a tomar todos los caracteres que no sean ":" y con la opción d los va a eliminar. Se lo pasa como salida al comando wc
# El comando wc con la opción -c cuenta la cantidad de caracteres , es decir, la cantidad de ":" que hay en la linea.
# Todo eso se evalua, y si la salida no es igual a 4, da un mensaje de error y sale del script. Deben ser 4 ya que las lineas del archivo estan compuestas por 5 campos.
# A continuación lo que se busca es separar los campos de cada linea para luego poder construir el comando useradd
# Para esto utilizamos el comando cut que separa la linea usando ":" como delimitador y devuelve el campo que necesitemos, para cargarlo en la variable correspondiente a cada uno.
# Ahora con un if verificamos si la variable usuario está vacía, en caso de estarlo se imprime un error y se sale del script. El nombre del usuario debe existir en el archivo para poder crear el usuario.
# Pasamos a inicializar una nueva variable (crear_mayus) que va a almacenar en mayúscula el contenido de la variable "crear"
# Utilizamos un if y con test -n comprobamos si la variable "crear" no contiene una cadena vacía. Si no está vacía, convierte el valor de "crear" a mayúscula usando el comando "tr".
# Y luego con otro if comprobamos si la variable convertida a mayúscula es diferente de "SI" y de "NO". En caso de que sea dieferente, se imprime un mensaje de error y se sale del script

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

    crear_mayus=""
    if [ -n "$crear_home" ]; then
        crear_mayus=$(echo "$crear_home" | tr a-z A-Z)
        if [ "$crear_mayus" != "SI" ] && [ "$crear_mayus" != "NO" ]; then
            echo "Valor inválido en crear_home: $crear_home" >&2
            exit 8
        fi
    fi

    # Bloque 3.4 - Construcción y ejecución de useradd
  
    # Creamos un arreglo llamado creacion_usuario, que representa el comando que se va a ejecutar.
    # El primer elemento es "useradd", que es el comando que vamos a usar para crear a los usuarios.
    # Luego le vamos a ir agregando elementos al array para al final poder ejecutar useradd
    # Si la variable comentario tiene contenido, agregamos la opcion -c y el contenido de la variable.
    # Si la variable home tiene contenido, agregamos la opción -d y el contenido de la variable
    # Si la variable crear_mayus contiene "SI" agregamos -m, si contiene "NO" agregamos -M
    # Si se definió una shell por defecto para el usuario, agregamos -s y el contenido de la variable shell_def
    # Finalmente, agregamos el nombre del usuario, éste siempre va como último argumento en el comando useradd
    # Por último ejecutamos el comando completo expandiendo el array con "${creacion_usuario[@]}"
    # Cada elemento del array se pasa como un argumento separado, por lo que evitamos problemas con los espacios que pueda haber en cada elemento
    # Redirigimos la salida a /dev/null para no mostrar el resultado en pantalla
    # Si el comando se ejecuta correctamente, incrementamos el contador de usuarios creados
    # Si falla, marcamos que hubo un error con la variable hubo_error=1
  
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
    
    # Definimos pass_correcta como indicador temporal de éxito/fallo en la asignación de la contraseña
    # 1 = éxito , 0 = fallo
    # Si el usuario se creó correctamente, y la persona definió una contraseña que se cargó correctamente en la variable contrasena entonces utilizamos el comando chpasswd para asignarle la contraseña al usuario con la sintaxis $usuario:$contraseña
    # Redirigimos los errores a /dev/null para no mostrarlo en pantalla
    # Luego comprobamos si chpasswd tuvo éxito utilizando un if y verificando la salida del comando anterior, para esto utilizamos $?.
    
    pass_correcta=1
    
    if [ "$creado_ok" -eq 1 ] && [ -n "$contrasena" ]; then
        echo "$usuario:$contrasena" | chpasswd 2>/dev/null
        if [ $? -ne 0 ]; then
            pass_correcta=0
            hubo_error=1
        fi
    fi
    
    
    # Bloque 3.6 - Informacion opcional (-i)
    # Si se especificó la opción -i, se muestra información detallada en pantalla.
    # Primero verificamos si el usuario se creó correctamente mediante la variable creado_ok.
    # Si lo anterior se cumple, imprimimos los detalles de los usuarios creados en pantalla
    # Para cada dato opcional usamos un if. Si la variable tiene contenido, la asignamos a una variable auxiliar. Si está vacía, le damos un valor por defecto. Repetimos este procedimiento para cada uno de los campos informativos.
    # Luego verifica si la contraseña no se pudo asignar en caso de que pass_correcta sea distinta de 0 (muestra en pantalla el error)
    # En caso de que el usuario no se haya creado con éxito, también le saldrá un msj en pantalla al usuario informandole.
    # Por último finaliza el bucle While, que leyó línea por línea el archivo con los usuarios
    
    if [ "$informar" = SI ]; then
        if [ "$creado_ok" -eq 1 ]; then
            echo "Usuario $usuario creado:"
            
        
            if [ -n "$comentario" ]; then
                valor_comentario="$comentario"
            else
                valor_comentario="<valor por defecto>"
            fi
            echo "Comentario: $valor_comentario"

        
            if [ -n "$home" ]; then
                valor_home="$home"
            else
                valor_home="<valor por defecto>"
            fi
            echo "Dir home: $valor_home"

        
            if [ -n "$crear_mayus" ]; then
                valor_crear="$crear_mayus"
            else
                valor_crear="<valor por defecto>"
            fi
            echo "Asegura home: $valor_crear"

      
            if [ -n "$shell_def" ]; then
                valor_shell="$shell_def"
            else
                valor_shell="<valor por defecto>"
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

# Si se indicó la opción -i, se muestra la cantidad de usuarios creados.
# Luego se verifica si ocurrió algún error durante el proceso mediante la variable hubo_error. Si vale 1, se informa al usuario y se finaliza con código de salida 7.
# Si no hubo errores, el script termina con código 0 (éxito)

if [ "$informar" = SI ]; then
    echo "Se crearon $cant_creados usuarios con éxito."
fi

if [ "$hubo_error" -eq 1 ]; then
    exit 9
fi

exit 0
