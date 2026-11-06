# Changelog

## 0.1.0 (2026-11-06)


### Features

* Fiji client scripts (no jar) and headless Fiji smoke test ([af02af8](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/commit/af02af8ff0d0505f8fdeb397ee1991ef2d108a6c))
* script template (Gaussian blur) and cellpose nuclei example ([33f23be](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/commit/33f23be9b35d15d35944a4e2edbe7ab32e878014))
* scripted pipelines (DAG) — table inputs, example steps, tested Fiji and napari pipelines; stream-analysis guide ([1c9f5b9](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/commit/1c9f5b988b089d4da0d1514c2f9788472e4eb14f))
* Wavu core + two frontends (wavu-fiji, wavu-napari); remote/container connect; reworked guide ([d2e93b1](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/commit/d2e93b1e88ae438ecf803d5f8d6582c8fd9a84ab))
* wavu package, installed script folders with Fiji menu stubs, and a release workflow in new scripts ([2eb7d11](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/commit/2eb7d11281b76804c620dbdd99704d588309664b))
* Wavu skill for AI coding agents, with an "AI agents" guide page ([8de56a7](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/commit/8de56a7ee2e5341056d76af9dc14ba535da94257))
* wavu worker with stdlib HTTP/SSE server, script contract, FakeCtx and CLI ([57f7f9a](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/commit/57f7f9aa23d4dca067b7b3e6aa19115e31aba2f3))
* wavu.client, a Python client for wavu-worker; VS Code extension recommendations in the template ([df1654f](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/commit/df1654ff01d9e10ab7df501557a01b95d680b094))


### Bug Fixes

* **examples:** cellpose_nuclei pins numpy&lt;2.1 so its environment solves ([92494fa](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/commit/92494fa29be49838667d78f6614f4e5a1bba1499))
* **worker:** no more hang on Windows when scripts load C extensions; Fiji scripting API; guide rework ([09c6256](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/commit/09c6256fc7e655477b643eb1e1843888c16ff29a))
