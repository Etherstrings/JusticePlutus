from src.notification import NotificationChannel, NotificationService


def build_test_notifier(
    channels,
    append_image_after_text_notify,
    markdown_to_image_channels=None,
):
    notifier = NotificationService.__new__(NotificationService)
    notifier._source_message = None
    notifier._available_channels = list(channels)
    notifier._markdown_to_image_channels = set(markdown_to_image_channels or [])
    notifier._markdown_to_image_max_chars = 15000
    notifier._append_image_after_text_notify = append_image_after_text_notify
    notifier._stock_email_groups = []
    notifier.send_to_context = lambda content: False
    notifier.get_all_email_receivers = lambda: []
    notifier.get_receivers_for_stocks = lambda stock_codes: []
    return notifier


def test_send_appends_png_after_text_when_switch_enabled(monkeypatch):
    notifier = build_test_notifier(
        channels=[NotificationChannel.TELEGRAM],
        append_image_after_text_notify=True,
    )
    events = []
    notifier.send_to_telegram = lambda content: events.append(("text", content)) or True
    notifier._send_telegram_photo = (
        lambda image_bytes: events.append(("image", image_bytes)) or True
    )
    monkeypatch.setattr(
        "src.md2img.markdown_to_image",
        lambda content, max_chars=15000: b"png",
    )

    assert notifier.send("hello") is True
    assert events == [("text", "hello"), ("image", b"png")]


def test_send_keeps_text_success_when_image_render_fails(monkeypatch):
    notifier = build_test_notifier(
        channels=[NotificationChannel.TELEGRAM],
        append_image_after_text_notify=True,
    )
    events = []
    notifier.send_to_telegram = lambda content: events.append(("text", content)) or True
    notifier._send_telegram_photo = (
        lambda image_bytes: events.append(("image", image_bytes)) or True
    )
    monkeypatch.setattr(
        "src.md2img.markdown_to_image",
        lambda content, max_chars=15000: None,
    )

    assert notifier.send("hello") is True
    assert events == [("text", "hello")]


def test_send_preserves_legacy_replace_with_image_mode_when_append_switch_off(monkeypatch):
    notifier = build_test_notifier(
        channels=[NotificationChannel.TELEGRAM],
        append_image_after_text_notify=False,
        markdown_to_image_channels={"telegram"},
    )
    events = []
    notifier.send_to_telegram = lambda content: events.append(("text", content)) or True
    notifier._send_telegram_photo = (
        lambda image_bytes: events.append(("image", image_bytes)) or True
    )
    monkeypatch.setattr(
        "src.md2img.markdown_to_image",
        lambda content, max_chars=15000: b"png",
    )

    assert notifier.send("hello") is True
    assert events == [("image", b"png")]
