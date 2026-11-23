# geometry_dash_project_trpo_lab_2026
technologiya razrabotki programmnogo obespecheniya

## Установка

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Интерфейс (UI)

Демо интерфейса: загрузка трека → выбор формы → экран с HUD.

```
python3 -m ui.demo
```

| Файл | Что внутри |
| --- | --- |
| `ui/theme.py` | Темы Swiss (светлая, красный акцент) и Noir (тёмная, золотой акцент), цвета форм |
| `ui/form_view.py` | Отрисовка форм: куб — оранжевый, корабль — синий, шар — красный, волна — бирюзовая, НЛО — фиолетовое |
| `ui/hud.py` | HUD: полоска прогресса, процент, лучший результат, попытка, текущая форма |
| `ui/menu.py` | Меню выбора формы; в первой версии открыты куб и корабль |
| `ui/track_screen.py` | Экран загрузки трека: выбор файла, проверка формата и длительности, анализ через `music/beat_detect.py` |
| `ui/demo.py` | Демо-запуск всех экранов |

Клавиша T переключает тему на любом экране.
