# Gestor de Vocabulario Francés

Aplicación de escritorio desarrollada en **Python** para gestionar vocabulario en francés, practicarlo mediante sesiones de aprendizaje y consultar el progreso.

El programa utiliza **Tkinter** para la interfaz gráfica y **SQLite** para almacenar los datos. Su arquitectura separa la interfaz, la lógica de negocio, el acceso a datos y la configuración, facilitando el mantenimiento y la ampliación de sus funcionalidades.

## Características principales

* **Gestión de vocabulario:** creación y administración de bases de datos independientes, consulta de palabras y gestión de sus traducciones.
* **Almacenamiento persistente:** uso de SQLite para conservar el vocabulario y los datos de aprendizaje entre sesiones.
* **Sesiones de aprendizaje:** organización de las sesiones mediante parámetros configurables para combinar palabras nuevas y palabras de repaso.
* **Cuestionarios:** práctica del vocabulario y registro de los resultados obtenidos.
* **Repaso adaptativo:** selección de palabras para repasar teniendo en cuenta su historial de aprendizaje y rendimiento.
* **Estadísticas:** consulta del progreso y de los resultados del aprendizaje.
* **Importación desde JSON:** conversión de vocabularios almacenados en JSON al formato SQLite.
* **Configuración externa:** personalización de distintos parámetros mediante `config.json`.
* **Pruebas automatizadas:** comprobación del comportamiento de los principales componentes mediante `pytest`.

## Tecnologías utilizadas

| Tecnología   | Aplicación en el proyecto                                        |
| ------------ | ---------------------------------------------------------------- |
| Python       | Desarrollo de la aplicación y su lógica.                         |
| Tkinter      | Creación de la interfaz gráfica de escritorio.                   |
| SQLite       | Almacenamiento local del vocabulario y los datos de aprendizaje. |
| JSON         | Configuración de la aplicación e importación de vocabulario.     |
| pytest       | Ejecución de pruebas automatizadas.                              |
| Git y GitHub | Control de versiones y alojamiento del código fuente.            |

La aplicación utiliza bibliotecas de la biblioteca estándar de Python para su funcionamiento principal. `pytest` se utiliza exclusivamente durante el desarrollo y las pruebas.

## Requisitos

* Python 3.10 o posterior.
* Una instalación de Python que incluya Tkinter.
* Git, si se desea clonar el repositorio.

En Windows, Tkinter suele estar incluido en la instalación oficial de Python. En otros sistemas operativos puede ser necesario instalar el componente correspondiente mediante el gestor de paquetes del sistema.

## Instalación

### 1. Obtener el código fuente

Clona el repositorio:

```bash
git clone https://github.com/AlgorithmEncoder/Programa-Aprendizaje-Vocabulario-Frances.git
cd Programa-Aprendizaje-Vocabulario-Frances
```

También puedes descargar el repositorio como archivo ZIP desde GitHub y descomprimirlo.

### 2. Crear un entorno virtual

Se recomienda utilizar un entorno virtual para mantener aisladas las dependencias de desarrollo.

```bash
python -m venv .venv
```

En Windows, activa el entorno con PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si utilizas el Símbolo del sistema de Windows:

```bat
.venv\Scripts\activate.bat
```

### 3. Instalar las dependencias de desarrollo

Con el entorno virtual activado, ejecuta:

```bash
python -m pip install -r requirements-dev.txt
```

Este comando instala las herramientas necesarias para el desarrollo y las pruebas. La aplicación no necesita dependencias externas adicionales para su funcionamiento habitual.

## Ejecución

Desde la raíz del proyecto, ejecuta:

```bash
python main.py
```

La aplicación abrirá su interfaz gráfica para acceder a las funcionalidades disponibles.

## Pruebas automatizadas

El proyecto incluye pruebas para comprobar diferentes partes de la aplicación, entre ellas el acceso a SQLite, la lógica de aprendizaje, los cuestionarios, las estadísticas, la conversión de datos, las funciones auxiliares y la integración entre componentes.

Para ejecutar toda la batería de pruebas, utiliza:

```bash
python -m pytest
```

Para obtener un informe más detallado:

```bash
python -m pytest -v
```

Las pruebas están organizadas en el directorio `tests/`.

## Configuración

Los parámetros generales se encuentran en el archivo `config.json`, situado en la raíz del proyecto.

Ejemplo de configuración:

```json
{
    "tamano_sesion_aprendizaje": 10,
    "porcentaje_nuevas": 0.6,
    "porcentaje_repaso": 0.4,
    "porcentaje_acierto_minimo": 0.5,
    "sesiones_para_aprender": 2,
    "opciones_multiple": 4
}
```

### Parámetros disponibles

