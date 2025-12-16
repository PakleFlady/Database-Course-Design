# University Course Registration and Grade Management (Django 版本)

本项目使用 **Django + SQLite** 构建了可直接运行的课程注册与成绩管理后台，提供完整的数据模型、管理后台界面、种子数据、以及快速启动教程。你可以通过 Django Admin 查看和维护院系、课程、先修课、教学班、上课时间、学生/教师档案及选课记录，页面风格与标准 Django 后台一致。

## 主要特性
- 覆盖学生、教师、院系、课程、教学班、上课时间、选课记录、先修要求等核心实体，并附带完整外键、唯一约束与时间有效性校验。
- 自定义管理后台：教学班支持上课时间内联编辑，选课记录/课程/教师/学生均配置了列表筛选与搜索，方便教务人员使用。
- 种子数据：`bootstrap_demo` 命令会创建管理员账号、示例教师/学生、课程、先修关系、教学班与选课记录，可立即在后台查看，含时间冲突和未满足先修的示例场景。
- 与此前的 CLI 工具兼容：保留 `app.py` 供快速命令行演示，Web 管理场景使用 Django Admin。

## 目录结构
- `manage.py`：Django 管理入口。
- `university/`：Django 项目配置。
- `registrar/`：领域模型、管理后台配置、演示数据命令、迁移文件。
- `sql/`、`docs/`、`app.py`：原有 SQL 脚本、设计文档与命令行演示工具。

## 快速开始
1. **准备环境**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows方法
   pip install -r requirements.txt
   ```

2. **初始化数据库并迁移**
   ```bash
   python manage.py migrate
   ```

3. **导入示例数据（含管理员与演示账号）**
   ```bash
   python manage.py bootstrap_demo
   ```
   该命令会生成：
   - 超级管理员：`admin / admin123`
   - 教师：`carol`、`dave`（如果尚无密码，自动设置为 `ChangeMe123!` 并要求首次登录修改）
   - 学生：`alice`、`bob`（如果尚无密码，自动设置为 `ChangeMe123!` 并要求首次登录修改）
   - 课程、先修课、教学班及上课时间；Alice/Bob 的选课与成绩示例

4. **运行开发服务器并进入后台**
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```
   浏览器访问 `http://127.0.0.1:8000/accounts/login/` 选择“学生/教师登录”，或直接访问 `http://127.0.0.1:8000/admin/` 使用 `admin/admin123` 登录，即可看到院系、课程、教学班、上课时间、学生、教师、选课记录等模块并进行维护。

## 关键模型与规则
- **StudentProfile / InstructorProfile**：与 Django User 绑定的一对一档案，存储性别、院系、联系方式、专业/职称等。
- **Course / CourseSection / MeetingTime**：课程、教学班、上课时间（含“结束时间必须晚于开始时间”的校验）。
- **CoursePrerequisite**：记录每门课的先修课及最低要求成绩。
- **Enrollment**：选课状态（选课中/候补/退课/通过/未通过）、最终成绩及绩点，限制同一学生同一教学班唯一。

## 设计文档与 SQL
- `docs/database_design.md`：实体关系、约束与业务流程说明。
- `sql/schema.sql`、`sql/sample_data.sql`、`sql/queries.sql`：可迁移到其他数据库方言的原始脚本。

## 兼容的命令行演示
如果只想快速演示核心查询（成绩单、先修检查、时间冲突、容量统计等），仍可执行原有 CLI：
```bash
python app.py init-db
python app.py transcript alice
```

## 默认账号策略
- 在 Django Admin 中创建用户时，系统会自动分配默认密码 `ChangeMe123!`，无须手动输入密码。
- 教师/学生新账号首次登录会被强制跳转到密码修改页面；管理员账号默认无需强制改密。

## 学生/教师自助与审批流
- 面向学生的自助前台：报名、退课、重修申请、容量候补等请求可在线提交并查看进度。
- 重修、跨院选课、超学分、候补转正等事项进入审批流，包含审核日志留痕，教师/管理员均可处理。
- 教师工作台展示名下教学班、待审批列表，并提示“成绩填报锁定”状态；管理员首页提供统一审批入口。
- 成绩填报锁定字段用于控制是否允许教学班录入/修改成绩，可在后台切换。

## 后续可扩展方向
- 批量导入（学生名单/成绩）以及与教务系统、LDAP 的同步配置。
