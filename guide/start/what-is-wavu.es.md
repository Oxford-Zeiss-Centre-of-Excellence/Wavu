# ¿Qué es Wavu?

## La idea en palabras sencillas

Ya conoces dos mundos. En **Fiji** abres imágenes, dibujas regiones y mides.
En un **notebook de Jupyter** ejecutas herramientas de Python como Cellpose o
scikit-image. Pasar de uno a otro suele significar guardar archivos, cambiar
de programa y volver a cargarlos.

Wavu es un **puente** entre los dos. Sigues trabajando en Fiji; cuando
necesitas Python, eliges una entrada del menú, rellenas un pequeño diálogo y
pulsas OK. El código de Python se ejecuta y los resultados vuelven a Fiji como
imágenes, tablas o contornos nuevos.

![La analogía del restaurante: Fiji es el camarero, el worker es la cocina, cada receta tiene su propia despensa](../assets/img/restaurant.svg){ width="720" }

La imagen del restaurante ayuda:

| En el restaurante | En Wavu | Qué es en realidad |
|---|---|---|
| El camarero toma tu pedido | **Fiji** muestra un diálogo | las entradas del menú Wavu en Fiji |
| La carta | **PARAMS** | una lista corta al principio del script de Python |
| La cocina | **el worker** | un pequeño programa de Python que se ejecuta en *tu* ordenador |
| Una receta | **tu script** | un archivo `.py` con una función `run` |
| La despensa de cada receta | **el entorno** | una carpeta con exactamente los paquetes que necesita ese script |

Como cada receta tiene su propia despensa, instalar PyTorch para un script
nunca puede romper otro. Nadie comparte despensa, así que nada se estropea.

## Para quién es

- Escribes notebooks y ya has usado Cellpose o scikit-image.
- Conoces Fiji y te gustaría que tu paso de Python fuera *un clic* allí.
- **No** quieres aprender Java, trucos de conda ni Docker.

## Lo que no es

!!! warning "No es para datos grandes"
    Wavu envía una imagen cada vez, y debe caber en la memoria de tu ordenador
    (aproximadamente hasta 1–2 GB). Para volúmenes enormes, muchos archivos o
    imágenes de portaobjetos completos (whole-slide), usa un flujo de trabajo
    por lotes o en un clúster (HPC).

!!! warning "No es un entorno aislado de seguridad"
    Los entornos separados mantienen apartados los *paquetes*. No encierran al
    script. Un script puede hacer todo lo que puede hacer tu cuenta de
    usuario, así que ejecuta solo scripts de confianza, igual que harías con
    un notebook.

Wavu tampoco sustituye a tu notebook. Los notebooks son geniales para
explorar; Wavu es para el momento en que la receta ya funciona y quieres
usarla, o que la usen tus colegas, desde Fiji.

## Cómo se siente una ejecución

1. En Fiji, abre una imagen.
2. Elige **Plugins › Wavu › Run Python Script** (ejecutar script de Python) y
   escoge una carpeta de script.
3. Aparece un diálogo. Rellénalo y pulsa **OK**.
4. Los mensajes van apareciendo en la ventana **Log** de Fiji y la barra de
   progreso avanza.
5. Los resultados se abren en Fiji.

La primera ejecución de un script es lenta, porque se está llenando su
despensa (el entorno): los paquetes se descargan una sola vez. Después,
arranca rápido.

## En una frase

Wavu permite que Fiji envíe una imagen y unos pocos ajustes a tu script de
Python, que se ejecuta en su propio entorno ordenado y devuelve los resultados
directamente.

[Siguiente: instalar Wavu en Fiji :material-arrow-right:](install.md){ .md-button }
