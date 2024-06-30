# Словарь для хранения полей вакансии и их обязательности
FIELDS = {
    "position": {
        "label": "Название вакансии-позиции",
        "required": 1,
        "example": "Системный аналитик на проект внедрения CRM",
    },
    "code": {"label": "Код вакансии", "required": 0, "example": "DAT-617"},
    "category": {"label": "Категория позиции", "required": 1, "example": "аналитик 1С"},
    "company_name": {"label": "Название компании", "required": 1, "example": "Ладома"},
    "company_url": {
        "label": "Сайт компании",
        "required": 0,
        "example": "https:/domen.ru/www.domen.ru/http://domen.ru/domen.ru/домен.рф",
    },
    "grade": {"label": "Грейд", "required": 0, "example": "Senior"},
    "location": {"label": "Локация", "required": 1, "example": "РФ"},
    "timezone": {"label": "Город и/или часовой пояс", "required": 1, "example": "Москва, +-2 часа"},
    "subject_area": {"label": "Предметная область", "required": 1, "example": ""},
    "job_format": {"label": "Формат работы", "required": 1, "example": "Гибрид"},
    "project_group": {"label": "Тематика проекта", "required": 1, "example": "Тематика!"},
    "salary": {"label": "Зарплата", "required": 0, "example": "100.000₽"},
    "responsibilities": {"label": "Ключевая зона ответственности", "required": 1,
                         "example": "Разработка требований и проектирование интеграций"},
    "requirements": {"label": "Требования", "required": 1, "example": "Быть онлайн 24/7"},
    "tasks": {"label": "Рабочие задачи", "required": 0, "example": "Рабочие задачи"},
    "wishes": {"label": "Пожелания", "required": 0, "example": "Знание английского на уровне C1"},
    "bonus": {"label": "Бонусы", "required": 0, "example": "Мерч"},
    "contacts": {"label": "Контакты", "required": 1, "example": "@telegramuser Ivan Ivanov, CEO"},
    "tags": {"label": "Теги", "required": 0, "example": "#интеграция, #B2B, #SaaS, #API"}
}

AWAITING_FIELD = 1