# Glosario

## La idea en palabras sencillas

Cada campo tiene su jerga. Aquí tienes cada palabra de Wavu en una línea
sencilla, con la imagen del restaurante cuando ayuda.

![La analogía del restaurante: Fiji es el camarero, el worker es la cocina, cada receta tiene su propia despensa](../assets/img/restaurant.svg){ width="560" }

## Palabras

**Fiji**
:   El programa de análisis de imagen que ya usas (ImageJ con plugins). En
    Wavu es el *camarero*: entra un diálogo, salen resultados.

**Wavu**
:   "Puente" en fiyiano. Las entradas del menú en Fiji más un pequeño
    ayudante de Python que conectan Fiji con tu script de Python.

**Script**
:   Un archivo `.py` con `PARAMS` y una función `run`. La *receta*.

**Carpeta de script**
:   Una carpeta con un `pixi.toml` y uno o más scripts. Lo que eliges en
    **Run Python Script**.

**PARAMS**
:   La lista al principio de un script que describe los campos del diálogo.
    La *carta*.

**`run(ctx, inputs, params)`**
:   La función que llama Wavu. `inputs` contiene las imágenes, `params` los
    demás ajustes, y `ctx` es la línea de vuelta a Fiji.

**ctx**
:   Abreviatura de "context" (contexto): `ctx.log`, `ctx.progress`,
    `ctx.cancelled` y compañía.

**Worker**
:   Un pequeño programa de Python en *tu* ordenador que ejecuta tu script
    cuando Fiji lo pide. La *cocina*. Solo habla con Fiji dentro de tu propia
    máquina.

**Entorno**
:   Una carpeta privada con un Python concreto más los paquetes que necesita
    un script, guardada en `.pixi` dentro de la carpeta del script. La
    *despensa*.

**pixi**
:   La herramienta gratuita que construye entornos y descarga paquetes, una
    alternativa moderna a conda. Wavu la descarga por ti.

**`pixi.toml`**
:   La *lista de la compra*: qué paquetes necesita el script.

**Archivo de bloqueo (`pixi.lock`)**
:   El *tique de compra*: la versión exacta de cada paquete. Compartirlo
    significa que todos obtienen el mismo entorno.

**conda-forge / PyPI**
:   Las dos grandes "tiendas" en línea de paquetes de Python. pixi usa
    conda-forge por defecto; PyPI es donde compra `pip`.

**Array de NumPy**
:   La cuadrícula de números de Python; así recibe y devuelve imágenes tu
    script.

**Etiquetas (imagen de etiquetas)**
:   Una imagen en la que cada objeto tiene su propio número entero (1, 2,
    3 …) y el fondo es 0. Fiji la muestra con colores vivos al azar.

**ROI**
:   "Region of interest" (región de interés): un contorno dibujado sobre una
    imagen. Fiji las guarda en el **ROI Manager**; un *RoiSet* es un archivo
    zip lleno de ellas.

**Cancelación cooperativa**
:   Esc levanta una bandera; tu script la comprueba y se detiene por sí
    mismo.

**Punto de interrupción (breakpoint)**
:   Un punto rojo en VS Code donde un script en marcha se pausa para que
    puedas mirar dentro.

**Etiqueta (tag) / versión publicada (release)**
:   Una marca de versión como `v1.0.0` en tu código, y la página de descarga
    que GitHub crea para ella.

**CI**
:   "Integración continua": el robot de GitHub que prueba y empaqueta tu
    código cuando subes una etiqueta. Opcional.

**Sitio de actualización (update site)**
:   Una fuente de descargas de Fiji que marcas en **Help › Update…** para
    instalar y actualizar plugins.

## En una frase

Fiji es el camarero, el worker la cocina, tu script la receta, su entorno
pixi la despensa y `pixi.lock` el tique de compra.
