# Avanc Otchet Automation

Полноценный локальный `React + FastAPI` проект с двумя отдельными порталами:

- `staff` для сотрудников: вход, личный кабинет, создание производственных отчетов, просмотр своей истории и авансовых документов.
- `admin` для администраторов: обзор всех данных, сводка по подразделениям, контроль отчетов и превью/скачивание авансовых отчетов в PDF.

В качестве локальной базы используется `SQLite`. База создается автоматически в файле [backend/avanc.db](/C:/Users/user/Desktop/Avanc%20otchet%20automation/backend/avanc.db) при первом запуске API.

## Стек

- Backend: `FastAPI`, `sqlite3`, `SQLite`, `JWT`, `Pillow`
- Frontend: `React`, `TypeScript`, `Vite`, `React Router`

## Структура

- [backend/app/main.py](/C:/Users/user/Desktop/Avanc%20otchet%20automation/backend/app/main.py) — вход в API
- [backend/app/api](/C:/Users/user/Desktop/Avanc%20otchet%20automation/backend/app/api) — роуты `auth`, `staff`, `admin`
- [frontend/src/App.tsx](/C:/Users/user/Desktop/Avanc%20otchet%20automation/frontend/src/App.tsx) — маршрутизация порталов
- [frontend/src/features/staff/StaffDashboardPage.tsx](/C:/Users/user/Desktop/Avanc%20otchet%20automation/frontend/src/features/staff/StaffDashboardPage.tsx) — кабинет сотрудника
- [frontend/src/features/admin/AdminDashboardPage.tsx](/C:/Users/user/Desktop/Avanc%20otchet%20automation/frontend/src/features/admin/AdminDashboardPage.tsx) — кабинет администратора

## Запуск backend

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r backend\requirements.txt
uvicorn app.main:app --reload --app-dir backend --host 127.0.0.1 --port 8000
```

API будет доступен по адресу `http://127.0.0.1:8000`, документация Swagger — `http://127.0.0.1:8000/docs`.

## Запуск frontend

В PowerShell обычный `npm` может блокироваться политикой исполнения, поэтому используйте `npm.cmd`.

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Frontend в dev-режиме использует Vite proxy и отправляет запросы на backend через `/api`, проксируя их на `http://127.0.0.1:8000`.

## Запуск всего проекта одной командой

```powershell
.\start-dev.ps1
```

Скрипт запускает backend на `127.0.0.1:8000` и frontend на `127.0.0.1:5173`.

При необходимости можно переопределить адрес через переменную окружения:

```powershell
$env:VITE_API_URL="http://127.0.0.1:8000/api"
npm.cmd run dev
```

## Демо-аккаунты

- Сотрудник: `staff1@avancfactory.com` / `Staff123!`
- Сотрудник: `staff2@avancfactory.com` / `Staff123!`
- Администратор: `admin@avancfactory.com` / `Admin123!`

## Что реализовано

- Раздельные входы для сотрудников и администраторов
- JWT-аутентификация и разграничение ролей
- Создание производственных отчетов по цехам
- Сводные административные показатели и поиск по данным
- Генерация авансовых отчетов в PDF
- Превью PDF в браузере и скачивание из админ-панели
- Классический строгий UI с адаптацией под мобильные экраны


 ## cd backend
 ## .\.venv\Scripts\activate
 ## python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

## cd frontend
 ##  npm run dev
 