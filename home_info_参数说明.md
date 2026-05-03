# 家园接口参数说明

## 接口信息

- **URL**: `GET/POST /api/v1/games/rocom/ingame/home/info`
- **请求参数**: `uid` (用户ID), `wait_ms` (可选, 同步等待时间)

---

## 响应结构

### 顶层字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | int | 响应码，0 表示成功 |
| `message` | string | 响应消息 |
| `data` | object | 数据主体 |

### data 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| `rows` | array | 扁平字段列表，包含返回码等基本信息 |
| `home_info` | object | 家园详细信息 |
| `meta` | object | 任务元信息 |

---

## rows 数组元素

| 字段 | 类型 | 说明 |
|------|------|------|
| `level` | int | 层级 |
| `field` | string | 字段名 |
| `label` | string | 字段标签（中文） |
| `value` | string | 字段值 |

---

## home_info 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| `ret_info` | object | 返回信息 |
| `ret_info.ret_code` | int | 返回码 |
| `uin` | int | 用户ID |
| `friend_cell_home_brief_info` | object | 家园简要信息 |
| `friend_home_brief_info` | object | 家园基本信息 |
| `home_feature_opened` | boolean | 家园功能是否开启 |

---

## friend_cell_home_brief_info 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| `uin` | int | 用户ID |
| `home_plant_info` | object | 种植信息 |
| `home_pets` | array | 居住精灵列表 |

---

## home_plant_info 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| `home_plant_land_list` | array | 地块列表 |
| `unlock` | boolean | 是否已解锁 |

### home_plant_land_list 数组元素

| 字段 | 类型 | 说明 |
|------|------|------|
| `land_index` | int | 地块索引 |
| `home_plant_list` | array | 该地块的植物列表 |

### home_plant_list 数组元素

| 字段 | 类型 | 说明 |
|------|------|------|
| `plant_id` | int | 植物实例ID |
| `plant_state` | int | 植物状态（1=生长中） |
| `plant_seed_id` | int | 种子配置ID |
| `plant_rip_time` | int | 成熟时间戳 |
| `plant_harvest_num` | int | 已收获数量 |
| `plant_tab_id` | int | 标签页ID |
| `plant_steal_account` | int | 被偷数量 |
| `plant_can_steal_account` | int | 可偷数量 |
| `slot_index` | int | 槽位索引 |

---

## home_pets 数组元素

每个元素包含 `home_pet_info` 和 `display_info` 两部分。

### home_pet_info 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| `pet_gid` | int | 精灵全局唯一ID |
| `pet_cfg_id` | int | 精灵配置ID |
| `furniture_guid` | int | 家具GUID（0表示无家具） |
| `status` | int | 状态码（1700=喂养中，1704=休息） |
| `speciality_id` | int | 特性ID |
| `feed_round` | int | 喂养轮次 |
| `real_speciality_ids` | array | 实际特性ID列表 |
| `name` | string | 精灵名称 |
| `feed_info` | object | 喂养信息（可选） |
| `awards_info` | object | 奖励信息 |
| `pos` | object | 位置坐标 {x, y, z} |

#### feed_info 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| `food_info` | object | 食物信息 {bag_item_id, num} |
| `begin_time` | int | 开始喂养时间戳 |
| `time_cost` | int | 喂养耗时（纳秒） |

### display_info 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| `base_conf_id` | int | 基础配置ID |
| `gender` | int | 性别（1=男，2=女） |
| `level` | int | 等级 |
| `mutation_type` | int | 变异类型（0=无，9=变异） |
| `energy` | int | 能量值 |
| `blood_id` | int | 血统ID |
| `nature` | int | 性格ID |
| `changed_nature_neg_attr_type` | int | 性格修正-负面属性类型 |
| `changed_nature_pos_attr_type` | int | 性格修正-正面属性类型 |
| `speciality_id` | int | 特性ID |
| `last_breakthrough_lv` | int | 上次突破等级 |
| `name` | string | 精灵名称 |
| `attribute_new_info` | object | 新版属性信息 |
| `attribute_info` | object | 属性详情 |
| `skill` | object | 技能信息 |
| `glass_info` | object | 玻璃信息 |

### attribute_info 对象

包含六维属性：`hp`（生命）、`attack`（攻击）、`special_attack`（特攻）、`defense`（防御）、`special_defense`（特防）、`speed`（速度）

每个属性包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| `total_race` | int | 种族值总和 |
| `talent` | int | 天赋值 |
| `base_value` | int | 基础值 |
| `effort_exp` | int | 努力值经验 |
| `effort_lv` | int | 努力值等级 |
| `effort_add` | int | 努力值加成 |
| `talent_add_value` | int | 天赋加成值 |

### skill 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| `skill_data` | array | 技能数据列表 |

### skill_data 数组元素

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 技能ID |
| `type` | int | 技能类型 |
| `pos` | int | 技能位置 |
| `unlock_need_lv` | int | 解锁所需等级 |
| `raw_id` | int | 原始ID |
| `conf_idx` | int | 配置索引 |
| `skill_src` | int | 技能来源 |
| `unlock_need_base_id` | int | 解锁所需基础ID |
| `is_learned` | boolean | 是否已学习 |
| `is_equipped` | boolean | 是否已装备 |
| `use_times` | int | 使用次数 |

### glass_info 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| `glass_type` | object | 玻璃类型 {value, name} |
| `glass_value` | int | 玻璃值 |

---

## friend_home_brief_info 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| `home_name` | string | 家园名称 |
| `home_name_hex` | string | 家园名称十六进制编码 |
| `home_experience` | int | 家园经验值 |
| `home_level` | int | 家园等级 |
| `room_level` | int | 房间等级 |
| `home_comfort_level` | int | 舒适度 |
| `room_expansion_info` | object | 房间扩建信息 |

### room_expansion_info 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| `room_level` | int | 房间等级 |
| `expansion_start_timestamp` | int | 扩建开始时间戳 |

---

## meta 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| `task_id` | string | 任务ID |
| `worker_id` | string | 工作节点ID |
| `created_at` | float | 创建时间戳 |
| `finished_at` | float | 完成时间戳 |

---

## have_egg 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `have_egg` | boolean | 是否有蛋 |

---

## 状态码说明

### status 状态码

| 值 | 说明 |
|------|------|
| 1700 | 喂养中 |
| 1704 | 休息中 |

### plant_state 植物状态

| 值 | 说明 |
|------|------|
| 1 | 生长中 |
