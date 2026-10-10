# OpenBot DIY

<p align="center">
  <span>Русский</span> |
  <a href="README.md">English</a> |
  <a href="README.zh-CN.md">简体中文</a> |
  <a href="README.de-DE.md">Deutsch</a> |
  <a href="README.fr-FR.md">Français</a> |
  <a href="README.es-ES.md">Español</a> |
  <a href="README.ko-KR.md">한국어</a>
</p>

Терминология: [глоссарий OpenBot DIY](../../GLOSSARY.ru-RU.md).

Разработчики спроектировали корпус колёсного робота, рассчитанный на недорогие и доступные компоненты для любительской робототехники. Ниже приведены инструкции по самостоятельной сборке. Если у вас возникнут вопросы, обратитесь к команде проекта. Удачной сборки!

## Шасси

### 3D-печать

Для сборки OpenBot напечатайте и соедините перечисленные ниже детали.

#### Корпус робота

Выберите вариант корпуса с учётом своих требований и возможностей 3D-принтера. Вы также можете разработать собственную конструкцию. За основу можно взять следующие варианты:

- [Стандартный корпус (Regular Body)](cad/regular_body/README.ru-RU.md) — базовый вариант, разработанный командой проекта. Требуется платформа печати размером не менее 240 × 150 мм.
- [Компактный корпус (Slim Body)](cad/slim_body/README.ru-RU.md) — уменьшенный вариант без бамперов для принтеров с небольшим рабочим объёмом. При повороте деталей на 45° помещается на платформе 220 × 220 мм.
- [Корпус из склеиваемых частей (Glueable Body)](cad/glue_body/README.ru-RU.md) — модульный вариант автора @sloretz для ещё меньших принтеров. Отдельные части склеиваются после печати; достаточно платформы 150 × 140 мм.
- [Корпус Blocky](cad/block_body/README.ru-RU.md) — разработка @Christos-Ps с несколькими вариантами крышки, в том числе с увеличенным внутренним объёмом и поверхностью, совместимой с LEGO. Для печати требуется область 221 × 150 мм.

#### Держатель смартфона

Также напечатайте держатель смартфона, который крепится к корпусу:

- `phone_mount_bottom` — нижняя часть держателя ([STL](../phone_mount/phone_mount_bottom.stl), [STEP](../phone_mount/phone_mount_bottom.step)).
- `phone_mount_top` — верхняя часть держателя ([STL](../phone_mount/phone_mount_top.stl), [STEP](../phone_mount/phone_mount_top.step)).

#### Обработка после печати

Перед сборкой может потребоваться очистить напечатанные детали от остатков материала и поддержек.

<p float="left">
  <img src="../../docs/images/clean_3d_print_1.jpg" width="32%" />
  <img src="../../docs/images/clean_3d_print_2.jpg" width="32%" />
  <img src="../../docs/images/clean_3d_print_3.jpg" width="32%" />
</p>

### Альтернативные варианты

Если 3D-принтер недоступен, можно использовать готовый комплект колёсного шасси для Arduino. Такие комплекты содержат шасси, двигатели и принадлежности. Разработчики рекомендуют базовый комплект: значительная часть электроники и датчиков из более дорогих наборов для этой сборки не нужна. В исходной инструкции приведены следующие варианты:

- Perseids DIY Robot Smart Car Chassis Kit ([EU](https://www.amazon.de/dp/B07DNXBNHY), [US](https://www.amazon.com/dp/B07DNXBFQN)).
- SZDoit 4WD Smart Metal Robot Car Chassis Kit ([US](https://www.amazon.com/dp/B083K4RKBP), [AE](https://www.aliexpress.com/item/33048227237.html)).
- Joy-it Robot Car Kit 01 ([EU](https://www.amazon.de/dp/B073ZGJF28)).
- Smart Car Kit 4WD Smart Robot Car Chassis Kit ([AE](https://www.aliexpress.com/item/4001238626191.html)).

Также понадобится держатель смартфона. Один из вариантов:

- Phone Mount ([EU](https://www.amazon.de/dp/B06XDYJNSR), [US](https://www.amazon.com/dp/B09CY8MC2R)).

Можно самостоятельно изготовить шасси и держатель смартфона из подходящего материала, например дерева, картона или пенополистирола. Если вы выбрали такой способ, поделитесь фотографиями в [канале Slack](https://github.com/ob-f/OpenBot#contact). Ниже приведён пример автора [@custom-build-robots](https://custom-build-robots.com/roboter/openbot-dein-smartphone-steuert-ein-roboter-auto-chassis-bauen/13636):

<p float="left">
  <img src="../../docs/images/chassis_cardboard_1.jpg" width="32%" />
  <img src="../../docs/images/chassis_cardboard_2.jpg" width="32%" />
  <img src="../../docs/images/chassis_cardboard_3.jpg" width="32%" />
</p>

## Сборка

Предусмотрены два варианта монтажа электроники: на отдельных модулях (DIY) и на специализированной печатной плате (PCB). Вариант DIY использует распространённый драйвер двигателей L298N и рассчитан на пользователей с некоторым опытом работы с электроникой. Он требует большого числа соединений проводами, особенно при установке всех датчиков и светодиодов. Компоненты при этом широко доступны, поэтому разработчики рекомендуют DIY для единичной сборки или знакомства с проектом. Для сокращения числа проводов и упрощения монтажа разработана [специализированная печатная плата](pcb/README.ru-RU.md). Она удобна для более аккуратной компоновки или сборки нескольких OpenBot.

**Уточнение по варианту робота:** приведённые ниже подключения к выводам `D2`, `D3`, `D5` и другим относятся к Arduino Nano. Для `DIY_ESP32` назначение выводов задаётся отдельно в [прошивке](../../firmware/openbot/openbot.ino); выберите соответствующую конфигурацию по [инструкции по прошивке](../../firmware/README.ru-RU.md).

### Перечень компонентов (BOM)

В конструкции используются доступные компоненты для любительской электроники. Разработчики привели ссылки для Германии (EU) и США (US), рассчитанные на быструю доставку. При готовности ждать дольше компоненты можно искать на AliExpress (AE). Для сборки нужны следующие детали.

#### Обязательные компоненты

- 1 × Arduino Nano ([EU](https://www.amazon.de/dp/B01MS7DUEM), [US](https://www.amazon.com/dp/B00NLAMS9C), [AE](https://www.aliexpress.com/item/32866959979.html)).
- 4 × мотор-редуктор TT с колесом ([EU](https://www.conrad.de/de/p/joy-it-com-motor01-getriebemotor-gelb-schwarz-passend-fuer-einplatinen-computer-arduino-banana-pi-cubieboard-raspbe-1573543.html), [US](https://www.amazon.com/dp/B081YQM55P), [AE](https://www.aliexpress.com/item/4000126948489.html)).
- 3 × аккумулятор 18650 ([EU](https://www.conrad.de/de/p/conrad-energy-18650-usb-spezial-akku-18650-li-ion-3-7-v-1400-mah-1525536.html), [US](https://www.amazon.com/dp/B083K4XSKG), [AE](https://www.aliexpress.com/item/32352434845.html)).
- 1 × держатель аккумуляторов 18650 ([EU](https://www.amazon.de/dp/B075V25QJ9), [US](https://www.amazon.com/dp/B07DWQYD7H), [AE](https://www.aliexpress.com/item/33037738446.html)).
- 1 × кабель USB OTG ([EU](https://www.amazon.de/gp/product/B075M4CQHZ), [US](https://www.amazon.com/dp/B07LBHKTMM), [AE](https://www.aliexpress.com/item/10000330515850.html)).
- 1 × пружина или резиновое кольцо ([EU](https://www.amazon.de/gp/product/B01N30EAZO/), [US](https://www.amazon.com/dp/B008RFVWU2), [AE](https://www.aliexpress.com/item/33043769059.html)).
- 16 × винт M3 × 25 ([EU](https://www.amazon.de/dp/B07KFL3SSV), [US](https://www.amazon.com/dp/B07WJL3P3X), [AE](https://www.aliexpress.com/item/4000173341865.html)).
- 16 × гайка M3 ([EU](https://www.amazon.de/dp/B07JMF3KMD), [US](https://www.amazon.com/dp/B071NLDW56), [AE](https://www.aliexpress.com/item/32977174437.html)).
- 6 × винт M3 × 5 ([EU](https://www.amazon.de/dp/B01HBRG3W8), [US](https://www.amazon.com/dp/B07MBHMLL2), [AE](https://www.aliexpress.com/item/32892594230.html)).
- Соединительные провода Dupont ([EU](https://www.amazon.de/dp/B07KYHBVR7), [US](https://www.amazon.com/dp/B07GD2BWPY), [AE](https://www.aliexpress.com/item/4000766001685.html)).

#### Дополнительные компоненты

- 2 × датчик частоты вращения (speed sensor) ([EU](https://www.conrad.de/de/p/joy-it-sen-speed-erweiterungsmodul-passend-fuer-einplatinen-computer-arduino-banana-pi-cubieboard-raspberry-pi-pc-1646891.html), [US](https://www.amazon.com/dp/B081W2TY6Q), [AE](https://www.aliexpress.com/i/32850602744.html)).
- 1 × ультразвуковой дальномер (ultrasonic sensor) ([EU](https://www.amazon.de/dp/B00LSJWRXU), [US](https://www.amazon.com/dp/B0852V181G/), [AE](https://www.aliexpress.com/item/32713522570.html)).
- 1 × выключатель питания ([EU](https://www.amazon.de/dp/B07QB22J62), [US](https://www.amazon.com/dp/B01N2U8PK0), [AE](https://www.aliexpress.com/item/1000005699023.html)).
- 2 × оранжевый светодиод диаметром 5 мм ([EU](https://www.amazon.de/gp/product/B01NCL0UTQ), [US](https://www.amazon.com/dp/B077XD7MVB), [AE](https://www.aliexpress.com/item/4000329069943.html)).
- 1 × OLED-дисплей ([EU](https://www.amazon.de/dp/B079H2C7WH), [US](https://www.amazon.com/dp/B085NHM5TC), [AE](https://www.aliexpress.com/item/4001268387467.html)).

#### Компоненты для монтажа на отдельных модулях — вариант 1

- 1 × драйвер двигателей L298N ([EU](https://www.conrad.de/de/p/joy-it-motormodul-2-u-4-phasen-6-bis-12v-1573541.html), [US](https://www.amazon.com/dp/B085XSLKFQ), [AE](https://www.aliexpress.com/item/32994608743.html)).
- Дополнительно: два резистора по 150 Ом для светодиодов и резисторы 20 кОм и 10 кОм для делителя напряжения.
- Комплект: четыре мотор-редуктора TT с колёсами, два модуля L298N и провода Dupont ([US](https://www.amazon.com/dp/B07ZT619TD)).
- Комплект: четыре мотор-редуктора TT с колёсами, провода и винты ([US](https://www.amazon.com/dp/B07DRGTCTP)).

#### Компоненты для сборки на печатной плате — вариант 2

- 1 × [специализированная печатная плата](pcb/README.ru-RU.md).
- 5 × кабель с разъёмом Micro JST PH 2.0 ([EU](https://www.amazon.de/gp/product/B07449V33P), [US](https://www.amazon.com/dp/B09JZC28DP), [AE](https://www.aliexpress.com/item/32963304134.html)).

### Порядок сборки

**Совет:** нажмите на изображение, чтобы открыть его в полном разрешении в новой вкладке.

#### Вариант 1: монтаж на отдельных модулях (DIY)

<p float="left">
  <img src="../../docs/images/diy_parts.jpg" height="300" />
  <img src="../../docs/images/wiring_diagram.png" height="300" />
</p>

**Совет:** для упрощения соединений `5V` и `GND` можно изготовить небольшой распределитель питания. Припаяйте двухрядную штыревую колодку 6 × 2 к перфорированной макетной плате (perfboard), затем подключите её к `5V` и `GND` драйвера двигателей.

1. Припаяйте провода к двигателям. Если планируете использовать датчики частоты вращения, установите диски энкодеров на два передних мотор-редуктора.
   <p float="left">
     <img src="../../docs/images/add_wires_motor.jpg" width="32%" />
     <img src="../../docs/images/add_disk_motor.jpg" width="32%" />
   </p>
2. Подключите положительные и отрицательные провода двух левых двигателей к `OUT1` (+) и `OUT2` (−) платы L298N. Провода двух правых двигателей подключите к `OUT4` (+) и `OUT3` (−).
3. Закрепите мотор-редукторы восемью винтами M3 × 25 с гайками.
   <p float="left">
     <img src="../../docs/images/attach_motors_1.jpg" width="32%" />
     <img src="../../docs/images/attach_motors_2.jpg" width="32%" />
     <img src="../../docs/images/attach_motors_3.jpg" width="32%" />
   </p>
4. Закрепите модуль L298N четырьмя винтами M3 × 5.
5. При необходимости установите ультразвуковой дальномер. Замените его угловую контактную колодку прямой либо осторожно согните выводы.
   <p float="left">
     <img src="../../docs/images/sonar_front.jpg" width="32%" />
     <img src="../../docs/images/sonar_back.jpg" width="32%" />
     <img src="../../docs/images/sonar_bend_pins.jpg" width="32%" />
   </p>
6. При необходимости установите оранжевые светодиоды указателей поворота.
   <p float="left">
     <img src="../../docs/images/led_insert.jpg" width="32%" />
     <img src="../../docs/images/led_left.jpg" width="32%" />
     <img src="../../docs/images/led_right.jpg" width="32%" />
   </p>
7. Прикрепите нижнюю часть держателя смартфона к верхней панели корпуса двумя винтами M3 × 25 с гайками.
   <p float="left">
     <img src="../../docs/images/install_camera_mount_1.jpg" width="32%" />
     <img src="../../docs/images/install_camera_mount_2.jpg" width="32%" />
     <img src="../../docs/images/install_camera_mount_3.jpg" width="32%" />
   </p>
8. Вставьте верхнюю часть держателя и установите пружину или резиновое кольцо.
   <p float="left">
     <img src="../../docs/images/install_spring_1.jpg" width="32%" />
     <img src="../../docs/images/install_spring_2.jpg" width="32%" />
   </p>
9. Замените угловые контактные колодки датчиков частоты вращения прямыми либо осторожно согните выводы. Закрепите каждый датчик одним винтом M3 × 5.
   <p float="left">
     <img src="../../docs/images/install_speed_sensor_1.jpg" width="32%" />
     <img src="../../docs/images/install_speed_sensor_2.jpg" width="32%" />
     <img src="../../docs/images/install_speed_sensor_3.jpg" width="32%" />
   </p>
10. Закрепите держатель аккумуляторов, например застёжкой-липучкой.
    <p float="left">
      <img src="../../docs/images/install_battery_1.jpg" width="32%" />
      <img src="../../docs/images/install_battery_2.jpg" width="32%" />
      <img src="../../docs/images/install_battery_3.jpg" width="32%" />
    </p>
11. При необходимости установите выключатель последовательно в цепь питания.
    1. Вставьте выключатель в предназначенное для него отверстие до щелчка.
    2. Припаяйте красный провод (12 В) от держателя аккумуляторов и красный провод кабеля питания к двум контактам выключателя, по одному проводу на контакт. Соедините чёрные провода (`GND`) между собой и изолируйте соединение термоусадочной трубкой.
    3. Зафиксируйте провода лентой.
    <p float="left">
      <img src="../../docs/images/install_switch_1.jpg" width="32%" />
      <img src="../../docs/images/install_switch_2.jpg" width="32%" />
      <img src="../../docs/images/install_switch_3.jpg" width="32%" />
    </p>
12. При необходимости закрепите OLED-дисплей.
13. Подключите входы управления ШИМ (PWM) модуля L298N к выводам `D5`, `D6`, `D9` и `D10` Arduino.
14. Подключите питание датчиков частоты вращения и ультразвукового дальномера к `5V` и `GND`.
15. Подключите вывод `D0` левого датчика частоты вращения к `D2` Arduino, а вывод `D0` правого датчика — к `D3`.
16. Подключите выводы `Echo` и `Trigger` ультразвукового дальномера к `D11` и `D12` Arduino соответственно.
17. При необходимости подключите светодиоды к `D4` (левый) и `D7` (правый), а также к `GND`. Для ограничения тока разработчики рекомендуют включить последовательно с каждым светодиодом резистор 150 Ом.
18. При необходимости подключите делитель напряжения к `A7` Arduino. Он используется для измерения напряжения аккумуляторной батареи.
19. При необходимости подключите OLED-дисплей с контроллером SSD1306 к Arduino Nano по шине I2C:
    1. Соедините `VIN` и `GND` дисплея с `5V` и `GND` соответственно.
    2. Соедините `SCL` дисплея с `A5`.
    3. Соедините `SDA` дисплея с `A4`.
20. Подключите провода питания к `+12V` и `GND` модуля L298N.
21. Подключите USB-кабель к Arduino и выведите его через крышку корпуса.
22. Вставьте шесть гаек M3 в нижнюю панель и закрепите крышку шестью винтами M3 × 25.
23. Установите колёса.

#### Вариант 2: специализированная печатная плата (PCB)

1. Припаяйте к двигателям провода с разъёмами Micro JST PH 2.0. Если планируете использовать датчики частоты вращения, установите диски энкодеров на два передних мотор-редуктора.
   <p float="left">
     <img src="../../docs/images/add_wires_motor.jpg" width="32%" />
     <img src="../../docs/images/add_disk_motor.jpg" width="32%" />
   </p>
2. Закрепите мотор-редукторы восемью винтами M3 × 25 с гайками.
   <p float="left">
     <img src="../../docs/images/attach_motors_1.jpg" width="32%" />
     <img src="../../docs/images/attach_motors_2.jpg" width="32%" />
     <img src="../../docs/images/attach_motors_3.jpg" width="32%" />
   </p>
3. Подключите два левых двигателя к разъёмам `M3` и `M4`, а два правых — к `M1` и `M2`.
   <p float="left">
     <img src="../../docs/images/connect_motors_pcb.jpg" width="32%" />
   </p>
4. Закрепите печатную плату четырьмя винтами M3 × 5. Для крепления двигателей используются восемь винтов M3 × 25 с гайками, указанные в шаге 2.
   <p float="left">
     <img src="../../docs/images/attach_pcb.jpg" width="32%" />
     <img src="../../docs/images/chassis_motors_pcb.jpg" width="32%" />
   </p>
5. Выполните шаги 5–12 из варианта DIY.
6. Подключите ультразвуковой дальномер (`VCC/+`, `Trig`, `Echo`, `GND/-`) к четырёхконтактной колодке с маркировкой `SONAR` на плате.
   <p float="left">
     <img src="../../docs/images/connect_sonar_sensor.jpg" width="32%" />
   </p>
7. Подключите левый и правый указатели поворота — оранжевые светодиоды — к двухконтактным колодкам `SIGNAL_L` и `SIGNAL_R`. Длинный вывод светодиода соответствует «+», короткий — «−».
8. Подключите левый и правый датчики частоты вращения (`VCC/+`, `GND/-`, `D0`) к трёхконтактным колодкам `SPEED_L` и `SPEED_R`.
9. При необходимости подключите OLED-дисплей с контроллером SSD1306 к колодке `IO2` на плате:
   1. Соедините `VIN` и `GND` дисплея с `5V` и `GND` соответственно.
   2. Соедините `SCL` дисплея с `A5`.
   3. Соедините `SDA` дисплея с `A4`.
10. Подключите провода питания к разъёму `Vin` платы — Micro JST PH 2.0.
11. Выполните шаги 21–23 из варианта DIY.

## Следующий шаг

Загрузите [прошивку микроконтроллера](../../firmware/README.ru-RU.md).