| Parámetro                   | Descripción                                                                |
| --------------------------- | -------------------------------------------------------------------------- |
| `tamano_sesion_aprendizaje` | Número de palabras previsto para cada sesión de aprendizaje.               |
| `porcentaje_nuevas`         | Proporción destinada a palabras nuevas, expresada entre `0` y `1`.         |
| `porcentaje_repaso`         | Proporción destinada a palabras de repaso, expresada entre `0` y `1`.      |
| `porcentaje_acierto_minimo` | Porcentaje mínimo de aciertos utilizado por la lógica de aprendizaje.      |
| `sesiones_para_aprender`    | Número de sesiones requerido para considerar aprendida una palabra.        |
| `opciones_multiple`         | Número de opciones disponibles en los cuestionarios de selección múltiple. |

La configuración se carga y valida antes de utilizarse. El programa también define valores predeterminados para los parámetros, lo que permite completar las propiedades que falten en el archivo de configuración.

Los valores de los porcentajes deben respetar los límites establecidos por el programa. La suma de `porcentaje_nuevas` y `porcentaje_repaso` no puede superar `1`.

## Almacenamiento de datos

La aplicación utiliza SQLite para almacenar los vocabularios en bases de datos locales.

La ubicación de los datos depende de cómo se ejecute el programa:

* **Durante el desarrollo:** las carpetas `databases/` y `results/` se encuentran en la raíz del proyecto.
* **En una aplicación empaquetada:** los datos se almacenan en `Documents/AprenderFrances`, dentro del directorio personal del usuario.

Esta separación permite mantener los datos generados durante el uso fuera del código fuente de la aplicación.

Las carpetas de datos generados están excluidas del control de versiones mediante `.gitignore`. Si se necesitan bases de datos de ejemplo para demostraciones o pruebas, es preferible mantenerlas en una ubicación específica y diferenciada de los datos personales de ejecución.

## Importación de vocabulario desde JSON

El proyecto incorpora funcionalidad para convertir archivos de vocabulario JSON al formato SQLite.

Esta funcionalidad facilita la migración desde el sistema de almacenamiento anterior y permite reutilizar vocabularios existentes.

Antes de realizar conversiones o sustituir bases de datos, se recomienda conservar una copia de los archivos originales.

## Estructura del proyecto

La estructura general del código se organiza por responsabilidades:

```text
.
├── config/
│   ├── app_config.py
│   └── config_loader.py
├── data/
│   ├── auxiliar.py
│   └── sqlite_db.py
├── logic/
│   ├── json_sqlite_converter.py
│   ├── learning.py
│   ├── quiz_logic.py
│   └── stats.py
├── ui/
│   ├── database_window.py
│   ├── learn_window.py
│   ├── main_window.py
│   ├── quiz_window.py
│   └── stats_window.py
├── utils/
│   └── helpers.py
├── tests/
├── config.json
├── main.py
├── requirements.txt
├── requirements-dev.txt
├── .gitignore
└── README.md
```

La estructura representa la organización prevista del proyecto. Si los nombres o las ubicaciones de los archivos de tu repositorio han cambiado, actualiza el árbol para que coincida exactamente con la versión publicada.

### Responsabilidades de los módulos

* **`config/`:** configuración de rutas, carga de parámetros y validación.
* **`data/`:** acceso a las bases de datos y operaciones de persistencia.
* **`logic/`:** reglas de aprendizaje, selección de palabras para cuestionarios, estadísticas y conversión de datos.
* **`ui/`:** ventanas y componentes de la interfaz gráfica.
* **`utils/`:** funciones auxiliares reutilizables.
* **`tests/`:** pruebas automatizadas de los componentes y de su integración.
* **`main.py`:** punto de entrada de la aplicación.
* **`config.json`:** parámetros configurables del programa.

Esta separación ayuda a mantener diferenciadas las reglas del programa de los detalles de la interfaz y del almacenamiento.

## Objetivos técnicos y aprendizaje

Este proyecto permite trabajar con conceptos y herramientas habituales en el desarrollo de aplicaciones de escritorio:

* Diseño de interfaces gráficas con Tkinter.
* Programación orientada a objetos y organización modular del código.
* Operaciones CRUD (*crear, consultar, actualizar y eliminar*) con SQLite.
* Persistencia de datos y gestión de archivos.
* Carga y validación de configuración externa.
* Conversión entre formatos de almacenamiento.
* Separación entre interfaz, lógica de negocio y acceso a datos.
* Pruebas unitarias y de integración con pytest.
* Uso de Git y GitHub para gestionar el código fuente.

## Estado del proyecto

El proyecto se encuentra en evolución. Su desarrollo se centra en mejorar la calidad del código, la fiabilidad de sus funcionalidades, la cobertura de pruebas y la documentación, con el objetivo de mantener una aplicación clara, mantenible y fácil de ampliar.

## Licencia

No se especifica una licencia en este documento. Si deseas permitir que otras personas utilicen, modifiquen o distribuyan el código, añade un archivo `LICENSE` con la licencia que hayas elegido.
