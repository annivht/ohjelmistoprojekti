import pygame

class Vahinko:
    def __init__(self, amount, source=None):
        """
        amount: kuinka paljon vahinkoa (esim. 10)
        source: mistä vahinko tuli (esim. ammus, meteoriitti, vihollinen)
        """
        self.amount = amount
        self.source = source

    def apply(self, target):
        """
        Vähennä targetin elämää vahingon verran.
        target: olio, jolla on 'health' attribuutti
        """
        if hasattr(target, 'health'):
            target.health -= self.amount
            if target.health < 0:
                target.health = 0

    def __repr__(self):
        return f"Vahinko(amount={self.amount}, source={self.source})"
