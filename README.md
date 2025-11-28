# University Course Registration and Grade Management (Django 版)

本仓库提供一个**基于 Django + SQLite** 的课程注册与成绩管理示例，覆盖学院/院系/专业、课程/先修课、教学班、学生/教师、选课与成绩等核心实体。借助 Django Admin 可获得类似下图的后台界面：课程、教学班、选课记录、教师、学生等均可在同一控制台进行维护和审计。

## 仓库结构
- `manage.py` / `university_portal/`：Django 项目入口与配置。
- `registration/`：业务模型、后台注册以及示例数据导入命令。
- `requirements.txt`：Python 依赖（Django）。
- `docs/database_design.md`、`sql/`：原始的数据库设计文档与 ANSI-SQL 脚本，可对照 Django 模型理解字段与约束。
- `app.py`：上一版的纯 SQLite 命令行工具，仍可用于无框架环境快速演示（可选）。

## 快速开始
1. **安装依赖**（建议在虚拟环境中）：
   ```bash
   pip install -r requirements.txt
   ```
2. **初始化数据库**（SQLite 默认保存在 `db.sqlite3`）：
   ```bash
   python manage.py migrate
   ```
3. **创建管理员账号**（用于登录 Django Admin）：
   ```bash
   python manage.py createsuperuser
   ```
4. **导入示例数据**（学院/院系/专业、课程、教学班、学生、选课与成绩）：
   ```bash
   python manage.py seed_sample
   ```
5. **启动开发服务并登录后台**：
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```
   打开浏览器访问 `http://localhost:8000/admin/`，使用上一步创建的管理员账号登录，即可看到课程、教学班、先修课、选课记录、教师、学生等模块，界面与截图所示的 Django Admin 类似。

## Django Admin 中的功能对应关系
- **学院 / 院系 / 专业**：维护组织架构，学生与教师均绑定所属院系与专业。
- **课程 / 先修课要求**：录入课程基础信息、学分与类别；在“课程先修要求”中配置必修的前置课程与最低分数。
- **教学班（Course sections）**：为课程在指定学期开班，设置容量、任课教师、教室与时间（周几、起止时间、备注）。
- **学生 / 教师**：录入基础信息并与院系、专业关联。教师不可跨时间段授课，学生的选课记录由 Enrollment 维护。
- **选课记录（Enrollment）**：记录选课状态（已选、退课、通过、未通过、重修申请）、成绩、绩点等。可结合先修要求与时间安排进行业务审核。

## 设计与数据说明
- 模型覆盖了最初需求中的关键表：学生、教师、课程、课程班、选课记录、课程先修、学院/院系/专业、学期等，字段含义和约束与 `docs/database_design.md`、`sql/schema.sql` 对应。
- `python manage.py seed_sample` 会生成可直接演示的冲突/先修案例：
  - 算法课（CSE200）与高等数学（MATH101）在周一 8:00-9:50 时间冲突。
  - 数据库系统（CSE210）需要算法课通过（≥60 分）；软件工程综合实践（SE320）需要数据库系统（≥70 分）。
  - 示例学生 Alice 已通过算法、正在修数据库；Bob 重修实践课程，可用于 GPA/通过率等统计。

## 继续扩展的建议
- 在 Django Admin 中启用自定义动作：批量通过/退课、导出成绩单、审核重修申请等。
- 增加前端页面或 API（Django REST Framework）以支持学生自助选课、冲突校验与 GPA 查询。
- 将账号体系与教师/学生关联，细化权限（仅本人可查看成绩，管理员可设容量与先修规则等）。
- 针对多学期、容量等待名单、并发选课的场景，结合数据库锁或队列实现冲突安全的登记逻辑。

## 命令行工具（可选）
若仅需快速验证 SQL 逻辑，仍可使用旧版 `app.py`：
```bash
python app.py init-db
python app.py transcript alice
```
其建表与测试数据与 Django 模型保持一致，可作为对照或离线演示脚本。
