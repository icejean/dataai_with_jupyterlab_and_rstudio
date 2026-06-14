# 注册到MCP Server
from jupyter_mcp import hook
hook.register(force=True)

# ============================================================
# 上海市二手房交易数据 — 数据预处理 Pipeline
# 参考: ~/python/Melbourne_housing_Pre.py
# ============================================================

import os
import pandas as pd
import numpy as np
import pymysql
from dotenv import load_dotenv 
from sqlalchemy import create_engine
import warnings
warnings.filterwarnings('ignore')

# ── 1. 从 MySQL 加载数据 ──
load_dotenv()
MYSQL_URI = f"mysql+pymysql://{os.getenv('MYSQLUSER')}:{os.getenv('MYSQLPASSWORD')}@{os.getenv('MYSQLHOST')}:{os.getenv('MYSQLPORT')}/{os.getenv('MYSQLDB')}"         
print(MYSQL_URI)

engine = create_engine(MYSQL_URI)
df = pd.read_sql('SELECT * FROM shanghai_housing WHERE deal_date >= "2015" AND deal_date < "2022"', con=engine)
print(f"原始数据: {df.shape}")
df.head(3)

# ── 2. 删除无价值列 ──
# city: 全是"上海"，无信息量
# heating: 全是 0
# property_id: 纯ID，无建模意义
# property_years: 98.7% 是"暂无数据"
drop_cols = ['city', 'heating', 'property_id', 'property_years']
df.drop(columns=drop_cols, inplace=True)
print(f"删除无价值列后: {df.shape}")

# ── 3. 去重 ──
df.drop_duplicates(inplace=True)
print(f"去重后: {df.shape}")

# ── 4. 删除极小类别 ──
# "上海周边"只有1条，删除
df = df[df['district'] != '上海周边'].copy()
# "使用权"只有2条，删除
df = df[~df['transaction_type'].isin(['使用权'])].copy()
# layout 中的 "车位" 非住宅交易，删除
df = df[df['layout'] != '车位'].copy()
# property_use 中的车库
df = df[df['property_use'] != '车库'].copy()
print(f"删除极小类别后: {df.shape}")

# ── 5. 特征工程: 解析 layout ──
# layout 格式: "2室1厅1厨1卫" 或 "0室0厅1厨0卫" 或 "--室--厅"
def parse_layout(layout_str):
    """从 layout 字符串提取室/厅/厨/卫数量"""
    import re
    rooms, halls, kitchens, bathrooms = 0, 0, 0, 0
    if pd.isna(layout_str) or layout_str == '--室--厅':
        return rooms, halls, kitchens, bathrooms
    # 匹配数字+室/厅/厨/卫
    m_room = re.search(r'(\d+)室', layout_str)
    m_hall = re.search(r'(\d+)厅', layout_str)
    m_kitchen = re.search(r'(\d+)厨', layout_str)
    m_bath = re.search(r'(\d+)卫', layout_str)
    if m_room: rooms = int(m_room.group(1))
    if m_hall: halls = int(m_hall.group(1))
    if m_kitchen: kitchens = int(m_kitchen.group(1))
    if m_bath: bathrooms = int(m_bath.group(1))
    return rooms, halls, kitchens, bathrooms

df[['rooms', 'halls', 'kitchens', 'bathrooms']] = df['layout'].apply(
    lambda x: pd.Series(parse_layout(x))
)
print(f"解析 layout 后: rooms={df['rooms'].min()}~{df['rooms'].max()}, "
      f"bathrooms={df['bathrooms'].min()}~{df['bathrooms'].max()}")

# ── 6. 特征工程: 解析 floor_level ──
# 格式: "高楼层(共6层)" "低楼层(共18层)" "地下室(共1层)" "地下室" "未知(共6层)"
def parse_floor(floor_str):
    """提取楼层位置类别、总层数"""
    import re
    level, total = '其他', 0
    if pd.isna(floor_str):
        return '其他', 0
    # 总层数
    m_total = re.search(r'共(\d+)层', floor_str)
    if m_total:
        total = int(m_total.group(1))
    # 楼层位置
    if '高楼层' in floor_str:
        level = '高'
    elif '中楼层' in floor_str:
        level = '中'
    elif '低楼层' in floor_str:
        level = '低'
    elif '地下室' in floor_str:
        level = '地下室'
    return level, total

