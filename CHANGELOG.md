# Changelog

## 0.1.0 (2026-11-22)


### Features

* **cadastro:** fusão de imagem 360°, cadastro BDGD e mapa OSM por rua ([#14](https://github.com/JulianoFJ/ip-mobile-survey/issues/14)) ([#22](https://github.com/JulianoFJ/ip-mobile-survey/issues/22)) ([2b5d46f](https://github.com/JulianoFJ/ip-mobile-survey/commit/2b5d46f62749bf0e25ade6a711e15b1e4269ec82))
* **detection:** detecções em ângulos e junção entre vistas ([#17](https://github.com/JulianoFJ/ip-mobile-survey/issues/17)) ([cb4b369](https://github.com/JulianoFJ/ip-mobile-survey/commit/cb4b369976a529b38cdf0d771c54745b6b263829)), closes [#15](https://github.com/JulianoFJ/ip-mobile-survey/issues/15)
* **detection:** detector zero-shot OWLv2 e avaliação visual ([#15](https://github.com/JulianoFJ/ip-mobile-survey/issues/15)) ([#19](https://github.com/JulianoFJ/ip-mobile-survey/issues/19)) ([b9c3df0](https://github.com/JulianoFJ/ip-mobile-survey/commit/b9c3df0e507fbb1423b18a81e8ae9f5b342ec903))
* **extraction:** atributos de via e malha a partir dos postes e luminárias ([#21](https://github.com/JulianoFJ/ip-mobile-survey/issues/21)) ([885c194](https://github.com/JulianoFJ/ip-mobile-survey/commit/885c1943ff811d3e3746e2e2c14c1c25f3d529cf))
* **extraction:** larguras da via pelo chão segmentado e frente do veículo medida ([#23](https://github.com/JulianoFJ/ip-mobile-survey/issues/23)) ([19555e2](https://github.com/JulianoFJ/ip-mobile-survey/commit/19555e28a8f580563b916fc915d8a83a11e22723))
* **geometry:** triangulação de postes com fotos vizinhas e cadastro BDGD das 17 cidades ([#29](https://github.com/JulianoFJ/ip-mobile-survey/issues/29)) ([5856b76](https://github.com/JulianoFJ/ip-mobile-survey/commit/5856b7691f32de5bd23abf85e7d49b1e96d9a8a8))
* **geometry:** vistas planas a partir do panorama equirretangular ([#16](https://github.com/JulianoFJ/ip-mobile-survey/issues/16)) ([d88d9e6](https://github.com/JulianoFJ/ip-mobile-survey/commit/d88d9e612d1c7b9f606bddf34f65ac0c9a844a0d)), closes [#15](https://github.com/JulianoFJ/ip-mobile-survey/issues/15)
* **golden:** dataset panoramax-br-v0 com 68 panoramas 360° urbanos ([#15](https://github.com/JulianoFJ/ip-mobile-survey/issues/15)) ([#18](https://github.com/JulianoFJ/ip-mobile-survey/issues/18)) ([a3a962d](https://github.com/JulianoFJ/ip-mobile-survey/commit/a3a962d48a3b68f91e0afea56af1ef4078a68781))
* **inspection:** contrato da planilha de inspeção e exportação .xlsx ([#13](https://github.com/JulianoFJ/ip-mobile-survey/issues/13)) ([9249aa3](https://github.com/JulianoFJ/ip-mobile-survey/commit/9249aa3e014c64c8ebed1754b60683fe5bd93443)), closes [#12](https://github.com/JulianoFJ/ip-mobile-survey/issues/12)
* **nbr5101:** malha de cálculo por vão ([#10](https://github.com/JulianoFJ/ip-mobile-survey/issues/10)) ([a23b6ff](https://github.com/JulianoFJ/ip-mobile-survey/commit/a23b6ff26fb109d46973d8cd70ab3e27b1b88315)), closes [#8](https://github.com/JulianoFJ/ip-mobile-survey/issues/8)
* **web:** correção das larguras na planta da via (rótulos de treino) ([#28](https://github.com/JulianoFJ/ip-mobile-survey/issues/28)) ([674c778](https://github.com/JulianoFJ/ip-mobile-survey/commit/674c77809758e30659a6a664ecc4d42120ecf8b5))
* **web:** módulo de inspeção de campo na pilha do Ignis ([#20](https://github.com/JulianoFJ/ip-mobile-survey/issues/20)) ([4156eaf](https://github.com/JulianoFJ/ip-mobile-survey/commit/4156eafab6656940d64ab95a6cc2bfdc538a64cf))


### Bug Fixes

* **nbr5101:** malha da calçada conforme NBR 5101:2024 (5.1.2.1) ([#11](https://github.com/JulianoFJ/ip-mobile-survey/issues/11)) ([3adfa3c](https://github.com/JulianoFJ/ip-mobile-survey/commit/3adfa3cb3cd68a6e44b073df7613919d5c08169d)), closes [#8](https://github.com/JulianoFJ/ip-mobile-survey/issues/8)
* **web:** corrige falhas de segurança do next, maplibre-gl, postcss e vitest ([#27](https://github.com/JulianoFJ/ip-mobile-survey/issues/27)) ([0c12466](https://github.com/JulianoFJ/ip-mobile-survey/commit/0c12466306e1d509850822370b11f165c07f0e41))
