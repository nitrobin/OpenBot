# OpenBot DIY: изображения плат во вкладке Breadboard

Открой нужный файл в Fritzing и выбери **Breadboard**. Платы, контакты, резисторы и провода — отдельные редактируемые объекты. Все определения компонентов включены в `.fzz`.

| Контроллер | Файл Fritzing | Картинка | Векторное превью |
| --- | --- | --- | --- |
| Arduino Nano ATmega328P | [openbot-diy-nano-breadboard.fzz](openbot-diy-nano-breadboard.fzz) | [PNG](openbot-diy-nano-breadboard.png) | [SVG](openbot-diy-nano-breadboard_breadboard.svg) |
| ESP32 DevKit ESP-WROOM-32, 38 контактов | [openbot-diy-esp32-breadboard.fzz](openbot-diy-esp32-breadboard.fzz) | [PNG](openbot-diy-esp32-breadboard.png) | [SVG](openbot-diy-esp32-breadboard_breadboard.svg) |

![Arduino Nano: вид Breadboard](openbot-diy-nano-breadboard.png)

![ESP32: вид Breadboard](openbot-diy-esp32-breadboard.png)

## Как пользоваться

Arduino Nano показана **сверху, USB Mini-B вверх**. Порядок двух рядов контактов соответствует [официальной распиновке Nano](https://docs.arduino.cc/resources/pinouts/A000005-full-pinout.pdf). `D5` Arduino Nano соединён с `IN1` L298N, `D6` — с `IN2`, `D9` — с `IN3`, `D10` — с `IN4`. Контакт `VIN` Arduino Nano свободен; делитель батареи подключён к `A7` Arduino Nano.

ESP32 показана **сверху, USB вниз**. Порядок 38 контактов соответствует [ESP32-DevKitC](https://documentation.espressif.com/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html#header-block). Подписи `IO13`, `IO12`, `IO15`, `IO2` на изображении ESP32 означают `GPIO13`, `GPIO12`, `GPIO15`, `GPIO2`; они соединены соответственно с `IN1`, `IN2`, `IN3`, `IN4` L298N. Подписи `SDx`, `CMD`, `CLK` относятся к выводам Flash — они свободны. У похожих плат с 30 или 36 контактами порядок другой.

L298N изображён с радиатором вверх, клеммами двигателей по бокам и разъёмом управления внизу; расположение групп соответствует [руководству Handson Technology](https://handsontec.com/dataspecs/L298N%20Motor%20Driver.pdf). Корпуса L298N, LM393, OLED и DC/DC нарисованы как примеры модулей. Размеры иллюстративные. Перед монтажом сверяй **маркировку конкретной платы**, особенно порядок `VCC`, `GND`, `DO` / `D0`, `AO` / `A0` на LM393 и `VCC`, `GND`, `SCL`, `SDA` на OLED. Для LM393 с тремя контактами используются `VCC`, `GND`, `DO` / `D0`; аналоговый выход свободен.

Цвета совпадают с предыдущими схемами; [таблица цветов](WIRE-COLORS.ru-RU.md) описывает назначение проводов. Чёрный — `GND` (общий провод). Цветные точки отмечают электрические ответвления. Пересечение линий **без точки** не соединяет провода. `A (+)` и `K (−)` подписаны у выводов каждого светодиода. Цветовые полосы резисторов показывают номинал и допуск 1 %; номиналы также указаны текстом.

Условия питания и настройки прошивки описаны в [инструкции Nano](README.ru-RU.md) и [инструкции ESP32](README.esp32.ru-RU.md). Вариант Nano сохраняет питание исходной схемы, которое нужно проверить для батареи 3S и конкретных TT-моторов. В варианте ESP32 сохранены два DC/DC, делитель `Echo`, подтяжки LM393 к `3V3` и снятая перемычка `5V-EN` L298N. Перемычки `ENA` и `ENB` L298N установлены в обоих вариантах.

## Файлы и проверка

В новых файлах вкладка **Schematic** сохранена из соответствующей прежней схемы. Прежние `.fzz`, включая ручную компоновку Nano, сохранены отдельно. Электрические цепи обоих видов совпадают: 37 у Nano и 45 у ESP32, включая свободные контакты. PNG и SVG экспортированы штатным Fritzing 1.0.8.

- `source-breadboard-nano/` и `source-breadboard-esp32/` содержат распакованные `.fz`, определения компонентов, SVG и `nets.json`.
- `generate_breadboard.py` создаёт оба варианта на основе прежних `.fzz`, проверяет назначения по прошивке, сравнивает электрические цепи каждого вида с исходными `nets.json` и проверяет сохранность Schematic.
- Каждая точка ответвления — отдельный контакт Fritzing, соединённый с проводами. Её можно перемещать вместе с подключёнными концами проводов.

```sh
python3 body/diy/fritzing/generate_breadboard.py
```

Повторный запуск заменяет новые `*-breadboard.fzz` и их распакованные исходники. Ручные правки сначала сохраняй отдельно. Прежние `openbot-diy-nano.fzz` и `openbot-diy-esp32.fzz` скрипт только читает.

Created with [Fritzing](https://fritzing.org/). Изображения компонентов нарисованы для этой схемы и распространяются по [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/). Скрипт — на условиях лицензии OpenBot в корне репозитория.
