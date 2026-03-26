"""הגדרת לוגינג מובנה באמצעות structlog."""

import logging
import sys

import structlog


def setup_logging(log_level: str = "INFO") -> None:
    """
    מגדיר את structlog ואת ספריית הלוגינג הסטנדרטית של Python.

    בסביבת production משתמש ב-JSONRenderer לפלט מובנה.
    בסביבת development משתמש ב-ConsoleRenderer לקריאות אנושית.
    """
    # קביעת רמת לוגינג
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # הגדרת מעבדי structlog משותפים
    shared_processors: list[structlog.types.Processor] = [
        # הוספת שם הלוגר לכל רשומה
        structlog.stdlib.add_logger_name,
        # הוספת רמת לוגינג
        structlog.stdlib.add_log_level,
        # הוספת חותמת זמן ISO 8601
        structlog.processors.TimeStamper(fmt="iso"),
        # הוספת מזהה שירות קבוע
        structlog.contextvars.merge_contextvars,
        # עיבוד חריגות לפלט קריא
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # הגדרת structlog
    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # בחירת renderer לפי סביבה
    # בדיקה פשוטה: אם stderr הוא TTY, נניח שזו סביבת פיתוח
    is_tty = sys.stderr.isatty()

    if is_tty:
        # renderer קריא לאנוש — לסביבת פיתוח
        renderer: structlog.types.Processor = structlog.dev.ConsoleRenderer()
    else:
        # renderer JSON — לסביבת production
        renderer = structlog.processors.JSONRenderer()

    # הגדרת formatter לשימוש עם logging stdlib
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    # handler לכתיבה ל-stderr
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)

    # הגדרת root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(numeric_level)

    # קישור משתנים קבועים לכל רשומות הלוג
    structlog.contextvars.bind_contextvars(service="cognet-api")


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    מחזיר לוגר structlog מקושר לשם המודול הנתון.

    שימוש:
        logger = get_logger(__name__)
        logger.info("אירוע", key="value")
    """
    return structlog.get_logger(name)
