from django.db import models


class Student(models.Model):
    name = models.CharField(max_length=255)
    grade = models.CharField(max_length=50)

    def __str__(self):
        return self.name


# =========================================================
# GAME STATUS
# =========================================================

class GameStatus(models.Model):

    STATUS_CHOICES = [
        ("not_started", "Not Started"),
        ("playing", "Playing"),
        ("paused", "Paused"),
        ("game_over", "Game Over"),
        ("completed", "Completed"),
    ]

    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name="game_status"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="not_started"
    )

    stage = models.IntegerField(
        default=0
    )

    monster = models.IntegerField(
        default=0
    )

    enemy_number = models.IntegerField(
        default=0
    )

    difficulty = models.CharField(
        max_length=30,
        blank=True,
        default=""
    )

    hp = models.IntegerField(
        default=0
    )

    max_hp = models.IntegerField(
        default=100
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.student.name} - {self.status}"