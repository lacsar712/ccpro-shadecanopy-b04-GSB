# ShadeCanopy-01 · 分区气候日志与轮灌计划

温室「分区气候日志与轮灌计划」全栈种子项目（非考勤 OA、非库存）。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 后端 | Python Django 5 · Django REST Framework · SimpleJWT · django-cors-headers · Gunicorn |
| 前端 | Vue 3 · Vite · Pinia · Vue Router |
| 数据库 | PostgreSQL 15 |
| 部署 | Docker Compose · Nginx（前端容器反代 `/api` → Django） |

## 路径与端口

- **项目路径**：`D:\work\document\bytecode\claudeCodePro\ShadeCanopy\ShadeCanopy-01\`
- **前端**：http://localhost:3500
- **后端 API**：http://localhost:8500（也可经前端同源 `/api` 访问）
- **PostgreSQL**：localhost:5435

## 演示账号

| 用户名 | 密码 | 角色 |
| --- | --- | --- |
| `admin` | `123456` | admin（管理员，可进 Django Admin） |
| `grower` | `123456` | grower（种植员） |

启动时 `entrypoint.sh` 会执行 `migrate` + `seed_data` 自动写入账号与示例业务数据。

## 快速启动

```bash
cd D:\work\document\bytecode\claudeCodePro\ShadeCanopy\ShadeCanopy-01
docker compose up --build
```

浏览器打开 http://localhost:3500 ，使用 `grower` / `123456` 登录。

停止：

```bash
docker compose down
```

## 业务模块

1. **Auth**：JWT `POST /api/auth/token/`，当前用户 `GET /api/auth/me/`
2. **Greenhouse**：name / location / areaM2 / notes
3. **Zone**：greenhouseId / zoneCode / cropName / status(`idle|growing|fallow`)；同温室 zoneCode 唯一
4. **ClimateLog**：zoneId / recordedAt / tempC / humidityPct / parUmol / co2Ppm / recorder / reviewer；**humidityPct ∈ [20, 100]**；**双签规则见下**
5. **IrrigationCycle**：zoneId / startAt / durationMin / waterLiters / status(`scheduled|running|done|skipped`)；**缺签分区禁止新建**
6. **Dashboard**：温室数、growing 分区数、近 24h 气候日志数、今日 scheduled 轮灌数、缺签气候条数、因缺签禁灌分区数 → `GET /api/dashboard/`

## 双签与禁灌规则

- **双签字段**：气候日志含 `recorder`（记录人）与 `reviewer`（复核人）。两者**去空白后均至少 2 字，且不得相同**，否则新建/更新返回 **400**。
- **同一套校验**：新建（POST）与更新（PUT/PATCH）调用同一套双签校验（`backend/core/signing.py::validate_dual_sign`）。
- **历史数据**：迁移前已存在或种子中的缺签行（记录人或复核人为空）**读取时照常返回**；但任何更新必须补齐双签才能保存。
- **缺签口径**：记录人或复核人**去空白后为空**即为缺签。该判定集中在 `backend/core/signing.py`，以下四处同源：
  1. 气候列表缺签过滤 `GET /api/climate-logs/?unsigned=1`（缺省不带该参数时仍返回全量，两者互不污染）；
  2. 新建轮灌拦截：分区存在缺签气候记录时，`POST /api/irrigation-cycles/` 返回 400，直至该分区缺签行补齐双签（无缺签行时不拦）；
  3. 看板 `unsignedClimateCount`：缺签气候条数，等于缺签过滤行数；
  4. 看板 `irrigationBlockedZoneCount`：因缺签被禁灌的分区数，等于至少有一条缺签气候的分区数。
- **种子数据**：`seed_data` 会在在种分区 `A-01` 上保留一条缺签历史行，用于演示缺签过滤与禁灌拦截。

## API 一览

| 方法 | 路径 |
| --- | --- |
| POST | `/api/auth/token/` |
| POST | `/api/auth/token/refresh/` |
| GET | `/api/auth/me/` |
| CRUD | `/api/greenhouses/` |
| CRUD | `/api/zones/?greenhouseId=&status=` |
| CRUD | `/api/climate-logs/?zoneId=&unsigned=1` |
| CRUD | `/api/irrigation-cycles/?zoneId=&status=` |
| GET | `/api/dashboard/` |

字段对外使用 camelCase（如 `areaM2`、`zoneCode`、`humidityPct`）。

## 本地开发（可选）

**后端**（需本机 Postgres 或已启动 compose 中的 db）：

```bash
cd backend
pip install -r requirements.txt
set POSTGRES_HOST=127.0.0.1
set POSTGRES_PORT=5435
python manage.py migrate
python manage.py seed_data
python manage.py runserver 0.0.0.0:8500
```

**前端**：

```bash
cd frontend
npm install
npm run dev
```

Vite 已将 `/api` 代理到 `http://127.0.0.1:8500`。

## 目录结构

```
ShadeCanopy-01/
├── docker-compose.yml
├── README.md
├── .gitignore
├── backend/
│   ├── Dockerfile
│   ├── entrypoint.sh      # migrate + seed + gunicorn
│   ├── requirements.txt
│   ├── manage.py
│   ├── config/            # settings / urls
│   ├── accounts/          # 自定义 User + role
│   └── core/              # 温室/分区/气候/轮灌 + seed_data
└── frontend/
    ├── Dockerfile
    ├── nginx.conf         # 静态资源 + /api 反代
    ├── package.json
    └── src/               # Vue 页面（叶绿/土色主题）
```

## 配色说明

前端采用叶绿（`#3d6b3a`）与土色（`#8b6b45`）主色，米色底与侧栏深绿渐变，贴近温室场景。
