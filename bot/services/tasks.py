from typing import Optional

from asgiref.sync import sync_to_async
from django.db import transaction, models
from django.utils import timezone

from bot.models import Task, TelegramUser, UserTask



@sync_to_async
def get_or_create_user(
    telegram_id: int,
    username: str,
    first_name: str,
) -> TelegramUser:
    """Получает или создаёт пользователя Telegram."""

    user, _ = TelegramUser.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={
            "username": username,
            "first_name": first_name,
        },
    )

    # Обновляем данные Telegram,
    # если пользователь уже существует.
    changed = False

    if user.username != username:
        user.username = username
        changed = True

    if user.first_name != first_name:
        user.first_name = first_name
        changed = True

    if changed:
        user.save(
            update_fields=[
                "username",
                "first_name",
            ]
        )

    return user



@sync_to_async
def get_available_tasks(telegram_id: int) -> list[Task]:
    """Возвращает доступные задания для пользователя."""

    now = timezone.now()

    taken_task_ids = UserTask.objects.filter(
        user__telegram_id=telegram_id,
    ).values("task_id")

    return list(
        Task.objects.filter(
            is_active=True,
            completions__lt=models.F("max_completions"),
        )
        .exclude(
            id__in=taken_task_ids,
        )
        .filter(
            models.Q(expires_at__isnull=True)
            | models.Q(expires_at__gt=now)
        )
        .order_by("-created_at")[:20]
    )

@sync_to_async
def get_user_by_telegram_id(
    telegram_id: int,
) -> Optional[TelegramUser]:
    """Получает пользователя по Telegram ID."""

    try:
        return TelegramUser.objects.get(
            telegram_id=telegram_id,
        )
    except TelegramUser.DoesNotExist:
        return None


@sync_to_async
def submit_task(
    user_id: int,
    task_id: int,
    review_url: str,
    screenshot=None,
) -> bool:
    """Отправляет выполненное задание на проверку."""

    updated = UserTask.objects.filter(
        user_id=user_id,
        task_id=task_id,
        status="taken",
    ).update(
        status="submitted",
        review_url=review_url,
        screenshot=screenshot,
        completed_at=timezone.now(),
    )

    return updated > 0


async def complete_task(
    telegram_id: int,
    task_id: int,
    review_url: str,
    screenshot=None,
) -> tuple[bool, str]:
    """Отправляет выполненное задание на проверку."""

    user = await get_user_by_telegram_id(telegram_id)

    if user is None:
        return False, "Пользователь не найден."

    user_task = await get_user_task(
        telegram_id=telegram_id,
        task_id=task_id,
    )

    if user_task is None:
        return False, "Вы не брали это задание."

    if user_task.status == "submitted":
        return False, "Вы уже отправили это задание на проверку."

    if user_task.status == "approved":
        return False, "Это задание уже одобрено."

    if user_task.status == "rejected":
        return False, "Это задание было отклонено."

    if user_task.status != "taken":
        return False, "Нельзя отправить это задание."

    success = await submit_task(
        user_id=user.id,
        task_id=task_id,
        review_url=review_url,
        screenshot=screenshot,
    )

    if not success:
        return False, "Не удалось отправить задание на проверку."

    return True, "Задание отправлено на проверку."


@sync_to_async
def get_task(task_id: int) -> Optional[Task]:
    """Получает доступное задание по ID."""

    now = timezone.now()

    try:
        return (
            Task.objects
            .filter(
                id=task_id,
                is_active=True,
                completions__lt=models.F("max_completions"),
            )
            .filter(
                models.Q(expires_at__isnull=True)
                | models.Q(expires_at__gt=now)
            )
            .first()
        )
    except Task.DoesNotExist:
        return None

@sync_to_async
def take_task(
    telegram_id: int,
    task_id: int,
) -> tuple[bool, str, Optional[Task]]:
    """
    Пользователь берёт задание.

    Возвращает:
        success
        message
        task
    """

    with transaction.atomic():

        try:
            user = TelegramUser.objects.get(
                telegram_id=telegram_id,
            )
        except TelegramUser.DoesNotExist:
            return (
                False,
                "Пользователь не найден.",
                None,
            )

        try:
            task = (
                Task.objects
                .select_for_update()
                .get(id=task_id)
            )
        except Task.DoesNotExist:
            return (
                False,
                "Задание не найдено.",
                None,
            )

        if not task.is_active:
            return (
                False,
                "Это задание больше недоступно.",
                None,
            )

        if task.expires_at:
            if task.expires_at <= timezone.now():
                return (
                    False,
                    "Срок выполнения задания истёк.",
                    None,
                )

        if task.completions >= task.max_completions:
            return (
                False,
                "Все места на это задание уже заняты.",
                None,
            )

        already_taken = UserTask.objects.filter(
            user=user,
            task=task,
        ).exists()

        if already_taken:
            return (
                False,
                "Вы уже брали это задание.",
                task,
            )

        UserTask.objects.create(
            user=user,
            task=task,
            status="taken",
        )

        # task.completions += 1
        task.save(
            update_fields=["completions"],
        )

        return (
            True,
            "Задание успешно взято.",
            task,
        )


@sync_to_async
def get_user_tasks(
    telegram_id: int,
) -> list[UserTask]:
    """Возвращает задания пользователя."""

    return list(
        UserTask.objects.filter(
            user__telegram_id=telegram_id,
        )
        .select_related("task")
        .order_by("-created_at")
    )

@sync_to_async
def get_check_tasks(
    telegram_id: int,
) -> list[UserTask]:
    return list(
            UserTask.objects.filter(
                user__telegram_id=telegram_id,
                status="submitted"
            )
            .select_related("task")
            .order_by("-created_at")
        )


async def get_approved_tasks_balance(
    telegram_id: int,
) -> int:
    user_tasks = await sync_to_async(list)(
        UserTask.objects.filter(
            user__telegram_id=telegram_id,
            status="approved",
        )
        .select_related("task")
        .order_by("-created_at")
    )

    total_reward = sum(
        user_task.task.reward
        for user_task in user_tasks
    )
    return total_reward


@sync_to_async
def update_task_completions(
    task_id: int
) -> None:
    Task.objects.filter(
        id=task_id
    ).update(
        completions=models.F("completions") + 1
    )


@sync_to_async
def get_user_task(
    telegram_id: int,
    task_id: int,
) -> Optional[UserTask]:
    """Возвращает конкретное задание пользователя."""

    try:
        return (
            UserTask.objects
            .select_related("task")
            .get(
                user__telegram_id=telegram_id,
                task_id=task_id,
            )
        )
    except UserTask.DoesNotExist:
        return None