# Стандартный корпус (Regular Body)

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

![Сборка корпуса](../../../../docs/images/assembly.gif)

## Детали

Для сборки OpenBot напечатайте следующие детали:

- `body_bottom` — нижняя панель корпуса ([STL](body_bottom.stl), [STEP](body_bottom.step)).
- `body_top` — крышка корпуса ([STL](body_top.stl), [STEP](body_top.step)).

Для этих деталей требуется платформа печати (build plate) размером не менее 240 × 150 мм.

## Параметры печати

На Ultimaker S5 хорошие результаты получены со следующими настройками:

- Высота слоя (layer height): 0,2 мм.
- Толщина стенки (wall thickness): 1,5 мм.
- Плотность заполнения (infill density): 20 %.
- Рисунок заполнения (infill pattern): сетка (`Grid`).
- Скорость печати: 80 мм/с.
- Поддержки (supports): не требуются.

Шасси удалось напечатать из PLA, ABS и CPE. По опыту разработчиков, изменение параметров печати не сильно влияло на результат. Тем не менее снижение скорости печати и высоты слоя позволяет улучшить качество, если вы готовы потратить больше времени. Добавление поддержек также может улучшить результат, но после печати их потребуется удалить.
