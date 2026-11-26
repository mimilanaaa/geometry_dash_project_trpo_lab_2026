from core import physics


class Form:
    """Форма персонажа: своя высота хитбокса и своя вертикальная физика."""

    name = "base"
    height = physics.BLOCK
    can_bonk = False   # можно ли безопасно удариться о низ блока

    def enter(self, player):
        """Вызывается при переходе в эту форму через портал."""

    def update(self, player, holding, dt):
        """Меняет player.vy (и угол) за один шаг симуляции."""
        raise NotImplementedError
