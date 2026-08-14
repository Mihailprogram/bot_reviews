# tasks/models.py

from django.db import models


class Task(models.Model):
    title = models.CharField(
        max_length=255,
        verbose_name="Название",
    )

    description = models.TextField(
        verbose_name="Описание",
    )

    platform = models.CharField(
        max_length=100,
        verbose_name="Площадка",
    )

    url = models.URLField(
        blank=True,
        verbose_name="Ссылка",
    )

    reward = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Вознаграждение",
    )

    max_completions = models.PositiveIntegerField(
        default=1,
        verbose_name="Максимум выполнений",
    )

    completions = models.PositiveIntegerField(
        default=0,
        verbose_name="Выполнено",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Активно",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата окончания",
    )

    class Meta:
        verbose_name = "Задание"
        verbose_name_plural = "Задания"
        ordering = ("-created_at",)

    def __str__(self):
        return self.title

    @property
    def available(self):
        return (
            self.is_active
            and self.completions < self.max_completions
        )


class TelegramUser(models.Model):
    telegram_id = models.BigIntegerField(
        unique=True,
    )

    username = models.CharField(
        max_length=255,
        blank=True,
    )

    first_name = models.CharField(
        max_length=255,
        blank=True,
    )

    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return (
            f"{self.first_name} "
            f"(@{self.username})"
        )


class UserTask(models.Model):

    STATUS_CHOICES = (
        ("taken", "Взято"),
        ("submitted", "Отправлено"),
        ("approved", "Одобрено"),
        ("rejected", "Отклонено"),
    )

    user = models.ForeignKey(
        TelegramUser,
        on_delete=models.CASCADE,
        related_name="tasks",
    )

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="users",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="taken",
    )

    review_url = models.URLField(
        blank=True,
    )

    screenshot = models.ImageField(
        upload_to="reviews/",
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("user", "task"),
                name="unique_user_task",
            ),
        ]