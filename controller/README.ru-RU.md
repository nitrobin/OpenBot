# Пульты управления OpenBot

<p align="center">
  <span>Русский</span> |
  <a href="README.md">English</a> |
  <a href="README.zh-CN.md">简体中文</a> |
  <a href="README.de-DE.md">Deutsch</a> |
  <a href="README.fr-FR.md">Français</a> |
  <a href="README.es-ES.md">Español</a> |
  <a href="README.ko-KR.md">한국어</a>
</p>

Терминология: [глоссарий OpenBot DIY](../GLOSSARY.ru-RU.md).

Роботом OpenBot можно управлять несколькими способами.

## Игровой контроллер Bluetooth

Самый простой способ — подключить игровой контроллер по Bluetooth. По сведениям разработчиков, большинство таких контроллеров должно работать. Команда проверила [контроллер PS4](https://www.amazon.de/-/en/Sony-Dualshock-Gamepad-Playstation-Black/dp/B01LYWPQUN), [контроллер Xbox](https://www.amazon.de/-/en/QAT-00002/dp/B07SDFLVKD) и несколько контроллеров сторонних производителей, включая [X3](https://www.amazon.com/Controller-Wireless-Joystick-Bluetooth-Android/dp/B08H5MM64P).

## [Пульт на Node.js](node-js)

Смартфон и компьютер, например ноутбук или Raspberry Pi, должны быть подключены к одной сети Wi-Fi. После установления соединения доступен видеопоток с малой задержкой; управлять роботом можно клавишами в браузере.

Благодарим Ivo Zivkov ([izivkov@gmail.com](mailto:izivkov@gmail.com)) за разработку.

## [Пульт на Python](python)

Смартфон и компьютер, например ноутбук или Raspberry Pi, должны быть подключены к одной сети Wi-Fi. После установления соединения доступен видеопоток RTSP; управлять роботом можно с клавиатуры из терминала. Скрипт Python можно использовать как основу для собственного пульта управления.

Благодарим Ivo Zivkov ([izivkov@gmail.com](mailto:izivkov@gmail.com)) за разработку.

## [Приложение пульта на Flutter](flutter)

Это приложение выполняет функции пульта дистанционного управления OpenBot, аналогично игровому контроллеру Bluetooth, например PS3/PS4 или Xbox. Оно работает на отдельном Android- или iOS-устройстве и, помимо управления, поддерживает передачу видео и звука в реальном времени.

## [Пульт на веб-сервере](web-server)

Это облачный вариант локального пульта на Node.js. Он позволяет оператору дистанционно управлять OpenBot через интернет (teleoperation).
