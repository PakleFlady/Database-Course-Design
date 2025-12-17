# 实验设计报告（课程注册与成绩管理系统）

## 1. 实验目的
- 验证数据库主键/唯一性设计（学号、课程代码、教学班组合、先修组合、账号一对一）。
- 通过典型业务流程（选课、时间冲突、先修校验、学分上下限、重修/跨院审批、成绩与绩点统计）检验约束、检查条件与应用逻辑的正确性。
- 基于真实样例数据生成可复现实验，产出可读的结果（成绩单、GPA、通过率、冲突提示）。

## 2. 环境与工具
- 数据库：PostgreSQL（生产）或 SQLite（教学演示，使用 `app.py` 内置 schema 与样例数据）。
- 代码与 DDL：`registrar/models.py`、`sql/schema.sql`、`sql/sample_data.sql`、`sql/queries.sql`、`app.py`。
- 运行方式：Django 管理后台 + CLI（`python app.py <command>`）。

## 3. 数据与约束概览
- 关键唯一性：`student_number` 非空唯一；`course_code` 唯一；`(course_id, semester_id, section_code)` 唯一；`(course_id, prereq_course_id)` 复合主键；选课 `(student_id, section_id)` 唯一。
- 检查约束：容量/候补容量非负；课程学分>0；学期开始日期早于结束日期；时间段必须 start < end；状态枚举限定（enrolling/dropped/passed/failed 等）。
- 自动生成：学生学号按“年份+院系编号+序号”生成；院系 numeric_code 按现有最大值递增。

## 4. 核心实验用例
1. **先修未满足拦截**：尝试为学生选 `CSE200`（先修 `CSE100`，最低 C），若未通过则返回未满足列表。
2. **时间冲突检测**：请求加入与已选课程同一天且交叠时段的教学班，应返回冲突的 section 列表。
3. **学分上下限**：计算学期计划学分，若 <10 或 >40，应标记 `OUT_OF_RANGE` 并拒绝导出课表。
4. **容量与候补**：当选课人数达到容量，保持状态为 enrolling 但在 UI/审批中提示容量已满，可通过 EnrollmentOverride/审批记录放行。
5. **成绩与绩点**：生成成绩单与 GPA，确认通过/需重修标记与绩点加权计算正确。
6. **重修/跨院/超学分审批**：提交申请记录 -> 审批 -> 审批日志生成，确保状态流转符合枚举。

## 5. 实施步骤
1. 初始化：
   - Django：`python manage.py migrate && python manage.py bootstrap_demo`。
   - SQLite 演示：`python app.py init-db`（自动导入样例数据）。
2. 运行 CLI 检查：
   - `python app.py prereq alice CSE200`（先修校验）。
   - `python app.py conflict alice 2`（时间冲突检查）。
   - `python app.py credit-load alice 2025FALL`（学分上下限）。
   - `python app.py capacity 2`（容量/候补）。
   - `python app.py transcript alice`（成绩单与 GPA）。
   - `python app.py pass-rate 2025FALL` / `gpa-distribution`（通过率与绩点分布）。
3. SQL 直接验证（PostgreSQL）：执行 `sql/queries.sql` 中对应编号的查询，替换参数 `:student_id`/`:course_id` 等。
4. 审批流程：在 Django Admin 的“学生自助申请”新增重修/跨院/超学分记录，设置审批人并保存，确认“审批日志”自动生成。

## 6. 预期结果与判定
- 先修不满足返回至少一条缺失记录；满足时返回空集/OK 提示。
- 时间冲突返回冲突 section_id 列表；无冲突时显示“No conflicts detected.”。
- 学分结果在 10–40 之间标记 `OK`，否则 `OUT_OF_RANGE`。
- 容量查询显示 `enrolled` 不超过 `capacity`；超过时需通过 override/审批才可入选。
- 成绩单按学期排序，GPA 为 (Σ绩点×学分)/Σ学分，保留两位小数；低绩点课程标记需重修。
- 审批完成后，申请状态从 pending -> approved/rejected，并在审批日志中出现对应动作。

## 7. 扩展与注意事项
- 如需并发压力测试，可在事务中对 `course_sections` 做行级锁或使用可串行化隔离级别，观察容量竞争是否被正确序列化。
- 可在测试库开启触发器/审计表记录成绩变更，验证审计链路完整性。
- 若切换数据库，请确认 JSON/TIMESTAMP 兼容性（SQLite 演示版使用 TEXT 存储 JSON）。
