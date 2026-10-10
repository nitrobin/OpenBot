# Компактный корпус (Slim Body)

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

Рабочий объём (build volume) некоторых 3D-принтеров слишком мал для печати полноразмерного корпуса OpenBot. В этой папке находится его компактный вариант. Если повернуть детали на 45°, их можно напечатать на платформе размером 220 × 220 мм.

![Компактный корпус](../../../../docs/images/slim_body.jpg)

## Детали

1. `slim_body_bottom` — нижняя панель корпуса ([STL](slim_body_bottom.stl), [STEP](slim_body_bottom.step)).
2. `slim_body_top` — крышка корпуса ([STL](slim_body_top.stl), [STEP](slim_body_top.step)).

Чтобы детали поместились на платформе, может потребоваться увеличить доступную область печати с помощью следующих настроек:

- Установите тип сцепления с платформой `Build Plate Adhesion Type` в значение `None`. Кайма (brim), юбка (skirt) и подложка (raft) увеличивают габариты задания на печать.
- Отключите стартовую каплю пластика (prime blob) в разделе `Build Plate`.
- Отключите второй экструдер, если он есть у принтера.

Если доступная область немного больше — 223 × 223 мм, — можно напечатать `slim_body_top_rim` ([STL](slim_body_top_rim.stl), [STEP](slim_body_top_rim.step)). У этой крышки увеличен бортик, благодаря чему её проще снимать.
