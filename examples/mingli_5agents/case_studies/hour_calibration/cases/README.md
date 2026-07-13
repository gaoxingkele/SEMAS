# 案例输入格式

每个案例一个 JSON 文件，字段如下：

```json
{
  "case_id": "sample_person",
  "name": "样例人物",
  "gender": "男",
  "birth_date": "1978-04-14",
  "birthplace": "福建省三明市",
  "birth_time_policy": "unknown_hour_generate_12_candidates",
  "events": [
    {
      "year": 1996,
      "type": "study_exam",
      "label": "升学或考试节点",
      "weight": 1.0,
      "source": "人工整理，待补公开来源"
    }
  ]
}
```

`type` 当前支持：

- `study_exam`
- `career_launch`
- `role_power`
- `role_transition`
- `business_power`
- `relationship`
- `movement`
- `public_visibility`
- `health_pressure`
- `scandal`
- `family`
- `death`
