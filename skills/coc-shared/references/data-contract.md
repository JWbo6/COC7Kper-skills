# CoC 数据契约

所有结构化记录使用 UTF-8 JSON 或 JSONL。名称只用于显示，关联必须使用稳定 ID。

## 公共元数据

```json
{
  "id": "campaign_01H00000000000000000000000",
  "record_type": "campaign",
  "schema_version": "1.0.0",
  "campaign_id": "campaign_01H00000000000000000000000",
  "created_at": "2026-08-01T00:00:00Z",
  "updated_at": "2026-08-01T00:00:00Z",
  "revision": 1,
  "status": "active"
}
```

- `id` 不因改名改变；建议使用 UUID/ULID 风格。
- 时间使用 ISO 8601 UTC；`occurred_at` 表示事件发生时间，`written_at` 表示写入时间。
- 修改实体时递增 `revision`，保留事件历史，不静默覆盖旧值。
- `campaign_id`、`session_id`、`entity_id` 用于跨文件追踪，不能只引用名称。

## 追加事件

`03-场次记录/掷骰记录.jsonl` 与变化记录可使用一行一事件：

```json
{"event_id":"event_01H...","event_type":"character.sanity_changed","schema_version":"1.0.0","campaign_id":"campaign_01H...","session_id":"session_001","entity_id":"character_01H...","occurred_at":"2026-08-01T00:00:00Z","written_at":"2026-08-01T00:00:01Z","payload":{"old":60,"new":55,"reason":"理智损失"},"execution_mode":"manual","revision":1}
```

重复事件用 `event_id` 或业务幂等键去重。JSONL 尾部不完整时隔离损坏尾部并报告，不要静默删除有效记录。索引应能从事件重建。

## 后台演化事件

后台事件用于记录玩家未必知道、但会随模组内时间和条件持续发生的世界变化。它与现实写入时间分离，且默认只供 KP 使用：

```json
{
  "event_id": "world_01H...",
  "event_type": "threat.tick",
  "schema_version": "1.1.0",
  "campaign_id": "campaign_01H...",
  "session_id": "session_001",
  "game_time": "2013-10-31T23:18:00+09:00",
  "elapsed_seconds": 180,
  "sequence": 12,
  "occurred_at": "2026-08-02T05:00:00Z",
  "written_at": "2026-08-02T05:00:01Z",
  "status": "fired",
  "trigger": {"type": "time", "due_after_seconds": 180},
  "caused_by_event_id": "event_01H...",
  "visibility": "kp_only",
  "related_entity_ids": ["location_01H..."],
  "payload": {
    "kp_state": {"threat_progress": 2},
    "public_projection": null
  },
  "execution_mode": "manual",
  "revision": 1
}
```

- `game_time` 是模组内时间；`elapsed_seconds` 是从团内时钟起点经过的时间；`occurred_at` 是记录系统中的发生时间；`written_at` 是写入时间，四者不能混用。
- `status` 使用 `scheduled`、`eligible`、`fired` 或 `cancelled`。事件不可变；状态变化追加新事件或新 revision，不删除旧行。
- `visibility` 默认 `kp_only`。`payload.kp_state` 保存隐藏进度；只有玩家已接触、观察、测量到的事实才能写入 `public_projection` 并投影到玩家文件。
- 使用 `event_id` 或业务幂等键去重；同一游戏时刻使用 `sequence` 保证结算顺序。后台事件可以影响环境、NPC、资源、危险和路径，但玩家未感知时不得写入玩家视图。

后台快照建议使用以下字段：`clock_id`、`game_time`、`elapsed_seconds`、`last_event_id`、`pending_event_ids`、`hidden_state`、`revision`。恢复时先加载后台快照和事件，再生成公开投影。
