# Detailed Alert Call Analysis

## Irrigation Events

| # | Function | Message | Context |
| --- | --- | --- | --- |
| 1 | publish_audit_log | `f"Irrigation completed for zone {state.zone_cfg.zone_name or state.zone_cfg.zone_id}: {json.dumps(event_payload, ensure_ascii=False)}"` | [See Below](#details-1) |
| 2 | publish_audit_log | `f"Schedule updated for zone {new_cfg.zone_name or new_cfg.zone_id}"` | [See Below](#details-2) |
| 3 | publish_audit_log | `(                         f"AI irrigation scheduled: starts at {scheduled_str}` | [See Below](#details-3) |
| 4 | publish_audit_log | `(                     f"Schedule triggered for zone {state.zone_cfg.zone_name or state.zone_cfg.zone_id}: "                     f"slot_id={slot.slot_id}` | [See Below](#details-4) |
| 5 | publish_audit_log | `json.dumps({"event": "start"` | [See Below](#details-5) |
| 6 | publish_audit_log | `json.dumps({                         "startTime": datetime.fromtimestamp(start_ts or end_ts` | [See Below](#details-6) |

## Plant Status

| # | Function | Message | Context |
| --- | --- | --- | --- |
| 7 | publish_audit_log | `f"Profile thresholds updated: min={new_cfg.profile.min_soil}%, max={new_cfg.profile.max_soil}%"` | [See Below](#details-7) |
| 8 | publish_audit_log | `f"Soil moisture alert: {soil}% is below min threshold {min_soil}%"` | [See Below](#details-8) |

## Device Status

| # | Function | Message | Context |
| --- | --- | --- | --- |
| 9 | publish_audit_log | `f"{DEVICE_FRIENDLY.get(device, device)} is back online"` | [See Below](#details-9) |
| 10 | publish_audit_log | `f"Profile mode changed from {old_cfg.profile.mode} to {new_cfg.profile.mode}"` | [See Below](#details-10) |
| 11 | publish_audit_log | `f"Failed to refresh zone/profile/schedule config: {exc}"` | [See Below](#details-11) |
| 12 | publish_audit_log | `f"{DEVICE_FRIENDLY.get(dev, dev)} offline: no telemetry received for {int(offline_for)} seconds from zone {state.zone_cfg.zone_name or state.zone_cfg.zone_id}"` | [See Below](#details-12) |

## Other / Unknown / Generic

| # | Function | Message | Context |
| --- | --- | --- | --- |
| 13 | publish_audit_log | `[Not found]` (Type: Unknown) | [See Below](#details-13) |
| 14 | backend.create_alert | `message` (Type: Variable (alert_type)) | [See Below](#details-14) |

## Call Details

### <a name='details-1'></a> Call 1: publish_audit_log
```python
publish_audit_log(
        zone_id=state.zone_cfg.zone_id,
        zone_name=state.zone_cfg.zone_name,
        severity="INFO",
        alert_type="IRRIGATION_EVENT",
        actor=actor,
        message=f"Irrigation completed for zone {state.zone_cfg.zone_name or state.zone_cfg.zone_id}: {json.dumps(event_payload, ensure_ascii=False)}",
    )
```

---

### <a name='details-2'></a> Call 2: publish_audit_log
```python
publish_audit_log(
                zone_id=new_cfg.zone_id,
                zone_name=new_cfg.zone_name,
                severity="INFO",
                alert_type="IRRIGATION_EVENT",
                actor="SYSTEM",
                message=f"Schedule updated for zone {new_cfg.zone_name or new_cfg.zone_id}",
            )
```

---

### <a name='details-3'></a> Call 3: publish_audit_log
```python
publish_audit_log(
                    zone_id=state.zone_cfg.zone_id,
                    zone_name=state.zone_cfg.zone_name,
                    severity="INFO",
                    alert_type="IRRIGATION_EVENT",
                    actor="AI",
                    message=(
                        f"AI irrigation scheduled: starts at {scheduled_str}, "
                        f"duration {ai_dur_sec}s"
                    ),
                )
```

---

### <a name='details-4'></a> Call 4: publish_audit_log
```python
publish_audit_log(
                zone_id=state.zone_cfg.zone_id,
                zone_name=state.zone_cfg.zone_name,
                severity="INFO",
                alert_type="IRRIGATION_EVENT",
                actor="SCHEDULE",
                message=(
                    f"Schedule triggered for zone {state.zone_cfg.zone_name or state.zone_cfg.zone_id}: "
                    f"slot_id={slot.slot_id}, schedule_id={slot.schedule_id or 'n/a'}, "
                    f"duration={dur_sec}s{', soil below threshold — priority boosted' if below_threshold else ''}"
                ),
            )
```

---

### <a name='details-5'></a> Call 5: publish_audit_log
```python
publish_audit_log(
                        zone_id=state.zone_cfg.zone_id,
                        zone_name=state.zone_cfg.zone_name,
                        severity="INFO",
                        alert_type="IRRIGATION_EVENT",
                        actor="DEVICE",
                        message=json.dumps({"event": "start", "zone": ezone, "id": eid, "ts": ets}, ensure_ascii=False),
                    )
```

---

### <a name='details-6'></a> Call 6: publish_audit_log
```python
publish_audit_log(
                    zone_id=state.zone_cfg.zone_id,
                    zone_name=state.zone_cfg.zone_name,
                    severity="INFO",
                    alert_type="IRRIGATION_EVENT",
                    actor="DEVICE",
                    message=json.dumps({
                        "startTime": datetime.fromtimestamp(start_ts or end_ts, UTC).isoformat().replace("+00:00", "Z"),
                        "endTime": datetime.fromtimestamp(end_ts, UTC).isoformat().replace("+00:00", "Z"),
                        "duration": duration_sec,
                    }, ensure_ascii=False),
                )
```

---

### <a name='details-7'></a> Call 7: publish_audit_log
```python
publish_audit_log(
            #     zone_id=new_cfg.zone_id,
            #     zone_name=new_cfg.zone_name,
            #     severity="INFO",
            #     alert_type="PLANT_STATUS",
            #     actor="SYSTEM",
            #     message=f"Profile thresholds updated: min={new_cfg.profile.min_soil}%, max={new_cfg.profile.max_soil}%",
            # )
```

---

### <a name='details-8'></a> Call 8: publish_audit_log
```python
publish_audit_log(
            zone_id=state.zone_cfg.zone_id,
            zone_name=state.zone_cfg.zone_name,
            severity="WARNING",
            alert_type="PLANT_STATUS",
            actor="SYSTEM",
            message=f"Soil moisture alert: {soil}% is below min threshold {min_soil}%",
        )
```

---

### <a name='details-9'></a> Call 9: publish_audit_log
```python
publish_audit_log(
                zone_id=self.zone_cfg.zone_id,
                zone_name=self.zone_cfg.zone_name,
                severity="INFO",
                alert_type="DEVICE_STATUS",
                actor="SYSTEM",
                message=f"{DEVICE_FRIENDLY.get(device, device)} is back online",
            )
```

---

### <a name='details-10'></a> Call 10: publish_audit_log
```python
publish_audit_log(
        #         zone_id=new_cfg.zone_id,
        #         zone_name=new_cfg.zone_name,
        #         severity="INFO",
        #         alert_type="DEVICE_STATUS",
        #         actor="SYSTEM",
        #         message=f"Profile mode changed from {old_cfg.profile.mode} to {new_cfg.profile.mode}",
        #     )
```

---

### <a name='details-11'></a> Call 11: publish_audit_log
```python
publish_audit_log(
            zone_id=state.zone_cfg.zone_id,
            zone_name=state.zone_cfg.zone_name,
            severity="WARNING",
            alert_type="DEVICE_STATUS",
            actor="SYSTEM",
            message=f"Failed to refresh zone/profile/schedule config: {exc}",
        )
```

---

### <a name='details-12'></a> Call 12: publish_audit_log
```python
publish_audit_log(
                zone_id=state.zone_cfg.zone_id,
                zone_name=state.zone_cfg.zone_name,
                severity="CRITICAL",
                alert_type="DEVICE_STATUS",
                actor="SYSTEM",
                message=f"{DEVICE_FRIENDLY.get(dev, dev)} offline: no telemetry received for {int(offline_for)} seconds from zone {state.zone_cfg.zone_name or state.zone_cfg.zone_id}",
            )
```

---

### <a name='details-13'></a> Call 13: publish_audit_log
```python
publish_audit_log(*, zone_id: Optional[str], zone_name: str, severity: str, alert_type: str, actor: str, message: str)
```

---

### <a name='details-14'></a> Call 14: backend.create_alert
```python
backend.create_alert(
            zone_id=zone_id,
            message=message,
            severity=severity,
            alert_type=alert_type,
            actor=actor,
        )
```

---