df[['floor_level_cat', 'total_floors']] = df['floor_level'].apply(
    lambda x: pd.Series(parse_floor(x))
)
print(f"解析 floor_level 后: total_floors={df['total_floors'].min()}~{df['total_floors'].max()}")

# ── 7. 特征工程: 解析 elevator_ratio ──
# 格式: "一梯三户" "两梯四户" ... 也可能"暂无数据"
def parse_elevator_ratio(ratio_str):
    """提取电梯数和每层户数"""
    import re
    elevators, units = 0, 0
    if pd.isna(ratio_str) or ratio_str == '暂无数据':
        return elevators, units
    cn_to_num = {'一': 1, '两': 2, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8}
    m_elev = re.search(r'([一两二三四五六七八九])梯', ratio_str)
    m_unit = re.search(r'([一两二三四五六七八九])户', ratio_str)
    if m_elev:
        elevators = cn_to_num.get(m_elev.group(1), 0)
    if m_unit:
        units = cn_to_num.get(m_unit.group(1), 0)
    return elevators, units

df[['elevator_count', 'units_per_floor']] = df['elevator_ratio'].apply(
    lambda x: pd.Series(parse_elevator_ratio(x))
)
print(f"解析 elevator_ratio 后: elevator_count={df['elevator_count'].min()}~{df['elevator_count'].max()}")

# ── 8. 特征工程: 日期处理 ──
df['list_date'] = pd.to_datetime(df['list_date'], format='%Y.%m.%d', errors='coerce')
df['deal_date'] = pd.to_datetime(df['deal_date'], format='%Y.%m.%d', errors='coerce')
df['list_year'] = df['list_date'].dt.year
df['list_month'] = df['list_date'].dt.month
df['deal_year'] = df['deal_date'].dt.year
df['deal_month'] = df['deal_date'].dt.month
print(f"日期范围: {df['deal_date'].min()} ~ {df['deal_date'].max()}")

# ── 9. 特征工程: 房龄 ──
# year_built 为 0 的视为缺失，用中位数填充
df['year_built'] = df['year_built'].replace(0, np.nan)
year_built_median = df['year_built'].median()
df['year_built'].fillna(year_built_median, inplace=True)
df['year_built'] = df['year_built'].astype(int)
df['house_age'] = df['deal_year'] - df['year_built']
df.loc[df['house_age'] < 0, 'house_age'] = 0  # 个别年份异常
print(f"房龄范围: {df['house_age'].min()} ~ {df['house_age'].max()} 年")

# ── 10. 特征工程: 单位面积价格 ──
# deal_price 单位是"万元"，building_area 是平方米
# 过滤异常 building_area（>2000平米 或 <10平米认为异常）
df = df[(df['building_area'] >= 10) & (df['building_area'] <= 2000)].copy()
df['unit_price'] = (df['deal_price'] * 10000 / df['building_area']).round(0)  # 元/平米
print(f"单价范围: {df['unit_price'].min():.0f} ~ {df['unit_price'].max():.0f} 元/平米")

# ── 11. 处理 orientation（朝向）──
# 取主朝向（多个朝向取第一个），"暂无数据" 填入 "其他"
def get_main_orientation(ori_str):
    if pd.isna(ori_str) or ori_str == '暂无数据':
        return '其他'
    # 多个朝向时取第1个
    main = ori_str[:1] if len(ori_str) >= 1 else '其他'
    if main in '南北东西':
        return main
    return '其他'

df['main_orientation'] = df['orientation'].apply(get_main_orientation)
print(f"主朝向分布:\n{df['main_orientation'].value_counts()}")

