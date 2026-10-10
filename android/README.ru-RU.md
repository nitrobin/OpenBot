# Приложения для Android

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

## Возможности

Описание функций приложений доступно по ссылкам:

- [Приложение робота (Robot App)](robot/README.md).
- [Приложение пульта управления (Controller App)](controller/README.md).

## Установка приложений

Самый простой способ получить приложение — скачать его непосредственно на смартфон по соответствующему QR-коду. Если вы открыли эту страницу в браузере смартфона, можно нажать на QR-код. Затем откройте APK-файл на телефоне и [установите приложение](https://www.lifewire.com/install-apk-on-android-4177185). Учтите, что APK подписан только отладочным ключом (debug key).

<table style="width:100%;border:none;text-align:center">
  <tr>
    <td><a href="https://app.openbot.org/robot" target="_blank"><img alt="Приложение робота" width="50%" src="../docs/images/robot_app_qr_code.png" /></a></td>
    <td><a href="https://app.openbot.org/controller" target="_blank"><img alt="Приложение пульта управления" width="50%" src="../docs/images/controller_app_qr_code.png" /></a></td>
  </tr>
  <tr>
    <td>🤖 Приложение робота</td>
    <td>🎮 Пульт управления</td>
  </tr>
</table>

APK-файлы также можно скачать из вложений к [выпускам исходного проекта](https://github.com/ob-f/OpenBot/releases). Последние приложения из ветки `master` доступны в [артефактах сборки GitHub Actions](https://github.com/ob-f/OpenBot/actions?query=workflow%3A%22Java+CI+with+Gradle%22); такие версии могут быть нестабильны. Если вы планируете изменять приложения, выполните следующие шаги для сборки и установки на смартфон.

## Сборка приложений

### Требования

- [Android Studio](https://developer.android.com/studio/index.html) для сборки и установки APK. Версия IDE должна поддерживать Android Gradle Plugin (AGP), указанный в [android/build.gradle](build.gradle).
- Android-устройство, соответствующее минимальному уровню API выбранного приложения.
- Установленный Android SDK с уровнем API, указанным в `compileSdkVersion`. Если пакет не установился автоматически, откройте `Android Studio > Preferences > Appearance & Behaviour > System Settings > Android SDK`, выберите нужный уровень API и нажмите `Apply`.

**Уточнение к исходнику:** английский README указывает Android Studio Electric Eel 2022.1.1, общий минимум API 21, `compileSdk` 33 и `targetSdk` 32. Эти сведения устарели относительно файлов сборки данной ветки. Здесь используются следующие параметры:

| Параметр | Приложение робота | Пульт управления |
| --- | --- | --- |
| Модуль | `robot` | `controller` |
| Минимальный уровень API (`minSdkVersion`) | 24 | 21 |
| Уровень API для сборки (`compileSdkVersion`) | 36 | 36 |
| Целевой уровень API (`targetSdkVersion`) | 36 | 36 |

Источник значений: [robot/build.gradle](robot/build.gradle) и [controller/build.gradle](controller/build.gradle). В проекте заданы AGP 8.7.3, [Gradle 8.9](gradle/wrapper/gradle-wrapper.properties) и Java 17. При последующих обновлениях сверяйте требования с этими файлами и [официальной таблицей совместимости AGP](https://developer.android.com/build/releases/agp-8-7-0-release-notes).

![Настройки Android SDK](../docs/images/android_studio_sdk.jpg)

### Порядок сборки

1. Откройте Android Studio и выберите `Open an existing Android Studio project`.
2. Выберите папку `OpenBot/android` и нажмите `OK`.
3. Для установки [приложения робота](robot/README.md) выберите конфигурацию запуска модуля `robot`, а для [пульта управления](controller/README.md) — `controller`. В исходном README конфигурация приложения робота названа `app`; в текущем проекте соответствующий модуль называется `robot`. При запросе подтвердите синхронизацию Gradle (`Gradle Sync`). Для её ручного запуска нажмите соответствующий значок Gradle.
   ![Синхронизация Gradle](../docs/images/android_studio_bar_gradle.jpg)
4. Подключите Android-устройство и включите отладку по USB (`USB Debugging`) в [настройках разработчика](https://developer.android.com/studio/debug/dev-options). В зависимости от среды разработки могут понадобиться [дополнительные действия](https://developer.android.com/studio/run/device). После подключения устройство должно появиться в верхней панели выбора устройства.
   ![Выбор подключённого смартфона](../docs/images/android_studio_bar_phone.jpg)
5. Нажмите `Run` — кнопку с зелёной стрелкой — либо выберите запуск нужной конфигурации в меню `Run`. В исходной инструкции приведены пункты `Run > Run 'android'` и, для повторной сборки, `Build > Rebuild Project`; доступные названия зависят от версии IDE и конфигурации проекта.
   ![Запуск приложения](../docs/images/android_studio_bar_run.jpg)
6. Если старая версия IDE предлагает использовать `Instant Run`, выберите `Proceed Without Instant Run`.

### Устранение неполадок

#### Совместимость версий

Если появляется сообщение вроде `The project is using an incompatible version (AGP 7.4.0) of the Android Gradle plugin. Latest supported version is AGP 7.3.0`, версии Android Studio и AGP несовместимы. В исходной инструкции предлагается обновить Android Studio либо понизить версию плагина Gradle. Перед изменением версий ознакомьтесь с [документацией по совместимости Android Studio и AGP](https://developer.android.com/studio/releases/gradle-plugin#android_gradle_plugin_and_android_studio_compatibility).

## Следующий шаг

Выберите способ [управления роботом](../controller/README.ru-RU.md).
