"""Shared wire colors and native SVG legend for every OpenBot Fritzing sketch."""
from html import escape

# One palette for both board variants and both Fritzing views. Keep electrical
# net names unchanged: colors describe their function, not a new connection.
WIRE_TYPES = {
    "VBAT": ("#c62828", "VBAT · плюс батареи", "красный"),
    "5V": ("#ef6c00", "5V · питание 5 В", "оранжевый"),
    "3V3": ("#ec407a", "3V3 · питание 3,3 В", "розовый"),
    "VMOT": ("#546e7a", "VMOT · питание L298N", "серо-синий"),
    "GND": ("#202124", "GND · общий провод", "чёрный"),
    "motor": ("#795548", "Моторы · OUT1–OUT4", "коричневый"),
    "PWM": ("#b08b00", "PWM · IN1–IN4", "золотистый"),
    "encoder": ("#228833", "Энкодеры · D0 / DO", "зелёный"),
    "sonar": ("#0077bb", "Дальномер · Trig / Echo", "синий"),
    "I2C": ("#7b2cbf", "I2C · SCL / SDA", "фиолетовый"),
    "LED": ("#b52ca4", "LED · поворотники", "пурпурный"),
    "ADC": ("#008577", "ADC · измерение батареи", "бирюзовый"),
}
COLORS = {name: values[0] for name, values in WIRE_TYPES.items()}


def legend_svg(width, height, layer):
    """Draw swatches from the exact palette used to serialize the wires."""
    font = 'font-family="Noto Sans,Arial,sans-serif"'
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width / 90:.8f}in" '
           f'height="{height / 90:.8f}in" viewBox="0 0 {width} {height}">',
           f'<g id="{layer}">',
           f'<text x="8" y="28" {font} font-size="21" font-weight="bold" '
           'fill="#172433">Цвета проводов · одинаковые для Nano и ESP32</text>']
    for i, (color, label, _) in enumerate(WIRE_TYPES.values()):
        x = 8 + (i % 4) * width / 4
        y = 60 + (i // 4) * 34
        out += [f'<line x1="{x}" y1="{y}" x2="{x + 30}" y2="{y}" '
                f'stroke="{color}" stroke-width="8" stroke-linecap="round"/>',
                f'<text x="{x + 45}" y="{y + 6}" {font} font-size="17" '
                f'fill="#172433">{escape(label)}</text>']
    out += [f'<text x="8" y="163" {font} font-size="15" fill="#172433">'
            'Цвет обозначает назначение; маркировка контактов определяет подключение. '
            'Легенда включает типы из обеих схем.</text>', '</g></svg>']
    return "\n".join(out).encode()
