# tasks/admin.py

from django.contrib import admin

from .models import Task, TelegramUser, UserTask


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "platform",
        "reward",
        "completions",
        "max_completions",
        "is_active",
        "created_at",
    )

    list_filter = (
        "platform",
        "is_active",
    )

    search_fields = (
        "title",
        "description",
    )


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):

    list_display = (
        "telegram_id",
        "username",
        "first_name",
        "balance",
        "created_at",
    )

    search_fields = (
        "telegram_id",
        "username",
        "first_name",
    )


@admin.register(UserTask)
class UserTaskAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "task",
        "status",
        "created_at",
        "completed_at",
    )

    list_filter = (
        "status",
    )

    search_fields = (
        "user__username",
        "task__title",
    )