# ── 12. 异常值处理: 成交价 ──
# 成交价范围: 1万 ~ 1350万，价格小于10万的可能非正常交易，过滤
# 价格过高也过滤（用 IQR 方法）
Q1 = df['deal_price'].quantile(0.01)
Q99 = df['deal_price'].quantile(0.99)
print(f"deal_price 1%分位={Q1}, 99%分位={Q99}")
df = df[(df['deal_price'] >= Q1) & (df['deal_price'] <= Q99)].copy()
print(f"过滤价格极端值后: {df.shape}")

# ── 13. 异常值处理: 挂牌价 ──
# list_price 有 0 值，不合理
df = df[df['list_price'] > 0].copy()
# 挂牌价与成交价比例异常
df['price_ratio'] = df['list_price'] / df['deal_price']
df = df[(df['price_ratio'] >= 0.5) & (df['price_ratio'] <= 5)].copy()
print(f"过滤价格比异常后: {df.shape}")

# ── 14. 异常值处理: 看房/关注/浏览 ──
# viewings, followers, pageviews 有大量 0值，保留但标记
df['has_viewings'] = (df['viewings'] > 0).astype(int)
df['has_followers'] = (df['followers'] > 0).astype(int)

# ── 15. 异常值处理: days_to_deal ──
# 最大2208天≈6年，保留上限 730天（2年）
# 这一步过滤了近5万条记录，可以考虑不做这个过滤
# df = df[df['days_to_deal'] <= 730].copy()
# print(f"过滤成交天数极端后: {df.shape}")

# ── 16. 处理 "暂无数据" / 未知值 ──
# has_elevator
df['has_elevator_flag'] = df['has_elevator'].map({'有': 1, '无': 0, '暂无数据': 0})
# building_type
df['building_type_clean'] = df['building_type'].replace('暂无数据', '其他')
# room_structure
df['room_structure_clean'] = df['room_structure'].replace('暂无数据', '平层')
# ownership_type
df['ownership_type_clean'] = df['ownership_type'].replace('暂无数据', '未知')
# decoration: "其他" 保留，作为基准类别
# business_area: 保留

# ── 17. 删除中间过程列（不再需要的原始文本列）──
cols_to_drop = [
    'layout', 'floor_level', 'elevator_ratio', 'orientation',
    'has_elevator', 'building_type', 'room_structure', 'ownership_type',
    'list_date', 'deal_date',  # 已提取年/月
    'price_ratio'  # 辅助过滤列
]
df.drop(columns=cols_to_drop, inplace=True)
print(f"删除原始文本列后: {df.shape}")

# ── 18. 分类变量编码 ──
from sklearn.preprocessing import LabelEncoder

# 标签编码: 高基数类别
le_cols = ['district', 'business_area', 'community']
for col in le_cols:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col].astype(str))
    print(f"{col}: {len(le.classes_)} 个唯一值")

# 独热编码: 低基数类别
dummy_cols = ['floor_level_cat', 'main_orientation', 'decoration', 'structure',
              'transaction_type', 'property_use', 'building_type_clean',
              'room_structure_clean', 'ownership_type_clean']
df = pd.get_dummies(df, columns=dummy_cols, prefix=dummy_cols, drop_first=False)
print(f"独热编码后: {df.shape}")

# ── 19. 目标变量处理: 对数转换 ──
df['log_deal_price'] = np.log(df['deal_price'])
df['log_unit_price'] = np.log(df['unit_price'])

# ── 20. 数值型列检查与处理（中位数填充）──
numeric_cols = ['interior_area', 'ownership_years', 'viewings', 'followers', 'price_adjustments']
for col in numeric_cols:
    if df[col].dtype in ['float64', 'int64']:
        df[col].fillna(df[col].median(), inplace=True)

# ── 21. 随机重排 ──
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

print(f"\n{'='*60}")
print(f"预处理完成！最终数据集: {df.shape}")
print(f"目标变量: deal_price (万元), log_deal_price (对数), unit_price (元/平米), log_unit_price (对数)")
print(f"{'='*60}")

