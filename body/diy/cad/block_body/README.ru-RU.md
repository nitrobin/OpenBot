# Корпус Blocky с увеличенным внутренним объёмом и совместимостью с LEGO

<p align="center">
  <span>Русский</span> |
  <a href="README.md">English</a> |
  <a href="README.zh-CN.md">简体中文</a> |
  <a href="README.de-DE.md">Deutsch</a> |
  <a href="README.fr-FR.md">Français</a> |
  <a href="README.es-ES.md">Español</a> |
  <a href="README.ko-KR.md">한국어</a>
</p>

Терминология: [глоссарий OpenBot DIY](../../../../GLOSSARY.ru-RU.md).

Этот вариант шасси имеет увеличенную высоту, чтобы упростить размещение электроники, и крышку, совместимую с LEGO. По прочности конструкция сопоставима со [стандартным корпусом](../regular_body/README.ru-RU.md). Дополнительные возможности включают увеличенное пространство внутри корпуса OpenBot, совместимую с LEGO крышку для игр и обучения, а также габариты, подходящие для небольших платформ печати. При этом бамперы сохранены.

![CAD-модель корпуса Blocky](../../../../docs/images/block_cad.jpg)

## Детали

Напечатайте нижнюю панель и один из вариантов крышки:

- `block_body_bottom` ([STL](block_body_bottom.stl), [STEP](block_body_bottom.step)) — нижняя панель корпуса.
- `block_body_top` ([STL](block_body_top.stl), [STEP](block_body_top.step)) — стандартная крышка.
- `block_body_top_lego` ([STL](block_body_top_lego.stl), [STEP](block_body_top_lego.step)) — стандартная крышка с поверхностью, совместимой с LEGO.
- `block_body_top_big` ([STL](block_body_top_big.stl), [STEP](block_body_top_big.step)) — увеличенная крышка с дополнительным объёмом для электроники.
- `block_body_top_big_lego` ([STL](block_body_top_big_lego.stl), [STEP](block_body_top_big_lego.step)) — увеличенная крышка с поверхностью, совместимой с LEGO.

Для этих деталей требуется платформа печати размером не менее 221 × 150 мм.

**Уточнение к исходнику:** последний вариант в английском перечне подписан как `block_body_top_lego`, однако его файлы называются `block_body_top_big_lego`. Здесь указано имя, соответствующее STL- и STEP-файлам.

## Параметры печати

Для наилучшего результата рекомендуются следующие настройки:

- Высота слоя (`Layer Height`): 0,2 мм.
- Число линий стенки (`Wall Line Count`): 3. Увеличение их числа повышает прочность крупных поверхностей.
- Число верхних слоёв (`Top Layers`): 5.
- Число нижних слоёв (`Bottom Layers`): 4.
- Плотность заполнения (`Infill`): 25 %.
- Рисунок заполнения (`Infill Pattern`): концентрический (`Concentric`). По опыту автора, он позволяет сократить время печати и расход пластика.
- Скорость печати (`Print Speed`): 50 мм/с.
- Создание поддержек (`Generate Support`): включено (`Yes`).
- Рисунок поддержек (`Support Pattern`): концентрический (`Concentric`).
- Плотность поддержек (`Support Density`): 15 %.
- Кайма для поддержек (`Enable Support Brim`): включена (`Yes`).
- Тип сцепления с платформой (`Build Plate Adhesion Type`): без дополнительных структур (`None`).

Удачной сборки!

![Корпус Blocky](../../../../docs/images/block_body.jpg)
