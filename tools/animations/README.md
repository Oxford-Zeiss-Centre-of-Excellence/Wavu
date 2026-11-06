# Guide animations

Generators for the animated SVGs on the "Large data: stream analysis" page
(`guide/assets/img/stream/`). Plain Node.js, no dependencies:

```sh
node tools/animations/sub-kitchens.js        guide/assets/img/stream/sub-kitchens.svg
node tools/animations/zarr-chunking.js       guide/assets/img/stream/zarr-chunking.svg
node tools/animations/stream-loading.js      guide/assets/img/stream/stream-loading.svg
node tools/animations/parallel-processing.js guide/assets/img/stream/parallel-processing.svg
```

The SVGs carry no visible text (they are shared by all nine languages; the
captions are in Markdown), except the code names `data.ome.zarr`, `/image` and
`/label` in `stream-loading.svg`. SMIL animation only, site palette.