# 最终确认无缺失
print(f"\n剩余缺失值:\n{df.isnull().sum()[df.isnull().sum() > 0]}")
print(f"\n数值列统计:\n{df.describe().T}")


# ============================================================
# 1. log_unit_price 分布图
# ============================================================
import matplotlib
matplotlib.rcdefaults()
matplotlib.rcParams['font.sans-serif'] = ['SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False
import matplotlib.pyplot as plt
import seaborn as sns

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

axes[0].hist(df['log_unit_price'], bins=80, density=True, alpha=0.6, color='steelblue', edgecolor='white')
axes[0].set_xlabel('log(单价 元/㎡)')
axes[0].set_ylabel('密度')
axes[0].set_title('log_unit_price 分布')
axes[0].axvline(df['log_unit_price'].mean(), color='red', ls='--', lw=1, label=f'均值={df["log_unit_price"].mean():.2f}')
axes[0].axvline(df['log_unit_price'].median(), color='orange', ls='--', lw=1, label=f'中位数={df["log_unit_price"].median():.2f}')
axes[0].legend()

axes[1].boxplot(df['log_unit_price'], vert=True, patch_artist=True,
                boxprops=dict(facecolor='lightblue'))
axes[1].set_ylabel('log(单价 元/㎡)')
axes[1].set_title('log_unit_price 箱线图')
axes[1].set_xticks([])

plt.tight_layout()
plt.show()

# ============================================================
# 2. 随机森林特征重要性评估（目标: log_unit_price）
# ============================================================
from sklearn.ensemble import RandomForestRegressor
from time import time

# 特征与目标定义
target = 'log_unit_price'
exclude_cols = ['deal_price', 'log_deal_price', 'unit_price', 'log_unit_price']
feature_cols = [c for c in df.columns if c not in exclude_cols]

X = df[feature_cols].copy()
y = df[target].copy()
bool_cols = X.select_dtypes(include='bool').columns
X[bool_cols] = X[bool_cols].astype(int)

print(f"特征数: {X.shape[1]}, 样本数: {X.shape[0]}")

t0 = time()
rf = RandomForestRegressor(
    n_estimators=50, max_depth=15, max_features='sqrt',
    n_jobs=-1, random_state=42
)
rf.fit(X, y)
print(f"训练完成: {time()-t0:.1f}s")

# 特征重要性（倒序排列，重要在前）
importance_df = pd.DataFrame({
    'feature': feature_cols,
    'importance': rf.feature_importances_
}).sort_values('importance', ascending=False).reset_index(drop=True)

print(f"\n{'='*60}")
print(f"{'特征重要性 Top 30':^60}")
print(f"{'='*60}")
for i, row in importance_df.head(30).iterrows():
    bar = '█' * int(row['importance'] * 100)
    print(f"{i+1:>3}. {row['feature']:<30s} {row['importance']:.4f}  {bar}")

print(f"\n共计 {len(importance_df)} 个特征")

# 可视化 Top 20
fig, ax = plt.subplots(figsize=(10, 8))
top20 = importance_df.head(20)
ax.barh(range(len(top20)), top20['importance'].values, color='steelblue')
ax.set_yticks(range(len(top20)))
ax.set_yticklabels(top20['feature'].values)
ax.invert_yaxis()
ax.set_xlabel('重要性')
ax.set_title('随机森林特征重要性 Top 20')
plt.tight_layout()
plt.show()


# ============================================================
# 3. 数据集划分: 70% 训练 / 15% 验证 / 15% 测试
# ============================================================
from sklearn.model_selection import train_test_split

# 目标变量
target = 'log_unit_price'
exclude_cols = ['deal_price', 'log_deal_price', 'unit_price', 'log_unit_price']
feature_cols = [c for c in df.columns if c not in exclude_cols]

X = df[feature_cols].copy()
y = df[target].copy()

# bool 转 int
bool_cols = X.select_dtypes(include='bool').columns
X[bool_cols] = X[bool_cols].astype(int)

# 随机重排（确保顺序不影响划分）
np.random.seed(42)
shuffle_idx = np.random.permutation(len(X))
X = X.iloc[shuffle_idx].reset_index(drop=True)
y = y.iloc[shuffle_idx].reset_index(drop=True)

# 先分出测试集 (15%)
X_temp, X_test, y_temp, y_test = train_test_split(
    X, y, test_size=0.15, random_state=42
)
# 再从剩余 (85%) 中分出验证集: 15/85 ≈ 0.1765
val_ratio = 0.15 / 0.85  # ≈ 0.1765
X_train, X_val, y_train, y_val = train_test_split(
    X_temp, y_temp, test_size=val_ratio, random_state=42
)

print(f"{'='*50}")
print(f"数据集划分完成")
print(f"{'='*50}")
print(f"训练集:   {X_train.shape[0]:>7,} 行 ({X_train.shape[0]/len(X)*100:.1f}%)")
print(f"验证集:   {X_val.shape[0]:>7,} 行 ({X_val.shape[0]/len(X)*100:.1f}%)")
print(f"测试集:   {X_test.shape[0]:>7,} 行 ({X_test.shape[0]/len(X)*100:.1f}%)")
print(f"{'='*50}")
print(f"总计:     {len(X):>7,} 行")
print(f"特征数:   {X.shape[1]}")

# 验证目标变量在各集上的分布一致性
print(f"\n目标变量 log_unit_price 分布对比:")
for name, yy in [('训练集', y_train), ('验证集', y_val), ('测试集', y_test)]:
    print(f"  {name}: 均值={yy.mean():.3f}  标准差={yy.std():.3f}  中位数={yy.median():.3f}")


# ============================================================
# 4. LightGBM 模型训练与拟合效果评估
# ============================================================
import lightgbm as lgb
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import matplotlib
matplotlib.rcdefaults()
matplotlib.rcParams['font.sans-serif'] = ['SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False
import matplotlib.pyplot as plt

# ── 训练 LightGBM ──
t0 = time()
lgb_model = lgb.LGBMRegressor(
    n_estimators=1000,
    learning_rate=0.05,
    max_depth=12,
    num_leaves=127,
    subsample=0.8,
    colsample_bytree=0.8,
    min_child_samples=20,
    reg_alpha=0.1,
    reg_lambda=0.1,
    random_state=42,
    n_jobs=-1,
    verbose=-1
)

lgb_model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    eval_metric='rmse',
    callbacks=[lgb.early_stopping(50), lgb.log_evaluation(100)]
)
print(f"LightGBM 训练完成: {time()-t0:.1f}s")

# ── 预测 ──
y_train_pred = lgb_model.predict(X_train)
y_val_pred = lgb_model.predict(X_val)
y_test_pred = lgb_model.predict(X_test)

# ── 回归指标 ──
def calc_metrics(y_true, y_pred, name):
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    # 还原到原始单价的 MAPE
    y_true_orig = np.exp(y_true)
    y_pred_orig = np.exp(y_pred)
    mape = np.mean(np.abs((y_true_orig - y_pred_orig) / y_true_orig)) * 100
    return {'数据集': name, 'R²': r2, 'RMSE': rmse, 'MAE': mae, 'MAPE(%)': mape}

metrics = []
for y_true, y_pred, name in [(y_train, y_train_pred, '训练集'),
                               (y_val, y_val_pred, '验证集'),
                               (y_test, y_test_pred, '测试集')]:
    m = calc_metrics(y_true, y_pred, name)
    metrics.append(m)
    print(f"{name}: R²={m['R²']:.4f}  RMSE={m['RMSE']:.4f}  MAE={m['MAE']:.4f}  MAPE={m['MAPE(%)']:.2f}%")

metrics_df = pd.DataFrame(metrics)

# ── 拟合效果散点图（按真实值排序）──
# 用测试集画图
test_df = pd.DataFrame({'actual': y_test, 'predicted': y_test_pred})
test_df = test_df.sort_values('actual').reset_index(drop=True)
test_df['idx'] = test_df.index

# ±30% 在 log 空间中的宽度 = log(1.3)
log_band = np.log(1.3)

fig, ax = plt.subplots(figsize=(16, 7))

# 黄色带状区域
ax.fill_between(
    test_df['idx'],
    test_df['actual'] - log_band,
    test_df['actual'] + log_band,
    color='gold', alpha=0.3, label='±30% 偏差带'
)

# 先画预测值（蓝色），再画真实值（红色）覆盖在上面
ax.scatter(test_df['idx'], test_df['predicted'],
           c='steelblue', s=1, alpha=0.4, label='预测值')

ax.scatter(test_df['idx'], test_df['actual'],
           c='red', s=1, alpha=0.4, label='真实值')

ax.set_xlabel('样本序号（按真实值排序）')
ax.set_ylabel('log(单价 元/㎡)')
ax.set_title('LightGBM 拟合效果（测试集）')
ax.legend(loc='upper left', markerscale=5)

# 添加性能指标文本
info_text = (f"测试集  R² = {metrics[2]['R²']:.4f}\n"
             f"RMSE = {metrics[2]['RMSE']:.4f}\n"
             f"MAE  = {metrics[2]['MAE']:.4f}\n"
             f"MAPE = {metrics[2]['MAPE(%)']:.2f}%")
ax.text(0.98, 0.05, info_text, transform=ax.transAxes,
        va='bottom', ha='right', fontsize=11,
        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))

