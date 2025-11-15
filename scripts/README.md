# 脚本使用说明

这个目录包含用于管理和分析数据的实用脚本。

## 脚本列表

### 1. check_status.py
快速检查数据收集状态

**用法:**
```bash
python scripts/check_status.py
```

**功能:**
- 显示总事件数、正在观察中、已完成观察等统计信息
- 检查是否有足够的数据进行 Granger 因果检验
- 显示最近完成的结果

### 2. analyze_granger.py
执行 Granger 因果检验分析

**用法:**
```bash
python scripts/analyze_granger.py
```

**功能:**
- 从 Redis 获取所有完成的结果
- 构建时间序列（转账金额 vs 价格变化）
- 执行 Granger 因果检验
- 显示分析结果

**要求:**
- 至少需要 34 个完成的事件

### 3. view_active.py
查看当前活跃的观察窗口

**用法:**
```bash
python scripts/view_active.py
```

**功能:**
- 显示所有正在观察中的事件
- 显示每个事件的币种、金额、基准价格
- 显示剩余观察时间和快照数量

### 4. recover_expired.py
恢复过期的观察窗口

**用法:**
```bash
python scripts/recover_expired.py
```

**功能:**
- 检查所有活跃的观察窗口
- 如果发现已过期但未完成的观察窗口，自动完成它们
- 获取当前价格并计算最终结果

**使用场景:**
- 服务重启后，如果有观察窗口在断开期间过期
- 定期运行以确保没有遗漏的观察窗口

### 5. export_data.py
导出数据到 CSV

**用法:**
```bash
# 使用默认文件名（带时间戳）
python scripts/export_data.py

# 指定文件名
python scripts/export_data.py my_export.csv
```

**功能:**
- 导出所有完成的结果到 CSV 文件
- 包含事件信息、价格变化、方向等
- 文件保存在 `data/results/` 目录

## 使用示例

### 日常检查
```bash
# 1. 检查数据状态
python scripts/check_status.py

# 2. 查看活跃窗口
python scripts/view_active.py
```

### 执行分析
```bash
# 1. 先检查数据是否充足
python scripts/check_status.py

# 2. 如果数据充足，执行分析
python scripts/analyze_granger.py
```

### 服务重启后
```bash
# 1. 检查状态
python scripts/check_status.py

# 2. 恢复过期的观察窗口（如果有）
python scripts/recover_expired.py

# 3. 再次检查状态
python scripts/check_status.py
```

### 数据备份
```bash
# 导出数据
python scripts/export_data.py backup_$(date +%Y%m%d).csv
```

## 注意事项

1. **运行环境**: 确保已激活虚拟环境并安装了所有依赖
2. **Redis 连接**: 确保 Redis 服务正在运行
3. **数据量**: Granger 分析需要至少 34 个完成的事件
4. **权限**: 确保脚本有执行权限（`chmod +x scripts/*.py`）

## 故障排除

### 连接 Redis 失败
```bash
# 检查 Redis 是否运行
docker-compose ps

# 启动 Redis
docker-compose up -d
```

### 数据不足
- 等待至少 24 小时让观察窗口完成
- 检查 `main_ws.py` 是否正常运行
- 运行 `check_status.py` 查看当前状态

### 脚本无法运行
```bash
# 确保在项目根目录
cd /path/to/whale_alert_trends

# 激活虚拟环境
source venv/bin/activate

# 运行脚本
python scripts/check_status.py
```

