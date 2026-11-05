---
title: Wavu
hide:
  - navigation
  - toc
---

# Wavu: tu Python, dentro de Fiji

*Wavu* significa **puente** en fiyiano. Conecta Fiji, donde miras tus
imágenes, con Python, donde viven herramientas como Cellpose y scikit-image.

Piensa en un restaurante. **Fiji es el camarero**: toma tu pedido (un diálogo
con unos pocos campos) y te trae el plato a la mesa (imágenes nuevas, tablas,
contornos). **El worker es la cocina** que está detrás de la puerta, y cada
receta tiene **su propia despensa**, así que la receta de Cellpose nunca toma
prestados (ni estropea) los ingredientes de la receta del desenfoque.

```mermaid
flowchart LR
    subgraph FIJI["Fiji (el camarero)"]
        D["Diálogo<br/>creado a partir de PARAMS"]:::fiji
        R["Resultados<br/>imágenes · tablas · ROI"]:::fiji
    end
    subgraph PY["Worker (la cocina)"]
        S["tu script.py"]:::script
    end
    E[("su propio entorno pixi<br/>(la despensa)")]:::env

    D -- "tu pedido" --> S
    S -.- E
    S -- "el plato + Log en directo" --> R

    classDef fiji   fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef worker fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef script fill:#fff3e0,stroke:#ef6c00,color:#e65100
    classDef env    fill:#f3e5f5,stroke:#6a1b9a,color:#4a148c
    style FIJI fill:#f5f9ff,stroke:#90caf9
    style PY   fill:#f6fbf6,stroke:#a5d6a7
```

## ¿Qué quieres hacer?

<div class="grid cards" markdown>

-   :material-play-circle-outline:{ .lg .middle } **Usar un script**

    ---

    Instala Wavu en Fiji y ejecuta tu primer script de Python sobre una
    imagen de ejemplo. Sin terminal.

    [:octicons-arrow-right-24: Empieza aquí](start/what-is-wavu.md)

-   :material-pencil-outline:{ .lg .middle } **Escribir un script**

    ---

    Convierte tu notebook en una entrada del menú de Fiji. Consigue la
    plantilla lista para usar con un clic:

    [Abrir la plantilla en VS Code](vscode://vscode.git/clone?url=https%3A%2F%2Fgithub.com%2FOxford-Zeiss-Centre-of-Excellence%2FWavu-Script-Template.git){ .md-button .md-button--primary }

    [:octicons-arrow-right-24: Cómo funciona](write/get-the-template.md)

-   :material-share-variant-outline:{ .lg .middle } **Compartir un script**

    ---

    Da tu herramienta a todo el laboratorio en un solo archivo zip.
    Publicarla para todo el mundo es opcional.

    [:octicons-arrow-right-24: Compartir con tu laboratorio](share/with-your-lab.md)

</div>

## Conviene saber

- **Datos pequeños e interactivos.** Una imagen que quepa en memoria, hasta
  aproximadamente 1–2 GB. Para datos enormes, usa un flujo de trabajo por
  lotes o en un clúster (HPC).
- **Cada script tiene su propio entorno**, así que un script con PyTorch y
  otro que solo usa NumPy nunca se pelean.

¿Quieres todos los detalles, desde la idea hasta un plugin publicado? Lee la
[guía completa en GitHub](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/blob/main/docs/tutorial-cellpose-plugin.md) (en inglés).