plt.tight_layout()
plt.show()


# ============================================================
# 5. MAPE 还原到原始单价量纲的偏差分析
# ============================================================
# 将 log_unit_price 预测值还原为原始单价（元/㎡）
unit_true = np.exp(y_test)
unit_pred = np.exp(y_test_pred)

# 绝对误差（元/㎡）
abs_error = np.abs(unit_true - unit_pred)
pct_error = abs_error / unit_true * 100  # 百分比误差

print(f"{'='*60}")
print(f"原始单价偏差分析（测试集，{len(unit_true):,} 条）")
print(f"{'='*60}")

# MAPE 最值的区间
for q in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
    val = np.percentile(abs_error, q)
    pct = np.percentile(pct_error, q)
    print(f"  P{q:>2}: 绝对偏差 ≤ {val:>8,.0f} 元/㎡  |  百分比偏差 ≤ {pct:>5.2f}%")

print(f"\n{'─'*60}")
print(f"  均值 (MAE):      {abs_error.mean():>8,.0f} 元/㎡  ({pct_error.mean():.2f}%)")
print(f"  中位数:          {np.median(abs_error):>8,.0f} 元/㎡  ({np.median(pct_error):.2f}%)")
print(f"  标准差:          {abs_error.std():>8,.0f} 元/㎡")
print(f"  最大值:          {abs_error.max():>8,.0f} 元/㎡  ({pct_error.max():.2f}%)")
print(f"{'─'*60}")

