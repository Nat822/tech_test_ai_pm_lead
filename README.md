AI Project Navigator — персональный AI‑помощник для PM по внедрению ИИ
FastAPI · Streamlit · NeuralDeep · ChromaDB · RAG

 Описание проекта
AI Project Navigator — это персональный AI‑агент для сотрудников Система.Поток, который помогает работать с проектами внедрения корпоративного ИИ.
Он анализирует материалы проекта (встречи, переписки, ТЗ, логи), выявляет изменения требований, готовит к встречам, находит блокеры и создаёт задачи.

Агент использует:

NeuralDeep (GPT‑OSS‑120B) как LLM‑движок

NeuralDeep bge‑m3 для embeddings

ChromaDB для векторного поиска

FastAPI для backend

Streamlit для интерфейса

RAG‑подход для работы с документами

 Основные возможности
1. Подготовка к встрече
Агент анализирует последние материалы проекта и формирует:

контекст проекта

принятые решения

открытые вопросы

что обязательно спросить

невыполненные обещания клиенту

2. Изменения требований
Агент сравнивает материалы и выявляет:

добавленные требования

изменённые

удалённые

противоречия (например, разные сроки)

гипотезу актуального требования

3. Поиск блокеров
Агент определяет:

технические блокеры

организационные

ответственных

предложенные следующие шаги

4. Создание задачи
Агент формирует задачу и вызывает локальный API /tasks, который сохраняет её в tasks.json.

 Архитектура
 agent/
│
├── main.py                # FastAPI entrypoint
├── llm.py                 # NeuralDeep client (chat + embeddings)
├── rag.py                 # RAG pipeline (indexing + retrieval)
├── tasks.py               # Tool/API for creating tasks
│
├── routes/
│   ├── meeting.py         # /prepare_meeting
│   ├── requirements.py    # /requirements_diff
│   ├── blockers.py        # /find_blockers
│   └── next_step.py       # /next_step_task
│
├── models/
│   ├── meeting.py         # Pydantic schemas
│   ├── requirements.py
│   ├── blockers.py
│   └── task.py
│
├── data/                  # Исходные материалы
├── embeddings/            # ChromaDB storage
├── tasks.json             # Хранилище задач
│
├── streamlit_app.py       # UI
└── .env.example

Используемые технологии
FastAPI (async) — backend

Streamlit — UI

NeuralDeep GPT‑OSS‑120B — LLM

NeuralDeep bge‑m3 — embeddings

ChromaDB — векторное хранилище

httpx — async HTTP‑клиент

Pydantic v2 — строгие JSON‑схемы

RAG — поиск по документам

Переменные окружения
Создайте файл .env:
NEURALDEEP_API_KEY=your_key_here
NEURALDEEP_MODEL=GPT-OSS-120B
NEURALDEEP_EMBED_MODEL=bge-m3
NEURALDEEP_BASE_URL=https://api.neuraldeep.ru/v1

Установка и запуск
1. Клонировать репозиторий
   git clone <your-repo-url>
   cd agent
2. Установить зависимости
   pip install -r requirements.txt
3. Создать .env
   cp .env.example .env
4. Запустить FastAPI
   uvicorn main:app --reload
5. Запустить Streamlit UI
   streamlit run streamlit_app.py

RAG‑пайплайн
Агент использует Retrieval‑Augmented Generation:

Загрузка документов из data/

Нарезка на chunks (500–1000 символов)

Генерация embeddings через NeuralDeep bge‑m3

Сохранение в ChromaDB

Поиск релевантных фрагментов

Формирование контекста для LLM

Генерация структурированного JSON‑ответа

API‑эндпоинты
/prepare_meeting
Подготовка к встрече.

/requirements_diff
Изменения требований.

/find_blockers
Поиск блокеров.

/next_step_task
Генерация задачи.

/tasks
Создание задачи (локальный tool/API).

JSON‑схемы
MeetingPrep
{
  "context": "...",
  "decisions": ["..."],
  "open_questions": ["..."],
  "must_ask": ["..."],
  "unfulfilled_promises": ["..."]
}

RequirementsDiff
{
  "added": ["..."],
  "changed": ["..."],
  "removed": ["..."],
  "conflicts": [
    {
      "field": "deadline",
      "values": ["2024-10-01", "2024-12-15"],
      "sources": ["meeting_2024_09_15.txt", "email_2024_09_20.txt"]
    }
  ],
  "current_hypothesis": "..."
}

Blockers
{
  "technical": ["..."],
  "organizational": ["..."],
  "responsibles": [
    {"blocker": "...", "person": "..."}
  ],
  "next_steps": ["..."]
}

TaskModel
{
  "title": "...",
  "description": "...",
  "priority": "high",
  "assignee": "PM"
}

Tool/API — создание задачи
Эндпоинт:
POST /tasks

Сохраняет задачу в tasks.json.

🎨 Streamlit UI
Функции:

выбор проекта

кнопки сценариев

отображение JSON‑ответов

кнопка «Создать задачу»

🧪 Проблемные сценарии (обязательное требование теста)
Агент обрабатывает:

недостаток данных

противоречивые требования

ошибки API

некорректный формат ответа модели

отсутствие релевантных документов

AI Usage Note
В проекте использовались AI‑инструменты для:

генерации архитектуры

проектирования структуры файлов

написания промптов

создания JSON‑схем

генерации кода FastAPI и Streamlit

проверки корректности RAG‑логики

Все результаты были проверены вручную и адаптированы под требования тестового задания.
