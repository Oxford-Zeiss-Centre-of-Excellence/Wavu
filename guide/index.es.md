---
title: Inicio
hide:
  - navigation
  - toc
---

# Wavu: tu Python, dentro de tu visor de imágenes

*Wavu* significa **puente** en fiyiano. Conecta el visor donde miras tus
imágenes, **Fiji** o **napari**, con Python, donde viven herramientas como
Cellpose y scikit-image.

Piensa en un restaurante. **El visor es el camarero**: toma tu pedido (un
diálogo con unos pocos campos), lleva tus imágenes a la cocina como
**ingredientes** y te trae el plato a la mesa (imágenes nuevas, tablas,
contornos). **El worker es la cocina** que está detrás de la puerta, y cada
receta tiene **sus propios utensilios de cocina**, sus propias ollas,
cuchillos y hornos (los paquetes de Python), así que la receta de Cellpose
nunca toma prestadas (ni estropea) las herramientas de la receta del
desenfoque. La misma receta la puede servir cualquiera de los dos camareros.

![Los camareros (frontends): wavu-fiji, wavu-napari → La cocina (backend): worker de wavu, tu script.py PARAMS + run(), su propio entorno pixi (los utensilios de cocina) — opcional: toda la cocina en un contenedor (Docker / Apptainer)](assets/img/home-model.svg){ width="1000" }

**Una carpeta de script, dos visores.** Escribes `script.py` una vez; lo
ejecutan tanto los usuarios de Fiji como los de napari, siempre en el entorno
propio de la carpeta.

## Por qué existe Wavu { #why-this-exists }

- **Un solo entorno para todo acaba rompiéndose.** Instala con `pip` un plugin
  de Cellpose en el entorno de napari y puede traer otra versión de PyTorch,
  NumPy o Qt; el siguiente plugin fija otras, y napari o la herramienta de un
  colega deja de arrancar. Mezclar `conda` y `pip` en un mismo entorno lo
  empeora.
- **Python dentro de Fiji es aún más difícil.** El lenguaje de scripts propio
  de Fiji es Jython (Python 2.7, sin NumPy). Puentes como PyImageJ obligan a
  ajustar a mano las versiones de Java, conda y paquetes en cada máquina.
- **La respuesta de Wavu:** el visor se mantiene pequeño y limpio, y cada
  script se ejecuta en **su propio entorno pixi**, construido a partir de su
  propio `pixi.lock`. Los scripts no comparten paquetes, así que no pueden
  romperse entre sí ni romper napari o Fiji, y la misma carpeta se instala
  igual en todos los ordenadores.

## No solo un puente: análisis completos, con scripts

Wavu es también una **llamada a función** que pueden hacer tus propios
scripts. Un script de Groovy, una macro de ImageJ o un notebook de Python
recorre una carpeta, hace él mismo los pasos nativos (abrir, preprocesar,
medir, guardar) y solo le pasa a Wavu el paso pesado, como Cellpose; Wavu lo
ejecuta en su propio entorno y devuelve el resultado al script. Un script,
la carpeta entera, siempre igual.

[Flujos de trabajo con scripts :material-arrow-right:](workflows/index.md){ .md-button .md-button--primary }

## ¿Por dónde quieres empezar?

<div class="grid cards" markdown>

-   :material-lightbulb-outline:{ .lg .middle } **Entender el modelo**

    ---

    Camarero, cocina, utensilios de cocina: qué se ejecuta dónde, y por qué
    tus paquetes nunca chocan.

    [:octicons-arrow-right-24: Cómo funciona](model/what-is-wavu.md)

-   :material-pencil-outline:{ .lg .middle } **Escribir un script**

    ---

    Convierte tu notebook en una entrada de menú, con las pruebas primero.
    Consigue la plantilla lista para usar con un clic:

    [Abrir la plantilla en VS Code](vscode://vscode.git/clone?url=https%3A%2F%2Fgithub.com%2FOxford-Zeiss-Centre-of-Excellence%2FWavu-Script-Template.git){ .md-button .md-button--primary }

    [:octicons-arrow-right-24: Conseguir la plantilla](write/get-the-template.md)

-   :material-microscope:{ .lg .middle } **Usarlo en Fiji**

    ---

    Instala wavu-fiji, ejecuta tu primer script sobre una imagen de ejemplo
    y comparte herramientas con tu laboratorio en un solo archivo zip.

    [:octicons-arrow-right-24: wavu-fiji](fiji/install.md)

-   :material-layers-outline:{ .lg .middle } **Usarlo en napari**

    ---

    Arranca napari con el panel de Wavu; los resultados vuelven como capas
    Image, Labels y Shapes.

    [:octicons-arrow-right-24: wavu-napari](napari/install.md)

</div>

## Conviene saber

- **¿Cuántos datos?** El uso interactivo es una imagen que cabe en memoria,
  unos 1–2 GB. Con procesamiento por bloques y en flujo (OME-Zarr), Wavu
  puede manejar hasta unos 50 GB en un ordenador local, **con una advertencia
  importante**: Fiji y napari son visores basados en un lienzo, pensados para
  datos en memoria; durante un flujo solo ven una vista previa pequeña o el
  resultado final, van lentos y no son el lugar recomendado para dirigirlo.
  Por encima de unos 50 GB, usa un pipeline por lotes o en HPC.
- **Cada script tiene su propio entorno**, así que un script con PyTorch y
  otro que solo usa NumPy nunca se pelean.
- **¿Te pica la curiosidad por cómo está hecho?** La página de
  [arquitectura](model/architecture.md) explica el worker, su protocolo HTTP
  y cómo lo arranca un visor.

¿Quieres todos los detalles, desde la idea hasta un plugin de Fiji publicado?
Lee la
[guía completa en GitHub](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/blob/main/docs/tutorial-cellpose-plugin.md) (en inglés).