# 按单价区间分段统计偏差
print(f"\n{'='*60}")
print(f"按单价区间分段的误差分布")
print(f"{'='*60}")
unit_bins = [0, 20000, 40000, 60000, 80000, 100000, 150000, 999999]
unit_labels = ['<2万', '2~4万', '4~6万', '6~8万', '8~10万', '10~15万', '>15万']
df_bins = pd.cut(unit_true, bins=unit_bins, labels=unit_labels, right=False)

seg_stats = pd.DataFrame({
    'count': unit_true.groupby(df_bins).count(),
    '均价(元/㎡)': unit_true.groupby(df_bins).mean().round(0),
    'MAE(元/㎡)': abs_error.groupby(df_bins).mean().round(0),
    'MAPE(%)': pct_error.groupby(df_bins).mean().round(2),
    '中位误差(元/㎡)': abs_error.groupby(df_bins).median().round(0)
})
seg_stats = seg_stats.dropna(subset=['均价(元/㎡)'])  # 去掉空档区间
seg_stats.index.name = '单价区间'
print(seg_stats.to_string())

# ── 偏差分布柱状图 ──
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# 左: 绝对偏差分布
axes[0].hist(abs_error, bins=60, color='steelblue', edgecolor='white', alpha=0.7)
axes[0].axvline(abs_error.mean(), color='red', ls='--', lw=2, label=f'MAE={abs_error.mean():.0f}')
axes[0].axvline(np.median(abs_error), color='orange', ls='--', lw=2, label=f'中位数={np.median(abs_error):.0f}')
axes[0].set_xlabel('绝对偏差 (元/㎡)')
axes[0].set_ylabel('样本数')
axes[0].set_title('预测绝对偏差分布')
axes[0].legend()

