<a href="https://www.openbot.org/" target="_blank">
  <img align="center" alt="Баннер OpenBot" width="100%" src="docs/images/banner.jpg" />
</a>

<h1 align="center"><a>Превращаем смартфоны в роботов</a></h1>

<p align="center">
   <img alt="Сборка исходного OpenBot" src="https://img.shields.io/github/actions/workflow/status/ob-f/OpenBot/gradle.yml?branch=master">
   <img alt="Задачи исходного OpenBot" src="https://img.shields.io/github/issues/ob-f/OpenBot">
   <img alt="Запросы на слияние исходного OpenBot" src="https://img.shields.io/github/issues-pr/ob-f/OpenBot">
   <img alt="Форки исходного OpenBot" src="https://img.shields.io/github/forks/ob-f/OpenBot">
   <img alt="Звёзды исходного OpenBot" src="https://img.shields.io/github/stars/ob-f/OpenBot">
   <img alt="Загрузки исходного OpenBot" src="https://img.shields.io/github/downloads/ob-f/OpenBot/total">
   <img alt="Размер исходного OpenBot" src="https://img.shields.io/github/repo-size/ob-f/OpenBot">
   <img alt="Лицензия исходного OpenBot" src="https://img.shields.io/github/license/ob-f/OpenBot">
</p>

<p align="center">
  <span>Русский</span> |
  <a href="README.en-US.md">English</a> |
  <a href="README.zh-CN.md">简体中文</a> |
  <a href="README.de-DE.md">Deutsch</a> |
  <a href="README.fr-FR.md">Français</a> |
  <a href="README.es-ES.md">Español</a> |
  <a href="README.ko-KR.md">한국어</a>
</p>

Это публичный форк [ob-f/OpenBot](https://github.com/ob-f/OpenBot). Основной README переведён на русский; английская версия сохранена в [README.en-US.md](README.en-US.md). Значки выше показывают состояние исходного проекта.

OpenBot использует смартфоны в качестве «мозга» недорогих роботов. Разработчики спроектировали небольшую электрическую платформу стоимостью около 50 долларов, которая служит корпусом робота. Программное обеспечение для смартфонов на Android поддерживает сложные задачи робототехники, включая следование за человеком и автономную навигацию в реальном времени.

## Начало работы с OpenBot

- Прочитайте [отказ от ответственности](DISCLAIMER.ru-RU.md).
- Соберите [корпус робота](body/README.ru-RU.md) по [инструкции OpenBot DIY](body/diy/README.ru-RU.md).
- Загрузите [прошивку микроконтроллера](firmware/README.ru-RU.md).
- Установите [приложения для Android](android/README.ru-RU.md).
- Выберите [пульт управления](controller/README.ru-RU.md).
- Программируйте робота в [среде Playground](open-code/README.md).
- Обучите собственную [модель управления движением](policy/README.md).

Для русской документации по сборке и запуску используйте [глоссарий терминов](GLOSSARY.ru-RU.md).

## Ветки форка

- `main-fork` — основная ветка этого репозитория. В ней находятся русский README и все пользовательские правки.
- `main` — чистая копия `master` из [исходного репозитория](https://github.com/ob-f/OpenBot). Она предназначена для синхронизации с upstream; пользовательские правки следует делать в `main-fork`.

Обновляйте `main` вручную, затем возвращайтесь в рабочую ветку:

```bash
git switch main
git pull --ff-only upstream master
git push origin main
git switch main-fork
```

Обновления из `main` можно переносить в `main-fork` командой `git merge main`, находясь в ветке `main-fork`.

## Получение исходного кода

- Скачайте этот форк как [ZIP-архив](https://github.com/nitrobin/OpenBot/archive/refs/heads/main-fork.zip) и распакуйте его в выбранную папку.
- Или клонируйте форк из GitHub:

  ```bash
  git clone --branch main-fork https://github.com/nitrobin/OpenBot.git
  ```

- После первого клонирования добавьте исходный репозиторий как `upstream` для получения обновлений:

  ```bash
  git remote add upstream https://github.com/ob-f/OpenBot.git
  ```

- Исходный проект доступен в [ob-f/OpenBot](https://github.com/ob-f/OpenBot). Если вы хотите внести изменения в него, ознакомьтесь с [правилами участия](CONTRIBUTING.md) и создайте собственный форк.

## Видео

<a href="https://www.youtube.com/watch?v=RbzPXywJifA" >
  <img align="center" width="300" alt="Видео об OpenBot на YouTube" src="https://img.youtube.com/vi/RbzPXywJifA/hqdefault.jpg" />
</a>

<a href="https://www.youtube.com/watch?v=qc8hFLyWDOM" >
  <img align="center" width="300" alt="Видео об OpenBot на YouTube" src="https://img.youtube.com/vi/qc8hFLyWDOM/hqdefault.jpg" />
</a>

## Интересные проекты на базе OpenBot

На базе OpenBot уже создано множество интересных проектов. Ниже приведена небольшая подборка. Нажмите на изображение, чтобы перейти к соответствующему проекту.

<p float="left">
  <a href="https://www.thingiverse.com/thing:4670884" target="_blank">
    <img alt="OpenBot на гусеницах" width="24%" src="docs/images/openbot_tank.jpg" />
  </a>
  <a href="https://diyrobocars.com/2020/12/14/an-improved-version-of-the-intel-openbot" target="_blank">
    <img alt="OpenBot с приводом на два колеса" width="24%" src="docs/images/openbot_2wd.jpg" />
  </a>
  <a href="https://custom-build-robots.com/raspberry-pi-robot-cars/openbot-your-smartphone-controls-a-robot-car-introduction/13860?lang=en" target="_blank">
    <img alt="OpenBot с картонным корпусом" width="24%" src="docs/images/chassis_cardboard_1.jpg" />
  </a>
  <a href="https://www.youtube.com/watch?v=PEj8jWapGt4" target="_blank">
    <img alt="OpenBot в виде малыша Йоды" width="24%" src="docs/images/openbot_yoda.jpg" />
  </a>
</p>

## Связь с сообществом OpenBot

- Присоединяйтесь к [каналу Slack](https://join.slack.com/t/openbot-community/shared_invite/zt-jl8ygxqt-WNRNi9yzh7Lu60qui6Nh6w), чтобы общаться с сообществом OpenBot.
- Напишите команде проекта по [электронной почте](mailto:openbot.team@gmail.com).

## Участие в разработке

Прочитайте [правила участия](CONTRIBUTING.md). Если не знаете, с чего начать, посмотрите [открытые задачи исходного проекта](https://github.com/ob-f/OpenBot/issues).

## Ссылка на научную публикацию

Если вы используете OpenBot, ссылайтесь на [научную статью разработчиков](https://arxiv.org/abs/2008.10631).

```bib
@inproceedings{mueller2021openbot,
    title     = {OpenBot: Turning Smartphones into Robots},
    author    = {M{\"u}ller, Matthias and Koltun, Vladlen},
    booktitle = {Proceedings of the International Conference on Robotics and Automation (ICRA)},
    year = {2021},
}
```

<a href="https://www.openbot.org/" target="_blank">
  <img align="center" alt="Анимация OpenBot" width="100%" src="docs/images/footer.gif" />
</a>
