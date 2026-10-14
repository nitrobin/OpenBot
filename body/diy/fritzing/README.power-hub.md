# OpenBot DIY power hub

[Editable Fritzing file](openbot-diy-power-hub.fzz), with short English labels.
J4 sits at the bottom, to the left of J5, with GND on the left and A7 on the
right. The battery holder is turned 90° clockwise above the board, beside the
switch; both battery wires go straight down to BAT. J5 has GND on the left
and 5V on the right; the orange 5V link follows the right and bottom edges. The separate
distribution header below uses the same column order and two straight wires.

![Power hub](openbot-diy-power-hub.png)

## Translate and export

Run the adjacent [script](translate_power_hub.py) with Python 3 and Fritzing
(CLI export verified with Fritzing 1.0.8):

```sh
python3 body/diy/fritzing/translate_power_hub.py
```

The script discovers repository languages from tracked README files, Android
resources and iOS localization folders. Current languages: `en`, `ru`, `de`,
`es`, `fr`, `zh`, `ko`, `hi`. It translates labels from the offline
[catalog](power_hub_i18n.json), then exports one Breadboard SVG per language
through Fritzing. Each language has a separate module cache ID. The English
source FZZ is preserved; localized FZZ files are temporary unless requested.

```sh
# Validate translations and unchanged geometry without launching Fritzing.
python3 body/diy/fritzing/translate_power_hub.py --check

# Select languages; regional codes such as ru-RU are accepted.
python3 body/diy/fritzing/translate_power_hub.py --languages en ru

# Also save editable localized FZZ files.
python3 body/diy/fritzing/translate_power_hub.py --languages ru --keep-fzz

# Override automatic executable detection if needed.
python3 body/diy/fritzing/translate_power_hub.py --fritzing /path/to/Fritzing
```

Missing or empty translations produce a warning and fall back to English.
If a catalog key or its English value is absent, the original English label
is retained. Generation continues; `manifest.json` lists the fallbacks and
SHA-256 hashes of the source, catalog, generator and outputs. Pin names,
component values, wire connections and geometry are checked for changes.

To add a label, give its SVG `<text>` element a `data-i18n` key inside the FZZ
and add that key to the catalog. Keep the English source text and the `en`
entry equal. `data-i18n-prefix` and `data-i18n-suffix` preserve fixed markers.
Exported translations contain technical markings such as `GND`, `5V`, `A7`,
`SW_IN`, `SW_OUT` and `periferial` in their original spelling.

## Generated SVGs

| Language | Breadboard |
| --- | --- |
| English | [en](power-hub-locales/en/openbot-diy-power-hub-breadboard.svg) |
| Русский | [ru](power-hub-locales/ru/openbot-diy-power-hub-breadboard.svg) |
| Deutsch | [de](power-hub-locales/de/openbot-diy-power-hub-breadboard.svg) |
| Español | [es](power-hub-locales/es/openbot-diy-power-hub-breadboard.svg) |
| Français | [fr](power-hub-locales/fr/openbot-diy-power-hub-breadboard.svg) |
| 简体中文 | [zh](power-hub-locales/zh/openbot-diy-power-hub-breadboard.svg) |
| 한국어 | [ko](power-hub-locales/ko/openbot-diy-power-hub-breadboard.svg) |
| हिन्दी | [hi](power-hub-locales/hi/openbot-diy-power-hub-breadboard.svg) |

[Export manifest](power-hub-locales/manifest.json).
[Electrical verification and component credits](README.power-hub.ru-RU.md).
Only Breadboard SVGs are saved; this file has no manufacturing PCB layout.