# 右: 百分比偏差分布
axes[1].hist(pct_error, bins=60, color='steelblue', edgecolor='white', alpha=0.7)
axes[1].axvline(pct_error.mean(), color='red', ls='--', lw=2, label=f'MAPE={pct_error.mean():.2f}%')
axes[1].axvline(np.median(pct_error), color='orange', ls='--', lw=2, label=f'中位数={np.median(pct_error):.2f}%')
axes[1].set_xlabel('百分比偏差 (%)')
axes[1].set_ylabel('样本数')
axes[1].set_title('预测百分比偏差分布')
axes[1].legend()

plt.tight_layout()
plt.show()


# ============================================================
# 6. 模型持久化：保存到磁盘 & 重新加载
# ============================================================
import joblib
import os

# ── 6.1 保存模型及预处理状态 ──
model_dir = "model"
os.makedirs(model_dir, exist_ok=True)

# 模型文件
joblib.dump(lgb_model, f"{model_dir}/lgb_model.pkl")
print(f"✅ 模型已保存: {model_dir}/lgb_model.pkl")

# 保存特征列名（加载模型后重建 DataFrame 时需要）
joblib.dump(feature_cols, f"{model_dir}/feature_cols.pkl")
print(f"✅ 特征列名已保存: {model_dir}/feature_cols.pkl")

# 保存 LabelEncoder（如果重新训练前还做了标签编码，这里留个记录）
print(f"\n模型文件大小: {os.path.getsize(f'{model_dir}/lgb_model.pkl') / 1024:.1f} KB")

# ── 6.2 从磁盘重新加载模型并预测 ──
print(f"\n{'='*50}")
print("从磁盘重新加载模型...")
print(f"{'='*50}")

loaded_model = joblib.load(f"{model_dir}/lgb_model.pkl")
loaded_features = joblib.load(f"{model_dir}/feature_cols.pkl")

# 用测试集验证加载后的模型
X_test_loaded = X_test[loaded_features]  # 确保列顺序一致
y_test_reload_pred = loaded_model.predict(X_test_loaded)

# 对比原始预测和重新加载后的预测是否一致
diff = np.abs(y_test_pred - y_test_reload_pred).max()
print(f"原始预测 vs 重载模型预测 最大差异: {diff:.2e}")
if diff < 1e-10:
    print("✅ 模型保存/加载验证通过，预测结果完全一致！")
else:
    print("⚠️ 预测有微小差异，需检查")

# 用重新加载的模型跑一遍测试集指标
unit_true = np.exp(y_test)
unit_pred_reload = np.exp(y_test_reload_pred)
mae_reload = np.mean(np.abs(unit_true - unit_pred_reload))
mape_reload = np.mean(np.abs(unit_true - unit_pred_reload) / unit_true) * 100
r2_reload = r2_score(y_test, y_test_reload_pred)

print(f"\n重载模型 - 测试集指标:")
print(f"  R²    = {r2_reload:.4f}")
print(f"  MAE   = {mae_reload:,.0f} 元/㎡")
print(f"  MAPE  = {mape_reload:.2f}%")

print(f"\n✅ 模型已保存至 {model_dir}/ 目录，可在任何脚本中加载使用。")
print(f"   使用方式: model = joblib.load('{model_dir}/lgb_model.pkl')")

