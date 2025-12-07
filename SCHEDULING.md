# Автоматический запуск по расписанию

Этот проект поддерживает автоматический запуск синхронизации согласно расписанию из `config.yaml`.

## Быстрый старт

1. **Установить расписание:**
   ```bash
   ./install_scheduler.sh
   ```

2. **Готово!** Синхронизация будет запускаться автоматически каждый день в указанное время.

## Настройка времени

Отредактируйте `config.yaml`:

```yaml
schedule:
  run_time: "11:00"  # 24-часовой формат (11:00 утра)
```

После изменения времени обновите расписание:

```bash
uv run python update_schedule.py install
```

## Управление расписанием

### Проверить статус
```bash
uv run python update_schedule.py status
```

### Установить/обновить расписание
```bash
uv run python update_schedule.py install
```

### Удалить расписание
```bash
uv run python update_schedule.py uninstall
```

### Запустить вручную
```bash
./sync_whoop.sh
```
или
```bash
uv run python -m whoop_obsidian
```

## Логи

- **Основные логи приложения:** `logs/whoop_sync.log`
- **Логи планировщика (stdout):** `logs/scheduler.log`
- **Логи ошибок планировщика (stderr):** `logs/scheduler_error.log`

Проверить последние записи:
```bash
tail -f logs/scheduler.log
```

## Как это работает

Система использует **launchd** (стандартный планировщик задач macOS):

1. `install_scheduler.sh` - устанавливает расписание
2. `update_schedule.py` - создает `.plist` файл для launchd и загружает его
3. `sync_whoop.sh` - обертка для запуска Python модуля
4. launchd автоматически запускает `sync_whoop.sh` в указанное время

### Файл plist

Создается автоматически в:
```
~/Library/LaunchAgents/com.whoop.obsidian.sync.plist
```

Вы можете посмотреть его содержимое, но редактировать напрямую не рекомендуется.

## Примеры времени

```yaml
schedule:
  run_time: "09:00"   # 9 утра
  run_time: "13:30"   # 1:30 дня
  run_time: "18:00"   # 6 вечера
  run_time: "23:59"   # 11:59 вечера
```

## Устранение проблем

### Расписание не работает

1. Проверьте статус:
   ```bash
   uv run python update_schedule.py status
   ```

2. Проверьте логи:
   ```bash
   cat logs/scheduler.log
   cat logs/scheduler_error.log
   ```

3. Переустановите:
   ```bash
   ./install_scheduler.sh
   ```

### Ручной запуск работает, а автоматический нет

Проверьте права доступа:
```bash
chmod +x sync_whoop.sh
```

Проверьте что `WHOOP_API_TOKEN` экспортирован глобально в `~/.zshrc`:
```bash
echo 'export WHOOP_API_TOKEN="your_token"' >> ~/.zshrc
source ~/.zshrc
```

### Изменить время запуска

1. Отредактируйте `config.yaml`
2. Запустите: `uv run python update_schedule.py install`
3. Проверьте: `uv run python update_schedule.py status`
